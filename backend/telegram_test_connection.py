"""Pengujian koneksi Telegram (AMAN - tidak mengirim pesan apa pun).

Memanggil getMe untuk memvalidasi TELEGRAM_BOT_TOKEN dan memastikan
TELEGRAM_CHAT_ID terisi. Tidak ada pesan yang dikirim ke chat manapun.

Cara pakai:
    cd backend
    venv\\Scripts\\python.exe telegram_test_connection.py
"""

import sys

sys.path.insert(0, ".")

from app import create_app
from services.telegram_service import test_telegram_connection


def main() -> int:
    app = create_app()
    with app.app_context():
        result = test_telegram_connection()

    if result["ok"]:
        print("[ok] Koneksi Telegram valid.")
        print("     bot :", result.get("bot_name"), f"(@{result.get('bot_username')})")
        print("     chat: chat_id terkonfigurasi")
        print("     CATATAN: bot hanya bisa mengirim ke chat ID Anda SETELAH")
        print("     Anda mengirim pesan apa saja (mis. /start) ke bot dari")
        print("     akun Telegram Anda sekali.")
        return 0

    print("[gagal]", result.get("reason"), "-", result.get("message"))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
