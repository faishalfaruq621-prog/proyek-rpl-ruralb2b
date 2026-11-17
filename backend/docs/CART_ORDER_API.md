# RuralB2B Stage 6 - Dokumentasi API Cart, Order, Checkout, dan Payment

Dokumen ini mencakup fitur Tahap 6: keranjang belanja, checkout, pesanan pembeli dan penjual, serta pembayaran dengan bukti pembayaran. Semua endpoint tercantum sesuai implementasi aktual di `backend/routes/cart.py`, `backend/routes/orders.py`, `backend/services/cart_service.py`, `backend/services/order_service.py`, `backend/services/payment_service.py`, `backend/services/payment_proof_storage_service.py`, dan `backend/utils/order_validators.py`.

## 1. Ringkasan Endpoint

| Method | Endpoint | Hak Akses | Keterangan |
|---|---|---|---|
| `GET` | `/api/cart` | Business User | Lihat keranjang belanja aktif sendiri |
| `POST` | `/api/cart/items` | Business User | Tambah produk ke keranjang |
| `PATCH` | `/api/cart/items/{item_id}` | Business User | Ubah jumlah item keranjang |
| `DELETE` | `/api/cart/items/{item_id}` | Business User | Hapus item keranjang |
| `POST` | `/api/orders/checkout` | Business User | Checkout keranjang, pecah per penjual |
| `GET` | `/api/orders` | Business User | Daftar pesanan sebagai pembeli |
| `GET` | `/api/orders/{order_id}` | Business User | Detail pesanan sebagai pembeli |
| `POST` | `/api/orders/{order_id}/cancel` | Business User | Batalkan pesanan sendiri |
| `GET` | `/api/orders/{order_id}/payment` | Business User | Lihat info pembayaran pesanan |
| `PATCH` | `/api/orders/{order_id}/payment` | Business User | Kirim informasi pembayaran |
| `POST` | `/api/orders/{order_id}/payment/proof` | Business User | Upload bukti pembayaran |
| `GET` | `/api/orders/{order_id}/payment/proof/download` | Business User | Unduh bukti pembayaran sendiri |
| `GET` | `/api/seller/orders` | Business User | Daftar pesanan sebagai penjual |
| `GET` | `/api/seller/orders/{order_id}` | Business User | Detail pesanan sebagai penjual |
| `PATCH` | `/api/seller/orders/{order_id}/status` | Business User | Ubah status pesanan (penjual) |
| `POST` | `/api/seller/orders/{order_id}/payment/confirm` | Business User | Konfirmasi pembayaran (penjual) |
| `GET` | `/api/seller/orders/{order_id}/payment/proof/download` | Business User | Unduh bukti pembayaran (penjual) |

Semua endpoint di atas membutuhkan header `Authorization: Bearer <access_token>` kecuali disebutkan lain. Role yang diwajibkan adalah `business_user` melalui middleware `business_user_required` (dilengkapi `token_required`).

## 2. Format Response Umum

Sukses:

```json
{
  "success": true,
  "message": "...",
  "data": {}
}
```

Error:

```json
{
  "success": false,
  "message": "...",
  "code": "...",
  "details": { ... },
  "errors": { ... }
}
```

HTTP status yang digunakan: `200`, `201`, `400`, `401`, `403`, `404`, `405`, `409`, `413`, `415`, `422`, `500`, `503`.

## 3. Aturan Bisnis Penting

- Satu order hanya berisi produk dari **satu penjual**. Checkout keranjang multi-penjual dipecah menjadi beberapa order.
- Harga dan total pesanan dihitung oleh **backend** berdasarkan harga produk dan kuantitas yang disetujui saat checkout.
- Stok divalidasi secara **atomik saat checkout** (revalidasi stok, minimum order, dan status produk tidak aktif).
- Pembayaran dilakukan **di luar platform** (misalnya transfer bank); tidak ada payment gateway dalam aplikasi.
- Pembeli **tidak dapat mengonfirmasi pembayarannya sendiri**; hanya penjual order yang dapat mengonfirmasi.
- Penjual tidak dapat mengonfirmasi pembayaran untuk pesanan yang ia beli sendiri (self-purchase).
- Proses fulfillment ke status `processing` (dan transitif ke `shipped`/`completed`) membutuhkan pembayaran dengan status `paid`.
- Pengguna tidak dapat membeli produk dari profil bisnisnya sendiri (self-purchase ditolak pada tambah/update keranjang dan checkout).
- Bukti pembayaran disimpan secara **privat** (di luar direktori publik/static), nama file UUID, divalidasi ekstensi dan magic bytes (PDF/JPG/JPEG/PNG), maksimal 5 MB, dan hanya dapat diunduh lewat endpoint download yang dikecualikan kepemilikan.

## 4. Detail Endpoint

### 4.1 Cart

#### 4.1.1 GET /api/cart

**Fungsi:** Mengembalikan keranjang belanja aktif pembeli yang login, lengkap dengan item dan detail produk.

**Hak akses:** Pembeli (role `business_user`).

