# RuralB2B Product Catalog API (Tahap 5)

Dokumen ini menjelaskan pengelolaan katalog produk B2B, inventori, gambar produk,
dan katalog publik. Tidak ada perubahan skema database pada tahap ini.

## 1. Ruang Lingkup

Fitur yang tersedia:

- Penjual dapat membuat, melihat, mengubah, menghapus, mengaktifkan, dan
  menonaktifkan produk miliknya.
- Penjual dapat mengunggah dan menghapus gambar produk.
- Penjual dapat menambah, mengurangi, atau mengganti stok melalui endpoint
  inventori.
- Pengunjung tanpa login dapat melihat katalog dan detail produk.
- Katalog publik mendukung pencarian, filter kategori/harga/lokasi/stok,
  pagination, dan sorting.
- Kategori dapat dibaca melalui endpoint publik. Pengelolaan kategori belum
  termasuk tahap ini.

Belum termasuk:

- Frontend React.
- Keranjang, checkout, order, dan pembayaran.
- Harga grosir.
- Pengelolaan kategori oleh admin.
- Lokasi khusus per produk.

## 2. Base URL dan Autentikasi

```text
http://127.0.0.1:5000
```

Endpoint privat memakai JWT:

```http
Authorization: Bearer <access_token>
```

- Pengelolaan produk hanya untuk user dengan role `business_user`.
- Admin tidak dapat membuat/mengubah produk melalui endpoint ini.
- Setiap operasi penjual diverifikasi terhadap `business_profile` pemilik.
  Produk milik pengguna lain menghasilkan `404` agar tidak membocorkan data.
- Endpoint publik tidak memerlukan token.

## 3. Pemetaan Skema Database

Tidak ada DDL, tabel baru, atau kolom baru.

### `products`

| Kolom | Tipe | Pemakaian API |
|---|---|---|
| `id` | BIGINT UNSIGNED PK | ID produk |
| `business_id` | BIGINT UNSIGNED FK | Diisi otomatis dari profil penjual |
| `category_id` | BIGINT UNSIGNED FK, nullable | Opsional, harus kategori yang ada |
| `product_name` | VARCHAR(180) | Wajib, 2-180 karakter |
| `description` | TEXT | Opsional, maksimal 5000 karakter |
| `price` | DECIMAL(14,2) | Wajib, 0-999999999999.99, maksimal 2 desimal |
| `unit` | VARCHAR(40) | Wajib, 1-40 karakter |
| `minimum_order` | INT UNSIGNED | Default 1, minimal 1 |
| `product_status` | ENUM(`active`,`inactive`,`out_of_stock`) | Default `active` |
| `created_at`, `updated_at` | DATETIME | Dari MySQL |

### `categories`

Dibaca melalui `GET /api/categories`. Produk boleh tidak memiliki kategori
(`category_id = null`). Jika `category_id` dikirim, kategori wajib ada.

Tabel `categories` saat ini kosong dan **tidak diisi data palsu** oleh tahap ini.
Isi kategori melalui seed/admin SQL di luar endpoint katalog:

```sql
INSERT INTO ruralb2b.categories (name, description, parent_id)
VALUES ('Sayuran', 'Produk sayuran segar', NULL);
```

### `product_images`

| Kolom | Tipe | Pemakaian API |
|---|---|---|
| `image_path` | VARCHAR(500) | Path relatif privat; tidak pernah diekspos |
| `is_primary` | TINYINT(1) | Maksimal satu gambar utama per produk |
| `created_at` | DATETIME | Dari MySQL |

### `inventories`

Satu produk memiliki satu baris inventori.

| Kolom | Tipe | Pemakaian API |
|---|---|---|
| `stock_quantity` | INT UNSIGNED | Stok total, tidak boleh negatif |
| `reserved_quantity` | INT UNSIGNED | Reservasi internal; tidak dapat diubah klien |
| `available_quantity` | turunan | `stock_quantity - reserved_quantity` |

Stok tersedia = stok total dikurangi reservasi. Penjual tidak boleh menurunkan
stok total di bawah jumlah yang sudah direservasi.

### `business_profiles` dan `users`

- `products.business_id` terhubung ke `business_profiles.id`.
- `business_profiles.user_id` terhubung ke `users.id`.
- Lokasi produk diambil dari profil bisnis: `village`, `district`, `city`,
  `province`, dan `postal_code`.
- Tidak ada kolom lokasi pada `products`; filter lokasi memakai profil penjual.

### Keterbatasan skema

