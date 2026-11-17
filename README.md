# 🌾 RuralB2B — Platform Marketplace B2B UMKM Pedesaan Indonesia

<div align="center">

![RuralB2B Logo](https://img.shields.io/badge/RuralB2B-Marketplace%20B2B%20UMKM-green?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-black?style=flat-square&logo=flask)
![React](https://img.shields.io/badge/React-18.x-61DAFB?style=flat-square&logo=react)
![MySQL](https://img.shields.io/badge/MySQL-8.x-4479A1?style=flat-square&logo=mysql)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

**Platform Business-to-Business (B2B) yang menghubungkan pelaku UMKM pedesaan  
dengan pembeli dan distributor secara digital, dilengkapi kecerdasan buatan.**

</div>

---

## 📖 Deskripsi Proyek

**RuralB2B** adalah aplikasi web full-stack yang dirancang sebagai platform marketplace B2B khusus untuk UMKM (Usaha Mikro, Kecil, dan Menengah) di wilayah pedesaan Indonesia. Aplikasi ini memungkinkan penjual/produsen lokal mendaftarkan bisnis mereka, mempublikasikan produk, dan mengelola transaksi; sementara pembeli dapat menelusuri katalog, melakukan pemesanan, dan berkomunikasi langsung dengan penjual.

Proyek ini dikembangkan sebagai **Tugas Akhir Rekayasa Perangkat Lunak (RPL)** dan mengimplementasikan praktik pengembangan perangkat lunak modern, mulai dari arsitektur RESTful API, otentikasi JWT, integrasi AI asisten, hingga notifikasi real-time via Telegram Bot.

---

## 🎯 Latar Belakang

Pelaku UMKM di pedesaan Indonesia sering kali menghadapi hambatan untuk mengakses pasar yang lebih luas karena keterbatasan teknologi dan infrastruktur digital. RuralB2B hadir sebagai solusi digital inklusif yang:

- Mempermudah proses pemasaran produk lokal secara online
- Mempersingkat rantai distribusi antara produsen dan pembeli
- Menyediakan sistem verifikasi bisnis untuk membangun kepercayaan
- Menghadirkan asisten AI untuk membantu analisis bisnis dan rekomendasi produk
- Memberikan notifikasi otomatis melalui Telegram Bot kepada admin

---

## ✨ Fitur Utama

### 👤 Autentikasi & Manajemen Pengguna
- Registrasi dan login pengguna dengan email/password
- Sistem JWT (JSON Web Token) untuk sesi yang aman
- Dua peran pengguna: **Penjual (Seller)** dan **Pembeli (Buyer)**
- Pengaturan akun dan profil pengguna

### 🏢 Profil & Verifikasi Bisnis
- Pembuatan dan pengelolaan profil bisnis/toko
- Sistem pengajuan verifikasi bisnis dengan upload dokumen pendukung
- Review dan persetujuan verifikasi oleh admin
- Status verifikasi: Pending → Disetujui / Ditolak

### 🛍️ Katalog & Manajemen Produk
- Penjual dapat menambah, mengedit, dan menghapus produk
- Upload hingga 5 gambar per produk
- Kategori produk yang dikelola admin
- Halaman katalog dengan fitur pencarian dan filter
- Halaman detail produk

### 🛒 Keranjang Belanja & Pemesanan
- Tambah/hapus produk ke keranjang belanja
- Proses checkout dan pembuatan pesanan
- Konfirmasi pesanan oleh penjual
- Upload bukti pembayaran oleh pembeli
- Konfirmasi pembayaran dan pelunasan oleh penjual
- Riwayat pesanan untuk pembeli dan penjual

### 💬 Chat Antar Pengguna
- Sistem pesan langsung antara pembeli dan penjual
- Daftar percakapan aktif
- Thread percakapan per pasangan pengguna

### 🔔 Notifikasi
- Notifikasi in-app untuk aktivitas pesanan, pembayaran, dan verifikasi
- Notifikasi otomatis ke Telegram Bot admin untuk pengajuan verifikasi baru

### 🤖 Integrasi Kecerdasan Buatan (AI)
- **AI Chat Standard**: Asisten AI umum untuk pertanyaan seputar platform
- **AI Chat Plus**: Asisten AI lanjutan dengan konteks bisnis
- **Rekomendasi Produk AI**: Rekomendasi produk berdasarkan preferensi pengguna
- **Analitik Bisnis AI**: Insight dan analisis performa bisnis bagi penjual
- Berbasis Google Gemini API dengan fallback ke OpenRouter
- Batas penggunaan AI per hari per pengguna

### 🛡️ Panel Admin
- Dashboard ringkasan statistik platform
- Manajemen pengguna (lihat, nonaktifkan)
- Manajemen kategori produk (tambah, edit, hapus)
- Manajemen verifikasi bisnis (review, setujui, tolak)
- Manajemen pesanan platform

---

## 🛠️ Teknologi yang Digunakan

### Backend
| Teknologi | Versi | Fungsi |
|-----------|-------|--------|
| Python | 3.11+ | Bahasa pemrograman utama |
| Flask | 3.x | Web framework |
| Flask-SQLAlchemy | 3.x | ORM database |
| PyMySQL | 1.x | Koneksi MySQL |
| PyJWT | 2.x | Autentikasi JWT |
| Flask-CORS | 4.x | Cross-Origin Resource Sharing |
| python-dotenv | 1.x | Manajemen environment |

### Frontend
| Teknologi | Versi | Fungsi |
|-----------|-------|--------|
| React | 18.x | UI library |
| Vite | 5.x | Build tool & dev server |
| React Router DOM | 6.x | Client-side routing |
| Axios | 1.x | HTTP client |
| Tailwind CSS | 3.x | Utility-first CSS framework |
| Lucide React | 0.390+ | Icon library |
| React Hook Form | 7.x | Form management |
| React Hot Toast | 2.x | Notifikasi toast |

### Database & Infrastruktur
| Teknologi | Versi | Fungsi |
|-----------|-------|--------|
| MySQL | 8.x | Database relasional |
| Laragon | Latest | Local development environment (Windows) |

### Layanan Eksternal
| Layanan | Fungsi |
|---------|--------|
| Google Gemini API | AI asisten dan analitik |
| OpenRouter API | Fallback provider AI |
| Telegram Bot API | Notifikasi admin |

---

## 🏗️ Arsitektur Sistem

```
RuralB2B
├── Arsitektur: Monorepo (Backend + Frontend terpisah)
├── Pola API: RESTful API
├── Autentikasi: JWT (stateless)
└── Komunikasi: HTTP/JSON (CORS-enabled)

Frontend (React + Vite)         Backend (Flask + SQLAlchemy)
         │                                    │
         │  HTTP/JSON Requests               │
         ├──────────────────────────────────► │
         │                                    ├── Routes (Blueprint)
         │  JSON Responses                    ├── Services (Business Logic)
         ◄──────────────────────────────────── ├── Models (ORM)
                                              ├── Middleware (Auth, JWT)
                                              └── Database (MySQL)
                                                       │
                                              External Services
                                              ├── Google Gemini API
                                              └── Telegram Bot API
```

---

## 📁 Struktur Direktori

```
ruralb2b/
├── backend/                    # Flask REST API
│   ├── migrations/             # Script migrasi database SQL
│   │   ├── 001_capabilities_notifications_chat.sql
│   │   └── 002_notifications_upgrade.sql
│   ├── middleware/             # Middleware (JWT auth, dll)
│   ├── models/                 # Model SQLAlchemy (ORM)
│   │   ├── user.py             # Model pengguna
│   │   ├── product.py          # Model produk
│   │   ├── order.py            # Model pesanan
│   │   ├── cart.py             # Model keranjang
│   │   ├── business_profile.py # Model profil bisnis
│   │   ├── chat.py             # Model percakapan/pesan
│   │   ├── notification.py     # Model notifikasi
│   │   └── ...                 # Model lainnya
│   ├── routes/                 # Blueprint endpoint API
│   │   ├── auth.py             # /api/auth/*
│   │   ├── products.py         # /api/products/*
│   │   ├── orders.py           # /api/orders/*
│   │   ├── cart.py             # /api/cart/*
│   │   ├── business.py         # /api/business/*
│   │   ├── chat.py             # /api/chat/*
│   │   ├── notifications.py    # /api/notifications/*
│   │   ├── ai.py               # /api/ai/*
│   │   └── admin.py            # /api/admin/*
│   ├── services/               # Business logic layer
│   │   ├── auth_service.py
│   │   ├── product_service.py
│   │   ├── order_service.py
│   │   ├── ai_provider.py      # Abstraksi provider AI
│   │   ├── ai_chat_service.py
│   │   ├── ai_recommendation_service.py
│   │   ├── ai_business_analytics.py
│   │   ├── telegram_service.py # Integrasi Telegram Bot
│   │   └── ...
│   ├── utils/                  # Helper & utilitas
│   ├── docs/                   # Dokumentasi teknis backend
│   ├── app.py                  # Entry point aplikasi
│   ├── config.py               # Konfigurasi aplikasi
│   ├── extensions.py           # Inisialisasi ekstensi Flask
│   ├── requirements.txt        # Dependensi Python
│   └── .env.example            # Template konfigurasi environment
│
├── frontend/                   # React + Vite SPA
│   ├── src/
│   │   ├── api/                # Fungsi pemanggil API (axios)
│   │   │   ├── auth.js         # Auth API calls
│   │   │   ├── ai.js           # AI API calls
│   │   │   └── axios.js        # Konfigurasi axios
│   │   ├── components/         # Komponen React reusable
│   │   │   ├── admin/          # Komponen panel admin
│   │   │   ├── ai/             # Komponen fitur AI
│   │   │   ├── auth/           # Komponen autentikasi
│   │   │   ├── layout/         # Layout (Navbar, Footer, dll)
│   │   │   ├── product/        # Komponen produk
│   │   │   └── ui/             # Komponen UI dasar
│   │   ├── context/            # React Context (Auth, Toast)
│   │   ├── hooks/              # Custom hooks
│   │   ├── pages/              # Halaman utama aplikasi
│   │   │   ├── Home.jsx        # Halaman beranda
│   │   │   ├── Catalog.jsx     # Katalog produk
│   │   │   ├── ProductDetail.jsx
│   │   │   ├── Dashboard.jsx   # Dashboard pengguna
│   │   │   ├── Cart.jsx        # Keranjang belanja
│   │   │   ├── Orders.jsx      # Riwayat pesanan pembeli
│   │   │   ├── SellerOrders.jsx# Pesanan penjual
│   │   │   ├── Verifikasi.jsx  # Halaman verifikasi bisnis
│   │   │   ├── AdminDashboard.jsx
│   │   │   └── ...
│   │   ├── routes/             # Konfigurasi routing
│   │   ├── utils/              # Fungsi utilitas frontend
│   │   ├── App.jsx             # Komponen root
│   │   └── main.jsx            # Entry point React
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── .env.example
│
├── docs/                       # Dokumentasi proyek
│   ├── ARSITEKTUR_SISTEM.md
│   ├── DAFTAR_FITUR.md
│   ├── DEPLOYMENT.md
│   ├── KONFIGURASI_TELEGRAM.md
│   ├── PANDUAN_DEMO.md
│   └── PANDUAN_PENGGUNA.md
│
├── README.md                   # Dokumentasi utama (file ini)
├── LICENSE                     # Lisensi MIT
└── .gitignore                  # Daftar file yang dikecualikan dari Git
```

---

## 💻 Persyaratan Sistem

| Komponen | Minimum |
|----------|---------|
| OS | Windows 10/11 (dengan Laragon) |
| Python | 3.11 atau lebih baru |
| Node.js | 18.x atau lebih baru |
| MySQL | 8.0 atau lebih baru |
| RAM | 4 GB (8 GB direkomendasikan) |
| Storage | 1 GB ruang kosong |

**Software yang diperlukan:**
- [Laragon](https://laragon.org/) — Local development environment (MySQL + Apache)
- [Python](https://www.python.org/downloads/) — Runtime backend
- [Node.js](https://nodejs.org/) — Runtime frontend
- Git — Version control

---

## 🚀 Panduan Instalasi

### 1. Clone Repository

```bash
git clone https://github.com/faishalfaruq621-prog/proyek-rpl-ruralb2b.git
cd proyek-rpl-ruralb2b
```

### 2. Siapkan Database (Laragon)

1. Buka **Laragon** dan pastikan **MySQL** sudah berjalan.
2. Buka **phpMyAdmin** atau **HeidiSQL** (tersedia di Laragon).
3. Buat database baru:
   ```sql
   CREATE DATABASE ruralb2b CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
4. Impor skema database dari file migrasi (urut):
   ```
   backend/migrations/001_capabilities_notifications_chat.sql
   backend/migrations/002_notifications_upgrade.sql
   ```

### 3. Setup Backend (Flask)

```bash
cd backend

# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
# Windows:
venv\Scripts\activate

# Install dependensi
pip install -r requirements.txt

# Salin template environment
copy .env.example .env
```

**Edit file `backend/.env`** dan isi nilai-nilai berikut:
```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=ruralb2b
DB_USER=root
DB_PASSWORD=            # password MySQL Laragon (biasanya kosong)

JWT_SECRET_KEY=         # Wajib: generate dengan: python -c "import secrets; print(secrets.token_urlsafe(48))"

TELEGRAM_BOT_TOKEN=     # Token dari @BotFather (opsional)
TELEGRAM_ADMIN_CHAT_ID= # Chat ID admin Telegram (opsional)

GEMINI_API_KEY=         # API Key dari https://aistudio.google.com (opsional)
```

### 4. Setup Frontend (React)

```bash
cd frontend

# Install dependensi Node.js
npm install

# Salin template environment
copy .env.example .env
```

**Edit file `frontend/.env`** (biasanya tidak perlu diubah untuk development lokal):
```env
VITE_API_BASE_URL=http://127.0.0.1:5000/api
VITE_APP_NAME=RuralB2B
VITE_APP_TAGLINE=Marketplace B2B UMKM Pedesaan Indonesia
```

---

## ▶️ Menjalankan Aplikasi

### Jalankan Backend

```bash
cd backend

# Aktifkan virtual environment (jika belum aktif)
venv\Scripts\activate

# Jalankan Flask development server
python app.py
```

Backend akan berjalan di: **http://127.0.0.1:5000**

Verifikasi: buka http://127.0.0.1:5000/api/health → harus mengembalikan `{"status": "ok"}`

### Jalankan Frontend

Buka terminal baru:

```bash
cd frontend

# Mode development
npm run dev
```

Frontend akan berjalan di: **http://localhost:5173**

### Akses Aplikasi

| URL | Keterangan |
|-----|-----------|
| `http://localhost:5173` | Aplikasi web utama |
| `http://127.0.0.1:5000` | Backend API |
| `http://127.0.0.1:5000/api/health` | Health check API |

---

## 🔐 Konfigurasi Environment

### Backend (`backend/.env`)

| Variabel | Wajib | Keterangan |
|----------|-------|-----------|
| `DB_HOST` | ✅ | Host database MySQL |
| `DB_PORT` | ✅ | Port MySQL (default: 3306) |
| `DB_NAME` | ✅ | Nama database |
| `DB_USER` | ✅ | Username MySQL |
| `DB_PASSWORD` | ✅ | Password MySQL |
| `JWT_SECRET_KEY` | ✅ | Secret key untuk token JWT (min. 32 karakter) |
| `JWT_EXPIRES_MINUTES` | ✅ | Durasi token JWT (default: 60) |
| `FLASK_PORT` | ✅ | Port backend (default: 5000) |
| `CORS_ORIGINS` | ✅ | Daftar origin frontend yang diizinkan |
| `GEMINI_API_KEY` | ⬜ | API key Google Gemini untuk fitur AI |
| `TELEGRAM_BOT_TOKEN` | ⬜ | Token Telegram Bot untuk notifikasi admin |
| `TELEGRAM_ADMIN_CHAT_ID` | ⬜ | Chat ID admin Telegram |

### Frontend (`frontend/.env`)

| Variabel | Keterangan |
|----------|-----------|
| `VITE_API_BASE_URL` | URL backend API (default: `http://127.0.0.1:5000/api`) |
| `VITE_APP_NAME` | Nama aplikasi |
| `VITE_APP_TAGLINE` | Tagline aplikasi |

---

## 🤖 Integrasi AI (Google Gemini)

Aplikasi menggunakan Google Gemini API untuk fitur kecerdasan buatan:

1. Dapatkan API Key dari [Google AI Studio](https://aistudio.google.com)
2. Isi `GEMINI_API_KEY` di `backend/.env`
3. Konfigurasikan model di `GEMINI_MODEL` (default: `gemini-2.0-flash-lite`)

**Fitur AI yang tersedia:**
- Chat AI asisten (Standard & Plus)
- Rekomendasi produk cerdas
- Analitik dan insight bisnis

---

## 📱 Integrasi Telegram Bot

Notifikasi otomatis dikirim ke Telegram admin saat ada pengajuan verifikasi bisnis baru:

1. Buat bot baru via [@BotFather](https://t.me/BotFather) di Telegram → salin token
2. Kirim pesan ke bot Anda, lalu cek Chat ID via [@userinfobot](https://t.me/userinfobot)
3. Isi `TELEGRAM_BOT_TOKEN` dan `TELEGRAM_ADMIN_CHAT_ID` di `backend/.env`

Detail lengkap: lihat [docs/KONFIGURASI_TELEGRAM.md](docs/KONFIGURASI_TELEGRAM.md)

---

## 🧪 Menjalankan Pengujian

### Integration Test

```bash
# Pastikan backend sedang berjalan di port 5000
cd ruralb2b  # root proyek

# Aktifkan virtual environment backend
backend\venv\Scripts\activate

# Jalankan integration test
python test_integration.py
python test_integration_v2.py
python test_stage8_integration.py
```

### Identity & Authentication Test

```bash
python test_identity.py
```

---

## 📚 Dokumentasi Tambahan

| Dokumen | Isi |
|---------|-----|
| [docs/ARSITEKTUR_SISTEM.md](docs/ARSITEKTUR_SISTEM.md) | Arsitektur teknis detail |
| [docs/DAFTAR_FITUR.md](docs/DAFTAR_FITUR.md) | Spesifikasi fitur lengkap |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Panduan deployment production |
| [docs/PANDUAN_PENGGUNA.md](docs/PANDUAN_PENGGUNA.md) | Panduan penggunaan aplikasi |
| [docs/PANDUAN_DEMO.md](docs/PANDUAN_DEMO.md) | Skenario demonstrasi |
| [docs/KONFIGURASI_TELEGRAM.md](docs/KONFIGURASI_TELEGRAM.md) | Konfigurasi Telegram Bot |

---

## 👥 Tim Pengembang

Proyek ini dikembangkan sebagai Tugas Akhir Mata Kuliah **Rekayasa Perangkat Lunak (RPL)**.

---

## 📄 Lisensi

Proyek ini dilisensikan di bawah [MIT License](LICENSE).

---

<div align="center">

**RuralB2B** — *Membangun Jembatan Digital untuk UMKM Pedesaan Indonesia* 🌾

</div>
