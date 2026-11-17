# Arsitektur Sistem RuralB2B

> Dokumen teknis sesuai implementasi aktual (Babak 1–5). Referensi silang:
> fitur per endpoint di `docs/DAFTAR_FITUR.md`, konfigurasi deployment di
> `docs/DEPLOYMENT.md`, skenario demonstrasi di `docs/PANDUAN_DEMO.md`.

## 1. Latar Belakang & Permasalahan

UMKM pedesaan (petani, nelayan, pengrajin) menghadapi rantai pasok panjang:
hasil pertanian/pengerajian melewati banyak perantara sebelum sampai ke
pembeli bisnis (toko, warung, kios, katering) di perkotaan. Akibatnya margin
produsen desa tipis, pembeli bisnis sulit menemukan pemasok langsung dengan
harga grosir yang transparan, dan tidak ada rekam jejak transaksi yang bisa
dipakai membangun kepercayaan antar pihak yang saling tidak kenal.

**RuralB2B menyelesaikan** dengan marketplace B2B yang:

1. Memotong perantara — produsen desa membuka toko dan menjual langsung
   dalam kuantitas grosir (satuan box/kg/sak dengan minimum order).
2. Membangun kepercayaan lewat **sistem verifikasi bisnis** oleh admin
   (dokumen legalitas ditinjau manusia, bukan otomatis).
3. Menyediakan alur transaksi terstruktur: keranjang → checkout → pembayaran
   terverifikasi penjual → pengiriman → konfirmasi penerimaan, dengan log
   status di setiap langkah.
4. Menghadirkan **asisten AI** untuk mendampingi pengguna yang belum terbiasa
   bertransaksi digital: panduan (Assistant), pencarian produk dengan bahasa
   sehari-hari (Recommendation), dan analisa performa toko (Insights).

**Tujuan aplikasi:** mempertemukan penawaran/permintaan grosir desa–kota,
mencatat transaksi secara akuntabel, dan menurunkan hambatan literasi digital
UMKM desa.

**Target pengguna:**
- *Produsen desa* (petani, kelompok tani, nelayan, pengrajin) yang punya
  stok grosir — akun dengan capability `can_sell`.
- *Pembeli bisnis* (pemilik toko/warung/kios/katering) yang membeli dalam
  jumlah besar — akun dengan capability `can_buy`.
- *Administrator* platform yang memverifikasi bisnis dan mengawasi transaksi.

## 2. Perbedaan Buyer dan Seller

Keduanya sama-sama akun `business_user`; perbedaannya di **capability** pada
`business_profiles` (`can_buy`, `can_sell` — bisa keduanya aktif):

| Aspek | Buyer (`can_buy`) | Seller (`can_sell`) |
|---|---|---|
| Fungsi utama | Mencari, membeli, membayar, menerima | Membuka toko, mengelola produk & stok, memproses pesanan |
| Halaman khas | Keranjang, Checkout, Pesanan saya, AI Recommendation | Dashboard penjual, Produk saya, Pesanan masuk, AI Insights, Pengajuan verifikasi |
| Aksi pada order | Buat order, unggah bukti bayar, batalkan, konfirmasi terima | Konfirmasi order, kirim (shipped), konfirmasi pembayaran |
| Data milik | `orders.buyer_id`, `carts.buyer_id` | `products.business_id`, `orders.seller_id` |

Keduanya dipisah di frontend oleh `ProtectedRoute capability=...` dan di
backend oleh middleware `business_user_required` + guard capability, sehingga
buyer tidak bisa memanggil endpoint penjualan dan sebaliknya.

## 3. Alur Transaksi (state machine)

```
                    ┌──────────────┐
   checkout ──────▶ │   pending    │ ◀── order dibuat, stok berkurang
                    └──────┬───────┘
        seller konfirmasi  │           buyer batalkan ──▶ cancelled
                           ▼
                    ┌──────────────┐
                    │  confirmed   │  pembayaran: unpaid ──▶
                    └──────┬───────┘  (buyer unggah bukti) pending_confirmation
        seller kirim       │          ──▶ (seller konfirmasi) paid
                           ▼
                    ┌──────────────┐
                    │   shipped    │
                    └──────┬───────┘
      buyer konfirmasi     │
      penerimaan           ▼
                    ┌──────────────┐
                    │  completed   │
                    └──────────────┘
```

