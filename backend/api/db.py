from __future__ import annotations

from functools import lru_cache

from bson import ObjectId
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.database import Database

_indexes_ready = False


@lru_cache(maxsize=1)
def get_client() -> MongoClient:
    if not settings.MONGODB_URI:
        raise ImproperlyConfigured("ATLAS_SRV_STRING is not configured.")
    return MongoClient(settings.MONGODB_URI)


@lru_cache(maxsize=1)
def get_db() -> Database:
    database = get_client()[settings.MONGODB_DB_NAME]
    ensure_indexes(database)
    return database


def ensure_indexes(database: Database) -> None:
    global _indexes_ready
    if _indexes_ready:
        return

    database.users.create_index([("email", ASCENDING)], unique=True)
    database.users.create_index([("username", ASCENDING)], unique=True)
    database.user_profiles.create_index([("user_id", ASCENDING)], unique=True)
    database.projects.create_index([("owner_id", ASCENDING), ("created_at", DESCENDING)])
    database.project_members.create_index([("project_id", ASCENDING), ("invited_email", ASCENDING)], unique=True)
    database.project_members.create_index([("project_id", ASCENDING), ("user_id", ASCENDING)])
    database.tags.create_index([("name", ASCENDING)], unique=True)
    database.documents.create_index([("project_id", ASCENDING), ("uploaded_at", DESCENDING)])
    database.document_chunks.create_index([("project_id", ASCENDING), ("document_id", ASCENDING), ("chunk_index", ASCENDING)])
    database.chunk_embeddings.create_index([("project_id", ASCENDING), ("chunk_id", ASCENDING), ("model_name", ASCENDING)])
    database.semantic_query_logs.create_index([("project_id", ASCENDING), ("created_at", DESCENDING)])
    database.conversations.create_index([("project_id", ASCENDING), ("last_updated", DESCENDING)])
    database.messages.create_index([("project_id", ASCENDING), ("conversation_id", ASCENDING), ("created_at", ASCENDING)])
    _indexes_ready = True


def to_object_id(value: str, field_name: str = "id") -> ObjectId:
    if not ObjectId.is_valid(value):
        raise ValueError(f"Invalid {field_name}.")
    return ObjectId(value)
