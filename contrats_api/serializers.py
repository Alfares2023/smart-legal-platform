from rest_framework import serializers
from .models import Contract, ServiceRequest, UserProfile
from django.contrib.auth.models import User


# 1. مُسلسِل ملف المستخدم (لإظهار مستوى الاشتراك)
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['subscription_level', 'tokens_remaining']  # نُظهر فقط معلومات الاشتراك والتوكنز


# 2. مُسلسِل بيانات المستخدم الأساسية
class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()  # تضمين ملف المستخدم الإضافي (الاحترافية)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']


# 3. مُسلسِل العقود (Contract Serializer)
# هذا هو أهم مُسلسِل، يستخدم لإدارة العقود (الأيقونة 1 و 3)
class ContractSerializer(serializers.ModelSerializer):
    # نستخدم UserSerializer للقراءة فقط لإظهار من هو صاحب العقد
    user = UserSerializer(read_only=True)

    # نستخدم حقل منفصل للمعرف (ID) الخاص بالمستخدم عند الإنشاء/التحديث
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Contract
        # الحقول التي سنتعامل معها في الـ API
        fields = [
            'id',
            'user',
            'user_id',
            'title',
            'original_text',
            'status',
            'analysis_results',
            'created_at'
        ]
        # جعل حقول النتائج للقراءة فقط عند العرض
        read_only_fields = ['status', 'analysis_results', 'created_at']

    # 4. مُسلسِل طلبات الخدمة (ServiceRequest Serializer)


# لتتبع طلبات التحليل والتوليد (الأيقونة 4)
class ServiceRequestSerializer(serializers.ModelSerializer):
    # حقل للقراءة فقط لإظهار نوع الخدمة بشكل واضح
    service_type_display = serializers.CharField(source='get_service_type_display', read_only=True)

    class Meta:
        model = ServiceRequest
        fields = [
            'id',
            'user',
            'service_type',
            'service_type_display',
            'tokens_used',
            'is_paid',
            'request_timestamp'
        ]
        read_only_fields = ['user', 'tokens_used', 'is_paid', 'request_timestamp']