# Persiapan Demo Final — RuralB2B

> Tanggal: 2026-11-11 (Babak 8 — finalisasi Babak 1–8)
> Status: **RELEASE CANDIDATE untuk demonstrasi** — stabil, teruji, bukan production-ready
> Dokumen pendamping: `PANDUAN_DEMO.md` (skenario 17 langkah), `LAPORAN_VISUAL_TESTING.md` (Babak 7), `RELEASE_CHECKLIST.md`.

## 1. Ringkasan Aplikasi

RuralB2B adalah **marketplace B2B untuk UMKM pedesaan Indonesia** — menghubungkan
petani/supplier/kolektor lokal (Seller) dengan pembeli bisnis (Buyer), dengan
asisten AI untuk membantu belanja dan pengelolaan bisnis.

| Lapisan | Teknologi | Status |
|---|---|---|
| Backend | Flask (Python) + SQLAlchemy + MySQL 8 | ✅ 28+ endpoint teruji, guard otorisasi lengkap |
| Frontend | React (Vite) + Tailwind, build produksi ✅ | ✅ 34 rute, 73/73 uji browser bersih |
| AI | Gemini (`gemini-3.5-flash-lite`) — chat, rekomendasi, insight | ✅ aktif, limit harian 50 req/akun |
| Database | `ruralb2b` (data demo dipertahankan — keputusan Pilihan B) | ✅ backup tersedia di `backups/` |

## 2. Daftar Fitur Utama (status keterhubungan terverifikasi)

| Fitur | Status | Bukti |
|---|---|---|
| Registrasi & Login | ✅ Berfungsi | Login end-to-end di browser; register terhubung ke `POST /api/auth/register` (submit registrasi tidak dieksekusi saat pengujian demi batasan data) |
| Dashboard | ✅ Berfungsi | Render + angka sesuai DB (screenshot Babak 7) |
| Katalog + pencarian | ✅ Berfungsi | `GET /api/products?search=...` = 200; render 3 lebar layar |
| Detail produk | ✅ Berfungsi | API 200 + render; placeholder gambar SVG lokal |
| Keranjang | ✅ Berfungsi | `GET /api/cart` = 200; validasi stok/min. beli aktif |
| Checkout | ✅ Terhubung | Form → `orderService.checkout()`; **eksekusi checkout tidak diuji** (larangan transaksi baru) — negative test Babak 6 lulus 5/5 |
| Riwayat & detail pesanan | ✅ Berfungsi | Order 43 tampil benar (buyer scope) |
| Manajemen produk Seller | ✅ Berfungsi | Kelola/Tambah/Edit render; endpoint business/products 200 |
| Chat Buyer–Seller | ✅ Berfungsi | Threads 200, thread render + auto-scroll; kirim pesan tidak dieksekusi (membuat data) |
| Notifikasi | ✅ Berfungsi | Badge = 1 sesuai DB; polling 60 dtk |
| Verifikasi bisnis | ✅ Berfungsi (alur tampil) | Seller page + admin list/detail render; request #9 (user 76) masih pending — dapat dipakai demo approve/reject + pemicu Telegram; eksekusi approve/reject tidak dieksekusi saat audit (mengubah data) |
| Notifikasi Telegram | ✅ Kode siap — menunggu token | Integrasi non-fatal di 3 titik (pengajuan/approve/reject verifikasi), dedup + audit log; fungsi uji koneksi aman `telegram_test_connection.py`; lihat `docs/KONFIGURASI_TELEGRAM.md` |
| AI Assistant Standard | ✅ Berfungsi | API 200 (Babak 6 T7), halaman render |
| AI Assistant Plus | ✅ Berfungsi | API 200 (T8) |
| AI Product Recommendation | ✅ Berfungsi | API 200 (T9), render |
| AI Business Insights | ✅ Berfungsi — **kini on-demand** | Statistik langsung dari DB; analisis Gemini hanya via tombol "Analisis Bisnis" (perbaikan Babak 8) |
| Dashboard Admin | ✅ Berfungsi | `GET /admin/stats` = 200, render |
| Manajemen pengguna | ✅ Berfungsi | `GET /admin/users` = 200; PATCH tidak dieksekusi (data) |
| Manajemen kategori | ✅ Berfungsi | `GET /admin/categories` = 200; CRUD tidak dieksekusi (batasan kategori) |
| Manajemen pesanan Admin | ✅ Berfungsi | `GET /admin/orders` = 200, render |

