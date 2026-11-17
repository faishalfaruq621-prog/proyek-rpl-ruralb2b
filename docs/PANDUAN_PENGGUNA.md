# Panduan Pengguna RuralB2B

> Manual untuk tiga jenis pengguna: **Pembeli (Buyer)**, **Penjual (Seller)**,
> dan **Admin**. Ditulis sesuai tampilan & fungsi aplikasi saat ini.
> Untuk latihan dengan akun demo, lihat `docs/PANDUAN_DEMO.md`.

## 1. Memulai

1. Buka alamat aplikasi (pengembangan: `http://localhost:5173`).
2. Belum punya akun? Klik **Daftar** di pojok kanan atas, isi data usaha,
   lalu masuk dengan akun baru.
3. Sudah punya akun? Klik **Masuk**, isi email & password.

Setelah masuk, menu di navbar menyesuaikan peran Anda:
- Menu **Pembeli**: Keranjang, Pesanan Saya, Riwayat Transaksi, AI Product
  Recommendation.
- Menu **Penjual**: Dashboard Penjual, Produk Saya, Tambah Produk, Pesanan
  Masuk, Riwayat Penjualan, AI Business Insights.
- Menu bersama: Katalog, AI Assistant, ikon Chat, ikon Notifikasi (dengan
  angka merah bila ada yang belum dibaca), dan menu akun (Profil Bisnis,
  Pengaturan Akun; Panel Admin untuk admin).

## 2. Untuk Pembeli (Buyer)

### 2.1 Mencari dan membeli produk
1. Buka **Katalog**. Gunakan kotak pencarian (mis. "sayuran") atau filter
   harga/urutan.
2. Klik produk untuk melihat **detail**: harga per satuan (box/kg/sak),
   stok, **minimum order**, nama toko, dan deskripsi.
3. Atur jumlah (harus ≥ minimum order dan ≤ stok) lalu klik
   **Tambah ke Keranjang**. Bila jumlah kurang dari minimum, sistem menolak
   dengan pesan — sesuaikan jumlah.
4. Buka **Keranjang**, periksa jumlah/subtotal, klik **Lanjut ke Checkout**.
5. Di **Checkout**, lengkapi alamat pengiriman dan metode pembayaran,
   lalu klik **Buat Pesanan**. Stok langsung dikurangi dan keranjang kosong.

### 2.2 Membayar pesanan
1. Buka **Pesanan Saya** → klik pesanan (status *pending*, pembayaran
   *unpaid*).
2. Di tab pembayaran, pilih metode, lalu **unggah bukti pembayaran**
   (gambar/PDF, maksimal sesuai batas aplikasi).
3. Status berubah menjadi *menunggu konfirmasi*. Penjual akan memeriksa dan
   mengonfirmasi; setelah dikonfirmasi status pembayaran jadi *paid* dan
   Anda menerima notifikasi.

### 2.3 Menerima barang
1. Setelah penjual mengirim (status *shipped*), buka detail pesanan.
2. Klik **Konfirmasi Penerimaan** saat barang sampai → status menjadi
   *completed*.
3. Bila pesanan masih *pending*, Anda bisa membatalkannya lewat tombol
   **Batalkan**.

### 2.4 Fitur pendukung
- **Chat**: klik ikon chat untuk bertanya ke penjual (percakapan bisa
  dimulai dari halaman produk atau detail pesanan).
- **AI Product Recommendation**: tulis kebutuhan dengan bahasa bebas, mis.
  "saya butuh beras 20 kg untuk warung saya" — sistem merekomendasikan
  produk dari katalog.
- **AI Assistant / Assistant Plus**: tanya apa saja seputar cara berjualan,
  membeli, atau bertransaksi di aplikasi.
- **Notifikasi**: pantau perubahan status pesanan, konfirmasi pembayaran,
  dan pesan baru; tandai dibaca di halaman Notifikasi.
- **Profil Bisnis / Pengaturan Akun**: perbarui data usaha; ganti password
  di Pengaturan Akun.

## 3. Untuk Penjual (Seller)

