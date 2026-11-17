# Release Checklist — RuralB2B

> Status: **RELEASE CANDIDATE untuk demonstrasi** — bukan production-ready
> (lihat §7 Keterbatasan). Terakhir diperbarui: 2026-11-11 (Babak 8:
> AI Insights on-demand, audit role, regresi 73/73 bersih).

## 1. Prasyarat Menjalankan Aplikasi

| Komponen | Nilai |
|---|---|
| Python | 3.11+ dengan venv di `backend/venv` (`pip install -r requirements.txt`) |
| Node.js | 18+ (`npm install` di `frontend/`) |
| MySQL | 8.x, database `ruralb2b` (Laragon: root tanpa password) |
| Backend | `venv\Scripts\python.exe app.py` → `http://127.0.0.1:5000` |
| Frontend dev | `npm run dev` → `http://localhost:5173` (proxy `/api` → 5000) |
| Frontend build | `npm run build` → `frontend/dist/` (build sukses 2026-11-11) |
| `backend/.env` | Wajib: `JWT_SECRET_KEY`, konfigurasi DB. Opsional: `GEMINI_API_KEY` (AI), `TELEGRAM_BOT_TOKEN` + `TELEGRAM_ADMIN_CHAT_ID` |
| Akun admin | Dibuat via `bootstrap_admin.py` (env vars) — admin 102 aktif |
| Health check | `GET /api/health` = 200; `GET /api/ai/status` = `configured:true` |

Detail lengkap: `docs/DEPLOYMENT.md`.

## 2. Daftar Pengujian & Status

### 2.1 Backend / API (Babak 1–5, tidak diulang)
| Area | Status |
|---|---|
| 28 endpoint Buyer/Seller/Admin (funnel lengkap) | ✅ PASS |
| Guard capability & kepemilikan sumber daya | ✅ PASS |
| Build frontend + proxy/interceptor | ✅ PASS |

