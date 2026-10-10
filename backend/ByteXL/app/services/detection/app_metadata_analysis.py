"""
App Store Listing Metadata Analysis Service.
Compares candidate mobile application listing metadata against verified brand official mobile assets.
Evaluates application name similarity, package identifiers, publisher authenticity,
description claims, store listing URLs, and visual trademarks using deterministic, explainable risk scoring.
"""

from datetime import datetime
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import uuid
from rapidfuzz import fuzz
from app.core.logging import get_logger
from app.models.enums import RiskSeverity
from app.schemas.app_metadata import (
    AppMetadataAnalysisRequest,
    AppMetadataAnalysisResponse,
    AppMetadataIndicator,
)
from app.services.detection.brand_intelligence import OfficialMobileAppProfile, VerifiedBrandProfile
from app.services.detection.homoglyphs import HomoglyphDetector
from app.services.scoring.config import (
    SCORING_METHODOLOGY_DISCLAIMER,
    SCORING_RULE_VERSION,
    STANDARD_RECOMMENDATIONS,
)
from app.services.scoring.engine import RiskScoringEngine, SignalItem, UnavailableSignal

logger = get_logger("app.services.detection.app_metadata_analysis")

MODIFIER_KEYWORDS = {
    "secure", "wallet", "support", "official", "login", "pay", "payments",
    "bank", "banking", "portal", "helpdesk", "online", "fast", "pro", "mobile",
    "app", "client", "auth", "verify", "security",
}

IMPERSONATION_CLAIM_REGEX = re.compile(
    r"\b(official(\s+mobile)?\s+app|official\s+support|authorized\s+by|official\s+account|"
    r"customer\s+(care|support|helpdesk)|verified\s+(app|application|service))\b",
    re.IGNORECASE,
)

CREDENTIAL_HARVEST_REGEX = re.compile(
    r"\b(enter\s+your\s+password|seed\s+phrase|private\s+key|credit\s+card|"
    r"pin\s+number|social\s+security|ssn|bank\s+account\s+password|2fa\s+code|otp\s+code|"
    r"master\s+key|recovery\s+phrase)\b",
    re.IGNORECASE,
)


