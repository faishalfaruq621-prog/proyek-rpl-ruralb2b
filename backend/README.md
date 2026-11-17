# RuralB2B Backend - Autentikasi, Profil Bisnis, Verifikasi, dan Katalog Produk

Backend marketplace B2B RuralB2B berbasis **Flask**, **SQLAlchemy**, dan **MySQL Laragon**.

Tahap yang sudah selesai:

- Autentikasi JWT: registrasi, login, logout, profil akun.
- Profil bisnis: lihat, ubah, alamat/lokasi, telepon, deskripsi.
- Verifikasi UMKM: pengajuan, upload dokumen, status, alasan penolakan.
- Admin: daftar/detail pengajuan, approve, reject, riwayat.
- Notifikasi Telegram ke admin (opsional, tidak menggagalkan pengajuan).
- Katalog produk: CRUD produk penjual, inventori, gambar, dan katalog publik.

Frontend belum dibangun. Dokumentasi rinci tahap 4 dan tahap 5 ada di
[`docs/BUSINESS_VERIFICATION_API.md`](docs/BUSINESS_VERIFICATION_API.md) dan
[`docs/PRODUCT_CATALOG_API.md`](docs/PRODUCT_CATALOG_API.md).

## 1. Ringkasan

| Komponen | Teknologi |
|---|---|
| Web framework | Flask 3.x |
| ORM | SQLAlchemy 2.x + Flask-SQLAlchemy |
| Database | MySQL 8 (Laragon) |
| Password hashing | Werkzeug `generate_password_hash` (scrypt) |
| Token | JWT HS256 (`PyJWT`) |
| CORS | Flask-Cors |
| Upload dokumen | Penyimpanan privat + validasi ekstensi/magic bytes/ukuran |
| Upload gambar produk | Penyimpanan privat + validasi ekstensi/magic bytes/ukuran/jumlah |
| Notifikasi | Telegram Bot API (opsional) |

Endpoint yang tersedia:

| Method | Endpoint | Autentikasi | Keterangan |
|---|---|---|---|
| `GET` | `/` | Tidak | Info aplikasi |
| `GET` | `/api/health` | Tidak | Cek koneksi database |
| `POST` | `/api/auth/register` | Tidak | Registrasi pengguna bisnis |
| `POST` | `/api/auth/login` | Tidak | Login dan dapatkan JWT |
| `GET` | `/api/auth/me` | Bearer token | Profil pengguna aktif |
| `POST` | `/api/auth/logout` | Bearer token | Revoke token aktif |
| `GET` | `/api/business/profile` | Bearer token | Profil bisnis sendiri + status verifikasi |
| `PUT` | `/api/business/profile` | Bearer token | Ganti profil bisnis |
| `PATCH` | `/api/business/profile` | Bearer token | Ubah sebagian profil bisnis |
| `GET` | `/api/business/verifications` | Bearer token | Daftar pengajuan sendiri |
| `POST` | `/api/business/verifications` | Bearer token | Ajukan verifikasi |
| `GET` | `/api/business/verifications/{id}` | Bearer token | Detail pengajuan sendiri |
| `POST` | `/api/business/verifications/{id}/documents` | Bearer token | Upload dokumen pendukung |
| `GET` | `/api/business/verifications/{id}/documents/{doc_id}/download` | Bearer token | Unduh dokumen sendiri |
| `GET` | `/api/admin/verifications` | Admin | Seluruh pengajuan |
| `GET` | `/api/admin/verifications/{id}` | Admin | Detail pengajuan + dokumen + riwayat |
| `POST` | `/api/admin/verifications/{id}/approve` | Admin | Setujui pengajuan |
| `POST` | `/api/admin/verifications/{id}/reject` | Admin | Tolak dengan alasan |
| `GET` | `/api/admin/verifications/{id}/logs` | Admin | Riwayat verifikasi |
| `GET` | `/api/admin/verifications/{id}/documents/{doc_id}/download` | Admin | Unduh dokumen |
| `GET` | `/api/products` | Tidak | Katalog produk publik |
| `GET` | `/api/products/{id}` | Tidak | Detail produk publik |
| `GET` | `/api/products/{product_id}/images/{image_id}/file` | Tidak | File gambar produk publik |
| `GET` | `/api/categories` | Tidak | Daftar kategori |
| `POST` | `/api/products` | Bearer token | Buat produk milik sendiri |
| `PUT` | `/api/products/{id}` | Bearer token | Ganti produk milik sendiri |
| `PATCH` | `/api/products/{id}` | Bearer token | Ubah sebagian produk/status |
| `DELETE` | `/api/products/{id}` | Bearer token | Hapus produk milik sendiri |
| `POST` | `/api/products/{id}/images` | Bearer token | Upload gambar produk |
| `DELETE` | `/api/products/{id}/images/{image_id}` | Bearer token | Hapus gambar produk |
| `GET` | `/api/business/products` | Bearer token | Daftar produk sendiri |
| `GET` | `/api/business/products/{id}` | Bearer token | Detail produk sendiri |
| `GET` | `/api/business/products/{product_id}/images/{image_id}/file` | Bearer token | File gambar produk sendiri |
| `GET` | `/api/business/inventory` | Bearer token | Daftar inventori sendiri |
| `PATCH` | `/api/business/inventory/{product_id}` | Bearer token | Set/tambah/kurangi stok |
| `GET` | `/api/cart` | Bearer token | Lihat keranjang belanja sendiri |
| `POST` | `/api/cart/items` | Bearer token | Tambah produk ke keranjang |
| `PATCH` | `/api/cart/items/{item_id}` | Bearer token | Ubah jumlah item keranjang |
| `DELETE` | `/api/cart/items/{item_id}` | Bearer token | Hapus item keranjang |
| `POST` | `/api/orders/checkout` | Bearer token | Checkout keranjang, pecah per penjual |
| `GET` | `/api/orders` | Bearer token | Daftar pesanan sebagai pembeli |
| `GET` | `/api/orders/{order_id}` | Bearer token | Detail pesanan sebagai pembeli |
| `POST` | `/api/orders/{order_id}/cancel` | Bearer token | Batalkan pesanan sendiri |
| `GET` | `/api/orders/{order_id}/payment` | Bearer token | Lihat info pembayaran pesanan |
| `PATCH` | `/api/orders/{order_id}/payment` | Bearer token | Kirim informasi pembayaran |
| `POST` | `/api/orders/{order_id}/payment/proof` | Bearer token | Upload bukti pembayaran |
| `GET` | `/api/orders/{order_id}/payment/proof/download` | Bearer token | Unduh bukti pembayaran sendiri |
| `GET` | `/api/seller/orders` | Bearer token | Daftar pesanan sebagai penjual |
| `GET` | `/api/seller/orders/{order_id}` | Bearer token | Detail pesanan sebagai penjual |
| `PATCH` | `/api/seller/orders/{order_id}/status` | Bearer token | Ubah status pesanan (penjual) |
| `POST` | `/api/seller/orders/{order_id}/payment/confirm` | Bearer token | Konfirmasi pembayaran (penjual) |
| `GET` | `/api/seller/orders/{order_id}/payment/proof/download` | Bearer token | Unduh bukti pembayaran (penjual) |