- **Harga grosir tidak didukung** karena tidak ada kolom harga grosir pada
  `products`. Field `wholesale_price` ditolak sebagai field tidak dikenal.
- **Lokasi per produk tidak didukung**. Produk mengikuti lokasi profil bisnis.
- **Varian produk, berat, dimensi, dan SKU tidak tersedia** pada skema saat ini.

## 4. Format Response

Sukses:

```json
{
  "success": true,
  "message": "Opsional",
  "data": {}
}
```

Gagal:

```json
{
  "success": false,
  "message": "Pesan error",
  "code": "kode_mesin",
  "errors": {
    "field": "Detail validasi"
  },
  "details": {}
}
```

Field `code`, `errors`, dan `details` hanya muncul jika relevan.

## 5. Endpoint Publik

### 5.1 `GET /api/products`

Mengembalikan produk yang tidak berstatus `inactive`. Produk `active` dan
`out_of_stock` tetap tampil; gunakan `in_stock=true` untuk hanya menampilkan
stok tersedia.

Query parameter:

| Parameter | Tipe | Keterangan |
|---|---|---|
| `q` / `search` | string | Cari berdasarkan nama produk, maksimal 180 karakter |
| `category_id` / `category` | integer | Filter kategori |
| `min_price` | decimal | Harga minimum |
| `max_price` | decimal | Harga maksimum; harus >= `min_price` |
| `location` | string | Cari di desa/kecamatan/kota/provinsi profil penjual |
| `city` | string | Filter kota/kabupaten |
| `province` | string | Filter provinsi |
| `district` | string | Filter kecamatan |
| `village` | string | Filter desa/kelurahan |
| `in_stock` | boolean | `true` = stok tersedia > 0; `false` = stok tersedia <= 0 |
| `available` / `stock` | boolean | Alias `in_stock` |
| `sort` | enum | `newest` (default), `oldest`, `price_asc`, `price_desc`, `name_asc`, `name_desc` |
| `page` | integer | Default 1 |
| `per_page` | integer | Default 20, maksimal 100 |

Contoh:

```http
GET /api/products?q=tomat&category_id=1&min_price=10000&max_price=50000&city=Bandung&in_stock=true&sort=price_asc&page=1&per_page=20
```

Response `200`:

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 12,
        "business_id": 4,
        "category_id": 1,
        "category": {"id": 1, "name": "Sayuran"},
        "product_name": "Tomat Merah",
        "description": "Tomat segar",
        "price": 12000.0,
        "unit": "kg",
        "minimum_order": 2,
        "product_status": "active",
        "is_active": true,
        "seller": {
          "id": 4,
          "business_name": "Tani Makmur",
          "business_type": "farmer"
        },
        "location": {
          "village": "Sukamaju",
          "district": "Cibiru",
          "city": "Bandung",
          "province": "Jawa Barat",
          "postal_code": "40615"
        },
        "inventory": {
          "id": 9,
          "product_id": 12,
          "stock_quantity": 100,
          "reserved_quantity": 5,
          "available_quantity": 95,
          "in_stock": true,
          "updated_at": "2026-11-08T13:00:00"
        },
        "stock_quantity": 100,
        "available_quantity": 95,
        "is_in_stock": true,
        "images": [
          {
            "id": 31,
            "product_id": 12,
            "is_primary": true,
            "url": "/api/products/12/images/31/file",
            "created_at": "2026-11-08T13:00:00"
          }
        ],
        "created_at": "2026-11-08T13:00:00",
        "updated_at": "2026-11-08T13:00:00"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 1,
      "pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

Catatan:

- `price` dikirim sebagai angka JSON hasil konversi dari `DECIMAL`.
- `image_path` dan path storage internal tidak pernah dikirim.
- URL gambar publik hanya dapat diakses untuk produk non-inactive.

### 5.2 `GET /api/products/{id}`

Response `200` dengan `data.product`. Produk `inactive` atau tidak ada
menghasilkan `404 product_not_found`.

### 5.3 `GET /api/categories`

