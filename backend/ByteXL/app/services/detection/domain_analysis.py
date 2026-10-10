"""
Domain Analysis Service.
Performs modular threat detection on domain names using:
- Public Suffix List (PSL) extraction via tldextract
- RapidFuzz string similarity metrics
- Homoglyph & Unicode confusable detection
- Suspicious brand keyword correlation
- Threat intelligence feed lookups
- Safe DNS observation recording
"""

from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field
from rapidfuzz import fuzz
import tldextract
from app.core.domain import normalize_domain
from app.core.logging import get_logger
from app.services.detection.brand_intelligence import VerifiedBrandProfile
from app.services.detection.homoglyphs import HomoglyphDetector

logger = get_logger("app.services.detection.domain_analysis")

# Known phishing and credential harvesting keywords
SUSPICIOUS_KEYWORDS: Set[str] = {
    "login", "signin", "sign-in", "log-in", "verify", "verification",
    "account", "secure", "security", "update", "banking", "support",
    "helpdesk", "wallet", "portal", "auth", "authorize", "recover",
    "recovery", "confirm", "confirmation", "billing", "payment", "alert",
    "service", "official", "direct", "online", "customer"
}

# Default known malicious domains for threat intelligence lookup
DEFAULT_THREAT_INTEL_DB: Set[str] = {
    "malicious-phish-kit.com",
    "bad-actor-c2.net",
    "known-credential-stealer.org",
    "fake-login-harvest.xyz",
    "scam-airdrop-claim.top",
}


class DomainAnalysisResult(BaseModel):
    """Structured outcome of multi-layered domain threat analysis."""

    raw_domain: str
    normalized_domain: str
    registrable_domain: str
    subdomain: str
    suffix: str

    # Similarity and brand correlation
    matched_brand_id: Optional[str] = None
    matched_brand_name: Optional[str] = None
    similarity_score: float = Field(0.0, description="Highest similarity score from 0.0 to 100.0")
    is_exact_match: bool = False
    is_official_domain: bool = False

    # Detection indicators
    has_homoglyphs: bool = False
    canonical_ascii_domain: Optional[str] = None
    homoglyphs_detected: List[Dict[str, str]] = Field(default_factory=list)
    has_mixed_script: bool = False

    suspicious_keywords_found: List[str] = Field(default_factory=list)
    threat_intel_match: bool = False
    threat_intel_details: Optional[str] = None

    # Overall risk score (0 to 100) and risk level
    risk_score: float = Field(0.0, ge=0.0, le=100.0)
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    analysis_reasons: List[str] = Field(default_factory=list)