## 3. Pembagian Fungsi per Role

Struktur: satu model pengguna `business_user` (kapabilitas ganda beli+jual,
dasar: kepemilikan profil bisnis di DB) dan `admin`. **Backend adalah penentu
otorisasi**: `@admin_required` (14 endpoint admin), `@business_user_required`
(cart/checkout/order/produk/insights), `@token_required` (chat/notifikasi/
profil). Frontend hanya menyembunyikan menu; akses URL langsung tetap ditolak.

| Role | Navigasi | Akses |
|---|---|---|
| **Buyer** | Pembelian: Keranjang, Pesanan Saya, Riwayat, AI Recommendation (+ Beranda/Katalog/Chat/Notifikasi/AI Assistant) | cart/checkout/pesanan miliknya |
| **Seller** | Semua menu Buyer **+** Penjualan: Dashboard Penjual, Produk Saya, Tambah Produk, Pesanan Masuk, Riwayat Penjualan, AI Business Insights | produk/inventory/order masuk miliknya |
| **Dual (Buyer+Seller)** | Kedua dropdown tampil berdampingan (`Pembelian` + `Penjualan`) — terverifikasi di browser | kedua kelompok endpoint |
| **Admin** | Beranda, Katalog, AI Assistant + **Panel Admin** di dropdown akun (Dashboard, Pengguna, Kategori, Transaksi, Verifikasi). **Tanpa menu Pembelian/Penjualan** (diperbaiki Babak 8 — selaras backend yang menolak admin 403) | seluruh endpoint admin |

Akun Buyer 75 & Seller 30 keduanya punya profil bisnis → keduanya dual
(bisa belanja & jualan) — sesuai desain platform.

## 4. Urutan Demonstrasi yang Disarankan

1. **Beranda (anonim)** — hero, katalog unggulan, cari produk.
2. **Login buyer 75** — tunjukkan dropdown akun & menu Pembelian.
3. **Katalog → detail produk 24** — kartu, badge stok, tambah ke keranjang.
4. **Keranjang → checkout (TANPA menyelesaikan)** — tunjukkan ringkasan; jangan submit (menjaga data demo). Alternatif aman: tunjukkan validasi produk 22 (stok 1, min. beli 2) → error muncul.
5. **Pesanan → detail Order 43** — **siklus penuh completed, paid COD** — tunjukkan timeline status pending → confirmed → processing → shipped → completed. (Contoh pesanan *pending*: Order 42.)
6. **AI Product Recommendation** (buyer) — query bebas.
7. **AI Assistant Standard / Plus** — tanya jawab.
8. **Logout → login seller 30** — badge notifikasi "1" terlihat.
9. **Dashboard Penjual + Produk Saya** — statistik & kelola produk.
10. **Pesanan Masuk → detail order #1** — alur seller.
11. **AI Business Insights** — statistik DB langsung; tekan **"Analisis Bisnis"** → loading → hasil Gemini (butuh beberapa detik); tunjukkan tombol "Analisis Ulang".
12. **Chat** — buka thread buyer–seller.
13. **Logout → login admin 102** — Panel Admin.
14. **Dashboard Admin → Pengguna → Kategori → Transaksi** — read-only.
15. **Verifikasi admin** — list & detail #9 (tampilkan saja; jangan approve/reject).
16. **Penutup** — kembali ke beranda.

## 5. Akun Demo (detail lengkap di `PANDUAN_DEMO.md` §2)

