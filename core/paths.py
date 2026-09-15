"""Filename sanitization and lookup for user-supplied PDF names.

Upload and ingest endpoints take a filename straight from the client, so
every path must be reduced to a bare basename and confirmed to resolve
inside an allowed directory before it is touched.
"""
import os
from pathlib import Path
from typing import Optional

from core import config


def safe_filename(filename: str) -> str:
    """Reduce a client-supplied name to a safe basename.

    Strips directory components (including Windows separators and drive
    letters) so values like "../../etc/passwd" cannot escape the data dirs.
    """
    if not filename:
        raise ValueError("Filename is empty")

    # Normalize separators, then take the final component only.
    name = filename.replace("\\", "/").split("/")[-1]
    name = os.path.basename(name).strip()

    if not name or name in {".", ".."} or name.startswith("."):
        raise ValueError(f"Invalid filename: {filename!r}")
    if not name.lower().endswith(".pdf"):
        raise ValueError("Only .pdf files are allowed")
    return name


def _within(path: Path, parent: Path) -> bool:
    """True if path resolves inside parent."""
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except (ValueError, OSError):
        return False


def resolve_pdf(filename: str) -> Optional[Path]:
    """Find a PDF by name in the allowed directories, or return None.

    The resolved path is verified to live inside an allowed directory, so a
    symlink pointing outside is rejected too.
    """
    name = safe_filename(filename)
    for directory in (config.PAPERS_DIR, config.UPLOADS_DIR):
        parent = Path(directory)
        candidate = parent / name
        if candidate.is_file() and _within(candidate, parent):
            return candidate
    return None


def upload_path(filename: str) -> Path:
    """Return the destination path for an upload, avoiding collisions."""
    name = safe_filename(filename)
    uploads = Path(config.UPLOADS_DIR)
    uploads.mkdir(parents=True, exist_ok=True)

    dest = uploads / name
    if dest.exists():
        from datetime import datetime

        stem, ext = os.path.splitext(name)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = uploads / f"{stem}_{stamp}{ext}"

    if not _within(dest, uploads):
        raise ValueError(f"Invalid filename: {filename!r}")
    return dest
