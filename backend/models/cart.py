"""Model tabel ``carts``.

Satu pembeli dapat memiliki riwayat keranjang, tetapi hanya satu keranjang
berstatus ``active`` yang dipakai untuk belanja. Setelah checkout berhasil,
keranjang lama ditandai ``converted``.
"""

from extensions import db


class Cart(db.Model):
    __tablename__ = "carts"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    buyer_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    status = db.Column(
        db.Enum("active", "converted", "abandoned", name="cart_status"),
        nullable=False,
        default="active",
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
    items = db.relationship(
        "CartItem",
        back_populates="cart",
        lazy="select",
        cascade="all, delete-orphan",
        order_by="CartItem.id",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "buyer_id": self.buyer_id,
            "status": self.status,
            "created_at": self.created_at.isoformat()
            if self.created_at
            else None,
            "updated_at": self.updated_at.isoformat()
            if self.updated_at
            else None,
        }

    def __repr__(self) -> str:  # pragma: no cover - bantuan debugging
        return f"<Cart {self.id} buyer={self.buyer_id} status={self.status}>"