## 2. Struktur Proyek

```text
backend/
├── app.py                     # Application factory, CORS, error handler, entry point
├── config.py                  # Konfigurasi DB, JWT, upload, Telegram dari .env
├── extensions.py              # Instance SQLAlchemy (menghindari circular import)
├── requirements.txt           # Dependensi Python
├── .env.example               # Contoh konfigurasi (tanpa secret asli)
├── .env                       # Konfigurasi lokal, tidak boleh di-commit
├── .gitignore
├── models/
│   ├── __init__.py
│   ├── user.py                # Mapping tabel users
│   ├── business_profile.py    # Mapping tabel business_profiles
│   ├── verification_request.py
│   ├── verification_document.py
│   ├── verification_log.py
│   ├── telegram_log.py
│   ├── category.py            # Mapping tabel categories (Tahap 5)
│   ├── product.py             # Mapping tabel products (Tahap 5)
│   ├── product_image.py       # Mapping tabel product_images (Tahap 5)
│   ├── inventory.py           # Mapping tabel inventories (Tahap 5)
│   ├── cart.py                # Mapping tabel carts (Tahap 6)
│   ├── cart_item.py           # Mapping tabel cart_items (Tahap 6)
│   ├── order.py               # Mapping tabel orders (Tahap 6)
│   ├── order_item.py          # Mapping tabel order_items (Tahap 6)
│   ├── order_status_log.py    # Mapping tabel order_status_logs (Tahap 6)
│   └── payment.py             # Mapping tabel payments (Tahap 6)
├── routes/
│   ├── __init__.py
│   ├── auth.py                # Blueprint /api/auth
│   ├── business.py            # Blueprint /api/business
│   ├── admin.py               # Blueprint /api/admin
│   ├── products.py            # Blueprint /api/products (Tahap 5)
│   ├── cart.py                # Blueprint /api/cart (Tahap 6)
│   └── orders.py              # Blueprint /api/orders (Tahap 6)
├── services/
│   ├── __init__.py
│   ├── auth_service.py        # Registrasi dan login
│   ├── business_profile_service.py
│   ├── verification_service.py
│   ├── storage_service.py     # Simpan/validasi/ambil file privat
│   ├── telegram_service.py    # Notifikasi Telegram + audit
│   ├── product_service.py     # CRUD produk dan katalog (Tahap 5)
│   ├── product_image_storage_service.py  # Simpan/gambar produk (Tahap 5)
│   ├── cart_service.py        # Logika keranjang belanja (Tahap 6)
│   ├── order_service.py       # Checkout, pesanan, dan status (Tahap 6)
│   ├── payment_service.py     # Informasi dan konfirmasi pembayaran (Tahap 6)
│   └── payment_proof_storage_service.py  # Penyimpanan bukti pembayaran (Tahap 6)
├── middleware/
│   ├── __init__.py
│   └── auth.py                # token_required dan admin_required
├── utils/
│   ├── __init__.py
│   ├── api_error.py           # Exception + response error konsisten
│   ├── jwt_utils.py           # Encode/decode JWT
│   ├── token_blocklist.py     # Revoke token untuk logout
│   ├── validators.py          # Validasi auth + konstanta dokumen
│   ├── profile_validators.py  # Validasi profil bisnis
│   ├── pagination.py          # Pagination query string
│   ├── request_utils.py       # Helper body JSON
│   ├── order_validators.py    # Validasi keranjang, pesanan, status, pembayaran (Tahap 6)
│   └── product_validators.py  # Validasi produk dan inventori (Tahap 5)
├── storage/
│   ├── verification_documents/  # File privat, dibuat otomatis
│   ├── product_images/          # File gambar produk privat, dibuat otomatis
│   └── payment_proofs/          # File bukti pembayaran privat, dibuat otomatis
└── docs/
    ├── RuralB2B-Auth.postman_collection.json
    ├── RuralB2B-Business-Verification.postman_collection.json
    ├── RuralB2B-Product-Catalog.postman_collection.json
    ├── RuralB2B-Cart-Order.postman_collection.json  # Koleksi Postman Tahap 6
    ├── BUSINESS_VERIFICATION_API.md
    ├── PRODUCT_CATALOG_API.md
    └── CART_ORDER_API.md  # Dokumentasi API Tahap 6
```

