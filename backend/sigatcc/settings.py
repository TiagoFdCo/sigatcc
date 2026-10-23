import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def _lista(nome, padrao=""):
    return [
        item.strip() for item in os.environ.get(nome, padrao).split(",") if item.strip()
    ]


DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() == "true"

# Em producao a chave e obrigatoria; so em DEBUG existe uma chave de desenvolvimento.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or (
    "chave-insegura-so-para-dev" if DEBUG else None
)
if not SECRET_KEY:
    raise RuntimeError(
        "Defina DJANGO_SECRET_KEY (ou DJANGO_DEBUG=True em desenvolvimento)."
    )

ALLOWED_HOSTS = _lista("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "core",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "sigatcc.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "sigatcc.wsgi.application"

# Le a variavel DATABASE_URL (ex.: postgres://usuario:senha@host:5432/banco)
DATABASES = {"default": dj_database_url.config(env="DATABASE_URL", conn_max_age=600)}

AUTH_USER_MODEL = "core.Usuario"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Manaus"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# SPA em outra origem (decisao do plano): so os dominios listados chamam a API
CORS_ALLOWED_ORIGINS = _lista("CORS_ALLOWED_ORIGINS", "http://localhost:5173")

# A configuracao de JWT (djangorestframework-simplejwt) entra no B5 (login).
# A chave ja vem do ambiente: JWT_SIGNING_KEY.
JWT_SIGNING_KEY = os.environ.get("JWT_SIGNING_KEY", SECRET_KEY)
