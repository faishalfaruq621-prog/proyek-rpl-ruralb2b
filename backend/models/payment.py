"""Model tabel ``payments``.

Pembayaran tidak memakai payment gateway. Pembeli dapat mengirim informasi
pembayaran untuk dikonfirmasi, dan hanya penjual yang dapat menandai
``paid``. Bukti pembayaran disimpan pada kolom ``proof_file_path`` melalui
endpoint upload yang sudah ada.
"""

from extensions import db


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    order_id = db.Column(
        db.BigInteger,
        db.ForeignKey("orders.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    payment_method = db.Column(db.String(80), nullable=True)
    payment_reference = db.Column(db.String(150), nullable=True)
    payment_status = db.Column(
        db.Enum(
            "unpaid",
            "pending_confirmation",
            "paid",
            "failed",
            "refunded",
            name="payment_status",
        ),
        nullable=False,
        default="unpaid",
        index=True,
    )
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    proof_file_path = db.Column(db.String(500), nullable=True)
    paid_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP"),
    )

    order = db.relationship("Order", back_populates="payments")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "payment_method": self.payment_method,
            "payment_reference": self.payment_reference,
            "payment_status": self.payment_status,
            "amount": float(self.amount) if self.amount is not None else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "created_at": self.created_at.isoformat()
            if self.created_at
            else None,
        }

    def __repr__(self) -> str:  # pragma: no cover - bantuan debugging
        return (
            f"<Payment {self.id} order={self.order_id} "
            f"status={self.payment_status}>"
        )
