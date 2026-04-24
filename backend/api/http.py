from __future__ import annotations

import json
import traceback
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt


@dataclass
class ApiError(Exception):
    message: str
    status_code: int = 400
    code: str | None = None


def json_response(payload: Any, status: int = 200) -> JsonResponse:
    return JsonResponse(payload, status=status, safe=not isinstance(payload, list))


def parse_json_body(request: HttpRequest) -> dict[str, Any]:
    if not request.body:
        return {}
    try:
        parsed = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ApiError("Invalid JSON body.", 400, "invalid_json") from exc
    if not isinstance(parsed, dict):
        raise ApiError("JSON body must be an object.", 400, "invalid_json")
    return parsed


def get_request_data(request: HttpRequest) -> dict[str, Any]:
    content_type = request.content_type or ""
    if content_type.startswith("application/json"):
        return parse_json_body(request)
    return request.POST.dict()


def api_view(view_func: Callable[..., JsonResponse]) -> Callable[..., JsonResponse]:
    @csrf_exempt
    @wraps(view_func)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        try:
            return view_func(request, *args, **kwargs)
        except ApiError as exc:
            payload = {"error": exc.message}
            if exc.code:
                payload["code"] = exc.code
            return json_response(payload, status=exc.status_code)
        except Exception:
            traceback.print_exc()
            return json_response({"error": "Internal server error."}, status=500)

    return wrapper


def require_methods(request: HttpRequest, allowed: list[str]) -> None:
    if request.method not in allowed:
        raise ApiError(f"Method {request.method} is not allowed.", 405, "method_not_allowed")
