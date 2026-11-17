"""Model tabel ``products``.

Produk selalu terhubung ke business profile pemilik. Stok disimpan pada
tabel ``inventories``, bukan pada tabel produk.
"""

from extensions import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    business_id = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "business_profiles.id", ondelete="RESTRICT", onupdate="CASCADE"
        ),
        nullable=False,
        index=True,
    )
    category_id = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "categories.id", ondelete="SET NULL", onupdate="CASCADE"
        ),
        nullable=True,
        index=True,
    )
    product_name = db.Column(db.String(180), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(14, 2), nullable=False)
    unit = db.Column(db.String(40), nullable=False)
    minimum_order = db.Column(
        db.Integer,
        nullable=False,
        default=1,
    )
    product_status = db.Column(
        db.Enum(
            "active",
            "inactive",
            "out_of_stock",
            name="product_status",
        ),
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

    business_profile = db.relationship(
        "BusinessProfile",
        back_populates="products",
        lazy="select",
    )
    category = db.relationship(
        "Category",
        back_populates="products",
        lazy="select",
    )
    inventory = db.relationship(
        "Inventory",
        back_populates="product",
        uselist=False,
        lazy="select",
    )
    images = db.relationship(
        "ProductImage",
        back_populates="product",
        lazy="select",
        cascade="all, delete-orphan",
    )

    @property
    def is_active(self) -> bool:
        return self.product_status != "inactive"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "business_id": self.business_id,
            "category_id": self.category_id,
            "product_name": self.product_name,
            "description": self.description,
            "price": float(self.price) if self.price is not None else None,
            "unit": self.unit,
            "minimum_order": self.minimum_order,
            "product_status": self.product_status,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat()
            if self.created_at
            else None,
            "updated_at": self.updated_at.isoformat()
            if self.updated_at
            else None,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Product {self.id} {self.product_name}>"