File tahap 5 yang ditambahkan antara lain:

- `models/category.py`, `models/product.py`, `models/product_image.py`, `models/inventory.py`
- `services/product_service.py`, `services/product_image_storage_service.py`
- `routes/products.py`, `utils/product_validators.py`
- `docs/PRODUCT_CATALOG_API.md`, `docs/RuralB2B-Product-Catalog.postman_collection.json`

File tahap 6 yang ditambahkan antara lain:

- `models/cart.py`, `models/cart_item.py`, `models/order.py`, `models/order_item.py`, `models/order_status_log.py`, `models/payment.py`
- `services/cart_service.py`, `services/order_service.py`, `services/payment_service.py`, `services/payment_proof_storage_service.py`
- `routes/cart.py`, `routes/orders.py`, `utils/order_validators.py`
- `docs/CART_ORDER_API.md`, `docs/RuralB2B-Cart-Order.postman_collection.json`

## 3. Kesesuaian dengan Database yang Sudah Ada

Tidak ada tabel yang dibuat, diubah, atau dihapus. Model SQLAlchemy disesuaikan
dengan struktur aktual:

### `users`

| Kolom | Tipe | Catatan |
|---|---|---|
| `id` | BIGINT UNSIGNED PK | Auto increment |
| `full_name` | VARCHAR(150) | Wajib |
| `email` | VARCHAR(190) UNIQUE | Disimpan lowercase, unik |
| `password_hash` | VARCHAR(255) | Hash scrypt, bukan password asli |
| `role` | ENUM(`business_user`,`admin`) | Registrasi selalu `business_user` |
| `account_status` | ENUM(`active`,`suspended`,`inactive`) | Registrasi selalu `active` |
| `created_at`, `updated_at` | DATETIME | Default/ON UPDATE dari MySQL |

### `business_profiles`

Satu user memiliki satu profil bisnis (`user_id` UNIQUE, FK ke `users.id`).

| Kolom | Tipe | Catatan |
|---|---|---|
| `business_name` | VARCHAR(180) | Wajib di database; API memakai `full_name` bila tidak dikirim |
| `business_type` | ENUM(`farmer`,`supplier`,`collector`,`producer`,`shop`,`warung`,`other`) | Default API `other` |
| `phone` | VARCHAR(30) | Opsional, disimpan di profil bisnis |
| `address`, `village`, `district`, `city`, `province`, `postal_code`, `description` | — | Opsional |
| `latitude`, `longitude` | DECIMAL(10,7) | Belum diisi lewat API registrasi |

Karena `users` tidak memiliki kolom telepon, nomor telepon disimpan pada
`business_profiles.phone` sesuai skema yang ada. Registrasi membuat **dua baris**
dalam satu transaksi: `users` dan `business_profiles`.

### `verification_requests`

| Kolom | Tipe | Catatan |
|---|---|---|
| `id` | BIGINT UNSIGNED PK | Auto increment |
| `business_profile_id` | BIGINT UNSIGNED FK | Ke `business_profiles.id` |
| `status` | ENUM(`pending`,`approved`,`rejected`) | Status pengajuan |
| `submitted_at` | DATETIME | Default `CURRENT_TIMESTAMP` |
| `reviewed_by` | BIGINT UNSIGNED FK | Ke `users.id`, admin yang memutuskan |
| `reviewed_at` | DATETIME | Waktu keputusan admin |
| `rejection_reason` | TEXT | Alasan saat ditolak |

### `verification_documents`

| Kolom | Tipe | Catatan |
|---|---|---|
| `id` | BIGINT UNSIGNED PK | Auto increment |
| `verification_id` | BIGINT UNSIGNED FK | Ke `verification_requests.id` |
| `document_type` | VARCHAR(80) | `ktp`, `kk`, `npwp`, `nib`, `siup`, `business_photo`, `other` |
| `file_path` | VARCHAR(500) | Path relatif privat, tidak diekspos API |
| `uploaded_at` | DATETIME | Default `CURRENT_TIMESTAMP` |

### `verification_logs`

Mencatat setiap perubahan status: pembuatan pengajuan (`NULL -> pending`),
approve (`pending -> approved`), dan reject (`pending -> rejected`).

