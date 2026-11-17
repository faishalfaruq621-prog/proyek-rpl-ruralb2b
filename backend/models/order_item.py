"""Model tabel ``order_items``.

``product_name`` dan ``price_snapshot`` disalin saat checkout agar riwayat
pesanan tidak berubah ketika produk di katalog diperbarui.
"""

from extensions import db


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    order_id = db.Column(
        db.BigInteger,
        db.ForeignKey("orders.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = db.Column(
        db.BigInteger,
        db.ForeignKey("products.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    product_name = db.Column(db.String(180), nullable=False)
    price_snapshot = db.Column(db.Numeric(14, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Numeric(14, 2), nullable=False)

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product", lazy="select")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "price_snapshot": float(self.price_snapshot)
            if self.price_snapshot is not None
            else None,
            "quantity": int(self.quantity),
            "subtotal": float(self.subtotal)
            if self.subtotal is not None
            else None,
        }

    def __repr__(self) -> str:  # pragma: no cover - bantuan debugging
        return f"<OrderItem {self.id} order={self.order_id}>"
