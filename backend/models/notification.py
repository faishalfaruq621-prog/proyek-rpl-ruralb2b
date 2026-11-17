"""Model tabel ``notifications``.

Tabel ini sudah ada di database (kolom lama: title, message,
notification_type, is_read, created_at). Migration 002 menambahkan
``link``, ``dedupe_key``, dan ``read_at`` tanpa menghapus data lama.
``dedupe_key`` mencegah satu aktivitas menciptakan dua notifikasi
untuk pengguna yang sama (UNIQUE (user_id, dedupe_key), NULL diizinkan
berulang).
"""

from extensions import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    title = db.Column(db.String(180), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(60), nullable=False)
    link = db.Column(db.String(255), nullable=True)
    dedupe_key = db.Column(db.String(150), nullable=True)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    read_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP"),
    )

    user = db.relationship("User", back_populates="notifications")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "type": self.notification_type,
            "link": self.link,
            "is_read": bool(self.is_read),
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
        }
