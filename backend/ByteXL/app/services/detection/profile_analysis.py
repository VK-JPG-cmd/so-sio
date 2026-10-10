"""
Social Profile Threat Analysis Service.
Evaluates potential brand impersonation, fake customer support accounts,
and profile spoofing using customer-submitted or authorized platform data.

Core Invariant: Missing profile fields (e.g. missing bio, absence of external links)
must NOT automatically increase the risk score.
"""

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from rapidfuzz import fuzz
from app.core.logging import get_logger
from app.services.detection.brand_intelligence import VerifiedBrandProfile
from app.services.detection.homoglyphs import HomoglyphDetector

logger = get_logger("app.services.detection.profile_analysis")

SUPPORT_IMPERSONATION_TERMS = [
    "official support", "customer care", "helpdesk", "official account",
    "support team", "security team", "verified support", "live help",
    "official customer support", "customer support",
]


class SocialProfileInput(BaseModel):
    """Profile data submitted by a customer or retrieved from an authorized source."""

    platform: str = Field(..., description="Target platform (e.g. Twitter, Instagram, LinkedIn, Telegram)")
    username: str = Field(..., description="Account username or handle (e.g. @acme_support)")
    display_name: Optional[str] = None
    bio: Optional[str] = None
    profile_url: Optional[str] = None
    external_links: List[str] = Field(default_factory=list)
    avatar_hash: Optional[str] = None


class ProfileAnalysisResult(BaseModel):
    """Detailed impersonation and spoofing assessment of a social profile."""

    platform: str
    username: str
    display_name: Optional[str] = None

    matched_brand_id: Optional[str] = None
    matched_brand_name: Optional[str] = None

    is_official_account: bool = False
    username_similarity: float = Field(0.0, ge=0.0, le=100.0)
    display_name_similarity: float = Field(0.0, ge=0.0, le=100.0)
    has_homoglyph_username: bool = False
    canonical_username: Optional[str] = None

    # Specific indicators
    profile_link_mismatch: bool = False
    bio_impersonation_detected: bool = False
    suspicious_external_links: List[str] = Field(default_factory=list)
    reused_brand_image: bool = False

    risk_score: float = Field(0.0, ge=0.0, le=100.0)
    risk_level: str = "LOW"
    analysis_reasons: List[str] = Field(default_factory=list)


