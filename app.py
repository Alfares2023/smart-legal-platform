import streamlit as st
import json
from datetime import datetime
import time
from typing import Optional

# --- Firebase Imports (يجب استخدام هذه المكتبات للاتصال بـ Firestore) ---
# ملاحظة: يجب أن تكون هذه المكتبات متاحة في بيئة Streamlit
try:
    from firebase_admin import initialize_app, credentials, firestore
    from firebase_admin import auth as firebase_auth
    from google.cloud.firestore import Client as FirestoreClient

    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    st.warning("تحذير: مكتبات Firebase Admin غير متاحة. سيتم استخدام البيانات الصورية.")


# --- تهيئة Firebase (يتم تنفيذها مرة واحدة فقط) ---
@st.cache_resource
def setup_firebase() -> tuple[Optional[FirestoreClient], str]:
    """
    تهيئة Firebase Firestore والتوثيق عند بدء التطبيق.
    """
    if not FIREBASE_AVAILABLE:
        return None, "MOCK_USER_ID"

    try:
        # المتغيرات العالمية المقدمة من بيئة Canvas
        app_id = globals().get('__app_id', 'default-app-id')
        firebase_config_str = globals().get('__firebase_config', '{}')
        auth_token = globals().get('__initial_auth_token', None)

        if not firebase_config_str or firebase_config_str == '{}':
            st.error("خطأ: لم يتم توفير إعدادات Firebase. الرجاء التأكد من تهيئة البيئة.")
            return None, "NO_CONFIG_USER"

        firebase_config = json.loads(firebase_config_str)
        cred = credentials.Certificate(firebase_config)

        # تهيئة التطبيق (نتحقق أولاً من عدم تهيئته مسبقاً)
        if not firebase_auth._apps:
            initialize_app(cred)

        db = firestore.client()

        # تحديد معرّف المستخدم
        user_id = f"anon_user_{app_id}_{str(hash(time.time()))}"
        if auth_token:
            # في بيئة Canvas، قد نستخدم معرفاً مبسطاً مشتقاً من التطبيق والرمز المميز
            # هذا تبسيط للتعامل مع متطلبات الأمان في بيئات العرض
            user_id = f"AuthenticatedUser_{app_id}"

        return db, user_id

    except Exception as e:
        st.error(f"خطأ فادح في تهيئة Firebase: {e}")
        return None, "FIREBASE_ERROR"


# --- دوال المنطق الخلفي (محاكاة لاستدعاء LLM/Backend) ---

def analyze_contract(file_name: str, text: str) -> str:
    """دالة محاكاة لتحليل محتوى العقد باستخدام نموذج ذكي."""
    time.sleep(1)  # محاكاة لوقت استجابة API
    risk_score = sum(ord(c) for c in text[:50]) % 100  # توليد درجة مخاطر عشوائية

    analysis_parts = []

    if risk_score > 70:
        analysis_parts.append("🛑 **درجة مخاطر عالية:** يوجد غموض شديد في بنود إنهاء العقد وتحديد المسؤوليات المالية.")
    elif risk_score > 40:
        analysis_parts.append(
            "⚠️ **درجة مخاطر متوسطة:** العقد سليم هيكلياً لكنه يفتقر إلى تحديد آلية واضحة لفض النزاعات الفنية.")
    else:
        analysis_parts.append("✅ **درجة مخاطر منخفضة:** صياغة العقد محكمة وتغطي الجوانب القانونية الأساسية بنجاح.")

    analysis_parts.append(f"\n- **الملف الذي تم تحليله:** {file_name}")
    analysis_parts.append(f"- **إجمالي الكلمات:** {len(text.split())}")
    analysis_parts.append(f"- **توصية المستشار:** يوصى بإضافة ملحق يوضح مؤشرات الأداء الرئيسية (KPIs) لضمان الامتثال.")

    return "\n\n".join(analysis_parts)


def generate_contract(topic: str, category: str) -> str:
    """دالة محاكاة لتوليد نموذج عقد بناءً على المدخلات."""
    time.sleep(1)  # محاكاة لوقت استجابة API
    if topic and category:
        return f"""
# نموذج اتفاقية {topic}
## تصنيف: {category}
---
**التاريخ:** {datetime.now().strftime('%Y-%m-%d')}

**البند 1 (الأطراف):**
هذا العقد ساري المفعول بين الطرف الأول (المشار إليه بـ "المقدم") والطرف الثاني (المشار إليه بـ "المستفيد").

**البند 2 (الهدف):**
يتفق الطرفان على أن الغرض من هذه الوثيقة هو تنظيم خدمات {topic} بما يتماشى مع المبادئ القانونية للمنطقة.

**البند 3 (المدة والإنهاء):**
مدة العقد سنة واحدة قابلة للتجديد بموافقة خطية من الطرفين، مع شرط جزائي قدره (5%) من القيمة الإجمالية في حال الإنهاء المبكر غير المبرر.

**البند 4 (القانون الواجب التطبيق):**
تخضع هذه الاتفاقية وتُفسّر وفقاً لقوانين [اسم الدولة العربية المعتمد].

**توقيع الطرفين:**
(المقدم) .................... (المستفيد)
"""
    return "الرجاء تحديد الموضوع والتصنيف لتوليد النموذج."