**Authentication:** `Authorization: Bearer <access_token>` (wajib).

**Parameter:** Tidak ada.

**Contoh Request:**

```http
GET /api/cart HTTP/1.1
Authorization: Bearer <access_token>
```

**Contoh Response Sukses (200 OK):**

```json
{
  "success": true,
  "data": {
    "cart": {
      "id": 1,
      "buyer_id": 10,
      "status": "active",
      "items": [
        {
          "id": 5,
          "cart_id": 1,
          "product_id": 23,
          "quantity": 2,
          "created_at": "2026-11-09T10:00:00"
        }
      ]
    }
  }
}
```

**Kemungkinan Error:** `401` (token tidak valid/kadaluarsa/dicabut), `403` (bukan business user).

---

#### 4.1.2 POST /api/cart/items

**Fungsi:** Menambahkan produk ke keranjang aktif pembeli. Jika produk sudah ada dalam keranjang, kuantitas akan ditambahkan.

**Hak akses:** Pembeli (role `business_user`).

**Authentication:** `Authorization: Bearer <access_token>` (wajib).

**Body Request (JSON):**

| Field | Tipe | Wajib | Keterangan |
|---|---|---|---|
| `product_id` | Integer | Ya | ID produk yang ditambahkan |
| `quantity` | Integer | Tidak (default 1) | Jumlah produk, minimal 1 |

**Contoh Request:**

```http
POST /api/cart/items HTTP/1.1
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "product_id": 23,
  "quantity": 2
}
```

**Contoh Response Sukses (201 Created):**

```json
{
  "success": true,
  "message": "Produk berhasil ditambahkan ke keranjang.",
  "data": {
    "cart": {
      "id": 1,
      "buyer_id": 10,
      "status": "active",
      "items": [
        {
          "id": 5,
          "cart_id": 1,
          "product_id": 23,
          "quantity": 2,
          "created_at": "2026-11-09T10:00:00"
        }
      ]
    }
  }
}
```

**Kemungkinan Error:**

| Status | Kode | Keterangan |
|---|---|---|
| `400` | — | JSON tidak valid |
| `401` | — | Token tidak valid/kadaluarsa/dicabut |
| `403` | — | Bukan business user |
| `404` | `product_not_found` | Produk tidak ditemukan |
| `409` | `self_purchase_not_allowed` | Produk milik profil bisnis pembeli sendiri |
| `409` | `product_unavailable` | Produk tidak aktif atau tidak tersedia |
| `409` | `minimum_order_not_met` | Kuantitas kurang dari minimum order |
| `409` | `insufficient_stock` | Stok tidak mencukupi |
| `415` | — | Bukan JSON |
| `422` | — | Validasi payload gagal |

---

#### 4.1.3 PATCH /api/cart/items/{item_id}

**Fungsi:** Mengubah jumlah item keranjang tertentu yang milik pembeli.

**Hak akses:** Pembeli (role `business_user`).

**Authentication:** `Authorization: Bearer <access_token>` (wajib).

**Parameter URL:**

| Parameter | Tipe | Keterangan |
|---|---|---|
| `item_id` | Integer | ID item keranjang |

**Body Request (JSON):**

| Field | Tipe | Wajib | Keterangan |
|---|---|---|---|
| `quantity` | Integer | Ya | Jumlah baru, minimal 1 |

**Contoh Request:**

```http
PATCH /api/cart/items/5 HTTP/1.1
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "quantity": 3
}
```

**Contoh Response Sukses (200 OK):**

```json
{
  "success": true,
  "message": "Jumlah produk di keranjang berhasil diperbarui.",
  "data": {
    "cart": {
      "id": 1,
      "status": "active",
      "items": [
        {
          "id": 5,
          "cart_id": 1,
          "product_id": 23,
          "quantity": 3,
          "created_at": "2026-11-09T10:00:00"
        }
      ]
    }
  }
}
```

**Kemungkinan Error:** Sama dengan `POST /api/cart/items`, tambahan `404 cart_item_not_found` jika item tidak ditemukan atau bukan milik keranjang pembeli.

---

#### 4.1.4 DELETE /api/cart/items/{item_id}

**Fungsi:** Menghapus item keranjang tertentu yang milik pembeli.

**Hak akses:** Pembeli (role `business_user`).

**Authentication:** `Authorization: Bearer <access_token>` (wajib).

**Parameter URL:**

| Parameter | Tipe | Keterangan |
|---|---|---|
| `item_id` | Integer | ID item keranjang |

**Contoh Request:**

```http
DELETE /api/cart/items/5 HTTP/1.1
Authorization: Bearer <access_token>
```

**Contoh Response Sukses (200 OK):**

```json
{
  "success": true,
  "message": "Produk berhasil dihapus dari keranjang.",
  "data": {
    "cart": {
      "id": 1,
      "status": "active",
      "items": []
    }
  }
}
```

**Kemungkinan Error:** `404 cart_item_not_found`, `401`, `403`.

---

### 4.2 Checkout

#### 4.2.1 POST /api/orders/checkout

