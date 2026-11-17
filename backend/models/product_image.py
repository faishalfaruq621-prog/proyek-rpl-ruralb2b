"""Model tabel ``product_images``.

``image_path`` adalah path relatif terhadap direktori penyimpanan privat dan
tidak boleh diekspos langsung melalui API.
"""

from extensions import db


class ProductImage(db.Model):
    __tablename__ = "product_images"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    product_id = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "products.id", ondelete="CASCADE", onupdate="CASCADE"
        ),
        nullable=False,
        index=True,
    )
    image_path = db.Column(db.String(500), nullable=False)
    is_primary = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP"),
    )

    product = db.relationship("Product", back_populates="images")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "is_primary": bool(self.is_primary),
            "created_at": self.created_at.isoformat()
            if self.created_at
            else None,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ProductImage {self.id} product={self.product_id}>"
