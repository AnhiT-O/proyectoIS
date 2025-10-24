import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno desde el archivo .env en el directorio raíz del proyecto
# El .env está un nivel arriba del directorio 'proyecto'
load_dotenv(BASE_DIR.parent / '.env')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY_PROYECTO')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']


# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'usuarios',
    'clientes',
    'roles',
    'monedas',
    'transacciones',
    'corsheaders',
    'medios_acreditacion'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware'
]

# Configuración de internacionalización
LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Asuncion'
USE_L10N = True
USE_I18N = True
USE_TZ = True

ROOT_URLCONF = 'proyecto.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'proyecto.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'bd_desarrollo',
        'USER': 'postgres',
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

# Validaciones de contraseña deshabilitadas - se manejan en forms.py
AUTH_PASSWORD_VALIDATORS = []

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'usuarios.Usuario'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587  # Puerto estándar para TLS
EMAIL_USE_TLS = True  # Habilitar seguridad TLS
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

# Configuración de mensajes de Django
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'error',
}

# Configuración de login/logout
LOGIN_URL = '/ingresar/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
PASSWORD_RESET_TIMEOUT = 3600

# Configuración de permisos personalizados
# NOTA: Para deshabilitar permisos automáticos, usa default_permissions = [] en cada modelo
# Silencia warnings sobre permisos faltantes ya que usas permisos personalizados
SILENCED_SYSTEM_CHECKS = ['auth.W004']

# Manejador personalizado para errores 403
HANDLER403 = 'proyecto.views.custom_permission_denied_view'

SESSION_COOKIE_AGE = 10 * 60  # 10 minutos de inactividad y se cierra la sesión
SESSION_SAVE_EVERY_REQUEST = True

STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5500",  # URL donde se sirve la pasarela
]

CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'OPTIONS',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Configuración de 2FA para transacciones
ENABLE_2FA_TRANSACTIONS = False # Cambiar a False para deshabilitar completamente el 2FA

# Configuración específica del 2FA
TWO_FACTOR_AUTH = {
    'TOKEN_LENGTH': 6,  # Longitud del token
    'TOKEN_EXPIRY_MINUTES': 1,  # Tiempo de expiración en minutos
    'EMAIL_SUBJECT': 'Código de verificación - Global Exchange',
    'EMAIL_FROM': os.environ.get('EMAIL_HOST_USER'),
}

# Configuración de Factura Segura
FACTURA_SEGURA_API_URL = 'https://apitest.facturasegura.com.py'
NUMERO_FACTURACION = 351