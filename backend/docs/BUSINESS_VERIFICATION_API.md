# RuralB2B — Profil Bisnis dan Verifikasi UMKM

Dokumen ini melengkapi `README.md` untuk tahap 4. Semua endpoint memakai JWT
Bearer token dari sistem autentikasi.

## 1. Ringkasan Fitur

- Pengguna bisnis dapat melihat dan memperbarui profil usahanya.
- Pengguna dapat mengajukan verifikasi dan mengunggah dokumen pendukung.
- Pengguna dapat melihat status, riwayat, dan alasan penolakan.
- Admin dapat melihat seluruh pengajuan, dokumen, menyetujui, menolak, dan
  melihat riwayat.
- Pengajuan baru mengirim notifikasi Telegram ke admin. Kegagalan Telegram
  tidak membatalkan pengajuan.

Tidak ada tabel yang dibuat, diubah, atau dihapus. Tabel yang digunakan:

| Tabel | Fungsi |
|---|---|
| `business_profiles` | Profil bisnis milik user |
| `verification_requests` | Pengajuan verifikasi |
| `verification_documents` | Dokumen pendukung |
| `verification_logs` | Riwayat perubahan status |
| `telegram_logs` | Audit pengiriman notifikasi Telegram |

Status verifikasi: `pending`, `approved`, `rejected`.

## 2. Endpoint

### Pengguna bisnis

| Method | Endpoint | Keterangan |
|---|---|---|
| `GET` | `/api/business/profile` | Profil sendiri + ringkasan verifikasi |
| `PUT` | `/api/business/profile` | Ganti profil (field wajib: nama & jenis bisnis) |
| `PATCH` | `/api/business/profile` | Ubah sebagian field |
| `GET` | `/api/business/verifications` | Daftar pengajuan sendiri |
| `POST` | `/api/business/verifications` | Ajukan verifikasi baru |
| `GET` | `/api/business/verifications/{id}` | Detail pengajuan + dokumen + riwayat |
| `POST` | `/api/business/verifications/{id}/documents` | Unggah dokumen (multipart) |
| `GET` | `/api/business/verifications/{id}/documents/{doc_id}/download` | Unduh dokumen sendiri |

### Admin

| Method | Endpoint | Keterangan |
|---|---|---|
| `GET` | `/api/admin/verifications` | Semua pengajuan, filter `?status=pending` |
| `GET` | `/api/admin/verifications/{id}` | Detail + dokumen + riwayat + log Telegram |
| `POST` | `/api/admin/verifications/{id}/approve` | Setujui pengajuan |
| `POST` | `/api/admin/verifications/{id}/reject` | Tolak dengan alasan |
| `GET` | `/api/admin/verifications/{id}/logs` | Riwayat perubahan status |
| `GET` | `/api/admin/verifications/{id}/documents/{doc_id}/download` | Unduh dokumen |

Semua endpoint pengguna membutuhkan header:

```http
Authorization: Bearer <access_token>
```

Endpoint admin juga membutuhkan role `admin` pada tabel `users`.

## 3. Profil Bisnis

### `GET /api/business/profile`

Response `200`:

```json
{
  "success": true,
  "data": {
    "profile": {
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
      "latitude": -6.914744,
      "longitude": 107.60981,
      "description": "Petani sayuran",
      "created_at": "2026-11-08T13:00:00",
      "updated_at": "2026-11-08T13:00:00"
    },
    "verification": {
      "status": "pending",
      "is_verified": false,
      "latest_request_id": 3,
      "pending_request_id": 3,
      "rejection_reason": null
    }
  }
}
```

`is_verified` bernilai `true` jika profil pernah memiliki pengajuan berstatus
`approved`. Status terbaru tetap ditampilkan pada `status`.

### `PATCH /api/business/profile`

Hanya field yang dikirim yang diubah. Contoh:

```json
{
  "phone": "+62 812-3456-7890",
  "address": "Jl. Raya Desa No. 1",
  "village": "Sukamaju",
  "district": "Cibiru",
  "city": "Bandung",
  "province": "Jawa Barat",
  "postal_code": "40615",
  "latitude": -6.914744,
  "longitude": 107.60981,
  "description": "Petani sayuran organik"
}
```