class ProfileAnalysisService:
    """Service detecting social media account impersonation against verified brands."""

    def analyze_profile(
        self,
        profile: SocialProfileInput,
        verified_brands: Optional[List[VerifiedBrandProfile]] = None,
    ) -> ProfileAnalysisResult:
        """
        Analyze social profile indicators against verified brand intelligence.
        Safeguard: Omitting optional fields does NOT penalize or increase risk.
        Recognizes registered official brand accounts to eliminate false positives.
        """
        clean_user = profile.username.lstrip("@").strip().lower()
        has_homo, canon_user, _ = HomoglyphDetector.analyze_string(clean_user)

        best_brand_id = None
        best_brand_name = None
        max_user_sim = 0.0
        max_name_sim = 0.0
        reasons: List[str] = []

        # 1. Official Account Recognition Check
        # Qualifies when exact normalized handle matches a registered official handle and has no homoglyphs.
        matching_official_brand: Optional[VerifiedBrandProfile] = None
        if verified_brands and not has_homo:
            for brand in verified_brands:
                norm_official_handles = {
                    h.lstrip("@").strip().lower() for h in brand.known_social_handles
                }
                if clean_user in norm_official_handles:
                    matching_official_brand = brand
                    best_brand_id = str(brand.brand_id)
                    best_brand_name = brand.display_name
                    max_user_sim = 100.0
                    if profile.display_name:
                        max_name_sim = float(
                            fuzz.token_set_ratio(
                                profile.display_name.lower(), brand.display_name.lower()
                            )
                        )
                    break

        # 2. Similarity analysis for non-official / unregistered accounts
        if not matching_official_brand and verified_brands:
            for brand in verified_brands:
                # Username similarity to official handles
                for official_handle in brand.known_social_handles:
                    sim = fuzz.ratio(clean_user, official_handle.lower())
                    if has_homo:
                        sim = max(sim, fuzz.ratio(canon_user.lower(), official_handle.lower()))
                    if sim > max_user_sim:
                        max_user_sim = sim
                        best_brand_id = str(brand.brand_id)
                        best_brand_name = brand.display_name

                # Compare against display name as well
                name_sim = fuzz.partial_ratio(clean_user, brand.display_name.lower())
                if name_sim > max_user_sim:
                    max_user_sim = max(max_user_sim, name_sim)
                    best_brand_id = str(brand.brand_id)
                    best_brand_name = brand.display_name

                # Display Name similarity (if supplied)
                if profile.display_name:
                    disp_sim = fuzz.token_set_ratio(
                        profile.display_name.lower(), brand.display_name.lower()
                    )
                    if disp_sim > max_name_sim:
                        max_name_sim = disp_sim
                        best_brand_id = str(brand.brand_id)
                        best_brand_name = brand.display_name

        # 3. Bio Impersonation Analysis (only if bio is provided)
        bio_impersonation = False
        if profile.bio and verified_brands:
            lower_bio = profile.bio.lower()
            if any(term in lower_bio for term in SUPPORT_IMPERSONATION_TERMS):
                for brand in verified_brands:
                    # Legitimate official accounts stating customer support/status for their own brand is authorized
                    if matching_official_brand and str(matching_official_brand.brand_id) == str(brand.brand_id):
                        continue

                    brand_name_lower = brand.display_name.lower()
                    cleaned_brand_name = re.sub(
                        r"\b(corp|inc|ltd|llc|co|corporation|company)\b", "", brand_name_lower
                    ).strip()
                    has_brand_ref = (
                        brand_name_lower in lower_bio
                        or (len(cleaned_brand_name) > 2 and cleaned_brand_name in lower_bio)
                        or any(kw.lower() in lower_bio for kw in brand.approved_keywords if len(kw) > 2)
                        or fuzz.partial_ratio(brand_name_lower, lower_bio) >= 80
                    )
                    if has_brand_ref:
                        bio_impersonation = True
                        if not best_brand_id:
                            best_brand_id = str(brand.brand_id)
                            best_brand_name = brand.display_name
                        reasons.append(
                            f"Bio claims official customer support/status for brand '{brand.display_name}'."
                        )
                        break

        # 4. Profile Link & External Links Mismatch (only if external links provided)
        link_mismatch = False
        suspicious_links: List[str] = []
        if profile.external_links and verified_brands:
            for link in profile.external_links:
                link_lower = link.lower()
                if matching_official_brand:
                    # When links are present, official account should point to official domain
                    official = matching_official_brand.official_domain.lower()
                    if official not in link_lower:
                        link_mismatch = True
                        suspicious_links.append(link)
                        reasons.append(
                            f"External link '{link}' does not point to official domain '{official}'."
                        )
                else:
                    for brand in verified_brands:
                        official = brand.official_domain.lower()
                        brand_keywords = brand.approved_keywords or [
                            w.lower() for w in brand.display_name.split() if len(w) > 2
                        ]
                        has_brand_ref = any(kw.lower() in link_lower for kw in brand_keywords if len(kw) > 2)
                        if has_brand_ref and official not in link_lower:
                            link_mismatch = True
                            suspicious_links.append(link)
                            reasons.append(
                                f"External link '{link}' references brand but does not point to official domain '{official}'."
                            )

        # 5. Reused Image / Avatar (only if avatar_hash is provided)
        reused_image = False
        if profile.avatar_hash and verified_brands:
            for brand in verified_brands:
                # Official accounts using their own registered brand logo is authorized
                if matching_official_brand and str(matching_official_brand.brand_id) == str(brand.brand_id):
                    continue
                if profile.avatar_hash in brand.logo_hashes:
                    reused_image = True
                    reasons.append(f"Profile avatar hash matches official registered logo of '{brand.display_name}'.")

        # 6. Calculate Composite Risk Score
        risk_score = 0.0
        is_official = matching_official_brand is not None

        if is_official:
            # Recognized Official Account:
            # Do NOT add impersonation penalty for matching username or display name
            if not link_mismatch and not bio_impersonation and not reused_image:
                risk_score = 0.0
                risk_level = "BENIGN"
                reasons.append(
                    f"Account handle is the verified official social account for brand '{matching_official_brand.display_name}'."
                )
            else:
                reasons.append(
                    f"Account handle matches registered official account for brand '{matching_official_brand.display_name}', but suspicious indicators were detected."
                )
                if link_mismatch:
                    risk_score += 25.0
                if bio_impersonation:
                    risk_score += 25.0
                if reused_image:
                    risk_score += 30.0

                risk_score = min(max(risk_score, 0.0), 100.0)
                if risk_score >= 80.0:
                    risk_level = "CRITICAL"
                elif risk_score >= 55.0:
                    risk_level = "HIGH"
                elif risk_score >= 25.0:
                    risk_level = "MEDIUM"
                else:
                    risk_level = "LOW"
        else:
            # Unregistered candidate profile: evaluate standard impersonation signals
            if has_homo and max_user_sim >= 70.0:
                risk_score += 40.0
                reasons.append(f"Username contains lookalike homoglyphs imitating '{canon_user}'.")

            if max_user_sim >= 85.0:
                risk_score += 35.0
                reasons.append(f"High username similarity ({max_user_sim:.1f}%) to brand '{best_brand_name}'.")
            elif max_user_sim >= 65.0:
                risk_score += 20.0
                reasons.append(f"Moderate username resemblance ({max_user_sim:.1f}%) to brand '{best_brand_name}'.")

            if max_name_sim >= 85.0:
                risk_score += 25.0
                reasons.append(f"Display name strongly resembles verified brand '{best_brand_name}'.")

            if bio_impersonation:
                risk_score += 25.0

            if link_mismatch:
                risk_score += 25.0

            if reused_image:
                risk_score += 30.0

            risk_score = min(max(risk_score, 0.0), 100.0)

            if risk_score >= 80.0:
                risk_level = "CRITICAL"
            elif risk_score >= 55.0:
                risk_level = "HIGH"
            elif risk_score >= 25.0:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"

        return ProfileAnalysisResult(
            platform=profile.platform,
            username=profile.username,
            display_name=profile.display_name,
            matched_brand_id=best_brand_id,
            matched_brand_name=best_brand_name,
            is_official_account=is_official,
            username_similarity=round(max_user_sim, 2),
            display_name_similarity=round(max_name_sim, 2),
            has_homoglyph_username=has_homo,
            canonical_username=canon_user if has_homo else None,
            profile_link_mismatch=link_mismatch,
            bio_impersonation_detected=bio_impersonation,
            suspicious_external_links=suspicious_links,
            reused_brand_image=reused_image,
            risk_score=round(risk_score, 2),
            risk_level=risk_level,
            analysis_reasons=reasons,
        )
