from django.contrib import admin
from django.urls import path, include

from rest_framework.routers import DefaultRouter
from .views import ContractAnalysisViewSet

# استخدام DefaultRouter لإنشاء جميع مسارات CRUD تلقائياً وبشكل احترافي
# (CREATE, READ, UPDATE, DELETE)
router = DefaultRouter()

# هذا سينشئ المسارات التالية (وغيرها):
# GET /api/contracts/         : لجلب جميع عقود المستخدم (قاعدة البيانات)
# POST /api/contracts/        : لرفع عقد جديد (قاعدة البيانات)
# GET /api/contracts/{id}/    : لجلب عقد محدد (قاعدة البيانات)
# POST /api/contracts/{id}/run_analysis/ : لتشغيل التحليل (الذكاء الاصطناعي)
router.register(r'contracts', ContractAnalysisViewSet, basename='contract')

urlpatterns = router.urls