### 3.1 Menyiapkan toko
1. Lengkapi **Profil Bisnis** (nama usaha, jenis, lokasi, deskripsi).
2. Ajukan **verifikasi bisnis** di halaman Verifikasi: isi formulir dan
   unggah dokumen legalitas. Admin akan meninjau; hasilnya dikirim lewat
   notifikasi. Terverifikasi meningkatkan kepercayaan pembeli.
3. Di **Produk Saya** → **Tambah Produk**: isi nama, deskripsi, harga per
   satuan, **minimum order**, stok, kategori; unggah foto produk.

### 3.2 Mengelola pesanan masuk
1. Buka **Pesanan Masuk** (default menampilkan yang *pending*).
2. Klik pesanan untuk melihat detail: pembeli, produk, jumlah, alamat.
3. Tekan **Konfirmasi Pesanan** bila siap memenuhi (status → *confirmed*),
   lalu saat barang dikirim ubah status menjadi *shipped*.
4. Riwayat penjualan tersimpan di menu **Riwayat Penjualan**.

### 3.3 Mengelola pembayaran
1. Pembeli yang sudah membayar mengunggah bukti; status pembayaran pesanan
   menjadi *menunggu konfirmasi*.
2. Buka detail pesanan, **unduh bukti pembayaran**, cocokkan dengan
   rekening Anda.
3. Klik **Konfirmasi Pembayaran** bila sah (status → *paid*). Pesanan yang
   sudah batal/selesai tidak bisa diubah pembayarannya.

### 3.4 Mengelola stok & melihat performa
- **Kelola stok** dari halaman Produk Saya/Inventori — jaga stok tetap
  di atas minimum order agar produk selalu bisa dipesan.
- **AI Business Insights**: ringkasan performa penjualan, pola transaksi,
  dan analisa produk Anda (butuh akun terverifikasi penggunaan wajar; kuota
  harian berlaku).
- **Chat**: balas pertanyaan pembeli dari ikon chat; pembeli mendapat
  notifikasi atas balasan Anda.

## 4. Untuk Admin

Semua halaman admin berada di bawah menu **Panel Admin** dan hanya bisa
dibuka dengan akun admin.

| Halaman | Isi & aksi |
|---|---|
| `/admin` | Statistik ringkas: jumlah pengguna, produk, transaksi |
| `/admin/pengguna` | Daftar pengguna; ubah status akun (aktif/suspend) |
| `/admin/kategori` | Kelola kategori produk (tambah, ubah, hapus, hierarki) |
| `/admin/transaksi` | Seluruh pesanan platform beserta status & pembayaran |
| `/verifikasi/admin` | Antrean verifikasi bisnis; buka detail untuk melihat dokumen & riwayat; tombol **Setujui** / **Tolak** |

Alur memverifikasi bisnis:
1. Buka antrean verifikasi, pilih pengajuan berstatus *pending*.
2. Periksa data usaha dan **unduh dokumen** yang diunggah.
3. Tekan **Setujui** atau **Tolak** — keputusan tercatat di log audit,
   pemohon menerima notifikasi, dan (bila aktif) admin menerima pemberitahuan
   via Telegram *(aktifkan dengan mengisi `TELEGRAM_BOT_TOKEN` — panduan:
   `docs/KONFIGURASI_TELEGRAM.md`)*.

## 5. Pertanyaan Umum

**Keranjang menolak jumlah saya?** Jumlah harus di antara *minimum order* dan
*stok tersedia* produk tersebut.

**Tidak bisa membeli produk sendiri?** Benar — akun yang sama tidak bisa
menjual & membeli produk miliknya sendiri.

**Sudah bayar tapi status belum berubah?** Pembayaran perlu dikonfirmasi
penjual. Pastikan bukti sudah terunggah; hubungi penjual lewat chat bila
tertunda.

**Notifikasi berbunyi/berangka merah terus?** Buka halaman Notifikasi dan
gunakan *tandai semua dibaca*.

**Kuota AI habis?** Setiap akun dibatasi sejumlah permintaan AI per hari;
coba lagi besok.

**Lupa password?** Gunakan fitur ganti password setelah login, atau hubungi
admin untuk bantuan akun.
