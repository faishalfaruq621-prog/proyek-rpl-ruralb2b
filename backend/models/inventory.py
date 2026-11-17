"""Model tabel ``inventories``.

Satu produk memiliki satu baris inventori. Stok tersedia adalah stok total
dikurangi jumlah yang sudah direservasi.
"""

from extensions import db


class Inventory(db.Model):
    __tablename__ = "inventories"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    product_id = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "products.id", ondelete="RESTRICT", onupdate="CASCADE"
        ),
        nullable=False,
        unique=True,
        index=True,
    )
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    reserved_quantity = db.Column(db.Integer, nullable=False, default=0)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP"),
        server_onupdate=db.text("CURRENT_TIMESTAMP"),
    )

    product = db.relationship("Product", back_populates="inventory")

    @property
    def available_quantity(self) -> int:
        return max(int(self.stock_quantity) - int(self.reserved_quantity), 0)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "stock_quantity": int(self.stock_quantity),
            "reserved_quantity": int(self.reserved_quantity),
            "available_quantity": self.available_quantity,
            "in_stock": self.available_quantity > 0,
            "updated_at": self.updated_at.isoformat()
            if self.updated_at
            else None,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Inventory product={self.product_id} stock={self.stock_quantity}>"
