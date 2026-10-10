import io
from pathlib import Path
import pytest
from fastapi import UploadFile
from app.core.file_security import FileSecurityError, FileSecurityService


def test_sanitize_filename_strips_traversal() -> None:
    """Verify path traversal sequences and dangerous characters are stripped."""
    service = FileSecurityService()

    assert service.sanitize_filename("../../../etc/passwd") == "passwd"
    assert service.sanitize_filename("..\\..\\windows\\system32\\cmd.exe") == "cmd.exe"
    assert service.sanitize_filename("valid_screenshot.png") == "valid_screenshot.png"
    assert service.sanitize_filename("test file (1).jpg") == "test_file__1_.jpg"
    assert service.sanitize_filename("") == "evidence_file"


def test_validate_extension_allowlist() -> None:
    """Verify only allowlisted file extensions are permitted."""
    service = FileSecurityService()

    assert service.validate_extension("image.PNG") == ".png"
    assert service.validate_extension("report.PDF") == ".pdf"
    assert service.validate_extension("data.json") == ".json"

    # Reject executable and script extensions
    with pytest.raises(FileSecurityError) as exc_exe:
        service.validate_extension("malware.exe")
    assert "not permitted" in str(exc_exe.value.message)

    with pytest.raises(FileSecurityError):
        service.validate_extension("script.sh")

    with pytest.raises(FileSecurityError):
        service.validate_extension("webshell.php")

    with pytest.raises(FileSecurityError):
        service.validate_extension("xss.html")


def test_inspect_content_magic_bytes_png() -> None:
    """Verify PNG header magic bytes validation."""
    service = FileSecurityService()

    # Valid PNG header
    valid_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    service.inspect_content(valid_png, ".png")

    # Disguised text claiming to be PNG
    with pytest.raises(FileSecurityError) as exc:
        service.inspect_content(b"not a png image", ".png")
    assert "does not match expected signature" in str(exc.value.message)


def test_inspect_content_magic_bytes_jpeg() -> None:
    """Verify JPEG header magic bytes validation."""
    service = FileSecurityService()

    valid_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF"
    service.inspect_content(valid_jpeg, ".jpg")

    with pytest.raises(FileSecurityError):
        service.inspect_content(b"fake jpeg content", ".jpg")


def test_inspect_content_magic_bytes_pdf() -> None:
    """Verify PDF header magic bytes validation."""
    service = FileSecurityService()

    valid_pdf = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n"
    service.inspect_content(valid_pdf, ".pdf")

    with pytest.raises(FileSecurityError):
        service.inspect_content(b"fake pdf content", ".pdf")


def test_inspect_content_rejects_dangerous_executable_headers() -> None:
    """Verify dangerous executable headers are rejected even if extension is .txt or .png."""
    service = FileSecurityService()

    # Windows PE executable header MZ
    with pytest.raises(FileSecurityError) as exc_mz:
        service.inspect_content(b"MZ\x90\x00\x03\x00\x00\x00", ".txt")
    assert "Executable, binary script, or active web content" in str(exc_mz.value.message)

    # Linux ELF header
    with pytest.raises(FileSecurityError):
        service.inspect_content(b"\x7fELF\x02\x01\x01\x00", ".log")

    # Shell script header
    with pytest.raises(FileSecurityError):
        service.inspect_content(b"#!/bin/bash\nrm -rf /", ".txt")

    # HTML / Script tags in text
    with pytest.raises(FileSecurityError):
        service.inspect_content(b"<script>alert(1)</script>", ".txt")


def test_inspect_content_rejects_empty_file() -> None:
    """Verify 0-byte files are rejected."""
    service = FileSecurityService()
    with pytest.raises(FileSecurityError) as exc:
        service.inspect_content(b"", ".png")
    assert "empty" in str(exc.value.message)
