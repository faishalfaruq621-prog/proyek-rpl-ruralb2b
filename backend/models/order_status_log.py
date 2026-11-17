"""Model tabel ``order_status_logs``."""

from extensions import db


class OrderStatusLog(db.Model):
    __tablename__ = "order_status_logs"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    order_id = db.Column(
        db.BigInteger,
        db.ForeignKey("orders.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    changed_by = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True,
    )
    old_status = db.Column(
        db.Enum(
            "pending",
            "confirmed",
            "processing",
            "shipped",
            "completed",
            "cancelled",
            name="order_status",
        ),
        nullable=True,
    )
    new_status = db.Column(
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
    )
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP"),
    )

    order = db.relationship("Order", back_populates="status_logs")
    changed_by_user = db.relationship(
        "User",
        foreign_keys=[changed_by],
        lazy="select",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "changed_by": self.changed_by,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat()
            if self.created_at
            else None,
        }

    def __repr__(self) -> str:  # pragma: no cover - bantuan debugging
        return f"<OrderStatusLog {self.id} order={self.order_id}>"
