import ipaddress
from datetime import timedelta
from pathlib import Path

from decouple import config  # pip install python-decouple

# === 기본 보안/환경 ===
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = config("SECRET_KEY")
DEBUG = False  # 공통은 False, dev에서만 True로 override

# === Allowed Hosts / CSRF ===
DJANGO_ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="")
ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    ".ngrok-free.app",
    "i13e102.p.ssafy.io",
    "ios.kr",
    "www.ios.kr",
    "alpacar.kr",
    "www.alpacar.kr",
]
CSRF_TRUSTED_ORIGINS = [
    "https://i13e102.p.ssafy.io",
    "https://ios.kr",
    "https://www.ios.kr",
    "https://alpacar.kr",
    "https://www.alpacar.kr",
]

# === Static ===
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]


# === Apps ===
INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "channels",
    "accounts",
    "streamapp",
    "vehicles",
    "parking",
    "events.apps.EventsConfig",
    "jetson",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    # DRF + JWT
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "corsheaders",
    "drf_yasg",
]

SWAGGER_SETTINGS = {
    "USE_SESSION_AUTH": False,
    "VALIDATOR_URL": None,
    "SECURITY_DEFINITIONS": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "중요! JWT 토큰을 Authorization 헤더에 “Bearer <token>” 형태로 입력하세요.",
        }
    },
    "SECURITY_REQUIREMENTS": [{"Bearer": []}],
}

# 192.168.0.0/16 대역을 모두 추가
network = ipaddress.ip_network("192.168.0.0/16")
# hosts() 대신 network itself를 허용하면 네트워크 주소도 함께 허용합니다.
ALLOWED_HOSTS += [str(ip) for ip in network.hosts()]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "formatters": {
        "simple": {
            "format": "[{levelname}] {name}:{lineno} {message}",
            "style": "{",
        },
    },
    "loggers": {
        # Django 요청
        "django": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        # Channels/WebSocket 라우터
        "channels": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "channels.routing": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    },
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": config("DB_NAME", default="alpaca_car"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="3306"),
    }
}

LOGIN_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_ON_GET = True

# allauth
SITE_ID = 1
AUTH_USER_MODEL = "accounts.User"
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_EMAIL_FIELD = "email"

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        # 요청할 권한 범위 (프로필·이메일)
        "SCOPE": [
            "profile",
            "email",
        ],
        # 추가 인증 파라미터
        "AUTH_PARAMS": {
            "access_type": "online",  # 'offline'으로 하면 refresh token 발급
        },
        # PKCE 사용 여부 (보안 강화)
        "OAUTH_PKCE_ENABLED": True,
        "APP": {
            "client_id": config("GOOGLE_CLIENT_ID"),  # 구글 API 콘솔에서 발급받은 ID
            "secret": config(
                "GOOGLE_CLIENT_SECRET"
            ),  # 구글 API 콘솔에서 발급받은 Secret
            "key": "",  # 일반적으로 비워둠
        },
    }
}


# dj‑rest‑auth 소셜 설정
REST_USE_JWT = True
JWT_AUTH_COOKIE = None  # 쿠키가 아닌 헤더로

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:8000",
    "https://i13e102.p.ssafy.io",
    "https://ios.kr",
    "https://www.ios.kr",
    "https://alpacar.kr",
    "https://www.alpacar.kr",
]

ROOT_URLCONF = "djangoApp.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "djangoApp.wsgi.application"
ASGI_APPLICATION = "djangoApp.asgi.application"

# WebSocket을 위해 최소한 In‑Memory 레이어 추가
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

VAPID_PUBLIC_KEY = config("VAPID_PUBLIC_KEY")
VAPID_PRIVATE_KEY = config("VAPID_PRIVATE_KEY")
VAPID_CLAIMS = {"sub": config("VAPID_CLAIM_SUB")}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.naver.com"  # 사용하시는 메일 서비스에 맞게
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config("SMTP_USER")  # 환경변수로 관리 추천
EMAIL_HOST_PASSWORD = config("SMTP_PASS")
DEFAULT_FROM_EMAIL = config("SMTP_DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER)


LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Seoul"

USE_I18N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