# --- دالة المستمع للتحميل في الوقت الفعلي ---
@st.cache_resource(ttl=300)
def setup_listener(db_client: FirestoreClient, path: str):
    """
    إعداد مستمع Firestore في الوقت الفعلي لتحديث حالة Streamlit.
    """
    if not FIREBASE_AVAILABLE or db_client is None:
        # إرجاع دالة صورية في حالة عدم توفر Firebase
        st.session_state.records = [
            {"id": "MOCK-1", "topic": "طلب استشارة إيجار", "community": "عقود الإيجار", "details": "تفاصيل صورية...",
             "status": "جديد", "created_at": "2023-10-01"},
            {"id": "MOCK-2", "topic": "تعديل عقد عمل", "community": "عقود العمل", "details": "تفاصيل صورية...",
             "status": "قيد المراجعة", "created_at": "2023-10-05"},
        ]
        return

    def on_snapshot(col_snapshot, changes, read_time):
        # يتم تشغيل هذه الدالة في سياق مختلف عن Streamlit
        records_list = []
        for doc in col_snapshot.docs:
            data = doc.to_dict()
            data['id'] = doc.id
            records_list.append(data)

        # تحديث حالة الجلسة وإعادة تشغيل التطبيق لعرض التحديثات
        st.session_state.records = records_list
        try:
            st.rerun()
        except Exception as e:
            # استخدام st.experimental_rerun() كخيار احتياطي إذا كان متاحاً
            st.experimental_rerun()

    try:
        col_ref = db_client.collection(path)
        col_ref.on_snapshot(on_snapshot)
        st.success("✅ المستمع في الوقت الفعلي مفعل.")
    except Exception as e:
        st.error(f"خطأ في تفعيل المستمع: {e}")


# --- واجهة المستخدم الرئيسية ---
st.set_page_config(layout="wide", page_title="المستشار الـمُحكِم - منصة قانونية ذكية")

# تهيئة Firebase
db, user_id = setup_firebase()

# تحديد مسار قاعدة البيانات الخاص بالمستخدم (Private Path)
app_id = globals().get('__app_id', 'default-app-id')
COLLECTION_PATH = f'artifacts/{app_id}/users/{user_id}/manual_records'

# تهيئة حالة الجلسة للسجلات
if 'records' not in st.session_state:
    st.session_state.records = []

# تشغيل المستمع بمجرد تهيئة قاعدة البيانات بنجاح
setup_listener(db, COLLECTION_PATH)

# --- شريط الجانب (Sidebar) ---
with st.sidebar:
    st.image("https://placehold.co/100x100/005691/ffffff?text=Legal+AI", width=50)
    st.title("الـمُحكِم الذكي")
    st.markdown("---")

    if db:
        st.markdown(f"**حالة الاتصال:** ✅ متصل بـ Firestore")
        st.markdown(f"**معرّف المستخدم:** `{user_id}`")
        st.caption(f"مسار التخزين: `{COLLECTION_PATH}`")
    else:
        st.markdown(f"**حالة الاتصال:** ❌ غير متصل (Mock Data)")
    st.markdown("---")
    st.info("هذا التطبيق يستخدم نماذج اللغة الكبيرة (LLMs) لمحاكاة المستشار القانوني الخبير.")

# --- علامات التبويب ---
tab1, tab2, tab3 = st.tabs(["📝 تسجيل طلب يدوي", "🔍 تحليل عقد موجود", "🖋️ توليد نموذج عقد"])

