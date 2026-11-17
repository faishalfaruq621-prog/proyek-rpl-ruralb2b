"""Model tabel ``categories``.

Kategori bersifat opsional pada produk. Relasi parent/child mengikuti
self-reference yang sudah ada pada database.
"""

from extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    parent_id = db.Column(
        db.BigInteger,
        db.ForeignKey("categories.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True,
    )

    parent = db.relationship(
        "Category",
        remote_side=[id],
        back_populates="children",
        lazy="select",
    )
    children = db.relationship(
        "Category",
        back_populates="parent",
        lazy="select",
    )
    products = db.relationship(
        "Product",
        back_populates="category",
        lazy="select",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parent_id": self.parent_id,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Category {self.id} {self.name}>"
