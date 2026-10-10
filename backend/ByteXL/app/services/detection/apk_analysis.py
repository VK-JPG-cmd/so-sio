"""
Android APK Static Analysis Service.
Uses Androguard to safely inspect package metadata, permissions, signing certificates,
embedded network endpoints, and file integrity without executing uploaded APK binaries.

Safety Invariant: APK files are NEVER executed. Analysis is strictly static and run
within an isolated worker with resource and timeout limits.
"""

from concurrent.futures import ThreadPoolExecutor, TimeoutError
import hashlib
import io
import re
from typing import Any, Dict, List, Optional, Set
import zipfile
from pydantic import BaseModel, Field
from rapidfuzz import fuzz
from app.core.exceptions import ValidationError
from app.core.logging import get_logger
from app.services.detection.brand_intelligence import VerifiedBrandProfile

logger = get_logger("app.services.detection.apk_analysis")

# Attempt importing Androguard safely across 4.x and 3.x
try:
    from androguard.core.apk import APK  # type: ignore
    ANDROGUARD_AVAILABLE = True
except ImportError:
    try:
        from androguard.core.bytecodes.apk import APK  # type: ignore
        ANDROGUARD_AVAILABLE = True
    except ImportError:
        APK = None  # type: ignore
        ANDROGUARD_AVAILABLE = False

MAX_APK_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
ANALYSIS_TIMEOUT_SECONDS = 15.0

SENSITIVE_PERMISSIONS = {
    "android.permission.SEND_SMS",
    "android.permission.READ_SMS",
    "android.permission.RECEIVE_SMS",
    "android.permission.RECEIVE_MMS",
    "android.permission.READ_CALL_LOG",
    "android.permission.WRITE_CALL_LOG",
    "android.permission.PROCESS_OUTGOING_CALLS",
    "android.permission.RECORD_AUDIO",
    "android.permission.CAMERA",
    "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.READ_CONTACTS",
    "android.permission.WRITE_CONTACTS",
    "android.permission.SYSTEM_ALERT_WINDOW",
    "android.permission.REQUEST_INSTALL_PACKAGES",
    "android.permission.BIND_ACCESSIBILITY_SERVICE",
    "android.permission.READ_EXTERNAL_STORAGE",
    "android.permission.WRITE_EXTERNAL_STORAGE",
}


class CertificateMetadata(BaseModel):
    """Metadata regarding APK signing certificates."""

    issuer: Optional[str] = None
    subject: Optional[str] = None
    sha256_fingerprint: Optional[str] = None
    serial_number: Optional[str] = None


class APKAnalysisResult(BaseModel):
    """Full static analysis report for an Android APK artifact."""

    file_name: str
    file_size_bytes: int
    sha256_hash: str
    md5_hash: str

    androguard_available: bool = True
    is_valid_apk: bool = False
    validation_error: Optional[str] = None

    # Package metadata
    package_name: Optional[str] = None
    app_name: Optional[str] = None
    version_code: Optional[str] = None
    version_name: Optional[str] = None
    min_sdk: Optional[str] = None
    target_sdk: Optional[str] = None
    main_activity: Optional[str] = None

    # Permissions
    declared_permissions: List[str] = Field(default_factory=list)
    sensitive_permissions: List[str] = Field(default_factory=list)

    # Certificates
    certificates: List[CertificateMetadata] = Field(default_factory=list)

    # Embedded URLs & endpoints
    embedded_urls: List[str] = Field(default_factory=list)
    embedded_domains: List[str] = Field(default_factory=list)

    # Impersonation and risk
    matched_brand_id: Optional[str] = None
    matched_brand_name: Optional[str] = None
    impersonation_score: float = Field(0.0, ge=0.0, le=100.0)

    risk_score: float = Field(0.0, ge=0.0, le=100.0)
    risk_level: str = "LOW"
    analysis_reasons: List[str] = Field(default_factory=list)


