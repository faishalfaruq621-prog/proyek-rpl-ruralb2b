"""
RuralB2B Stage 7 Final Integration Test
Menguji integrasi frontend dengan backend Stage 1-6
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
    """
    data: dict untuk JSON, atau list of tuples untuk form-field (saat files tidak None)
    files: dict of {field_name: (filename, bytes, content_type)}
    """
    url = BASE_URL + path
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    if files:
        boundary = "----RuralB2BFormBoundary" + str(abs(hash(path + str(time.time()))))
        parts = []
        # Add regular form fields
        if data:
            if isinstance(data, dict):
                items = data.items()
            else:
                items = data
            for key, value in items:
                parts.append(f"--{boundary}")
                parts.append(f'Content-Disposition: form-data; name="{key}"')
                parts.append("")
                parts.append(str(value))
        # Add files
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

# ============================================================
# TAHAP 1: Koneksi ke Flask API
# ============================================================
print("\n=== TAHAP 1: Koneksi ke Flask API ===")
status, data = req("GET", "/api/health")
if status == 200:
    log("BERHASIL", "Koneksi ke Flask API (health check)", f"Status {status}")
else:
    log("GAGAL", "Koneksi ke Flask API (health check)", f"Status {status}: {data.get('message', data)}")

# ============================================================
# TAHAP 2: Register, Login, Logout, Persistensi Sesi
# ============================================================
print("\n=== TAHAP 2: Register, Login, Logout, Persistensi Sesi ===")

ts = str(int(time.time()))
buyer_email = f"pembeli.uji.{ts}@example.com"
reg_data = {
    "full_name": "Pembeli Uji",
    "email": buyer_email,
    "password": "RuralB2B!2026",
    "business_type": "farmer",
    "business_name": "Toko Uji Pembeli",
    "phone": "+628123456789",
    "address": "Jl. Test No. 1",
    "city": "Bandung",
    "province": "Jawa Barat",
}
status, data = req("POST", "/api/auth/register", reg_data)
if status == 201:
    log("BERHASIL", "Register user pembeli", f"Status {status}")
else:
    log("GAGAL", "Register user pembeli", f"Status {status}: {data.get('message', data)}")
    buyer_email = None

if buyer_email:
    login_data = {"email": buyer_email, "password": "RuralB2B!2026"}
    status, data = req("POST", "/api/auth/login", login_data)
    if status == 200 and "access_token" in data.get("data", {}):
        buyer_token = data["data"]["access_token"]
        log("BERHASIL", "Login user pembeli", f"Status {status}, token diterima")
    else:
        log("GAGAL", "Login user pembeli", f"Status {status}: {data.get('message', data)}")
        buyer_token = None

if buyer_token:
    status, data = req("GET", "/api/auth/me", token=buyer_token)
    if status == 200:
        user_email = data.get("data", {}).get("user", {}).get("email", "-")
        log("BERHASIL", "Persistensi sesi (GET /auth/me)", f"Status {status}, user: {user_email}")
    else:
        log("GAGAL", "Persistensi sesi (GET /auth/me)", f"Status {status}: {data.get('message', data)}")

if buyer_token:
    status, data = req("POST", "/api/auth/logout", token=buyer_token)
    if status == 200:
        log("BERHASIL", "Logout user pembeli", f"Status {status}")
    else:
        log("GAGAL", "Logout user pembeli", f"Status {status}: {data.get('message', data)}")

if buyer_email:
    login_data = {"email": buyer_email, "password": "RuralB2B!2026"}
    status, data = req("POST", "/api/auth/login", login_data)
    if status == 200:
        buyer_token = data["data"]["access_token"]
    else:
        buyer_token = None

# ============================================================
# TAHAP 3: Pengambilan katalog dan detail produk
# ============================================================
print("\n=== TAHAP 3: Katalog dan Detail Produk ===")

status, data = req("GET", "/api/products")
if status == 200:
    items = data.get("data", {}).get("items", [])
    log("BERHASIL", "Pengambilan katalog produk publik", f"Status {status}, {len(items)} produk")
else:
    log("GAGAL", "Pengambilan katalog produk publik", f"Status {status}: {data.get('message', data)}")
    items = []

status, data = req("GET", "/api/categories")
if status == 200:
    cats = data.get("data", {}).get("items", [])
    log("BERHASIL", "Pengambilan kategori produk", f"Status {status}, {len(cats)} kategori")
else:
    log("GAGAL", "Pengambilan kategori produk", f"Status {status}: {data.get('message', data)}")

if items:
    first_product_id = items[0]["id"]
    status, data = req("GET", f"/api/products/{first_product_id}")
    if status == 200:
        pname = data.get("data", {}).get("product", {}).get("product_name", "-")
        log("BERHASIL", "Detail produk publik", f"Status {status}, produk: {pname}")
    else:
        log("GAGAL", "Detail produk publik", f"Status {status}: {data.get('message', data)}")

# ============================================================
# TAHAP 4: Profil bisnis dan verifikasi
# ============================================================
print("\n=== TAHAP 4: Profil Bisnis dan Verifikasi ===")

verif_id = None
if buyer_token:
    status, data = req("GET", "/api/business/profile", token=buyer_token)
    if status == 200:
        log("BERHASIL", "Lihat profil bisnis", f"Status {status}")
    else:
        log("GAGAL", "Lihat profil bisnis", f"Status {status}: {data.get('message', data)}")

    patch_data = {"phone": "+628123456789", "description": "Toko uji integrasi"}
    status, data = req("PATCH", "/api/business/profile", patch_data, token=buyer_token)
    if status == 200:
        log("BERHASIL", "Update profil bisnis (PATCH)", f"Status {status}")
    else:
        log("GAGAL", "Update profil bisnis (PATCH)", f"Status {status}: {data.get('message', data)}")

    status, data = req("POST", "/api/business/verifications", None, token=buyer_token)
    if status == 201:
        log("BERHASIL", "Ajukan verifikasi UMKM", f"Status {status}")
        verif_id = data.get("data", {}).get("verification", {}).get("id")
    elif status == 409:
        log("GAGAL", "Ajukan verifikasi UMKM", f"Status 409: sudah ada pengajuan pending")
    else:
        log("GAGAL", "Ajukan verifikasi UMKM", f"Status {status}: {data.get('message', data)}")

    status, data = req("GET", "/api/business/verifications", token=buyer_token)
    if status == 200:
        log("BERHASIL", "Lihat daftar verifikasi sendiri", f"Status {status}")
    else:
        log("GAGAL", "Lihat daftar verifikasi sendiri", f"Status {status}: {data.get('message', data)}")

    if verif_id:
        dummy_pdf = (
            b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj "
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj "
            b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]>>endobj "
            b"xref 0 4\n0000000000 65535 f \n0000000009 00000 n \n"
            b"0000000058 00000 n \n0000000115 00000 n \ntrailer<</Size 4/Root 1 0 R>>"
            b"startxref 178\n%%EOF"
        )
        files = {"file": ("ktp.pdf", dummy_pdf, "application/pdf")}
        status, data = req(
            "POST", f"/api/business/verifications/{verif_id}/documents",
            [("document_type", "ktp")], token=buyer_token, files=files
        )
        if status == 201:
            log("BERHASIL", "Upload dokumen verifikasi", f"Status {status}")
        else:
            log("GAGAL", "Upload dokumen verifikasi", f"Status {status}: {data.get('message', data)}")

# ============================================================
# TAHAP 5: Manajemen produk penjual
# ============================================================
print("\n=== TAHAP 5: Manajemen Produk Penjual ===")

product_id = None
if buyer_token:
    product_data = {
        "product_name": "Produk Uji Integrasi",
        "description": "Produk untuk pengujian integrasi",
        "price": 15000,
        "unit": "kg",
        "minimum_order": 1,
        "product_status": "active",
        "stock_quantity": 100,
    }
    status, data = req("POST", "/api/products", product_data, token=buyer_token)
    if status == 201:
        log("BERHASIL", "Buat produk penjual", f"Status {status}")
        product_id = data.get("data", {}).get("product", {}).get("id")
    else:
        log("GAGAL", "Buat produk penjual", f"Status {status}: {data.get('message', data)}")

    status, data = req("GET", "/api/business/products", token=buyer_token)
    if status == 200:
        log("BERHASIL", "Lihat daftar produk sendiri", f"Status {status}")
    else:
        log("GAGAL", "Lihat daftar produk sendiri", f"Status {status}: {data.get('message', data)}")

    if product_id:
        status, data = req("GET", f"/api/business/products/{product_id}", token=buyer_token)
        if status == 200:
            log("BERHASIL", "Detail produk sendiri", f"Status {status}")
        else:
            log("GAGAL", "Detail produk sendiri", f"Status {status}: {data.get('message', data)}")

        patch_data = {"product_name": "Produk Uji Integrasi (Diupdate)"}
        status, data = req("PATCH", f"/api/products/{product_id}", patch_data, token=buyer_token)
        if status == 200:
            log("BERHASIL", "Update produk (PATCH)", f"Status {status}")
        else:
            log("GAGAL", "Update produk (PATCH)", f"Status {status}: {data.get('message', data)}")

        inv_data = {"adjustment": 10}
        status, data = req("PATCH", f"/api/business/inventory/{product_id}", inv_data, token=buyer_token)
        if status == 200:
            log("BERHASIL", "Update stok produk (inventory)", f"Status {status}")
        else:
            log("GAGAL", "Update stok produk (inventory)", f"Status {status}: {data.get('message', data)}")

# ============================================================
# TAHAP 6: Keranjang dan checkout
# ============================================================
print("\n=== TAHAP 6: Keranjang dan Checkout ===")

order_id = None
if buyer_token and product_id:
    cart_data = {"product_id": product_id, "quantity": 2}
    status, data = req("POST", "/api/cart/items", cart_data, token=buyer_token)
    if status == 201:
        log("BERHASIL", "Tambah produk ke keranjang", f"Status {status}")
    else:
        log("GAGAL", "Tambah produk ke keranjang", f"Status {status}: {data.get('message', data)}")

    status, data = req("GET", "/api/cart", token=buyer_token)
    if status == 200:
        log("BERHASIL", "Lihat keranjang belanja", f"Status {status}")
    else:
        log("GAGAL", "Lihat keranjang belanja", f"Status {status}: {data.get('message', data)}")

    checkout_data = {
        "shipping_address": "Jl. Test No. 1, Bandung",
        "buyer_note": "Pengujian integrasi",
        "payment_method": "transfer",
        "payment_reference": f"TRX-{ts}-001",
    }
    status, data = req("POST", "/api/orders/checkout", checkout_data, token=buyer_token)
    if status == 201:
        log("BERHASIL", "Checkout pesanan", f"Status {status}")
        orders = data.get("data", {}).get("orders", [])
        if orders:
            order_id = orders[0]["id"]
    else:
        log("GAGAL", "Checkout pesanan", f"Status {status}: {data.get('message', data)}")

# ============================================================
# TAHAP 7: Riwayat dan detail pesanan
# ============================================================
print("\n=== TAHAP 7: Riwayat dan Detail Pesanan ===")

if buyer_token:
    status, data = req("GET", "/api/orders", token=buyer_token)
    if status == 200:
        log("BERHASIL", "Lihat daftar pesanan pembeli", f"Status {status}")
    else:
        log("GAGAL", "Lihat daftar pesanan pembeli", f"Status {status}: {data.get('message', data)}")

    if order_id:
        status, data = req("GET", f"/api/orders/{order_id}", token=buyer_token)
        if status == 200:
            log("BERHASIL", "Detail pesanan pembeli", f"Status {status}, order #{order_id}")
        else:
            log("GAGAL", "Detail pesanan pembeli", f"Status {status}: {data.get('message', data)}")

        status, data = req("GET", f"/api/orders/{order_id}/payment", token=buyer_token)
        if status == 200:
            log("BERHASIL", "Lihat info pembayaran pesanan", f"Status {status}")
        else:
            log("GAGAL", "Lihat info pembayaran pesanan", f"Status {status}: {data.get('message', data)}")

        pay_data = {
            "payment_method": "transfer",
            "payment_reference": f"TRX-{ts}-001",
            "paid_at": "2026-11-09T10:00:00",
        }
        status, data = req("PATCH", f"/api/orders/{order_id}/payment", pay_data, token=buyer_token)
        if status == 200:
            log("BERHASIL", "Kirim informasi pembayaran", f"Status {status}")
        else:
            log("GAGAL", "Kirim informasi pembayaran", f"Status {status}: {data.get('message', data)}")

# ============================================================
# TAHAP 8: Upload dan download bukti pembayaran
# ============================================================
print("\n=== TAHAP 8: Upload dan Download Bukti Pembayaran ===")

if buyer_token and order_id:
    dummy_proof = (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj "
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj "
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]>>endobj "
        b"xref 0 4\n0000000000 65535 f \n0000000009 00000 n \n"
        b"0000000058 00000 n \n0000000115 00000 n \ntrailer<</Size 4/Root 1 0 R>>"
        b"startxref 178\n%%EOF"
    )
    files = {"file": ("bukti.pdf", dummy_proof, "application/pdf")}
    status, data = req(
        "POST", f"/api/orders/{order_id}/payment/proof",
        None, token=buyer_token, files=files
    )
    if status == 201:
        log("BERHASIL", "Upload bukti pembayaran", f"Status {status}")
    else:
        log("GAGAL", "Upload bukti pembayaran", f"Status {status}: {data.get('message', data)}")

    status, data = req("GET", f"/api/orders/{order_id}/payment/proof/download", token=buyer_token)
    if status == 200:
        log("BERHASIL", "Download bukti pembayaran (pembeli)", f"Status {status}")
    else:
        log("GAGAL", "Download bukti pembayaran (pembeli)", f"Status {status}: {data.get('message', data)}")

# ============================================================
# TAHAP 9: Konfirmasi pembayaran dan perubahan status pesanan
# ============================================================
print("\n=== TAHAP 9: Konfirmasi Pembayaran dan Status Pesanan ===")

if buyer_token and order_id:
    confirm_data = {"payment_method": "transfer"}
    status, data = req(
        "POST", f"/api/seller/orders/{order_id}/payment/confirm",
        confirm_data, token=buyer_token
    )
    if status == 200:
        log("BERHASIL", "Konfirmasi pembayaran (penjual)", f"Status {status}")
    else:
        log("GAGAL", "Konfirmasi pembayaran (penjual)", f"Status {status}: {data.get('message', data)}")

    status_data = {"status": "processing", "notes": "Memproses pesanan"}
    status, data = req(
        "PATCH", f"/api/seller/orders/{order_id}/status",
        status_data, token=buyer_token
    )
    if status == 200:
        log("BERHASIL", "Ubah status pesanan (penjual)", f"Status {status}")
    else:
        log("GAGAL", "Ubah status pesanan (penjual)", f"Status {status}: {data.get('message', data)}")

# ============================================================
# TAHAP 10: Hak akses pembeli, penjual, dan admin
# ============================================================
print("\n=== TAHAP 10: Hak Akses Pembeli, Penjual, dan Admin ===")

if buyer_token:
    status, data = req("GET", "/api/admin/verifications", token=buyer_token)
    if status == 403:
        log("BERHASIL", "Akses admin ditolak untuk non-admin", "Status 403 (dikenal sebagai non-admin)")
    else:
        log("GAGAL", "Akses admin ditolak untuk non-admin", f"Status {status} (harus 403)")

log("BELUM_DAPAT_DIUJI", "Akses admin verifikasi (approve/reject)",
    "Tidak ada akun admin, perlu SQL UPDATE role di database")

# ============================================================
# RINGKASAN
# ============================================================
print("\n" + "=" * 60)
print("RINGKASAN HASIL PENGUJIAN INTEGRASI")
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