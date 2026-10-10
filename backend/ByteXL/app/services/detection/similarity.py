"""
Unified Look-Alike and String Similarity Detection Engine.
Provides deterministic, boundary-aware similarity metrics for:
- Application names & display names (homoglyphs, substitutions, modifiers, typos)
- Social media handles
- Android package identifiers (component-aware comparison)
- Domain names (registrable domain and Public Suffix List aware)

Critical Invariant: High string similarity alone does not prove maliciousness.
Unrelated legitimate entities must not receive elevated similarity scores.
"""

import re
from typing import Any, Dict, List, Optional, Set
from rapidfuzz import fuzz
from app.core.normalization import (
    decode_leetspeak,
    extract_package_components,
    normalize_text,
    normalize_unicode_text,
    tokenize_identifier,
)
from app.services.detection.homoglyphs import HomoglyphDetector

# Common brand-modifier terms frequently used in phishing and impersonation
STANDARD_MODIFIER_TERMS: Set[str] = {
    "official", "support", "helpdesk", "help", "care", "customer", "customercare",
    "secure", "security", "wallet", "login", "signin", "verify", "verification",
    "portal", "auth", "banking", "bank", "pay", "payments", "alert", "update",
    "service", "app", "mobile", "recovery", "recover", "online", "direct", "pro",
}

# Generic TLDs or top-level package namespaces that should NOT contribute to similarity
GENERIC_PACKAGE_PREFIXES: Set[str] = {
    "com", "org", "net", "io", "app", "co", "dev", "ai", "me", "tech", "us", "uk", "in",
}