- Setiap transisi status ditulis ke `order_status_logs` (aktor + waktu) dan
  memicu notifikasi in-app ke pihak lawan.
- Pembayaran (`payments`) berjalan paralel: `unpaid → pending_confirmation →
  paid`; bukti bayar disimpan sebagai berkas privat di
  `backend/storage/payment_proofs/order_<id>/`.
- Stok: `inventories.stock_quantity` berkurang saat checkout;
  `reserved_quantity` menjaga order yang sedang berjalan.

## 4. Sistem Verifikasi Bisnis

1. Seller membuka `/verifikasi`, mengisi formulir pengajuan, mengunggah
   dokumen (`POST /business/verifications/:id/documents`).
2. Dokumen disimpan di folder privat (di luar root statis), hanya bisa
   diunduh lewat endpoint terlindungi.
3. Admin meninjau di `/verifikasi/admin` → detail pengajuan menampilkan
   profil bisnis, dokumen, dan riwayat log.
4. Keputusan **Setujui/Tolak**: status pengajuan berubah, `verification_logs`
   mencatat admin_id + keputusan, notifikasi in-app terkirim ke pemohon.
5. **Notifikasi Telegram** (opsional) mengabari admin saat ada pengajuan baru
   dan saat keputusan diambil — dengan dedupe key per event dan fail-safe
   (kegagalan kirim tidak memengaruhi data; status kirim tercatat di
   `telegram_logs`).

## 5. Fitur AI (ringkas)

| Modul | Input | Proses | Output |
|---|---|---|---|
| Assistant Standard | pertanyaan bebas | Gemini, konteks panduan aplikasi | jawaban percakapan |
| Assistant Plus | pertanyaan bisnis | Gemini, prompt analisa mendalam | jawaban analitis |
| Product Recommendation | kebutuhan bebas ("beras untuk warung") | analisa per-kata ke katalog + skor | daftar produk rekomendasi (disimpan `ai_recommendations`) |
| Business Insights | data transaksi seller miliknya | agregat lokal + Gemini | ringkasan, pola transaksi, analisa produk |

Semua endpoint AI memerlukan login, dibatasi `AI_DAILY_LIMIT` per akun/hari,
dan `GET /ai/status` melaporkan konfigurasi + sisa kuota.

## 6. Tumpukan Teknologi

```
┌─────────────────────────────── Browser ───────────────────────────────┐
│  React 18 + Vite + Tailwind CSS + React Router                        │
│  SPA di frontend/ (build → dist/); axios + interceptor JWT            │
└───────────────────────────────┬───────────────────────────────────────┘
                                │  HTTP JSON  /api/*  (dev: proxy Vite
                                │  → http://127.0.0.1:5000)
┌───────────────────────────────▼───────────────────────────────────────┐
│  Flask (Python) backend/app.py — create_app()                         │
│  Blueprint per domain: auth, products, cart, orders, business,        │
│  chat, notifications, ai, admin                                       │
│  Middleware: token_required, admin_required, business_user_required   │
│  Service layer: order_service, payment_service, telegram_service,     │
│  ai_recommendation_service, ai_business_analytics                     │
└───────────────┬──────────────────────────────┬────────────────────────┘
                │ SQLAlchemy                   │ HTTPS (opsional)
┌───────────────▼──────────────┐   ┌───────────▼─────────────────────┐
│  MySQL 8 — database          │   │  Google Gemini API (fitur AI)   │
│  ruralb2b                    │   │  Telegram Bot API (opsional)    │
│  users, business_profiles,   │   └─────────────────────────────────┘
│  products, product_images,   │
│  inventories, categories,    │   Berkas privat di disk:
│  carts, cart_items, orders,  │   backend/storage/payment_proofs/
│  order_items, payments,      │   backend/storage/verification_documents/
│  order_status_logs,          │   backend/storage/product_images/
│  conversations, messages,    │
│  notifications,              │
│  verification_requests,      │
│  verification_documents,     │
│  verification_logs,          │
│  telegram_logs,              │
│  ai_recommendations(+items), │
│  chatbot_sessions(+messages) │
└──────────────────────────────┘
```