### `PUT /api/business/profile`

Mengganti profil. `business_name` dan `business_type` wajib. Field opsional yang
tidak dikirim akan dikosongkan (`null`). Contoh:

```json
{
  "business_name": "Tani Makmur Baru",
  "business_type": "supplier",
  "phone": "+62 812-3456-7890",
  "address": "Jl. Baru No. 2",
  "village": "Sukamaju",
  "district": "Cibiru",
  "city": "Bandung",
  "province": "Jawa Barat",
  "postal_code": "40615",
  "latitude": -6.914744,
  "longitude": 107.60981,
  "description": "Supplier sayuran"
}
```

Aturan validasi:

- `business_name`: 2–180 karakter, wajib pada `PUT`.
- `business_type`: `farmer`, `supplier`, `collector`, `producer`, `shop`,
  `warung`, `other`. Wajib pada `PUT`.
- `phone`: opsional, 8–15 digit, boleh diawali `+`.
- `address`, `description`: maksimal 2.000 karakter.
- `village`, `district`, `city`, `province`: maksimal 120 karakter.
- `postal_code`: 3–15 karakter huruf/angka/tanda hubung.
- `latitude`: -90 s/d 90. `longitude`: -180 s/d 180.
- Field yang tidak dikenal ditolak dengan `422`.
- `PATCH` tanpa field yang dikenal ditolak dengan `422`.

## 4. Alur Verifikasi Pengguna

### 4.1 Ajukan verifikasi

```http
POST /api/business/verifications
Authorization: Bearer <access_token>
```

Tidak membutuhkan body JSON. Response `201`:

```json
{
  "success": true,
  "message": "Pengajuan verifikasi berhasil dibuat.",
  "data": {
    "verification": {
      "id": 3,
      "business_profile_id": 1,
      "status": "pending",
      "submitted_at": "2026-11-08T13:30:00",
      "reviewed_by": null,
      "reviewed_at": null,
      "rejection_reason": null,
      "business_profile": {},
      "user": {}
    },
    "documents": [],
    "history": [
      {
        "id": 1,
        "verification_id": 3,
        "admin_id": null,
        "old_status": null,
        "new_status": "pending",
        "notes": "Pengajuan verifikasi dibuat.",
        "created_at": "2026-11-08T13:30:00"
      }
    ],
    "notification": {
      "sent": false,
      "reason": "not_configured"
    }
  }
}
```

Aturan:

- Hanya boleh ada **satu pengajuan pending** per profil.
- Pengajuan ganda menghasilkan `409 verification_already_pending` beserta
  `details.verification_id`.
- Setelah pengajuan `rejected` atau `approved`, pengguna dapat mengajukan
  verifikasi baru.
- Pembuatan pengajuan selalu menulis log awal `NULL -> pending`.
- Notifikasi Telegram dikirim setelah pengajuan tersimpan. Jika gagal,
  pengajuan tetap ada.

### 4.2 Unggah dokumen

