"""
Logo and Image Perceptual Similarity Service.
Uses Pillow and ImageHash to compute visual resemblance between suspected assets
and authoritative registered brand logos.

Architectural Notice:
Perceptual similarity indicates visual resemblance (e.g. logo reuse or cropping),
but does NOT prove malicious impersonation on its own.
"""

import io
from typing import Any, Dict, List, Optional, Tuple
import imagehash
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field
from app.core.exceptions import ValidationError
from app.core.logging import get_logger

logger = get_logger("app.services.detection.image_similarity")

ALLOWED_IMAGE_FORMATS = {"PNG", "JPEG", "WEBP"}
MIN_DIMENSION = 16
MAX_DIMENSION = 8192


class ImageValidationResult(BaseModel):
    """Validation report on decoded image properties."""

    is_valid: bool
    format: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    color_mode: Optional[str] = None
    error_message: Optional[str] = None


class ImageHashResult(BaseModel):
    """Perceptual hash fingerprints for an image asset."""

    phash: str = Field(..., description="Perceptual hash (DCT-based)")
    dhash: str = Field(..., description="Difference gradient hash")
    ahash: str = Field(..., description="Average luminance hash")


class ImageComparisonResult(BaseModel):
    """Outcome of comparing a target image against a reference brand logo."""

    similarity_score: float = Field(..., ge=0.0, le=100.0, description="Visual similarity percentage")
    hamming_distance: int = Field(..., description="Hamming bit distance between perceptual hashes")
    is_visual_match: bool = Field(..., description="True if distance is within spoof threshold (<= 10)")
    disclaimer: str = (
        "Perceptual similarity indicates visual resemblance but does NOT prove impersonation. "
        "Context, authorization, and trademark boundaries must be verified."
    )


class ImageSimilarityService:
    """Service for validating image assets and computing perceptual similarity."""

    @classmethod
    def validate_and_open_image(cls, image_bytes: bytes) -> Tuple[Image.Image, ImageValidationResult]:
        """
        Validate image format, bounds, and integrity before processing.
        Guards against decompression bombs and corrupted binaries.
        """
        if not image_bytes or len(image_bytes) == 0:
            raise ValidationError("Image byte stream is empty.")

        try:
            img = Image.open(io.BytesIO(image_bytes))
            img_format = (img.format or "").upper()
            w, h = img.size

            if img_format not in ALLOWED_IMAGE_FORMATS:
                raise ValidationError(
                    f"Unsupported image format '{img_format}'. Supported formats: {', '.join(ALLOWED_IMAGE_FORMATS)}"
                )

            if w < MIN_DIMENSION or h < MIN_DIMENSION:
                raise ValidationError(f"Image dimensions ({w}x{h}) are below minimum {MIN_DIMENSION}x{MIN_DIMENSION}.")

            if w > MAX_DIMENSION or h > MAX_DIMENSION:
                raise ValidationError(f"Image dimensions ({w}x{h}) exceed maximum {MAX_DIMENSION}x{MAX_DIMENSION}.")

            val_res = ImageValidationResult(
                is_valid=True,
                format=img_format,
                width=w,
                height=h,
                color_mode=img.mode,
            )
            return img, val_res

        except (UnidentifiedImageError, OSError) as e:
            logger.warning(f"Failed to open image: {e}")
            raise ValidationError(f"Corrupted or invalid image data: {str(e)}")

    def compute_hashes(self, image_bytes: bytes) -> Tuple[ImageHashResult, ImageValidationResult]:
        """Compute DCT perceptual hash, difference hash, and average hash for an image."""
        img, val_res = self.validate_and_open_image(image_bytes)

        # Convert to RGB to ensure uniform hash computation across palette/alpha modes
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        p = str(imagehash.phash(img))
        d = str(imagehash.dhash(img))
        a = str(imagehash.average_hash(img))

        return ImageHashResult(phash=p, dhash=d, ahash=a), val_res

    def compare_hashes(self, hash_a_str: str, hash_b_str: str) -> ImageComparisonResult:
        """
        Compare two perceptual hash hex strings using Hamming bit distance.
        A distance of 0 indicates an identical image; distance <= 10 indicates high visual similarity.
        """
        try:
            h1 = imagehash.hex_to_hash(hash_a_str)
            h2 = imagehash.hex_to_hash(hash_b_str)
        except Exception as e:
            raise ValidationError(f"Invalid perceptual hash hex representation: {e}")

        distance = h1 - h2
        # A 64-bit hash has a max distance of 64
        similarity = max(0.0, 1.0 - (distance / 64.0)) * 100.0
        is_match = distance <= 10  # Standard perceptual threshold

        return ImageComparisonResult(
            similarity_score=round(similarity, 2),
            hamming_distance=distance,
            is_visual_match=is_match,
        )

    def compare_image_to_hash(
        self,
        image_bytes: bytes,
        reference_phash: str,
    ) -> Tuple[ImageComparisonResult, ImageHashResult]:
        """Compute target image hash and compare against a stored reference brand logo hash."""
        target_hashes, _ = self.compute_hashes(image_bytes)
        comparison = self.compare_hashes(target_hashes.phash, reference_phash)
        return comparison, target_hashes
