"""Layanan chat AI untuk Chatbot Standard dan Chatbot Plus."""

from __future__ import annotations

import json
from typing import Any

from services.ai_orchestration import AIOrchestration, AIOrchestrationError


class AIChatService:
    """Mengelola percakapan AI untuk chatbot standard dan plus."""

    def __init__(self) -> None:
        self.orchestration = AIOrchestration()

    # ------------------------------------------------------------------
    # Sistem prompt
    # ------------------------------------------------------------------

    @staticmethod
    def _standard_system_prompt(identity_context: dict | None = None) -> str:
        base = (
            "Anda adalah asisten AI untuk RuralB2B, marketplace B2B untuk "
            "UMKM pedesaan Indonesia. Tugas Anda adalah membantu pengguna "
            "memahami dan menggunakan platform RuralB2B.\n\n"
            "Tanggung jawab Anda:\n"
            "1. Menjawab pertanyaan tentang cara menggunakan RuralB2B.\n"
            "2. Membantu mencari dan memahami produk di marketplace.\n"
            "3. Menjelaskan proses pemesanan dan pembayaran.\n"
            "4. Membantu pengguna memahami fitur marketplace.\n"
            "5. Berkomunikasi dalam bahasa Indonesia yang natural dan ramah.\n\n"
        )

        if identity_context:
            base += "Informasi identitas pengguna (dari JWT dan database, jangan diubah):\n"
            base += f"- Status login: {identity_context.get('is_authenticated', False)}\n"
            base += f"- Nama lengkap: {identity_context.get('full_name', '-')}\n"
            base += f"- Role/aktor: {identity_context.get('role', '-')}\n"
            if identity_context.get('business_name'):
                base += f"- Nama usaha: {identity_context['business_name']}\n"
            if identity_context.get('business_type'):
                base += f"- Kategori usaha: {identity_context['business_type']}\n"
            if identity_context.get('verification_status'):
                vs = identity_context['verification_status']
                vs_label = {
                    'pending': 'Menunggu verifikasi',
                    'approved': 'Terverifikasi',
                    'rejected': 'Ditolak',
                    'belum_diajukan': 'Belum mengajukan verifikasi',
                }.get(vs, vs)
                base += f"- Status verifikasi bisnis: {vs_label}\n"
            if identity_context.get('can_buy') is not None:
                base += f"- Dapat membeli produk: {'Ya' if identity_context['can_buy'] else 'Tidak'}\n"
            if identity_context.get('can_sell') is not None:
                base += f"- Dapat menjual produk: {'Ya' if identity_context['can_sell'] else 'Tidak'}\n"
            base += (
                "\nJika pengguna bertanya tentang identitasnya (contoh: 'Siapa saya?', "
                "'Saya terdaftar sebagai apa?', 'Apa peran saya?'), jawab berdasarkan "
                "informasi di atas dengan jujur. Jangan mengarang nama, kategori usaha, "
                "atau status verifikasi jika data tidak tersedia. Jangan memberikan hak "
                "akses tambahan atau mengubah role pengguna. Jelaskan hanya identitas "
                "dan kemampuan yang ada."
            )

        base += (
            "\nPanduan:\n"
            "- Jawablah secara singkat, jelas, dan mudah dipahami.\n"
            "- Jika tidak yakin, jujur sampaikan keterbatasan.\n"
            "- Jangan memberikan komitmen resmi atas nama RuralB2B.\n"
            "- Jangan meminta atau menyimpan data pribadi sensitif pengguna.\n"
            "- Jangan membocorkan email, nomor telepon, password, token, atau dokumen verifikasi.\n"
            "- Selalu bersikap profesional dan sopan."
        )

        return base

    @staticmethod
    def _plus_system_prompt() -> str:
        return (
            "Anda adalah asisten bisnis UMKM untuk RuralB2B. Tugas Anda "
            "adalah membantu penjual UMKM pedesaan menganalisis performa "
            "bisnis mereka dan memberikan rekomendasi strategi.\n\n"
            "Kemampuan Anda:\n"
            "1. Analisis penjualan berdasarkan data transaksi.\n"
            "2. Analisis produk terlaris.\n"
            "3. Analisis performa produk individu.\n"
            "4. Evaluasi harga berdasarkan data yang tersedia.\n"
            "5. Rekomendasi strategi penjualan.\n"
            "6. Analisis tren transaksi.\n"
            "7. Rekomendasi pengembangan usaha.\n\n"
            "Penting:\n"
            "- Semua analisis HARUS berdasarkan data aktual yang tersedia.\n"
            "- Jika data tidak cukup atau tidak tersedia, sampaikan secara jujur.\n"
            "- JANGAN mengarang angka penjualan, keuntungan, atau tren.\n"
            "- Berikan rekomendasi yang praktis dan relevan untuk UMKM pedesaan.\n"
            "- Gunakan bahasa Indonesia yang natural dan mudah dipahami."
        )

    # ------------------------------------------------------------------
    # Chat Standard
    # ------------------------------------------------------------------

    def chat_standard(
        self,
        messages: list[dict[str, str]],
        identity_context: dict | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Chatbot standard untuk pertanyaan umum tentang RuralB2B."""
        if not self.orchestration.is_configured():
            return {
                "success": False,
                "error": "ai_provider_not_configured",
                "message": "Provider AI belum dikonfigurasi. Silakan atur GEMINI_API_KEY atau OPENROUTER_API_KEY di backend.",
            }

        full_messages = [
            {"role": "system", "content": self._standard_system_prompt(identity_context)}
        ]
        full_messages.extend(messages)

        try:
            result = self.orchestration.chat_completion(
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return {
                "success": True,
                "content": result["content"],
                "provider": result["provider"],
                "model": result["model"],
            }
        except AIOrchestrationError as exc:
            return {
                "success": False,
                "error": "ai_provider_error",
                "message": str(exc),
            }

    # ------------------------------------------------------------------
    # Chat Plus (Business Assistant)
    # ------------------------------------------------------------------

    def chat_plus(
        self,
        messages: list[dict[str, str]],
        business_context: dict[str, Any] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Chatbot Plus untuk analisis bisnis UMKM.

        ``business_context`` berisi data aktual bisnis yang akan disertakan
        ke dalam prompt agar AI dapat menganalisis berdasarkan data nyata.
        """
        if not self.orchestration.is_configured():
            return {
                "success": False,
                "error": "ai_provider_not_configured",
                "message": "Provider AI belum dikonfigurasi. Silakan atur GEMINI_API_KEY atau OPENROUTER_API_KEY di backend.",
            }

        system_prompt = self._plus_system_prompt()

        if business_context:
            context_text = "\n\nData bisnis aktual (jangan mengarang angka):\n"
            context_text += json.dumps(business_context, ensure_ascii=False, indent=2)
            system_prompt += context_text
            system_prompt += (
                "\n\nGunakan data di atas untuk menganalisis dan memberikan rekomendasi. "
                "Jika data kosong atau tidak cukup, sampaikan keterbatasan tersebut."
            )

        full_messages = [{"role": "system", "content": system_prompt}]
        full_messages.extend(messages)

        try:
            result = self.orchestration.chat_completion(
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return {
                "success": True,
                "content": result["content"],
                "provider": result["provider"],
                "model": result["model"],
            }
        except AIOrchestrationError as exc:
            return {
                "success": False,
                "error": "ai_provider_error",
                "message": str(exc),
            }