```http
POST /api/business/verifications/{id}/documents
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

Form field:

| Field | Nilai |
|---|---|
| `document_type` | `ktp`, `kk`, `npwp`, `nib`, `siup`, `business_photo`, `other` |
| `file` | File PDF/JPG/JPEG/PNG/WEBP |

Aturan file:

- Maksimal **5 MB** per file (dapat diubah lewat `.env`).
- Maksimal **10 dokumen** per pengajuan.
- Ekstensi dan isi file harus cocok (dicek dengan magic bytes).
- Nama file asli tidak dipakai. File disimpan dengan nama UUID.
- File disimpan di `backend/storage/verification_documents/`, **di luar**
  direktori `static`.
- Dokumen hanya bisa diunggah saat pengajuan `pending`.
- Satu request mengunggah satu file. Ulangi request untuk dokumen lain.

Response `201`:

```json
{
  "success": true,
  "message": "Dokumen berhasil diunggah.",
  "data": {
    "document": {
      "id": 4,
      "verification_id": 3,
      "document_type": "ktp",
      "file_name": "ktp_4.pdf",
      "uploaded_at": "2026-11-08T13:31:00",
      "download_url": "/api/business/verifications/3/documents/4/download"
    }
  }
}
```

`file_path` internal tidak pernah diekspos.

### 4.3 Lihat status dan riwayat

```http
GET /api/business/verifications?page=1&per_page=20
GET /api/business/verifications/{id}
```

Daftar berisi ringkasan setiap pengajuan. Detail berisi `verification`,
`documents`, dan `history`. Alasan penolakan tersedia pada
`verification.rejection_reason` jika status `rejected`.

### 4.4 Unduh dokumen sendiri

```http
GET /api/business/verifications/{id}/documents/{doc_id}/download
```

Hanya pemilik profil yang boleh mengunduh. Response berupa file attachment.

## 5. Alur Admin

### 5.1 Daftar pengajuan

```http
GET /api/admin/verifications?status=pending&page=1&per_page=20
```

Filter `status` opsional: `pending`, `approved`, `rejected`. Item berisi data
verifikasi, profil bisnis, pemilik, dan `documents_count`.

### 5.2 Detail pengajuan

```http
GET /api/admin/verifications/{id}
```

Response berisi:

- `verification` beserta profil, pemilik, dan reviewer,
- `documents` beserta `download_url` admin,
- `history` dengan identitas admin,
- `telegram_notifications` (status kirim, message ID, error aman).

### 5.3 Setujui

```http
POST /api/admin/verifications/{id}/approve
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "notes": "Dokumen sesuai."
}
```

Syarat:

- Status masih `pending`.
- Minimal ada satu dokumen. Jika belum ada: `422 documents_required`.
- Admin tercatat pada `reviewed_by`, `reviewed_at`, dan log.

### 5.4 Tolak

```http
POST /api/admin/verifications/{id}/reject
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "rejection_reason": "Dokumen KTP tidak terbaca.",
  "notes": "Silakan unggah ulang."
}
```

`rejection_reason` wajib, maksimal 2.000 karakter. Alasan terlihat oleh pemilik
pengajuan.

### 5.5 Riwayat

```http
GET /api/admin/verifications/{id}/logs
```

Log berurutan dari awal. Setiap log memuat status lama/baru, catatan, waktu,
dan admin (jika ada).

### 5.6 Unduh dokumen

```http
GET /api/admin/verifications/{id}/documents/{doc_id}/download
```

Hanya admin. File dikirim sebagai attachment.

## 6. Menjadikan User sebagai Admin

Tidak ada endpoint registrasi admin. Promosikan user yang sudah terdaftar
melalui SQL berikut (data, bukan perubahan skema):

```sql
UPDATE ruralb2b.users
SET role = 'admin'
WHERE email = 'admin@example.com';
```

Setelah itu login ulang. Token lama tetap akan dicek role-nya ke database,
tetapi login ulang disarankan.

## 7. Konfigurasi `.env`

```dotenv
# Penyimpanan dokumen (kosong = backend/storage/verification_documents)
VERIFICATION_UPLOAD_DIR=
MAX_VERIFICATION_DOCUMENT_SIZE=5242880
MAX_VERIFICATION_DOCUMENTS=10
MAX_CONTENT_LENGTH=10485760

# Telegram Bot API
TELEGRAM_BOT_TOKEN=
TELEGRAM_ADMIN_CHAT_ID=
TELEGRAM_API_TIMEOUT=5
```

Catatan:

- `TELEGRAM_BOT_TOKEN` dan `TELEGRAM_ADMIN_CHAT_ID` tidak pernah dikirim ke
  response API.
- Jika keduanya kosong, pengajuan tetap berhasil dan `telegram_logs` mencatat
  kegagalan konfigurasi.
- Jika Telegram gagal (network/API error), pengajuan tetap tersimpan.
- Jangan commit `.env`.

## 8. Pengujian dengan Postman

Import:

```text
backend/docs/RuralB2B-Business-Verification.postman_collection.json
```

Urutan:

1. **Login Business** → menyimpan `access_token`.
2. **Get My Profile** → cek profil.
3. **Update Profile (PATCH)** → ubah sebagian data.
4. **Submit Verification** → menyimpan `verification_id`.
5. **Upload Document** → pilih file PDF/gambar, menyimpan `document_id`.
6. **Get My Verifications** dan **Get Verification Detail**.
7. **Download Document**.
8. **Login Admin** → menyimpan `admin_token`.
9. **Admin List Verifications**, **Admin Detail**.
10. **Admin Approve** atau **Admin Reject**.
11. **Admin Logs** dan **Admin Download Document**.

Untuk upload di Postman: buka tab **Body → form-data**, pilih file pada field
`file`, dan isi `document_type`.

## 9. Contoh cURL

```bash
# Profil
curl http://127.0.0.1:5000/api/business/profile \
  -H "Authorization: Bearer <access_token>"

