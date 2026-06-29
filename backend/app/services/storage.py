"""Storage service — supports Supabase Storage and a local filesystem fallback."""
import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

ALLOWED_IMAGE_TYPES: set[str] = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_VIDEO_TYPES: set[str] = {"video/mp4", "video/quicktime", "video/webm"}

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


async def upload_media(
    file: UploadFile,
    folder: str,
    allowed_types: set[str],
) -> str:
    """Upload *file* to the configured backend and return the public URL."""
    content_type = file.content_type or ""
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported media type: {content_type}. Allowed: {allowed_types}",
        )

    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large (max 100 MB)",
        )

    ext = (file.filename or "file").rsplit(".", 1)[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    path = f"{folder}/{filename}"

    if settings.STORAGE_BACKEND == "supabase":
        return _upload_supabase(data, path, content_type)
    return _upload_local(data, path)


def _upload_supabase(data: bytes, path: str, content_type: str) -> str:
    from supabase import create_client  # lazy import — only needed when STORAGE_BACKEND=supabase

    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    client.storage.from_(settings.SUPABASE_STORAGE_BUCKET).upload(
        path, data, {"content-type": content_type, "upsert": "true"}
    )
    return client.storage.from_(settings.SUPABASE_STORAGE_BUCKET).get_public_url(path)


def _upload_local(data: bytes, path: str) -> str:
    dest = Path(settings.MEDIA_ROOT) / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return f"{settings.BACKEND_PUBLIC_URL}/media/{path}"
