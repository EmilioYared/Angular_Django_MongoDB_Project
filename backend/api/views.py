from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId
from django.http import FileResponse, HttpRequest
from gridfs.errors import NoFile

from api.auth import create_access_token, get_authenticated_user, hash_password, normalize_email, verify_password
from api.db import get_db, to_object_id
from api.http import ApiError, api_view, get_request_data, json_response, require_methods
from api.semantic import (
    cascade_delete_document,
    cascade_delete_project,
    generate_grounded_answer,
    rank_project_matches,
    rebuild_document_embeddings,
)
from api.serializers import (
    serialize_conversation,
    serialize_document,
    serialize_member,
    serialize_message,
    serialize_profile,
    serialize_project,
    serialize_query_log,
    serialize_tag,
    serialize_user,
)
from api.storage import save_uploaded_file


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _regex_filter(value: str) -> dict:
    return {"$regex": re.escape(value), "$options": "i"}


def _require_text(data: dict, field: str) -> str:
    value = str(data.get(field, "")).strip()
    if not value:
        raise ApiError(f"{field} is required.", 400, "missing_field")
    return value


def _project_access_role(user_id: ObjectId, project: dict) -> str | None:
    if project["owner_id"] == user_id:
        return "owner"
    membership = get_db().project_members.find_one({"project_id": project["_id"], "user_id": user_id})
    if membership:
        return membership.get("role", "collaborator")
    return None


def _get_accessible_project(request: HttpRequest, project_id: str) -> tuple[dict, dict, str]:
    user = get_authenticated_user(request)
    project = get_db().projects.find_one({"_id": to_object_id(project_id, "project_id")})
    if not project:
        raise ApiError("Project was not found.", 404, "project_not_found")

    access_role = _project_access_role(user["_id"], project)
    if not access_role:
        raise ApiError("You do not have access to this project.", 403, "forbidden")
    return user, project, access_role


def _get_owner_project(request: HttpRequest, project_id: str) -> tuple[dict, dict]:
    user, project, access_role = _get_accessible_project(request, project_id)
    if access_role != "owner":
        raise ApiError("Only the project owner can modify this resource.", 403, "owner_required")
    return user, project


def _require_file_access(request: HttpRequest, file_metadata: dict | None) -> dict:
    user = get_authenticated_user(request)
    metadata = file_metadata or {}
    project_id = metadata.get("project_id")
    user_id = metadata.get("user_id")

    if project_id:
        project = get_db().projects.find_one({"_id": to_object_id(project_id, "project_id")})
        if not project or not _project_access_role(user["_id"], project):
            raise ApiError("You do not have access to this file.", 403, "forbidden")
        return user

    if user_id:
        if user["_id"] != to_object_id(user_id, "user_id"):
            raise ApiError("You do not have access to this file.", 403, "forbidden")
        return user

    raise ApiError("File access metadata is missing.", 403, "forbidden")


def _load_project_tags(project: dict) -> list[dict]:
    tag_ids = project.get("tag_ids", [])
    if not tag_ids:
        return []
    return list(get_db().tags.find({"_id": {"$in": tag_ids}}).sort("name"))


def _serialize_project_detail(project: dict, request, access_role: str) -> dict:
    database = get_db()
    members = list(database.project_members.find({"project_id": project["_id"]}).sort("added_at"))
    user_ids = [member["user_id"] for member in members if member.get("user_id")]
    users = {row["_id"]: row for row in database.users.find({"_id": {"$in": user_ids}})} if user_ids else {}
    tags = _load_project_tags(project)
    return {
        **serialize_project(project, request, tags, len(members), access_role),
        "members": [serialize_member(member, users.get(member.get("user_id"))) for member in members],
    }


@api_view
def health(request: HttpRequest):
    require_methods(request, ["GET"])
    database = get_db()
    database.command("ping")
    return json_response(
        {
            "status": "ok",
            "database": "connected",
            "semantic_search": "project-scoped",
        }
    )