# Ajukan verifikasi
curl -X POST http://127.0.0.1:5000/api/business/verifications \
  -H "Authorization: Bearer <access_token>"

# Unggah dokumen
curl -X POST http://127.0.0.1:5000/api/business/verifications/1/documents \
  -H "Authorization: Bearer <access_token>" \
  -F "document_type=ktp" \
  -F "file=@C:/path/ktp.pdf"

# Admin approve
curl -X POST http://127.0.0.1:5000/api/admin/verifications/1/approve \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d "{\"notes\":\"Dokumen sesuai\"}"

# Admin reject
curl -X POST http://127.0.0.1:5000/api/admin/verifications/1/reject \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d "{\"rejection_reason\":\"Dokumen tidak terbaca\"}"
```

## 10. Kode Error Utama

| HTTP | Code | Arti |
|---|---|---|
| `403` | `admin_required` | Endpoint hanya untuk admin |
| `404` | `verification_not_found` | Pengajuan tidak ada/bukan milik user |
| `404` | `document_not_found` | Dokumen tidak ada/bukan milik user |
| `409` | `verification_already_pending` | Sudah ada pengajuan pending |
| `409` | `verification_not_pending` | Pengajuan sudah diproses |
| `409` | `document_limit_reached` | Batas jumlah dokumen |
| `413` | `file_too_large` | File melebihi batas per file |
| `413` | `request_too_large` | Request multipart melebihi `MAX_CONTENT_LENGTH` |
| `422` | `invalid_file_type` | Ekstensi tidak diizinkan |
| `422` | `invalid_file_content` | Isi file tidak cocok dengan ekstensi |
| `422` | `documents_required` | Approve tanpa dokumen |
| `422` | `rejection_reason_required` | Reject tanpa alasan |
| `422` | `file_required` | Field file tidak ada |
| `500` | `storage_error` | Gagal menulis file |
| `500` | `document_save_failed` | Gagal menyimpan metadata dokumen |

## 11. Catatan Keamanan

- Semua endpoint profil/verifikasi pengguna memakai `token_required`.
- Semua endpoint admin memakai `admin_required` yang mengecek role dari database.
- Query pengguna selalu difilter dengan `business_profile.user_id`.
- Query admin tidak dibatasi user, tetapi hanya bisa diakses admin.
- File disimpan di luar public/static dan tidak punya URL publik.
- Nama file dibuat UUID; nama asli tidak dipakai.
- Path download di-resolve dan dicek agar tetap berada di direktori penyimpanan.
- Ekstensi, magic bytes, jumlah dokumen, dan ukuran file divalidasi.
- Token dan chat ID Telegram tidak pernah masuk response API atau pesan error.
- `file_path` internal tidak diekspos.
- `.env` dan folder `storage/` masuk `.gitignore`.

## 12. Hasil Pengujian Tahap 4

Seluruh pengujian dijalankan dengan Flask test client dan data sementara yang
dihapus kembali:

- CRUD profil, validasi telepon/koordinat/field/partial update: lulus.
- Pengajuan verifikasi + log awal: lulus.
- Pencegahan pengajuan pending ganda: lulus.
- Upload PDF/PNG valid: lulus.
- Penolakan ekstensi salah, magic bytes salah, file > 5 MB: lulus.
- Isolasi akses antar pengguna: lulus.
- Admin list/detail/approve/reject/logs/download: lulus.
- Approve tanpa dokumen: `422 documents_required`.
- Reject tanpa alasan: `422`.
- Alasan penolakan terlihat oleh pemilik.
- Pengajuan ulang setelah rejected: lulus.
- Approve ganda: `409`.
- Telegram sukses/gagal dengan mock: lulus; token tidak muncul di response/log.
- Data uji dan file uji dihapus; seluruh tabel terkait kembali kosong.
