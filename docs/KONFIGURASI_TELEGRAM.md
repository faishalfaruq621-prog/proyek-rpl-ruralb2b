# Konfigurasi Notifikasi Telegram — RuralB2B

Integrasi Telegram mengirim notifikasi ke admin saat ada aktivitas verifikasi
akun bisnis. Kode integrasi sudah lengkap dan teruji; yang dibutuhkan hanya
konfigurasi token di `backend/.env`.

## 1. Kapan Notifikasi Terkirim

| Peristiwa | Pesan yang dikirim ke admin |
|---|---|
| Pengajuan verifikasi baru (`POST /api/business/verifications`) | "Pengajuan Verifikasi Baru" — ID, nama bisnis, jenis, pemilik, email, telepon, waktu |
| Admin menyetujui verifikasi | "Verifikasi Disetujui" — ID, nama bisnis, waktu |
| Admin menolak verifikasi | "Verifikasi Ditolak" — ID, nama bisnis, alasan, waktu |

## 2. Jaminan Keamanan & Keandalan (sudah diimplementasi di kode)

- **Token tidak pernah bocor**: token hanya dipakai internal untuk memanggil
  Bot API, tidak pernah dikembalikan ke klien, tidak masuk log, dan tidak ada
  di respons API.
- **Non-fatal**: kegagalan Telegram (token salah, jaringan mati, dll.)
  **tidak** menggagalkan proses utama aplikasi — pengajuan/approve/reject
  verifikasi tetap sukses; kegagalan hanya dicatat sebagai log internal.
- **Anti-duplikat**: sebelum kirim, sistem memeriksa `telegram_logs`; pesan
  yang identik & sudah sukses pada pengajuan yang sama tidak dikirim ulang.
- **Audit trail**: setiap upaya kirim tercatat di tabel `telegram_logs`
  (status success/failed + pesan error).

## 3. Langkah Konfigurasi

1. Buat bot via **@BotFather** di Telegram → `/newbot` → salin token yang
   diberikan. **Jangan pernah membagikan token ini ke chat/siapa pun dan
   jangan menuliskannya di dokumen.**
2. Buka `backend/.env`, isi dua variabel berikut:

   ```env
   TELEGRAM_BOT_TOKEN=<token dari BotFather>
   TELEGRAM_CHAT_ID=6830085415
   ```

   (`TELEGRAM_CHAT_ID` sudah terisi. `TELEGRAM_ADMIN_CHAT_ID` adalah nama
   alias lama — cukup salah satu, keduanya dibaca.)
3. **Wajib**: restart backend setelah mengubah `.env`:

   ```powershell
   cd C:\laragon\www\ruralb2b\backend
   venv\Scripts\python.exe app.py
   ```

4. **Satu kali saja**: buka chat dengan bot Anda di Telegram dan kirim pesan
   apa pun (mis. `/start`). Telegram menolak pesan bot ke pengguna yang belum
   pernah menghubungi bot — langkah ini membuka izin kirim ke chat Anda.

## 4. Menguji Koneksi (tanpa mengirim pesan)

```powershell
cd C:\laragon\www\ruralb2b\backend
venv\Scripts\python.exe telegram_test_connection.py
```

Skrip ini memanggil `getMe` — **hanya memvalidasi token, tidak mengirim
pesan apa pun ke chat manapun**. Hasil yang diharapkan:

```
[ok] Koneksi Telegram valid.
     bot : <nama bot> (@<username_bot>)
```

Jika gagal:
- `not_configured` → salah satu variabel belum terisi di `.env`.
- `token_invalid` → token salah/terhapus di BotFather; periksa ulang.
- `network_error` → tidak bisa menjangkau `api.telegram.org` (proxy/firewall).

## 5. Menguji Notifikasi Nyata (end-to-end)

Setelah token terisi dan langkah `/start` dilakukan:

1. Login admin → `/verifikasi/admin` → buka request **#9** (user 76,
   masih pending — dipertahankan khusus untuk demo ini).
2. Tekan **Setujui** (atau **Tolak** dengan alasan).
3. Pesan "Verifikasi Disetujui/Ditolak" akan muncul di Telegram Anda.
4. Notifikasi pengajuan baru otomatis terkirim ketika ada akun yang submit
   verifikasi baru (`/verifikasi` di sisi seller/buyer).

⚠️ Approve/reject **mengubah data** (status verifikasi #9) — lakukan hanya
jika Anda menyetujuinya; setelah diproses, request #9 tidak bisa dipakai
ulang untuk demo yang sama.

## 6. Troubleshooting

| Gejala | Penyebab & solusi |
|---|---|
| Tidak ada pesan masuk, log `failed` "bot blocked" | Anda belum pernah `/start` bot dari akun Telegram tersebut |
| Log `failed` "chat not found" | `TELEGRAM_CHAT_ID` salah; pastikan angka murni tanpa spasi |
| Proses utama tetap jalan meski Telegram gagal | **Memang disengaja** — integrasi non-fatal; detail error ada di tabel `telegram_logs` |
