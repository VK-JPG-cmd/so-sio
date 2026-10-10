"""
Unit tests for look-alike detection, false-positive reduction, and string similarity.
Verifies:
- Added characters (e.g. AcmePaay)
- Removed characters (e.g. AcmPay)
- Character swaps (e.g. AcmePya)
- Substitutions and leetspeak (e.g. 4cm3p@y)
- Hyphens, underscores, and spacing (e.g. Acme-Pay, acme_pay)
- Added modifier words (e.g. AcmePay Support, AcmePay Secure Wallet)
- Homoglyphs and Unicode confusables (e.g. Cyrillic АсmеPау)
- Unrelated legitimate entities (ensuring low similarity and no false flags)
- Android package component-aware comparisons
- Generic package prefixes (com.) do not trigger similarity
"""

import pytest
from app.services.detection.similarity import (
    calculate_lookalike_similarity,
    compare_package_identifiers,
)


def test_lookalike_exact_match() -> None:
    """Exact match returns 100.0% similarity with EXACT_MATCH mutation type."""
    res = calculate_lookalike_similarity("AcmePay", "AcmePay")
    assert res["is_exact_match"] is True
    assert res["similarity_score"] == 100.0
    assert res["mutation_type"] == "EXACT_MATCH"


def test_lookalike_added_character() -> None:
    """Extra character insertion (e.g. AcmePaay vs AcmePay) receives high ratio."""
    res = calculate_lookalike_similarity("AcmePaay", "AcmePay")
    assert res["is_exact_match"] is False
    assert res["similarity_score"] >= 88.0
    assert res["mutation_type"] == "CHARACTER_MUTATION"


def test_lookalike_removed_character() -> None:
    """Character deletion (e.g. AcmPay vs AcmePay) receives high ratio."""
    res = calculate_lookalike_similarity("AcmPay", "AcmePay")
    assert res["is_exact_match"] is False
    assert res["similarity_score"] >= 88.0
    assert res["mutation_type"] == "CHARACTER_MUTATION"


def test_lookalike_character_swap() -> None:
    """Character transposition (e.g. AcmePya vs AcmePay) receives high ratio."""
    res = calculate_lookalike_similarity("AcmePya", "AcmePay")
    assert res["is_exact_match"] is False
    assert res["similarity_score"] >= 85.0
    assert res["mutation_type"] == "CHARACTER_MUTATION"


def test_lookalike_hyphens_underscores_separators() -> None:
    """Separator variations (Acme-Pay, Acme_Pay, Acme Pay) receive high similarity."""
    for variant in ["Acme-Pay", "Acme_Pay", "Acme Pay"]:
        res = calculate_lookalike_similarity(variant, "AcmePay")
        assert res["similarity_score"] >= 88.0


def test_lookalike_added_modifier_keywords() -> None:
    """Brand name with added modifier words (Official, Support, Secure, Wallet)."""
    modifiers = [
        "AcmePay Support",
        "AcmePay Official",
        "AcmePay Secure Wallet",
        "AcmePay Customer Care",
        "AcmePay Login Portal",
    ]
    for candidate in modifiers:
        res = calculate_lookalike_similarity(candidate, "AcmePay")
        assert res["has_modifiers"] is True
        assert len(res["detected_modifiers"]) > 0
        assert res["similarity_score"] >= 85.0
        assert res["mutation_type"] == "MODIFIER_EXTENSION"


def test_lookalike_homoglyph_unicode_confusable() -> None:
    """Cyrillic lookalike characters (e.g. АсmеPау) decode to exact canonical text."""
    # Cyrillic A (U+0410), c (U+0441), e (U+0435), P (U+0420), a (U+0430), y (U+0443)
    cyrillic_acmepay = "\u0410\u0441m\u0435\u0420\u0430\u0443"
    res = calculate_lookalike_similarity(cyrillic_acmepay, "AcmePay")
    assert res["has_homoglyphs"] is True
    assert res["similarity_score"] == 100.0
    assert res["mutation_type"] == "HOMOGLYPH_SPOOF"


def test_lookalike_leetspeak_substitution() -> None:
    """Leetspeak numbers/symbols substituting letters (e.g. 4cm3p@y)."""
    res = calculate_lookalike_similarity("4cm3p@y", "AcmePay")
    assert res["has_leetspeak"] is True
    assert res["similarity_score"] >= 90.0
    assert res["mutation_type"] == "LEETSPEAK_SUBSTITUTION"


def test_unrelated_legitimate_entities_no_false_high_scores() -> None:
    """Unrelated names must receive low similarity scores (< 40.0)."""
    unrelated_examples = [
        "Zen Meditation Timer",
        "Nature Photography Club",
        "Classic Car Restoration",
        "Baking Bread Recipes",
        "Solar Panel Installation",
    ]
    for unrelated in unrelated_examples:
        res = calculate_lookalike_similarity(unrelated, "AcmePay")
        assert res["similarity_score"] <= 40.0
        assert res["is_exact_match"] is False
        assert res["mutation_type"] == "UNRELATED"


def test_common_modifier_word_without_brand_is_not_impersonation() -> None:
    """Common words like 'Wallet' or 'Secure' alone must not trigger impersonation against AcmePay."""
    res = calculate_lookalike_similarity("Crypto Secure Vault", "AcmePay")
    assert res["similarity_score"] <= 40.0
    assert res["mutation_type"] == "UNRELATED"


def test_package_identifier_exact_match() -> None:
    """Exact package identifier match returns 100.0%."""
    res = compare_package_identifiers("com.acmepay.wallet", "com.acmepay.wallet")
    assert res["is_exact_match"] is True
    assert res["similarity_score"] == 100.0


def test_package_identifier_lookalike_extension() -> None:
    """Package with appended scam component (com.acmepay.wallet.scam) is flagged."""
    res = compare_package_identifiers("com.acmepay.wallet.scam", "com.acmepay.wallet")
    assert res["is_lookalike"] is True
    assert res["target_components_present"] is True
    assert res["similarity_score"] >= 80.0


def test_package_identifier_typo_component() -> None:
    """Package with typo in brand component (com.acmepayy.wallet) is flagged."""
    res = compare_package_identifiers("com.acmepayy.wallet", "com.acmepay.wallet", brand_name="AcmePay")
    assert res["is_lookalike"] is True
    assert res["similarity_score"] >= 85.0


def test_package_identifier_shared_generic_prefix_not_flagged() -> None:
    """Two packages simply sharing 'com.' prefix are NOT lookalikes."""
    res = compare_package_identifiers("com.zenstudios.meditation", "com.acmepay.wallet", brand_name="AcmePay")
    assert res["is_lookalike"] is False
    assert res["similarity_score"] <= 40.0