class APKAnalysisService:
    """Isolated service performing static inspection of Android application packages."""

    def __init__(self) -> None:
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="apk-analyzer")

    def analyze_apk(
        self,
        apk_bytes: bytes,
        file_name: str = "application.apk",
        verified_brands: Optional[List[VerifiedBrandProfile]] = None,
    ) -> APKAnalysisResult:
        """
        Execute static analysis with timeout enforcement and resource boundaries.
        Never executes code.
        """
        if not ANDROGUARD_AVAILABLE or APK is None:
            return APKAnalysisResult(
                file_name=file_name,
                file_size_bytes=len(apk_bytes),
                sha256_hash=hashlib.sha256(apk_bytes).hexdigest(),
                md5_hash=hashlib.md5(apk_bytes).hexdigest(),
                androguard_available=False,
                is_valid_apk=False,
                validation_error="Androguard dependency is unavailable in runtime environment.",
                risk_level="INCONCLUSIVE",
                analysis_reasons=["Static analysis could not be performed because Androguard is unavailable."],
            )

        # Enforce size limits
        size = len(apk_bytes)
        if size == 0:
            raise ValidationError("APK byte stream is empty (0 bytes).")
        if size > MAX_APK_FILE_SIZE_BYTES:
            max_mb = MAX_APK_FILE_SIZE_BYTES / (1024 * 1024)
            raise ValidationError(f"APK file size ({size / (1024*1024):.1f} MB) exceeds maximum allowed {max_mb:.0f} MB.")

        # Pre-flight ZIP validation & zip bomb defenses
        try:
            with zipfile.ZipFile(io.BytesIO(apk_bytes), "r") as zf:
                infolist = zf.infolist()
                total_uncompressed = 0
                max_total_uncompressed = 250 * 1024 * 1024  # 250 MB
                max_single_entry = 100 * 1024 * 1024  # 100 MB

                for info in infolist:
                    # Path traversal check
                    if ".." in info.filename or info.filename.startswith(("/", "\\")):
                        raise ValidationError(f"Malicious archive member path detected: {info.filename}")

                    total_uncompressed += info.file_size
                    if info.file_size > max_single_entry:
                        raise ValidationError(
                            f"Archive entry '{info.filename}' exceeds maximum uncompressed size ({info.file_size} > {max_single_entry})."
                        )
                    if total_uncompressed > max_total_uncompressed:
                        raise ValidationError(
                            f"Archive total uncompressed size exceeds limit ({total_uncompressed} > {max_total_uncompressed})."
                        )

                    # Check compression ratio for zip bomb defense
                    if info.compress_size > 0 and info.file_size > 1024 * 1024:
                        ratio = info.file_size / info.compress_size
                        if ratio > 100:
                            raise ValidationError(
                                f"Archive entry '{info.filename}' has abnormal compression ratio ({ratio:.1f}:1), potential zip bomb."
                            )

                namelist = [info.filename for info in infolist]
                if "AndroidManifest.xml" not in namelist:
                    raise ValidationError("File is not a valid APK: AndroidManifest.xml missing.")
        except zipfile.BadZipFile as e:
            raise ValidationError(f"Malformed APK package: invalid ZIP archive structure ({e}).")

        # Run static inspection in worker thread with timeout
        future = self.executor.submit(
            self._do_static_analysis, apk_bytes, file_name, verified_brands
        )

        try:
            return future.result(timeout=ANALYSIS_TIMEOUT_SECONDS)
        except TimeoutError:
            logger.error(f"APK static analysis timed out after {ANALYSIS_TIMEOUT_SECONDS}s.")
            raise ValidationError(f"APK analysis timed out after {ANALYSIS_TIMEOUT_SECONDS} seconds (resource limit).")
        except Exception as e:
            logger.warning(f"APK analysis failed: {e}")
            raise ValidationError(f"Failed to inspect APK package: {str(e)}")

    def _do_static_analysis(
        self,
        apk_bytes: bytes,
        file_name: str,
        verified_brands: Optional[List[VerifiedBrandProfile]],
    ) -> APKAnalysisResult:
        """Internal synchronous worker method performing static inspection."""
        sha256_hex = hashlib.sha256(apk_bytes).hexdigest()
        md5_hex = hashlib.md5(apk_bytes).hexdigest()

        try:
            apk = APK(apk_bytes, raw=True)
        except Exception as e:
            return APKAnalysisResult(
                file_name=file_name,
                file_size_bytes=len(apk_bytes),
                sha256_hash=sha256_hex,
                md5_hash=md5_hex,
                is_valid_apk=False,
                validation_error=f"Androguard parser failed: {e}",
                risk_level="HIGH",
                analysis_reasons=["Malformed or obfuscated APK structure detected."],
            )

        def _safe(fn: Any, default: str = "") -> str:
            try:
                res = fn()
                return str(res) if res is not None else default
            except Exception:
                return default

        pkg_name = _safe(apk.get_package, "unknown.package")
        app_name = _safe(apk.get_app_name, "")
        v_code = _safe(apk.get_androidversion_code, "")
        v_name = _safe(apk.get_androidversion_name, "")
        min_sdk = _safe(apk.get_min_sdk_version, "")
        target_sdk = _safe(apk.get_target_sdk_version, "")
        main_act = _safe(apk.get_main_activity, "")

        # Extract declared and sensitive permissions
        try:
            declared_perms = apk.get_permissions() or []
        except Exception:
            declared_perms = []
        sens_perms = [p for p in declared_perms if p in SENSITIVE_PERMISSIONS]

        # Extract certificates
        cert_list: List[CertificateMetadata] = []
        try:
            certs = apk.get_certificates() or []
            for cert in certs:
                cert_list.append(
                    CertificateMetadata(
                        issuer=str(getattr(cert, "issuer", "")),
                        subject=str(getattr(cert, "subject", "")),
                        sha256_fingerprint=str(getattr(cert, "sha256", "")),
                        serial_number=str(getattr(cert, "serial_number", "")),
                    )
                )
        except Exception:
            pass

        # Extract embedded URLs and domains from files inside the APK zip
        embedded_urls: Set[str] = set()
        embedded_domains: Set[str] = set()
        url_pattern = re.compile(r"https?://([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(?:/[^\s\"'<>]*)?")

        try:
            with zipfile.ZipFile(io.BytesIO(apk_bytes), "r") as zf:
                total_decompressed = 0
                max_total_decompressed = 20 * 1024 * 1024  # 20 MB max cumulative decompressed
                max_entry_size = 5 * 1024 * 1024  # 5 MB max per entry

                # Inspect text/xml/dex assets up to first 30 files with zip bomb protection
                for info in zf.infolist()[:30]:
                    name = info.filename
                    # Path traversal guard for zip members
                    if ".." in name or name.startswith(("/", "\\")):
                        continue

                    if name.endswith((".xml", ".dex", ".json", ".txt", ".properties")):
                        # Guard against zip bombs (excessive uncompressed size or ratio)
                        if info.file_size > max_entry_size:
                            continue
                        if total_decompressed + info.file_size > max_total_decompressed:
                            break

                        try:
                            with zf.open(info) as entry_file:
                                data = entry_file.read(1024 * 1024)  # Read up to 1MB
                                total_decompressed += len(data)
                                content = data.decode("utf-8", errors="ignore")
                                for match in url_pattern.finditer(content):
                                    full_url = match.group(0)
                                    domain = match.group(1).lower()
                                    if len(embedded_urls) < 50:
                                        embedded_urls.add(full_url)
                                    if len(embedded_domains) < 50:
                                        embedded_domains.add(domain)
                        except Exception:
                            continue
        except Exception:
            pass

        # Impersonation and Brand Correlation
        best_brand_id = None
        best_brand_name = None
        max_sim = 0.0
        reasons: List[str] = []

        is_official_app = False
        if verified_brands:
            # First check for registered, verified official mobile applications
            for brand in verified_brands:
                for off_app in getattr(brand, "official_mobile_apps", []):
                    if off_app.is_verified and off_app.platform.upper() == "ANDROID" and off_app.app_identifier.lower() == pkg_name.lower():
                        is_official_app = True
                        best_brand_id = str(brand.brand_id)
                        best_brand_name = brand.display_name
                        reasons.append(
                            f"Package '{pkg_name}' matches verified official application for brand '{brand.display_name}'."
                        )
                        break
                if is_official_app:
                    break

            if not is_official_app:
                for brand in verified_brands:
                    b_name = brand.display_name.lower()
                    b_domain = brand.official_domain.lower()

                    # Compare against app name
                    sim_app = fuzz.partial_ratio(b_name, app_name.lower()) if app_name else 0.0
                    # Compare against package name
                    sim_pkg = fuzz.partial_ratio(b_name, pkg_name.lower())

                    sim = max(sim_app, sim_pkg)
                    if sim > max_sim:
                        max_sim = sim
                        best_brand_id = str(brand.brand_id)
                        best_brand_name = brand.display_name

        # Calculate Risk Score
        risk_score = 0.0

        if not is_official_app:
            if max_sim >= 85.0:
                risk_score += 45.0
                reasons.append(
                    f"Application name or package identifier strongly mimics verified brand '{best_brand_name}' ({max_sim:.1f}% similarity)."
                )
            elif max_sim >= 65.0:
                risk_score += 25.0
                reasons.append(
                    f"Moderate similarity ({max_sim:.1f}%) to verified brand '{best_brand_name}'."
                )

        if sens_perms:
            risk_score += min(len(sens_perms) * 10.0, 35.0)
            reasons.append(f"Requests {len(sens_perms)} high-risk permissions: {', '.join(sens_perms[:5])}.")

        if not cert_list:
            risk_score += 15.0
            reasons.append("Missing or unverified signing certificate metadata.")

        risk_score = min(max(risk_score, 0.0), 100.0)

        if risk_score >= 80.0:
            risk_level = "CRITICAL"
        elif risk_score >= 55.0:
            risk_level = "HIGH"
        elif risk_score >= 25.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return APKAnalysisResult(
            file_name=file_name,
            file_size_bytes=len(apk_bytes),
            sha256_hash=sha256_hex,
            md5_hash=md5_hex,
            is_valid_apk=True,
            package_name=pkg_name,
            app_name=app_name,
            version_code=v_code,
            version_name=v_name,
            min_sdk=min_sdk,
            target_sdk=target_sdk,
            main_activity=main_act,
            declared_permissions=declared_perms,
            sensitive_permissions=sens_perms,
            certificates=cert_list,
            embedded_urls=sorted(list(embedded_urls)),
            embedded_domains=sorted(list(embedded_domains)),
            matched_brand_id=best_brand_id,
            matched_brand_name=best_brand_name,
            impersonation_score=round(max_sim, 2),
            risk_score=round(risk_score, 2),
            risk_level=risk_level,
            analysis_reasons=reasons,
        )