**Fungsi:** Melakukan checkout keranjang aktif. Setiap group produk per penjual dibuat menjadi satu order terpisah. Stok divalidasi secara atomik (minimum order dan ketersediaan stok) sebelum order dibuat. Keranjang ditandai `converted` setelah checkout berhasil.

**Hak akses:** Pembeli (role `business_user`).

**Authentication:** `Authorization: Bearer <access_token>` (wajib).

**Body Request (JSON):**

| Field | Tipe | Wajib | Keterangan |
|---|---|---|---|
| `shipping_address` | String | Tidak | Alamat pengiriman, maksimal 2000 karakter |
| `buyer_note` | String | Tidak | Catatan pembeli, maksimal 2000 karakter |
| `payment_method` | String | Tidak | Metode pembayaran, maksimal 80 karakter |
| `payment_reference` | String | Tidak | Referensi pembayaran, maksimal 150 karakter |

**Contoh Request:**

```http
POST /api/orders/checkout HTTP/1.1
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "shipping_address": "Jl. Raya Desa No. 1, Sukamaju",
  "buyer_note": "Tolong dikirim pagi hari",
  "payment_method": "transfer",
  "payment_reference": "TRX-20261109-001"
}
```

**Contoh Response Sukses (201 Created):**

```json
{
  "success": true,
  "message": "Checkout berhasil. Pesanan dipisahkan per penjual.",
  "data": {
    "orders": [
      {
        "id": 38,
        "order_number": "ORD-20261109-XXXX",
        "buyer_id": 10,
        "seller_id": 5,
        "total_amount": 20000.0,
        "shipping_address": "Jl. Raya Desa No. 1, Sukamaju",
        "buyer_note": "Tolong dikirim pagi hari",
        "order_status": "pending",
        "payment": {
          "id": 38,
          "order_id": 38,
          "payment_method": null,
          "payment_reference": null,
          "payment_status": "unpaid",
          "amount": 20000.0,
          "paid_at": null,
          "created_at": "2026-11-09T10:00:00"
        },
        "items": [ ... ],
        "status_logs": [ ... ]
      }
    ],
    "order_count": 1
  }
}
```

**Kemungkinan Error:**

| Status | Kode | Keterangan |
|---|---|---|
| `400` | — | JSON tidak valid |
| `401` | — | Token tidak valid/kadaluarsa/dicabut |
| `403` | — | Bukan business user |
| `409` | `self_purchase_not_allowed` | Keranjang berisi produk milik profil pembeli sendiri |
| `409` | `product_unavailable` | Salah satu produk tidak aktif/tidak ditemukan |
| `409` | `minimum_order_not_met` | Salah satu produk tidak memenuhi minimum order |
| `409` | `insufficient_stock` | Stok salah satu produk tidak mencukupi |
| `409` | `checkout_conflict` | Konflik data saat checkout |
| `415` | — | Bukan JSON |
| `422` | `cart_empty` | Keranjang kosong atau tidak ada item |
| `422` | — | Validasi payload gagal |

---

### 4.3 Buyer Orders

#### 4.3.1 GET /api/orders

**Fungsi:** Mengembalikan daftar pesanan milik pembeli yang login, dengan pagination.

**Hak akses:** Pembeli (role `business_user`).

**Authentication:** `Authorization: Bearer <access_token>` (wajib).

**Parameter Query:**

| Parameter | Tipe | Keterangan |
|---|---|---|
| `page` | Integer | Halaman (default 1) |
| `per_page` | Integer | Item per halaman |
| `status` | String | Filter status pesanan |
| `sort` | String | `newest` atau `oldest` |
| `q` | String | Pencarian, maksimal 180 karakter |

**Contoh Request:**

```http
GET /api/orders?page=1&per_page=10&status=pending&sort=newest HTTP/1.1
Authorization: Bearer <access_token>
```

