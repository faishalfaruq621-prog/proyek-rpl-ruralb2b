"""Model tabel ``telegram_logs`` untuk audit pengiriman notifikasi."""

from extensions import db


class TelegramLog(db.Model):
    __tablename__ = "telegram_logs"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    verification_id = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "verification_requests.id", ondelete="RESTRICT", onupdate="CASCADE"
        ),
        nullable=False,
        index=True,
    )
    message = db.Column(db.Text, nullable=False)
    delivery_status = db.Column(
        db.Enum("success", "failed", name="telegram_delivery_status"),
        nullable=False,
    )
    telegram_message_id = db.Column(db.String(80), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    sent_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP"),
    )

    verification = db.relationship(
        "VerificationRequest",
        back_populates="telegram_logs",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "delivery_status": self.delivery_status,
            "telegram_message_id": self.telegram_message_id,
            "error_message": self.error_message,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TelegramLog {self.id} {self.delivery_status}>"