@api_view
def file_download(request: HttpRequest, file_id: str):
    require_methods(request, ["GET"])
    from api.storage import get_gridfs

    if not ObjectId.is_valid(file_id):
        raise ApiError("Invalid file id.", 400, "invalid_file_id")

    try:
        grid_file = get_gridfs().get(to_object_id(file_id, "file_id"))
    except NoFile as exc:
        raise ApiError("File was not found.", 404, "file_not_found") from exc

    metadata = grid_file.metadata or {}
    _require_file_access(request, metadata)
    filename = metadata.get("original_filename") or Path(grid_file.filename or "attachment").name
    content_type = getattr(grid_file, "content_type", None) or "application/octet-stream"
    return FileResponse(grid_file, content_type=content_type, as_attachment=False, filename=filename)


@api_view
def register(request: HttpRequest):
    require_methods(request, ["POST"])
    data = get_request_data(request)
    username = _require_text(data, "username")
    email = normalize_email(_require_text(data, "email"))
    password = _require_text(data, "password")
    full_name = str(data.get("full_name", "")).strip()

    database = get_db()
    if database.users.find_one({"email": email}):
        raise ApiError("A user with that email already exists.", 409, "email_taken")
    if database.users.find_one({"username": username}):
        raise ApiError("A user with that username already exists.", 409, "username_taken")

    now = _now()
    user = {
        "username": username,
        "email": email,
        "password_hash": hash_password(password),
        "created_at": now,
        "updated_at": now,
    }
    user_id = database.users.insert_one(user).inserted_id
    user["_id"] = user_id

    profile = {
        "user_id": user_id,
        "full_name": full_name,
        "profile_email": email,
        "joined_date": now,
        "profile_image_path": None,
    }
    profile_id = database.user_profiles.insert_one(profile).inserted_id
    profile["_id"] = profile_id

    return json_response(
        {
            "token": create_access_token(user),
            "user": serialize_user(user),
            "profile": serialize_profile(profile, request),
        },
        status=201,
    )


@api_view
def login(request: HttpRequest):
    require_methods(request, ["POST"])
    data = get_request_data(request)
    email = normalize_email(_require_text(data, "email"))
    password = _require_text(data, "password")

    database = get_db()
    user = database.users.find_one({"email": email})
    if not user or not verify_password(password, user["password_hash"]):
        raise ApiError("Invalid email or password.", 401, "invalid_credentials")

    profile = database.user_profiles.find_one({"user_id": user["_id"]})
    return json_response(
        {
            "token": create_access_token(user),
            "user": serialize_user(user),
            "profile": serialize_profile(profile, request),
        }
    )


@api_view
def profile(request: HttpRequest):
    user = get_authenticated_user(request)
    database = get_db()
    profile_doc = database.user_profiles.find_one({"user_id": user["_id"]})
    if not profile_doc:
        raise ApiError("Profile was not found.", 404, "profile_not_found")

    if request.method == "GET":
        return json_response({"user": serialize_user(user), "profile": serialize_profile(profile_doc, request)})

    require_methods(request, ["PATCH", "POST"])
    data = get_request_data(request)
    updates = {}

    if "username" in data:
        username = _require_text(data, "username")
        existing = database.users.find_one({"username": username, "_id": {"$ne": user["_id"]}})
        if existing:
            raise ApiError("Username is already in use.", 409, "username_taken")
        updates["username"] = username

    if "full_name" in data:
        profile_doc["full_name"] = str(data.get("full_name", "")).strip()
    if "profile_email" in data:
        profile_doc["profile_email"] = normalize_email(str(data.get("profile_email", "")).strip())

    if request.FILES.get("profile_image"):
        from api.storage import delete_media_file

        delete_media_file(profile_doc.get("profile_image_path"))
        profile_doc["profile_image_path"] = save_uploaded_file(
            request.FILES["profile_image"],
            "profiles",
            {"user_id": str(user["_id"]), "scope": "profile-image"},
        )

    if updates:
        updates["updated_at"] = _now()
        database.users.update_one({"_id": user["_id"]}, {"$set": updates})
        user.update(updates)

    profile_doc["updated_at"] = _now()
    database.user_profiles.update_one(
        {"_id": profile_doc["_id"]},
        {
            "$set": {
                "full_name": profile_doc.get("full_name", ""),
                "profile_email": profile_doc.get("profile_email", ""),
                "profile_image_path": profile_doc.get("profile_image_path"),
                "updated_at": profile_doc["updated_at"],
            }
        },
    )

    return json_response({"user": serialize_user(user), "profile": serialize_profile(profile_doc, request)})


