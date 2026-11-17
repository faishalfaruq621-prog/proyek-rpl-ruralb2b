"""Layanan analitik bisnis untuk AI Business Insights.

Semua data dibatasi berdasarkan business_id pengguna yang login.
Tidak ada data palsu; jika data tidak tersedia, keterbatasan disampaikan.
"""

from __future__ import annotations

import json
from typing import Any

from extensions import db
from services.ai_orchestration import AIOrchestration, AIOrchestrationError
from models import Order, OrderItem, Product, Inventory, BusinessProfile


class AIBusinessAnalyticsService:
    """Mengelola analitik bisnis untuk penjual UMKM."""

    def __init__(self) -> None:
        self.orchestration = AIOrchestration()

    @staticmethod
    def _business_analysis_system_prompt() -> str:
        return (
            "Anda adalah analis bisnis AI untuk RuralB2B, marketplace B2B untuk "
            "UMKM pedesaan Indonesia. Tugas Anda adalah menganalisis data bisnis "
            "penjual dan memberikan rekomendasi tindakan yang praktis.\n\n"
            "Kemampuan Anda:\n"
            "1. Evaluasi performa penjualan berdasarkan data transaksi aktual.\n"
            "2. Analisis produk terlaris dan kontribusi masing-masing produk.\n"
            "3. Identifikasi produk dengan performa rendah (stok tersedia tapi belum terjual).\n"
            "4. Evaluasi ketersediaan stok dan risiko kehabisan stok.\n"
            "5. Identifikasi peluang peningkatan penjualan.\n"
            "6. Rekomendasi tindakan bisnis yang realistis untuk UMKM pedesaan.\n\n"
            "PENTING - Integritas Data:\n"
            "- Semua angka (penjualan, pendapatan, stok, jumlah pesanan) HARUS berasal "
            "dari data faktual di bawah. JANGAN mengarang atau memperkirakan angka.\n"
            "- Pisahkan antara FAKTA (data dari database) dan INTERPRETASI (analisis AI).\n"
            "- Jika data kosong atau tidak cukup, sampaikan keterbatasan secara jujur.\n"
            "- JANGAN mencakup data pribadi pelanggan (nama, email, telepon, alamat).\n"
            "- Berikan rekomendasi yang praktis dan relevan untuk UMKM pedesaan Indonesia.\n"
            "- Gunakan bahasa Indonesia yang natural, mudah dipahami, dan profesional.\n"
            "- Format output dengan judul, daftar bullet poin, dan rekomendasi tindakan yang jelas."
        )

    def get_business_summary(
        self, business_id: int
    ) -> dict[str, Any]:
        """Ringkasan performa bisnis untuk satu business profile."""
        # Verifikasi bisnis ada
        business = db.session.get(BusinessProfile, business_id)
        if not business:
            return {
                "success": False,
                "error": "business_not_found",
                "message": "Profil bisnis tidak ditemukan.",
            }

        # Produk milik bisnis
        products = (
            db.session.query(Product)
            .filter(Product.business_id == business_id)
            .all()
        )
        product_ids = [p.id for p in products]

        # Pesanan milik bisnis ini
        orders = (
            db.session.query(Order)
            .filter(Order.seller_id == business_id)
            .all()
        )

        total_orders = len(orders)
        total_revenue = sum(
            float(o.total_amount) for o in orders if o.total_amount
        )
        completed_orders = [
            o for o in orders if o.order_status == "completed"
        ]
        pending_orders = [
            o for o in orders if o.order_status in ("pending", "confirmed")
        ]
        cancelled_orders = [
            o for o in orders if o.order_status == "cancelled"
        ]

        # Produk terlaris (berdasarkan jumlah item terjual)
        product_sales: dict[int, dict[str, Any]] = {}
        for o in orders:
            for item in o.items:
                pid = item.product_id
                qty = int(item.quantity) if item.quantity else 0
                subtotal = (
                    float(item.subtotal) if item.subtotal else 0.0
                )
                if pid not in product_sales:
                    product_sales[pid] = {
                        "product_id": pid,
                        "product_name": "",
                        "total_quantity": 0,
                        "total_revenue": 0.0,
                        "order_count": 0,
                    }
                product_sales[pid]["total_quantity"] += qty
                product_sales[pid]["total_revenue"] += subtotal
                product_sales[pid]["order_count"] += 1

        # Isi nama produk
        for p in products:
            if p.id in product_sales:
                product_sales[p.id]["product_name"] = p.product_name

        top_products = sorted(
            product_sales.values(),
            key=lambda x: x["total_quantity"],
            reverse=True,
        )[:5]

        # Produk yang perlu ditingkatkan (stok tersedia tapi belum terjual)
        low_performance = []
        for p in products:
            inventory = p.inventory
            avail = inventory.available_quantity if inventory else 0
            sold = product_sales.get(p.id, {}).get("total_quantity", 0)
            if avail > 0 and sold == 0 and p.product_status == "active":
                low_performance.append(
                    {
                        "product_id": p.id,
                        "product_name": p.product_name,
                        "price": float(p.price) if p.price else 0,
                        "unit": p.unit,
                        "available_quantity": avail,
                    }
                )

        return {
            "success": True,
            "business_id": business_id,
            "business_name": business.business_name,
            "business_type": business.business_type,
            "summary": {
                "total_products": len(products),
                "total_orders": total_orders,
                "completed_orders": len(completed_orders),
                "pending_orders": len(pending_orders),
                "cancelled_orders": len(cancelled_orders),
                "total_revenue": round(total_revenue, 2),
                "conversion_rate": round(
                    (len(completed_orders) / total_orders * 100)
                    if total_orders > 0 else 0,
                    2,
                ),
            },
            "top_products": top_products,
            "low_performance_products": low_performance,
        }

    def get_transaction_analysis(
        self, business_id: int
    ) -> dict[str, Any]:
        """Analisis tren transaksi untuk bisnis."""
        business = db.session.get(BusinessProfile, business_id)
        if not business:
            return {
                "success": False,
                "error": "business_not_found",
                "message": "Profil bisnis tidak ditemukan.",
            }

        orders = (
            db.session.query(Order)
            .filter(Order.seller_id == business_id)
            .order_by(Order.created_at.asc())
            .all()
        )

        if not orders:
            return {
                "success": True,
                "business_id": business_id,
                "message": "Belum ada data transaksi untuk dianalisis.",
                "transactions": [],
                "monthly_revenue": [],
                "status_distribution": {},
            }

        # Grup per bulan
        monthly: dict[str, dict[str, Any]] = {}
        status_dist: dict[str, int] = {}
        for o in orders:
            month_key = o.created_at.strftime("%Y-%m") if o.created_at else "unknown"
            amount = float(o.total_amount) if o.total_amount else 0.0
            if month_key not in monthly:
                monthly[month_key] = {
                    "month": month_key,
                    "order_count": 0,
                    "revenue": 0.0,
                }
            monthly[month_key]["order_count"] += 1
            monthly[month_key]["revenue"] += amount

            status = o.order_status
            status_dist[status] = status_dist.get(status, 0) + 1

        monthly_revenue = sorted(
            monthly.values(), key=lambda x: x["month"]
        )

        return {
            "success": True,
            "business_id": business_id,
            "total_transactions": len(orders),
            "total_revenue": round(
                sum(float(o.total_amount) for o in orders if o.total_amount), 2
            ),
            "monthly_revenue": [
                {
                    "month": m["month"],
                    "order_count": m["order_count"],
                    "revenue": round(m["revenue"], 2),
                }
                for m in monthly_revenue
            ],
            "status_distribution": status_dist,
        }

    def get_product_performance(
        self, business_id: int
    ) -> dict[str, Any]:
        """Analisis performa setiap produk milik bisnis."""
        products = (
            db.session.query(Product)
            .filter(Product.business_id == business_id)
            .all()
        )

        if not products:
            return {
                "success": True,
                "business_id": business_id,
                "message": "Belum ada produk untuk dianalisis.",
                "products": [],
            }

        # Kumpulkan data penjualan per produk
        order_items = (
            db.session.query(OrderItem)
            .join(Order, OrderItem.order_id == Order.id)
            .filter(Order.seller_id == business_id)
            .all()
        )

        sales_by_product: dict[int, dict[str, Any]] = {}
        for item in order_items:
            pid = item.product_id
            qty = int(item.quantity) if item.quantity else 0
            subtotal = float(item.subtotal) if item.subtotal else 0.0
            if pid not in sales_by_product:
                sales_by_product[pid] = {
                    "total_quantity": 0,
                    "total_revenue": 0.0,
                    "order_count": 0,
                }
            sales_by_product[pid]["total_quantity"] += qty
            sales_by_product[pid]["total_revenue"] += subtotal
            sales_by_product[pid]["order_count"] += 1

        product_list = []
        for p in products:
            inv = p.inventory
            avail = inv.available_quantity if inv else 0
            sales = sales_by_product.get(p.id, {
                "total_quantity": 0,
                "total_revenue": 0.0,
                "order_count": 0,
            })
            product_list.append(
                {
                    "product_id": p.id,
                    "product_name": p.product_name,
                    "price": float(p.price) if p.price else 0,
                    "unit": p.unit,
                    "status": p.product_status,
                    "available_quantity": avail,
                    "total_sold": sales["total_quantity"],
                    "total_revenue": round(sales["total_revenue"], 2),
                    "order_count": sales["order_count"],
                    "needs_attention": (
                        avail > 0 and sales["total_quantity"] == 0
                        and p.product_status == "active"
                    ),
                }
            )

        # Urutkan berdasarkan total terjual
        product_list.sort(key=lambda x: x["total_sold"], reverse=True)

        return {
            "success": True,
            "business_id": business_id,
            "total_products": len(products),
            "products": product_list,
        }

    def get_business_analysis(self, business_id: int) -> dict[str, Any]:
        """Menghasilkan analisis bisnis yang dihasilkan AI berdasarkan data aktual.

        Menggabungkan statistik dari database sebagai sumber fakta, lalu
        meminta AI untuk memberikan interpretasi dan rekomendasi tindakan.
        """
        # Kumpulkan data faktual dari database
        summary = self.get_business_summary(business_id)
        transactions = self.get_transaction_analysis(business_id)
        products = self.get_product_performance(business_id)

        if not summary.get("success"):
            return summary

        # Bangun konteks fakta (data dari database, tidak boleh diubah AI)
        fact_context = {
            "business_id": business_id,
            "business_name": summary.get("business_name"),
            "business_type": summary.get("business_type"),
            "summary": summary.get("summary"),
            "top_products": summary.get("top_products", []),
            "low_performance_products": summary.get("low_performance_products", []),
            "transactions": transactions.get("transactions", []),
            "monthly_revenue": transactions.get("monthly_revenue", []),
            "status_distribution": transactions.get("status_distribution", {}),
            "products": products.get("products", []),
            "total_products": products.get("total_products", 0),
        }

        # Periksa apakah AI provider terkonfigurasi
        if not self.orchestration.is_configured():
            return {
                "success": False,
                "error": "ai_provider_not_configured",
                "message": "Provider AI belum dikonfigurasi. Atur GEMINI_API_KEY atau OPENROUTER_API_KEY di backend/.env.",
                "facts": fact_context,
            }

        # Bangun prompt dengan data faktual
        system_prompt = self._business_analysis_system_prompt()

        context_text = "\n\nDATA FAKTUAL DARI DATABASE (jangan mengarang angka):\n"
        context_text += json.dumps(fact_context, ensure_ascii=False, indent=2)
        context_text += (
            "\n\nINSTRUKSI:\n"
            "- Semua analisis HARUS berdasarkan data aktual di atas.\n"
            "- Pisahkan antara FAKTA (angka dari database) dan INTERPRETASI (analisis AI).\n"
            "- JANGAN mengarang angka penjualan, keuntungan, atau tren.\n"
            "- Jika data kosong atau tidak cukup, sampaikan keterbatasan secara jujur.\n"
            "- Berikan rekomendasi yang praktis dan relevan untuk UMKM pedesaan Indonesia.\n"
            "- JANGAN mencakup data pribadi pelanggan (nama, email, telepon, dll).\n"
            "- Format output dengan judul, daftar bullet poin, dan rekomendasi tindakan yang jelas."
        )

        full_messages = [
            {"role": "system", "content": system_prompt + context_text},
            {
                "role": "user",
                "content": (
                    "Buatlah analisis bisnis lengkap dan rekomendasi tindakan "
                    "berdasarkan data faktual di atas. Sertakan evaluasi performa "
                    "penjualan, analisis produk terlaris, identifikasi produk dengan "
                    "performa rendah, evaluasi ketersediaan stok, peluang peningkatan "
                    "penjualan, dan rekomendasi tindakan bisnis yang realistis."
                ),
            },
        ]

        try:
            result = self.orchestration.chat_completion(
                messages=full_messages,
                temperature=0.7,
                max_tokens=1500,
            )
            return {
                "success": True,
                "business_id": business_id,
                "analysis": result["content"],
                "provider": result["provider"],
                "model": result["model"],
                "facts": fact_context,
            }
        except AIOrchestrationError as exc:
            return {
                "success": False,
                "error": "ai_provider_error",
                "message": str(exc),
                "facts": fact_context,
            }
