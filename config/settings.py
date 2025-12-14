from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-tu-clave-secreta-aqui'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*'] # Permitir todo por ahora (para Railway/Render)

# Application definition

INSTALLED_APPS = [
    'jazzmin',              # <--- 1. Diseño Admin (Primero)
    'django.contrib.admin', # <--- 2. Admin Original (Después)
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic', # <--- Optimización local
    'django.contrib.staticfiles',
    
    # Mis Apps
    'rest_framework',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware", # <--- ¡MOTOR DE LA NUBE! (Vital)
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
        'DIRS': [BASE_DIR / 'core' / 'templates'], # <--- Ruta forzada para encontrar index.html
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

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'es-co' # Español Colombia

TIME_ZONE = 'America/Bogota' # Hora Uniandes

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles' # <--- Carpeta para la nube
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage" # <--- Compresión

# Media files (FOTOS DE COMPROBANTES)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Usuario Personalizado
AUTH_USER_MODEL = 'core.User'

# --- CONFIGURACIÓN DE CORREO (SIMULADO) ---
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# --- SEGURIDAD DE SESIONES ---
SESSION_COOKIE_AGE = 600 # 10 minutos
SESSION_SAVE_EVERY_REQUEST = True 
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
LOGOUT_REDIRECT_URL = '/admin/login/'

# --- CONFIGURACIÓN DE JAZZMIN (DISEÑO) ---
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