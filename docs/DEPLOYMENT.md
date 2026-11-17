# Panduan Deployment RuralB2B (Windows + Laragon)

> Dokumen konfigurasi untuk menjalankan RuralB2B di lingkungan produksi/dev
> Windows dengan Laragon. Semua credential masuk lewat environment variables
> (file `backend/.env`) — tidak ada secret di dalam source code.

## 1. Prasyarat

| Komponen | Versi minimum | Catatan |
|---|---|---|
| Python | 3.11+ | gunakan venv di `backend/venv` |
| Node.js | 18+ | untuk build frontend |
| MySQL | 8.x | database `ruralb2b` |
| Laragon | full | menyediakan MySQL & servable Apache/nginx (opsional) |

## 2. Struktur

```
ruralb2b/
├── backend/          # Flask API (port 5000)
│   ├── app.py        # entrypoint: create_app()
│   ├── .env          # KREDENSIAL — tidak boleh masuk Git (sudah di .gitignore)
│   ├── .env.example  # templat konfigurasi
│   ├── venv/         # virtual environment
│   ├── storage/      # file privat: bukti bayar, dokumen verifikasi, gambar produk
│   │   ├── payment_proofs/
│   │   ├── verification_documents/
│   │   └── product_images/
│   └── bootstrap_admin.py  # pembuatan akun admin pertama (env vars)
├── frontend/         # React + Vite + Tailwind (build → dist/)
└── docs/             # dokumentasi proyek
```

## 3. Konfigurasi Environment Variables (`backend/.env`)

Salin `.env.example` → `.env` lalu isi. Nilai yang wajib/opsional:

### Wajib
| Variabel | Keterangan |
|---|---|
| `SECRET_KEY` | secret key Flask (acak, ≥32 karakter, jangan pernah di-commit) |
| `DATABASE_URL` / konfigurasi MySQL | host/user/password/nama db (default Laragon: root tanpa password) |
| `JWT_SECRET_KEY` | kunci token JWT (acak, unik per environment) |

### AI (fitur chat & insight)
| Variabel | Keterangan |
|---|---|
| `AI_PROVIDER` | `gemini` atau `openrouter` |
| `GEMINI_API_KEY` | API key Gemini (https://aistudio.google.com) |
| `GEMINI_MODEL` | model Gemini yang dipakai |
| `OPENROUTER_API_KEY` | (jika provider openrouter) |
| `AI_DAILY_LIMIT` | limit request AI harian per user (default 50) |

### Telegram (notifikasi verifikasi bisnis ke admin)
| Variabel | Keterangan |
|---|---|
| `TELEGRAM_BOT_TOKEN` | token dari @BotFather |
| `TELEGRAM_ADMIN_CHAT_ID` | chat ID admin (alias `TELEGRAM_CHAT_ID` juga diterima) |
| `TELEGRAM_API_TIMEOUT` | timeout kirim (detik, default 5) |

Cara mengisi: buat bot via @BotFather → dapat token → kirim satu pesan apa pun
ke bot dari akun admin → ambil chat ID (mis. via @userinfobot) → isi dua
variabel → restart backend. Jika kosong/gagal, aplikasi tetap berjalan;
pengajuan verifikasi tetap tersimpan dan status pengiriman tercatat di tabel
`telegram_logs`.

### Upload & batasan file
| Variabel | Default | Keterangan |
|---|---|---|
| `VERIFICATION_UPLOAD_DIR` | `backend/dokumen verifikasi` | folder dokumen verifikasi (HARUS di luar folder statis publik) |
| `PAYMENT_PROOF_UPLOAD_DIR` | `backend/storage/payment_proofs` | folder bukti pembayaran |
| `MAX_PAYMENT_PROOF_SIZE` | 5 MB | batas ukuran bukti bayar |
| `MAX_CONTENT_LENGTH` | 10 MB | batas body request Flask |

> Catatan: `VERIFICATION_UPLOAD_DIR` di `.env` saat ini kosong sehingga
> memakai default `backend/dokumen verifikasi`. Untuk produksi disarankan
> mengarahkan ke `backend/storage/verification_documents` agar semua file
> privat berada di `storage/` (sudah dikecualikan dari Git).

## 4. Menjalankan Backend

```powershell
cd C:\laragon\www\ruralb2b\backend
# pertama kali:
python -m venv venv
venv\Scripts\pip install -r requirements.txt
# database awal (pilih salah satu sesuai mekanisme proyek):
#   venv\Scripts\flask --app app db upgrade    # jika migrasi tersedia
#   atau impor dump SQL yang disediakan

# membuat akun admin pertama (credential lewat env, bukan file):
$env:ADMIN_EMAIL='admin@domain-anda.com'
$env:ADMIN_NAME='Administrator'
$env:ADMIN_PASSWORD='<password kuat>'
venv\Scripts\python.exe bootstrap_admin.py

# menjalankan (dev):
venv\Scripts\python.exe app.py          # listen di port 5000
```

Untuk produksi gunakan server WSGI (mis. `waitress-serve --host=127.0.0.1
--port=5000 app:app`) dan jalankan sebagai service; `app.py` dev-server hanya
untuk pengembangan.

## 5. Menjalankan Frontend

```powershell
cd C:\laragon\www\ruralb2b\frontend
npm install
npm run build          # hasil: frontend/dist/
```

Serve `dist/` dengan salah satu cara:
1. **Laragon**: buat virtual host yang document root-nya menunjuk `frontend/dist`
   dan konfigurasikan reverse-proxy `/api` → `http://127.0.0.1:5000`.
2. **Static server + proxy** (mis. `vite preview --port 4173`, atau nginx).

Base URL API frontend diatur lewat `VITE_API_BASE_URL` (fallback
`http://127.0.0.1:5000/api`, lihat `frontend/src/api/axios.js`). Saat build
produksi, set variabel ini ke domain API yang sebenarnya, contoh:

```powershell
$env:VITE_API_BASE_URL='https://api.domain-anda.com/api'
npm run build
```

## 6. Keamanan

- `.gitignore` (root, backend, frontend) sudah mengecualikan `.env`, `storage/`,
  `venv/`, `node_modules/`, `dist/`. Verifikasi: `git status` tidak menampilkan
  `.env` maupun `storage/`.
- Endpoint admin memakai decorator `@admin_required` (role ≠ admin → 403).
- Endpoint bisnis memakai `@business_user_required` + guard capability
  (`can_buy`/`can_sell`).
- Password di-hash Werkzeug; tidak ada password plaintext di DB/log.
- Audit secret otomatis (pola API key/token) terhadap source code: bersih.

## 7. Health Check pasca-deploy

| Endpoint | Ekspektasi |
|---|---|
| `GET /api/health` | 200 |
| `GET /api/products` | 200 (list produk) |
| `POST /api/auth/login` (akun admin) | 200 + access_token |
| `GET /api/ai/status` | 200, `configured: true` (bila AI key terisi) |
| `GET /api/admin/stats` (admin) | 200 |

## 8. Operating Notes

- Restart backend setiap kali `.env` atau source backend berubah.
- Backup rutin: `mysqldump -u root ruralb2b > backup_YYYYMMDD.sql` +
  salin folder `storage/`.
- Dokumen verifikasi & bukti bayar di `storage/` adalah PII — batasi akses
  filesystem (ACL) dan jangan tautkan dari domain publik.
- Rencana pembersihan data demo: lihat `docs/RENCANA_PEMBERSIHAN_DATA_DEMO.md`.