**Contoh Response Sukses (200 OK):**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 38,
        "order_number": "ORD-20261109-XXXX",
        "seller_id": 5,
        "total_amount": 20000.0,
        "order_status": "pending",
        "created_at": "2026-11-09T10:00:00",
        "updated_at": "2026-11-09T10:00:00"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 10,
      "total": 1,
      "pages": 1
    }
  }
}
```

**Kemungkinan Error:** `401`, `403`, `422` (parameter sort/filter tidak valid).

---

#### 4.3.2 GET /api/orders/{order_id}

**Fungsi:** Mengembalikan detail pesanan milik pembeli yang login, termasuk item, pembayaran, dan riwayat status.

**Hak akses:** Pembeli (role `business_user`).

**Authentication:** `Authorization: Bearer <access_token>` (wajib).

**Parameter URL:**

| Parameter | Tipe | Keterangan |
|---|---|---|
| `order_id` | Integer | ID pesanan |

**Contoh Request:**

```http
GET /api/orders/38 HTTP/1.1
Authorization: Bearer <access_token>
```

**Contoh Response Sukses (200 OK):**

```json
{
  "success": true,
  "data": {
    "order": {
      "id": 38,
      "order_number": "ORD-20261109-XXXX",
      "buyer_id": 10,
      "seller_id": 5,
      "total_amount": 20000.0,
      "shipping_address": "Jl. Raya Desa No. 1, Sukamaju",
      "buyer_note": "Tolong dikirim pagi hari",
      "order_status": "pending",
      "items": [ ... ],
      "payments": [ ... ],
      "status_logs": [ ... ]
    }
  }
}
```

**Kemungkinan Error:** `404` jika pesanan tidak ditemukan atau bukan milik pembeli, `401`, `403`.

---

### 4.4 Cancel Order

#### 4.4.1 POST /api/orders/{order_id}/cancel

**Fungsi:** Membatalkan pesanan milik pembeli yang login. Hanya pesanan dengan status `pending` yang dapat dibatalkan. Stok akan dikembalikan ke inventori. Pembayaran dan bukti pembayaran tidak dihapus; status pembayaran tetap utuh (tidak diubah menjadi `refunded` tanpa mekanisme refund nyata).

**Hak akses:** Pembeli (role `business_user`).

**Authentication:** `Authorization: Bearer <access_token>` (wajib).

**Parameter URL:**

| Parameter | Tipe | Keterangan |
|---|---|---|
| `order_id` | Integer | ID pesanan |

**Body Request (JSON):**

| Field | Tipe | Wajib | Keterangan |
|---|---|---|---|
| `reason` | String | Tidak | Alasan pembatalan, maksimal 2000 karakter |
| `notes` | String | Tidak | Catatan pembatalan, maksimal 2000 karakter |

**Contoh Request:**

```http
POST /api/orders/38/cancel HTTP/1.1
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "reason": "Barang tidak tersedia",
  "notes": "Pembatalan oleh pembeli"
}
```

**Contoh Response Sukses (200 OK):**

```json
{
  "success": true,
  "message": "Pesanan berhasil dibatalkan.",
  "data": {
    "order": {
      "id": 38,
      "order_number": "ORD-20261109-XXXX",
      "order_status": "cancelled",
      ...
    }
  }
}
```

**Kemungkinan Error:**

| Status | Kode | Keterangan |
|---|---|---|
| `400` | — | JSON tidak valid |
| `401` | — | Token tidak valid/kadaluarsa/dicabut |
| `403` | — | Bukan business user |
| `404` | — | Pesanan tidak ditemukan atau bukan milik pembeli |
| `409` | `order_cannot_be_cancelled` | Pesanan tidak dapat dibatalkan pada status ini |
| `409` | `stock_overflow` | Stok melebihi batas maksimum saat pengembalian |
| `415` | — | Bukan JSON |
| `422` | — | Validasi payload gagal |

---

### 4.5 Buyer Payment

#### 4.5.1 GET /api/orders/{order_id}/payment

**Fungsi:** Mengembalikan informasi pembayaran terbaru pesanan milik pembeli, termasuk status dan bukti pembayaran jika ada.

**Hak akses:** Pembeli (role `business_user`).

**Authentication:** `Authorization: Bearer <access_token>` (wajib).

**Parameter URL:**

| Parameter | Tipe | Keterangan |
|---|---|---|
| `order_id` | Integer | ID pesanan |

**Contoh Request:**

```http
GET /api/orders/38/payment HTTP/1.1
Authorization: Bearer <access_token>
```

**Contoh Response Sukses (200 OK):**

```json
{
  "success": true,
  "data": {
    "order_id": 38,
    "order_status": "pending_confirmation",
    "payment": {
      "id": 38,
      "order_id": 38,
      "payment_method": "transfer",
      "payment_reference": "TRX-20261109-001",
      "payment_status": "pending_confirmation",
      "amount": 20000.0,
      "paid_at": "2026-11-09T10:00:00",
      "created_at": "2026-11-09T10:00:00",
      "proof_file_path": null
    }
  }
}
```

**Kemungkinan Error:** `404`, `401`, `403`.

---

#### 4.5.2 PATCH /api/orders/{order_id}/payment

**Fungsi:** Pembeli mengirim informasi pembayaran (metode, referensi, tanggal) untuk pesanan. Hanya dapat diajukan pada status pesanan `pending` atau `confirmed`, dan pembayaran harus masih `unpaid`. Setelah berhasil, status pembayaran berubah menjadi `pending_confirmation` menunggu konfirmasi penjual. Nominal pembayaran diatur backend sesuai total pesanan.

**Hak akses:** Pembeli (role `business_user`).

**Authentication:** `Authorization: Bearer <access_token>` (wajib).

**Parameter URL:**

| Parameter | Tipe | Keterangan |
|---|---|---|
| `order_id` | Integer | ID pesanan |

**Body Request (JSON):**

| Field | Tipe | Wajib | Keterangan |
|---|---|---|---|
| `payment_method` | String | Ya | Metode pembayaran, maksimal 80 karakter |
| `payment_reference` | String | Tidak | Referensi pembayaran, maksimal 150 karakter |
| `paid_at` | String | Tidak | Tanggal pembayaran, format ISO 8601, tidak boleh di masa depan |

**Contoh Request:**

```http
PATCH /api/orders/38/payment HTTP/1.1
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "payment_method": "transfer",
  "payment_reference": "TRX-20261109-001",
  "paid_at": "2026-11-09T10:00:00"
}
```

**Contoh Response Sukses (200 OK):**

```json
{
  "success": true,
  "message": "Informasi pembayaran dikirim dan menunggu konfirmasi penjual.",
  "data": {
    "order_id": 38,
    "order_status": "pending",
    "payment": {
      "id": 38,
      "order_id": 38,
      "payment_method": "transfer",
      "payment_reference": "TRX-20261109-001",
      "payment_status": "pending_confirmation",
      "amount": 20000.0,
      "paid_at": "2026-11-09T10:00:00",
      "created_at": "2026-11-09T10:00:00"
    }
  }
}
```

**Kemungkinan Error:**

| Status | Kode | Keterangan |
|---|---|---|
| `400` | — | JSON tidak valid |
| `401` | — | Token tidak valid/kadaluarsa/dicabut |
| `403` | — | Bukan business user |
| `404` | — | Pesanan tidak ditemukan atau bukan milik pembeli |
| `409` | `payment_order_status_not_allowed` | Status pesanan tidak menerima pengajuan pembayaran (detail: `allowed_statuses`) |
| `409` | `payment_not_pending_submission` | Pembayaran belum dapat diajukan pada status ini |
| `409` | `self_purchase_not_allowed` | (checkout) Produk milik profil pembeli sendiri |
| `422` | `payment_method_required` | Metode pembayaran wajib diisi |
| `415` | — | Bukan JSON |
| `422` | — | Validasi payload gagal |

---

### 4.6 Payment Proof Upload

#### 4.6.1 POST /api/orders/{order_id}/payment/proof

**Fungsi:** Pembeli mengunggah bukti pembayaran (foto transfer/dokumen) untuk pesanan. Hanya dapat diunggah saat status pembayaran `pending_confirmation` dan pesanan belum dibatalkan/selesai. File disimpan privat dengan nama UUID di luar direktori publik. Tipe yang diizinkan: PDF, JPG, JPEG, PNG. Maksimal ukuran 5 MB per file. Isi file divalidasi dengan magic bytes.

**Hak akses:** Pembeli (role `business_user`).

**Authentication:** `Authorization: Bearer <access_token>` (wajib).

**Parameter URL:**

| Parameter | Tipe | Keterangan |
|---|---|---|
| `order_id` | Integer | ID pesanan |

**Body Request (multipart/form-data):**

| Field | Tipe | Wajib | Keterangan |
|---|---|---|---|
| `file` | File | Ya | File bukti pembayaran (PDF/JPG/JPEG/PNG, maksimal 5 MB) |

**Contoh Request (cURL):**

```bash
curl -X POST http://127.0.0.1:5000/api/orders/38/payment/proof \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@C:/path/bukti_transfer.pdf"
```

**Contoh Response Sukses (201 Created):**

```json
{
  "success": true,
  "message": "Bukti pembayaran berhasil diunggah.",
  "data": {
    "order_id": 38,
    "order_status": "pending",
    "payment": {
      "id": 38,
      "order_id": 38,
      "payment_method": "transfer",
      "payment_reference": "TRX-20261109-001",
      "payment_status": "pending_confirmation",
      "amount": 20000.0,
      "paid_at": "2026-11-09T10:00:00",
      "created_at": "2026-11-09T10:00:00"
    },
    "proof": {
      "file_name": "bukti_transfer.pdf",
      "mime_type": "application/pdf",
      "download_url": "/api/orders/38/payment/proof/download"
    }
  }
}
```

**Kemungkinan Error:**

| Status | Kode | Keterangan |
|---|---|---|
| `401` | — | Token tidak valid/kadaluarsa/dicabut |
| `403` | — | Bukan business user |
| `404` | — | Pesanan tidak ditemukan atau bukan milik pembeli |
| `409` | `order_cancelled` | Pesanan sudah dibatalkan |
| `409` | `order_completed` | Pesanan sudah selesai |
| `409` | `payment_proof_not_pending_confirmation` | Bukti hanya dapat diunggah saat menunggu konfirmasi |
| `413` | `file_too_large` | File melebihi 5 MB |
| `422` | `file_required` | File wajib diunggah / nama file tidak valid |
| `422` | `invalid_file_type` | Ekstensi bukan PDF/JPG/JPEG/PNG |
| `422` | `invalid_file_content` | Isi file tidak sesuai ekstensi |
| `422` | `empty_file` | File kosong |
| `500` | `payment_proof_save_failed` | Gagal menyimpan file |
| `500` | `storage_error` | Kesalahan penyimpanan |

---

### 4.7 Payment Proof Download

#### 4.7.1 GET /api/orders/{order_id}/payment/proof/download (Pembeli)

**Fungsi:** Pembeli mengunduh berkas bukti pembayaran pesanan miliknya. Kepemilikan divalidasi sebelum file disajikan.

**Hak akses:** Pembeli (role `business_user`).

**Authentication:** `Authorization: Bearer <access_token>` (wajib).

**Parameter URL:**

| Parameter | Tipe | Keterangan |
|---|---|---|
| `order_id` | Integer | ID pesanan |

**Contoh Request:**

```http
GET /api/orders/38/payment/proof/download HTTP/1.1
Authorization: Bearer <access_token>
```

**Contoh Response Sukses (200 OK):**

File bukti pembayaran dikirim sebagai lampiran (`as_attachment`) dengan nama unduhan `payment_38.pdf` dan MIME type sesuai (misalnya `application/pdf`).

**Kemungkinan Error:** `404 payment_proof_file_not_found` jika bukti tidak ditemukan atau tidak ada, `401`, `403`.

---

#### 4.7.2 GET /api/seller/orders/{order_id}/payment/proof/download (Penjual)

**Fungsi:** Penjual mengunduh berkas bukti pembayaran pesanan yang ia jual. Kepemilikan penjual divalidasi sebelum file disajikan.

**Hak akses:** Penjual (role `business_user`).

**Authentication:** `Authorization: Bearer <access_token>` (wajib).

**Parameter URL:**

| Parameter | Tipe | Keterangan |
|---|---|---|
| `order_id` | Integer | ID pesanan |

**Contoh Request:**

```http
GET /api/seller/orders/38/payment/proof/download HTTP/1.1
Authorization: Bearer <access_token>
```

**Contoh Response Sukses (200 OK):**

File bukti pembayaran dikirim sebagai lampiran dengan nama unduhan `payment_38.pdf` dan MIME type sesuai.

**Kemungkinan Error:** `404 payment_proof_file_not_found`, `401`, `403`.

---

### 4.8 Seller Orders

#### 4.8.1 GET /api/seller/orders

**Fungsi:** Mengembalikan daftar pesanan milik penjual yang login, dengan pagination.

**Hak akses:** Penjual (role `business_user`).

**Authentication:** `Authorization: Bearer <access_token>` (wajib).

**Parameter Query:** Sama dengan `GET /api/orders` (`page`, `per_page`, `status`, `sort`, `q`).

**Contoh Request:**

```http
GET /api/seller/orders?page=1&per_page=10&status=pending_confirmation HTTP/1.1
Authorization: Bearer <access_token>
```

**Contoh Response Sukses (200 OK):**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 38,
        "order_number": "ORD-20261109-XXXX",
        "buyer_id": 10,
        "total_amount": 20000.0,
        "order_status": "pending",
        "created_at": "2026-11-09T10:00:00"
      }
    ],
    "pagination": { ... }
  }
}
```

