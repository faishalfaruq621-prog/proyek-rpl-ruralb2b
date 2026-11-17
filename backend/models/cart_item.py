"""Model tabel ``cart_items``.

Tidak ada reservasi stok pada keranjang. Stok divalidasi ulang dan dikurangi
secara atomik saat checkout.
"""

from extensions import db


class CartItem(db.Model):
    __tablename__ = "cart_items"
    __table_args__ = (
        db.UniqueConstraint("cart_id", "product_id", name="uq_cart_product"),
    )

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    cart_id = db.Column(
        db.BigInteger,
        db.ForeignKey("carts.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = db.Column(
        db.BigInteger,
        db.ForeignKey("products.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    quantity = db.Column(db.Integer, nullable=False)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP"),
    )

    cart = db.relationship("Cart", back_populates="items")
    product = db.relationship("Product", lazy="select")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "cart_id": self.cart_id,
            "product_id": self.product_id,
            "quantity": int(self.quantity),
            "created_at": self.created_at.isoformat()
            if self.created_at
            else None,
        }

    def __repr__(self) -> str:  # pragma: no cover - bantuan debugging
        return (
            f"<CartItem {self.id} cart={self.cart_id} "
            f"product={self.product_id}>"
        )