@api_view
def projects(request: HttpRequest):
    user = get_authenticated_user(request)
    database = get_db()

    if request.method == "GET":
        q = request.GET.get("q", "").strip()
        order = request.GET.get("order", "-created_at")
        sort_map = {
            "created_at": ("created_at", 1),
            "-created_at": ("created_at", -1),
            "title": ("title", 1),
            "-title": ("title", -1),
        }
        sort_field, sort_direction = sort_map.get(order, ("created_at", -1))
        member_project_ids = database.project_members.distinct("project_id", {"user_id": user["_id"]})
        query = {"$or": [{"owner_id": user["_id"]}, {"_id": {"$in": member_project_ids}}]}
        if q:
            query["title"] = _regex_filter(q)

        project_rows = list(database.projects.find(query).sort(sort_field, sort_direction))
        results = []
        for project in project_rows:
            access_role = _project_access_role(user["_id"], project) or "viewer"
            members_count = database.project_members.count_documents({"project_id": project["_id"]})
            results.append(serialize_project(project, request, _load_project_tags(project), members_count, access_role))
        return json_response({"projects": results})

    require_methods(request, ["POST"])
    data = get_request_data(request)
    title = _require_text(data, "title")
    description = str(data.get("description", "")).strip()
    visibility_status = str(data.get("visibility_status", "private")).strip() or "private"
    now = _now()
    project = {
        "owner_id": user["_id"],
        "owner_email": user["email"],
        "title": title,
        "description": description,
        "visibility_status": visibility_status,
        "cover_image_path": None,
        "tag_ids": [],
        "created_at": now,
        "updated_at": now,
    }
    project_id = database.projects.insert_one(project).inserted_id
    project["_id"] = project_id

    if request.FILES.get("cover_image"):
        cover_image_path = save_uploaded_file(
            request.FILES["cover_image"],
            "project-covers",
            {"project_id": str(project_id), "user_id": str(user["_id"]), "scope": "project-cover"},
        )
        database.projects.update_one({"_id": project_id}, {"$set": {"cover_image_path": cover_image_path}})
        project["cover_image_path"] = cover_image_path

    return json_response({"project": serialize_project(project, request, [], 0, "owner")}, status=201)


@api_view
def project_detail(request: HttpRequest, project_id: str):
    database = get_db()

    if request.method == "GET":
        _, project, access_role = _get_accessible_project(request, project_id)
        return json_response({"project": _serialize_project_detail(project, request, access_role)})

    if request.method in {"PATCH", "POST"}:
        _, project = _get_owner_project(request, project_id)
        data = get_request_data(request)
        updates = {"updated_at": _now()}
        for field in ["title", "description", "visibility_status"]:
            if field in data:
                value = str(data.get(field, "")).strip()
                if field == "title" and not value:
                    raise ApiError("title is required.", 400, "missing_field")
                updates[field] = value

        if request.FILES.get("cover_image"):
            from api.storage import delete_media_file

            delete_media_file(project.get("cover_image_path"))
            updates["cover_image_path"] = save_uploaded_file(
                request.FILES["cover_image"],
                "project-covers",
                {"project_id": str(project["_id"]), "user_id": str(project["owner_id"]), "scope": "project-cover"},
            )

        database.projects.update_one({"_id": project["_id"]}, {"$set": updates})
        project.update(updates)
        return json_response({"project": _serialize_project_detail(project, request, "owner")})

    require_methods(request, ["DELETE"])
    _, project = _get_owner_project(request, project_id)
    cascade_delete_project(project)
    return json_response({"deleted": True})


