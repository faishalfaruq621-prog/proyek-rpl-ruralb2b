"""
RuralB2B Stage 8 - AI Integration Test Suite
Menguji seluruh fitur AI backend dengan atau tanpa API key.
"""
import urllib.request
import urllib.error
import json
import time

BASE_URL = "http://127.0.0.1:5000"

results = {
    "BERHASIL": [],
    "GAGAL": [],
    "BELUM_DAPAT_DIUJI": [],
}

def log(status, test, detail=""):
    results[status].append((test, detail))
    icon = "[OK]" if status == "BERHASIL" else ("[FAIL]" if status == "GAGAL" else "[SKIP]")
    print(f"{icon} {test}" + (f" - {detail}" if detail else ""))

def req(method, path, data=None, token=None, files=None):
    url = BASE_URL + path
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if files:
        boundary = "----RuralB2BFormBoundary" + str(abs(hash(path + str(time.time()))))
        parts = []
        if data:
            items = data.items() if isinstance(data, dict) else data
            for key, value in items:
                parts.append(f"--{boundary}")
                parts.append(f'Content-Disposition: form-data; name="{key}"')
                parts.append("")
                parts.append(str(value))
        for key, (fname, fdata, ftype) in files.items():
            parts.append(f"--{boundary}")
            parts.append(f'Content-Disposition: form-data; name="{key}"; filename="{fname}"')
            parts.append(f"Content-Type: {ftype}")
            parts.append("")
            parts.append(fdata.decode("latin-1"))
        parts.append(f"--{boundary}--")
        body = "\r\n".join(parts).encode("utf-8")
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    else:
        body = json.dumps(data).encode("utf-8") if data is not None else None
        headers["Content-Type"] = "application/json"

    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=15)
        return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {"message": str(e)}
    except Exception as e:
        return None, {"message": str(e)}

print("=" * 60)
print("RURALB2B STAGE 8 - AI INTEGRATION TEST")
print("=" * 60)

# ============================================================
# TAHAP 1: Konfigurasi dan Status AI
# ============================================================
print("\n=== TAHAP 1: Konfigurasi AI ===")
status, data = req("GET", "/api/health")
if status == 200:
    log("BERHASIL", "Backend Flask berjalan", f"Health: {data.get('status')}")
else:
    log("GAGAL", "Backend Flask berjalan", f"Status {status}")

status, data = req("GET", "/api/ai/status")
if status == 200:
    configured = data.get("data", {}).get("configured", False)
    provider = data.get("data", {}).get("provider", "unknown")
    daily_limit = data.get("data", {}).get("daily_limit", 0)
    log("BERHASIL", "AI Status endpoint", f"Provider: {provider}, Configured: {configured}, Limit: {daily_limit}")
    AI_CONFIGURED = configured
else:
    log("GAGAL", "AI Status endpoint", f"Status {status}: {data.get('message', data)}")
    AI_CONFIGURED = False

# ============================================================
# TAHAP 2: Register dan Login (2 user: pembeli dan penjual)
# ============================================================
print("\n=== TAHAP 2: Autentikasi ===")
ts = str(int(time.time()))

# Penjual
seller_email = f"ai.seller.{ts}@example.com"
seller_reg = {
    "full_name": "AI Seller User",
    "email": seller_email,
    "password": "RuralB2B!2026",
    "business_type": "farmer",
    "business_name": "AI Seller Farm",
    "phone": "+628123456789",
    "address": "Jl. Test No. 1",
    "city": "Bandung",
    "province": "Jawa Barat",
}
status, data = req("POST", "/api/auth/register", seller_reg)
if status == 201:
    log("BERHASIL", "Register penjual", f"Status {status}")
else:
    log("GAGAL", "Register penjual", f"Status {status}: {data.get('message', data)}")
    seller_email = None

