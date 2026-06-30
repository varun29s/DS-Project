"""Upload media (photos / reels / stories / avatars).

Two backends, selected by ``settings.STORAGE_BACKEND``:
  - ``"supabase"`` (default): upload to a public Supabase Storage bucket.
  - ``"local"``: write to a local directory served at ``/media`` — handy for local
    testing without Supabase credentials.
"""
import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/webm"}

_EXT_BY_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
    "video/webm": ".webm",
}

# Reuse a single Supabase client across requests (created lazily).
_client = None


def _get_client():
    global _client
    if _client is None:
        from supabase import create_client

        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _client


def _resolve_extension(file: UploadFile, content_type: str) -> str:
    ext = os.path.splitext(file.filename or "")[1].lower()
    return ext or _EXT_BY_TYPE.get(content_type, "")


async def _read_validated(file: UploadFile, allowed_types, max_mb: int) -> tuple[bytes, str]:
    content_type = (file.content_type or "application/octet-stream").lower()
    if allowed_types and content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{content_type}'. Allowed: {sorted(allowed_types)}",
        )
    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
    if len(data) > max_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large (max {max_mb} MB)",
        )
    return data, content_type


def _save_local(folder: str, filename: str, data: bytes) -> str:
    dest_dir = Path(settings.MEDIA_ROOT) / folder
    dest_dir.mkdir(parents=True, exist_ok=True)
    (dest_dir / filename).write_bytes(data)
    return f"{settings.BACKEND_PUBLIC_URL.rstrip('/')}/media/{folder}/{filename}"


def _save_supabase(folder: str, filename: str, data: bytes, content_type: str) -> str:
    path = f"{folder}/{filename}"
    bucket = settings.SUPABASE_STORAGE_BUCKET
    client = _get_client()
    try:
        client.storage.from_(bucket).upload(
            path, data, {"content-type": content_type, "upsert": "true"}
        )
    except Exception as exc:  # storage3 / network errors
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to upload to storage: {exc}",
        )
    return client.storage.from_(bucket).get_public_url(path)


async def upload_media(
    file: UploadFile,
    folder: str,
    allowed_types: set[str] | None = None,
    max_mb: int = 50,
) -> str:
    """Validate, store, and return a public URL for the uploaded file."""
    data, content_type = await _read_validated(file, allowed_types, max_mb)
    filename = f"{uuid.uuid4().hex}{_resolve_extension(file, content_type)}"

    if settings.STORAGE_BACKEND == "local":
        return _save_local(folder, filename, data)
    return _save_supabase(folder, filename, data, content_type)