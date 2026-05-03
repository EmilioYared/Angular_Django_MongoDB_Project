from __future__ import annotations

from datetime import datetime

from bson import ObjectId

from api.storage import build_media_url


def isoformat(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def serialize_user(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "created_at": isoformat(user.get("created_at")),
    }


def serialize_profile(profile: dict | None, request) -> dict | None:
    if not profile:
        return None
    return {
        "id": str(profile["_id"]),
        "user_id": str(profile["user_id"]),
        "full_name": profile.get("full_name", ""),
        "profile_email": profile.get("profile_email", ""),
        "joined_date": isoformat(profile.get("joined_date")),
        "profile_image_url": build_media_url(request, profile.get("profile_image_path")),
    }


def serialize_tag(tag: dict) -> dict:
    return {
        "id": str(tag["_id"]),
        "name": tag["name"],
        "created_at": isoformat(tag.get("created_at")),
    }


def serialize_member(member: dict, user: dict | None = None) -> dict:
    return {
        "id": str(member["_id"]),
        "project_id": str(member["project_id"]),
        "user_id": str(member["user_id"]) if member.get("user_id") else None,
        "username": user.get("username") if user else None,
        "email": member.get("invited_email"),
        "role": member.get("role", "collaborator"),
        "added_at": isoformat(member.get("added_at")),
    }


def serialize_project(project: dict, request, tags: list[dict], members_count: int, access_role: str) -> dict:
    return {
        "id": str(project["_id"]),
        "title": project["title"],
        "description": project.get("description", ""),
        "created_at": isoformat(project.get("created_at")),
        "updated_at": isoformat(project.get("updated_at")),
        "owner_id": str(project["owner_id"]),
        "owner_email": project.get("owner_email"),
        "visibility_status": project.get("visibility_status", "private"),
        "cover_image_url": build_media_url(request, project.get("cover_image_path")),
        "access_role": access_role,
        "members_count": members_count,
        "tags": [serialize_tag(tag) for tag in tags],
    }


def serialize_document(document: dict, request) -> dict:
    return {
        "id": str(document["_id"]),
        "project_id": str(document["project_id"]),
        "uploaded_by_user_id": str(document["uploaded_by_user_id"]),
        "title": document["title"],
        "original_filename": document.get("original_filename"),
        "document_type": document.get("document_type"),
        "uploaded_at": isoformat(document.get("uploaded_at")),
        "updated_at": isoformat(document.get("updated_at")),
        "chunk_count": document.get("chunk_count", 0),
        "indexing_status": document.get("indexing_status", "pending"),
        "file_url": build_media_url(request, document.get("file_path")),
        "thumbnail_image_url": build_media_url(request, document.get("thumbnail_image_path")),
        "excerpt": (document.get("extracted_text") or "")[:240],
    }


def serialize_conversation(conversation: dict) -> dict:
    return {
        "id": str(conversation["_id"]),
        "project_id": str(conversation["project_id"]),
        "user_id": str(conversation["user_id"]),
        "title": conversation["title"],
        "created_at": isoformat(conversation.get("created_at")),
        "last_updated": isoformat(conversation.get("last_updated")),
    }


def serialize_message(message: dict) -> dict:
    return {
        "id": str(message["_id"]),
        "project_id": str(message["project_id"]),
        "conversation_id": str(message["conversation_id"]),
        "sender_type": message["sender_type"],
        "content": message["content"],
        "created_at": isoformat(message.get("created_at")),
        "source_matches": message.get("source_matches", []),
    }


def serialize_query_log(row: dict) -> dict:
    return {
        "id": str(row["_id"]),
        "project_id": str(row["project_id"]),
        "user_id": str(row["user_id"]),
        "query_text": row["query_text"],
        "generated_answer": row.get("generated_answer", ""),
        "matches": row.get("matches", []),
        "result_count": row.get("result_count", len(row.get("matches", []))),
        "top_k": row["top_k"],
        "created_at": isoformat(row.get("created_at")),
    }
