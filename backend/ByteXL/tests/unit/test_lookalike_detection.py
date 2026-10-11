import pytest
from app.services.detection.lookalike_detector import LookalikeNameDetector


@pytest.mark.asyncio
@pytest.mark.parametrize("official,threat", [
    ("ApexBank", "ApexBannk"),         # Typo / repeated consonant
    ("ApexBank", "Apex Bank"),         # Spacing
    ("ApexBank", "ApexB4nk"),          # Homoglyph / Leet substitution
    ("ApexBank", "ApexBnka"),          # Character swap / Transposition
    ("ApexBank", "ApexBankOfficial"),  # Brand suffix addition
    ("ApexBank", "ApexBank_support"),  # Lure addition
])
async def test_lookalike_detection(official: str, threat: str):
    detector = LookalikeNameDetector()
    score = await detector.calculate_similarity(official, threat)
    assert score > 0.80, f"Expected {threat} to be scored > 0.80 similarity to {official}, got {score}"


def test_generate_variations():
    detector = LookalikeNameDetector()
    variations = detector.detect_name_variations("ApexBank", max_variations=20)
    assert len(variations) >= 5
    assert any("4" in v or "@" in v for v in variations)  # Homoglyphs generated
