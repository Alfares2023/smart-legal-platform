import openai
from django.db.models import Q
from .models import KnowledgeBaseClause
from smart_legal_platform.settings import config
import logging

logger = logging.getLogger(__name__)

# إعداد العميل والمفتاح (مماثل لملف views.py السابق)
OPENAI_API_KEY = config('OPENAI_API_KEY', default=None)
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# الأمر الرئيسي لعملية التوليد باستخدام البنود المسترجعة
GENERATION_PROMPT_TEMPLATE_AR = (
    "أنت نظام توليد عقود قانونية خبير وموثوق. "
    "مهمتك هي إنشاء عقد قانوني كامل وآمن بناءً على تفاصيل طلب المستخدم والبنود الآمنة المقدمة لك.\n"
    "1. يجب أن تستخدم البنود الآمنة المرفقة كـ 'مكونات أساسية' للعقد.\n"
    "2. يجب ملء الفراغات في البنود بالبيانات التي يقدمها المستخدم.\n"
    "3. يجب تنسيق الرد على شكل نص عادي (Plain Text) للعقد النهائي.\n\n"
    "**تفاصيل طلب المستخدم:** {user_request_details}\n\n"
    "**البنود الآمنة المسترجعة (RAG Clauses):**\n---\n{retrieved_clauses}\n---"
)


def retrieve_safe_clauses(contract_type: str, keywords: str):
    """
    وظيفة RAG: تبحث في قاعدة المعرفة عن البنود الآمنة.
    في تطبيق متقدم، سيتم استخدام Vector Database. هنا، نستخدم بحث Django مبسط.
    """
    # 1. البحث حسب نوع العقد
    clauses_by_type = KnowledgeBaseClause.objects.filter(clause_type=contract_type, is_verified=True)

    # 2. البحث الإضافي بالكلمات المفتاحية (لتحديد البنود الدقيقة)
    if keywords:
        search_query = Q(title__icontains=keywords) | Q(text_content__icontains=keywords)
        clauses = clauses_by_type.filter(search_query).distinct()
    else:
        clauses = clauses_by_type

    # تحويل البنود المسترجعة إلى نص واحد لتقديمه للنموذج (LLM)
    retrieved_text = "\n\n".join([f"## {c.title}\n{c.text_content}" for c in clauses])

    return retrieved_text, clauses.count()


def generate_contract_with_rag(contract_type: str, user_details: dict):
    """
    الوظيفة الرئيسية لتوليد العقد بالاعتماد على RAG.
    """
    if not OPENAI_API_KEY:
        return {"error": "AI service key is missing."}, 0

    # 1. استرجاع البنود الآمنة (RAG)
    keywords = user_details.get('keywords', '')
    safe_clauses_text, clause_count = retrieve_safe_clauses(contract_type, keywords)

    if clause_count == 0:
        return {"error": "لم يتم العثور على بنود آمنة لإنشاء هذا النوع من العقود."}, 0

    # 2. إعداد الأمر للنموذج
    full_prompt = GENERATION_PROMPT_TEMPLATE_AR.format(
        user_request_details=json.dumps(user_details, ensure_ascii=False, indent=2),  # تفاصيل المستخدم
        retrieved_clauses=safe_clauses_text  # البنود المسترجعة
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",  # استخدام نموذج عالي الجودة لضمان سلامة التوليد
            messages=[
                {"role": "system", "content": "أنت نظام توليد عقود قانونية، مهمتك هي توليد عقد نهائي وآمن."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=4000,  # زيادة التوكنز لإنشاء عقد كامل
            temperature=0.4  # درجة حرارة منخفضة لتقليل الخيال وزيادة الالتزام بالبنود
        )

        tokens_used = response['usage']['total_tokens']
        generated_contract_text = response['choices'][0]['message']['content']

        return {"contract_text": generated_contract_text}, tokens_used

    except Exception as e:
        logger.error(f"AI Contract Generation Failed: {e}")
        return {"error": f"فشل في الاتصال بخدمة الذكاء الاصطناعي أثناء التوليد: {str(e)}"}, 0