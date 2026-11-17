"""Service notifikasi dalam aplikasi.

Satu notifikasi tidak dibuat dua kali untuk aktivitas yang sama karena
``dedupe_key`` unik per pengguna (UNIQUE (user_id, dedupe_key)). Gagal
membuat notifikasi tidak pernah menggagalkan aktivitas utama.
"""

from datetime import datetime

from extensions import db
from models import Notification
from utils.api_error import ApiError


def create_notification(
    user_id: int,
    title: str,
    message: str,
    type_: str,
    link: str | None = None,
    dedupe_key: str | None = None,
) -> Notification | None:
    """Membuat satu notifikasi. Idempotent bila dedupe_key sama sudah ada."""
    if user_id is None:
        return None

    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=type_,
        link=link,
        dedupe_key=dedupe_key,
    )
    try:
        db.session.add(notification)
        db.session.flush()
    except Exception:
        # Duplikat dedupe_key atau kegagalan lain dinilai tidak fatal.
        db.session.rollback()
        return None
    return notification


def list_notifications(user, page: int, per_page: int) -> tuple[list, object]:
    statement = (
        db.select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
    )
    pagination = db.paginate(statement, page=page, per_page=per_page, error_out=False)
    items = [notif.to_dict() for notif in pagination.items]
    return items, pagination


def unread_count(user) -> int:
    return int(
        db.session.scalar(
            db.select(db.func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user.id,
                Notification.is_read.is_(False),
            )
        )
        or 0
    )


def notification_summary(user) -> dict:
    return {"unread_count": unread_count(user)}


def mark_read(user, ids: list[int]) -> dict:
    if not isinstance(ids, list):
        raise ApiError(
            "Validasi gagal.",
            status_code=422,
            errors={"ids": "Daftar id harus berupa array."},
        )
    updated = 0
    for notification in db.session.scalars(
        db.select(Notification).where(
            Notification.user_id == user.id,
            Notification.id.in_(ids),
            Notification.is_read.is_(False),
        )
    ):
        notification.is_read = True
        notification.read_at = datetime.now()
        updated += 1
    db.session.commit()
    return {"updated": updated}


def mark_all_read(user) -> dict:
    now = datetime.now()
    updated = db.session.execute(
        db.update(Notification)
        .where(
            Notification.user_id == user.id,
            Notification.is_read.is_(False),
        )
        .values(is_read=True, read_at=now)
        .execution_options(synchronize_session=False)
    ).rowcount
    db.session.commit()
    return {"updated": int(updated or 0)}