**Kemungkinan Error:** `401`, `403`, `422`.

---

#### 4.8.2 GET /api/seller/orders/{order_id}

**Fungsi:** Mengembalikan detail pesanan milik penjual yang login, termasuk item, pembeli, dan pembayaran.

**Hak akses:** Penjual (role `business_user`).

**Authentication:** `Authorization: Bearer <access_token>` (wajib).

**Parameter URL:**

| Parameter | Tipe | Keterangan |
|---|---|---|
| `order_id` | Integer | ID pesanan |

**Contoh Request:**

```http
GET /api/seller/orders/38 HTTP/1.1
Authorization: Bearer <access_token>
```

**Contoh Response Sukses (200 OK):**

```json
{
  "success": true,
  "data": {
    "order": {
      "id": 38,
      "order_number": "ORD-20261109-XXXX",
      "buyer_id": 10,
      "seller_id": 5,
      "total_amount": 20000.0,
      "order_status": "pending",
      "items": [ ... ],
      "payments": [ ... ],
      "status_logs": [ ... ]
    }
  }
}
```

**Kemungkinan Error:** `404`, `401`, `403`.

---

### 4.9 Update Order Status

#### 4.9.1 PATCH /api/seller/orders/{order_id}/status

**Fungsi:** Penjual mengubah status pesanan. Transisi yang diizinkan: `pending` → `confirmed`/`cancelled`, `confirmed` → `processing`/`cancelled`, `processing` → `shipped`/`cancelled`, `shipped` → `completed`. Transisi ke `processing` membutuhkan pembayaran dengan status `paid` (409 `payment_not_paid` jika belum). Pembatalan oleh penjual mengembalikan stok. Status yang sama ditolak (`order_status_unchanged`).

