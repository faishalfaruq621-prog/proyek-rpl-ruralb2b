"""Layanan rekomendasi produk AI untuk pembeli."""

from __future__ import annotations

from typing import Any

from extensions import db
from models import Product, Inventory, BusinessProfile


class AIRecommendationService:
    """Mengelola rekomendasi produk berdasarkan data aktual."""

    def __init__(self) -> None:
        pass

    def get_available_products(
        self,
        limit: int = 100,
        category_id: int | None = None,
        search: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Mengambil produk yang aktif dan tersedia (stok > 0).

        ``search`` dapat berupa satu frasa atau daftar kata kunci; daftar
        dicocokkan memakai OR sehingga cukup salah satu kata yang cocok.
        """
        query = (
            db.session.query(Product, Inventory, BusinessProfile)
            .join(Inventory, Product.id == Inventory.product_id)
            .join(BusinessProfile, Product.business_id == BusinessProfile.id)
            .filter(Product.product_status == "active")
            .filter(Inventory.stock_quantity > Inventory.reserved_quantity)
        )

        if category_id is not None:
            query = query.filter(Product.category_id == category_id)

        if search:
            searches = (
                [search] if isinstance(search, str) else [s for s in search if s]
            )
            from sqlalchemy import or_

            conditions = [
                Product.product_name.ilike(f"%{term}%") for term in searches
            ]
            query = query.filter(or_(*conditions))

        rows = query.limit(limit).all()

        results = []
        for product, inventory, business in rows:
            results.append(
                {
                    "product_id": product.id,
                    "product_name": product.product_name,
                    "description": product.description,
                    "price": float(product.price) if product.price else 0,
                    "unit": product.unit,
                    "category_id": product.category_id,
                    "business_id": business.id,
                    "business_name": business.business_name,
                    "business_type": business.business_type,
                    "available_quantity": inventory.available_quantity,
                    "city": business.city,
                    "province": business.province,
                }
            )
        return results

    #: Kata umum yang tidak berguna sebagai kata kunci pencarian.
    _STOPWORDS = {
        "yang", "untuk", "dan", "atau", "dengan", "saya", "kami", "butuh",
        "ingin", "cari", "mau", "ada", "keperluan", "kebutuhan", "toko",
        "warung", "akan", "dari", "para", "banyak", "sekali",
    }

    def recommend_by_need(
        self,
        buyer_need: str,
        limit: int = 10,
        category_id: int | None = None,
    ) -> dict[str, Any]:
        """Merekomendasikan produk berdasarkan kebutuhan pembeli.

        Mencocokkan kata kunci kebutuhan dengan nama/deskripsi produk dan
        mengembalikan produk yang aktif serta tersedia. Kalimat kebutuhan
        dipecah menjadi kata agar pencarian tidak menuntut kecocokan
        kalimat persis.
        """
        keywords = sorted(
            {
                word
                for word in buyer_need.lower().split()
                if len(word) >= 3 and not any(c.isdigit() for c in word)
                if word not in self._STOPWORDS
            }
        )
        search_terms = keywords or [buyer_need]

        products = self.get_available_products(
            limit=limit * 3, category_id=category_id, search=search_terms
        )

        # Skoring: kata kunci yang muncul di nama bernilai 2, di
        # deskripsi bernilai 1.
        scored = []
        for p in products:
            score = 0
            name_lower = (p["product_name"] or "").lower()
            desc_lower = (p["description"] or "").lower()
            for word in keywords:
                if word in name_lower:
                    score += 2
                if word in desc_lower:
                    score += 1
            scored.append((score, p))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = [p for _, p in scored[:limit]]

        return {
            "success": True,
            "buyer_need": buyer_need,
            "total_found": len(products),
            "recommendations": top,
            "method": "keyword_match_with_availability",
        }

    def recommend_by_category(
        self,
        category_id: int,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Merekomendasikan produk dalam kategori tertentu."""
        products = self.get_available_products(
            limit=limit, category_id=category_id
        )
        return {
            "success": True,
            "category_id": category_id,
            "recommendations": products,
            "method": "category_filter_with_availability",
        }

    def get_all_recommendations(
        self,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Mengambil rekomendasi umum (produk populer/tersedia)."""
        products = self.get_available_products(limit=limit)
        return {
            "success": True,
            "recommendations": products,
            "method": "available_products",
        }