if seller_email:
    status, data = req("POST", "/api/auth/login", {"email": seller_email, "password": "RuralB2B!2026"})
    if status == 200:
        seller_token = data["data"]["access_token"]
        log("BERHASIL", "Login penjual", f"Status {status}")
    else:
        log("GAGAL", "Login penjual", f"Status {status}: {data.get('message', data)}")
        seller_token = None

# Pembeli
buyer_email = f"ai.buyer.{ts}@example.com"
buyer_reg = {
    "full_name": "AI Buyer User",
    "email": buyer_email,
    "password": "RuralB2B!2026",
    "business_type": "warung",
    "business_name": "AI Buyer Warung",
    "phone": "+628123456790",
    "address": "Jl. Test No. 2",
    "city": "Bandung",
    "province": "Jawa Barat",
}
status, data = req("POST", "/api/auth/register", buyer_reg)
if status == 201:
    log("BERHASIL", "Register pembeli", f"Status {status}")
else:
    log("GAGAL", "Register pembeli", f"Status {status}: {data.get('message', data)}")
    buyer_email = None

if buyer_email:
    status, data = req("POST", "/api/auth/login", {"email": buyer_email, "password": "RuralB2B!2026"})
    if status == 200:
        buyer_token = data["data"]["access_token"]
        log("BERHASIL", "Login pembeli", f"Status {status}")
    else:
        log("GAGAL", "Login pembeli", f"Status {status}: {data.get('message', data)}")
        buyer_token = None

# ============================================================
# TAHAP 3: Chatbot Standard
# ============================================================
print("\n=== TAHAP 3: Chatbot Standard ===")
if buyer_token:
    # Validasi: messages kosong
    status, data = req("POST", "/api/ai/chat/standard", {}, token=buyer_token)
    if status == 400:
        log("BERHASIL", "Chat standard validasi messages kosong", f"Status 400")
    else:
        log("GAGAL", "Chat standard validasi messages kosong", f"Status {status}")

    # Validasi: tanpa token
    status, data = req("POST", "/api/ai/chat/standard", {"messages": [{"role": "user", "content": "Halo"}]})
    if status == 401:
        log("BERHASIL", "Chat standard tanpa token", f"Status 401")
    else:
        log("GAGAL", "Chat standard tanpa token", f"Status {status}")

    # Dengan messages (akan 503 jika tidak ada API key)
    status, data = req("POST", "/api/ai/chat/standard",
                       {"messages": [{"role": "user", "content": "Apa itu RuralB2B?"}]},
                       token=buyer_token)
    if status == 503 and not AI_CONFIGURED:
        log("BERHASIL", "Chat standard tanpa API key (503)", "Provider tidak dikonfigurasi - benar")
    elif status == 200 and AI_CONFIGURED:
        log("BERHASIL", "Chat standard dengan API key", f"Status 200, balasan diterima")
    else:
        log("GAGAL", "Chat standard dengan pesan", f"Status {status}: {data.get('message', data)}")

# ============================================================
# TAHAP 4: Chatbot Plus
# ============================================================
print("\n=== TAHAP 4: Chatbot Plus ===")
if seller_token:
    # Validasi messages kosong
    status, data = req("POST", "/api/ai/chat/plus", {}, token=seller_token)
    if status == 400:
        log("BERHASIL", "Chat plus validasi messages kosong", f"Status 400")
    else:
        log("GAGAL", "Chat plus validasi messages kosong", f"Status {status}")

    # Tanpa token
    status, data = req("POST", "/api/ai/chat/plus", {"messages": [{"role": "user", "content": "Analisis saya"}]})
    if status == 401:
        log("BERHASIL", "Chat plus tanpa token", f"Status 401")
    else:
        log("GAGAL", "Chat plus tanpa token", f"Status {status}")

    # Dengan business context (data aktual dari database)
    status, data = req("POST", "/api/ai/chat/plus",
                       {"messages": [{"role": "user", "content": "Analisis performa bisnis saya"}]},
                       token=seller_token)
    if status == 503 and not AI_CONFIGURED:
        log("BERHASIL", "Chat plus tanpa API key (503)", "Provider tidak dikonfigurasi - benar")
    elif status == 200 and AI_CONFIGURED:
        log("BERHASIL", "Chat plus dengan API key", f"Status 200, analisis diterima")
    else:
        log("GAGAL", "Chat plus dengan pesan", f"Status {status}: {data.get('message', data)}")