class DomainAnalysisService:
    """Modular analysis engine for domain threat intelligence and impersonation detection."""

    def __init__(self, threat_intel_feed: Optional[Set[str]] = None) -> None:
        self.threat_intel = threat_intel_feed or DEFAULT_THREAT_INTEL_DB
        # Configure tldextract without automatic network download to ensure deterministic offline execution
        self.extractor = tldextract.TLDExtract(cache_dir=None)

    def analyze_domain(
        self,
        domain_string: str,
        verified_brands: Optional[List[VerifiedBrandProfile]] = None,
    ) -> DomainAnalysisResult:
        """
        Execute comprehensive threat analysis on a target domain against verified brand intelligence.
        """
        # 1. Normalize domain
        try:
            normalized = normalize_domain(domain_string)
        except Exception:
            normalized = domain_string.strip().lower()

        # 2. Extract registrable domain using maintained Public Suffix List
        ext = self.extractor(normalized)
        if hasattr(ext, "top_domain_under_public_suffix"):
            registrable = ext.top_domain_under_public_suffix or normalized
        else:
            registrable = ext.registered_domain or normalized
        subdomain = ext.subdomain
        suffix = ext.suffix

        # 3. Homoglyph & Unicode confusable analysis
        has_homo, canonical_ascii, detected_homos = HomoglyphDetector.analyze_string(normalized)
        has_mixed = HomoglyphDetector.detect_mixed_script(normalized)

        # 4. Keyword analysis
        clean_text_for_keywords = normalized.replace(".", "-").split("-")
        keywords_found = [
            kw for kw in clean_text_for_keywords if kw in SUSPICIOUS_KEYWORDS
        ]

        # 5. Threat Intelligence Feed check
        in_threat_intel = (
            normalized in self.threat_intel or registrable in self.threat_intel
        )

        # 6. Brand similarity comparison using RapidFuzz
        best_brand_id = None
        best_brand_name = None
        highest_score = 0.0
        is_exact = False
        is_official = False
        reasons: List[str] = []

        if verified_brands:
            for brand in verified_brands:
                official = brand.official_domain.lower()
                if normalized == official:
                    is_official = True
                    best_brand_id = str(brand.brand_id)
                    best_brand_name = brand.display_name
                    highest_score = 100.0
                    is_exact = True
                    reasons.append(f"Domain is the official verified domain for {brand.display_name}.")
                    break

                # Extract brand SLD (second-level domain) with fallback for test TLDs (.example, .test)
                brand_ext = self.extractor(official)
                if brand_ext.suffix:
                    brand_sld = brand_ext.domain.lower()
                else:
                    brand_sld = brand_ext.subdomain.lower() if brand_ext.subdomain else brand_ext.domain.lower()

                if ext.suffix:
                    target_sld = ext.domain.lower()
                else:
                    target_sld = ext.subdomain.lower() if ext.subdomain else ext.domain.lower()

                # Also consider brand display name as an authoritative SLD reference
                clean_brand_name = brand.display_name.lower().replace(" ", "").replace("-", "")

                # Calculate RapidFuzz similarities against target domain and canonical ASCII
                score_full = fuzz.ratio(normalized, official)
                score_sld = fuzz.ratio(target_sld, brand_sld)
                score_token_set = fuzz.token_set_ratio(target_sld, brand_sld)

                # Check canonical homoglyph variation against brand SLD
                if has_homo:
                    canon_ext = self.extractor(canonical_ascii)
                    canon_sld = canon_ext.domain.lower()
                    score_homo_sld = fuzz.ratio(canon_sld, brand_sld)
                    score_homo_token = fuzz.token_set_ratio(canon_sld, brand_sld)
                    score_sld = max(score_sld, score_homo_sld)
                    score_token_set = max(score_token_set, score_homo_token)

                # If brand SLD is present as a token or substring in target SLD (e.g. acmebank-login)
                brand_in_domain = (
                    brand_sld in target_sld
                    or clean_brand_name in target_sld
                    or (has_homo and (brand_sld in canonical_ascii or clean_brand_name in canonical_ascii))
                )
                if brand_in_domain:
                    max_brand_score = max(score_full, score_sld, score_token_set, 85.0)
                elif score_sld >= 60.0:
                    max_brand_score = max(score_full, score_sld)
                elif score_full >= 60.0:
                    max_brand_score = score_full
                else:
                    # Unrelated domain: do not let partial_ratio create false correlation floors
                    max_brand_score = min(score_sld, 40.0)

                if max_brand_score > highest_score and (max_brand_score >= 60.0 or brand_in_domain):
                    highest_score = max_brand_score
                    best_brand_id = str(brand.brand_id)
                    best_brand_name = brand.display_name

        # 7. Calculate composite risk score
        risk_score = 0.0

        if is_official:
            if in_threat_intel:
                risk_score = 90.0
                risk_level = "CRITICAL"
                reasons.append("Official verified brand domain is listed in active threat intelligence feed (potential domain hijacking or compromise).")
            else:
                risk_score = 0.0
                risk_level = "BENIGN"
        else:
            if in_threat_intel:
                risk_score += 90.0
                reasons.append("Domain matches active threat intelligence feed (known malicious IOC).")

            if has_homo:
                risk_score += 40.0
                reasons.append(
                    f"Visual homoglyphs detected ({len(detected_homos)} lookalike characters). "
                    f"Decodes to lookalike: '{canonical_ascii}'"
                )

            if has_mixed:
                risk_score += 25.0
                reasons.append("Mixed Unicode scripts detected (common in IDN spoofing attacks).")

            if highest_score >= 80.0:
                risk_score += 35.0
                reasons.append(
                    f"High domain lexical similarity ({highest_score:.1f}%) to verified brand '{best_brand_name}'."
                )
            elif highest_score >= 60.0:
                risk_score += 15.0
                reasons.append(
                    f"Moderate similarity ({highest_score:.1f}%) to verified brand '{best_brand_name}'."
                )

            if keywords_found:
                risk_score += min(len(keywords_found) * 15.0, 30.0)
                reasons.append(f"Suspicious security/phishing keywords present: {', '.join(keywords_found)}.")

            # Bound risk score between 0 and 100
            risk_score = min(max(risk_score, 0.0), 100.0)

            if risk_score >= 80.0:
                risk_level = "CRITICAL"
            elif risk_score >= 55.0:
                risk_level = "HIGH"
            elif risk_score >= 25.0:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"

        return DomainAnalysisResult(
            raw_domain=domain_string,
            normalized_domain=normalized,
            registrable_domain=registrable,
            subdomain=subdomain,
            suffix=suffix,
            matched_brand_id=best_brand_id,
            matched_brand_name=best_brand_name,
            similarity_score=highest_score,
            is_exact_match=is_exact,
            is_official_domain=is_official,
            has_homoglyphs=has_homo,
            canonical_ascii_domain=canonical_ascii if has_homo else None,
            homoglyphs_detected=detected_homos,
            has_mixed_script=has_mixed,
            suspicious_keywords_found=keywords_found,
            threat_intel_match=in_threat_intel,
            threat_intel_details="Identified in local threat intelligence repository" if in_threat_intel else None,
            risk_score=risk_score,
            risk_level=risk_level,
            analysis_reasons=reasons,
        )
