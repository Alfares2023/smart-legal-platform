import os
import json
import time
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from google.cloud.firestore import Client

# --- محاولة استيراد مكتبات Firebase ---
try:
    import firebase_admin
    from firebase_admin import credentials, firestore

    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("WARNING: Firebase Admin SDK not installed.")

# --- إعدادات التطبيق ---
app = FastAPI(title="Smart Legal Platform Backend", version="1.1.0")

# إعداد CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ثوابت وإعدادات قاعدة البيانات ---
APP_ID = os.environ.get('__app_id', 'default-app-id')
# تحديد مسار المجموعة (Collection) في متغير واحد لسهولة التعديل
MANUAL_REQUESTS_COLLECTION = f"artifacts/{APP_ID}/public/data/manual_requests"


# --- دالة تهيئة قاعدة البيانات ---
def init_firestore() -> Optional[Client]:
    """
    تقوم هذه الدالة بتهيئة اتصال Firestore.
    تعيد كائن Client في حالة النجاح، أو None في حالة الفشل أو عدم وجود إعدادات.
    """
    if not FIREBASE_AVAILABLE:
        return None

    try:
        firebase_config = os.environ.get('__firebase_config', '{}')

        # التحقق من وجود تهيئة سابقة لتجنب خطأ "App already exists"
        if not firebase_admin._apps:
            if firebase_config and firebase_config != '{}':
                print("INFO: Initializing Firebase with Environment Config.")
                # في بيئات مثل Project IDX، قد يتم التعرف على الاعتمادات تلقائياً
                # أو يمكن تمرير credentials.Certificate(json.loads(firebase_config)) هنا
                firebase_admin.initialize_app()
            else:
                print("NOTE: No Firebase config found. Using Mock mode.")
                return None

        return firestore.client()

    except Exception as e:
        print(f"ERROR: Failed to initialize Firestore: {e}")
        return None


# تهيئة العميل (Client) عند بدء التشغيل
DB_CLIENT: Optional[Client] = init_firestore()


# --- نماذج البيانات (Pydantic Models) ---
# ... (نماذج Generate و Analysis و Chat تبقى كما هي) ...

class ManualRequest(BaseModel):
    """نموذج استلام الطلب من المستخدم"""
    subject: str = Field(..., min_length=3, description="موضوع الطلب")
    parties: str = Field(..., description="الأطراف المعنية")
    description: str = Field(..., description="تفاصيل الطلب")
    outcome: str = Field(..., description="النتيجة المطلوبة")


class ManualRequestEntry(BaseModel):
    """نموذج عرض الطلب (بما في ذلك البيانات التي يولدها النظام)"""
    id: str
    subject: str
    parties: str
    description: str
    outcome: str
    status: str
    created_at: str


# --- العمليات على قاعدة البيانات (API Endpoints) ---

@app.post("/requests/manual/", response_model=Dict[str, str])
async def submit_manual_request(request: ManualRequest):
    """
    تسجيل طلب يدوي جديد.
    يقوم بحفظ الطلب في Firestore إذا كان متاحاً، وإلا يعيد استجابة صورية.
    """
    # تجهيز البيانات
    request_data = request.dict()
    request_data["status"] = "New"
    # استخدام UTC لضمان توحيد التوقيت
    request_data["created_at"] = datetime.now(timezone.utc)

    # 1. حالة قاعدة البيانات غير متصلة (Mock Mode)
    if DB_CLIENT is None:
        print("INFO: Mocking DB Write Operation")
        return {
            "message": "تم استلام الطلب بنجاح (وضع العرض التجريبي - لم يتم الحفظ فعلياً).",
            "id": f"MOCK-{int(time.time())}"
        }

    # 2. حالة الاتصال بقاعدة البيانات
    try:
        # الإضافة إلى Firestore والحصول على الوقت والمرجع
        update_time, doc_ref = DB_CLIENT.collection(MANUAL_REQUESTS_COLLECTION).add(request_data)

        return {
            "message": "تم تسجيل الطلب وحفظه في قاعدة البيانات بنجاح.",
            "id": doc_ref.id
        }

    except Exception as e:
        print(f"Firestore Write Error: {e}")
        raise HTTPException(status_code=500, detail="حدث خطأ أثناء حفظ البيانات في الخادم.")


@app.get("/requests/manual/", response_model=List[ManualRequestEntry])
async def get_manual_requests():
    """
    جلب قائمة الطلبات اليدوية.
    """
    # 1. حالة قاعدة البيانات غير متصلة (Mock Mode)
    if DB_CLIENT is None:
        return [
            ManualRequestEntry(
                id="MOCK-001",
                subject="بيانات تجريبية 1",
                parties="تجربة أ - تجربة ب",
                description="هذه بيانات تظهر لعدم وجود اتصال بقاعدة البيانات.",
                outcome="تجربة",
                status="New",
                created_at=datetime.now(timezone.utc).isoformat()
            )
        ]

    # 2. حالة الاتصال بقاعدة البيانات
    try:
        # جلب المستندات وترتيبها من الأحدث للأقدم
        docs = DB_CLIENT.collection(MANUAL_REQUESTS_COLLECTION) \
            .order_by("created_at", direction=firestore.Query.DESCENDING) \
            .stream()

        results = []
        for doc in docs:
            data = doc.to_dict()

            # معالجة حقل التاريخ: Firestore يعيده كـ datetime object
            created_at_val = data.get("created_at")
            if isinstance(created_at_val, datetime):
                created_at_str = created_at_val.isoformat()
            else:
                created_at_str = str(created_at_val) if created_at_val else datetime.now(timezone.utc).isoformat()

            results.append(ManualRequestEntry(
                id=doc.id,
                subject=data.get("subject", "غير محدد"),
                parties=data.get("parties", ""),
                description=data.get("description", ""),
                outcome=data.get("outcome", ""),
                status=data.get("status", "New"),
                created_at=created_at_str
            ))

        return results

    except Exception as e:
        print(f"Firestore Read Error: {e}")
        raise HTTPException(status_code=500, detail="حدث خطأ أثناء استرجاع البيانات.")

# --- باقي الكود (endpoints الخاصة بـ Gemini) ---
# ... (يمكنك إدراج دوال call_gemini_api وباقي الـ endpoints هنا) ...