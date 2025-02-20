from pathlib import Path

import toml

BASE_DIR = Path(__file__).resolve().parent.parent

_config = toml.load(BASE_DIR / "config.toml")

SECRET_KEY = _config["DJANGO"]["SECRET_KEY"]

DEBUG = _config["DJANGO"]["DEBUG"]
ENABLE_HMAC_VALIDATION = _config["HMAC"]["ENABLE"]

ALLOWED_HOSTS = _config["DJANGO"]["ALLOWED_HOSTS"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "playtime",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "settings.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "settings.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _config["POSTGRES"]["DATABASE_NAME"],
        "USER": _config["POSTGRES"]["USER"],
        "PASSWORD": _config["POSTGRES"]["PASSWORD"],
        "HOST": _config["POSTGRES"]["HOST"],
        "PORT": _config["POSTGRES"]["PORT"],
    }
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


LANGUAGE_CODE = _config["DJANGO"]["LANGUAGE_CODE"]

TIME_ZONE = _config["DJANGO"]["TIME_ZONE"]

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# STEAM API
STEAM_API_KEY = _config["STEAM"]["KEY"]
STEAM_API_TIMEOUT = _config["STEAM"]["TIMEOUT"]

BATTLEMETRICS_SIGNATURE_REGEX = r"(?<=s=)\w+(?=,|\Z)"
BATTLEMETRICS_TIMESTAMP_REGEX = r"(?<=t=)[\w\-:.+]+(?=,|\Z)"
HMAC_TIMESTAMP_DEVIATION = _config["HMAC"]["TIMESTAMP_DEVIATION"]