### `products`, `categories`, `product_images`, dan `inventories`

Tahap 5 memakai tabel yang sudah ada tanpa perubahan DDL. Produk terhubung ke
`business_profiles`; stok disimpan di `inventories`; gambar di `product_images`;
kategori opsional di `categories`. Detail kolom, aturan, dan contoh response ada di
[`docs/PRODUCT_CATALOG_API.md`](docs/PRODUCT_CATALOG_API.md).

Catatan skema: tidak ada kolom harga grosir dan tidak ada lokasi per produk.
Harga grosir tidak didukung; lokasi produk mengikuti profil bisnis penjual.

### `telegram_logs`

Audit pengiriman notifikasi Telegram. Berisi status `success`/`failed`, message
ID Telegram, dan pesan error yang sudah disanitasi. Token bot dan chat ID tidak
pernah disimpan pada tabel ini.

## 4. Menjalankan Backend

### Prasyarat

- Python 3.10+ (lingkungan saat ini: Python 3.14)
- MySQL Laragon berjalan
- Database `ruralb2b` sudah ada

### Langkah

```powershell
cd C:\laragon\www\ruralb2b\backend

# Sekali saja jika venv belum ada
python -m venv venv

# Aktifkan virtual environment
.\venv\Scripts\Activate.ps1

# Install dependensi
pip install -r requirements.txt

# Siapkan .env dari contoh (jika belum ada)
Copy-Item .env.example .env
```

Buat `JWT_SECRET_KEY` acak (minimal 32 karakter) dan isi di `.env`:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Contoh isi `.env` (jangan gunakan secret contoh ini):

```dotenv
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=ruralb2b
DB_USER=root
DB_PASSWORD=

JWT_SECRET_KEY=<hasil-generate-secret>
JWT_ALGORITHM=HS256
JWT_EXPIRES_MINUTES=60
JWT_ISSUER=ruralb2b-api
JWT_AUDIENCE=ruralb2b-client

CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_DEBUG=true

# Upload dokumen verifikasi (kosong = backend/storage/verification_documents)
VERIFICATION_UPLOAD_DIR=
MAX_VERIFICATION_DOCUMENT_SIZE=5242880
MAX_VERIFICATION_DOCUMENTS=10

# Upload gambar produk (kosong = backend/storage/product_images)
PRODUCT_IMAGE_UPLOAD_DIR=
MAX_PRODUCT_IMAGE_SIZE=5242880
MAX_PRODUCT_IMAGES=5
MAX_CONTENT_LENGTH=10485760

# Telegram Bot API (opsional)
TELEGRAM_BOT_TOKEN=
TELEGRAM_ADMIN_CHAT_ID=
TELEGRAM_API_TIMEOUT=5
```

Catatan:

- `VERIFICATION_UPLOAD_DIR` harus berada **di luar** direktori `static`.
  Aplikasi menolak start jika diarahkan ke folder publik.
- `MAX_VERIFICATION_DOCUMENT_SIZE` adalah batas per file (default 5 MB).
- `MAX_CONTENT_LENGTH` adalah batas total request multipart (default 10 MB).
- Jika `TELEGRAM_BOT_TOKEN`/`TELEGRAM_ADMIN_CHAT_ID` kosong, pengajuan tetap
  berhasil; kegagalan notifikasi dicatat pada `telegram_logs`.

Jalankan server:

```powershell
python app.py
```

Atau dengan Flask CLI:

```powershell
$env:FLASK_APP = "app.py"
flask run --debug --host 127.0.0.1 --port 5000
```

