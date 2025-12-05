import os
from decouple import config # لاستيراد البيانات من ملف .env

# Base directory setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# الأمن (Security) - يتم تحميله من .env
SECRET_KEY = config('SECRET_KEY', default='django-insecure-fallback-key-for-dev')

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['*'] # يجب تعديله في الإنتاج

# التطبيقات المثبتة (Installed Apps)
INSTALLED_APPS = [
    # Django Core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third Party Apps
    'rest_framework', # الواجهة الاحترافية للـ API
    'corsheaders', # ضروري لربط React (الواجهة الأمامية) بالخادم

    # Local Apps (تطبيقنا الخاص)
    'contracts_api',
]

# إعدادات قاعدة البيانات
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': '5432', # منفذ PostgreSQL الافتراضي
    }
}
# إعدادات CORS (ضروري للربط بـ React)
# سيسمح React (الذي يعمل على منفذ مختلف) بالتواصل مع Django
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000", # مثال لمنفذ React المحلي
    "http://127.0.0.1:3000",
    # يجب إضافة نطاق الـ React النهائي هنا (مثل https://your-legal-frontend.com)
]