def calculate_lookalike_similarity(
    candidate_text: str,
    target_text: str,
    target_keywords: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Calculate boundary-aware lookalike similarity between candidate and target text.
    Evaluates:
    - Exact match
    - Unicode homoglyphs / confusables
    - Leetspeak substitutions
    - Character additions, deletions, swaps, and typos
    - Added modifier keywords (e.g. 'AcmePay Support' or 'AcmePay Secure Wallet')
    - Prevents elevated scores on unrelated legitimate names
    """
    norm_cand = normalize_text(candidate_text)
    norm_target = normalize_text(target_text)

    if not norm_cand or not norm_target:
        return {
            "similarity_score": 0.0,
            "is_exact_match": False,
            "has_homoglyphs": False,
            "has_leetspeak": False,
            "has_modifiers": False,
            "detected_modifiers": [],
            "mutation_type": None,
            "explanation": "One or both input strings are empty.",
        }

    # 1. Exact match check
    if norm_cand == norm_target:
        return {
            "similarity_score": 100.0,
            "is_exact_match": True,
            "has_homoglyphs": False,
            "has_leetspeak": False,
            "has_modifiers": False,
            "detected_modifiers": [],
            "mutation_type": "EXACT_MATCH",
            "explanation": "Exact normalized string match.",
        }

    # 2. Homoglyph / Confusable analysis
    has_homo, canon_cand, detected_homos = HomoglyphDetector.analyze_string(norm_cand)
    norm_canon_cand = normalize_text(canon_cand)

    # 3. Leetspeak substitution check
    canon_leet_cand = decode_leetspeak(norm_canon_cand)
    has_leetspeak = canon_leet_cand != norm_canon_cand and canon_leet_cand == norm_target

    # 4. Tokenization and boundary analysis
    cand_tokens = tokenize_identifier(norm_cand)
    target_tokens = tokenize_identifier(norm_target)
    canon_cand_tokens = tokenize_identifier(norm_canon_cand)

    # Determine modifier keywords added to the target brand
    extra_tokens = set(canon_cand_tokens) - set(target_tokens)
    detected_modifiers = sorted(list(extra_tokens & STANDARD_MODIFIER_TERMS))

    # Check if target name appears as an entity in candidate tokens
    target_collapsed = "".join(target_tokens)
    cand_collapsed = "".join(cand_tokens)
    canon_cand_collapsed = "".join(canon_cand_tokens)

    brand_in_cand = (
        norm_target in norm_cand
        or target_collapsed in cand_collapsed
        or norm_target in norm_canon_cand
        or target_collapsed in canon_cand_collapsed
        or all(t in canon_cand_tokens for t in target_tokens)
    )

    # 5. Compute specialized similarity scores
    # Levenshtein ratio on canonical ASCII
    ratio_direct = float(fuzz.ratio(norm_cand, norm_target))
    ratio_canon = float(fuzz.ratio(norm_canon_cand, norm_target)) if has_homo else ratio_direct
    ratio_leet = float(fuzz.ratio(canon_leet_cand, norm_target)) if has_leetspeak else ratio_canon

    # Token set ratio handles word reordering and added modifiers
    token_set_sim = float(fuzz.token_set_ratio(norm_canon_cand, norm_target))

    # Base similarity score
    effective_ratio = max(ratio_direct, ratio_canon, ratio_leet)

    # Classify mutation and assign final calibrated similarity score
    mutation_type: Optional[str] = None
    similarity_score = 0.0

    if has_homo and (norm_canon_cand == norm_target or ratio_canon >= 95.0):
        mutation_type = "HOMOGLYPH_SPOOF"
        similarity_score = 100.0
    elif has_leetspeak and canon_leet_cand == norm_target:
        mutation_type = "LEETSPEAK_SUBSTITUTION"
        similarity_score = 95.0
    elif brand_in_cand and detected_modifiers:
        mutation_type = "MODIFIER_EXTENSION"
        # Modifier added to exact brand name (e.g. AcmePay Official / AcmePay Wallet)
        similarity_score = max(token_set_sim, 85.0)
    elif effective_ratio >= 85.0:
        mutation_type = "CHARACTER_MUTATION"  # typo, insertion, deletion, swap
        similarity_score = effective_ratio
    elif brand_in_cand and token_set_sim >= 75.0:
        mutation_type = "TOKEN_REORDER_OR_VARIATION"
        similarity_score = token_set_sim
    else:
        # Avoid artificial similarity floors for completely unrelated names
        # Check token overlap
        overlap = set(canon_cand_tokens) & set(target_tokens)
        if not overlap and effective_ratio < 65.0:
            similarity_score = min(effective_ratio, 30.0)
            mutation_type = "UNRELATED"
        else:
            similarity_score = effective_ratio
            mutation_type = "MODERATE_SIMILARITY" if effective_ratio >= 60.0 else "UNRELATED"

    return {
        "similarity_score": round(similarity_score, 2),
        "is_exact_match": False,
        "has_homoglyphs": has_homo,
        "homoglyphs_detected": detected_homos,
        "has_leetspeak": has_leetspeak,
        "has_modifiers": len(detected_modifiers) > 0,
        "detected_modifiers": detected_modifiers,
        "mutation_type": mutation_type,
        "canonical_text": norm_canon_cand if has_homo else norm_cand,
        "explanation": f"Evaluated as {mutation_type} with {similarity_score:.1f}% similarity.",
    }


def compare_package_identifiers(
    candidate_pkg: str,
    target_pkg: str,
    brand_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Component-aware comparison of application package identifiers (e.g. Android packages).
    Ignores generic top-level prefixes (e.g. 'com.') to prevent false positives.
    """
    cand_norm = normalize_text(candidate_pkg)
    target_norm = normalize_text(target_pkg)

    if not cand_norm or not target_norm:
        return {"similarity_score": 0.0, "is_exact_match": False, "is_lookalike": False}

    if cand_norm == target_norm:
        return {
            "similarity_score": 100.0,
            "is_exact_match": True,
            "is_lookalike": False,
            "explanation": "Exact package identifier match.",
        }

    cand_comps = extract_package_components(cand_norm)
    target_comps = extract_package_components(target_norm)

    # Strip generic prefix if both have it (e.g., 'com.')
    cand_meaningful = [c for c in cand_comps if c not in GENERIC_PACKAGE_PREFIXES]
    target_meaningful = [c for c in target_comps if c not in GENERIC_PACKAGE_PREFIXES]

    # Meaningful string representations
    cand_str = ".".join(cand_meaningful)
    target_str = ".".join(target_meaningful)

    if not cand_str or not target_str:
        return {"similarity_score": 0.0, "is_exact_match": False, "is_lookalike": False}

    # Check component-level lookalike
    # E.g. target is ['acmepay', 'wallet'], candidate is ['acmepay', 'wallet', 'scam']
    target_in_cand = all(c in cand_meaningful for c in target_meaningful)
    
    # Check if candidate has a lookalike brand component
    brand_tokens = tokenize_identifier(brand_name) if brand_name else []
    brand_clean = "".join(brand_tokens)

    brand_in_pkg = False
    if brand_clean:
        # Only match if brand appears as a component or clear prefix/suffix of a component
        brand_in_pkg = any(
            c == brand_clean or c.startswith(brand_clean) or c.endswith(brand_clean)
            for c in cand_meaningful
        )

    # Ratio on non-generic components
    comp_ratio = float(fuzz.ratio(cand_str, target_str))

    is_lookalike = False
    if target_in_cand and len(cand_meaningful) > len(target_meaningful):
        is_lookalike = True
        sim_score = max(comp_ratio, 80.0)
    elif comp_ratio >= 75.0 or (brand_in_pkg and comp_ratio >= 60.0):
        is_lookalike = True
        sim_score = comp_ratio
    else:
        # Unrelated package
        sim_score = min(comp_ratio, 40.0) if not brand_in_pkg else comp_ratio

    return {
        "similarity_score": round(sim_score, 2),
        "is_exact_match": False,
        "is_lookalike": is_lookalike,
        "target_components_present": target_in_cand,
        "brand_token_present": brand_in_pkg,
        "explanation": f"Package component comparison yielded {sim_score:.1f}% resemblance.",
    }