### 2.2 Acceptance Babak 6 (sesi ini)
| # | Uji | Metode | Hasil |
|---|---|---|---|
| T1 | Transisi ilegal `pending→shipped` (langsung) | API | ✅ Ditolak 422 |
| T2 | Konfirmasi bayar order *unpaid* tanpa bukti (#43) | API | ✅ Ditolak 409 |
| T3 | Buyer *receive* order belum *shipped* (#43) | API | ✅ Ditolak 409 |
| T4 | Buyer mengubah pembayaran order milik orang lain | API | ✅ Ditolak 404 |
| T5 | Buyer memanggil endpoint aksi seller | API | ✅ Ditolak 422 |
| T6 | List & detail order buyer 75 / seller 30 / payment #43 | API (read-only) | ✅ PASS (scoping benar: buyer hanya melihat order miliknya) |
| T7 | AI Assistant Standard | API | ✅ 200, respons model Gemini |
| T8 | AI Assistant Plus | API | ✅ 200 |
| T9 | AI Product Recommendation (query bebas) | API | ✅ 200, menghasilkan item |
| T10 | AI Business Insights summary (seller) | API | ✅ 200 |
| T11 | AI error handling: pesan kosong | API | ✅ Ditolak 400 |
| T12 | AI tanpa token | API | ✅ Ditolak 401 |
| S1–S5 | Proteksi auth/otorisasi (unauth 401, buyer→admin 403, akses data orang lain 404) | API | ✅ Semua ditolak benar |
| T13 | Data tidak berubah setelah seluruh uji (order 1/43, stok produk 22, notifikasi) | DB read-only | ✅ Utuh |

**Pengujian yang BELUM dilakukan (tidak boleh diklaim):**
- Telegram end-to-end — menunggu kredensial bot di `backend/.env`.
- Alur *shipped→completed* live (butuh mengubah data order; sengaja tidak
  dijalankan) — state machine tervalidasi di kode (`order_validators.py`)
  dan ditolak-benar lewat T1/T3.
- Pengujian build produksi `dist/` disajikan penuh (visual testing memakai
  dev server Vite).

### 2.3 Visual Testing Babak 7 (2026-11-11) — Chrome headless nyata
Detail lengkap: `docs/LAPORAN_VISUAL_TESTING.md`.
| # | Uji | Metode | Hasil |
|---|---|---|---|
| V1 | 34 rute × 1440/768/375 = **73 uji** render (layout, overflow, console, API) | Chrome headless via `puppeteer-core` | ✅ **71/73 bersih** (2 = 503 transien Gemini; error state OK) |
| V2 | Interaksi: hamburger, login form, dropdown akun, logout, badge notifikasi | Browser nyata | ✅ Semua PASS |
| V3 | Route guard visual (buyer→admin, admin→seller) | Browser nyata | ✅ Redirect benar |
| V4 | 9 bug visual ditemukan & diperbaiki (crash `asChild` 6 lokasi, gambar 404, kontras hero, double navbar, overflow mobile, dll.) | Fix minimal + retest + `npm run build` | ✅ Semua terverifikasi lulus |

### 2.4 Finalisasi Babak 8 (2026-11-11)
| # | Uji | Hasil |
|---|---|---|
| F1 | AI Business Insights on-demand: **0 request** ke `/ai/insights/analyze` saat halaman dibuka (pantau 8 dtk via Chrome headless) | ✅ PASS |
| F2 | Tombol "Analisis Bisnis" → loading → hasil Gemini 200; guard double-click (hanya 1 POST); tombol "Analisis Ulang" di hasil & error state | ✅ PASS |
| F3 | Audit navigasi per role (browser nyata, desktop + mobile): buyer/seller dual ✅, admin tanpa menu Pembelian/Penjualan (capabilities selaras backend yang menolak admin 403) | ✅ PASS |
| F4 | Sweep API read-only seluruh fitur inti (produk/search/cart/order/chat/notif/admin/AI) | ✅ Semua 200; scoping kepemilikan benar |
| F5 | Regresi penuh 73 uji browser | ✅ **73/73 bersih** |

Ringkasan demo akhir: `docs/PERSIAPAN_DEMO_FINAL.md`.

## 3. Status Data Demo (keputusan pemilik: Pilihan B)

Data demo **dipertahankan** (produk 22–33 & 51–52, order 1–12 & 42, akun uji).
Rencana pembersihan menjelang produksi: `docs/RENCANA_PEMBERSIHAN_DATA_DEMO.md`.
Order 43, akun 91, admin 102: tidak disentuh sepanjang Babak 6 (terverifikasi).

**Update 2026-11-11 (Babak 9)**: Order 43 & Order 1 berubah status oleh
**aksi pengujian manual pemilik via UI seller 30** (23:32–23:33, tercatat di
`order_status_logs`) — bukan aksi agent: Order 43 → completed (paid COD,
pembayaran #42), Order 1 → confirmed (unpaid/transfer). Selanjutnya Order 43
diperlakukan sebagai **contoh siklus pesanan penuh**; contoh pesanan pending
berganti ke **Order 42** (seller 76). Distribusi: 9 pending / 4 confirmed /
1 completed; stok 22/24/52 = 1/3/108; verifikasi #9 (user 76) tetap pending.

## 4. Prosedur Backup

### 4.1 Backup database
```powershell
$ts   = Get-Date -Format 'yyyyMMdd_HHmm'
$out  = "C:\laragon\www\ruralb2b\backups\ruralb2b_db_backup_$ts.sql"
New-Item -ItemType Directory -Force -Path C:\laragon\www\ruralb2b\backups | Out-Null
& C:\laragon\bin\mysql\mysql-8.4.3-winx64\bin\mysqldump.exe -u root --databases ruralb2b --routines --triggers --single-transaction --result-file="$out"
# verifikasi: baris terakhir harus "-- Dump completed on ..."
Get-Content $out -Tail 1
```
- Nama file **bertanggal + jam** → tidak pernah menimpa backup lama.
- Folder `backups/` dikecualikan dari Git (root `.gitignore`).

### 4.2 Arsip source code (tanpa credential)
```powershell
$stage = "$env:TEMP\ruralb2b_src_stage"
robocopy C:\laragon\www\ruralb2b $stage /E /XD node_modules venv dist storage backups __pycache__ .git .vscode /XF .env .env.local *.log *.zip *.sql
Compress-Archive -Path "$stage\*" -DestinationPath "C:\laragon\www\ruralb2b\backups\ruralb2b_source_$ts.zip"
```
Yang **tidak ikut** dalam arsip: `.env` (credential), `node_modules`, `venv`,
`dist`, `storage/` (PII), `backups/`. `.env.example` (templat tanpa secret)
ikut. Kalau butuh PII/credential, backup terpisah secara manual dengan
penyimpanan aman.

### 4.3 Backup yang sudah ada (per 2026-11-11)
| Berkas | Ukuran | Verifikasi |
|---|---|---|
| `backups/ruralb2b_db_backup_20261111_2049.sql` | 63,4 KB | "Dump completed"; 46 users/45 profil/14 produk/14 order/payments cocok dgn live; Order 43 ada |
| `backups/ruralb2b_source_20261111_2049.zip` | 316 KB | 161 entri; file kunci lengkap; **0** berkas `.env`/storage/node_modules |

### 4.4 Restore (rollback data)
```powershell
# hentikan backend dulu, lalu:
mysql -u root -e "DROP DATABASE IF EXISTS ruralb2b; CREATE DATABASE ruralb2b CHARACTER SET utf8mb4;"
mysql -u root ruralb2b < backups\ruralb2b_db_backup_YYYYMMDD_HHMM.sql
# verifikasi: SELECT COUNT(*) FROM orders;  (harus 14 per backup 20261111_2049)
```

## 5. Prosedur Menjalankan Aplikasi (ringkas)

1. Jalankan MySQL (Laragon).
2. Backend: `cd backend; venv\Scripts\python.exe app.py` → cek `/api/health`.
3. Frontend dev: `cd frontend; npm run dev` → buka `http://localhost:5173`.
4. Skenario demo 17 langkah: `docs/PANDUAN_DEMO.md`.
5. Matikan dengan Ctrl-C; backend restart wajib setelah `.env` berubah.

## 6. Bug yang Ditemukan & Diperbaiki

**Babak 8 (finalisasi):** mismatch kapabilitas admin — `capabilities.js`
memberi admin `canBuy: true` padahal backend menolak admin dari endpoint
pembelian (`@business_user_required` → 403, terverifikasi API); menu
"Pembelian" diberlakukan selaras backend. Halaman AI Business Insights tidak
lagi memanggil Gemini otomatis saat dibuka (on-demand via tombol).

**Babak 7 (visual): 9 bug ditemukan, semuanya diperbaiki & diuji ulang** —
daftar lengkap dengan langkah reproduksi: `docs/LAPORAN_VISUAL_TESTING.md` §6–8.
Ringkas: crash white screen 4 halaman (`asChild` ×6 lokasi), fabrikasi URL
gambar produk 404 (placeholder SVG lokal), 6 URL Unsplash mati, kontras hero,
double navbar beranda, tombol Cari kosong, overflow mobile detail verifikasi,
CardBody ref, typo AdminDashboard.

Babak 6 **tidak menemukan bug baru** — seluruh negative test ditolak sesuai
desain dan read-only check PASS. Perbaikan kecil selama Babak 5–6:
- Komentar kadaluarsa di `frontend/src/routes/index.jsx` (klaim "tidak ada
  akun admin") dikoreksi — fungsional tidak berubah, build tetap sukses.

## 7. Keterbatasan yang Belum Terselesaikan

1. **Pengujian visual browser SELESAI (Babak 7)** — 73 uji Chrome headless,
   71/73 bersih, 9 bug diperbaiki (`docs/LAPORAN_VISUAL_TESTING.md`).
   Sisa: build produksi `dist/` belum diuji disajikan penuh.
2. **Telegram end-to-end** menunggu `TELEGRAM_BOT_TOKEN` +
   `TELEGRAM_ADMIN_CHAT_ID`.
3. **Database berisi data demo** — katalog/order/statistik menampilkan data
   uji (keputusan Pilihan B; pembersihan menunggu keputusan produksi).
4. **Belum production-ready**: dev-server Flask (gunakan WSGI server di
   produksi — `docs/DEPLOYMENT.md` §4), belum ada HTTPS/domain, belum ada
   monitoring/logging produksi, backup belum dijadwalkan otomatis.
5. Produk demo tanpa `category_id` → filter kategori kosong.

## 8. Prosedur Rollback (jika demo/deploy gagal)

1. **Data**: restore dump terbaru (§4.4). Cek Order 43 & login admin setelah
   restore.
2. **Source**: ekstrak `ruralb2b_source_*.zip` ke folder baru, salin
   `backend/.env` dari luar arsip (tidak ikut arsip), `pip install`,
   `npm install && npm run build`.
3. **Frontend**: kembalikan `frontend/dist/` dari build sebelumnya (simpan
   salinan dist sebelum build baru).
4. Selama rollback, backend dimatikan agar tidak ada request masuk.

## 9. Babak 9 — Integrasi Telegram & Audit Admin (2026-11-11)

| Item | Status | Bukti |
|---|---|---|
| Audit kode Telegram (3 titik notifikasi, non-fatal, dedup, audit log, token aman) | ✅ PASS | `telegram_service.py`, `verification_service.py:254/499/580` |
| `TELEGRAM_CHAT_ID=6830085415` dikonfigurasi di `backend/.env` | ✅ PASS | preflight `not_configured` → terisi; token menyusul |
| Fungsi uji koneksi aman (getMe, tanpa kirim pesan) | ✅ PASS | `backend/telegram_test_connection.py` |
| Kirim notifikasi nyata end-to-end | ⏳ PENDING | menunggu `TELEGRAM_BOT_TOKEN` diisi pemilik + persetujuan uji |
| Guard API Admin (buyer/seller/anonim → 5 endpoint = 403/401) | ✅ PASS | `visualtest/admin_guard_api.json` — 18/18 sesuai harapan |
| Akses Admin ke 5 endpoint admin | ✅ PASS | semua 200 |
| 5 halaman Admin termuat tanpa console error | ✅ PASS | screenshot `shots/admin_audit_*.png` |
| Frontend guard rute admin (roles=['admin']) | ✅ PASS | `routes/index.jsx:231–280` + uji Babak 8 |
| Sinkron dokumentasi kondisi data terkini | ✅ PASS | PANDUAN_DEMO, PERSIAPAN_DEMO_FINAL, RELEASE_CHECKLIST §3 |
| Dokumentasi Telegram baru | ✅ PASS | `docs/KONFIGURASI_TELEGRAM.md` |

## 10. Babak 10 — Final Test Telegram UI, Perbaikan Kartu Login, Regresi Final (2026-11-12)

| Item | Status | Bukti |
|---|---|---|
| Audit implementasi Telegram (getMe aktual, confirm dialog, 1 pesan, tanpa retry, token tak pernah ke frontend, riwayat DB aktual) | ✅ PASS | `telegram_service.py`, `routes/admin.py`, `TelegramSettings.jsx`, `AccountSettings.jsx` |
| Kirim pesan tes nyata dari UI Admin 102 (konfirmasi → 1 pesan) | ✅ PASS | HTTP 200, `sent=true`, **message_id 4** — log backend: tepat 1× POST 200 |
| Hasil pengiriman tampil di UI (toast sukses) | ✅ PASS | toast "Pesan tes terkirim (message_id …)" — diverifikasi tanpa kirim kedua via intersepsi response (POST mock tak pernah sampai server) |
| Dialog konfirmasi wajib + pembatalan tanpa efek | ✅ PASS | uji dialog cancel → 0 request ke endpoint kirim |
| `telegram_logs` tetap 0 setelah pengujian (pesan tes tidak menulis DB — by design) | ✅ PASS | snapshot DB sebelum/sesudah identik |
| Akar masalah kartu promosi Login putih-di-putih | ✅ DIPERBAIKI | Card `bg-white` menang atas `bg-rural-900` (urutan CSS); fix: `!bg-rural-900 !border-rural-800` di `Login.jsx` |
| Palette `rural` kurang shade 200/300/700/800 (`text-rural-200`, `hover:bg-rural-700`, `bg-rural-800`, `border-rural-300` tidak tergenerate) | ✅ DIPERBAIKI | `tailwind.config.js` dilengkapi; kontras kartu Login: putih/green-900 ≈ 9:1 (AAA), subteks rural-200 ≈ 8:1 |
| Backend health | ✅ PASS | `/api/health` → `{"status":"ok","database":"connected"}` |
| Guard API Admin (buyer/seller 403 ×2 endpoint, anonim 401) | ✅ PASS | `final_regression.json` |
| Regresi 3 role × halaman inti (katalog, detail, keranjang, pesanan, dashboard, produk, AI×3, notifikasi, profil) | ✅ PASS | **34/34** (`final_regression.json`) + cek nav role dikoreksi PASS |
| Regresi responsive (desktop 1440 / tablet 768 / mobile 375) | ✅ PASS | katalog & profil admin 3 viewport, screenshot `shots/final_*.png` |
| Frontend build produksi | ✅ PASS | `npm run build` sukses (9.6s, CSS 34.25 kB) |
| Integritas database (46 users/14 orders/8 kategori/14 produk/stok/Order 1-42-43/verifikasi #9) | ✅ PASS | snapshot sebelum = sesudah, byte-identik |

> Kuota AI: pengujian AI dibatasi load UI + endpoint status (tanpa mengirim
> pesan chat) untuk menjaga kuota Gemini 50/hari/akun.
