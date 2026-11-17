"""Bootstrap akun admin RuralB2B — AMAN, tanpa password bawaan.

Password TIDAK ditulis di source code. Semua nilai wajib diambil dari
environment variables:

    ADMIN_EMAIL    (wajib) alamat email akun admin
    ADMIN_NAME     (wajib) nama lengkap admin
    ADMIN_PASSWORD (wajib) password minimal 8 karakter (kebijakan sama
                   dengan registrasi: huruf + angka)

Cara pakai (dari folder backend, gunakan venv):

    PowerShell:
        $env:ADMIN_EMAIL="admin@example.com"; $env:ADMIN_NAME="Admin"; $env:ADMIN_PASSWORD="..." ; venv\\Scripts\\python.exe bootstrap_admin.py

Perilaku:
- Jika email belum terdaftar -> buat akun role="admin", status active.
- Jika email sudah terdaftar sebagai admin -> hanya reset password jika
  ADMIN_RESET=1 diset (eksplisit), tanpa mengubah data lain.
- Jika email terdaftar sebagai business_user -> ditolak (menghindari
  peningkatan role tidak disengaja); ubah role manual lewat panel admin.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extensions import db  # noqa: E402
from models import User  # noqa: E402

PASSWORD_RULE_NOTE = "Password minimal 8 karakter dan mengandung huruf serta angka."


def _password_problems(password: str) -> str | None:
    if len(password) < 8:
        return "ADMIN_PASSWORD minimal 8 karakter."
    if not any(char.isdigit() for char in password):
        return "ADMIN_PASSWORD harus mengandung angka."
    if not any(char.isalpha() for char in password):
        return "ADMIN_PASSWORD harus mengandung huruf."
    return None


def main() -> int:
    from app import create_app

    email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
    full_name = os.environ.get("ADMIN_NAME", "").strip()
    password = os.environ.get("ADMIN_PASSWORD", "")
    reset_allowed = os.environ.get("ADMIN_RESET", "").strip() == "1"

    missing = [
        name
        for name, value in (
            ("ADMIN_EMAIL", email),
            ("ADMIN_NAME", full_name),
            ("ADMIN_PASSWORD", password),
        )
        if not value
    ]
    if missing:
        print("[kesalahan] Environment wajib belum lengkap:", ", ".join(missing))
        print(PASSWORD_RULE_NOTE)
        return 2

    problem = _password_problems(password)
    if problem:
        print(f"[kesalahan] {problem}")
        return 2

    app = create_app()
    with app.app_context():
        existing = db.session.scalar(db.select(User).where(User.email == email))

        if existing is None:
            user = User(
                full_name=full_name,
                email=email,
                role="admin",
                account_status="active",
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            print(f"[ok] Admin dibuat: id={user.id} email={user.email}")
            return 0

        if existing.role == "admin":
            if reset_allowed:
                existing.set_password(password)
                db.session.commit()
                print(f"[ok] Password admin id={existing.id} direset (ADMIN_RESET=1).")
            else:
                print(
                    f"[tampa perubahan] Email {email} sudah admin (id={existing.id}). "
                    "Set ADMIN_RESET=1 untuk mengatur ulang password."
                )
            return 0

        print(
            f"[kesalahan] Email {email} sudah terdaftar sebagai business_user "
            f"(id={existing.id}). Role tidak diubah otomatis; gunakan panel admin."
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