@api_view
def project_members(request: HttpRequest, project_id: str):
    database = get_db()

    if request.method == "GET":
        _, project, _ = _get_accessible_project(request, project_id)
        members = list(database.project_members.find({"project_id": project["_id"]}).sort("added_at", 1))
        user_ids = [row["user_id"] for row in members if row.get("user_id")]
        users = {row["_id"]: row for row in database.users.find({"_id": {"$in": user_ids}})} if user_ids else {}
        return json_response({"members": [serialize_member(row, users.get(row.get("user_id"))) for row in members]})

    require_methods(request, ["POST"])
    _, project = _get_owner_project(request, project_id)
    data = get_request_data(request)
    email = normalize_email(_require_text(data, "email"))
    role = str(data.get("role", "collaborator")).strip() or "collaborator"

    existing = database.project_members.find_one({"project_id": project["_id"], "invited_email": email})
    if existing:
        raise ApiError("That member is already attached to the project.", 409, "member_exists")

    linked_user = database.users.find_one({"email": email})
    if not linked_user:
        raise ApiError("That email is not registered. Ask the user to create an account first.", 404, "user_not_registered")

    member = {
        "project_id": project["_id"],
        "user_id": linked_user["_id"],
        "invited_email": email,
        "role": role,
        "added_at": _now(),
    }
    member_id = database.project_members.insert_one(member).inserted_id
    member["_id"] = member_id
    return json_response({"member": serialize_member(member, linked_user)}, status=201)


@api_view
def project_member_detail(request: HttpRequest, project_id: str, member_id: str):
    require_methods(request, ["DELETE"])
    _, project = _get_owner_project(request, project_id)
    database = get_db()
    deleted = database.project_members.delete_one({"_id": to_object_id(member_id, "member_id"), "project_id": project["_id"]})
    if not deleted.deleted_count:
        raise ApiError("Member was not found.", 404, "member_not_found")
    return json_response({"deleted": True})


@api_view
def project_tags(request: HttpRequest, project_id: str):
    database = get_db()

    if request.method == "GET":
        _, project, _ = _get_accessible_project(request, project_id)
        return json_response({"tags": [serialize_tag(tag) for tag in _load_project_tags(project)]})

    require_methods(request, ["POST"])
    _, project = _get_owner_project(request, project_id)
    data = get_request_data(request)
    name = _require_text(data, "name").lower()

    tag = database.tags.find_one({"name": name})
    if not tag:
        tag = {"name": name, "created_at": _now()}
        tag_id = database.tags.insert_one(tag).inserted_id
        tag["_id"] = tag_id

    if tag["_id"] not in project.get("tag_ids", []):
        database.projects.update_one({"_id": project["_id"]}, {"$addToSet": {"tag_ids": tag["_id"]}, "$set": {"updated_at": _now()}})
        project.setdefault("tag_ids", []).append(tag["_id"])

    return json_response({"tag": serialize_tag(tag)}, status=201)


@api_view
def project_tag_detail(request: HttpRequest, project_id: str, tag_id: str):
    require_methods(request, ["DELETE"])
    _, project = _get_owner_project(request, project_id)
    tag_object_id = to_object_id(tag_id, "tag_id")
    get_db().projects.update_one({"_id": project["_id"]}, {"$pull": {"tag_ids": tag_object_id}, "$set": {"updated_at": _now()}})
    return json_response({"deleted": True})