class AppMetadataAnalysisService:
    """Service evaluating app-store listing metadata against verified brand intelligence."""

    def __init__(self, rule_version: str = SCORING_RULE_VERSION) -> None:
        self.rule_version = rule_version
        self.scoring_engine = RiskScoringEngine(rule_version=rule_version)

    def analyze_metadata(
        self,
        candidate: AppMetadataAnalysisRequest,
        brand: VerifiedBrandProfile,
    ) -> AppMetadataAnalysisResponse:
        """
        Execute deterministic, explainable metadata analysis.
        Does not execute APK code or fetch external URLs.
        """
        signals: List[SignalItem] = []
        unavailable_signals: List[UnavailableSignal] = []
        explanations: List[str] = []
        available_evidence: Dict[str, Any] = {
            "brand_id": str(brand.brand_id),
            "brand_name": brand.display_name,
            "candidate_app_name": candidate.app_name,
            "candidate_platform": candidate.platform,
            "candidate_app_identifier": candidate.app_identifier,
        }

        # ---------------------------------------------------------------------
        # 1. Check for Exact Match to Verified Official Mobile Application
        # ---------------------------------------------------------------------
        matched_official_app: Optional[OfficialMobileAppProfile] = None
        for off_app in brand.official_mobile_apps:
            if (
                off_app.is_verified
                and off_app.platform.upper() == candidate.platform.upper()
                and off_app.app_identifier.lower() == candidate.app_identifier.lower()
            ):
                # If candidate publisher is given, check if publisher matches
                if candidate.publisher_name:
                    if off_app.publisher_name.strip().lower() == candidate.publisher_name.strip().lower():
                        matched_official_app = off_app
                        break
                else:
                    matched_official_app = off_app
                    break

        is_official_match = matched_official_app is not None

        # ---------------------------------------------------------------------
        # 2. Application Name Similarity & Look-alikes
        # ---------------------------------------------------------------------
        clean_app_name = candidate.app_name.strip()
        has_homo, canon_name, _ = HomoglyphDetector.analyze_string(clean_app_name)
        brand_clean = brand.display_name.strip()

        # Compare with brand name and official app names
        max_name_sim = float(fuzz.token_set_ratio(clean_app_name.lower(), brand_clean.lower()))
        for off_app in brand.official_mobile_apps:
            sim = float(fuzz.token_set_ratio(clean_app_name.lower(), off_app.app_name.lower()))
            if sim > max_name_sim:
                max_name_sim = sim

        available_evidence["name_similarity_score"] = round(max_name_sim, 2)
        available_evidence["has_homoglyph_name"] = has_homo

        if not is_official_match:
            if has_homo:
                signals.append(
                    SignalItem(
                        category="DOMAIN_SIMILARITY",
                        signal_type="HOMOGLYPH_APP_NAME",
                        points=15.0,
                        description=f"Candidate application name '{clean_app_name}' contains Unicode homoglyph characters mimicking '{canon_name}'.",
                        evidence_context={"original": clean_app_name, "canonical": canon_name},
                    )
                )

            # Detect modifier keywords
            name_tokens = set(re.findall(r"\b[a-zA-Z]+\b", clean_app_name.lower()))
            brand_tokens = set(re.findall(r"\b[a-zA-Z]+\b", brand_clean.lower()))
            added_modifiers = (name_tokens - brand_tokens) & MODIFIER_KEYWORDS

            if max_name_sim >= 80.0:
                signals.append(
                    SignalItem(
                        category="DOMAIN_SIMILARITY",
                        signal_type="APP_NAME_IMPERSONATION",
                        points=20.0,
                        description=f"Candidate application name '{clean_app_name}' strongly mimics verified brand '{brand_clean}' ({max_name_sim:.1f}% similarity).",
                        evidence_context={"similarity": max_name_sim, "brand": brand_clean},
                    )
                )
            elif max_name_sim >= 60.0:
                signals.append(
                    SignalItem(
                        category="DOMAIN_SIMILARITY",
                        signal_type="MODERATE_APP_NAME_SIMILARITY",
                        points=10.0,
                        description=f"Candidate application name '{clean_app_name}' moderately resembles verified brand '{brand_clean}' ({max_name_sim:.1f}% similarity).",
                        evidence_context={"similarity": max_name_sim},
                    )
                )

            if added_modifiers and brand_clean.lower() in clean_app_name.lower():
                signals.append(
                    SignalItem(
                        category="DOMAIN_SIMILARITY",
                        signal_type="KEYWORD_IN_APP_NAME",
                        points=10.0,
                        description=f"Candidate application name incorporates brand '{brand_clean}' with security/modifier keywords: {', '.join(sorted(added_modifiers))}.",
                        evidence_context={"keywords": list(added_modifiers)},
                    )
                )

        # ---------------------------------------------------------------------
        # 3. Application Identifier (Package / Bundle ID) Comparison
        # ---------------------------------------------------------------------
        cand_id_lower = candidate.app_identifier.lower().strip()
        matched_official_pkg = any(
            cand_id_lower == off.app_identifier.lower().strip() for off in brand.official_mobile_apps if off.is_verified
        )

        if not is_official_match:
            # Check package similarity against official packages using component-aware matching
            from app.core.normalization import extract_package_components
            from app.services.detection.similarity import GENERIC_PACKAGE_PREFIXES

            pkg_sim = 0.0
            brand_token = brand.display_name.lower().replace(" ", "").replace("-", "")
            pkg_components = extract_package_components(cand_id_lower)
            meaningful_components = [c for c in pkg_components if c not in GENERIC_PACKAGE_PREFIXES]

            brand_in_pkg = any(
                brand_token == c or c.startswith(brand_token) or c.endswith(brand_token)
                for c in meaningful_components
            ) or any(
                kw.lower() in meaningful_components for kw in brand.approved_keywords if len(kw) > 2
            )

            for off in brand.official_mobile_apps:
                off_id = off.app_identifier.lower().strip()
                off_comps = [c for c in extract_package_components(off_id) if c not in GENERIC_PACKAGE_PREFIXES]
                # Compare non-generic components
                cand_sub = ".".join(meaningful_components)
                off_sub = ".".join(off_comps)
                sim = float(fuzz.ratio(cand_sub, off_sub))
                if sim > pkg_sim:
                    pkg_sim = sim

            available_evidence["package_similarity_score"] = round(pkg_sim, 2)

            if matched_official_pkg:
                # Same package identifier but publisher mismatch (unauthorized duplicate listing)
                signals.append(
                    SignalItem(
                        category="DOMAIN_SIMILARITY",
                        signal_type="PACKAGE_IDENTIFIER_UNVERIFIED_LISTING",
                        points=20.0,
                        description=f"Candidate uses registered package identifier '{candidate.app_identifier}' under an unverified publisher.",
                    )
                )
            elif brand_in_pkg or pkg_sim >= 70.0:
                signals.append(
                    SignalItem(
                        category="DOMAIN_SIMILARITY",
                        signal_type="SIMILAR_PACKAGE_IDENTIFIER",
                        points=15.0,
                        description=f"Package identifier '{candidate.app_identifier}' mimics official brand naming structure ({pkg_sim:.1f}% resemblance).",
                        evidence_context={"package": candidate.app_identifier, "similarity": pkg_sim},
                    )
                )

        # ---------------------------------------------------------------------
        # 4. Publisher / Developer Name Analysis
        # ---------------------------------------------------------------------
        if candidate.publisher_name and candidate.publisher_name.strip():
            cand_pub = candidate.publisher_name.strip()
            available_evidence["publisher_name"] = cand_pub
            official_pubs = {
                off.publisher_name.strip().lower() for off in brand.official_mobile_apps if off.publisher_name
            }

            if not is_official_match:
                has_brand_resemblance = (
                    max_name_sim >= 60.0
                    or brand_in_pkg
                    or matched_official_pkg
                    or (candidate.description and brand_clean.lower() in candidate.description.lower())
                )
                if has_brand_resemblance and official_pubs and cand_pub.lower() not in official_pubs:
                    signals.append(
                        SignalItem(
                            category="SCAM_AND_CREDENTIAL_HARVESTING",
                            signal_type="PUBLISHER_MISMATCH",
                            points=15.0,
                            description=f"Publisher '{cand_pub}' differs from registered official publisher for '{brand_clean}'.",
                            evidence_context={"candidate_publisher": cand_pub, "official_publishers": list(official_pubs)},
                        )
                    )
                elif brand_clean.lower() in cand_pub.lower():
                    signals.append(
                        SignalItem(
                            category="SCAM_AND_CREDENTIAL_HARVESTING",
                            signal_type="PUBLISHER_NAME_IMPERSONATION",
                            points=10.0,
                            description=f"Publisher '{cand_pub}' references verified brand '{brand_clean}' without registered official publisher record.",
                        )
                    )
        else:
            unavailable_signals.append(
                UnavailableSignal(
                    category="SCAM_AND_CREDENTIAL_HARVESTING",
                    reason="No publisher or developer name provided in candidate metadata.",
                )
            )

        # ---------------------------------------------------------------------
        # 5. Store Listing Description Analysis
        # ---------------------------------------------------------------------
        if candidate.description and candidate.description.strip():
            desc_text = candidate.description.strip()
            available_evidence["description_analyzed"] = True

            has_impersonation_claim = bool(IMPERSONATION_CLAIM_REGEX.search(desc_text))
            has_credential_harvest = bool(CREDENTIAL_HARVEST_REGEX.search(desc_text))

            if has_credential_harvest:
                signals.append(
                    SignalItem(
                        category="SCAM_AND_CREDENTIAL_HARVESTING",
                        signal_type="CREDENTIAL_HARVESTING_LURE",
                        points=25.0,
                        description="Application description solicits passwords, PINs, seed phrases, or private security credentials.",
                    )
                )

            if not is_official_match and has_impersonation_claim:
                signals.append(
                    SignalItem(
                        category="SCAM_AND_CREDENTIAL_HARVESTING",
                        signal_type="DESCRIPTION_IMPERSONATION_CLAIM",
                        points=15.0,
                        description=f"Description explicitly claims official representation or customer care status for brand '{brand_clean}'.",
                    )
                )
        else:
            unavailable_signals.append(
                UnavailableSignal(
                    category="SCAM_AND_CREDENTIAL_HARVESTING",
                    reason="No application description provided in candidate metadata.",
                )
            )

        # ---------------------------------------------------------------------
        # 6. Store Listing URL & Platform Host Verification
        # ---------------------------------------------------------------------
        if candidate.store_url and candidate.store_url.strip():
            available_evidence["store_url"] = candidate.store_url
            parsed = urlparse(candidate.store_url)
            host = parsed.netloc.lower().split(":")[0] if ":" in parsed.netloc else parsed.netloc.lower()

            if candidate.platform.upper() == "ANDROID":
                if not (host == "play.google.com" or host.endswith(".play.google.com") or host == "market.android.com"):
                    signals.append(
                        SignalItem(
                            category="REDIRECT_AND_INFRASTRUCTURE",
                            signal_type="STORE_URL_HOST_MISMATCH",
                            points=10.0,
                            description=f"Declared Android store URL host '{host}' does not match official Google Play store domain ('play.google.com').",
                            evidence_context={"host": host, "expected": "play.google.com"},
                        )
                    )
            elif candidate.platform.upper() == "IOS":
                if not (host == "apps.apple.com" or host.endswith(".apps.apple.com") or host == "itunes.apple.com"):
                    signals.append(
                        SignalItem(
                            category="REDIRECT_AND_INFRASTRUCTURE",
                            signal_type="STORE_URL_HOST_MISMATCH",
                            points=10.0,
                            description=f"Declared iOS store URL host '{host}' does not match official Apple App Store domain ('apps.apple.com').",
                            evidence_context={"host": host, "expected": "apps.apple.com"},
                        )
                    )
        else:
            unavailable_signals.append(
                UnavailableSignal(
                    category="REDIRECT_AND_INFRASTRUCTURE",
                    reason="No store listing URL provided in candidate metadata.",
                )
            )

        # ---------------------------------------------------------------------
        # 7. Logo Perceptual Hash Analysis
        # ---------------------------------------------------------------------
        if candidate.logo_hash and candidate.logo_hash.strip():
            available_evidence["logo_hash"] = candidate.logo_hash
            if not is_official_match and candidate.logo_hash in brand.logo_hashes:
                signals.append(
                    SignalItem(
                        category="VISUAL_SIMILARITY",
                        signal_type="UNAUTHORIZED_LOGO_REUSE",
                        points=20.0,
                        description=f"Application icon hash matches registered trademark logo of brand '{brand_clean}'.",
                    )
                )
        else:
            unavailable_signals.append(
                UnavailableSignal(
                    category="VISUAL_SIMILARITY",
                    reason="No application logo hash provided for visual comparison.",
                )
            )

        # Threat Intelligence Category marked unavailable for metadata inspection
        unavailable_signals.append(
            UnavailableSignal(
                category="THREAT_INTELLIGENCE",
                reason="App store listing metadata not directly indexed in infrastructure threat feeds.",
            )
        )

        # ---------------------------------------------------------------------
        # 8. Composite Risk Score Calculation
        # ---------------------------------------------------------------------
        if is_official_match:
            # Check for independent malicious behaviors (e.g. credential harvesting in description)
            independent_suspicious_signals = [
                s for s in signals if s.signal_type in ("CREDENTIAL_HARVESTING_LURE", "STORE_URL_HOST_MISMATCH")
            ]
            if not independent_suspicious_signals:
                # Fully clean official match
                risk_score = 0.0
                severity = RiskSeverity.LOW
                assessment_status = "OFFICIAL_ASSET_MATCH"
                explanations.append(
                    f"Candidate application matches verified official mobile application '{matched_official_app.app_name}' for brand '{brand_clean}'."
                )
                recommendations = [STANDARD_RECOMMENDATIONS["ROUTINE_MONITORING"]]
                scoring_result_indicators: List[AppMetadataIndicator] = []
            else:
                # Official package with compromised/malicious description or store link
                scoring_result = self.scoring_engine.evaluate_signals(
                    signals=independent_suspicious_signals,
                    unavailable_signals=unavailable_signals,
                )
                risk_score = scoring_result.risk_score
                severity = scoring_result.severity
                assessment_status = "NEEDS_INVESTIGATION"
                explanations.append(
                    f"Application matches official package identifier, but independent suspicious signals require investigation."
                )
                recommendations = scoring_result.recommendations
                scoring_result_indicators = [
                    AppMetadataIndicator(
                        category=s.category,
                        signal_type=s.signal_type,
                        points=s.points,
                        description=s.description,
                        evidence_context=s.evidence_context,
                    )
                    for s in independent_suspicious_signals
                ]
        else:
            # Non-official candidate evaluation
            scoring_result = self.scoring_engine.evaluate_signals(
                signals=signals,
                unavailable_signals=unavailable_signals,
            )
            risk_score = scoring_result.risk_score
            severity = scoring_result.severity

            # Determine assessment status
            if risk_score >= 60.0:
                assessment_status = "LIKELY_IMPERSONATION"
            elif risk_score >= 25.0:
                assessment_status = "NEEDS_INVESTIGATION"
            elif max_name_sim == 0.0 and len(signals) == 0:
                assessment_status = "BENIGN_UNRELATED"
            elif len(signals) == 0 and len(unavailable_signals) >= 3:
                assessment_status = "INSUFFICIENT_INFORMATION" if max_name_sim > 0.0 else "BENIGN_UNRELATED"
            else:
                assessment_status = "BENIGN_UNRELATED"

            for s in signals:
                explanations.append(s.description)

            if not signals:
                explanations.append(
                    f"Candidate application shows no significant technical resemblance or malicious indicators targeting brand '{brand_clean}'."
                )

            recommendations = scoring_result.recommendations
            scoring_result_indicators = [
                AppMetadataIndicator(
                    category=s.category,
                    signal_type=s.signal_type,
                    points=s.points,
                    description=s.description,
                    evidence_context=s.evidence_context,
                )
                for s in signals
            ]

        missing_records = [{"category": u.category, "reason": u.reason} for u in unavailable_signals]

        return AppMetadataAnalysisResponse(
            brand_id=brand.brand_id,
            brand_name=brand.display_name,
            candidate_app_name=candidate.app_name,
            platform=candidate.platform,
            app_identifier=candidate.app_identifier,
            publisher_name=candidate.publisher_name,
            store_url=candidate.store_url,
            description=candidate.description,
            matched_official_app_id=matched_official_app.id if matched_official_app else None,
            is_official_match=is_official_match,
            assessment_status=assessment_status,
            risk_score=risk_score,
            severity=severity,
            model_version=self.rule_version,
            contributing_indicators=scoring_result_indicators,
            explanations=explanations,
            available_evidence=available_evidence,
            missing_signals=missing_records,
            recommended_actions=recommendations,
            assessment_timestamp=datetime.utcnow(),
        )
