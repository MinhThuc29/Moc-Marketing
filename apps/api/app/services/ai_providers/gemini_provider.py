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


class GeminiProvider(BaseAIProvider):
    """
    Adapter tích hợp Google Gemini API v1beta qua HTTP REST API Client (httpx).
    Tối ưu cho các mô hình Gemini Flash (gemini-1.5-flash / gemini-2.0-flash).
    """

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_seconds: float = 30.0,
    ):
        self._provider_name = "GEMINI"
        self._api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self._model_name = model_name or os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")
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

    def _get_endpoint(self) -> str:
        return f"{self.BASE_URL}/{self._model_name}:generateContent?key={self._api_key}"

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> AITextResult:
        if not self._api_key:
            raise RuntimeError("GEMINI_API_KEY chưa được cấu hình trong môi trường hệ thống.")

        start_time = time.perf_counter()
        payload: Dict[str, Any] = {
            "contents": [
                {
                    "parts": [{"text": prompt}],
                    "role": "user",
                }
            ],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
            },
        }

        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            resp = await client.post(self._get_endpoint(), json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini API returned HTTP {resp.status_code}: {resp.text}")
            data = resp.json()

        latency = int((time.perf_counter() - start_time) * 1000)

        # Parse output
        text = ""
        candidates = data.get("candidates", [])
        if candidates and "content" in candidates[0]:
            parts = candidates[0]["content"].get("parts", [])
            if parts:
                text = parts[0].get("text", "")

        usage = data.get("usageMetadata", {})
        p_tok = usage.get("promptTokenCount", len(prompt) // 4)
        c_tok = usage.get("candidatesTokenCount", len(text) // 4)
        t_tok = usage.get("totalTokenCount", p_tok + c_tok)
        cost = round((p_tok * 0.000000075) + (c_tok * 0.0000003), 6)

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
            raise RuntimeError("GEMINI_API_KEY chưa được cấu hình trong môi trường hệ thống.")

        start_time = time.perf_counter()
        payload: Dict[str, Any] = {
            "contents": [
                {
                    "parts": [{"text": prompt}],
                    "role": "user",
                }
            ],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
                "responseMimeType": "application/json",
            },
        }

        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            resp = await client.post(self._get_endpoint(), json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini API returned HTTP {resp.status_code}: {resp.text}")
            data = resp.json()

        latency = int((time.perf_counter() - start_time) * 1000)

        raw_text = ""
        candidates = data.get("candidates", [])
        if candidates and "content" in candidates[0]:
            parts = candidates[0]["content"].get("parts", [])
            if parts:
                raw_text = parts[0].get("text", "{}")

        parsed_json: Dict[str, Any] = {}
        try:
            parsed_json = json.loads(raw_text)
        except json.JSONDecodeError as err:
            raise ValueError(f"Gemini JSON response is malformed: {str(err)}. Raw output: {raw_text}")

        usage = data.get("usageMetadata", {})
        p_tok = usage.get("promptTokenCount", len(prompt) // 4)
        c_tok = usage.get("candidatesTokenCount", len(raw_text) // 4)
        t_tok = usage.get("totalTokenCount", p_tok + c_tok)
        cost = round((p_tok * 0.000000075) + (c_tok * 0.0000003), 6)

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
        full_prompt = f"Phân tích tác vụ '{task}' dựa trên nội dung sau:\n\n{content}"
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
                message="GEMINI_API_KEY chưa được thiết lập.",
            )

        try:
            # Thực hiện ping nhẹ bằng generate_text ngắn
            await self.generate_text("Ping", max_tokens=5, temperature=0.0)
            latency = int((time.perf_counter() - start_time) * 1000)
            return AIHealthResult(
                is_healthy=True,
                provider_name=self._provider_name,
                model_name=self._model_name,
                latency_ms=latency,
                is_mock=False,
                message="Google Gemini API kết nối thành công.",
            )
        except Exception as e:
            latency = int((time.perf_counter() - start_time) * 1000)
            return AIHealthResult(
                is_healthy=False,
                provider_name=self._provider_name,
                model_name=self._model_name,
                latency_ms=latency,
                is_mock=False,
                message=f"Lỗi kiểm tra sức khỏe Gemini API: {str(e)}",
            )
