# Panduan Demonstrasi RuralB2B

> Dokumen ini disusun berdasarkan implementasi kode aktual (route frontend di
> `frontend/src/routes/index.jsx`, endpoint backend di `backend/routes/*`,
> data database per 2026-11-11). Credential **tidak** dicantumkan di dokumen
> ini; password seluruh akun demo adalah password uji standar yang terdokumentasi
> pada skrip `test_integration.py` / `test_integration_v2.py` di root proyek.

> ### ⚠️ Update Snapshot Data (2026-11-11, setelah uji alur manual)
> Alur order **sudah pernah didemokan langsung** lewat UI (aksi pengujian
> seller 30, tercatat di `order_status_logs`):
> - **Order 43** (buyer 75): pending → confirmed → processing → shipped →
>   **completed** (23:32–23:33). Pembayaran #42: **paid, COD**. Sekarang menjadi
>   contoh **siklus pesanan lengkap** — tampilkan timeline statusnya di
>   `/pesanan/43`.
> - **Order 1** (buyer 29): pending → **confirmed** (23:32:06). Pembayaran
>   masih unpaid/transfer.
> - **Order 42** (buyer 77, seller 76): masih **pending** — pakai ini sebagai
>   contoh pesanan pending. Pembayarannya sudah paid/transfer (data historis).
> - Distribusi 14 order: 9 pending, 4 confirmed, 1 completed. Stok produk
>   22/24/52 = 1/3/108 (tidak berubah). Verifikasi bisnis #9 (user 76) masih
>   **pending** — aset demo untuk alur approve/reject admin (+ notifikasi
>   Telegram).

## 1. Persiapan Sebelum Demo

```powershell
# Terminal 1 — backend
cd C:\laragon\www\ruralb2b\backend
venv\Scripts\python.exe app.py          # http://127.0.0.1:5000

# Terminal 2 — frontend
cd C:\laragon\www\ruralb2b\frontend
npm run dev                             # http://localhost:5173
```

Verifikasi cepat: buka `http://127.0.0.1:5000/api/health` (harus 200) dan
`http://localhost:5173` (halaman utama tampil). Status AI:
`GET /api/ai/status` → `configured: true` (provider Gemini).

## 2. Akun Demo (hasil audit read-only)

