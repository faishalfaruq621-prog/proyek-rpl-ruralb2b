# Rencana Pembersihan Data Demo Menjelang Peluncuran Produksi

> Status: **DOKUMEN RENCANA — belum dieksekusi.**
> Sesuai keputusan pemilik proyek (Babak 4), data pengujian dipertahankan sebagai
> data demo (Pilihan B). Dokumen ini hanya menjadi panduan bila kelak diputuskan
> untuk beralih ke mode produksi (Pilihan A).
>
> **Aturan mutlak: tidak ada UPDATE/DELETE yang dijalankan sebelum pemilik
> menyetujui rencana ini dan backup penuh sudah terverifikasi.**

## 1. Prinsip Eksekusi

1. Backup database penuh **dan verifikasi restore-nya** sebelum satu baris pun diubah.
2. Eksekusi dilakukan per-fase; setiap fase diverifikasi sebelum lanjut.
3. Semua DELETE memakai daftar ID eksplisit hasil query verifikasi (bukan kondisi longgar).
4. Data berkas di disk (`backend/storage/`) hanya dihapus setelah baris DB terkait hilang.
5. Order 43, akun 91 (`Faishal`), dan akun admin 102 **dikecualikan total**.

## 2. Klasifikasi Data (per 2026-11-11)

### 2.1 Data OPERASIONAL yang dipertahankan

| Objek | Detail |
|---|---|
| Akun admin | id 102 (`Administrator RuralB2B`) |
| Akun pemilik | id 91 (`Faishal`, tanpa produk/transaksi) |
| Order 43 | `RBB2B-20261110191607-3755CC62C1`, pending, total 24.000, payment #42 (unpaid/COD), status log id 66, item ke produk 22, notifikasi terkait (jika ada), percakapan dengan `order_id=43` (conv id 2) |

### 2.2 Data DEMO yang menjadi target pembersihan

| Kelompok | Isi | Jumlah |
|---|---|---|
| Akun uji | users id 29–88 dan 89–101 (pola email `stage6.*`, `pembeli.uji.*`, `test.*`, `ai.*`, `ident.*`, dll) | 45 akun |
| Profil bisnis uji | business_profiles milik akun di atas | 45 |
| Produk demo | id 22–33 (Stage6) dan 51–52 (uji integrasi) | 14 |
| Order demo | id 1–12 dan 42 (+ items, payments, status_logs, notifikasi) | 13 order |
| Keranjang | carts milik akun uji (semuanya sudah kosong) | 11 |
| Chat demo | conversation id 1 (produk 22) + 3 pesan | 1 conv |
| Verifikasi uji | verification_requests (3) + dokumen, log, telegram_logs | 3 |
| Berkas disk | `storage/payment_proofs/order_{3,5,7,9,11,42}`, `storage/verification_documents/business_76` | 7 berkas |

⚠️ Konsekuensi Pilihan B: katalog publik dan daftar order admin saat ini menampilkan
data demo. Ini disepakati diterima sampai peluncuran produksi.

## 3. Peta Foreign Key (hasil audit `information_schema`, 2026-11-11)

Urutan penghapusan HARUS mengikuti ketergantungan ini (anak dulu, induk belakangan).

| Tabel | Kolom | Referensi | ON DELETE |
|---|---|---|---|
| ai_recommendation_items | product_id | products | CASCADE |
| ai_recommendation_items | recommendation_id | ai_recommendations | CASCADE |
| ai_recommendation_items | supplier_business_id | business_profiles | CASCADE |
| ai_recommendations | user_id | users | CASCADE |
| business_profiles | user_id | users | RESTRICT |
| cart_items | cart_id | carts | CASCADE |
| cart_items | product_id | products | RESTRICT |
| carts | buyer_id | users | RESTRICT |
| categories | parent_id | categories | SET NULL |
| chatbot_messages | session_id | chatbot_sessions | CASCADE |
| chatbot_sessions | user_id | users | CASCADE |
| conversations | buyer_id | users | CASCADE |
| conversations | order_id | orders | SET NULL |
| conversations | product_id | products | SET NULL |
| conversations | seller_id | users | CASCADE |
| inventories | product_id | products | RESTRICT |
| messages | conversation_id | conversations | CASCADE |
| messages | sender_id | users | CASCADE |
| notifications | user_id | users | CASCADE |
| order_items | order_id | orders | RESTRICT |
| order_items | product_id | products | RESTRICT |
| order_status_logs | changed_by | users | SET NULL |
| order_status_logs | order_id | orders | RESTRICT |
| orders | buyer_id | users | RESTRICT |
| orders | seller_id | business_profiles | RESTRICT |
| payments | order_id | orders | RESTRICT |
| product_images | product_id | products | CASCADE |
| products | business_id | business_profiles | RESTRICT |
| products | category_id | categories | SET NULL |
| telegram_logs | verification_id | verification_requests | RESTRICT |
| verification_documents | verification_id | verification_requests | CASCADE |
| verification_logs | admin_id | users | SET NULL |
| verification_logs | verification_id | verification_requests | RESTRICT |
| verification_requests | business_profile_id | business_profiles | RESTRICT |
| verification_requests | reviewed_by | users | SET NULL |

