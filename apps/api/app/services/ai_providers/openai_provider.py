import os
import json
import time
from typing import Optional, Dict, Any, Type
import httpx
from pydantic import BaseModel

from app.services.ai_providers.base import (
    BaseAIProvider,
    AITextResult,
    AIJsonResult,
    AIHealthResult,
)


class OpenAIProvider(BaseAIProvider):
    """
    Adapter tương thích với OpenAI Chat Completions REST API (hoặc OpenAI-compatible endpoints như Groq, Ollama, OpenRouter).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_seconds: float = 30.0,
    ):
        self._provider_name = "OPENAI"
        self._api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self._base_url = (base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self._model_name = model_name or os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
        self.timeout_seconds = timeout_seconds

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def is_mock(self) -> bool:
        return False

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> AITextResult:
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY chưa được cấu hình trong môi trường hệ thống.")

        start_time = time.perf_counter()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self._model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            resp = await client.post(
                f"{self._base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload,
            )
            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI API returned HTTP {resp.status_code}: {resp.text}")
            data = resp.json()

        latency = int((time.perf_counter() - start_time) * 1000)
        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        usage = data.get("usage", {})
        p_tok = usage.get("prompt_tokens", len(prompt) // 4)
        c_tok = usage.get("completion_tokens", len(text) // 4)
        t_tok = usage.get("total_tokens", p_tok + c_tok)
        cost = round((p_tok * 0.00000015) + (c_tok * 0.0000006), 6)

        return AITextResult(
            text=text,
            prompt_tokens=p_tok,
            completion_tokens=c_tok,
            total_tokens=t_tok,
            estimated_cost_usd=cost,
            latency_ms=latency,
            model_name=self._model_name,
            provider_name=self._provider_name,
        )

    async def generate_json(
        self,
        prompt: str,
        schema: Optional[Type[BaseModel]] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1500,
        temperature: float = 0.3,
    ) -> AIJsonResult:
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY chưa được cấu hình trong môi trường hệ thống.")

        start_time = time.perf_counter()
        messages = []
        effective_sys = system_prompt or "You are an AI assistant that only responds in valid JSON format."
        if "JSON" not in effective_sys:
            effective_sys += " You must respond strictly with valid JSON."
        messages.append({"role": "system", "content": effective_sys})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self._model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            resp = await client.post(
                f"{self._base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload,
            )
            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI API returned HTTP {resp.status_code}: {resp.text}")
            data = resp.json()

        latency = int((time.perf_counter() - start_time) * 1000)
        raw_text = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")

        try:
            parsed_json = json.loads(raw_text)
        except json.JSONDecodeError as err:
            raise ValueError(f"OpenAI JSON output is invalid: {str(err)}. Raw output: {raw_text}")

        usage = data.get("usage", {})
        p_tok = usage.get("prompt_tokens", len(prompt) // 4)
        c_tok = usage.get("completion_tokens", len(raw_text) // 4)
        t_tok = usage.get("total_tokens", p_tok + c_tok)
        cost = round((p_tok * 0.00000015) + (c_tok * 0.0000006), 6)

        return AIJsonResult(
            parsed_json=parsed_json,
            raw_text=raw_text,
            prompt_tokens=p_tok,
            completion_tokens=c_tok,
            total_tokens=t_tok,
            estimated_cost_usd=cost,
            latency_ms=latency,
            model_name=self._model_name,
            provider_name=self._provider_name,
        )

    async def analyze(
        self,
        content: str,
        task: str,
        system_prompt: Optional[str] = None,
    ) -> AITextResult:
        full_prompt = f"Phân tích tác vụ '{task}' cho nội dung sau:\n\n{content}"
        return await self.generate_text(full_prompt, system_prompt=system_prompt)

    async def health_check(self) -> AIHealthResult:
        start_time = time.perf_counter()
        if not self._api_key:
            return AIHealthResult(
                is_healthy=False,
                provider_name=self._provider_name,
                model_name=self._model_name,
                latency_ms=0,
                is_mock=False,
                message="OPENAI_API_KEY chưa được cấu hình.",
            )

        try:
            # Gửi tin nhắn ping kiểm tra
            await self.generate_text("Ping", max_tokens=5, temperature=0.0)
            latency = int((time.perf_counter() - start_time) * 1000)
            return AIHealthResult(
                is_healthy=True,
                provider_name=self._provider_name,
                model_name=self._model_name,
                latency_ms=latency,
                is_mock=False,
                message="OpenAI API kết nối thành công.",
            )
        except Exception as e:
            latency = int((time.perf_counter() - start_time) * 1000)
            return AIHealthResult(
                is_healthy=False,
                provider_name=self._provider_name,
                model_name=self._model_name,
                latency_ms=latency,
                is_mock=False,
                message=f"Lỗi kiểm tra OpenAI API: {str(e)}",
            )