### 6.1 Frontend

- **Struktur**: `src/pages` (35+ halaman), `src/components/layout/Navbar`
  (menu berbeda per role/capability + badge notifikasi polling 60 dtk),
  `src/api/*` (service per domain di atas satu axios instance),
  `src/routes/index.jsx` (peta route + gate).
- **Proteksi halaman**: `ProtectedRoute` — belum login → redirect `/login`;
  capability tidak memenuhi → halaman terlarang; admin-only → `roles=['admin']`.
- **Build**: `npm run build` → `dist/`; base URL API lewat
  `VITE_API_BASE_URL` (fallback `http://127.0.0.1:5000/api`).

### 6.2 Backend

- **Blueprint + service layer**: route tipis, logika bisnis (validasi stok,
  transisi status, dedupe notifikasi, integrasi Telegram/AI) di `services/`.
- **Database**: SQLAlchemy ORM; relasi FK penuh (peta 35 FK terdokumentasi di
  `docs/RENCANA_PEMBERSIHAN_DATA_DEMO.md` §3) dengan ON DELETE CASCADE/RESTRICT
  yang menjaga integritas (mis. produk yang pernah diorder tidak bisa dihapus).
- **Berkas**: upload divalidasi (jenis, ukuran ≤ batas env); folder penyimpanan
  dikonfigurasi lewat env (`PAYMENT_PROOF_UPLOAD_DIR`,
  `VERIFICATION_UPLOAD_DIR`).

### 6.3 Database (tabel inti)

| Domain | Tabel |
|---|---|
| Identitas | `users`, `business_profiles`, `categories` |
| Katalog | `products`, `product_images`, `inventories` |
| Transaksi | `carts`, `cart_items`, `orders`, `order_items`, `payments`, `order_status_logs` |
| Komunikasi | `conversations`, `messages`, `notifications` |
| Kepercayaan | `verification_requests`, `verification_documents`, `verification_logs`, `telegram_logs` |
| AI | `ai_recommendations`, `ai_recommendation_items`, `chatbot_sessions`, `chatbot_messages` |

## 7. Keamanan & Autentikasi

| Lapisan | Implementasi |
|---|---|
| Autentikasi | JWT (access + refresh); token disimpan sisi klien, dikirim header `Authorization: Bearer` |
| Password | Hash Werkzeug; kebijakan ganti password via endpoint terlindungi sesi |
| Otorisasi | `token_required` → `admin_required` (14 endpoint admin) / `business_user_required` + capability; kepemilikan data dicek per objek (order/produk hanya untuk pemiliknya) |
| Rangkaian verifikasi | Buyer tidak bisa membeli produk sendiri (409); stok & minimum order divalidasi server-side; order terminal (cancelled/completed) tidak bisa diubah |
| Kerahasiaan | Semua kredensial (DB, JWT secret, Gemini, Telegram) via environment variables (`backend/.env`, tidak masuk Git — `.gitignore` root/backend/frontend); audit pola secret di source code: bersih |
| Berkas privat | Bukti bayar & dokumen verifikasi di `storage/` di luar folder statis, diunduh lewat endpoint terlindungi; `storage/` dikecualikan Git |
| Data pribadi | Password tidak pernah dikembalikan API; log tidak memuat credential |
| Notifikasi | Idempoten via `dedupe_key`; kegagalan Telegram fail-safe |

## 8. Keterbatasan yang Diketahui (per 2026-11-11)

1. **Belum diuji visual di browser** (tool tidak tersedia) — alur terverifikasi
   di level API/integrasi; checklist manual ada di `docs/PANDUAN_DEMO.md` §4.
2. **Telegram belum diuji end-to-end** — menunggu kredensial bot di `.env`.
3. **Database berisi data demo** (keputusan pemilik, Pilihan B); rencana
   pembersihan menjelang produksi ada di `docs/RENCANA_PEMBERSIHAN_DATA_DEMO.md`.
4. Dev-server Flask (`app.py`) hanya untuk pengembangan; produksi disarankan
   WSGI server (lihat `docs/DEPLOYMENT.md` §4).