**Hak akses:** Penjual (role `business_user`).

**Authentication:** `Authorization: Bearer <access_token>` (wajib).

**Parameter URL:**

| Parameter | Tipe | Keterangan |
|---|---|---|
| `order_id` | Integer | ID pesanan |

**Body Request (JSON):**

| Field | Tipe | Wajib | Keterangan |
|---|---|---|---|
| `status` | String | Ya | Status tujuan: `pending`, `confirmed`, `processing`, `shipped`, `completed`, `cancelled` |
| `notes` | String | Tidak | Catatan perubahan status, maksimal 2000 karakter |

**Contoh Request:**

```http
PATCH /api/seller/orders/38/status HTTP/1.1
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "status": "confirmed",
  "notes": "Pesanan diterima, menunggu pembayaran dikonfirmasi"
}
```

**Contoh Response Sukses (200 OK):**

```json
{
  "success": true,
  "message": "Status pesanan berhasil diperbarui.",
  "data": {
    "order": {
      "id": 38,
      "order_number": "ORD-20261109-XXXX",
      "order_status": "confirmed",
      ...
    }
  }
}
```

**Kemungkinan Error:**

| Status | Kode | Keterangan |
|---|---|---|
| `400` | — | JSON tidak valid |
| `401` | — | Token tidak valid/kadaluarsa/dicabut |
| `403` | — | Bukan business user |
| `404` | — | Pesanan tidak ditemukan atau bukan milik penjual |
| `409` | `order_status_unchanged` | Status tidak berubah |
| `409` | `invalid_status_transition` | Transisi status tidak diizinkan (detail: `allowed_statuses`) |
| `409` | `payment_not_paid` | Target `processing` membutuhkan pembayaran `paid` |
| `409` | `stock_overflow` | Stok melebihi batas saat pengembalian (pembatalan) |
| `415` | — | Bukan JSON |
| `422` | — | Validasi payload gagal |

