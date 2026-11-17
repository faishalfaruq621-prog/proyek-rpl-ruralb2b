"""Orchestration layanan AI.

Mengelola pemilihan provider, fallback, dan penanganan gagal provider.
Tidak bergantung langsung pada satu SDK provider.
"""

from __future__ import annotations

from typing import Any

from services.ai_provider import AIProvider, AIProviderError, get_ai_provider


class AIOrchestrationError(Exception):
    """Error yang terkait dengan orchestrasi AI."""


class AIOrchestration:
    """Mengelola pemilihan provider AI dan fallback."""

    def __init__(self) -> None:
        self._provider: AIProvider | None = None

    def _get_provider(self) -> AIProvider:
        if self._provider is None:
            self._provider = get_ai_provider()
        return self._provider

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        fallback: bool = True,
    ) -> dict[str, Any]:
        """Mengirim pesan chat dengan dukungan fallback provider.

        Mengembalikan dict dengan kunci:
            - ``content``: teks balasan dari AI
            - ``provider``: nama provider yang digunakan
            - ``model``: model yang digunakan
        """
        provider = self._get_provider()
        provider_name = provider.__class__.__name__.replace("Provider", "").lower()

        try:
            content = provider.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return {
                "content": content,
                "provider": provider_name,
                "model": provider.model or "default",
            }
        except AIProviderError as exc:
            if not fallback:
                raise AIOrchestrationError(str(exc)) from exc

            # Coba fallback ke provider lain
            fallback_provider_name = (
                "openrouter" if provider_name == "gemini" else "gemini"
            )

            from config import Config

            try:
                if fallback_provider_name == "openrouter":
                    from services.ai_provider import OpenRouterProvider

                    fb_provider = OpenRouterProvider(
                        api_key=Config.OPENROUTER_API_KEY,
                        model=Config.OPENROUTER_MODEL,
                        timeout=Config.AI_REQUEST_TIMEOUT,
                    )
                else:
                    from services.ai_provider import GeminiProvider

                    fb_provider = GeminiProvider(
                        api_key=Config.GEMINI_API_KEY,
                        model=Config.GEMINI_MODEL,
                        timeout=Config.AI_REQUEST_TIMEOUT,
                    )

                content = fb_provider.chat_completion(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return {
                    "content": content,
                    "provider": fallback_provider_name,
                    "model": fb_provider.model or "default",
                }
            except AIProviderError as fb_exc:
                raise AIOrchestrationError(
                    f"Provider utama gagal ({exc}); provider fallback juga gagal ({fb_exc})"
                ) from fb_exc

    def is_configured(self) -> bool:
        """Memeriksa apakah setidaknya satu provider AI terkonfigurasi."""
        from config import Config

        return bool(Config.GEMINI_API_KEY or Config.OPENROUTER_API_KEY)

    def get_provider_name(self) -> str:
        """Mengembalikan nama provider yang sedang aktif."""
        from config import Config

        return Config.AI_PROVIDER or "gemini"
