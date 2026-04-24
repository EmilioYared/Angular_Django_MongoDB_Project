from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.http import HttpRequest

from api.db import get_db, to_object_id
from api.http import ApiError


TOKEN_TTL_DAYS = 7


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    return make_password(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return check_password(password, hashed_password)


def create_access_token(user: dict) -> str:
    payload = {
        "sub": str(user["_id"]),
        "email": user["email"],
        "username": user["username"],
        "exp": datetime.now(timezone.utc) + timedelta(days=TOKEN_TTL_DAYS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def get_bearer_token(request: HttpRequest) -> str:
    header = request.headers.get("Authorization", "")
    prefix = "Bearer "
    if not header.startswith(prefix):
        raise ApiError("Authentication credentials were not provided.", 401, "missing_token")
    return header[len(prefix) :].strip()


def get_authenticated_user(request: HttpRequest) -> dict:
    token = get_bearer_token(request)
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.InvalidTokenError as exc:
        raise ApiError("Invalid or expired token.", 401, "invalid_token") from exc

    user_id = payload.get("sub")
    if not user_id:
        raise ApiError("Invalid token payload.", 401, "invalid_token")

    user = get_db().users.find_one({"_id": to_object_id(user_id, "user_id")})
    if not user:
        raise ApiError("User was not found.", 401, "invalid_user")
    return user
