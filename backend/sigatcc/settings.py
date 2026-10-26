import os
from datetime import timedelta
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
    "rest_framework_simplejwt.token_blacklist",
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

# RBN29: minimo de 8 caracteres, com maiuscula, numero e caractere especial
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "core.validators.SenhaForteValidator"},
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

# --- API e autenticacao (B5) ---
JWT_SIGNING_KEY = os.environ.get("JWT_SIGNING_KEY", SECRET_KEY)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
}

# RNF02: sessao de 30 min. O access dura 15 min e o refresh 30 min; como o refresh
# e trocado a cada uso, a sessao so expira apos 30 min sem atividade.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(minutes=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "SIGNING_KEY": JWT_SIGNING_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# --- Producao e homologacao (B11) ---
# O TLS termina no proxy (Caddy/nginx); ele avisa o Django pelo X-Forwarded-Proto.
CSRF_TRUSTED_ORIGINS = _lista("CSRF_TRUSTED_ORIGINS")
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = (
        os.environ.get("DJANGO_SSL_REDIRECT", "True").lower() == "true"
    )
    SECURE_REDIRECT_EXEMPT = [r"^saude/$"]  # o healthcheck interno usa HTTP
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", "0"))
    X_FRAME_OPTIONS = "DENY"
    # Sem DEBUG a API fala so JSON (a pagina navegavel do DRF precisa de estaticos)
    REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
        "rest_framework.renderers.JSONRenderer"
    ]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {
        "handlers": ["console"],
        "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
    },
}
