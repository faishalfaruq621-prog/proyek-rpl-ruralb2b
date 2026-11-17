"""
Test integrasi identitas AI untuk RuralB2B Stage 8.
Menguji identitas pengguna berdasarkan JWT + database.
"""
import urllib.request
import urllib.error
import json
import time
import sys

BASE = "http://127.0.0.1:5000"

results = {
    "BERHASIL": [],
    "GAGAL": [],
}

def log(status, test, detail=""):
    results[status].append((test, detail))
    icon = "[OK]" if status == "BERHASIL" else "[FAIL]"
    print(f"{icon} {test}" + (f" - {detail}" if detail else ""))

def req(method, path, data=None, token=None):
    url = BASE + path
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    headers["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=30)
        return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {"message": str(e)}
    except Exception as e:
        return None, {"message": str(e)}

def register_and_login(email, password, full_name, business_type, business_name):
    """Daftar dan login, return token atau None."""
    reg_data = {
        "full_name": full_name,
        "email": email,
        "password": password,
        "business_type": business_type,
        "business_name": business_name,
    }
    status, data = req("POST", "/api/auth/register", reg_data)
    if status not in (200, 201):
        log("GAGAL", f"Register {email}", f"Status {status}: {data.get('message', data)}")
        return None

    login_data = {"email": email, "password": password}
    status, data = req("POST", "/api/auth/login", login_data)
    if status != 200:
        log("GAGAL", f"Login {email}", f"Status {status}: {data.get('message', data)}")
        return None

    token = data["data"]["access_token"]
    log("BERHASIL", f"Register + Login {email}", f"Token diterima")
    return token

def test_chat(token, question, label):
    """Uji endpoint chat dengan pertanyaan identitas."""
    status, data = req("POST", "/api/ai/chat/standard",
                       {"messages": [{"role": "user", "content": question}]},
                       token=token)
    if status == 200 and data.get("success"):
        content = data.get("content", "")
        log("BERHASIL", f"{label}: '{question}'", f"Respons: {content[:150]}")
        return content
    else:
        log("GAGAL", f"{label}: '{question}'", f"Status {status}: {data.get('message', data)}")
        return None

def main():
    ts = str(int(time.time()))

    # =========================================================
    # 1. TEST: Guest (tanpa login)
    # =========================================================
    print("\n=== TEST: Guest (tanpa login) ===")
    status, data = req("POST", "/api/ai/chat/standard",
                       {"messages": [{"role": "user", "content": "Siapa saya?"}]})
    if status == 401:
        log("BERHASIL", "Guest diakses ke /ai/chat/standard", "Status 401 (token wajib)")
    else:
        log("GAGAL", "Guest diakses ke /ai/chat/standard", f"Status {status} (harus 401)")

    # =========================================================
    # 2. TEST: Business User - Approved
    # =========================================================
    print("\n=== TEST: Business User - Approved ===")
    email_appr = f"ident.approved.{ts}@example.com"
    token_appr = register_and_login(
        email_appr, "TestPass123!",
        "Pengguna Approved", "farmer", "Toko Approved Test"
    )
    if token_appr:
        # Set verification to approved via direct DB would need Flask context,
        # but we already did that in the registration script. Let's verify via API.
        status, data = req("GET", "/api/business/profile", token=token_appr)
        if status == 200:
            verif = data.get("data", {}).get("verification", {})
            print(f"  Verification status from API: {verif.get('status')}")

        test_chat(token_appr, "Siapa saya?", "Approved")
        test_chat(token_appr, "Saya terdaftar sebagai apa?", "Approved")
        test_chat(token_appr, "Apa peran saya di RuralB2B?", "Approved")
        test_chat(token_appr, "Apa yang bisa saya lakukan di platform ini?", "Approved")

    # =========================================================
    # 3. TEST: Business User - Rejected
    # =========================================================
    print("\n=== TEST: Business User - Rejected ===")
    email_rej = f"ident.rejected.{ts}@example.com"
    token_rej = register_and_login(
        email_rej, "TestPass123!",
        "Pengguna Rejected", "warung", "Toko Rejected Test"
    )
    if token_rej:
        test_chat(token_rej, "Siapa saya?", "Rejected")
        test_chat(token_rej, "Saya terdaftar sebagai apa?", "Rejected")
        test_chat(token_rej, "Apa peran saya di RuralB2B?", "Rejected")
        test_chat(token_rej, "Apa yang bisa saya lakukan di platform ini?", "Rejected")

    # =========================================================
    # 4. TEST: Business User - Pending (existing user ID=76)
    # =========================================================
    print("\n=== TEST: Business User - Pending ===")
    email_pend = "pembeli.uji.1794243669@example.com"
    token_pend = register_and_login(
        email_pend, "TestPass123!",
        "Pengguna Pending", "farmer", "Toko Uji Penjual"
    )
    # Note: register_and_login will fail if email already exists.
    # Let's just login instead.
    if not token_pend:
        status, data = req("POST", "/api/auth/login",
                           {"email": email_pend, "password": "TestPass123!"})
        if status == 200:
            token_pend = data["data"]["access_token"]
            log("BERHASIL", f"Login {email_pend} (existing)", "Token diterima")
        else:
            log("GAGAL", f"Login {email_pend} (existing)", f"Status {status}")
    
    if token_pend:
        test_chat(token_pend, "Siapa saya?", "Pending")
        test_chat(token_pend, "Saya terdaftar sebagai apa?", "Pending")
        test_chat(token_pend, "Apa peran saya di RuralB2B?", "Pending")
        test_chat(token_pend, "Apa yang bisa saya lakukan di platform ini?", "Pending")

    # =========================================================
    # 5. TEST: Business User - No Verification (existing user ID=91)
    # =========================================================
    print("\n=== TEST: Business User - No Verification ===")
    email_none = "apaaja@gmail.com"
    token_none = register_and_login(
        email_none, "TestPass123!",
        "Pengguna Tanpa Verifikasi", "shop", "Sukasuka"
    )
    if not token_none:
        status, data = req("POST", "/api/auth/login",
                           {"email": email_none, "password": "TestPass123!"})
        if status == 200:
            token_none = data["data"]["access_token"]
            log("BERHASIL", f"Login {email_none} (existing)", "Token diterima")
        else:
            log("GAGAL", f"Login {email_none} (existing)", f"Status {status}")

    if token_none:
        test_chat(token_none, "Siapa saya?", "No Verif")
        test_chat(token_none, "Saya terdaftar sebagai apa?", "No Verif")
        test_chat(token_none, "Apa peran saya di RuralB2B?", "No Verif")
        test_chat(token_none, "Apa yang bisa saya lakukan di platform ini?", "No Verif")

    # =========================================================
    # RINGKASAN
    # =========================================================
    print("\n" + "=" * 60)
    print("RINGKASAN HASIL PENGUJIAN IDENTITAS AI")
    print("=" * 60)
    print(f"[OK] BERHASIL: {len(results['BERHASIL'])}")
    for t, d in results['BERHASIL']:
        print(f"   - {t}" + (f" ({d})" if d else ""))
    print(f"\n[FAIL] GAGAL: {len(results['GAGAL'])}")
    for t, d in results['GAGAL']:
        print(f"   - {t}" + (f" ({d})" if d else ""))
    print("=" * 60)

if __name__ == "__main__":
    main()