"""Integrasi Telegram Bot API untuk notifikasi admin.

Token dan chat ID hanya dibaca dari konfigurasi. Token tidak pernah
dikembalikan ke klien dan tidak pernah dimasukkan ke pesan error.
"""

import html
import json
from urllib import error as urlerror
from urllib import request as urlrequest

from flask import current_app

from extensions import db
from models import TelegramLog

_MAX_MESSAGE_LENGTH = 4000


def _build_message(verification) -> str:
    profile = verification.business_profile
    owner = profile.user if profile is not None else None

    business_name = html.escape(profile.business_name) if profile else "-"
    business_type = html.escape(profile.business_type) if profile else "-"
    owner_name = html.escape(owner.full_name) if owner else "-"
    owner_email = html.escape(owner.email) if owner else "-"
    phone = html.escape(profile.phone) if profile and profile.phone else "-"
    submitted_at = (
        verification.submitted_at.strftime("%Y-%m-%d %H:%M")
        if verification.submitted_at
        else "-"
    )

    text = (
        "<b>Pengajuan Verifikasi Baru</b>\n"
        f"ID: <b>#{verification.id}</b>\n"
        f"Bisnis: <b>{business_name}</b>\n"
        f"Jenis: {business_type}\n"
        f"Pemilik: {owner_name}\n"
        f"Email: {owner_email}\n"
        f"Telepon: {phone}\n"
        f"Diajukan: {submitted_at}\n"
        f"Review: GET /api/admin/verifications/{verification.id}"
    )
    return text[:_MAX_MESSAGE_LENGTH]


