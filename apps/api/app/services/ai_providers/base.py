from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, Type
from pydantic import BaseModel


@dataclass
class AITextResult:
    text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    latency_ms: int
    model_name: str
    provider_name: str


@dataclass
class AIJsonResult:
    parsed_json: Dict[str, Any]
    raw_text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    latency_ms: int
    model_name: str
    provider_name: str


@dataclass
class AIHealthResult:
    is_healthy: bool
    provider_name: str
    model_name: str
    latency_ms: int
    is_mock: bool
    message: str


class BaseAIProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

    @property
    @abstractmethod
    def is_mock(self) -> bool:
        pass

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> AITextResult:
        """Sinh văn bản tự do từ prompt"""
        pass

    @abstractmethod
    async def generate_json(
        self,
        prompt: str,
        schema: Optional[Type[BaseModel]] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1500,
        temperature: float = 0.3,
    ) -> AIJsonResult:
        """Sinh dữ liệu JSON cấu trúc và kiểm tra tính hợp lệ với Pydantic schema nếu có"""
        pass

    @abstractmethod
    async def analyze(
        self,
        content: str,
        task: str,
        system_prompt: Optional[str] = None,
    ) -> AITextResult:
        """Phân tích nội dung và đưa ra nhận định"""
        pass

    @abstractmethod
    async def health_check(self) -> AIHealthResult:
        """Kiểm tra kết nối và độ trễ tới AI Provider"""
        pass
