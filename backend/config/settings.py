import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
load_dotenv(PROJECT_ROOT / ".env.local")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "projectnest-dev-secret-key-2026-long")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = [host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,testserver").split(",") if host.strip()]
if DEBUG and "*" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("*")

INSTALLED_APPS = [
    "corsheaders",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "api",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Beirut"

USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = PROJECT_ROOT / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

APPEND_SLASH = True

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:4200,http://127.0.0.1:4200",
    ).split(",")
    if origin.strip()
]
CORS_ALLOW_ALL_ORIGINS = DEBUG and os.getenv("CORS_ALLOW_ALL_ORIGINS", "true").lower() == "true"
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

MONGODB_URI = os.getenv("ATLAS_SRV_STRING", "")
MONGODB_DB_NAME = os.getenv("ATLAS_DB_NAME", "projectnest")

OPENROUTER_API_KEY = os.getenv("OPEN_ROUTER_API") or os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_EMBEDDING_MODEL = os.getenv(
    "OPENROUTER_EMBEDDING_MODEL", "nvidia/llama-nemotron-embed-vl-1b-v2:free"
)
OPENROUTER_CHAT_MODEL = os.getenv(
    "OPENROUTER_CHAT_MODEL", "openai/gpt-oss-120b:free"
)
JWT_SECRET = os.getenv("JWT_SECRET", SECRET_KEY)
