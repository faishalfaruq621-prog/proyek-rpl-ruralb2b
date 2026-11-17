"""Abstraction layer untuk provider AI.

Mendukung multi-provider (Gemini dan OpenRouter) agar fitur AI tidak
bergantung langsung pada satu SDK. Provider dipilih melalui konfigurasi
environment variable ``AI_PROVIDER``.

Nama model tidak di-hardcode; diambil dari environment variable.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any

import urllib.request
import urllib.error


class AIProviderError(Exception):
    """Error yang terkait dengan provider AI."""


class AIProvider(ABC):
    """Antarmuka abstrak untuk semua provider AI."""

    def __init__(self, api_key: str, model: str, timeout: int = 30) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    @abstractmethod
    def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        """Mengirim pesan chat dan mengembalikan teks balasan."""


class GeminiProvider(AIProvider):
    """Provider AI menggunakan Google Gemini REST API."""

    def __init__(self, api_key: str, model: str, timeout: int = 30) -> None:
        super().__init__(api_key, model, timeout)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        if not self.api_key:
            raise AIProviderError("GEMINI_API_KEY belum diatur.")

        model_name = self.model or "gemini-1.5-flash"
        url = (
            f"{self.base_url}/models/{model_name}:generateContent"
            f"?key={self.api_key}"
        )

        # Konversi format pesan ke format Gemini
        contents = []
        system_instruction = None
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                system_instruction = content
                continue
            gemini_role = "model" if role == "assistant" else "user"
            contents.append({"role": gemini_role, "parts": [{"text": content}]})

        payload: dict[str, Any] = {"contents": contents}
        if system_instruction:
            payload["system_instruction"] = {"parts": [{"text": system_instruction}]}

        generation_config: dict[str, Any] = {
            "temperature": temperature,
        }
        if max_tokens is not None:
            generation_config["maxOutputTokens"] = max_tokens
        payload["generationConfig"] = generation_config

        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
        }

        req = urllib.request.Request(
            url, data=body, headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            try:
                err_data = json.loads(exc.read().decode())
                msg = err_data.get("error", {}).get("message", str(exc))
            except Exception:
                msg = str(exc)
            raise AIProviderError(f"Gemini API error: {msg}") from exc
        except Exception as exc:
            raise AIProviderError(f"Gagal menghubungi Gemini: {exc}") from exc

        try:
            candidates = data.get("candidates", [])
            if not candidates:
                raise AIProviderError("Tidak ada respons dari Gemini.")
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise AIProviderError("Respons Gemini kosong.")
            return parts[0].get("text", "")
        except (KeyError, IndexError, TypeError) as exc:
            raise AIProviderError(
                f"Format respons Gemini tidak valid: {exc}"
            ) from exc


class OpenRouterProvider(AIProvider):
    """Provider AI menggunakan OpenRouter REST API."""

    def __init__(self, api_key: str, model: str, timeout: int = 30) -> None:
        super().__init__(api_key, model, timeout)
        self.base_url = "https://openrouter.ai/api/v1"

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        if not self.api_key:
            raise AIProviderError("OPENROUTER_API_KEY belum diatur.")

        model_name = self.model or "openrouter/auto"
        url = f"{self.base_url}/chat/completions"

        payload: dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://ruralb2b.local",
            "X-Title": "RuralB2B AI Assistant",
        }

        req = urllib.request.Request(
            url, data=body, headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            try:
                err_data = json.loads(exc.read().decode())
                msg = err_data.get("error", {}).get("message", str(exc))
            except Exception:
                msg = str(exc)
            raise AIProviderError(f"OpenRouter API error: {msg}") from exc
        except Exception as exc:
            raise AIProviderError(f"Gagal menghubungi OpenRouter: {exc}") from exc

        try:
            choices = data.get("choices", [])
            if not choices:
                raise AIProviderError("Tidak ada respons dari OpenRouter.")
            return choices[0].get("message", {}).get("content", "")
        except (KeyError, IndexError, TypeError) as exc:
            raise AIProviderError(
                f"Format respons OpenRouter tidak valid: {exc}"
            ) from exc


def get_ai_provider() -> AIProvider:
    """Membuat instance provider AI berdasarkan konfigurasi environment.

    Provider dipilih melalui variabel environment ``AI_PROVIDER``
    (nilai: ``gemini`` atau ``openrouter``).
    """
    from config import Config  # import lokal untuk menghindari circular import

    provider_name = Config.AI_PROVIDER or "gemini"

    if provider_name == "openrouter":
        return OpenRouterProvider(
            api_key=Config.OPENROUTER_API_KEY,
            model=Config.OPENROUTER_MODEL,
            timeout=Config.AI_REQUEST_TIMEOUT,
        )

    # Default: Gemini
    return GeminiProvider(
        api_key=Config.GEMINI_API_KEY,
        model=Config.GEMINI_MODEL,
        timeout=Config.AI_REQUEST_TIMEOUT,
    )