| Peran | ID | Nama akun | Catatan demo |
|---|---|---|---|
| Buyer utama | 75 | Pembeli Uji | Order 43, chat, notifikasi |
| Seller utama | 30 | Stage6 Seller Satu Uji | Produk 22, order #1 (confirmed) & #43 (completed — siklus penuh), badge notif 1 |
| Seller pendukung | 33 | (profil #33) | Order #3 `pending_confirmation` — untuk demo konfirmasi pembayaran |
| Seller alternatif | 76 | Penjual Uji | Produk 52 (stok 108), verifikasi pending (#9) |
| Admin | 102 | Administrator RuralB2B | Panel admin penuh |
| Buyer pendukung | 29 / 32 | Stage6 Buyer Uji | Pemilik order #1–#12 |

- Password seluruh akun demo = password uji standar yang terdokumentasi di
  `PANDUAN_DEMO.md` (tidak dicantumkan di sini).
- **Jangan gunakan akun 91** (pribadi pemilik proyek).
- Admin 102: password admin tidak untuk demo; gunakan sesi yang sudah login.

## 6. Keterbatasan yang Harus Dijelaskan Saat Presentasi

| # | Keterbatasan | Cara menyampaikan |
|---|---|---|
| 1 | Data demo (order #1–43, produk uji) dipertahankan untuk keperluan demo | "Data ini adalah data contoh untuk demonstrasi; produksi memakai database bersih" |
| 2 | Checkout/konfirmasi pembayaran/kirim pesan/approve verifikasi **tidak dieksekusi live** demi menjaga data demo | Tunjukkan form & validasi saja, atau sebutkan "di lingkungan produksi alur ini aktif penuh" |
| 3 | Analisis AI butuh beberapa detik & kuota harian 50 request/akun | Tekan tombol sekali; bila gagal (upstream transien), tekan "Analisis Ulang" — ini juga menunjukkan error handling |
| 4 | Gambar produk memakai placeholder (tabel foto kosong) | "Fitur upload foto tersedia di form produk; data demo belum lengkapi foto" |
| 5 | Notifikasi Telegram: **sudah aktif & teruji end-to-end (Babak 10)** — pengiriman nyata dari UI Admin terkonfirmasi diterima Telegram (message_id 4) | Boleh didemokan: Profil Admin → Integrasi Telegram → Tes Koneksi (tanpa pesan) atau Kirim Pesan Tes (dengan konfirmasi) |
| 6 | Belum production-ready: dev-server Flask, tanpa HTTPS/monitoring; deployment di `DEPLOYMENT.md` | Sampaikan di bagian penutup/roadmap |
| 7 | Produk 22 stok 1 < min. beli 2 → tidak bisa masuk keranjang | Justru tunjukkan sebagai bukti validasi backend |

## 7. Status Akhir Kesiapan Demonstrasi

**✅ SIAP DIDEMOKAN.**

| Aspek | Hasil akhir |
|---|---|
| Pengujian API & workflow | ✅ Babak 1—6: negative test 5/5, guard 34/35, data utuh |
| Pengujian visual browser | ✅ Babak 7: 73 uji (34 rute × 3 lebar), 9 bug diperbaiki |
| Regresi final (Babak 8) | ✅ **73/73 uji browser bersih** (0 console error, 0 API gagal, 0 overflow) |
| Integrasi Telegram | ✅ **Babak 10: aktif & teruji end-to-end** — koneksi `connected` (getMe), pesan tes nyata dari UI Admin diterima (message_id 4), toast hasil tampil, guard 403/401, `telegram_logs` tetap 0 |
| Perbaikan visual (Babak 10) | ✅ Kartu promosi Login putih-di-putih diperbaiki (`!bg-rural-900`) + palette `rural` dilengkapi (200/300/700/800); kontras AAA |
| Regresi final Babak 10 | ✅ **34/34** — 3 role × halaman inti × 3 viewport, guard API, backend health |
| AI Business Insights | ✅ On-demand (tombol), loading/error/analisis-ulang teruji nyata; **0 pemanggilan Gemini saat halaman dibuka** |
| Pemisahan role | ✅ Terverifikasi di browser (buyer/seller/dual/admin); backend penentu otorisasi |
| Build produksi | ✅ `npm run build` sukses (`dist/`) |
| Backup & rollback | ✅ DB + source tersedia (`RELEASE_CHECKLIST.md` §4) |

Sisa pekerjaan pasca-demo (bukan penghalang demo): uji build `dist/` disajikan
penuh, deployment produksi (WSGI/HTTPS), dan pembersihan data demo sesuai
`RENCANA_PEMBERSIHAN_DATA_DEMO.md`.
