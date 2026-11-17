# Daftar Fitur RuralB2B

> Disusun dari implementasi aktual: endpoint di `backend/routes/*` dan halaman
> di `frontend/src/routes/index.jsx`. Setiap fitur mencantumkan endpoint API
> dan halaman yang memakainya.

## 1. Profil & Peran

RuralB2B adalah marketplace **B2B untuk UMKM pedesaan**: pembeli bisnis
(toko/warung/kios) membeli langsung dari produsen desa (petani, nelayan,
pengrajin) dengan harga grosir.

| Peran | Capability | Halaman yang bisa diakses |
|---|---|---|
| Pengunjung | — | Beranda, Katalog, Detail produk, Login, Register |
| `business_user` dengan `can_buy` | Pembelian | Keranjang, Checkout, Pesanan saya, Detail pesanan, AI Product Recommendation |
| `business_user` dengan `can_sell` | Penjualan | Dashboard penjual, Produk saya (tambah/edit/kelola), Pesanan masuk, Riwayat penjualan, AI Business Insights, Pengajuan verifikasi |
| Semua akun login | Bersama | Profil bisnis, Dashboard, AI Assistant Standard & Plus, Chat, Notifikasi, Pengaturan akun |
| `admin` | Administrasi | Panel admin: statistik, pengguna, kategori, transaksi, verifikasi bisnis |

Capability `can_buy`/`can_sell` disimpan di `business_profiles` dan
ditegakkan di frontend (`ProtectedRoute capability=...`) **dan** backend
(middleware `@business_user_required` + guard capability).

## 2. Autentikasi & Akun

| Fitur | Endpoint | Halaman |
|---|---|---|
| Registrasi akun bisnis | `POST /auth/register` | `/register` |
| Login (JWT access + refresh) | `POST /auth/login` | `/login` |
| Logout | `POST /auth/logout` | — |
| Profil sesi | `GET /auth/me` | — |
| Ganti password | `POST /auth/change-password` | `/pengaturan-akun` |

- Token disimpan di `localStorage` (`ruralb2b_token`), disisipkan interceptor
  axios; respons 401 membersihkan sesi dan mengarahkan ke `/login`.
- Password di-hash (Werkzeug); tidak ada password plaintext di DB maupun log.

## 3. Profil Bisnis & Verifikasi

| Fitur | Endpoint | Halaman |
|---|---|---|
| Lihat/ubah profil bisnis | `GET/PUT/PATCH /business/profile` | `/profil-bisnis` |
| Ajukan verifikasi bisnis | `POST /business/verifications` | `/verifikasi` |
| Unggah dokumen verifikasi | `POST /business/verifications/:id/documents` | `/verifikasi` |
| Riwayat pengajuan | `GET /business/verifications`, `GET .../:id` | `/verifikasi` |

Alur verifikasi: pengguna mengajukan + mengunggah dokumen (disimpan di folder
privat `storage/verification_documents`, tidak dapat diakses publik) → admin
meninjau di `/verifikasi/admin/:id` → **Setujui/Tolak** → status tersimpan,
log audit tercatat (`verification_logs`), notifikasi in-app terkirim ke
pemohon, dan (bila kredensial terisi) notifikasi Telegram ke admin untuk
pengajuan baru/keputusan.

Verifikasi mempengaruhi kepercayaan: profil terverifikasi ditandai di
katalog/detail toko.

## 4. Katalog & Produk

| Fitur | Endpoint | Halaman |
|---|---|---|
| Katalog publik (pencarian, filter harga, urutan, pagination) | `GET /products` | `/katalog` |
| Detail produk + gambar | `GET /products/:id`, `GET .../images/:imageId/file` | `/produk/:id` |
| Kategori publik | `GET /categories` | filter katalog |
| Tambah/ubah/hapus produk (seller) | `POST /products`, `PUT/PATCH/DELETE /products/:id` | `/produk/tambah`, `/produk/edit/:id` |
| Unggah/hapus gambar produk | `POST /products/:id/images`, `DELETE .../images/:imageId` | `/produk/edit/:id` |
| Kelola produk & inventori | `GET /business/products`, `GET /business/inventory`, `PATCH /business/inventory/:productId` | `/produk/kelola` |

Aturan bisnis yang ditegakkan backend: stok tersimpan di tabel `inventories`
(stok + reserved), **minimum order** per produk (penolakan add-to-cart bila
jumlah < minimum atau melebihi stok), produk hanya bisa dikelola pemiliknya.

## 5. Keranjang & Transaksi

| Fitur | Endpoint | Halaman |
|---|---|---|
| Lihat keranjang | `GET /cart` | `/keranjang` |
| Tambah/ubah/hapus item | `POST /cart/items`, `PATCH/DELETE /cart/items/:itemId` | `/produk/:id`, `/keranjang` |
| Checkout (buat order + kurangi stok) | `POST /orders/checkout` | `/checkout` |
| Daftar & detail pesanan (buyer) | `GET /orders`, `GET /orders/:id` | `/pesanan`, `/pesanan/:id` |
| Batalkan pesanan | `POST /orders/:id/cancel` | `/pesanan/:id` |
| Data pembayaran | `GET /orders/:id/payment` | `/pesanan/:id` |
| Perbarui metode/unggah bukti bayar | `PATCH /orders/:id/payment`, `POST /orders/:id/payment/proof` | `/pesanan/:id` |
| Unduh bukti bayar | `GET /orders/:id/payment/proof/download` (buyer), `GET /seller/orders/:id/payment/proof/download` (seller) | detail pesanan |
| Pesanan masuk (seller) | `GET /seller/orders`, `GET /seller/orders/:id` | `/seller/pesanan` |
| Ubah status pesanan (seller) | `PATCH /seller/orders/:id/status` | `/seller/pesanan/:id` |
| Konfirmasi pembayaran (seller) | `POST /seller/orders/:id/payment/confirm` | `/seller/pesanan/:id` |
| Konfirmasi terima barang (buyer) | `POST /orders/:id/receive` | `/pesanan/:id` |