Response `200`:

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "name": "Sayuran",
        "description": "Produk sayuran segar",
        "parent_id": null
      }
    ]
  }
}
```

Query opsional: `parent_id` (integer positif).

### 5.4 `GET /api/products/{product_id}/images/{image_id}/file`

Mengirim file gambar secara inline. Endpoint publik hanya melayani gambar milik
produk yang tidak `inactive`. File disimpan di luar direktori publik dan path
internal tidak diekspos.

## 6. Endpoint Penjual

Semua endpoint pada bagian ini memerlukan Bearer token `business_user`.

### 6.1 `GET /api/business/products`

Daftar seluruh produk milik penjual, termasuk `inactive` dan `out_of_stock`.

Query parameter: `q`/`search`, `status`/`product_status`
(`active`/`inactive`/`out_of_stock`), `category_id`/`category`,
`in_stock`/`available`/`stock`, `sort`, `page`, `per_page`.
Response sama dengan katalog publik, tetapi URL gambar memakai
`/api/business/products/...` agar pemilik dapat melihat gambar produk inactive.

### 6.2 `GET /api/business/products/{id}`

Detail produk milik sendiri, termasuk produk inactive. Produk milik user lain
menghasilkan `404 product_not_found`.

### 6.3 `POST /api/products`

Membuat produk baru. `business_id` diisi otomatis dari profil penjual.

Request:

```json
{
  "product_name": "Tomat Merah",
  "description": "Tomat segar dari petani",
  "category_id": 1,
  "price": 12000,
  "unit": "kg",
  "minimum_order": 2,
  "product_status": "active",
  "stock_quantity": 100
}
```

Field:

| Field | Wajib | Aturan |
|---|---|---|
| `product_name` | Ya | 2-180 karakter |
| `description` | Tidak | Maksimal 5000 karakter; string kosong menjadi `null` |
| `category_id` | Tidak | Integer positif; harus ada |
| `price` | Ya | 0-999999999999.99, maksimal 2 desimal |
| `unit` | Ya | 1-40 karakter, misalnya `kg`, `liter`, `pcs`, `karung` |
| `minimum_order` | Tidak | Default 1, minimal 1 |
| `product_status` | Tidak | Default `active`; pilihan `active`, `inactive`, `out_of_stock` |
| `stock_quantity` | Tidak | Default 0, hanya boleh saat create |

Field asing ditolak, termasuk `wholesale_price`, `location`, `business_id`, dan
`stock_quantity` pada update.

Response `201` dengan `data.product`. Stok awal dibuat pada `inventories`.

### 6.4 `PUT /api/products/{id}`

Mengganti data produk. Field wajib: `product_name`, `price`, `unit`.

Field opsional yang dihilangkan akan di-reset:

- `description` menjadi `null`
- `category_id` menjadi `null`
- `minimum_order` menjadi `1`
- `product_status` menjadi `active`

Stok tidak diubah oleh PUT. Gunakan endpoint inventori.

### 6.5 `PATCH /api/products/{id}`

Mengubah sebagian field. Minimal satu field harus dikirim. Field yang tidak
dikirim tidak berubah. `stock_quantity` tidak diterima di sini.

Contoh menonaktifkan produk:

```json
{
  "product_status": "inactive"
}
```

### 6.6 `DELETE /api/products/{id}`

Menghapus produk milik sendiri beserta inventori dan gambar.

- Jika produk masih dipakai pada `cart_items` atau `order_items`, response
  `409 product_in_use` dan produk tidak dihapus. Nonaktifkan produk sebagai
  gantinya.
- File gambar dihapus setelah transaksi database berhasil.
- Produk milik user lain menghasilkan `404`.

### 6.7 `POST /api/products/{id}/images`

Upload satu gambar per request dengan `multipart/form-data`.

Form field:

| Field | Wajib | Keterangan |
|---|---|---|
| `file` | Ya | JPG, JPEG, PNG, atau WEBP |
| `is_primary` | Tidak | `true`/`false`; gambar pertama otomatis utama |

Batasan:

- Maksimal 5 gambar per produk (`MAX_PRODUCT_IMAGES`).
- Maksimal 5 MB per gambar (`MAX_PRODUCT_IMAGE_SIZE`).
- Maksimal request 10 MB (`MAX_CONTENT_LENGTH`).
- Ekstensi dan magic bytes harus cocok.
- Nama file asli tidak dipakai; nama file dibuat UUID.
- Jika `is_primary=true`, gambar utama lama otomatis dilepas.

Response `201`:

```json
{
  "success": true,
  "message": "Gambar produk berhasil diunggah.",
  "data": {
    "image": {
      "id": 31,
      "product_id": 12,
      "is_primary": true,
      "url": "/api/business/products/12/images/31/file",
      "created_at": "2026-11-08T13:00:00"
    }
  }
}
```

### 6.8 `DELETE /api/products/{id}/images/{image_id}`

Menghapus gambar. Jika gambar yang dihapus adalah gambar utama, gambar tersisa
dengan ID terkecil otomatis menjadi utama. File fisik dihapus setelah transaksi
database berhasil.

### 6.9 `GET /api/business/products/{product_id}/images/{image_id}/file`

Mengirim gambar produk milik sendiri, termasuk produk inactive. Berguna untuk
preview di dashboard penjual. Endpoint publik tetap menyembunyikan gambar produk
inactive.

### 6.10 `GET /api/business/inventory`

Daftar produk milik penjual beserta data inventori. Mendukung `q`, `status`,
`category_id`, `in_stock`/`available`, `sort`, `page`, `per_page`.

Setiap item berisi data produk dan objek `inventory` yang sama seperti katalog.

### 6.11 `PATCH /api/business/inventory/{product_id}`

Mengubah stok produk milik sendiri. Kirim **salah satu** dari:

- `stock_quantity`: menetapkan stok total secara absolut.
- `adjustment`: menambah (positif) atau mengurangi (negatif) stok.

Contoh menambah 10:

```json
{
  "adjustment": 10
}
```

Contoh menetapkan stok menjadi 50:

```json
{
  "stock_quantity": 50
}
```

Aturan:

- Hasil akhir tidak boleh negatif.
- Hasil akhir tidak boleh melebihi `4294967295`.
- Hasil akhir tidak boleh lebih kecil dari `reserved_quantity`.
- `reserved_quantity` tidak dapat diubah dari endpoint ini.
- Status produk tidak diubah otomatis; gunakan `PATCH /api/products/{id}` untuk
  mengubah `product_status`.

Response `200`:

```json
{
  "success": true,
  "message": "Stok produk berhasil diperbarui.",
  "data": {
    "inventory": {
      "id": 9,
      "product_id": 12,
      "stock_quantity": 50,
      "reserved_quantity": 0,
      "available_quantity": 50,
      "in_stock": true,
      "updated_at": "2026-11-08T13:00:00"
    },
    "product": {}
  }
}
```

## 7. Aturan Bisnis

1. Pengunjung tanpa login hanya dapat membaca katalog dan detail.
2. Hanya `business_user` yang dapat mengelola produk.
3. Pemilik produk ditentukan dari `business_profile` user yang login.
4. Produk selalu terhubung ke profil bisnis; `business_id` tidak dapat diisi
   klien.
5. Katalog publik menyembunyikan produk `inactive`.
6. Produk `out_of_stock` tetap dapat tampil di katalog dengan
   `is_in_stock=false`, kecuali difilter `in_stock=true`.
7. Harga, stok, minimum order, satuan, kategori, status, dan gambar divalidasi.
8. Stok tidak boleh negatif dan tidak boleh di bawah reservasi.
9. Hapus produk ditolak jika masih dipakai keranjang/pesanan.
10. File gambar disimpan privat; API hanya mengembalikan URL endpoint.
11. Tidak ada data produk contoh yang dibuat oleh aplikasi atau pengujian akhir.

## 8. Kode Error Penting

| HTTP | Code | Keterangan |
|---|---|---|
| 401 | `token_missing` | Bearer token tidak ada |
| 401 | `token_expired` / `token_revoked` | Token tidak valid lagi |
| 403 | `business_user_required` | Bukan user bisnis/admin mencoba mengelola produk |
| 404 | `product_not_found` | Produk tidak ada atau bukan milik user |
| 404 | `product_image_not_found` | Gambar tidak ada atau bukan milik produk |
| 404 | `business_profile_not_found` | User belum memiliki profil bisnis |
| 409 | `product_in_use` | Produk masih ada di keranjang/pesanan |
| 409 | `image_limit_reached` | Jumlah gambar sudah maksimal |
| 413 | `image_too_large` | Gambar melebihi batas per file |
| 413 | `request_too_large` | Total request multipart melebihi batas |
| 415 | `unsupported_media_type` | Body JSON tidak memakai Content-Type yang benar |
| 422 | `category_not_found` | `category_id` tidak ada |
| 422 | `invalid_image_type` | Ekstensi gambar tidak diizinkan |
| 422 | `invalid_image_content` | Magic bytes tidak cocok dengan ekstensi |
| 422 | `empty_image` | File gambar kosong |
| 422 | `file_required` | Field `file` tidak dikirim |
| 422 | `negative_stock` | Hasil stok negatif |
| 422 | `stock_overflow` | Stok melebihi batas unsigned int |
| 422 | `stock_below_reserved` | Stok di bawah jumlah reservasi |
| 422 | validasi lain | Lihat `errors` per field |

## 9. Keamanan

- Semua endpoint privat memakai JWT dan pengecekan role dari database.
- Setiap query produk penjual difilter dengan `business_id` milik user.
- ID produk pengguna lain diperlakukan sebagai `404`.
- Semua input divalidasi sebelum menyentuh database.
- File gambar divalidasi ekstensi, magic bytes, ukuran, jumlah, dan total request.
- File disimpan di `backend/storage/product_images/` (default), di luar `static`.
- Nama file memakai UUID; nama asli tidak disimpan.
- Path internal tidak dikembalikan API.
- Resolusi path gambar memastikan file tetap berada di dalam storage.
- `storage/` dan `.env` diabaikan `.gitignore`.
- Tidak ada kredensial atau path internal pada response error.

## 10. Pengujian

### 10.1 Persiapan

```powershell
cd C:\laragon\www\ruralb2b\backend
.\venv\Scripts\python.exe app.py
```

Pastikan MySQL Laragon berjalan. Login sebagai user bisnis untuk mendapatkan
token.

### 10.2 Urutan Postman

Import
[`RuralB2B-Product-Catalog.postman_collection.json`](RuralB2B-Product-Catalog.postman_collection.json).

1. **Health Check**.
2. **Login Business** — token disimpan otomatis.
3. **Public Categories** — opsional, isi `category_id` jika ada kategori.
4. **Create Product** — `product_id` disimpan otomatis.
5. **Public List Products** → **Public Product Detail**.
6. **Business Product List** → **Get Business Product**.
7. **PUT Product** atau **PATCH Product**.
8. **Get Inventory** → **PATCH Inventory Set** / **PATCH Inventory Adjust**.
9. **Upload Product Image** — pilih file; `image_id` disimpan otomatis.
10. **Public Image File** / **Business Image File**.
11. **Delete Product Image**.
12. **Delete Product**.

### 10.3 Contoh cURL

```bash
# Login
TOKEN=$(curl -s -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"budi.umkm@example.com","password":"RuralB2B!2026"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")

# Buat produk
curl -X POST http://127.0.0.1:5000/api/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_name":"Tomat Merah","price":12000,"unit":"kg","minimum_order":2,"stock_quantity":100}'

# Katalog publik
curl "http://127.0.0.1:5000/api/products?q=tomat&in_stock=true&sort=price_asc"

# Ubah stok (tambah 10)
curl -X PATCH http://127.0.0.1:5000/api/business/inventory/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"adjustment":10}'

# Upload gambar
curl -X POST http://127.0.0.1:5000/api/products/1/images \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@C:/path/tomat.png" \
  -F "is_primary=true"
```

### 10.4 Matriks Pengujian yang Dilakukan

| Skenario | Hasil |
|---|---|
| Create/read/update/delete produk | berhasil |
| PUT reset field opsional dan PATCH parsial | berhasil |
| Produk inactive disembunyikan dari publik | berhasil |
| Produk out_of_stock tetap terlihat dengan `is_in_stock=false` | berhasil |
| Search, kategori, harga, lokasi, stok, sorting, pagination | berhasil |
| Validasi harga negatif/3 desimal, stok negatif, minimum order 0, status salah | `422` |
| Field `wholesale_price` ditolak | `422` |
| Akses produk/inventori/gambar user lain | `404` |
| Admin mencoba mengelola produk | `403` |
| Upload JPG/PNG, primary image, limit 5 gambar | berhasil |
| Ekstensi salah, magic bytes salah, file kosong, file > 5 MB | `422`/`413` |
| Hapus gambar utama dan promosi primary | berhasil |
| Hapus produk dengan gambar | file dan baris terkait terhapus |
| Hapus produk yang masih di keranjang | `409 product_in_use` |
| Profil, verifikasi, admin, health regression | tetap berfungsi |
| Data dan file uji | dihapus; tabel terkait kosong |

## 11. Catatan Implementasi

- `product_status` tidak diubah otomatis saat stok berubah. Ini mencegah status
  manual penjual tertimpa. Ketersediaan sebenarnya selalu dapat dibaca dari
  `is_in_stock`/`available_quantity`.
- `minimum_order` dan stok adalah bilangan bulat. `price` memakai `DECIMAL` dan
  dikembalikan sebagai angka JSON.
- Kategori bersifat opsional dan belum memiliki CRUD pada tahap ini.
- Tidak ada perubahan skema database. Semua mapping disesuaikan dengan tabel
  aktual.