# ------------------------------------
# TAB 1: تسجيل طلب يدوي جديد وعرض السجلات
# ------------------------------------
with tab1:
    st.header("تسجيل طلب يدوي جديد")
    st.markdown("الرجاء إدخال تفاصيل الطلب لحفظه في سجل المتابعة الشخصي.")

    with st.form("manual_request_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            request_topic = st.text_input("موضوع الطلب:", key="topic_input")
        with col_b:
            community_class = st.selectbox("صنف المجتمع:",
                                           ["عقود الإيجار", "عقود العمل", "عقود الشراكة", "قضايا الملكية الفكرية"],
                                           key="community_input")

        request_details = st.text_area("تفاصيل الطلب والمستندات (وصف المشكلة القانونية):", key="details_input",
                                       height=150)
        expected_outcome = st.text_area("النتيجة المطلوبة والتوقعات:", key="outcome_input", height=100)

        submitted = st.form_submit_button("✅ تسجيل الطلب وحفظه")

        if submitted:
            if db and request_topic and request_details:
                try:
                    # 1. إنشاء وثيقة الطلب
                    record_data = {
                        "topic": request_topic,
                        "community": community_class,
                        "details": request_details,
                        "outcome": expected_outcome,
                        "status": "جديد",
                        "created_at": datetime.now().isoformat()
                    }

                    # 2. حفظ البيانات في Firestore
                    db.collection(COLLECTION_PATH).add(record_data)

                    st.success(f"تم تسجيل الطلب بنجاح. الموضوع: **{request_topic}**")

                except Exception as e:
                    st.error(f"خطأ في حفظ البيانات (قد يكون السبب في الاتصال): {e}")
            else:
                st.warning("الرجاء ملء حقل الموضوع والتفاصيل على الأقل، والتأكد من اتصال Firebase.")

    # ------------------------------------
    # عرض السجلات المصنوعة يدوياً (عرض البيانات من Firestore)
    # ------------------------------------
    st.markdown("---")
    st.header("📁 سجلات المتابعة الشخصية")
    st.info("هذا الجدول يعرض طلباتك المسجلة (بيانات في الوقت الفعلي من Firestore).")

    if st.session_state.records:
        data_for_display = []
        for rec in st.session_state.records:
            # تنسيق البيانات للعرض في الجدول
            data_for_display.append({
                "الموضوع": rec.get("topic", "N/A"),
                "الصنف": rec.get("community", "N/A"),
                "التفاصيل المختصرة": rec.get("details", "N/A")[:70] + "...",
                "الحالة": rec.get("status", "غير محدد"),
                "تاريخ التسجيل": rec.get("created_at", "N/A")[:10]
            })

        st.dataframe(data_for_display, use_container_width=True, hide_index=True)
    else:
        st.markdown("_لا توجد سجلات يدوية مسجلة في قاعدة البيانات لهذا المستخدم حتى الآن._")

# ------------------------------------
# TAB 2: تحليل عقد موجود
# ------------------------------------
with tab2:
    st.header("تحليل عقد موجود")
    st.markdown("قم برفع ملف العقد (Text/Doc) أو ألصق النص لتحليل المخاطر القانونية فورياً.")

    # استخدام st.file_uploader لتحميل الملف
    uploaded_file = st.file_uploader("اختر ملف العقد:", type=['txt', 'md', 'doc', 'docx'])

    contract_text = st.text_area("أو ألصق نص العقد كاملاً هنا (للتجربة السريعة):", height=300, key="analysis_text")

    analysis_source = None
    if uploaded_file is not None:
        try:
            # قراءة محتوى الملف المرفوع
            file_name = uploaded_file.name
            file_contents = uploaded_file.read().decode("utf-8")
            if not contract_text:  # استخدام الملف إذا لم يكن هناك نص ملصق
                contract_text = file_contents
                analysis_source = file_name
        except Exception as e:
            st.error(f"خطأ في قراءة الملف: {e}")

    if not analysis_source and contract_text:
        analysis_source = "النص الملصق"

    st.markdown("---")

    if st.button("🚀 تحليل العقد (توليد تقرير المخاطر)"):
        if contract_text:
            with st.spinner("جاري إرسال النص إلى نموذج LLM لتحليل المخاطر..."):
                analysis_result = analyze_contract(analysis_source or "النص الملصق", contract_text)
                st.success("✅ تم التحليل بنجاح. راجع التقرير أدناه.")

                st.text_area("تقرير المستشار القانوني (درجة المخاطر والتوصيات):", analysis_result, height=250)
        else:
            st.warning("الرجاء إرفاق ملف أو إدخال نص العقد للتحليل.")

# ------------------------------------
# TAB 3: توليد نموذج عقد
# ------------------------------------
with tab3:
    st.header("توليد نموذج عقد")
    st.markdown("سيقوم النظام بتوليد نموذج عقد محكم بناءً على مدخلاتك، يحاكي خبرة المستشار.")

    gen_topic = st.text_input("موضوع العقد المطلوب توليده (مثل: اتفاقية خدمات صيانة برمجيات):", key="gen_topic")
    gen_category = st.selectbox("تصنيف العقد:", ["عقود بيع وشراء", "عقود خدمات واستشارات", "اتفاقيات سرية", "عقود عمل"],
                                key="gen_category")

    if st.button("🖋️ توليد النموذج الآن"):
        if gen_topic and gen_category:
            with st.spinner("جاري صياغة النموذج القانوني..."):
                generated_contract = generate_contract(gen_topic, gen_category)
                st.success("✅ تم توليد نموذج العقد بنجاح!")
                st.text_area("نموذج العقد المُولّد:", generated_contract, height=400)
        else:
            st.warning("الرجاء ملء حقل الموضوع والتصنيف لتوليد النموذج.")