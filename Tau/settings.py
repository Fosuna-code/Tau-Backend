"""
Django settings for Tau project.
"""

from pathlib import Path
import os
from datetime import timedelta # <--- Added for JWT Expiration settings
from gqlauth.settings_type import GqlAuthSettings # <--- Added for GqlAuth config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-qs36i#k6kewr98bl%c5d%0acg-vz*etm$s9cd2gad0wd7qt2^h").replace('"', '')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1 localhost pgaebbga2s.us-east-1.awsapprunner.com").split(" ")

# --- 1. CORS CONFIGURATION (Updated for Cookies) ---
# We cannot use ALLOW_ALL_ORIGINS = True if we want to use Cookies (Credentials).
# We must list the origins explicitly.
CORS_ALLOW_CREDENTIALS = True 
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5173",
    "https://production.d1hn7bwhpawu23.amplifyapp.com",
]
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000", 
    "http://127.0.0.1:3000",
    "http://localhost:8000", 
    "http://127.0.0.1:8000",
    "http://localhost:5173",
    "https://production.d1hn7bwhpawu23.amplifyapp.com",
]

AUTH_USER_MODEL = 'users.CustomUser'

# --- 2. AUTHENTICATION BACKENDS ---
AUTHENTICATION_BACKENDS = [
    "users.backends.EmailBackend",  # Custom backend for email-based login
    "django.contrib.auth.backends.ModelBackend",  # Default Django backend
    # Note: JWT authentication is handled by gqlauth.core.middlewares.django_jwt_middleware
    # in the MIDDLEWARE section, not here
]


# --- 3. EMAIL BACKEND ---
# Check for SMTP credentials in environment
if os.environ.get('EMAIL_HOST_USER') and os.environ.get('EMAIL_HOST_PASSWORD'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)
else:
    # Fallback to console for development if no credentials provided
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# --- 4. GQLAUTH SETTINGS ---
# Email-based login is handled by the custom EmailBackend in AUTHENTICATION_BACKENDS
# The tokenAuth mutation accepts a 'username' parameter, but our EmailBackend
# will recognize email addresses (containing '@') and authenticate accordingly
GQL_AUTH = GqlAuthSettings(
    LOGIN_REQUIRE_CAPTCHA=False,
    REGISTER_REQUIRE_CAPTCHA=False,
    ALLOW_LOGIN_NOT_VERIFIED=False, # Enforce verification
    SEND_ACTIVATION_EMAIL=True,
    ACTIVATION_PATH_ON_EMAIL="activate-account",
)
GRAPHQL_JWT = {
    "JWT_VERIFY_EXPIRATION": True,
    "JWT_LONG_RUNNING_REFRESH_TOKEN": True,
    "JWT_ALLOW_ANY_CLASSES": [
        "strawberry.types.execution.ExecutionContext",
    ],
    "JWT_EXPIRATION_DELTA": timedelta(minutes=15),
    "JWT_REFRESH_EXPIRATION_DELTA": timedelta(days=7),
    
    # Cookie Configuration
    "JWT_AUTH_COOKIE": "tau_auth_token",
    "JWT_AUTH_REFRESH_COOKIE": "tau_refresh_token",
    
    # HttpOnly and Security Settings
    "JWT_COOKIE_HTTPONLY": True,           # Prevents JavaScript access (XSS protection)
    "JWT_COOKIE_SECURE": False,            # Set to True in production (requires HTTPS)
    "JWT_COOKIE_SAMESITE": "Lax",          # CSRF protection (Lax allows navigation)
}

# Required by gqlauth to initialize, even if you don't use Stripe
STRIPE_PUBLISHABLE_KEY = "dummy"

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    
    # Third Party
    'strawberry_django',
    'imagekit',
    'corsheaders',
    "gqlauth",

    # Local Apps
    'streaming',
    'users',
]

# --- 5. MIDDLEWARE (Order is Critical) ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    
    'corsheaders.middleware.CorsMiddleware', # <--- MOVED UP (Must be before CommonMiddleware)
    
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    
    'gqlauth.core.middlewares.django_jwt_middleware', # <--- ADDED (Must be after AuthMiddleware)
    
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = "Tau.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
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

WSGI_APPLICATION = "Tau.wsgi.application"


# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "tau_db"),
        "USER": os.environ.get("POSTGRES_USER", "tau_user"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "tau_password"),
        "HOST": os.environ.get("POSTGRES_HOST", "db"),
        "PORT": "5432",
    }
}


# Password validation
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


# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"

# Media files (uploads)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
STATIC_ROOT = BASE_DIR / "static"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# File Upload Handlers for GraphQL
FILE_UPLOAD_HANDLERS = [
    "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler",
]