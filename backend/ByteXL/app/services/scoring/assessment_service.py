"""
Unified Risk Assessment Service for BrandShield AI.
Integrates detection engines from Phase 5 (Domain, URL, Scam Text, Profile, Image, APK)
to produce explainable, deterministic RiskAssessment records.
"""

from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, NotFoundError
from app.core.logging import get_logger
from app.models.enums import RiskSeverity, TargetType, ThreatReportStatus, UserRole
from app.models.risk_assessment import RiskAssessment
from app.models.threat_report import ThreatReport
from app.models.user import User
from app.repositories.risk_assessment_repo import RiskAssessmentRepository
from app.repositories.threat_report_repo import ThreatReportRepository
from app.services.detection.brand_intelligence import BrandIntelligenceService
from app.services.detection.domain_analysis import DomainAnalysisService
from app.services.detection.profile_analysis import ProfileAnalysisService, SocialProfileInput
from app.services.detection.scam_text import ScamTextClassifier
from app.services.detection.url_analysis import SecureURLAnalysisService
from app.services.scoring.engine import RiskScoringEngine, SignalItem, UnavailableSignal

logger = get_logger("app.services.scoring.assessment_service")


class RiskAssessmentService:
    """
    Unified threat risk assessment service.
    Coordinates domain, URL, scam text, and profile analysis services
    into deterministic, explainable risk assessments.
    """

    def __init__(self) -> None:
        self.assessment_repo = RiskAssessmentRepository()
        self.report_repo = ThreatReportRepository()
        self.brand_intel = BrandIntelligenceService()
        self.domain_service = DomainAnalysisService()
        self.url_service = SecureURLAnalysisService()
        self.scam_classifier = ScamTextClassifier()
        self.profile_service = ProfileAnalysisService()
        self._app_metadata_service = None
        self.scoring_engine = RiskScoringEngine()

    @property
    def app_metadata_service(self):
        if self._app_metadata_service is None:
            from app.services.detection.app_metadata_analysis import AppMetadataAnalysisService
            self._app_metadata_service = AppMetadataAnalysisService()
        return self._app_metadata_service

    async def get_assessment(
        self,
        db: AsyncSession,
        report_id: uuid.UUID,
        current_user: User,
    ) -> RiskAssessment:
        """
        Retrieve the latest risk assessment for a threat report with ownership authorization.
        """
        report = await self.report_repo.get_by_id(db, report_id)
        if not report:
            raise NotFoundError(f"Threat report with id '{report_id}' not found.")

        # Authorization: report owner or admin
        is_owner = report.reporter_id == current_user.id
        is_admin = current_user.role == UserRole.ADMIN

        if not is_owner and not is_admin:
            raise AuthorizationError("You do not have permission to view assessments for this report.")

        assessment = await self.assessment_repo.get_latest_by_report_id(db, report_id)
        if not assessment:
            raise NotFoundError(f"No risk assessment found for threat report '{report_id}'.")

        return assessment

    async def analyze_report(
        self,
        db: AsyncSession,
        report_id: uuid.UUID,
        current_user: User,
    ) -> RiskAssessment:
        """
        Execute unified risk assessment pipeline on a threat report.
        Integrates Phase 5 detection services, generates explainability breakdown,
        and persists the assessment.
        """
        report = await self.report_repo.get_by_id(db, report_id)
        if not report:
            raise NotFoundError(f"Threat report with id '{report_id}' not found.")

        # Authorization check: only submitting customer or admin can trigger analysis
        is_owner = report.reporter_id == current_user.id
        is_admin = current_user.role == UserRole.ADMIN

        if not is_owner and not is_admin:
            logger.warning(
                f"Unauthorized analyze attempt: user {current_user.id} on report {report_id}"
            )
            raise AuthorizationError("You do not have permission to analyze this threat report.")

        # Transition status to ANALYZING during execution
        if report.status == ThreatReportStatus.SUBMITTED:
            report.status = ThreatReportStatus.ANALYZING
            await self.report_repo.update(db, report)

        # Retrieve authoritative reference data for verified brands
        verified_brands = await self.brand_intel.get_verified_brands(db)

        signals: List[SignalItem] = []
        unavailable_signals: List[UnavailableSignal] = []
        confidence: Optional[float] = None

        target_type = report.target_type
        target_value = report.target_value

        # --------------------------------------------------------------------
        # 1. EVALUATE TARGET TYPE USING PHASE 5 ENGINES
        # --------------------------------------------------------------------
        if target_type == TargetType.DOMAIN:
            domain_res = self.domain_service.analyze_domain(target_value, verified_brands)
            
            # Domain similarity signals
            if domain_res.similarity_score >= 70.0:
                pts = min(25.0, round((domain_res.similarity_score - 70.0) / 30.0 * 20.0 + 5.0, 2))
                matched = domain_res.matched_brand_name or "Verified Brand"
                signals.append(
                    SignalItem(
                        category="DOMAIN_SIMILARITY",
                        signal_type="HIGH_LEXICAL_SIMILARITY",
                        points=pts,
                        description=f"Domain '{target_value}' has {domain_res.similarity_score:.1f}% similarity to verified brand '{matched}'.",
                        evidence_context={"matched_brand": matched, "score": domain_res.similarity_score},
                    )
                )

            if domain_res.has_homoglyphs:
                signals.append(
                    SignalItem(
                        category="DOMAIN_SIMILARITY",
                        signal_type="HOMOGLYPH_LOOKALIKE",
                        points=15.0,
                        description=f"Domain utilizes visual lookalike Unicode characters (confusables): {domain_res.homoglyphs_detected}",
                        evidence_context={"homoglyphs": domain_res.homoglyphs_detected},
                    )
                )

            if domain_res.suspicious_keywords_found:
                signals.append(
                    SignalItem(
                        category="DOMAIN_SIMILARITY",
                        signal_type="BRAND_KEYWORD_TYPO",
                        points=10.0,
                        description="Domain combines verified brand keyword with generic phishing terms.",
                        evidence_context={"keywords": domain_res.suspicious_keywords_found},
                    )
                )

            # Threat Intel Matches
            if domain_res.threat_intel_match:
                feed = domain_res.threat_intel_details or "Global Threat Feed"
                signals.append(
                    SignalItem(
                        category="THREAT_INTELLIGENCE",
                        signal_type="THREAT_FEED_MATCH",
                        points=15.0,
                        description=f"Domain matches configured threat intelligence feed: {feed}.",
                        evidence_context={"feed_name": feed},
                    )
                )
            else:
                unavailable_signals.append(
                    UnavailableSignal(
                        category="THREAT_INTELLIGENCE",
                        reason="Domain was checked against threat intelligence feeds but produced no matches.",
                    )
                )

            # Infrastructure / TLD check
            high_risk_tlds = {"top", "xyz", "click", "buzz", "tk", "ml", "ga", "cf", "gq"}
            if domain_res.suffix in high_risk_tlds:
                signals.append(
                    SignalItem(
                        category="REDIRECT_AND_INFRASTRUCTURE",
                        signal_type="SUSPICIOUS_TLD",
                        points=5.0,
                        description=f"Domain registered under high-risk TLD: .{domain_res.suffix}.",
                    )
                )

            unavailable_signals.append(
                UnavailableSignal(
                    category="SCAM_AND_CREDENTIAL_HARVESTING",
                    reason="Target is a domain; scam text body was not provided for NLP classification.",
                )
            )

        elif target_type == TargetType.URL:
            url_res = self.url_service.analyze_url(target_value, verified_brands)

            # Domain component in URL
            if url_res.domain_analysis.similarity_score >= 70.0:
                pts = min(25.0, round((url_res.domain_analysis.similarity_score - 70.0) / 30.0 * 20.0 + 5.0, 2))
                matched = url_res.domain_analysis.matched_brand_name or "Verified Brand"
                signals.append(
                    SignalItem(
                        category="DOMAIN_SIMILARITY",
                        signal_type="URL_HOST_SIMILARITY",
                        points=pts,
                        description=f"URL host '{url_res.domain_analysis.registrable_domain}' has {url_res.domain_analysis.similarity_score:.1f}% similarity to '{matched}'.",
                    )
                )

            if url_res.domain_analysis.has_homoglyphs:
                signals.append(
                    SignalItem(
                        category="DOMAIN_SIMILARITY",
                        signal_type="HOMOGLYPH_LOOKALIKE",
                        points=15.0,
                        description="URL host contains visual Unicode confusables.",
                    )
                )

            # Credential Harvesting / Scam indicators in URL
            if url_res.credential_harvesting_params or url_res.suspicious_path_segments:
                signals.append(
                    SignalItem(
                        category="SCAM_AND_CREDENTIAL_HARVESTING",
                        signal_type="CREDENTIAL_HARVESTING_LURE",
                        points=25.0,
                        description=f"URL contains credential harvesting paths or parameters: {url_res.suspicious_path_segments + url_res.credential_harvesting_params}",
                    )
                )

            # Threat Intel Matches
            if url_res.domain_analysis.threat_intel_match:
                signals.append(
                    SignalItem(
                        category="THREAT_INTELLIGENCE",
                        signal_type="THREAT_FEED_MATCH",
                        points=15.0,
                        description="URL host matches active threat intelligence feed entries.",
                    )
                )
            else:
                unavailable_signals.append(
                    UnavailableSignal(
                        category="THREAT_INTELLIGENCE",
                        reason="URL host verified against threat feeds with no positive matches.",
                    )
                )

            # SSRF / Restricted IP Infrastructure
            if url_res.is_ssrf_blocked or (url_res.ip_validation and not url_res.ip_validation.is_safe_public_ip):
                reason = url_res.ssrf_block_reason or (url_res.ip_validation.rejection_reason if url_res.ip_validation else "Restricted address")
                signals.append(
                    SignalItem(
                        category="REDIRECT_AND_INFRASTRUCTURE",
                        signal_type="RESTRICTED_IP_TARGET",
                        points=10.0,
                        description=f"URL targets restricted IP space or metadata: {reason}",
                    )
                )
            elif url_res.is_suspicious_redirect:
                signals.append(
                    SignalItem(
                        category="REDIRECT_AND_INFRASTRUCTURE",
                        signal_type="UNVALIDATED_REDIRECT",
                        points=10.0,
                        description="URL exhibits open redirect or suspicious target parameters.",
                    )
                )

        elif target_type == TargetType.SCAM_TEXT:
            text_res = self.scam_classifier.classify_text(target_value)
            confidence = text_res.scam_probability

            if text_res.scam_probability >= 0.50:
                pts = min(25.0, round(text_res.scam_probability * 15.0, 2))
                signals.append(
                    SignalItem(
                        category="SCAM_AND_CREDENTIAL_HARVESTING",
                        signal_type="ML_SCAM_CLASSIFICATION",
                        points=pts,
                        description=f"ML baseline classified message as scam with {text_res.scam_probability * 100:.1f}% probability.",
                        evidence_context={"probability": text_res.scam_probability, "model": text_res.model_metadata.model_version},
                    )
                )

            if text_res.urgency_indicators:
                signals.append(
                    SignalItem(
                        category="SCAM_AND_CREDENTIAL_HARVESTING",
                        signal_type="URGENCY_LURE",
                        points=5.0,
                        description=f"Urgency manipulation phrases detected: {', '.join(text_res.urgency_indicators)}",
                    )
                )

            if text_res.credential_indicators:
                signals.append(
                    SignalItem(
                        category="SCAM_AND_CREDENTIAL_HARVESTING",
                        signal_type="CREDENTIAL_THEFT_INDICATOR",
                        points=5.0,
                        description=f"Credential theft lures detected: {', '.join(text_res.credential_indicators)}",
                    )
                )

            if text_res.financial_indicators:
                signals.append(
                    SignalItem(
                        category="SCAM_AND_CREDENTIAL_HARVESTING",
                        signal_type="FINANCIAL_SCAM_INDICATOR",
                        points=5.0,
                        description=f"Financial scam terms detected: {', '.join(text_res.financial_indicators)}",
                    )
                )

            if text_res.contains_links:
                signals.append(
                    SignalItem(
                        category="REDIRECT_AND_INFRASTRUCTURE",
                        signal_type="EMBEDDED_LINK",
                        points=5.0,
                        description="Scam message contains embedded external links directing users off-platform.",
                    )
                )

            unavailable_signals.append(
                UnavailableSignal(
                    category="DOMAIN_SIMILARITY",
                    reason="Target is raw scam text; no dedicated registrable domain analyzed.",
                )
            )
            unavailable_signals.append(
                UnavailableSignal(
                    category="THREAT_INTELLIGENCE",
                    reason="Text payload not correlated with IP/Domain reputation feeds.",
                )
            )

        elif target_type == TargetType.SOCIAL_PROFILE:
            profile_input = SocialProfileInput(
                platform="Generic",
                username=target_value,
                bio=report.description,
            )
            profile_res = self.profile_service.analyze_profile(profile_input, verified_brands)

            if not profile_res.is_official_account and profile_res.username_similarity >= 70.0:
                pts = min(25.0, round((profile_res.username_similarity - 70.0) / 30.0 * 20.0 + 5.0, 2))
                matched = profile_res.matched_brand_name or "Verified Brand"
                signals.append(
                    SignalItem(
                        category="DOMAIN_SIMILARITY",
                        signal_type="PROFILE_HANDLE_IMPERSONATION",
                        points=pts,
                        description=f"Social handle '{target_value}' has {profile_res.username_similarity:.1f}% similarity to verified brand '{matched}'.",
                    )
                )

            if not profile_res.is_official_account and profile_res.bio_impersonation_detected:
                signals.append(
                    SignalItem(
                        category="SCAM_AND_CREDENTIAL_HARVESTING",
                        signal_type="SUPPORT_IMPERSONATION_CLAIM",
                        points=25.0,
                        description=f"Profile bio claims official support status for brand '{profile_res.matched_brand_name}'.",
                    )
                )

            if profile_res.profile_link_mismatch:
                signals.append(
                    SignalItem(
                        category="REDIRECT_AND_INFRASTRUCTURE",
                        signal_type="EXTERNAL_LINK_MISMATCH",
                        points=10.0,
                        description="Profile links to external domains that mismatch the official brand domain.",
                    )
                )

            unavailable_signals.append(
                UnavailableSignal(
                    category="THREAT_INTELLIGENCE",
                    reason="Social handle not directly indexed in infrastructure threat feeds.",
                )
            )

        elif target_type == TargetType.MOBILE_APP:
            # Mobile app metadata / package analysis
            handled_by_metadata = False
            brand_profile = (
                next((b for b in verified_brands if b.brand_id == report.brand_id), None)
                if (report.brand_id and verified_brands)
                else None
            )

            if brand_profile:
                try:
                    from app.schemas.app_metadata import AppMetadataAnalysisRequest
                    # Validate or structure package identifier
                    pkg_id = target_value if ("." in target_value and not target_value.startswith("http")) else f"com.{target_value.lower().replace(' ', '')}.app"
                    meta_req = AppMetadataAnalysisRequest(
                        brand_id=brand_profile.brand_id,
                        app_name=target_value,
                        platform="ANDROID",
                        app_identifier=pkg_id,
                        description=report.description,
                    )
                    meta_res = self.app_metadata_service.analyze_metadata(meta_req, brand_profile)
                    for ind in meta_res.contributing_indicators:
                        signals.append(
                            SignalItem(
                                category=ind.category,
                                signal_type=ind.signal_type,
                                points=ind.points,
                                description=ind.description,
                                evidence_context=ind.evidence_context,
                            )
                        )
                    for miss in meta_res.missing_signals:
                        unavailable_signals.append(
                            UnavailableSignal(category=miss["category"], reason=miss["reason"])
                        )
                    handled_by_metadata = True
                except Exception:
                    pass

            if not handled_by_metadata:
                signals.append(
                    SignalItem(
                        category="DOMAIN_SIMILARITY",
                        signal_type="APP_PACKAGE_NAME_OBSERVATION",
                        points=5.0,
                        description=f"Mobile app package '{target_value}' registered for investigation.",
                    )
                )
                unavailable_signals.append(
                    UnavailableSignal(
                        category="SCAM_AND_CREDENTIAL_HARVESTING",
                        reason="APK bytecode static analysis queued separately.",
                    )
                )

        # --------------------------------------------------------------------
        # 2. CHECK VISUAL SIMILARITY (EVIDENCES)
        # --------------------------------------------------------------------
        has_image_evidence = any(
            ev.evidence_type.value in ["SCREENSHOT", "SCAM_SAMPLE"] for ev in report.evidences
        )
        if not has_image_evidence:
            unavailable_signals.append(
                UnavailableSignal(
                    category="VISUAL_SIMILARITY",
                    reason="No image or screenshot artifacts attached to threat report for perceptual hashing.",
                )
            )

        # --------------------------------------------------------------------
        # 3. RUN RISK SCORING ENGINE
        # --------------------------------------------------------------------
        scoring_result = self.scoring_engine.evaluate_signals(
            signals=signals,
            unavailable_signals=unavailable_signals,
            confidence=confidence,
        )

        # --------------------------------------------------------------------
        # 4. PERSIST AND UPDATE THREAT REPORT
        # --------------------------------------------------------------------
        assessment = await self.assessment_repo.create(
            db=db,
            report_id=report.id,
            entity_id=str(report.id),
            model_version=scoring_result.model_version,
            risk_score=scoring_result.risk_score,
            severity=scoring_result.severity,
            confidence=scoring_result.confidence,
            explanation_json=scoring_result.explanation,
            indicators_json=scoring_result.indicators,
            recommendation_json=scoring_result.recommendations,
        )

        # Transition report to UNDER_REVIEW
        report.status = ThreatReportStatus.UNDER_REVIEW
        await self.report_repo.update(db, report)

        await db.commit()
        await db.refresh(assessment)

        logger.info(
            f"Completed risk assessment for report {report_id}: "
            f"score={assessment.risk_score}, severity={assessment.severity.value}, "
            f"indicators={len(assessment.indicators_json)}"
        )

        return assessment
