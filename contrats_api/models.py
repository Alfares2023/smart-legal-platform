from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# 1. نموذج العقود (Contract Model)
# لتخزين جميع العقود المرفوعة أو المولدة من قبل المستخدمين.
class Contract(models.Model):
    # ربط العقد بالمستخدم الذي قام بإنشائه أو رفعه.
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contracts', verbose_name="المستخدم")

    # خيارات حالة العقد
    STATUS_CHOICES = [
        ('UPL', 'تم الرفع'),
        ('GEN', 'تم التوليد'),
        ('ARC', 'أرشيف'),
    ]

    title = models.CharField(max_length=255, verbose_name="عنوان العقد")
    original_text = models.TextField(verbose_name="النص الأصلي للعقد")
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default='UPL', verbose_name="الحالة")

    # نتائج التحليل (لتخزين نتائج الذكاء الاصطناعي)
    # نستخدم JSONField لأنه مرن ويسمح بتخزين نتائج معقدة.
    analysis_results = models.JSONField(null=True, blank=True, verbose_name="نتائج التحليل والمخاطر")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "عقد"
        verbose_name_plural = "العقود"
        ordering = ['-created_at']  # عرض الأحدث أولاً

    def __str__(self):
        return f"{self.title} للمستخدم {self.user.username}"


# ---

# 2. نموذج طلب الخدمة (ServiceRequest Model)
# هذا النموذج بالغ الأهمية لخاصية التسعير/الفوترة (الأيقونة 4) وتتبع استخدام الذكاء الاصطناعي.
class ServiceRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_requests', verbose_name="المستخدم")
    # قد يكون الطلب مرتبطاً بعقد موجود (لتحليله) أو غير مرتبط (لإنشاء عقد جديد).
    related_contract = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True,
                                         verbose_name="العقد المرتبط")

    SERVICE_TYPE_CHOICES = [
        ('ANL', 'تحليل العقد'),
        ('GEN', 'توليد العقد'),
        ('QRY', 'استعلام قاعدة البيانات الذكية'),
    ]
    service_type = models.CharField(max_length=3, choices=SERVICE_TYPE_CHOICES, verbose_name="نوع الخدمة المطلوبة")

    # تتبع التكلفة (ضروري جداً عند استخدام نماذج OpenAI/Gemini القائمة على التوكنز)
    tokens_used = models.IntegerField(default=0, verbose_name="عدد التوكنز المستخدمة")
    is_paid = models.BooleanField(default=False, verbose_name="تم الدفع (أو ضمن الاشتراك)")

    request_timestamp = models.DateTimeField(default=timezone.now, verbose_name="وقت الطلب")

    class Meta:
        verbose_name = "طلب خدمة"
        verbose_name_plural = "طلبات الخدمات"
        ordering = ['-request_timestamp']

    def __str__(self):
        return f"طلب {self.get_service_type_display()} من {self.user.username}"


# ---

# 3. نموذج ملف المستخدم الإضافي (UserProfile)
# لتخزين بيانات إضافية غير موجودة في نموذج المستخدم الافتراضي (مثل مستوى الاشتراك).
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subscription_level = models.CharField(max_length=50, default='Basic', verbose_name="مستوى الاشتراك")
    tokens_remaining = models.IntegerField(default=1000, verbose_name="التوكنز المتبقية")

    class Meta:
        verbose_name = "ملف المستخدم"
        verbose_name_plural = "ملفات المستخدمين"

    def __str__(self):
        return f"ملف المستخدم لـ {self.user.username}"

    # 4. نموذج بند قاعدة المعرفة القانونية (KnowledgeBaseClause Model)
    # هذا هو البنك الذي يضم البنود الآمنة لعملية RAG
    class KnowledgeBaseClause(models.Model):
        # نوع البند (لتسهيل البحث بواسطة RAG)
        CLAUSE_TYPE_CHOICES = [
            ('GEN', 'عام'),  # بنود عامة (مثل القوة القاهرة)
            ('EMP', 'عمل'),  # بنود عقود العمل
            ('REN', 'إيجار'),  # بنود عقود الإيجار
            ('NDA', 'سرية'),  # بنود اتفاقيات عدم الإفصاح
        ]

        title = models.CharField(max_length=100, verbose_name="عنوان البند")
        clause_type = models.CharField(max_length=3, choices=CLAUSE_TYPE_CHOICES, verbose_name="نوع العقد")
        text_content = models.TextField(verbose_name="نص البند القانوني الآمن")
        is_verified = models.BooleanField(default=False, verbose_name="تم التحقق منه قانونياً")

        class Meta:
            verbose_name = "بند قاعدة المعرفة"
            verbose_name_plural = "بنود قاعدة المعرفة"

        def __str__(self):
            return f"{self.title} ({self.get_clause_type_display()})"