Cek kesehatan:

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/health
```

## 5. Kontrak API

Sebagian besar request dan response menggunakan `application/json`. Pengecualian:
upload dokumen memakai `multipart/form-data`. Dokumentasi rinci profil bisnis
dan verifikasi ada di
[`docs/BUSINESS_VERIFICATION_API.md`](docs/BUSINESS_VERIFICATION_API.md).

Format sukses:

```json
{
  "success": true,
  "message": "…",
  "data": {}
}
```

Format error:

```json
{
  "success": false,
  "message": "…",
  "code": "…",
  "errors": {
    "field": "…"
  }
}
```

### 5.1 `POST /api/auth/register`

Request:

```json
{
  "full_name": "Budi Santoso",
  "email": "budi.umkm@example.com",
  "password": "RuralB2B!2026",
  "phone": "+62 812-3456-7890",
  "business_type": "farmer",
  "business_name": "Tani Makmur",
  "address": "Jl. Raya Desa No. 1",
  "village": "Sukamaju",
  "district": "Cibiru",
  "city": "Bandung",
  "province": "Jawa Barat",
  "postal_code": "40615",
  "description": "Petani sayuran"
}
```

Field wajib: `full_name`, `email`, `password`.
Field opsional: `phone`, `business_type`, `business_name`, alamat, dan deskripsi.

Aturan:

- `full_name`: 2–150 karakter.
- `email`: format valid, maksimal 190 karakter, unik (case-insensitive).
- `password`: 8–128 karakter, mengandung huruf besar, huruf kecil, angka, dan
  karakter khusus.
- `phone`: opsional, 8–15 digit, boleh diawali `+`.
- `business_type`: salah satu dari `farmer`, `supplier`, `collector`, `producer`,
  `shop`, `warung`, `other`. Default `other`.
- `business_name`: maksimal 180 karakter. Jika kosong, memakai `full_name`.
- `role` tidak boleh diisi selain `business_user`; permintaan role admin
  ditolak dengan **403**.
- `account_status` selalu `active`.

Response `201 Created`:

```json
{
  "success": true,
  "message": "Registrasi berhasil. Silakan login untuk mendapatkan token.",
  "data": {
    "user": {
      "id": 1,
      "full_name": "Budi Santoso",
      "email": "budi.umkm@example.com",
      "role": "business_user",
      "account_status": "active",
      "created_at": "2026-11-08T13:00:00",
      "updated_at": "2026-11-08T13:00:00",
      "business_profile": {
        "id": 1,
        "business_name": "Tani Makmur",
        "business_type": "farmer",
        "phone": "+62 812-3456-7890",
        "address": "Jl. Raya Desa No. 1",
        "village": "Sukamaju",
        "district": "Cibiru",
        "city": "Bandung",
        "province": "Jawa Barat",
        "postal_code": "40615",
        "latitude": null,
        "longitude": null,
        "description": "Petani sayuran",
        "created_at": "2026-11-08T13:00:00",
        "updated_at": "2026-11-08T13:00:00"
      }
    }
  }
}
```

Error yang mungkin: `400` JSON tidak valid, `403` role admin, `409` email sudah
terdaftar, `415` bukan JSON, `422` validasi gagal.

### 5.2 `POST /api/auth/login`

Request:

```json
{
  "email": "budi.umkm@example.com",
  "password": "RuralB2B!2026"
}
```

Response `200 OK`:

```json
{
  "success": true,
  "message": "Login berhasil.",
  "data": {
    "access_token": "<jwt>",
    "token_type": "Bearer",
    "expires_in": 3600,
    "expires_at": "2026-11-08T14:00:00+00:00",
    "user": {
      "id": 1,
      "full_name": "Budi Santoso",
      "email": "budi.umkm@example.com",
      "role": "business_user",
      "account_status": "active",
      "business_profile": {}
    }
  }
}
```

Jika email/password salah, response `401` dengan
`code: "invalid_credentials"` dan pesan **“Email atau password salah.”**
(pesan tidak membedakan email tidak ditemukan atau password salah).

Akun `suspended` atau `inactive` ditolak dengan `403`.

### 5.3 `GET /api/auth/me`

Header:

```http
Authorization: Bearer <access_token>
```

Response `200 OK` berisi objek `user` yang sama dengan response login
(tanpa `password_hash`).

Error: `401 token_missing`, `401 token_invalid`, `401 token_expired`,
`401 token_revoked`, `403 account_suspended`, `403 account_inactive`.

### 5.4 `POST /api/auth/logout`

Header:

```http
Authorization: Bearer <access_token>
```

Response `200 OK`:

```json
{
  "success": true,
  "message": "Logout berhasil. Token tidak dapat digunakan lagi."
}
```

Token yang sudah logout akan ditolak pada request berikutnya dengan
`401` dan `code: "token_revoked"`.

### 5.5 Profil bisnis dan verifikasi

Ringkasan alur:

1. `GET /api/business/profile` — lihat profil dan status verifikasi.
2. `PATCH /api/business/profile` — ubah sebagian data; `PUT` untuk mengganti
   seluruh profil (field wajib: `business_name`, `business_type`).
3. `POST /api/business/verifications` — buat pengajuan `pending`.
4. `POST /api/business/verifications/{id}/documents` — upload dokumen
   (multipart, field `document_type` dan `file`).
5. `GET /api/business/verifications` / `/{id}` — lihat status, dokumen, riwayat,
   dan alasan penolakan.
6. Admin memakai `/api/admin/verifications` untuk list/detail/approve/reject/logs.

Aturan penting:

- Satu profil hanya boleh memiliki satu pengajuan `pending`.
- Approve membutuhkan minimal satu dokumen.
- Reject wajib menyertakan `rejection_reason`.
- Dokumen maksimal 5 MB, tipe PDF/JPG/JPEG/PNG/WEBP, maksimal 10 dokumen.
- File disimpan privat dengan nama UUID dan hanya bisa diunduh lewat endpoint
  berautentikasi.
- `is_verified` bernilai `true` jika profil pernah memiliki pengajuan `approved`.

Detail request/response dan daftar kode error ada pada
[`docs/BUSINESS_VERIFICATION_API.md`](docs/BUSINESS_VERIFICATION_API.md).

### 5.6 Katalog produk

Alur singkat:

1. `GET /api/products` - katalog publik (tanpa token).
2. `GET /api/products/{id}` - detail produk publik.
3. `POST /api/products` - buat produk; `business_id` otomatis dari profil.
4. `PUT/PATCH /api/products/{id}` - ubah produk dan status aktif/nonaktif.
5. `POST /api/products/{id}/images` - upload gambar multipart field `file`.
6. `PATCH /api/business/inventory/{product_id}` - set stok absolut atau adjustment.
7. `GET /api/business/products` dan `GET /api/business/inventory` - data penjual.

Aturan penting:

- Katalog publik menyembunyikan produk `inactive`; produk `out_of_stock` tetap
  tampil dengan `is_in_stock=false`.
- Hanya role `business_user` yang boleh mengelola produk.
- Pengguna hanya dapat mengubah produk miliknya sendiri; produk pengguna lain
  menghasilkan `404`.
- Gambar maksimal 5 file per produk, 5 MB per file, tipe JPG/JPEG/PNG/WEBP,
  divalidasi magic bytes dan disimpan privat dengan nama UUID.
- Hapus produk ditolak (`409 product_in_use`) jika masih dipakai keranjang/pesanan.

Dokumentasi lengkap ada di
[`docs/PRODUCT_CATALOG_API.md`](docs/PRODUCT_CATALOG_API.md).

## 6. Pengujian dengan Postman

1. Import file
   `backend/docs/RuralB2B-Auth.postman_collection.json` ke Postman.
2. Pastikan collection variable `base_url` bernilai
   `http://127.0.0.1:5000`.