@api_view
def documents(request: HttpRequest, project_id: str):
    user, project, _ = _get_accessible_project(request, project_id)
    database = get_db()

    if request.method == "GET":
        q = request.GET.get("q", "").strip()
        order = request.GET.get("order", "-uploaded_at")
        sort_map = {
            "uploaded_at": ("uploaded_at", 1),
            "-uploaded_at": ("uploaded_at", -1),
            "title": ("title", 1),
            "-title": ("title", -1),
        }
        sort_field, sort_direction = sort_map.get(order, ("uploaded_at", -1))
        query = {"project_id": project["_id"]}
        if q:
            query["title"] = _regex_filter(q)
        rows = list(database.documents.find(query).sort(sort_field, sort_direction))
        return json_response({"documents": [serialize_document(row, request) for row in rows]})

    require_methods(request, ["POST"])
    if not request.FILES.get("document"):
        raise ApiError("document file is required.", 400, "missing_file")

    data = get_request_data(request)
    uploaded_file = request.FILES["document"]
    thumbnail_image = request.FILES.get("thumbnail_image")
    title = str(data.get("title", "")).strip() or uploaded_file.name
    extension = uploaded_file.name.rsplit(".", 1)[-1].lower() if "." in uploaded_file.name else ""
    document_type = str(data.get("document_type", extension or "file")).strip() or "file"

    document_metadata = {"project_id": str(project["_id"]), "user_id": str(user["_id"])}
    file_path = save_uploaded_file(
        uploaded_file,
        "documents",
        {**document_metadata, "scope": "document-file"},
    )
    thumbnail_path = (
        save_uploaded_file(
            thumbnail_image,
            "document-thumbnails",
            {**document_metadata, "scope": "document-thumbnail"},
        )
        if thumbnail_image
        else None
    )
    now = _now()
    document = {
        "project_id": project["_id"],
        "uploaded_by_user_id": user["_id"],
        "title": title,
        "original_filename": uploaded_file.name,
        "document_type": document_type,
        "file_path": file_path,
        "thumbnail_image_path": thumbnail_path,
        "uploaded_at": now,
        "updated_at": now,
        "extracted_text": "",
        "chunk_count": 0,
        "indexing_status": "pending",
    }
    document_id = database.documents.insert_one(document).inserted_id
    document["_id"] = document_id

    try:
        rebuild_document_embeddings(document)
        document = database.documents.find_one({"_id": document_id})
    except Exception:
        database.documents.update_one(
            {"_id": document_id},
            {"$set": {"indexing_status": "failed", "updated_at": _now()}},
        )
        document = database.documents.find_one({"_id": document_id})

    return json_response({"document": serialize_document(document, request)}, status=201)


@api_view
def document_detail(request: HttpRequest, project_id: str, document_id: str):
    _, project, access_role = _get_accessible_project(request, project_id)
    database = get_db()
    document = database.documents.find_one({"_id": to_object_id(document_id, "document_id"), "project_id": project["_id"]})
    if not document:
        raise ApiError("Document was not found.", 404, "document_not_found")

    if request.method == "GET":
        return json_response({"document": serialize_document(document, request)})

    if request.method == "PATCH":
        if access_role not in {"owner", "editor"}:
            raise ApiError("You do not have permission to edit this document.", 403, "forbidden")
        data = get_request_data(request)
        updates = {"updated_at": _now()}
        if "title" in data:
            updates["title"] = _require_text(data, "title")
        if request.FILES.get("thumbnail_image"):
            from api.storage import delete_media_file

            delete_media_file(document.get("thumbnail_image_path"))
            updates["thumbnail_image_path"] = save_uploaded_file(
                request.FILES["thumbnail_image"],
                "document-thumbnails",
                {
                    "project_id": str(project["_id"]),
                    "user_id": str(document["uploaded_by_user_id"]),
                    "scope": "document-thumbnail",
                },
            )
        database.documents.update_one({"_id": document["_id"]}, {"$set": updates})
        document.update(updates)
        return json_response({"document": serialize_document(document, request)})

    require_methods(request, ["DELETE"])
    if access_role not in {"owner", "editor"}:
        raise ApiError("You do not have permission to delete this document.", 403, "forbidden")
    cascade_delete_document(document)
    return json_response({"deleted": True})


@api_view
def semantic_search(request: HttpRequest, project_id: str):
    require_methods(request, ["POST"])
    user, project, _ = _get_accessible_project(request, project_id)
    data = get_request_data(request)
    question = _require_text(data, "question")
    top_k = int(data.get("top_k", 5))
    top_k = min(max(top_k, 1), 10)

    matches = rank_project_matches(project["_id"], question, top_k)
    generated_answer = generate_grounded_answer(question, matches)
    log_row = {
        "project_id": project["_id"],
        "user_id": user["_id"],
        "query_text": question,
        "top_k": top_k,
        "created_at": _now(),
    }
    get_db().semantic_query_logs.insert_one(log_row)

    return json_response(
        {
            "project_id": str(project["_id"]),
            "question": question,
            "matches": matches,
            "generated_answer": generated_answer,
            "message": "Searching inside this project only.",
        }
    )


