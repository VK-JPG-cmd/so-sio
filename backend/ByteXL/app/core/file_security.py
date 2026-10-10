import hashlib
import json
import os
from pathlib import Path
import re
from typing import Tuple
import uuid
from fastapi import UploadFile
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import get_logger

logger = get_logger("app.core.file_security")


class FileSecurityError(AppError):
    """Raised when an uploaded file violates security or integrity rules."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(
            message=message,
            status_code=status_code,
            error_code="INVALID_FILE_UPLOAD",
        )


class FileSecurityService:
    """
    Enforces strict security validation, content inspection, sanitization,
    and server-side isolation for evidence artifact uploads.
    """

    # Magic byte header signatures
    MAGIC_SIGNATURES = {
        ".png": [b"\x89PNG\r\n\x1a\n"],
        ".jpg": [b"\xff\xd8\xff"],
        ".jpeg": [b"\xff\xd8\xff"],
        ".webp": [b"RIFF"],  # Also requires 'WEBP' at offset 8
        ".pdf": [b"%PDF-"],
    }

    # Executable or dangerous script header signatures to immediately reject
    DANGEROUS_SIGNATURES = [
        b"MZ",  # Windows PE / EXE / DLL
        b"\x7fELF",  # Linux ELF
        b"\xca\xfe\xba\xbe",  # Mach-O / Java bytecode
        b"#!/bin/",  # Shell script
        b"#!/usr/bin/",
        b"<?php",
        b"<html",
        b"<script",
        b"<!DOCTYPE html",
    ]

    def __init__(self) -> None:
        self.settings = get_settings()

    def sanitize_filename(self, filename: str) -> str:
        """
        Strip path components and dangerous characters from user-provided filename
        to completely prevent path traversal attacks.
        """
        if not filename:
            return "evidence_file"

        # Extract only the base name (strip any leading directory paths)
        base = os.path.basename(filename.strip().replace("\\", "/"))

        # Remove null bytes, path traversal sequences, and special characters
        base = base.replace("\0", "")
        # Remove any leading dots or slashes
        base = re.sub(r"^[.\s/\\]+", "", base)
        # Keep alphanumeric, dot, underscore, dash
        sanitized = re.sub(r"[^a-zA-Z0-9._-]", "_", base)

        if not sanitized or sanitized.startswith("."):
            sanitized = f"evidence_{uuid.uuid4().hex[:8]}"

        # Truncate length to 255 chars
        return sanitized[:255]

    def validate_extension(self, filename: str) -> str:
        """
        Extract and validate the file extension against the strict allowlist.
        Returns the normalized lowercase extension (e.g. '.png').
        """
        ext = Path(filename).suffix.lower()
        if not ext or ext not in self.settings.ALLOWED_EVIDENCE_EXTENSIONS:
            allowed = ", ".join(self.settings.ALLOWED_EVIDENCE_EXTENSIONS)
            raise FileSecurityError(
                f"File extension '{ext}' is not permitted. Allowed extensions are: {allowed}"
            )
        return ext

    def inspect_content(self, data: bytes, extension: str) -> None:
        """
        Inspect file magic bytes and contents to prevent disguised executables
        and malformed files. Never relies on client MIME header alone.
        """
        if not data or len(data) == 0:
            raise FileSecurityError("Uploaded file is empty (0 bytes).")

        header = data[:64]

        # Check for banned executable/script headers regardless of declared extension
        for dangerous in self.DANGEROUS_SIGNATURES:
            if header.startswith(dangerous) or dangerous in header[:32].lower():
                logger.warning(f"Rejected file containing dangerous signature: {dangerous}")
                raise FileSecurityError("Executable, binary script, or active web content is strictly forbidden.")

        # Inspect specific format magic bytes
        if extension in ('.png', '.jpg', '.jpeg', '.pdf'):
            valid = False
            for sig in self.MAGIC_SIGNATURES[extension]:
                if header.startswith(sig):
                    valid = True
                    break
            if not valid:
                raise FileSecurityError(
                    f"File content does not match expected signature for '{extension}' format."
                )

        elif extension == ".webp":
            if not (header.startswith(b"RIFF") and len(data) >= 12 and data[8:12] == b"WEBP"):
                raise FileSecurityError("File content is not a valid WebP image.")

        elif extension in (".txt", ".log"):
            if b"\x00" in data[:1024]:
                raise FileSecurityError("Text or log evidence must not contain null binary bytes.")
            try:
                data.decode("utf-8")
            except UnicodeDecodeError:
                raise FileSecurityError("Text evidence must be valid UTF-8 text.")

        elif extension == ".json":
            if b"\x00" in data[:1024]:
                raise FileSecurityError("JSON evidence must not contain null binary bytes.")
            try:
                text_content = data.decode("utf-8")
                json.loads(text_content)
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise FileSecurityError("JSON evidence must be valid, well-formed UTF-8 JSON.")

    async def process_and_store_file(
        self,
        upload_file: UploadFile,
        report_id: uuid.UUID,
    ) -> Tuple[str, str, str, int]:
        """
        Securely process and store an uploaded evidence file:
        1. Sanitize filename and validate extension.
        2. Stream content enforcing max file size.
        3. Inspect magic bytes and verify content integrity.
        4. Compute SHA-256 hash.
        5. Generate server-side random storage key.
        6. Write to isolated storage directory with safe permissions.

        Returns: (storage_key, sha256_hash, sanitized_original_filename, file_size)
        """
        raw_filename = upload_file.filename or "evidence"
        sanitized_filename = self.sanitize_filename(raw_filename)
        extension = self.validate_extension(sanitized_filename)

        # Read content while strictly checking max size
        content = bytearray()
        sha256 = hashlib.sha256()
        chunk_size = 64 * 1024  # 64 KB chunks

        while True:
            chunk = await upload_file.read(chunk_size)
            if not chunk:
                break
            content.extend(chunk)
            sha256.update(chunk)
            if len(content) > self.settings.MAX_EVIDENCE_FILE_SIZE_BYTES:
                max_mb = self.settings.MAX_EVIDENCE_FILE_SIZE_BYTES / (1024 * 1024)
                raise FileSecurityError(
                    f"File exceeds maximum allowed size of {max_mb:.1f} MB.",
                    status_code=413,
                )

        file_bytes = bytes(content)
        file_size = len(file_bytes)

        # Inspect content header / magic bytes
        self.inspect_content(file_bytes, extension)

        sha256_hex = sha256.hexdigest()

        # Generate unique server-side storage key
        random_file_id = uuid.uuid4().hex
        storage_key = f"evidence/{report_id}/{random_file_id}{extension}"

        # Resolve storage directory
        base_dir = Path(self.settings.EVIDENCE_STORAGE_DIR).resolve()
        target_path = (base_dir / storage_key).resolve()

        # Path traversal guard: verify target path is inside base_dir
        if not str(target_path).startswith(str(base_dir)):
            logger.error(f"Path traversal detected! Attempted path: {target_path}")
            raise FileSecurityError("Invalid storage target location.")

        # Ensure directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file with non-executable permissions
        with open(target_path, "wb") as f:
            f.write(file_bytes)

        # Set permissions: 0o600 (read/write by owner only) on Unix if supported
        try:
            os.chmod(target_path, 0o600)
        except Exception:
            pass

        logger.info(
            f"Stored evidence file for report {report_id}: {storage_key} "
            f"(size={file_size} bytes, sha256={sha256_hex})"
        )

        return storage_key, sha256_hex, sanitized_filename, file_size

    def get_secure_file_path(self, storage_key: str) -> Path:
        """
        Resolve storage key to absolute filesystem path with path traversal protection.
        """
        # Guard against traversal characters in storage_key
        if ".." in storage_key or storage_key.startswith("/") or storage_key.startswith("\\"):
            raise FileSecurityError("Invalid storage key path.")

        base_dir = Path(self.settings.EVIDENCE_STORAGE_DIR).resolve()
        resolved_path = (base_dir / storage_key).resolve()

        if not str(resolved_path).startswith(str(base_dir)):
            raise FileSecurityError("Unauthorized storage path traversal attempt.")

        if not resolved_path.exists() or not resolved_path.is_file():
            raise FileSecurityError("Evidence file not found on storage server.", status_code=404)

        return resolved_path