3. Jalankan **Register** dengan email baru. Ganti `email` pada body agar tidak
   bentrok dengan data yang sudah ada.
4. Jalankan **Login**. Script test pada request ini otomatis menyimpan
   `access_token` ke collection variable.
5. Jalankan **Me** untuk melihat profil.
6. Jalankan **Logout**.
7. Jalankan **Me** lagi — harus menghasilkan `401 token_revoked`.

Untuk profil bisnis dan verifikasi, import
`backend/docs/RuralB2B-Business-Verification.postman_collection.json`.
Urutan pengujian:

1. **Login Business** — menyimpan `access_token`.
2. **Get My Profile** → **Update Profile (PATCH)**.
3. **Submit Verification** — menyimpan `verification_id`.
4. **Upload Document** — pilih file pada form-data field `file`, isi
   `document_type`, lalu request menyimpan `document_id`.
5. **Get My Verifications** → **Get Verification Detail** →
   **Download Document**.
6. **Login Admin** — menyimpan `admin_token`.
7. **Admin List Verifications** → **Admin Verification Detail**.
8. **Admin Approve** atau **Admin Reject**.
9. **Admin Logs** dan **Admin Download Document**.

Untuk katalog produk, import
`backend/docs/RuralB2B-Product-Catalog.postman_collection.json`. Urutan:
**Login Business** -> **Public Categories** -> **Create Product** ->
**Public List/Detail** -> **PUT/PATCH Product** -> **Get/PATCH Inventory** ->
**Upload Product Image** -> **Public/Business Image File** ->
**Delete Product Image** -> **Delete Product**.

Catatan: akun admin tidak dibuat lewat registrasi. Promosikan user melalui SQL
data (bukan perubahan skema):

```sql
UPDATE ruralb2b.users SET role = 'admin' WHERE email = 'admin@example.com';
```

Contoh cURL:

```bash
# Register
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Budi Santoso","email":"budi.umkm@example.com","password":"RuralB2B!2026","business_type":"farmer"}'

# Login
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"budi.umkm@example.com","password":"RuralB2B!2026"}'

# Me
curl http://127.0.0.1:5000/api/auth/me \
  -H "Authorization: Bearer <access_token>"

# Logout
curl -X POST http://127.0.0.1:5000/api/auth/logout \
  -H "Authorization: Bearer <access_token>"

# Profil bisnis
curl http://127.0.0.1:5000/api/business/profile \
  -H "Authorization: Bearer <access_token>"

# Ajukan verifikasi
curl -X POST http://127.0.0.1:5000/api/business/verifications \
  -H "Authorization: Bearer <access_token>"

# Upload dokumen
curl -X POST http://127.0.0.1:5000/api/business/verifications/1/documents \
  -H "Authorization: Bearer <access_token>" \
  -F "document_type=ktp" \
  -F "file=@C:/path/ktp.pdf"

# Admin approve
curl -X POST http://127.0.0.1:5000/api/admin/verifications/1/approve \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d "{\"notes\":\"Dokumen sesuai\"}"
```

## 7. Keamanan

- Password di-hash dengan scrypt melalui Werkzeug; password asli tidak disimpan.
- `password_hash` tidak pernah disertakan pada response API.
- JWT ditandatangani dengan `JWT_SECRET_KEY` dari `.env`; aplikasi menolak
  berjalan jika secret belum diatur.
- Algoritma JWT dibatasi ke HS256/HS384/HS512.
- Token memuat `iss`, `aud`, `iat`, `nbf`, `exp`, dan `jti`; semua diverifikasi.
- Login memakai pesan generik dan dummy hash untuk mengurangi enumerasi email.
- Kredensial database dan secret tidak ditulis di kode.
- `.env` diabaikan oleh `.gitignore`; `.env.example` tidak berisi secret asli.
- CORS dibatasi lewat `CORS_ORIGINS` (default development: localhost:3000 dan localhost:5173).
- Input divalidasi sebelum menyentuh database.
- Registrasi tidak mengizinkan role `admin`.
- Endpoint pengguna memakai `token_required`; endpoint admin memakai
  `admin_required` yang mengecek role dari database.
- Query pengguna selalu difilter dengan `business_profile.user_id`, sehingga
  pengguna tidak bisa membaca/mengubah data pengguna lain.
- File verifikasi disimpan di luar `static`, memakai nama UUID, dan hanya
  dilayani lewat endpoint download berautentikasi.
