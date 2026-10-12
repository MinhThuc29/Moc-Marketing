import os
from typing import Optional, Dict, Any, List

from app.services.ai_providers.base import BaseAIProvider
from app.services.ai_providers.mock_provider import MockAIProvider
from app.services.ai_providers.gemini_provider import GeminiProvider
from app.services.ai_providers.openai_provider import OpenAIProvider


def get_ai_provider(
    provider_type: Optional[str] = None,
    **kwargs: Any,
) -> BaseAIProvider:
    """
    Factory khởi tạo AI Provider:
    - Nếu không chỉ định provider_type, đọc từ biến môi trường AI_PROVIDER (mặc định 'mock').
    - Hỗ trợ MOCK, GEMINI, OPENAI.
    - Fallback về MockAIProvider an toàn nếu thiếu API key để hệ thống không bao giờ bị dừng đột ngột.
    """
    resolved_type = (provider_type or os.getenv("AI_PROVIDER", "mock")).strip().upper()

    if resolved_type == "GEMINI":
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        if gemini_key:
            return GeminiProvider(**kwargs)
        # Nếu chưa cấu hình key, dùng Mock với thông báo rõ ràng
        return MockAIProvider(model_name="mock-gemini-fallback", **kwargs)

    elif resolved_type == "OPENAI":
        openai_key = os.getenv("OPENAI_API_KEY", "")
        if openai_key:
            return OpenAIProvider(**kwargs)
        return MockAIProvider(model_name="mock-openai-fallback", **kwargs)

    # Mặc định: MOCK
    return MockAIProvider(**kwargs)


def list_supported_providers() -> List[Dict[str, Any]]:
    """Danh sách các nhà cung cấp AI được nền tảng hỗ trợ"""
    active_env_provider = os.getenv("AI_PROVIDER", "mock").upper()
    return [
        {
            "name": "Mộc Healthy AI Sandbox (Mock)",
            "type": "MOCK",
            "default_model": "mock-gpt-healthy-v1",
            "is_active": active_env_provider in ("MOCK", ""),
            "description": "Provider mô phỏng phục vụ phát triển cục bộ và kiểm thử tự động, không tốn chi phí API.",
        },
        {
            "name": "Google Gemini",
            "type": "GEMINI",
            "default_model": os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash"),
            "is_active": active_env_provider == "GEMINI",
            "description": "Mô hình đa phương tiện tốc độ cao từ Google với cửa sổ ngữ cảnh lớn và chi phí tối ưu.",
        },
        {
            "name": "OpenAI / Compatible Endpoint",
            "type": "OPENAI",
            "default_model": os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
            "is_active": active_env_provider == "OPENAI",
            "description": "Mô hình suy luận tiên tiến từ OpenAI hoặc các endpoint tương thích chuẩn vLLM / Groq.",
        },
    ]
