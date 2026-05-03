from __future__ import annotations

from pathlib import Path
from urllib.parse import urlencode
from uuid import uuid4

import gridfs
from bson import ObjectId
from gridfs.errors import NoFile

from api.db import get_db

GRIDFS_PREFIX = "gridfs:"


def get_gridfs() -> gridfs.GridFS:
    return gridfs.GridFS(get_db())


def is_gridfs_reference(value: str | None) -> bool:
    return bool(value and value.startswith(GRIDFS_PREFIX))


def gridfs_file_id(storage_reference: str) -> ObjectId:
    if not is_gridfs_reference(storage_reference):
        raise ValueError("Storage reference is not a GridFS reference.")
    return ObjectId(storage_reference.removeprefix(GRIDFS_PREFIX))


def save_uploaded_file(uploaded_file, subdir: str, metadata: dict | None = None) -> str:
    suffix = Path(uploaded_file.name).suffix
    filename = f"{subdir}/{uuid4().hex}{suffix}"
    grid_in = get_gridfs().new_file(
        filename=filename,
        content_type=getattr(uploaded_file, "content_type", None),
        metadata={
            "subdir": subdir,
            "original_filename": uploaded_file.name,
            **(metadata or {}),
        },
    )
    try:
        for chunk in uploaded_file.chunks():
            grid_in.write(chunk)
    finally:
        grid_in.close()

    return f"{GRIDFS_PREFIX}{grid_in._id}"


def delete_media_file(relative_path: str | None) -> None:
    if not relative_path:
        return
    if is_gridfs_reference(relative_path):
        try:
            get_gridfs().delete(gridfs_file_id(relative_path))
        except NoFile:
            pass


def read_stored_file(storage_reference: str) -> tuple[str, bytes]:
    if not is_gridfs_reference(storage_reference):
        raise ValueError("Stored files must use a GridFS reference.")

    grid_file = get_gridfs().get(gridfs_file_id(storage_reference))
    return grid_file.filename or "attachment", grid_file.read()


def build_media_url(request, relative_path: str | None) -> str | None:
    if not relative_path:
        return None
    if is_gridfs_reference(relative_path):
        token = ""
        authorization = request.headers.get("Authorization", "")
        if authorization.startswith("Bearer "):
            token = f"?{urlencode({'token': authorization.removeprefix('Bearer ').strip()})}"
        return request.build_absolute_uri(f"/api/files/{gridfs_file_id(relative_path)}/{token}")
    return None
