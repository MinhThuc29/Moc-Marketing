import asyncio
import json
import time
from typing import Optional, Dict, Any, Type
from pydantic import BaseModel

from app.services.ai_providers.base import (
    BaseAIProvider,
    AITextResult,
    AIJsonResult,
    AIHealthResult,
)


class MockAIProvider(BaseAIProvider):
    """
    Mock AI Provider phục vụ kiểm thử, offline development và fallback an toàn.
    Hỗ trợ cấu hình các cờ giả lập:
    - simulate_timeout: Giả lập lỗi timeout
    - simulate_malformed_json: Giả lập kết quả JSON sai cú pháp
    - simulate_transient_failure: Giả lập lỗi tạm thời N lần đầu rồi thành công
    - is_available: Cờ trạng thái sống của provider
    """

    def __init__(
        self,
        model_name: str = "mock-gpt-healthy-v1",
        simulate_timeout: bool = False,
        simulate_malformed_json: bool = False,
        simulate_transient_failure: int = 0,
        is_available: bool = True,
        mock_latency_ms: int = 40,
    ):
        self._provider_name = "MOCK"
        self._model_name = model_name
        self.simulate_timeout = simulate_timeout
        self.simulate_malformed_json = simulate_malformed_json
        self.simulate_transient_failure = simulate_transient_failure
        self.is_available = is_available
        self.mock_latency_ms = mock_latency_ms
        self._failure_counter = 0

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def is_mock(self) -> bool:
        return True

    def _check_availability_and_failures(self):
        if not self.is_available:
            raise RuntimeError("Mock AI Provider is currently unavailable (HTTP 503 Service Unavailable)")

        if self.simulate_timeout:
            raise asyncio.TimeoutError("Mock AI provider request timed out after deadline")

        if self.simulate_transient_failure > 0:
            if self._failure_counter < self.simulate_transient_failure:
                self._failure_counter += 1
                raise RuntimeError(
                    f"Simulated transient error ({self._failure_counter}/{self.simulate_transient_failure}): Upstream 502 Bad Gateway"
                )

    def _estimate_tokens_and_cost(self, prompt: str, output: str) -> tuple[int, int, int, float]:
        p_tokens = max(1, len(prompt) // 4)
        c_tokens = max(1, len(output) // 4)
        t_tokens = p_tokens + c_tokens
        # Ước tính chi phí USD: input $0.15/1M tokens, output $0.60/1M tokens
        cost = round((p_tokens * 0.00000015) + (c_tokens * 0.0000006), 6)
        return p_tokens, c_tokens, t_tokens, cost

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> AITextResult:
        start_time = time.perf_counter()
        if self.mock_latency_ms > 0:
            await asyncio.sleep(self.mock_latency_ms / 1000.0)

        self._check_availability_and_failures()

        # Nội dung mẫu chuẩn phong cách sống xanh Mộc Healthy
        response_text = (
            f"🌿 [Mộc Healthy AI Content]: Dựa trên yêu cầu '{prompt[:60]}...'\n"
            "Bữa ăn dinh dưỡng chuẩn Eat Clean giúp bạn tràn đầy năng lượng mà không lo tăng cân! "
            "100% nguyên liệu tươi sạch, cân bằng calo và tốt cho sức khỏe tim mạch."
        )

        latency = int((time.perf_counter() - start_time) * 1000)
        p_tok, c_tok, t_tok, cost = self._estimate_tokens_and_cost(prompt, response_text)

        return AITextResult(
            text=response_text,
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
        start_time = time.perf_counter()
        if self.mock_latency_ms > 0:
            await asyncio.sleep(self.mock_latency_ms / 1000.0)

        self._check_availability_and_failures()

        if self.simulate_malformed_json:
            raw_text = '{"title": "Mộc Healthy Khuyến Mãi", "items": [1, 2, 3,, missing_quote}'
            latency = int((time.perf_counter() - start_time) * 1000)
            p_tok, c_tok, t_tok, cost = self._estimate_tokens_and_cost(prompt, raw_text)
            # Trả về text hỏng để lớp service hoặc client bắt lỗi JSONDecodeError / ValidationError
            return AIJsonResult(
                parsed_json={},
                raw_text=raw_text,
                prompt_tokens=p_tok,
                completion_tokens=c_tok,
                total_tokens=t_tok,
                estimated_cost_usd=cost,
                latency_ms=latency,
                model_name=self._model_name,
                provider_name=self._provider_name,
            )

        # Tạo JSON cấu trúc mẫu
        default_payload = {
            "title": "Bữa Trưa Xanh Giữ Dáng Mộc Healthy",
            "hook": "Đừng để bữa trưa bận rộn làm hỏng chế độ eat clean của bạn!",
            "body": "Salad Ức Gà Áp Chảo sốt mè rang thanh mát, chỉ 350 kcal nhưng no lâu và giàu protein tự nhiên.",
            "cta": "Bấm đặt ngay trước 10h30 để nhận ưu đãi freeship 5km!",
            "hashtags": ["#MocHealthy", "#EatClean", "#BuaTruaXanh"],
            "confidence_score": 0.95,
            "target_channel": "FACEBOOK",
        }

        # Nếu có schema Pydantic, cố gắng tạo dữ liệu khớp với fields của schema
        if schema and hasattr(schema, "model_fields"):
            mock_data: Dict[str, Any] = {}
            for field_name, field_info in schema.model_fields.items():
                annotation = str(field_info.annotation)
                if "int" in annotation:
                    mock_data[field_name] = 100
                elif "float" in annotation:
                    mock_data[field_name] = 0.95
                elif "bool" in annotation:
                    mock_data[field_name] = True
                elif "list" in annotation.lower() or "List" in annotation:
                    mock_data[field_name] = ["#MocHealthy", "#EatClean"]
                elif "dict" in annotation.lower() or "Dict" in annotation:
                    mock_data[field_name] = {"key": "value"}
                else:
                    mock_data[field_name] = default_payload.get(field_name, f"Giá trị {field_name} Mộc Healthy")
            parsed_data = mock_data
        else:
            parsed_data = default_payload

        raw_text = json.dumps(parsed_data, ensure_ascii=False)
        latency = int((time.perf_counter() - start_time) * 1000)
        p_tok, c_tok, t_tok, cost = self._estimate_tokens_and_cost(prompt, raw_text)

        return AIJsonResult(
            parsed_json=parsed_data,
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
        prompt = f"Phân tích tác vụ '{task}' cho nội dung: {content[:100]}"
        return await self.generate_text(prompt, system_prompt=system_prompt)

    async def health_check(self) -> AIHealthResult:
        start_time = time.perf_counter()
        try:
            self._check_availability_and_failures()
            latency = int((time.perf_counter() - start_time) * 1000) + 5
            return AIHealthResult(
                is_healthy=True,
                provider_name=self._provider_name,
                model_name=self._model_name,
                latency_ms=latency,
                is_mock=True,
                message="Mock AI Provider đang hoạt động ổn định và sẵn sàng phục vụ.",
            )
        except Exception as e:
            latency = int((time.perf_counter() - start_time) * 1000)
            return AIHealthResult(
                is_healthy=False,
                provider_name=self._provider_name,
                model_name=self._model_name,
                latency_ms=latency,
                is_mock=True,
                message=f"Mock AI Provider không khả dụng: {str(e)}",
            )