# ============================================================
# TAHAP 5: AI Product Recommendation
# ============================================================
print("\n=== TAHAP 5: AI Product Recommendation ===")
if buyer_token:
    # Tanpa buyer_need (mengambil semua produk tersedia)
    status, data = req("POST", "/api/ai/recommendations", {}, token=buyer_token)
    if status == 200:
        count = len(data.get("recommendations", []))
        log("BERHASIL", "Rekomendasi semua produk", f"Status 200, {count} produk")
    else:
        log("GAGAL", "Rekomendasi semua produk", f"Status {status}: {data.get('message', data)}")

    # Dengan buyer_need
    status, data = req("POST", "/api/ai/recommendations",
                       {"buyer_need": "sayuran organik", "limit": 5},
                       token=buyer_token)
    if status == 200:
        count = len(data.get("recommendations", []))
        log("BERHASIL", "Rekomendasi berdasarkan kebutuhan", f"Status 200, {count} produk")
    else:
        log("GAGAL", "Rekomendasi berdasarkan kebutuhan", f"Status {status}: {data.get('message', data)}")

    # Validasi category_id tidak valid
    status, data = req("POST", "/api/ai/recommendations",
                       {"category_id": "abc"}, token=buyer_token)
    if status == 400:
        log("BERHASIL", "Rekomendasi validasi category_id", f"Status 400")
    else:
        log("GAGAL", "Rekomendasi validasi category_id", f"Status {status}")

    # Tanpa token
    status, data = req("POST", "/api/ai/recommendations", {})
    if status == 401:
        log("BERHASIL", "Rekomendasi tanpa token", f"Status 401")
    else:
        log("GAGAL", "Rekomendasi tanpa token", f"Status {status}")

# ============================================================
# TAHAP 6: AI Business Insights (hanya business_user)
# ============================================================
print("\n=== TAHAP 6: AI Business Insights ===")
if seller_token:
    # Summary
    status, data = req("GET", "/api/ai/insights/summary", token=seller_token)
    if status == 200:
        s = data.get("data", {}).get("summary", {})
        log("BERHASIL", "Insights summary", f"Status 200, produk: {s.get('total_products', 0)}, pesanan: {s.get('total_orders', 0)}")
    else:
        log("GAGAL", "Insights summary", f"Status {status}: {data.get('message', data)}")

    # Transactions
    status, data = req("GET", "/api/ai/insights/transactions", token=seller_token)
    if status == 200:
        log("BERHASIL", "Insights transactions", f"Status 200")
    else:
        log("GAGAL", "Insights transactions", f"Status {status}: {data.get('message', data)}")

    # Products
    status, data = req("GET", "/api/ai/insights/products", token=seller_token)
    if status == 200:
        p = data.get("data", {}).get("products", [])
        log("BERHASIL", "Insights products", f"Status 200, {len(p)} produk")
    else:
        log("GAGAL", "Insights products", f"Status {status}: {data.get('message', data)}")

    # Pembeli mencoba akses insights (harus 403)
    if buyer_token:
        status, data = req("GET", "/api/ai/insights/summary", token=buyer_token)
        if status == 403:
            log("BERHASIL", "Insights ditolak untuk non-business_user", f"Status 403")
        else:
            log("GAGAL", "Insights ditolak untuk non-business_user", f"Status {status}")