- Gambar produk disimpan di luar `static`; ekstensi, magic bytes, ukuran, jumlah,
  dan total request divalidasi. Path internal tidak diekspos.
- URL gambar publik hanya melayani produk non-inactive; pemilik memakai endpoint
  gambar business untuk preview produk inactive.
- Ekstensi, magic bytes, ukuran per file, jumlah dokumen, dan total request
  divalidasi.
- Path download di-resolve dan dicek agar tidak keluar dari direktori storage.
- `file_path` internal tidak diekspos pada response.
- Token dan chat ID Telegram tidak pernah dikembalikan API atau ditulis ke pesan
  error.
- Folder `storage/` dan `.env` masuk `.gitignore`.

### Catatan logout

Karena skema database tidak diubah pada tahap ini, blocklist token disimpan di
memori proses. Konsekuensinya:

- Token yang di-logout langsung tidak valid pada proses server yang sama.
- Blocklist hilang saat server restart.
- Pada deployment multi-worker, blocklist tidak dibagi antar worker.

Untuk produksi, ganti `utils/token_blocklist.py` dengan Redis atau tabel
blocklist khusus. Perubahan skema semacam itu memerlukan persetujuan terpisah.

## 8. Hasil Pengujian

Pengujian dilakukan dengan Flask test client terhadap database `ruralb2b`:

| Skenario | Hasil |
|---|---|
| Registrasi valid | `201`, user + business profile dibuat |
| Registrasi email duplikat | `409 email_already_registered` |
| Registrasi role admin | `403 forbidden_role` |
| Registrasi password lemah | `422` dengan detail aturan password |
| Login password salah | `401 invalid_credentials` |
| Login valid | `200`, JWT diterbitkan |
| `GET /me` dengan token | `200`, profil lengkap tanpa hash |
| `GET /me` tanpa token | `401 token_missing` |
| Logout | `200`, token masuk blocklist |
| `GET /me` setelah logout | `401 token_revoked` |
| Password di database | scrypt, bukan plaintext |
| Data uji | dihapus setelah pengujian; tabel `users` kembali kosong |

Pengujian tahap 4 juga dilakukan dengan data sementara yang dihapus kembali:

| Skenario | Hasil |
|---|---|
| `GET/PATCH/PUT` profil dan validasi input | `200` / `422` sesuai aturan |
| Pengajuan verifikasi + log awal | `201`, status `pending`, log `NULL -> pending` |
| Pengajuan pending ganda | `409 verification_already_pending` |
| Upload PDF/PNG valid | `201`, file tersimpan privat |
| Ekstensi salah / magic bytes salah / file > 5 MB | `422` / `422` / `413` |
| Akses pengajuan/dokumen milik user lain | `404` |
| Non-admin mengakses endpoint admin | `403 admin_required` |
| Admin list/detail/approve/reject/logs/download | berhasil |
| Approve tanpa dokumen | `422 documents_required` |
| Reject tanpa alasan | `422` |
| Alasan penolakan terlihat pemilik | berhasil |
| Approve ganda | `409 verification_not_pending` |
| Telegram sukses/gagal (mock) | tercatat di `telegram_logs`, token tidak bocor |
| Data dan file uji | dihapus; tabel terkait kembali kosong |

Pengujian tahap 5 (162 skenario) juga dilakukan dengan data sementara yang
dihapus kembali:

| Skenario | Hasil |
|---|---|
| CRUD produk, PUT/PATCH, aktivasi/nonaktivasi | berhasil |
| Katalog publik, search, filter kategori/harga/lokasi/stok, sorting, pagination | berhasil |
| Validasi harga/stok/status/kategori/field asing | `422` sesuai aturan |
| Akses produk/inventori/gambar pengguna lain | `404` |
| Admin mengelola produk | `403 business_user_required` |
| Upload gambar valid, primary image, limit 5, validasi tipe/ukuran | berhasil / `413` / `422` |
| Hapus gambar utama dan promosi primary | berhasil |
| Hapus produk dengan gambar dan inventori | berhasil, file dibersihkan |
| Hapus produk yang masih di keranjang | `409 product_in_use` |
| Regresi profil, verifikasi, admin, health | tetap berfungsi |
| Data dan file uji | dihapus; tabel terkait kosong |

## 9. Troubleshooting

