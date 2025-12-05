import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# يجب إضافة استيراد models من Django لتعريف النموذج
from django.db import transaction, models
from django.shortcuts import get_object_or_404

from .models import Contract, ServiceRequest, UserProfile
from .serializers import ContractSerializer
from smart_legal_platform.settings import config

# لاستدعاء خدمات الذكاء الاصطناعي الخارجية
import openai
import json
import logging


# ==========================================================
# ملاحظة: هذا النموذج يجب أن يكون في ملف 'contracts_api/models.py'
# تم وضعه هنا مؤقتاً لغرض الإصلاح والتجميع.
# ==========================================================
class KnowledgeBaseClause(models.Model):
    CLAUSE_TYPE_CHOICES = [
        ('GEN', 'عام'),
        ('EMP', 'عمل'),
        ('REN', 'إيجار'),
        ('NDA', 'سرية'),
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


# ==========================================================


# إعداد السجل (Logging) للتطبيقات الاحترافية
logger = logging.getLogger(__name__)

# --- إعداد خدمة الذكاء الاصطناعي ---

# تحميل مفتاح API بشكل آمن من ملف .env
OPENAI_API_KEY = config('OPENAI_API_KEY', default=None)

if OPENAI_API_KEY:
    try:
        openai.api_key = OPENAI_API_KEY
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")

# الأمر (Prompt) القانوني باللغة العربية
ANALYSIS_PROMPT_TEMPLATE_AR = (
    "أنت مستشار قانوني خبير ومختص في تحليل العقود باللغة العربية. "
    "مهمتك هي تحليل النص القانوني التالي وكشف جميع الثغرات والمخاطر القانونية التى "
    "قد تضر بالطرف الأول. يجب أن يكون ردك بتنسيق JSON حصراً ويحتوي على المفاتيح التالية:\n"
    "1. 'summary': (ملخص للمخاطر الرئيسية والتقييم العام).\n"
    "2. 'risks': (مصفوفة من المخاطر, كل عنصر يحتوي على 'clause_text', 'risk_description', 'suggested_amendment').\n"
    "3. 'rating': (تقييم للخطر من 1 إلى 5 حيث 5 هو الأعلى).\n\n"
    "نص العقد للتحليل:\n---\n{contract_text}\n---"
)


def call_ai_analysis_service(contract_text: str):
    """
    وظيفة احترافية للاتصال بنموذج لغوي كبير والحصول على استجابة JSON.
    """
    if not OPENAI_API_KEY:
        return {"error": "AI service key is missing."}, 0

    try:
        full_prompt = ANALYSIS_PROMPT_TEMPLATE_AR.format(contract_text=contract_text)

        # استخدام وظيفة الإكمال (Completion) أو الدردشة (Chat) مع طلب تنسيق JSON
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "أنت مستشار قانوني خبير. يجب أن يكون الرد بتنسيق JSON حصراً."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=3000,
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        tokens_used = response['usage']['total_tokens']
        # تفريغ استجابة JSON
        analysis_result_json = json.loads(response['choices'][0]['message']['content'])

        # يجب أن يكون الإرجاع داخل كتلة try بعد الحصول على النتيجة
        return analysis_result_json, tokens_used

    except Exception as e:
        # هذه الكتلة تعالج أي خطأ في الاتصال أو التحليل أو الـ JSON
        logger.error(f"AI Service Call Failed: {e}")
        return {"error": f"فشل في الاتصال بخدمة الذكاء الاصطناعي أو تحليل الاستجابة: {str(e)}"}, 0


# --- ViewSet الرئيسي (الواجهة الخلفية) ---

class ContractAnalysisViewSet(viewsets.ModelViewSet):
    # 1. الأمان: يجب أن يكون المستخدم مسجلاً للدخول
    permission_classes = [IsAuthenticated]

    # 2. النماذج والمُسلسِلات
    serializer_class = ContractSerializer

    # 3. تصفية البيانات: المستخدم يرى عقوده فقط
    def get_queryset(self):
        return Contract.objects.filter(user=self.request.user)

    # 4. معالجة الإنشاء: ربط العقد بالمستخدم الحالي تلقائياً
    def perform_create(self, serializer):
        # هنا يتم حفظ العقد قبل التحليل (إذا كان تم رفعه)
        serializer.save(user=self.request.user, status='UPL')  # UPL: تم الرفع

    # 5. الإجراء المخصص: /api/contracts/{id}/run_analysis/
    @action(detail=True, methods=['post'], url_path='run-analysis')
    def run_analysis(self, request, pk=None):
        contract = self.get_object()

        try:
            # استخدام 'get_object_or_404' لضمان وجود ملف المستخدم
            user_profile = get_object_or_404(UserProfile, user=request.user)

            # **منطق التسعير والتوكنز:**
            ESTIMATED_COST_TOKENS = 500
            if user_profile.tokens_remaining < ESTIMATED_COST_TOKENS:
                return Response(
                    {"error": "🚫 رصيد التوكنز غير كافٍ لإجراء هذا التحليل. يرجى الاشتراك أو شراء المزيد."},
                    status=status.HTTP_402_PAYMENT_REQUIRED
                )

            # 1. استدعاء خدمة الذكاء الاصطناعي
            analysis_data, tokens_used = call_ai_analysis_service(contract.original_text)

            if 'error' in analysis_data:
                return Response(analysis_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 2. تحديث حالة العقد وحفظ النتائج (في عملية واحدة متماسكة)
            with transaction.atomic():
                contract.analysis_results = analysis_data
                contract.status = 'ANL'  # ANL: Analysis Complete
                contract.save()

                # تسجيل طلب الخدمة (لتتبع الفواتير والتوكنز)
                ServiceRequest.objects.create(
                    user=request.user,
                    related_contract=contract,
                    service_type='ANL',
                    tokens_used=tokens_used,
                    is_paid=True
                )

                # خصم التوكنز من رصيد المستخدم
                user_profile.tokens_remaining -= tokens_used
                user_profile.save()

            # 3. إرجاع العقد المحدث مع نتائج التحليل
            serializer = self.get_serializer(contract)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Analysis process failed for contract {pk}: {e}")
            return Response({"error": f"حدث خطأ غير متوقع في معالجة التحليل: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)