### Implikasi penting dari peta FK

1. `order_items.product_id` = **RESTRICT** → produk 22–33 TIDAK BISA dihapus selama
   order 43 (itemnya ke produk 22) masih dipertahankan. Konsekuensi desain:
   produk 22 harus **dipertahankan** bersama Order 43, atau diubah statusnya
   menjadi non-aktif (`product_status='inactive'`) tanpa dihapus.
2. `orders.buyer_id/seller_id`, `business_profiles.user_id` = **RESTRICT** →
   akun uji yang terlibat Order 43 (buyer 75, seller 30 / profil 30) juga tidak
   dapat dihapus selama Order 43 dipertahankan.
3. `payments`, `order_items`, `order_status_logs` = RESTRICT ke orders →
   hapus dulu ketiganya sebelum menghapus orders.
4. `inventories.product_id` = RESTRICT → hapus inventories sebelum products.
5. `verification_logs`, `telegram_logs` = RESTRICT ke verification_requests →
   hapus keduanya dulu.
6. `products.business_id` = RESTRICT → hapus products (per profil) sebelum
   menghapus business_profiles.

## 4. Fase Eksekusi (rancangan)

### Fase 0 — Persiapan
- [ ] `mysqldump -u root ruralb2b > backup_pra_bersih_YYYYMMDD.sql` (schema+data).
- [ ] Verifikasi restore: impor dump ke database sementara, bandingkan jumlah baris per tabel.
- [ ] Snapshot folder `backend/storage/` (salin ke luar direktori proyek).
- [ ] Kumpulkan daftar ID eksplisit dan simpan sebagai artefak persetujuan.

### Fase 1 — Hapus tabel anak yang berdiri sendiri (per akun uji)
```
urutan: ai_recommendation_items → ai_recommendations → chatbot_messages
        → chatbot_sessions → notifications → cart_items → carts
        → messages → conversations (kecuali conv order 43)
```

### Fase 2 — Verifikasi uji
```
urutan: telegram_logs → verification_logs → verification_documents
        → verification_requests
```

### Fase 3 — Transaksi demo
```
urutan: order_status_logs → payments → order_items → orders (id 1–12, 42)
```
Berkas disk terkait (`payment_proofs/order_3|5|7|9|11|42`) dihapus setelah verifikasi.

### Fase 4 — Produk demo
```
urutan: inventories → product_images → products (51, 52, 23–33; produk 22
        DIPERTAHANKAN karena dirujuk order_items milik Order 43)
```

### Fase 5 — Profil & akun uji
```
urutan: business_profiles (45) → users (29–88, 89–101)
        KECUALI buyer 75 & seller 30 (dirujuk Order 43, lihat §3 poin 2)
```
Kedua akun yang dipertahankan opsional dinonaktifkan lewat
`account_status='suspended'` **dengan persetujuan terpisah** (bukan dihapus).

### Fase 6 — Verifikasi akhir
- [ ] Tidak ada orphan: `LEFT JOIN` setiap tabel anak ke induknya → hasil harus 0.
- [ ] Order 43 + payment + item + status log + conv utuh (bandingkan nilai dengan snapshot Fase 0).
- [ ] Login admin 102 & akun 91 berfungsi.
- [ ] Katalog/produk/statistik admin menampilkan data bersih.
- [ ] Backup pasca-bersih disimpan terpisah dari backup pra-bersih.

### Rollback
Restore dari `backup_pra_bersih_*.sql` + salin kembali snapshot `storage/`.
Aplikasi dimatikan (backend stop) selama proses restore.

## 5. Hal yang TIDAK disentuh dalam rencana ini

- Struktur tabel/skema (tanpa DDL).
- Kategori (8 kategori tetap).
- Order 43 beserta seluruh relasi historisnya.
- Akun 91 dan admin 102.
- Konfigurasi `.env` (token Telegram/AI tetap via environment variables).