| Peran | User ID | Nama akun | Bisnis | Kenapa dipakai |
|---|---|---|---|---|
| **Buyer utama** | 75 | Pembeli Uji | Toko Uji Pembeli | Login terverifikasi; punya Order 43, percakapan & notifikasi |
| **Seller utama** | 30 | Stage6 Seller Satu Uji | Stage6 Seller Satu Uji (farmer, Bandung) | Login terverifikasi; punya produk 22, order masuk #1 & #43, **1 notifikasi belum dibaca** (badge terlihat) |
| **Seller pendukung** | 33 | Stage6 Seller Satu Uji | profil #33 | Login terverifikasi; order #3 status pembayaran *pending_confirmation* — ideal untuk demo konfirmasi pembayaran |
| **Seller alternatif** | 76 | Penjual Uji | Toko Uji Penjual | Login terverifikasi; produk 52 (stok 108, min. beli 1), verifikasi bisnis **pending** (request #9) |
| **Admin** | 102 | Administrator RuralB2B | — | Panel admin penuh |
| Buyer pendukung | 29 / 32 | Stage6 Buyer Uji | — | Pemilik order #1–#12 (untuk melihat sisi buyer tanpa transaksi baru) |

**Tidak dipakai:** akun 91 (`Faishal`) — akun pribadi pemilik proyek, jangan
digunakan di depan audiens.

### Keterbatasan akun/produk demo (penting diketahui pemesan demo)

| Keterbatasan | Penjelasan | Cara menangani saat demo |
|---|---|---|
| Produk 22 (seller 30) stok 1, min. beli 2 | **Tidak bisa masuk keranjang** — validasi backend menolak | Justru dipakai sebagai momen "validasi berjalan": coba tambah → pesan error muncul |
| Produk 51 milik buyer 75 | Buyer tidak bisa membeli produk sendiri (HTTP 409) | Skip; tidak perlu disinggung kecuali ditanya |
| Order 43 | **Sudah completed** (siklus penuh via uji UI 2026-11-11, paid COD) | Tampilkan timeline lengkapnya di `/pesanan/43` — bukti alur end-to-end. **Jangan diproses/dibatalkan** |
| Semua produk category_id NULL | Filter kategori katalog kosong; rekomendasi AI per-kategori tidak berfungsi untuk produk ini | Demo rekomendasi AI pakai input kata kunci bebas, bukan filter kategori |
| Stok produk 24 = 3 | Checkout qty 2 menyisakan stok 1; mengulang checkout bisa menghabiskan stok | Checkout cukup **satu kali** |

## 3. Skenario Demonstrasi (17 Langkah)

Legenda: 🔄 = langkah **mengubah data demo** (aman, tapi jangan diulang);
👁️ = read-only, bisa diulang bebas.

### Bagian A — Sisi Buyer (±10 menit)

**Langkah 1 — Login Buyer** 👁️
- Halaman: `/login`
- Akun: buyer 75
- Tombol: isi email & password → klik **Masuk**
- Hasil: diarahkan ke beranda; navbar menampilkan menu **Pembeli** (Keranjang,
  Pesanan Saya, Riwayat Transaksi, AI Product Recommendation), ikon chat,
  ikon notifikasi, dan avatar dropdown (Profil Bisnis / Pengaturan Akun).

**Langkah 2 — Buka katalog** 👁️
- Halaman: klik **Katalog** di navbar → `/katalog`
- Tombol: bilah pencarian, filter harga/urutan
- Hasil: 14 produk demo tampil (kartu: nama, harga, satuan, nama toko).
  Catatan: semua produk category NULL → daftar kategori tampil tapi tanpa
  produk per kategori.

**Langkah 3 — Cari produk** 👁️
- Halaman: `/katalog`
- Tombol: ketik mis. `Sayuran` di kotak pencarian
- Hasil: daftar tersaring ke produk berjudul memuat kata tersebut.

**Langkah 4 — Detail produk** 👁️
- Halaman: klik kartu produk → `/produk/24` (Sayuran Test Stage6 A, seller 33,
  Rp 12.000/box, stok 3, min. beli 2)
- Tombol: (di halaman detail) tombol **Tambah ke Keranjang**
- Hasil: informasi produk, toko, stok, minimum order tampil lengkap.
- 💡 Opsional: buka `/produk/22` (seller 30, stok 1) untuk menunjukkan label
  stok terbatas.

**Langkah 5 — Masukkan ke keranjang** 🔄 (sekali saja)
- Halaman: `/produk/24`
- Tombol: atur jumlah = 2 → **Tambah ke Keranjang**
- Hasil: item masuk keranjang; badge/ikon keranjang diperbarui.
- ▶️ Momenn tambahan: di `/produk/22`, coba tambah → **backend menolak**
  (stok 1 < minimum 2) → pesan validasi tampil. Tunjukkan ini sebagai bukti
  aturan bisnis dijalankan server-side.

**Langkah 6 — Checkout** 🔄 (membuat 1 order baru; jangan diulang)
- Halaman: klik **Keranjang** → `/keranjang` → tombol **Lanjut ke Checkout** → `/checkout`
- Akun: buyer 75
- Tombol: isi/verifikasi alamat → **Buat Pesanan**
- Hasil: order baru dibuat (status *pending*, pembayaran *unpaid*), stok
  produk 24 berkurang 2 → tersisa 1, keranjang kosong, diarahkan ke detail
  pesanan.
- 👁️ **Alternatif read-only** (jika tidak ingin mengubah data): buka
  `/pesanan` → klik **Order 42** (`pending`, total Rp 30.000, seller 76)
  sebagai contoh pesanan pending, dan **Order 43** (completed, paid COD)
  untuk menunjukkan siklus lengkap dari data yang sudah ada.

### Bagian B — Sisi Seller (±10 menit)

**Langkah 7 — Login Seller** 👁️
- Logout dari buyer → `/login` dengan akun seller 30
- Hasil: navbar kini menampilkan menu **Penjual** (Dashboard Penjual, Produk
  Saya, Tambah Produk, Pesanan Masuk, Riwayat Penjualan, AI Business Insights).

**Langkah 8 — Pesanan masuk** 👁️
- Halaman: **Pesanan Masuk** → `/seller/pesanan?status=pending`
- Akun: seller 30 → **list pending kini kosong** (order #1 sudah confirmed,
  #43 completed). Tunjukkan tab `confirmed` berisi order #1, lalu
- 👁️ Untuk contoh pesanan masuk yang masih pending: logout → login
  **seller 76** → Pesanan Masuk → order **#42** (pembeli 77, transfer).

**Langkah 9 — Proses pesanan** 🔄 (mengubah status order; jangan diulang)
- Order **#1** **sudah pernah diproses** sampai confirmed lewat uji UI
  (23:32, tercatat di status log) — cukup tampilkan detailnya.
- 👁️ Alternatif read-only: jelaskan alur pending → confirmed → processing →
  shipped → completed langsung dari **timeline Order 43** (buyer 75) yang
  sudah melalui semua status — bukti alur end-to-end yang nyata.
- ⚠️ Jangan memproses order baru; order #42 dibiarkan pending sebagai contoh.

**Langkah 10 — Kelola pembayaran** 🔄 (mengubah pembayaran order #3)
- Login sebagai **seller 33** → **Pesanan Masuk** → order **#3** (pembayar
  sudah upload bukti: status *pending_confirmation*)
- Tombol: buka tab pembayaran → **Konfirmasi Pembayaran**
- Hasil: payment_status → *paid*, buyer menerima notifikasi.
- 👁️ Alternatif read-only: seller 30 melihat order #1 *unpaid* (sudah
  confirmed, menunggu bukti) — jelaskan bahwa buyer mengunggah bukti
  (`PATCH /orders/:id/payment` + upload proof) sebelum seller bisa
  mengonfirmasi. Order #43 sudah melewati tahap ini (paid COD).

### Bagian C — Kembali ke Buyer (±5 menit)

**Langkah 11 — Login kembali sebagai Buyer** 👁️
- `/login` dengan akun buyer 75 → `/pesanan`
- Hasil: daftar pesanan (termasuk order baru dari langkah 6 / Order 43).

**Langkah 12 — Konfirmasi barang diterima** 👁️
- Order 43 **sudah pernah** melalui shipped → completed lewat uji UI
  (buyer 75, 23:33) — tampilkan **timeline lengkapnya** di `/pesanan/43`
  sebagai bukti alur penerimaan yang benar-benar berjalan.
- 👁️ Alternatif: jelaskan tombol **Konfirmasi Penerimaan** di halaman
  `/pesanan/:id` dan status log yang tersimpan.

**Langkah 13 — Chat** 🔄 (mengirim 1 pesan demo)
- Halaman: ikon chat → `/chat` (daftar percakapan; buyer 75 punya 2
  percakapan dengan seller 30: percakapan produk 22 & percakapan Order 43)
- Tombol: buka percakapan → ketik pesan → kirim
- Hasil: pesan tersimpan; seller 30 menerima notifikasi "Pesan baru".

**Langkah 14 — Notifikasi** 👁️
- Login sebagai **seller 30**: ikon notifikasi di navbar menampilkan **badge
  jumlah belum dibaca** (ada 1 notifikasi "Pesan baru" dari langkah 13).
- Halaman: `/notifikasi`
- Tombol: tandai dibaca / tandai semua dibaca
- Hasil: badge berkurang; polling badge berjalan tiap 60 detik.

### Bagian D — Admin & AI (±10 menit)

**Langkah 15 — Login Admin** 👁️
- `/login` dengan akun admin 102 → dropdown avatar memuat **Panel Admin**
- Halaman: `/admin` (statistik pengguna, produk, transaksi).

**Langkah 16 — Kelola data admin** 👁️ (baca; tulis hanya bila diminta)
- `/admin/pengguna` — daftar & ubah status pengguna
- `/admin/kategori` — 8 kategori (CRUD)
- `/admin/transaksi` — semua order (termasuk #1–#12, #42, #43)
- `/verifikasi/admin` — antrean verifikasi: **request #9 pending**
  (Toko Uji Penjual), #10 approved, #11 rejected; buka detail #9 untuk melihat
  dokumen & riwayat log; tombol **Setujui/Tolak** tersedia (jangan ditekan
  kecuali ingin mendemokan alur + notifikasi Telegram bila kredensial terisi).

**Langkah 17 — Fitur AI** 👁️ (konsumsi kuota API Gemini)
- `/ai/chat` — AI Assistant Standard (tanya apa saja seputar jual-beli)
- `/ai/chat/plus` — AI Assistant Plus (analisa lebih dalam)
- Login buyer 75 → `/ai/recommendations` — AI Product Recommendation
  (ketik kebutuhan mis. "saya butuh beras untuk warung" → rekomendasi produk
  dari katalog, berbasis analisa per-kata)
- Login seller 30 → `/ai/insights` — AI Business Insights (ringkasan
  penjualan, analisa transaksi & produk milik seller)
- Catatan: limit harian 50 request/akun (`AI_DAILY_LIMIT`).

## 4. Audit Visual — Status Jujur

**Pengujian browser otomatis SUDAH dilakukan** (Babak 7–8: 73/73 uji Chrome
headless; Babak 9–10: uji UI Telegram, kartu promosi Login, dan regresi final
34/34 — 3 role, 3 viewport). Hasil terverifikasi: 0 console error, 0 API gagal
pada alur baca.

### Checklist pemeriksaan visual manual (lakukan sebelum presentasi)

Jalankan di `http://localhost:5173`, ukuran layar: desktop 1440px, tablet
768px, mobile 375px (DevTools → device toolbar).

| # | Halaman | Yang diperiksa |
|---|---|---|
| 1 | `/` (Beranda) | Hero, kartu fitur, CTA; tidak ada teks terpotong |
| 2 | `/katalog` | Grid kartu rapi; filter & pagination tampil; kartu tanpa gambar tidak merusak layout |
| 3 | `/produk/24` | Informasi stok/min. beli; tombol add-to-cart aktif; error state produk 22 tampil jelas |
| 4 | `/keranjang` & `/checkout` | Tabel item, ubah qty, subtotal; form checkout rapi |
| 5 | `/pesanan` & `/pesanan/:id` | Badge status berwarna; tab pembayaran; tombol upload bukti |
| 6 | `/seller/pesanan` & detail | Tab status; tombol konfirmasi; log status |
| 7 | `/produk/kelola` & `/produk/tambah` | Tabel produk; form tambah validasi wajib |
| 8 | `/chat` & `/chat/:id` | Bubble chat; input; scroll ke bawah otomatis |
| 9 | `/notifikasi` | Badge navbar sinkron; aksi tandai dibaca |
| 10 | `/admin`, `/admin/pengguna`, `/admin/kategori`, `/admin/transaksi` | Tabel muat; aksi inline tidak overflow |
| 11 | `/verifikasi/admin` & detail #9 | Dokumen tampil/bisa diunduh; tombol setujui/tolak |
| 12 | `/ai/chat`, `/ai/chat/plus`, `/ai/recommendations`, `/ai/insights` | Streaming/hasil tampil; loading state |
| 13 | Navbar mobile | Hamburger membuka semua menu sesuai role; badge notifikasi terlihat |
| 14 | Semua halaman | Console browser tanpa error merah; navigasi back/forward wajar |

> Pertahankan identitas visual saat ini — checklist ini untuk menemukan bug,
> bukan dasar redesain.

## 5. Hal yang Belum Teruji End-to-End (sampaikan apa adanya bila ditanya)

1. **Notifikasi Telegram** — ✅ **SUDAH TERUJI END-TO-END (Babak 10)**: token &
   chat ID terkonfigurasi; status koneksi `connected` via getMe; **pengiriman
   nyata dari UI Admin** (Profil → Integrasi Telegram → Kirim Pesan Tes)
   terkonfirmasi diterima Telegram (`message_id 4`; sebelumnya `message_id 3`
   via skrip uji). Notifikasi otomatis verifikasi bisnis memakai jalur yang
   sama — siap didemokan (akan menulis ke `telegram_logs`).
2. **Kebersihan produksi** — database masih berisi data demo (keputusan
   pemilik); rencana pembersihan ada di `docs/RENCANA_PEMBERSIHAN_DATA_DEMO.md`.
