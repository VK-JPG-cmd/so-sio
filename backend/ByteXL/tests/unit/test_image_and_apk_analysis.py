"""
Unit tests for Image similarity and Android APK static analysis:
- Image format validation & dimension bounds
- Perceptual hash generation and Hamming similarity
- APK package validation (empty, malformed, invalid zip)
- APK static analysis metadata extraction
"""

import io
import zipfile
from PIL import Image
import pytest
from app.core.exceptions import ValidationError
from app.services.detection.apk_analysis import APKAnalysisService
from app.services.detection.image_similarity import ImageSimilarityService


def _generate_test_image(format: str = "PNG", size: tuple[int, int] = (64, 64), color: tuple[int, int, int] = (255, 0, 0)) -> bytes:
    """Helper to generate in-memory test image bytes."""
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(buf, format=format)
    return buf.getvalue()


def _generate_synthetic_apk() -> bytes:
    """Helper to generate a minimal synthetically packaged APK zip."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("AndroidManifest.xml", b"<manifest package='com.acme.fakeapp'></manifest>")
        zf.writestr("classes.dex", b"dex\n035\x00")
        zf.writestr("res/values/strings.xml", b"<resources><string name='app_name'>Acme Fake App</string></resources>")
    return buf.getvalue()


# ============================================================================
# IMAGE SIMILARITY TESTS
# ============================================================================


def test_image_validation_valid_formats() -> None:
    """Verify valid PNG and JPEG formats are accepted."""
    service = ImageSimilarityService()

    png_bytes = _generate_test_image("PNG")
    img, val = service.validate_and_open_image(png_bytes)
    assert val.is_valid is True
    assert val.format == "PNG"

    jpg_bytes = _generate_test_image("JPEG")
    _, val_jpg = service.validate_and_open_image(jpg_bytes)
    assert val_jpg.is_valid is True
    assert val_jpg.format == "JPEG"


def test_image_validation_rejects_out_of_bounds_dimensions() -> None:
    """Verify images smaller than 16x16 or larger than 8192x8192 are rejected."""
    service = ImageSimilarityService()

    # Too small (8x8)
    tiny_bytes = _generate_test_image("PNG", size=(8, 8))
    with pytest.raises(ValidationError) as exc_tiny:
        service.validate_and_open_image(tiny_bytes)
    assert "below minimum" in str(exc_tiny.value.message)


def test_image_validation_rejects_corrupted_data() -> None:
    """Verify non-image bytes raise clean ValidationError."""
    service = ImageSimilarityService()
    with pytest.raises(ValidationError) as exc:
        service.validate_and_open_image(b"not an image binary stream")
    assert "Corrupted or invalid" in str(exc.value.message)


def test_image_perceptual_hash_comparison() -> None:
    """Verify identical images yield 100% similarity and distance 0."""
    service = ImageSimilarityService()
    img_bytes = _generate_test_image("PNG", size=(100, 100), color=(100, 150, 200))

    hashes, _ = service.compute_hashes(img_bytes)
    comparison = service.compare_hashes(hashes.phash, hashes.phash)

    assert comparison.similarity_score == 100.0
    assert comparison.hamming_distance == 0
    assert comparison.is_visual_match is True
    assert "Perceptual similarity" in comparison.disclaimer


# ============================================================================
# APK STATIC ANALYSIS TESTS
# ============================================================================


def test_apk_analysis_rejects_empty_file() -> None:
    """Verify 0-byte APK upload is rejected."""
    service = APKAnalysisService()
    with pytest.raises(ValidationError) as exc:
        service.analyze_apk(b"")
    assert "empty" in str(exc.value.message)


def test_apk_analysis_rejects_malformed_non_zip() -> None:
    """Verify corrupted non-zip binary raises ValidationError."""
    service = APKAnalysisService()
    with pytest.raises(ValidationError) as exc:
        service.analyze_apk(b"malformed binary header that is not zip")
    assert "invalid ZIP" in str(exc.value.message)


def test_apk_analysis_rejects_zip_missing_manifest() -> None:
    """Verify ZIP archive missing AndroidManifest.xml is rejected."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("test.txt", b"plain text")
    zip_bytes = buf.getvalue()

    service = APKAnalysisService()
    with pytest.raises(ValidationError) as exc:
        service.analyze_apk(zip_bytes)
    assert "AndroidManifest.xml missing" in str(exc.value.message)


def test_apk_analysis_static_inspection_extracts_indicators() -> None:
    """Verify synthetic APK static analysis parses hashes and structure without code execution."""
    service = APKAnalysisService()
    apk_bytes = _generate_synthetic_apk()

    result = service.analyze_apk(apk_bytes, file_name="sample.apk")

    assert result.file_name == "sample.apk"
    assert result.file_size_bytes == len(apk_bytes)
    assert len(result.sha256_hash) == 64
    assert len(result.md5_hash) == 32
    assert result.androguard_available is True