def _record_log(
    verification_id: int,
    message: str,
    status: str,
    telegram_message_id: str | None = None,
    error_message: str | None = None,
) -> None:
    try:
        log = TelegramLog(
            verification_id=verification_id,
            message=message,
            delivery_status=status,
            telegram_message_id=telegram_message_id,
            error_message=error_message,
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.error("Gagal menyimpan log notifikasi Telegram")


def _send_message(token: str, chat_id: str, text: str, timeout: int) -> str | None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps(
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
    ).encode("utf-8")
    request = urlrequest.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlrequest.urlopen(request, timeout=timeout) as response:
            body = response.read(8192).decode("utf-8", errors="replace")
    except urlerror.HTTPError as exc:
        description = "Telegram menolak permintaan."
        try:
            error_body = exc.read(2048).decode("utf-8", errors="replace")
            parsed = json.loads(error_body)
            description = parsed.get("description") or description
        except Exception:
            description = f"Telegram HTTP error {exc.code}."
        raise RuntimeError(description) from exc
    except urlerror.URLError as exc:
        raise RuntimeError(f"Network error: {exc.reason}") from exc
    except Exception as exc:
        raise RuntimeError(f"Telegram error: {type(exc).__name__}") from exc

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Respons Telegram tidak valid.") from exc

    if not parsed.get("ok"):
        raise RuntimeError(
            parsed.get("description") or "Telegram mengembalikan status gagal."
        )

    result = parsed.get("result") or {}
    message_id = result.get("message_id")
    return str(message_id) if message_id is not None else None


def test_telegram_connection() -> dict:
    """Menguji koneksi ke Telegram Bot API dengan aman.

    Memanggil endpoint ``getMe`` yang hanya memvalidasi token — TIDAK
    mengirim pesan apa pun ke chat manapun. Token tidak pernah muncul
    pada hasil; hanya status dan nama bot publik (first_name).
    """
    token = current_app.config.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = current_app.config.get("TELEGRAM_ADMIN_CHAT_ID", "")

    if not token or not chat_id:
        return {
            "ok": False,
            "reason": "not_configured",
            "message": "TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID belum dikonfigurasi di backend/.env.",
            "chat_id_set": bool(chat_id),
        }

    timeout = int(current_app.config.get("TELEGRAM_API_TIMEOUT", 5))
    url = f"https://api.telegram.org/bot{token}/getMe"
    request = urlrequest.Request(url, method="GET")

    try:
        with urlrequest.urlopen(request, timeout=timeout) as response:
            body = response.read(8192).decode("utf-8", errors="replace")
        parsed = json.loads(body)
    except urlerror.HTTPError as exc:
        reason = "token_invalid"
        try:
            parsed_err = json.loads(exc.read(2048).decode("utf-8", errors="replace"))
            if parsed_err.get("description"):
                current_app.logger.warning("Telegram getMe ditolak: %s", parsed_err["description"])
        except Exception:
            pass
        return {"ok": False, "reason": reason, "message": "Token ditolak Telegram ( Unauthorized ). Periksa TELEGRAM_BOT_TOKEN.", "chat_id_set": True}
    except urlerror.URLError as exc:
        return {"ok": False, "reason": "network_error", "message": f"Tidak dapat terhubung ke Telegram: {exc.reason}", "chat_id_set": True}
    except Exception as exc:
        return {"ok": False, "reason": "unexpected_error", "message": f"Kesalahan tak terduga: {type(exc).__name__}", "chat_id_set": True}

    if not parsed.get("ok"):
        return {"ok": False, "reason": "api_error", "message": "Telegram mengembalikan status gagal.", "chat_id_set": True}

    result = parsed.get("result") or {}
    return {
        "ok": True,
        "bot_username": result.get("username"),
        "bot_name": result.get("first_name"),
        "chat_id_set": True,
        "message": "Token valid. Bot siap. Kirim pesan apa saja ke bot dari akun Telegram Anda (atau /start) agar bot bisa mengirim balik ke chat ID Anda.",
    }


def notify_admin_new_verification(verification) -> dict:
    """Mengirim notifikasi pengajuan baru tanpa menggagalkan proses utama."""
    return _notify(verification, _build_message(verification))


def _mask_chat_id(chat_id: str) -> str:
    """Menyamarkan chat ID untuk tampilan (mis. 68••••••5415)."""
    if not chat_id:
        return "-"
    if len(chat_id) <= 4:
        return "•" * len(chat_id)
    return f"{chat_id[:2]}{'•' * (len(chat_id) - 6)}{chat_id[-4:]}"


def admin_telegram_status() -> dict:
    """Status integrasi Telegram untuk panel Admin.

    Melakukan pemeriksaan aktual ke Bot API (getMe) — bukan sekadar cek
    token tersedia. Tidak mengirim pesan. Token tidak pernah dikembalikan.
    """
    token = current_app.config.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = current_app.config.get("TELEGRAM_ADMIN_CHAT_ID", "")

    if not token or not chat_id:
        return {
            "configured": False,
            "connection": "not_connected",
            "chat_id_masked": _mask_chat_id(chat_id),
            "bot_username": None,
            "bot_name": None,
            "checked_at": None,
            "message": "TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID belum dikonfigurasi di backend/.env.",
        }

    from datetime import datetime, timezone

    result = test_telegram_connection()
    if result.get("ok"):
        connection = "connected"
    elif result.get("reason") == "network_error":
        connection = "error"
    else:
        connection = "not_connected"

    return {
        "configured": True,
        "connection": connection,
        "chat_id_masked": _mask_chat_id(chat_id),
        "bot_username": result.get("bot_username"),
        "bot_name": result.get("bot_name"),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "message": result.get("message"),
    }


def admin_send_test_message() -> dict:
    """Mengirim TEPAT SATU pesan tes ke chat admin yang terkonfigurasi.

    Memakai primitif resmi ``_send_message`` (yang sama dipakai notifikasi
    verifikasi). Tanpa retry otomatis; satu panggilan API per pemanggilan.
    Tidak menulis ke database. Token tidak pernah dikembalikan.
    """
    token = current_app.config.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = current_app.config.get("TELEGRAM_ADMIN_CHAT_ID", "")

    if not token or not chat_id:
        return {
            "sent": False,
            "reason": "not_configured",
            "message": "TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID belum dikonfigurasi.",
        }

    text = (
        "<b>✅ TES NOTIFIKASI RURALB2B BERHASIL!</b>\n\n"
        "Bot Telegram RuralB2B sudah terhubung dan siap mengirim notifikasi sistem.\n\n"
        "Jenis pengujian: Pengiriman pesan langsung.\n"
        "Status: Berhasil."
    )
    timeout = int(current_app.config.get("TELEGRAM_API_TIMEOUT", 5))

    try:
        message_id = _send_message(token, chat_id, text, timeout)
    except Exception as exc:
        current_app.logger.warning("Pengiriman pesan tes Telegram gagal: %s", str(exc)[:300])
        return {
            "sent": False,
            "reason": "delivery_failed",
            "message": str(exc)[:300],
        }

    return {"sent": True, "message_id": message_id}


def admin_notification_logs(limit: int = 20) -> list[dict]:
    """Riwayat pengiriman notifikasi Telegram (dari tabel telegram_logs).

    Tidak ada data yang direkayasa — hanya baris aktual; jika kosong,
    pemanggil menampilkan empty state. Token tidak pernah termasuk hasil.
    """
    try:
        rows = db.session.scalars(
            db.select(TelegramLog)
            .order_by(TelegramLog.created_at.desc(), TelegramLog.id.desc())
            .limit(limit)
        ).all()
    except Exception:
        db.session.rollback()
        return []

    def _jenis(message: str) -> str:
        if "Pengajuan Verifikasi Baru" in message:
            return "Pengajuan verifikasi baru"
        if "Verifikasi Disetujui" in message:
            return "Verifikasi disetujui"
        if "Verifikasi Ditolak" in message:
            return "Verifikasi ditolak"
        if "TES NOTIFIKASI" in message:
            return "Pesan tes admin"
        return "Notifikasi"

    return [
        {
            "id": row.id,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "jenis": _jenis(row.message or ""),
            "delivery_status": row.delivery_status,
            "error_message": row.error_message,
        }
        for row in rows
    ]


def _build_approved_message(verification) -> str:
    profile = verification.business_profile
    business_name = html.escape(profile.business_name) if profile else "-"
    reviewed_at = (
        verification.reviewed_at.strftime("%Y-%m-%d %H:%M")
        if verification.reviewed_at
        else "-"
    )
    text = (
        "<b>Verifikasi Disetujui</b>\n"
        f"ID: <b>#{verification.id}</b>\n"
        f"Bisnis: <b>{business_name}</b>\n"
        f"Disetujui: {reviewed_at}"
    )
    return text[:_MAX_MESSAGE_LENGTH]


def _build_rejected_message(verification) -> str:
    profile = verification.business_profile
    business_name = html.escape(profile.business_name) if profile else "-"
    reason = html.escape(verification.rejection_reason or "-")
    reviewed_at = (
        verification.reviewed_at.strftime("%Y-%m-%d %H:%M")
        if verification.reviewed_at
        else "-"
    )
    text = (
        "<b>Verifikasi Ditolak</b>\n"
        f"ID: <b>#{verification.id}</b>\n"
        f"Bisnis: <b>{business_name}</b>\n"
        f"Alasan: {reason}\n"
        f"Diproses: {reviewed_at}"
    )
    return text[:_MAX_MESSAGE_LENGTH]


def notify_admin_verification_approved(verification) -> dict:
    """Notifikasi admin ketika pengajuan disetujui (non-fatal)."""
    return _notify(verification, _build_approved_message(verification))


def notify_admin_verification_rejected(verification) -> dict:
    """Notifikasi admin ketika pengajuan ditolak (non-fatal)."""
    return _notify(verification, _build_rejected_message(verification))


def _notify(verification, message: str) -> dict:
    """Mengirim satu pesan Telegram dan mencatat audit log-nya.

    - Tidak pernah melempar exception ke pemanggil; kegagalan Telegram
      tidak boleh menggagalkan proses utama aplikasi.
    - Notifikasi ganda dicegah dengan memeriksa log pengiriman sukses
      untuk pesan yang identik pada pengajuan yang sama.
    """
    token = current_app.config.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = current_app.config.get("TELEGRAM_ADMIN_CHAT_ID", "")

    if not token or not chat_id:
        _record_log(
            verification.id,
            message,
            "failed",
            error_message="Telegram bot token/chat ID belum dikonfigurasi.",
        )
        return {"sent": False, "reason": "not_configured"}

    try:
        existing = db.session.scalar(
            db.select(TelegramLog).where(
                TelegramLog.verification_id == verification.id,
                TelegramLog.delivery_status == "success",
                TelegramLog.message == message,
            ).limit(1)
        )
    except Exception:
        db.session.rollback()
        existing = None
    if existing is not None:
        return {"sent": False, "reason": "already_sent"}

    timeout = int(current_app.config.get("TELEGRAM_API_TIMEOUT", 5))

    try:
        telegram_message_id = _send_message(token, chat_id, message, timeout)
    except Exception as exc:
        error_message = str(exc)[:500]
        _record_log(
            verification.id,
            message,
            "failed",
            error_message=error_message,
        )
        current_app.logger.warning(
            "Notifikasi Telegram gagal untuk verifikasi #%s: %s",
            verification.id,
            error_message,
        )
        return {"sent": False, "reason": "delivery_failed"}

    _record_log(
        verification.id,
        message,
        "success",
        telegram_message_id=telegram_message_id,
    )
    return {"sent": True}
