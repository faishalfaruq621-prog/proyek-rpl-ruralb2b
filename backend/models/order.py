"""Model tabel ``orders``.

Satu order hanya dimiliki satu penjual. Checkout keranjang multi-penjual
dipecah menjadi beberapa order berdasarkan ``seller_id``.
"""

from extensions import db


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    order_number = db.Column(db.String(40), nullable=False, unique=True)
    buyer_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    seller_id = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "business_profiles.id", ondelete="RESTRICT", onupdate="CASCADE"
        ),
        nullable=False,
        index=True,
    )
    total_amount = db.Column(db.Numeric(14, 2), nullable=False)
    shipping_address = db.Column(db.Text, nullable=False)
    buyer_note = db.Column(db.Text, nullable=True)
    order_status = db.Column(
        db.Enum(
            "pending",
            "confirmed",
            "processing",
            "shipped",
            "completed",
            "cancelled",
            name="order_status",
        ),
        nullable=False,
        default="pending",
        index=True,
    )
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP"),
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP"),
        server_onupdate=db.text("CURRENT_TIMESTAMP"),
    )

    buyer = db.relationship(
        "User",
        foreign_keys=[buyer_id],
        lazy="select",
    )
    seller = db.relationship(
        "BusinessProfile",
        foreign_keys=[seller_id],
        lazy="select",
    )
    items = db.relationship(
        "OrderItem",
        back_populates="order",
        lazy="select",
        order_by="OrderItem.id",
    )
    payments = db.relationship(
        "Payment",
        back_populates="order",
        lazy="select",
        order_by="Payment.id",
    )
    status_logs = db.relationship(
        "OrderStatusLog",
        back_populates="order",
        lazy="select",
        order_by="OrderStatusLog.id",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "order_number": self.order_number,
            "buyer_id": self.buyer_id,
            "seller_id": self.seller_id,
            "total_amount": float(self.total_amount)
            if self.total_amount is not None
            else None,
            "shipping_address": self.shipping_address,
            "buyer_note": self.buyer_note,
            "order_status": self.order_status,
            "created_at": self.created_at.isoformat()
            if self.created_at
            else None,
            "updated_at": self.updated_at.isoformat()
            if self.updated_at
            else None,
        }

    def __repr__(self) -> str:  # pragma: no cover - bantuan debugging
        return (
            f"<Order {self.id} {self.order_number} "
            f"status={self.order_status}>"
        )
