"""Pengujian pengiriman pesan Telegram nyata (SATU kali, tanpa retry).

Menggunakan fungsi resmi ``_send_message`` dari services/telegram_service.py
(primitif yang sama dipakai notifikasi verifikasi) — bukan mekanisme duplikat.
Tidak menulis ke database. Token tidak pernah dicetak.

AMAN: tanpa argumen ``--kirim``, skrip hanya mencetak rencana pengujian dan
TIDAK mengirim apa pun. Pengiriman nyata hanya terjadi dengan konfirmasi
eksplisit:

    venv\\Scripts\\python.exe telegram_test_message.py --kirim
"""

import sys

sys.path.insert(0, ".")

KONFIRMASI = "--kirim" in sys.argv

PESAN_UJI = (
    "<b>✅ TES NOTIFIKASI RURALB2B BERHASIL!</b>\n\n"
    "Bot Telegram RuralB2B sudah terhubung dan siap mengirim notifikasi sistem.\n\n"
    "Jenis pengujian: Pengiriman pesan langsung.\n"
    "Status: Berhasil."
)


def main() -> int:
    from flask import current_app

    from app import create_app
    from services.telegram_service import _send_message

    app = create_app()
    with app.app_context():
        token = current_app.config.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = current_app.config.get("TELEGRAM_ADMIN_CHAT_ID", "")
        timeout = int(current_app.config.get("TELEGRAM_API_TIMEOUT", 5))

    if not token or not chat_id:
        print("FAILED: TELEGRAM_BOT_TOKEN / chat ID belum terkonfigurasi.")
        return 1

    print(f"Target chat_id : {chat_id}")
    print(f"Panjang pesan  : {len(PESAN_UJI)} karakter (HTML)")
    print(f"Status konfirm : {'--kirim diberikan' if KONFIRMASI else 'TIDAK (tidak ada pesan dikirim)'}")

    if not KONFIRMASI:
        print("\nMenunggu konfirmasi eksplisit. Jalankan:")
        print("    venv\\Scripts\\python.exe telegram_test_message.py --kirim")
        return 0

    # SATU kali kirim; _send_message tidak melakukan retry.
    try:
        message_id = _send_message(token, chat_id, PESAN_UJI, timeout)
    except Exception as exc:
        print("FAILED: pengiriman gagal.")
        print(f"Alasan : {str(exc)[:300]}")
        return 1

    print("SUCCESS: pesan terkirim tepat satu kali.")
    print(f"message_id Telegram: {message_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