---

### 4.10 Confirm Payment

#### 4.10.1 POST /api/seller/orders/{order_id}/payment/confirm

**Fungsi:** Penjual mengonfirmasi pembayaran pesanan. Hanya dapat dilakukan jika pesanan belum dibatalkan dan belum selesai, dan pembeli sudah mengajukan pembayaran dengan status `pending_confirmation`. Nominal pembayaran harus sesuai total pesanan (409 `payment_amount_mismatch` jika tidak). Setelah berhasil, status pembayaran berubah menjadi `paid`. Penjual tidak dapat mengonfirmasi pembayaran untuk pesanan yang ia beli sendiri (self-purchase).

**Hak akses:** Penjual (role `business_user`).

**Authentication:** `Authorization: Bearer <access_token>` (wajib).

**Parameter URL:**

| Parameter | Tipe | Keterangan |
|---|---|---|
| `order_id` | Integer | ID pesanan |

**Body Request (JSON):**

| Field | Tipe | Wajib | Keterangan |
|---|---|---|---|
| `payment_method` | String | Tidak | Metode pembayaran, maksimal 80 karakter |
| `payment_reference` | String | Tidak | Referensi pembayaran, maksimal 150 karakter |
| `paid_at` | String | Tidak | Tanggal pembayaran, format ISO 8601 |

**Contoh Request:**

```http
POST /api/seller/orders/38/payment/confirm HTTP/1.1
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "payment_method": "transfer",
  "payment_reference": "TRX-20261109-001",
  "paid_at": "2026-11-09T10:00:00"
}
```

**Contoh Response Sukses (200 OK):**

```json
{
  "success": true,
  "message": "Pembayaran berhasil dikonfirmasi.",
  "data": {
    "order_id": 38,
    "order_status": "pending",
    "payment": {
      "id": 38,
      "order_id": 38,
      "payment_method": "transfer",
      "payment_reference": "TRX-20261109-001",
      "payment_status": "paid",
      "amount": 20000.0,
      "paid_at": "2026-11-09T10:00:00",
      "created_at": "2026-11-09T10:00:00"
    }
  }
}
```

**Kemungkinan Error:**

| Status | Kode | Keterangan |
|---|---|---|
| `400` | — | JSON tidak valid |
| `401` | — | Token tidak valid/kadaluarsa/dicabut |
| `403` | — | Bukan business user |
| `404` | — | Pesanan tidak ditemukan atau bukan milik penjual |
| `409` | `self_purchase_not_allowed` | Tidak dapat mengonfirmasi pembayaran pesanan yang dibeli sendiri |
| `409` | `order_cancelled` | Pesanan sudah dibatalkan |
| `409` | `order_completed` | Pesanan sudah selesai |
| `409` | `payment_already_paid` | Pembayaran sudah dikonfirmasi |
| `409` | `payment_already_refunded` | Pembayaran sudah direfund |
| `409` | `payment_not_pending_confirmation` | Pembayaran belum diajukan oleh pembeli |
| `409` | `payment_amount_mismatch` | Nominal pembayaran tidak sesuai total pesanan (detail: `payment_amount`, `order_total`) |
| `422` | `payment_method_required` | Metode pembayaran wajib diisi |
| `415` | — | Bukan JSON |
| `422` | — | Validasi payload gagal |

---

## 5. Alur Pembayaran dan Fulfillment

