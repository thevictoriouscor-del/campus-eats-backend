from pathlib import Path
import os
import dj_database_url # <--- IMPORTANTE: Librería para leer la base de datos de la nube

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# En la nube leerá la variable, en local usa la insegura por defecto
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-tu-clave-secreta-aqui')

# SECURITY WARNING: don't run with debug turned on in production!
# En la nube será False automáticamente si configuras la variable RENDER
DEBUG = 'RENDER' not in os.environ

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'rest_framework',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# --- BASE DE DATOS INTELIGENTE (SQLite Local / PostgreSQL Nube) ---
# Si existe la variable DATABASE_URL (en Render), usa PostgreSQL.
# Si no (en tu PC), usa el archivo db.sqlite3.
DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media files (FOTOS)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'core.User'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Seguridad de Sesiones
SESSION_COOKIE_AGE = 600 
SESSION_SAVE_EVERY_REQUEST = True 
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
LOGOUT_REDIRECT_URL = '/admin/login/'

# Diseño Admin
JAZZMIN_SETTINGS = {
    "site_title": "Campus Eats Admin",
    "site_header": "Campus Eats",
    "site_brand": "Campus Eats",
    "welcome_sign": "Bienvenido al Centro de Comando",
    "copyright": "Campus Eats Ltd",
    "search_model": "core.User",
    "topmenu_links": [{"name": "Ver Sitio Web", "url": "home", "permissions": ["auth.view_user"]}],
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "auth": "fas fa-users-cog",
        "core.User": "fas fa-user",
        "core.Restaurante": "fas fa-store",
        "core.Producto": "fas fa-hamburger",
        "core.Pedido": "fas fa-motorcycle",
    },
}

JAZZMIN_UI_TWEAKS = {
    "theme": "darkly",
    "brand_colour": "warning",
    "accent": "accent-warning",
    "navbar": "navbar-dark",
    "sidebar": "sidebar-dark-warning",
    "button_classes": {
        "primary": "btn-warning",
        "secondary": "btn-outline-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}