| Gejala | Penyebab umum | Solusi |
|---|---|---|
| `JWT_SECRET_KEY belum diatur` | `.env` belum diisi | Generate secret dan isi `.env` |
| `Access denied for user` | Kredensial DB salah | Sesuaikan `DB_USER`/`DB_PASSWORD` |
| `Can't connect to MySQL` | Laragon/MySQL belum berjalan | Start MySQL di Laragon |
| `401 token_expired` | Token melewati `exp` | Login ulang |
| `401 token_revoked` | Token sudah logout | Login ulang |
| `415 unsupported_media_type` | Body bukan JSON | Set `Content-Type: application/json` |
| `503 database disconnected` | Koneksi DB gagal | Cek service MySQL dan konfigurasi `.env` |
| `413 request_too_large` | Request multipart melebihi batas | Perkecil file atau naikkan `MAX_CONTENT_LENGTH` |
| `413 file_too_large` | File melebihi batas per file | Perkecil file atau ubah `MAX_VERIFICATION_DOCUMENT_SIZE` |
| `422 invalid_file_type` | Ekstensi bukan PDF/JPG/JPEG/PNG/WEBP | Gunakan tipe yang didukung |
| `422 invalid_file_content` | Isi file tidak cocok dengan ekstensi | Pastikan file asli, bukan hasil rename |
| `422 documents_required` | Approve sebelum ada dokumen | Upload dokumen lalu approve |
| `403 admin_required` | Token bukan admin | Promosikan user dan login ulang |
| Notifikasi Telegram gagal | Token/chat ID kosong atau API error | Cek `.env` dan `telegram_logs`; pengajuan tetap tersimpan |
| `VERIFICATION_UPLOAD_DIR ... static` | Folder upload diarahkan ke public/static | Gunakan folder privat seperti `storage/verification_documents` |
| `413 image_too_large` | Gambar melebihi `MAX_PRODUCT_IMAGE_SIZE` | Perkecil gambar atau ubah batas |
| `422 invalid_image_type` / `invalid_image_content` | Tipe/isi gambar tidak valid | Gunakan JPG/JPEG/PNG/WEBP asli |
| `409 image_limit_reached` | Gambar sudah 5 | Hapus gambar lama terlebih dahulu |
| `409 product_in_use` | Produk masih di keranjang/pesanan | Nonaktifkan produk atau bersihkan referensi |
| `422 stock_below_reserved` | Stok di bawah reservasi | Naikkan stok atau selesaikan reservasi |
| `403 business_user_required` | Token bukan business user | Gunakan akun bisnis |

## 10. Catatan Pengembangan Berikutnya

- Backend Tahap 1–6 sudah selesai dan diuji (authentikasi, profil bisnis, verifikasi, katalog produk, keranjang, checkout, pesanan, pembayaran, dan bukti pembayaran).
- Frontend React belum dibuat.
- Untuk produksi: matikan `FLASK_DEBUG`, gunakan HTTPS, batasi CORS ke domain frontend, gunakan blocklist token berbasis Redis/database, dan pertimbangkan penyimpanan file di object storage privat.
- Notifikasi Telegram saat ini dikirim secara sinkron dengan timeout pendek. Untuk trafik tinggi, pertimbangkan queue/worker.
- Perubahan skema database memerlukan persetujuan terpisah; saat ini tidak ada tabel yang ditambah, diubah, atau dihapus pada Tahap 6 (21 tabel tetap sama).

## 11. Dokumentasi Tahap 4

- [`docs/BUSINESS_VERIFICATION_API.md`](docs/BUSINESS_VERIFICATION_API.md) —
  kontrak lengkap, aturan validasi, keamanan file, Telegram, kode error, dan
  cara pengujian.
- [`docs/RuralB2B-Business-Verification.postman_collection.json`](docs/RuralB2B-Business-Verification.postman_collection.json)
  — koleksi Postman siap import.
- [`docs/RuralB2B-Auth.postman_collection.json`](docs/RuralB2B-Auth.postman_collection.json)
  — koleksi Postman autentikasi.

## 12. Dokumentasi Tahap 5

- [`docs/PRODUCT_CATALOG_API.md`](docs/PRODUCT_CATALOG_API.md) - kontrak katalog produk, inventori, gambar, filter, keamanan, error, dan pengujian.
- [`docs/RuralB2B-Product-Catalog.postman_collection.json`](docs/RuralB2B-Product-Catalog.postman_collection.json) - koleksi Postman siap import.

## 13. Dokumentasi Tahap 6

- [`docs/CART_ORDER_API.md`](docs/CART_ORDER_API.md) - kontrak lengkap API keranjang, checkout, pesanan pembeli dan penjual, pembayaran, dan bukti pembayaran, termasuk daftar endpoint, contoh request/response, kode error, dan aturan bisnis.
- [`docs/RuralB2B-Cart-Order.postman_collection.json`](docs/RuralB2B-Cart-Order.postman_collection.json) - koleksi Postman siap import untuk Tahap 6.

Pengujian Tahap 6 dilakukan dengan Flask test client terhadap database `ruralb2b`:

| Skenario | Hasil |
|---|---|
| Validasi nominal pembayaran (lebih rendah/tinggi) | `409 payment_amount_mismatch` |
| Nominal pembayaran benar | `200 paid` |
| Self-purchase (cart, checkout, konfirmasi) | `409 self_purchase_not_allowed` |
| Submit pembayaran pada status tidak diizinkan | `409 payment_order_status_not_allowed` |
| Konfirmasi pembayaran pada `completed` | `409 order_completed` |
| Konfirmasi pembayaran pada `cancelled` | `409 order_cancelled` |
| `processing` tanpa pembayaran `paid` | `409 payment_not_paid` |
| Pembatalan pesanan dan pemulihan stok | `200`, stok kembali |
| Pembatalan ganda | `409`, stok tidak dikembalikan dua kali |
| Bukti pembayaran tetap ada setelah pembatalan | File dan path tetap utuh |
| Pembayaran `paid` tidak berubah menjadi `refunded` | Tetap `paid` |
| Fungsi tes fungsional Tahap 6 | `STAGE6_FUNCTIONAL_OK` |