@api_view
def query_history(request: HttpRequest, project_id: str):
    require_methods(request, ["GET"])
    _, project, _ = _get_accessible_project(request, project_id)
    rows = list(get_db().semantic_query_logs.find({"project_id": project["_id"]}).sort("created_at", -1).limit(20))
    return json_response({"queries": [serialize_query_log(row) for row in rows]})


@api_view
def conversations(request: HttpRequest, project_id: str):
    user, project, _ = _get_accessible_project(request, project_id)
    database = get_db()

    if request.method == "GET":
        q = request.GET.get("q", "").strip()
        order = request.GET.get("order", "-last_updated")
        sort_map = {
            "last_updated": ("last_updated", 1),
            "-last_updated": ("last_updated", -1),
            "title": ("title", 1),
            "-title": ("title", -1),
        }
        sort_field, sort_direction = sort_map.get(order, ("last_updated", -1))
        query = {"project_id": project["_id"]}
        if q:
            query["title"] = _regex_filter(q)
        rows = list(database.conversations.find(query).sort(sort_field, sort_direction))
        return json_response({"conversations": [serialize_conversation(row) for row in rows]})

    require_methods(request, ["POST"])
    data = get_request_data(request)
    title = _require_text(data, "title")
    now = _now()
    conversation = {
        "project_id": project["_id"],
        "user_id": user["_id"],
        "title": title,
        "created_at": now,
        "last_updated": now,
    }
    conversation_id = database.conversations.insert_one(conversation).inserted_id
    conversation["_id"] = conversation_id
    return json_response({"conversation": serialize_conversation(conversation)}, status=201)


@api_view
def conversation_detail(request: HttpRequest, project_id: str, conversation_id: str):
    _, project, _ = _get_accessible_project(request, project_id)
    database = get_db()
    conversation = database.conversations.find_one({"_id": to_object_id(conversation_id, "conversation_id"), "project_id": project["_id"]})
    if not conversation:
        raise ApiError("Conversation was not found.", 404, "conversation_not_found")

    if request.method == "GET":
        messages = list(database.messages.find({"conversation_id": conversation["_id"], "project_id": project["_id"]}).sort("created_at", 1))
        return json_response(
            {
                "conversation": serialize_conversation(conversation),
                "messages": [serialize_message(row) for row in messages],
            }
        )

    require_methods(request, ["DELETE"])
    database.messages.delete_many({"conversation_id": conversation["_id"]})
    database.conversations.delete_one({"_id": conversation["_id"]})
    return json_response({"deleted": True})


@api_view
def conversation_messages(request: HttpRequest, project_id: str, conversation_id: str):
    require_methods(request, ["POST"])
    _, project, _ = _get_accessible_project(request, project_id)
    database = get_db()
    conversation = database.conversations.find_one({"_id": to_object_id(conversation_id, "conversation_id"), "project_id": project["_id"]})
    if not conversation:
        raise ApiError("Conversation was not found.", 404, "conversation_not_found")

    data = get_request_data(request)
    sender_type = str(data.get("sender_type", "user")).strip() or "user"
    content = _require_text(data, "content")
    source_matches = data.get("source_matches") or []
    if not isinstance(source_matches, list):
        source_matches = []

    now = _now()
    message = {
        "project_id": project["_id"],
        "conversation_id": conversation["_id"],
        "sender_type": sender_type,
        "content": content,
        "source_matches": source_matches,
        "created_at": now,
    }
    message_id = database.messages.insert_one(message).inserted_id
    message["_id"] = message_id
    database.conversations.update_one({"_id": conversation["_id"]}, {"$set": {"last_updated": now}})
    return json_response({"message": serialize_message(message)}, status=201)
