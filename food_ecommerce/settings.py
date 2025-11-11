import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-=2(g(n=jwk!x2)@&hztqcl)!5i=1ehek@c%8ox4y#0v^rxq-g@'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'ecommerce',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'food_ecommerce.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
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

WSGI_APPLICATION = 'food_ecommerce.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'food_db',     
        'USER': 'postgres',      
        'PASSWORD': 'cp7kvt',
        'HOST': 'localhost',              
        'PORT': '5432',                    
    }
}



# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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


# ==================== TIMEZONE ====================

# Kenya timezone
TIME_ZONE = 'Africa/Nairobi'
USE_TZ = True

# ==================== MEDIA FILES ====================

# For food item images
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ==================== STATIC FILES ====================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==================== M-PESA CONFIGURATION ====================

# M-Pesa Credentials (Get these from Daraja API Portal: https://developer.safaricom.co.ke)
MPESA_ENVIRONMENT = 'sandbox'  # Change to 'production' for live

# Sandbox Credentials (Replace with your own)
MPESA_CONSUMER_KEY = 'your_consumer_key_here'
MPESA_CONSUMER_SECRET = 'your_consumer_secret_here'
MPESA_SHORTCODE = '174379'  # Sandbox paybill number
MPESA_PASSKEY = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'  # Sandbox passkey

# Production Credentials (Uncomment when going live)
# MPESA_CONSUMER_KEY = 'your_production_consumer_key'
# MPESA_CONSUMER_SECRET = 'your_production_consumer_secret'
# MPESA_SHORTCODE = 'your_production_paybill'
# MPESA_PASSKEY = 'your_production_passkey'

# M-Pesa API URLs
if MPESA_ENVIRONMENT == 'sandbox':
    MPESA_AUTH_URL = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    MPESA_STK_PUSH_URL = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    MPESA_QUERY_URL = 'https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query'
else:
    MPESA_AUTH_URL = 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    MPESA_STK_PUSH_URL = 'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    MPESA_QUERY_URL = 'https://api.safaricom.co.ke/mpesa/stkpushquery/v1/query'

# Callback URL (Must be publicly accessible - use ngrok for testing)
# For production, use your actual domain
MPESA_CALLBACK_URL = 'https://your-domain.com/mpesa/callback/'  
# For testing with ngrok: 'https://xxxx-xx-xxx-xxx-xx.ngrok.io/mpesa/callback/'


# ==================== EMAIL CONFIGURATION ====================

# Email Settings (for sending receipts)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'  # Use app password for Gmail
DEFAULT_FROM_EMAIL = 'Muranga University Mess <your-email@gmail.com>'
CONTACT_EMAIL = 'admin@murangauniversity.ac.ke'

# ==================== SESSION CONFIGURATION ====================

# Session settings for cart
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = True

