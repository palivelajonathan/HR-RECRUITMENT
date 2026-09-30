"""
Secure File Upload Validation & Path Traversal Defense.

CAPABL Track 6 Requirement:
- Never trust uploaded filenames: strip path traversal, null bytes, and malicious characters.
- Validate file extension, magic bytes (%PDF-), MIME/type, and file size limits.
- Detect and reject empty files (0 bytes), malformed PDFs, and encrypted PDFs.
- Enforce strict resource limits on maximum page count and file size.
- Prevent arbitrary filesystem writes and temporary file leaks.
"""

import io
import re
import uuid
from pathlib import Path
from typing import Union, Tuple, Optional
import pypdf

# Default resource limits
DEFAULT_MAX_UPLOAD_SIZE_MB = 10
DEFAULT_MAX_PDF_PAGES = 20


def sanitize_filename(filename: Optional[str]) -> str:
    """
    Sanitizes an untrusted filename, stripping directory traversal patterns,
    path separators, null bytes, and illegal characters.
    
    Examples:
        '../../secret.pdf' -> 'secret.pdf'
        '..\\..\\Windows\\System32\\cmd.pdf' -> 'cmd.pdf'
        '/etc/passwd' -> 'passwd.pdf'
    """
    if not filename:
        return f"upload_{uuid.uuid4().hex[:8]}.pdf"

    # Remove null bytes and control characters
    cleaned = filename.replace("\x00", "").strip()

    # Extract basename only (stripping both Unix and Windows separators)
    cleaned = cleaned.replace("\\", "/")
    basename = cleaned.split("/")[-1].strip()

    # Remove leading dots to prevent hidden files or traversal tricks
    basename = re.sub(r'^\.+', '', basename).strip()

    # Ensure .pdf extension
    if not basename.lower().endswith(".pdf"):
        basename = f"{basename}.pdf"

    # Normalize name: allow alphanumeric, underscore, hyphen, and period
    name_stem = basename[:-4]
    safe_stem = re.sub(r'[^a-zA-Z0-9_\-]', '_', name_stem).strip('_')

    if not safe_stem:
        safe_stem = f"upload_{uuid.uuid4().hex[:8]}"

    return f"{safe_stem}.pdf"


def validate_pdf_content(
    file_path_or_bytes: Union[str, bytes, Path],
    filename: Optional[str] = None,
    max_size_mb: Optional[int] = None,
    max_pages: Optional[int] = None,
) -> Tuple[bytes, str]:
    """
    Validates PDF file inputs thoroughly before ingestion.
    
    Checks:
    1. Path traversal & filename safety
    2. Zero-byte (empty) file check
    3. File size ceiling check (MAX_UPLOAD_SIZE_MB)
    4. Magic byte signature check (%PDF-)
    5. Structural PDF readability & encryption check
    6. Page count ceiling check (MAX_PDF_PAGES)
    
    Returns:
        Tuple[bytes, str]: (validated_raw_bytes, sanitized_filename)
        
    Raises:
        FileNotFoundError: If a file path is provided that does not exist.
        ValueError: If any security or structural validation check fails.
    """
    try:
        from capabl_core.config.settings import get_settings
        cfg = get_settings()
        limit_size_mb = max_size_mb if max_size_mb is not None else cfg.max_upload_size_mb
        limit_pages = max_pages if max_pages is not None else cfg.max_pdf_pages
    except Exception:
        limit_size_mb = max_size_mb or DEFAULT_MAX_UPLOAD_SIZE_MB
        limit_pages = max_pages or DEFAULT_MAX_PDF_PAGES

    # Resolve filename
    original_name = filename
    if isinstance(file_path_or_bytes, (str, Path)):
        p = Path(file_path_or_bytes)
        if not original_name:
            original_name = p.name
        if not p.exists():
            raise FileNotFoundError(f"File not found: {p}")
        try:
            raw_bytes = p.read_bytes()
        except Exception as exc:
            raise ValueError(f"Unable to read file content: {exc}")
    elif isinstance(file_path_or_bytes, bytes):
        raw_bytes = file_path_or_bytes
    else:
        raise ValueError(f"Unsupported file input type: {type(file_path_or_bytes)}")

    clean_filename = sanitize_filename(original_name)

    # 1. Empty file validation
    if len(raw_bytes) == 0:
        raise ValueError("Uploaded file is empty (0 bytes).")

    # 2. File size ceiling check
    max_bytes = limit_size_mb * 1024 * 1024
    if len(raw_bytes) > max_bytes:
        size_mb = len(raw_bytes) / (1024 * 1024)
        raise ValueError(
            f"File size ({size_mb:.2f} MB) exceeds maximum allowed limit of {limit_size_mb} MB."
        )

    # 3. Magic byte signature validation (%PDF-)
    if not raw_bytes.startswith(b"%PDF-"):
        raise ValueError(
            "Invalid file format: Missing '%PDF-' header signature. "
            "Only genuine PDF documents are accepted."
        )

    # 4. Structural validation via pypdf
    try:
        reader = pypdf.PdfReader(io.BytesIO(raw_bytes))
    except Exception as exc:
        raise ValueError(f"Malformed or unreadable PDF document: {exc}")

    # 5. Encryption check
    if getattr(reader, "is_encrypted", False):
        raise ValueError("Encrypted or password-protected PDFs are not supported.")

    # 6. Page count checks
    try:
        page_count = len(reader.pages)
    except Exception as exc:
        raise ValueError(f"Failed to inspect PDF pages: {exc}")

    if page_count == 0:
        raise ValueError("PDF document contains zero pages.")

    if page_count > limit_pages:
        raise ValueError(
            f"PDF document exceeds page limit ({page_count} pages > {limit_pages} maximum allowed)."
        )

    return raw_bytes, clean_filename
