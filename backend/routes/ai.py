"""Endpoint AI untuk RuralB2B Stage 8.

Semua endpoint memerlukan autentikasi JWT kecuali yang dinyatakan lain.
Data analitik dibatasi berdasarkan business_id pengguna yang login.
"""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from extensions import db
from middleware.auth import token_required, business_user_required
from services.ai_chat_service import AIChatService
from services.ai_orchestration import AIOrchestration
from services.ai_recommendation_service import AIRecommendationService
from services.ai_business_analytics import AIBusinessAnalyticsService
from config import Config
from utils.api_error import ApiError
from utils.request_utils import get_json_body
from utils.rate_limit import ai_rate_limit, ai_strict_rate_limit
from models import VerificationRequest

ai_bp = Blueprint("ai", __name__)

chat_service = AIChatService()
orchestration = AIOrchestration()
recommendation_service = AIRecommendationService()
analytics_service = AIBusinessAnalyticsService()


def _require_ai_configured() -> None:
    if not orchestration.is_configured():
        raise ApiError(
            "Provider AI belum dikonfigurasi. Atur GEMINI_API_KEY atau "
            "OPENROUTER_API_KEY di backend/.env.",
            status_code=503,
            code="ai_provider_not_configured",
        )


# ----------------------------------------------------------------------
# Status / konfigurasi AI
# ----------------------------------------------------------------------

@ai_bp.get("/ai/status")
def ai_status():
    """Mengembalikan status konfigurasi provider AI."""
    return (
        jsonify(
            {
                "success": True,
                "data": {
                    "provider": orchestration.get_provider_name(),
                    "configured": orchestration.is_configured(),
                    "daily_limit": Config.AI_DAILY_LIMIT,
                },
            }
        ),
        200,
    )


# ----------------------------------------------------------------------
# Chatbot Standard
# ----------------------------------------------------------------------

