from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from django.conf import settings


def ensure_media_subdir(name: str) -> Path:
    target = Path(settings.MEDIA_ROOT) / name
    target.mkdir(parents=True, exist_ok=True)
    return target


def save_uploaded_file(uploaded_file, subdir: str) -> str:
    destination_dir = ensure_media_subdir(subdir)
    suffix = Path(uploaded_file.name).suffix
    filename = f"{uuid4().hex}{suffix}"
    destination = destination_dir / filename

    with destination.open("wb") as stream:
        for chunk in uploaded_file.chunks():
            stream.write(chunk)

    return str(destination.relative_to(settings.MEDIA_ROOT)).replace("\\", "/")


def absolute_media_path(relative_path: str) -> Path:
    return Path(settings.MEDIA_ROOT) / relative_path


def delete_media_file(relative_path: str | None) -> None:
    if not relative_path:
        return
    target = absolute_media_path(relative_path)
    if target.exists():
        target.unlink()


def build_media_url(request, relative_path: str | None) -> str | None:
    if not relative_path:
        return None
    normalized = relative_path.replace("\\", "/")
    return request.build_absolute_uri(f"{settings.MEDIA_URL}{normalized}")