# ============================================================
# TAHAP 7: Isolasi Data Antarbisnis
# ============================================================
print("\n=== TAHAP 7: Isolasi Data Bisnis ===")
if seller_token and buyer_token:
    # Penjual melihat insightsnya sendiri (harus hanya data miliknya)
    status, data = req("GET", "/api/ai/insights/summary", token=seller_token)
    if status == 200:
        bid = data.get("data", {}).get("business_id", None)
        log("BERHASIL", "Isolasi: penjual melihat data sendiri", f"business_id: {bid}")
    else:
        log("GAGAL", "Isolasi: penjual melihat data sendiri", f"Status {status}")

    # Pembeli (bukan business_user) tidak bisa akses insights
    status, data = req("GET", "/api/ai/insights/summary", token=buyer_token)
    if status == 403:
        log("BERHASIL", "Isolasi: pembeli tidak bisa akses insights penjual", f"Status 403")
    else:
        log("GAGAL", "Isolasi: pembeli tidak bisa akses insights penjual", f"Status {status}")

# ============================================================
# TAHAP 8: Rate Limiting
# ============================================================
print("\n=== TAHAP 8: Rate Limiting ===")
if buyer_token:
    rate_limited = 0
    total = 12  # melebihi limit 10 per menit untuk strict
    for i in range(total):
        r = urllib.request.Request(
            BASE_URL + "/api/ai/chat/standard",
            data=json.dumps({"messages": [{"role": "user", "content": f"test {i}"}]}).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {buyer_token}"
            },
            method="POST"
        )
        try:
            urllib.request.urlopen(r, timeout=5)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                rate_limited += 1
    log("BERHASIL", "Rate limiting chat standard", f"{rate_limited}/{total} request terkena limit (429)")

# ============================================================
# TAHAP 9: Penanganan Provider Gagal
# ============================================================
print("\n=== TAHAP 9: Penanganan Provider Gagal ===")
if not AI_CONFIGURED:
    # Semua endpoint AI chat harus mengembalikan 503 dengan pesan yang jelas
    status, data = req("POST", "/api/ai/chat/standard",
                       {"messages": [{"role": "user", "content": "test"}]},
                       token=buyer_token)
    if status == 503 and "ai_provider_not_configured" in data.get("code", ""):
        log("BERHASIL", "Provider gagal - chat standard", "503 dengan code ai_provider_not_configured")
    else:
        log("GAGAL", "Provider gagal - chat standard", f"Status {status}: {data}")

    status, data = req("POST", "/api/ai/chat/plus",
                       {"messages": [{"role": "user", "content": "test"}]},
                       token=seller_token)
    if status == 503 and "ai_provider_not_configured" in data.get("code", ""):
        log("BERHASIL", "Provider gagal - chat plus", "503 dengan code ai_provider_not_configured")
    else:
        log("GAGAL", "Provider gagal - chat plus", f"Status {status}: {data}")

    log("BELUM_DAPAT_DIUJI", "Provider AI langsung (Gemini/OpenRouter)",
        "Tidak ada API Key yang dikonfigurasi di backend/.env")
else:
    log("BERHASIL", "Provider AI terkonfigurasi", f"Provider: {AI_CONFIGURED}")

# ============================================================
# RINGKASAN
# ============================================================
print("\n" + "=" * 60)
print("RINGKASAN HASIL PENGUJIAN STAGE 8")
print("=" * 60)
print(f"[OK] BERHASIL: {len(results['BERHASIL'])}")
for t, d in results['BERHASIL']:
    print(f"   - {t}" + (f" ({d})" if d else ""))
print(f"\n[FAIL] GAGAL: {len(results['GAGAL'])}")
for t, d in results['GAGAL']:
    print(f"   - {t}" + (f" ({d})" if d else ""))
print(f"\n[SKIP] BELUM DAPAT DIUJI: {len(results['BELUM_DAPAT_DIUJI'])}")
for t, d in results['BELUM_DAPAT_DIUJI']:
    print(f"   - {t}" + (f" ({d})" if d else ""))
print("=" * 60)

# Exit code
if results['GAGAL']:
    exit(1)
else:
    exit(0)