@ai_bp.post("/ai/chat/standard")
@token_required
@ai_strict_rate_limit
def ai_chat_standard():
    """Chatbot standard untuk pertanyaan umum tentang RuralB2B."""
    data = get_json_body()

    messages = data.get("messages")
    if not isinstance(messages, list) or not messages:
        raise ApiError(
            "Field 'messages' (daftar) wajib diisi.",
            status_code=400,
            code="invalid_messages",
        )

    _require_ai_configured()

    temperature = data.get("temperature", 0.7)
    max_tokens = data.get("max_tokens")

    # Bangun konteks identitas dari JWT + database (tidak dipercaya dari frontend)
    user = g.current_user
    is_business_user = user.role == "business_user"

    identity_context = {
        "is_authenticated": True,
        "full_name": user.full_name,
        "role": user.role,
        "can_buy": is_business_user,
        "can_sell": is_business_user,
    }

    profile = user.business_profile
    if profile:
        identity_context["business_name"] = profile.business_name
        identity_context["business_type"] = profile.business_type

        # Cari verifikasi terbaru
        latest_verification = (
            db.session.query(VerificationRequest)
            .filter(VerificationRequest.business_profile_id == profile.id)
            .order_by(VerificationRequest.submitted_at.desc())
            .first()
        )
        if latest_verification:
            identity_context["verification_status"] = latest_verification.status
        else:
            identity_context["verification_status"] = "belum_diajukan"
    else:
        identity_context["business_name"] = None
        identity_context["business_type"] = None
        identity_context["verification_status"] = "belum_diajukan"

    result = chat_service.chat_standard(
        messages=messages,
        identity_context=identity_context,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    status_code = 200 if result.get("success") else 503
    return jsonify(result), status_code


# ----------------------------------------------------------------------
# Chatbot Plus (Business Assistant)
# ----------------------------------------------------------------------

@ai_bp.post("/ai/chat/plus")
@token_required
@ai_strict_rate_limit
def ai_chat_plus():
    """Chatbot Plus untuk analisis bisnis UMKM dengan data aktual."""
    data = get_json_body()

    messages = data.get("messages")
    if not isinstance(messages, list) or not messages:
        raise ApiError(
            "Field 'messages' (daftar) wajib diisi.",
            status_code=400,
            code="invalid_messages",
        )

    _require_ai_configured()

    business_context = data.get("business_context")
    temperature = data.get("temperature", 0.7)
    max_tokens = data.get("max_tokens")

    result = chat_service.chat_plus(
        messages=messages,
        business_context=business_context,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    status_code = 200 if result.get("success") else 503
    return jsonify(result), status_code


# ----------------------------------------------------------------------
# AI Product Recommendation
# ----------------------------------------------------------------------

@ai_bp.post("/ai/recommendations")
@token_required
@ai_rate_limit
def ai_recommendations():
    """Rekomendasi produk berdasarkan kebutuhan pembeli.
    
    Endpoint ini hanya mengakses database, tidak memerlukan AI provider.
    """
    data = get_json_body()

    buyer_need = data.get("buyer_need")
    category_id = data.get("category_id")
    limit = data.get("limit", 10)

    if category_id is not None:
        try:
            category_id = int(category_id)
        except (TypeError, ValueError):
            raise ApiError(
                "category_id harus berupa angka.",
                status_code=400,
                code="invalid_category_id",
            )

    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 10

    if buyer_need:
        result = recommendation_service.recommend_by_need(
            buyer_need=buyer_need,
            limit=limit,
            category_id=category_id,
        )
    else:
        result = recommendation_service.get_all_recommendations(limit=limit)

    status_code = 200 if result.get("success") else 503
    return jsonify(result), status_code


@ai_bp.get("/ai/recommendations/category/<int:category_id>")
@token_required
@ai_rate_limit
def ai_recommendations_by_category(category_id: int):
    """Rekomendasi produk dalam kategori tertentu.
    
    Endpoint ini hanya mengakses database, tidak memerlukan AI provider.
    """
    limit = request.args.get("limit", 10)
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 10

    result = recommendation_service.recommend_by_category(
        category_id=category_id,
        limit=limit,
    )
    return jsonify(result), 200


# ----------------------------------------------------------------------
# AI Business Insights (hanya untuk business_user)
# ----------------------------------------------------------------------

@ai_bp.get("/ai/insights/summary")
@business_user_required
@ai_rate_limit
def ai_business_summary():
    """Ringkasan performa bisnis untuk penjual yang login."""
    user = g.current_user
    profile = user.business_profile
    if not profile:
        raise ApiError(
            "Profil bisnis tidak ditemukan.",
            status_code=404,
            code="business_profile_not_found",
        )

    result = analytics_service.get_business_summary(profile.id)
    status_code = 200 if result.get("success") else 404
    return jsonify(result), status_code


@ai_bp.get("/ai/insights/transactions")
@business_user_required
@ai_rate_limit
def ai_business_transactions():
    """Analisis tren transaksi untuk penjual yang login."""
    user = g.current_user
    profile = user.business_profile
    if not profile:
        raise ApiError(
            "Profil bisnis tidak ditemukan.",
            status_code=404,
            code="business_profile_not_found",
        )

    result = analytics_service.get_transaction_analysis(profile.id)
    return jsonify(result), 200


@ai_bp.get("/ai/insights/products")
@business_user_required
@ai_rate_limit
def ai_business_products():
    """Analisis performa produk untuk penjual yang login."""
    user = g.current_user
    profile = user.business_profile
    if not profile:
        raise ApiError(
            "Profil bisnis tidak ditemukan.",
            status_code=404,
            code="business_profile_not_found",
        )

    result = analytics_service.get_product_performance(profile.id)
    return jsonify(result), 200


@ai_bp.post("/ai/insights/analyze")
@business_user_required
@ai_rate_limit
def ai_business_analyze():
    """Analisis bisnis yang dihasilkan AI berdasarkan data aktual."""
    user = g.current_user
    profile = user.business_profile
    if not profile:
        raise ApiError(
            "Profil bisnis tidak ditemukan.",
            status_code=404,
            code="business_profile_not_found",
        )

    result = analytics_service.get_business_analysis(profile.id)
    status_code = 200 if result.get("success") else 503
    return jsonify(result), status_code
