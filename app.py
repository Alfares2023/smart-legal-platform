import streamlit as st
import requests
import json
import time
from datetime import datetime

# --- إعدادات التطبيق ---
# عند النشر، يجب التأكد من أن هذا الرابط هو الرابط الفعلي لخادم FastAPI الخاص بك
# حاليًا، سنستخدم رابط وهمي (Mock) وسنعتبر أن الخادم يعمل.
# ملاحظة: إذا كنت تنشر هذا على Streamlit Cloud، فلن يتمكن من الوصول إلى localhost.
# يجب استبدال الرابط برابط الخادم الخلفي المنشور (مثل Render, Heroku, إلخ).
API_URL = "http://localhost:8000"

# --- تهيئة الواجهة ---
st.set_page_config(
    page_title="منصة المستشار القانوني الذكي",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("⚖️ منصة تحليل وتوليد العقود")
st.markdown("---")


# --- دالة إرسال الطلب اليدوي ---
def submit_request(subject: str, parties: str, description: str, outcome: str):
    """إرسال البيانات إلى خادم FastAPI Backend عبر POST"""
    endpoint = f"{API_URL}/requests/manual/"
    data = {
        "subject": subject,
        "parties": parties,
        "description": description,
        "outcome": outcome
    }

    try:
        response = requests.post(endpoint, json=data)
        response.raise_for_status()  # إثارة استثناء للأكواد 4xx/5xx
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"فشل الاتصال بالخادم الخلفي. تأكد من تشغيل FastAPI على {API_URL}.")
        # في حالة عدم الاتصال، نعيد استجابة وهمية (Mock) لتجنب توقف التطبيق
        return {
            "message": "فشل الاتصال، تم إنشاء طلب وهمي (Mock) بدلاً منه.",
            "id": f"MOCK-{int(time.time())}"
        }
    except requests.exceptions.RequestException as e:
        st.error(f"خطأ في إرسال الطلب: {e}")
        return None


# --- دالة جلب الطلبات المسجلة ---
def fetch_requests():
    """جلب الطلبات من خادم FastAPI Backend عبر GET"""
    try:
        response = requests.get(f"{API_URL}/requests/manual/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.warning(f"فشل الاتصال بالخادم الخلفي، جاري عرض بيانات تجريبية (Mock Data).")
        # بيانات تجريبية (Mock Data) للتحقق من تصميم الواجهة
        return [
            {
                "id": "MOCK-001",
                "subject": "بيانات تجريبية: تحليل عقود",
                "parties": "العميل والشركة",
                "description": "هذه بيانات وهمية تظهر لعدم وجود اتصال بخادم FastAPI.",
                "outcome": "تقرير مخاطر",
                "status": "New",
                "created_at": datetime.now().isoformat()
            }
        ]
    except requests.exceptions.RequestException as e:
        st.error(f"خطأ في جلب البيانات: {e}")
        return []


# --- 1. بناء واجهة الإدخال ---
with st.container():
    st.header("تسجيل طلب استشارة يدوي جديد")
    st.info("الرجاء ملء النموذج أدناه لتسجيل طلبك القانوني يدوياً ليتم مراجعته لاحقاً.")

    with st.form("manual_request_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            subject = st.text_input("1. موضوع الطلب:",
                                    placeholder="تحليل بند عدم المنافسة في عقد عمل",
                                    key="input_subject")
        with col2:
            parties = st.text_input("2. الأطراف المعنية:",
                                    placeholder="الشركة أ والعميل ب",
                                    key="input_parties")

        description = st.text_area("3. تفاصيل الطلب والمستندات (إن وجدت):",
                                   height=150,
                                   placeholder="أرجو مراجعة البند الخامس من العقد وتقييم مدى قانونيته حسب القانون السعودي، مع الإشارة إلى أي ثغرات محتملة.",
                                   key="input_description")

        outcome = st.text_input("4. النتيجة المطلوبة والتوقعات:",
                                placeholder="تقرير مُفصل بالمخاطر وتوصية قانونية بالإجراء الأنسب.",
                                key="input_outcome")

        submitted = st.form_submit_button("✅ تسجيل الطلب الآن")

    if submitted:
        if subject and parties and description and outcome:
            with st.spinner("جاري إرسال الطلب إلى الخادم الخلفي (FastAPI)..."):
                result = submit_request(subject, parties, description, outcome)
                if result and "id" in result:
                    st.success(f"تم تسجيل طلبك بنجاح! رقم المرجع: **{result['id']}**")
                    if "MOCK" in result['id']:
                        st.warning("⚠️ **ملاحظة:** تم إنشاء هذا الطلب في وضع وهمي (Mock) لأن الخادم الخلفي غير متصل.")
                elif result:
                    st.info(f"تمت الاستجابة: {result.get('message', 'لا يوجد رسالة')}")
        else:
            st.error("الرجاء ملء جميع الحقول المطلوبة لتسجيل الطلب.")

# --- 2. عرض الطلبات المسجلة ---
st.markdown("---")
st.header("📁 سجل الطلبات اليدوية")
st.caption("يعرض هذا الجدول الطلبات التي تم تسجيلها في قاعدة البيانات عبر الخادم الخلفي.")

# الزر والتخزين المؤقت للبيانات
if st.button("🔄 تحديث قائمة الطلبات", key="refresh_button"):
    st.session_state['requests_data'] = fetch_requests()

# جلب البيانات عند بدء التشغيل أو بعد التحديث
if 'requests_data' not in st.session_state:
    st.session_state['requests_data'] = fetch_requests()

data = st.session_state['requests_data']

if data:
    # تهيئة البيانات للعرض في جدول Streamlit
    df_data = [{
        "ID": entry.get("id", "-"),
        "الموضوع": entry.get("subject", "-"),
        "الأطراف": entry.get("parties", "-"),
        "الحالة": entry.get("status", "-"),
        "تاريخ التسجيل": entry.get("created_at", "-")[:10],  # عرض التاريخ فقط
        "الوصف الكامل": entry.get("description", "-"),
        "النتيجة المتوقعة": entry.get("outcome", "-"),
    } for entry in data]

    st.dataframe(
        df_data,
        use_container_width=True,
        # تحديد عرض الأعمدة الرئيسية ليتناسب مع المحتوى
        column_config={
            "ID": st.column_config.TextColumn("رقم المرجع", width="small"),
            "الموضوع": st.column_config.TextColumn("موضوع الطلب", width="medium"),
            "الحالة": st.column_config.TextColumn("الحالة", width="small"),
            "الوصف الكامل": st.column_config.TextColumn("الوصف الكامل", width="large"),
        }
    )
else:
    st.info("لا توجد طلبات مسجلة لعرضها حالياً.")