1. Pembeli menambahkan produk ke keranjang (`POST /api/cart/items`).
2. Pembeli melakukan checkout (`POST /api/orders/checkout`). Order dibuat dengan status `pending`, pembayaran `unpaid`.
3. Pembeli mengirim informasi pembayaran (`PATCH /api/orders/{id}/payment`). Status pembayaran menjadi `pending_confirmation`.
4. Pembeli mengunggah bukti pembayaran (`POST /api/orders/{id}/payment/proof`) — opsional tapi direkomendasikan.
5. Penjual melihat daftar pesanan (`GET /api/seller/orders`) dan detail pesanan.
6. Penjual mengonfirmasi status pesanan menjadi `confirmed` (`PATCH /api/seller/orders/{id}/status`).
7. Penjual mengonfirmasi pembayaran (`POST /api/seller/orders/{id}/payment/confirm`). Status pembayaran menjadi `paid`.
8. Penjual mengubah status ke `processing` (membutuhkan `paid`), kemudian `shipped`, dan akhirnya `completed`.

Pembeli dapat membatalkan pesanan (`POST /api/orders/{id}/cancel`) selama status masih `pending`; stok akan dikembalikan.

---

## 6. Status dan Transisi

### Status Pesanan (`order_status`)

| Status | Keterangan |
|---|---|
| `pending` | Pesanan baru, belum diproses penjual |
| `confirmed` | Pesanan diterima penjual |
| `processing` | Sedang diproses (memerlukan pembayaran `paid`) |
| `shipped` | Telah dikirim |
| `completed` | Selesai |
| `cancelled` | Dibatalkan |

### Transisi yang Diizinkan Penjual

| Status Saat Ini | Tujuan yang Diizinkan |
|---|---|
| `pending` | `confirmed`, `cancelled` |
| `confirmed` | `processing`, `cancelled` |
| `processing` | `shipped`, `cancelled` |
| `shipped` | `completed` |
| `completed` | (tidak ada) |
| `cancelled` | (tidak ada) |

### Status Pembayaran (`payment_status`)

| Status | Keterangan |
|---|---|
| `unpaid` | Belum ada informasi pembayaran |
| `pending_confirmation` | Pembeli telah mengajukan pembayaran, menunggu konfirmasi penjual |
| `paid` | Dikonfirmasi penjual |
| `failed` | Gagal |
| `refunded` | Direfund (tidak ada mekanisme refund otomatis dalam aplikasi saat ini) |

---

## 7. Keamanan dan Privasi File

- Bukti pembayaran disimpan di luar direktori `static` (direktori privat).
- Nama file menggunakan UUID agar tidak dapat ditebak.
- Ekstensi file dan magic bytes divalidasi (PDF/JPG/JPEG/PNG).
- Maksimal ukuran file 5 MB per bukti pembayaran.
- Download bukti pembayaran hanya melalui endpoint yang mengautentikasi dan memeriksa kepemilikan (pembeli atau penjual order terkait).
- Path internal file tidak diekspos dalam response API.

---

## 8. Contoh cURL Lengkap

```bash
# 1. Register dan login pembeli
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Pembeli","email":"pembeli@example.com","password":"RuralB2B!2026","business_type":"farmer"}'
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"pembeli@example.com","password":"RuralB2B!2026"}'

# 2. Lihat keranjang
curl http://127.0.0.1:5000/api/cart \
  -H "Authorization: Bearer <token_pembeli>"

# 3. Checkout
curl -X POST http://127.0.0.1:5000/api/orders/checkout \
  -H "Authorization: Bearer <token_pembeli>" \
  -H "Content-Type: application/json" \
  -d '{"shipping_address":"Jl. Contoh No. 1","payment_method":"transfer","payment_reference":"TRX-001"}'

# 4. Kirim informasi pembayaran
curl -X PATCH http://127.0.0.1:5000/api/orders/<order_id>/payment \
  -H "Authorization: Bearer <token_pembeli>" \
  -H "Content-Type: application/json" \
  -d '{"payment_method":"transfer","payment_reference":"TRX-001","paid_at":"2026-11-09T10:00:00"}'

# 5. Upload bukti pembayaran (penjual melihat dan mengonfirmasi)
curl -X POST http://127.0.0.1:5000/api/orders/<order_id>/payment/proof \
  -H "Authorization: Bearer <token_pembeli>" \
  -F "file=@bukti.pdf"

# 6. Penjual mengonfirmasi pembayaran
curl -X POST http://127.0.0.1:5000/api/seller/orders/<order_id>/payment/confirm \
  -H "Authorization: Bearer <token_penjual>" \
  -H "Content-Type: application/json" \
  -d '{"payment_method":"transfer"}'

# 7. Penjual mengubah status pesanan
curl -X PATCH http://127.0.0.1:5000/api/seller/orders/<order_id>/status \
  -H "Authorization: Bearer <token_penjual>" \
  -H "Content-Type: application/json" \
  -d '{"status":"processing"}'
```

---

## 9. Catatan Pengujian

Pengujian Stage 6 dilakukan dengan Flask test client terhadap database `ruralb2b`. Seluruh data uji dibuat dengan email dan sufix unik, serta dibersihkan setelah pengujian selesai. Tabel terkait (`carts`, `cart_items`, `orders`, `order_items`, `payments`, `order_status_logs`) kembali ke kondisi awal. Tidak ada perubahan struktur database (DDL) dan tidak ada frontend yang dibangun.