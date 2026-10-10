from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.dependencies import (
    get_current_active_user,
    require_admin,
    require_customer,
)
from app.db.session import get_db
from app.models.enums import EvidenceType, ThreatReportStatus
from app.models.user import User
from app.schemas.evidence import EvidenceResponse
from app.schemas.risk_assessment import RiskAssessmentResponse
from app.schemas.threat_report import (
    ThreatReportCreate,
    ThreatReportResponse,
    ThreatReportStatusUpdate,
)
from app.services.scoring import RiskAssessmentService
from app.services.threat_report_service import ThreatReportService

router = APIRouter(prefix="/threat-reports", tags=["Threat Reports"])
threat_report_service = ThreatReportService()
risk_assessment_service = RiskAssessmentService()


@router.post(
    "",
    response_model=ThreatReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a threat or impersonation report",
    description="Allows authenticated customers to report scam domains, URLs, social profiles, scam text, or fake apps.",
)
async def create_threat_report(
    payload: ThreatReportCreate,
    current_customer: User = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
) -> ThreatReportResponse:
    report = await threat_report_service.create_report(
        db=db,
        current_user=current_customer,
        payload=payload,
    )
    return ThreatReportResponse.model_validate(report)


@router.get(
    "/me",
    response_model=List[ThreatReportResponse],
    status_code=status.HTTP_200_OK,
    summary="Get my threat reports (alias)",
    description="Retrieve all threat reports submitted by the authenticated customer with pagination and filtering.",
)
async def get_my_reports_alias(
    response: Response,
    status_filter: Optional[ThreatReportStatus] = Query(default=None, alias="status", description="Filter by report status"),
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    limit: Optional[int] = Query(default=None, ge=1, le=100, description="Raw limit override"),
    offset: Optional[int] = Query(default=None, ge=0, description="Raw offset override"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[ThreatReportResponse]:
    eff_limit = limit if limit is not None else page_size
    eff_offset = offset if offset is not None else (page - 1) * page_size
    eff_page = (eff_offset // eff_limit) + 1 if eff_limit > 0 else 1

    total = await threat_report_service.count_my_reports(
        db=db,
        current_user=current_user,
        status=status_filter,
    )
    reports = await threat_report_service.get_my_reports(
        db=db,
        current_user=current_user,
        status=status_filter,
        limit=eff_limit,
        offset=eff_offset,
    )
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page"] = str(eff_page)
    response.headers["X-Page-Size"] = str(eff_limit)
    return [ThreatReportResponse.model_validate(r) for r in reports]


@router.get(
    "/{report_id}",
    response_model=ThreatReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get threat report details",
    description="Retrieve detailed threat report and attached evidence. Access is strictly restricted to the submitting customer and administrators.",
)
async def get_threat_report(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ThreatReportResponse:
    report = await threat_report_service.get_report_by_id(
        db=db,
        report_id=report_id,
        current_user=current_user,
    )
    return ThreatReportResponse.model_validate(report)


@router.patch(
    "/{report_id}",
    response_model=ThreatReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Update threat report investigation status",
    description="Allows administrators to transition threat report status across investigation lifecycle stages.",
)
async def update_report_status(
    report_id: uuid.UUID,
    payload: ThreatReportStatusUpdate,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ThreatReportResponse:
    report = await threat_report_service.update_report_status(
        db=db,
        report_id=report_id,
        current_user=current_admin,
        new_status=payload.status,
    )
    return ThreatReportResponse.model_validate(report)


@router.post(
    "/{report_id}/evidence",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload secure evidence attachment",
    description=(
        "Upload a supporting evidence artifact (screenshot, document, header, log) for a threat report. "
        "Enforces strict allowlisting, magic byte header inspection, file size limits, content hashing, "
        "and isolated private storage."
    ),
)
async def upload_evidence(
    report_id: uuid.UUID,
    file: UploadFile = File(..., description="Evidence file to upload"),
    evidence_type: EvidenceType = Form(default=EvidenceType.SCREENSHOT),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> EvidenceResponse:
    evidence = await threat_report_service.attach_evidence(
        db=db,
        report_id=report_id,
        file=file,
        evidence_type=evidence_type,
        current_user=current_user,
    )
    return EvidenceResponse.model_validate(evidence)


@router.get(
    "/{report_id}/evidence/{evidence_id}",
    status_code=status.HTTP_200_OK,
    summary="Download secure evidence artifact",
    description=(
        "Retrieve private evidence file. Access is strictly restricted to the report owner or platform administrators. "
        "Responses enforce safe download headers and nosniff to prevent content execution."
    ),
)
async def get_evidence_file(
    report_id: uuid.UUID,
    evidence_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    file_path, evidence = await threat_report_service.get_evidence_file(
        db=db,
        report_id=report_id,
        evidence_id=evidence_id,
        current_user=current_user,
    )

    return FileResponse(
        path=str(file_path),
        filename=evidence.original_filename,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{evidence.original_filename}"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-cache, no-store, must-revalidate",
            "Content-Security-Policy": "default-src 'none'",
        },
    )


@router.post(
    "/{report_id}/analyze",
    response_model=RiskAssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute explainable risk assessment on threat report",
    description=(
        "Analyzes reported entity across domain, URL, scam text, and profile detection engines. "
        "Applies deterministic scoring rules, explains all contributing signals, records unavailable "
        "data categories without penalty, and generates actionable recommendations. "
        "Access is strictly restricted to the report owner and administrators."
    ),
)
async def analyze_threat_report(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RiskAssessmentResponse:
    assessment = await risk_assessment_service.analyze_report(
        db=db,
        report_id=report_id,
        current_user=current_user,
    )
    return RiskAssessmentResponse.model_validate(assessment)


@router.get(
    "/{report_id}/assessment",
    response_model=RiskAssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get latest explainable risk assessment",
    description=(
        "Retrieves the most recent explainable risk assessment for a threat report. "
        "Includes scoring breakdown, contributing signals, unavailable signals, and recommendations. "
        "Access is strictly restricted to the report owner and administrators."
    ),
)
async def get_threat_report_assessment(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RiskAssessmentResponse:
    assessment = await risk_assessment_service.get_assessment(
        db=db,
        report_id=report_id,
        current_user=current_user,
    )
    return RiskAssessmentResponse.model_validate(assessment)