**Alur status pesanan:** `pending → confirmed → shipped → completed`
(dibatalkan: `cancelled`). Setiap perubahan tercatat di `order_status_logs`
(dengan aktor) dan memicu notifikasi in-app.

**Alur pembayaran:** `unpaid` → buyer mengunggah bukti →
`pending_confirmation` → seller memverifikasi & mengonfirmasi → `paid`.
Bukti pembayaran (PDF/gambar) disimpan di `storage/payment_proofs` (privat).

Pengaman transaksi: pembelian produk sendiri ditolak (409), stok dikunci
saat checkout, pembayaran tidak bisa diubah pada order `cancelled`/
`completed`.

## 6. Chat Antar-Pengguna

| Fitur | Endpoint | Halaman |
|---|---|---|
| Mulai/daftar percakapan | `POST/GET /chat/conversations` | `/chat` |
| Detail percakapan | `GET /chat/conversations/:id` | `/chat/:id` |
| Kirim/daftar pesan | `POST/GET /chat/conversations/:id/messages` | `/chat/:id` |

Percakapan terkait produk atau order; pesan baru memicu notifikasi in-app
("Pesan baru") dengan `dedupe_key` agar tidak dobel.

## 7. Notifikasi

| Fitur | Endpoint | Halaman |
|---|---|---|
| Daftar notifikasi | `GET /notifications` | `/notifikasi` |
| Jumlah belum dibaca (badge navbar) | `GET /notifications/unread-count` | navbar (polling 60 detik) |
| Tandai dibaca / semua dibaca | `PATCH /notifications/read`, `POST /notifications/read-all` | `/notifikasi` |

Jenis notifikasi yang terkirim otomatis: perubahan status pesanan, konfirmasi
pembayaran, pesan chat baru, perubahan status akun, keputusan verifikasi.
Semua notifikasi punya `dedupe_key` (idempoten) dan dicatat `read_at`.

## 8. Fitur AI

Semua fitur AI memakai provider Gemini (`AI_PROVIDER`, kunci via
`GEMINI_API_KEY`), limit harian per pengguna (`AI_DAILY_LIMIT`, default 50),
dan terekam di tabel `ai_recommendations`/`ai_recommendation_items` bila
menghasilkan rekomendasi.

| Fitur | Endpoint | Halaman | Keterangan |
|---|---|---|---|
| AI Assistant Standard | `POST /ai/chat/standard` | `/ai/chat` | Tanya-jawab seputar jual-beli & panduan aplikasi |
| AI Assistant Plus | `POST /ai/chat/plus` | `/ai/chat/plus` | Analisa lebih mendalam untuk keputusan bisnis |
| AI Product Recommendation | `POST /ai/recommendations`, `GET /ai/recommendations/category/:id` | `/ai/recommendations` | Kebutuhan dalam bahasa bebas → rekomendasi produk dari katalog (pencocokan per-kata, bukan sembarangan match substring) |
| AI Business Insights | `GET /ai/insights/summary`, `/transactions`, `/products`, `POST /ai/insights/analyze` | `/ai/insights` | Ringkasan performa penjualan, pola transaksi, dan analisa produk milik seller (hanya capability `can_sell`) |
| Status AI | `GET /ai/status` | — | Konfigurasi & sisa kuota harian |

## 9. Panel Admin

| Fitur | Endpoint |
|---|---|
| Statistik ringkas | `GET /admin/stats` |
| Daftar & kelola pengguna | `GET /admin/users`, `PATCH /admin/users/:id` |
| Kategori (CRUD, hierarki parent) | `GET/POST /admin/categories`, `PATCH/DELETE /admin/categories/:id` |
| Semua transaksi | `GET /admin/orders` |
| Antrean & detail verifikasi | `GET /admin/verifications`, `GET /admin/verifications/:id` |
| Setujui/Tolak verifikasi | `POST /admin/verifications/:id/approve`, `.../reject` |
| Log keputusan verifikasi | `GET /admin/verifications/:id/logs` |
| Log notifikasi Telegram | `GET /admin/verifications/:id/telegram` |

Seluruh endpoint admin dilindungi `@admin_required` (role ≠ admin → HTTP 403)
— 14/14 route terverifikasi.

## 10. Notifikasi Telegram (Opsional)

3 event dikirim ke chat admin: pengajuan verifikasi baru, keputusan
approve/reject, dengan dedupe per event dan **fail-safe** (kegagalan Telegram
tidak pernah menggagalkan transaksi utama; status kirim tercatat di
`telegram_logs`). Konfigurasi via `TELEGRAM_BOT_TOKEN` +
`TELEGRAM_ADMIN_CHAT_ID` di `backend/.env` — tanpa kredensial, aplikasi tetap
berjalan penuh.
