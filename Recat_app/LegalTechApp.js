import React, { useState, useEffect, useCallback } from 'react';

// عنوان الـ API الذي تم إعداده في app/main.py (يتم الافتراض أنه يعمل على نفس المضيف والمنفذ)
const API_BASE_URL = window.location.origin.includes('localhost')
    ? 'http://localhost:8000'
    : '/api'; // مسار افتراضي في بيئة الإنتاج

// ----------------------------------------------------------------------------------
// 1. المكونات الهيكلية الرئيسية
// ----------------------------------------------------------------------------------

// قائمة التنقل الجانبية
const Sidebar = ({ currentView, setView }) => {
    const navItems = [
        { id: 'dashboard', label: 'الرئيسية', icon: 'M10 20v-6h4v6h5v-8h3L12 3L2 12h3v8h5z' },
        { id: 'clients', label: 'العملاء', icon: 'M16 7a4 4 0 11-8 0a4 4 0 018 0zm-4 7a7 7 0 00-7 7h14a7 7 0 00-7-7z' },
        { id: 'contracts', label: 'العقود والتحليل', icon: 'M15 13H5v-2h10m4 0H15v-2h4m2 0H19V7m0-2h2V3h-2M5 17h10v-2H5m-2 2H3V15h2v2z' },
        { id: 'cases', label: 'القضايا', icon: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10s10-4.48 10-10S17.52 2 12 2zm-1 15h2v-2h-2v2zm0-4h2V7h-2v6z' }
    ];

    return (
        <div className="w-64 bg-gray-900 text-white min-h-screen p-4 flex flex-col shadow-lg">
            <h1 className="text-2xl font-bold text-teal-400 mb-8 border-b border-gray-700 pb-3">Legal AI Hub</h1>
            <nav className="space-y-2">
                {navItems.map(item => (
                    <button
                        key={item.id}
                        onClick={() => setView(item.id)}
                        className={`w-full text-right flex items-center p-3 rounded-xl transition duration-200 ${
                            currentView === item.id 
                                ? 'bg-teal-600 text-white shadow-md' 
                                : 'text-gray-300 hover:bg-gray-700 hover:text-teal-400'
                        }`}
                    >
                        <svg className="w-6 h-6 ml-3" fill="currentColor" viewBox="0 0 24 24"><path d={item.icon} /></svg>
                        <span className="font-medium">{item.label}</span>
                    </button>
                ))}
            </nav>
        </div>
    );
};

// رأس الصفحة مع تفاصيل المستخدم الوهمي
const Header = ({ userId }) => (
    <header className="bg-white p-4 border-b border-gray-200 flex justify-between items-center shadow-md">
        <div className="text-gray-800 text-xl font-semibold">لوحة التحكم</div>
        <div className="flex items-center space-x-3 rtl:space-x-reverse">
            <span className="text-sm text-gray-600">المستخدم:</span>
            <span className="bg-teal-100 text-teal-800 text-sm font-medium px-3 py-1 rounded-full">{userId}</span>
        </div>
    </header>
);

// ----------------------------------------------------------------------------------
// 2. مكون إدارة العملاء (Clients View)
// ----------------------------------------------------------------------------------

const ClientsView = ({ userId }) => {
    const [clients, setClients] = useState([]);
    const [newClient, setNewClient] = useState({ full_name: '', email: '', phone: '' });
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    // جلب العملاء
    const fetchClients = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE_URL}/clients/`, {
                headers: { 'X-User-ID': userId } // إرسال معرف المستخدم
            });
            if (!response.ok) throw new Error("فشل جلب قائمة العملاء");
            const data = await response.json();
            setClients(data);
        } catch (err) {
            console.error("Fetch Clients Error:", err);
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    }, [userId]);

    useEffect(() => {
        fetchClients();
    }, [fetchClients]);

    // إنشاء عميل جديد
    const handleCreateClient = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE_URL}/clients/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-ID': userId
                },
                body: JSON.stringify(newClient)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "فشل إنشاء العميل");
            }

            const createdClient = await response.json();
            setClients([...clients, createdClient]);
            setNewClient({ full_name: '', email: '', phone: '' }); // تفريغ النموذج
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    const handleChange = (e) => {
        setNewClient({ ...newClient, [e.target.name]: e.target.value });
    };

    return (
        <div className="p-6 bg-white rounded-xl shadow-lg space-y-8">
            <h2 className="text-3xl font-bold text-teal-700 border-b pb-4">إدارة العملاء</h2>

            {/* نموذج إضافة عميل جديد */}
            <form onSubmit={handleCreateClient} className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 border border-teal-200 rounded-xl bg-teal-50">
                <input
                    type="text"
                    name="full_name"
                    value={newClient.full_name}
                    onChange={handleChange}
                    placeholder="الاسم الكامل"
                    required
                    className="p-3 border border-gray-300 rounded-lg focus:ring-teal-500 focus:border-teal-500 transition"
                />
                <input
                    type="email"
                    name="email"
                    value={newClient.email}
                    onChange={handleChange}
                    placeholder="البريد الإلكتروني"
                    required
                    className="p-3 border border-gray-300 rounded-lg focus:ring-teal-500 focus:border-teal-500 transition"
                />
                <input
                    type="tel"
                    name="phone"
                    value={newClient.phone}
                    onChange={handleChange}
                    placeholder="رقم الهاتف"
                    required
                    className="p-3 border border-gray-300 rounded-lg focus:ring-teal-500 focus:border-teal-500 transition"
                />
                <button
                    type="submit"
                    disabled={isLoading}
                    className="col-span-1 md:col-span-3 bg-teal-600 hover:bg-teal-700 text-white font-bold py-3 rounded-lg transition duration-200 disabled:opacity-50"
                >
                    {isLoading ? 'جاري الحفظ...' : 'إضافة عميل جديد'}
                </button>
            </form>

            {/* عرض الأخطاء */}
            {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">{error}</div>}

            {/* قائمة العملاء */}
            <h3 className="text-2xl font-semibold mt-8">قائمة العملاء ({clients.length})</h3>
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">الاسم</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">البريد</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">الهاتف</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">تاريخ الإضافة</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {clients.map((client) => (
                            <tr key={client.id} className="hover:bg-gray-50 transition duration-150">
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{client.full_name}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{client.email}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{client.phone}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {new Date(client.created_at).toLocaleDateString('ar-SA')}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {clients.length === 0 && !isLoading && !error && (
                    <div className="text-center py-8 text-gray-500">لا يوجد عملاء بعد. أضف عميلاً جديداً للبدء.</div>
                )}
            </div>
        </div>
    );
};

// ----------------------------------------------------------------------------------
// 3. المكون الرئيسي للتطبيق
// ----------------------------------------------------------------------------------

export default function App() {
    // محاكاة لمعرّف المستخدم الذي نحصل عليه من المصادقة (لإرساله في الـ Header)
    const [userId] = useState("lawyer-A-42");
    const [currentView, setCurrentView] = useState('clients');

    let ContentComponent;
    switch (currentView) {
        case 'clients':
            ContentComponent = <ClientsView userId={userId} />;
            break;
        case 'contracts':
            ContentComponent = <div className="p-6">قريباً: واجهة توليد وتحليل العقود</div>;
            break;
        case 'cases':
            ContentComponent = <div className="p-6">قريباً: واجهة إدارة القضايا</div>;
            break;
        case 'dashboard':
        default:
            ContentComponent = <div className="p-6">مرحباً بك في لوحة تحكم Legal AI.</div>;
    }

    // هنا يتم حل مشكلة الـ "Target container is not a DOM element"
    // عن طريق دمج البنية الهيكلية الكاملة للتطبيق في ملف واحد
    return (
        <html>
            <head>
                <meta charSet="UTF-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <title>Legal Tech AI Dashboard</title>
                {/* تحميل خط Inter */}
                <link href="https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap" rel="stylesheet" />
                {/* تحميل Tailwind CSS */}
                <script src="https://cdn.tailwindcss.com"></script>
                <style>
                    {`
                        body {
                            font-family: 'Inter', sans-serif;
                            direction: rtl; /* دعم اللغة العربية */
                            text-align: right;
                        }
                    `}
                </style>
            </head>
            <body className="bg-gray-100">
                {/* هذه هي الحاوية المطلوبة (Target container) */}
                <div id="root" className="min-h-screen flex">
                    <Sidebar currentView={currentView} setView={setCurrentView} />
                    <div className="flex-1 flex flex-col">
                        <Header userId={userId} />
                        <main className="flex-1 p-6 overflow-y-auto">
                            {ContentComponent}
                        </main>
                    </div>
                </div>
            </body>
        </html>
    );
}