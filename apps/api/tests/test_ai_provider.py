import pytest
from pydantic import BaseModel, Field
from typing import List, Optional


class HealthyRecipeOutput(BaseModel):
    title: str
    calories: int
    protein_grams: float
    ingredients: List[str]
    is_vegan: bool


def test_ai_provider_health_check(client, admin_headers):
    """Kiểm tra health endpoint của AI Provider"""
    res = client.get("/api/v1/ai/health", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("ONLINE", "DEGRADED", "OFFLINE")
    assert "provider" in data
    assert "model" in data
    assert data["latency_ms"] >= 0
    assert data["is_mock"] is True


def test_list_ai_providers(client, admin_headers):
    """Kiểm tra danh sách các providers được hỗ trợ"""
    res = client.get("/api/v1/ai/providers", headers=admin_headers)
    assert res.status_code == 200
    providers = res.json()
    assert len(providers) >= 3
    types = [p["type"] for p in providers]
    assert "MOCK" in types
    assert "GEMINI" in types
    assert "OPENAI" in types


def test_structured_json_success(client, admin_headers):
    """Kiểm tra sinh structured JSON thành công và khớp kiểu dữ liệu"""
    payload = {
        "prompt": "Gợi ý công thức món Salad Ức Gà áp chảo dinh dưỡng.",
        "expect_json": True,
        "temperature": 0.2,
    }
    res = client.post("/api/v1/ai/test-generate", json=payload, headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["json_output"] is not None
    assert isinstance(data["json_output"], dict)
    assert data["prompt_tokens"] > 0
    assert data["completion_tokens"] > 0
    assert data["log_id"] is not None


def test_malformed_json_handling(client, admin_headers):
    """Kiểm tra xử lý khi AI trả về JSON lỗi cú pháp (malformed JSON)"""
    payload = {
        "prompt": "Yêu cầu trả về JSON bị hỏng để kiểm tra resilience.",
        "expect_json": True,
        "simulate_behavior": "malformed_json",
    }
    res = client.post("/api/v1/ai/test-generate", json=payload, headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert data["error_message"] is not None
    assert "JSON" in data["error_message"]

    # Kiểm tra log ghi nhận trạng thái VALIDATION_ERROR
    log_id = data["log_id"]
    log_res = client.get(f"/api/v1/ai/logs/{log_id}", headers=admin_headers)
    assert log_res.status_code == 200
    log_data = log_res.json()
    assert log_data["status"] == "VALIDATION_ERROR"


def test_timeout_handling(client, admin_headers):
    """Kiểm tra xử lý timeout khi AI provider phản hồi quá chậm"""
    payload = {
        "prompt": "Test mô phỏng timeout.",
        "simulate_behavior": "timeout",
    }
    res = client.post("/api/v1/ai/test-generate", json=payload, headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert data["error_message"] is not None
    assert "thời gian" in data["error_message"].lower() or "timeout" in data["error_message"].lower()

    # Kiểm tra log ghi nhận TIMEOUT
    log_id = data["log_id"]
    log_res = client.get(f"/api/v1/ai/logs/{log_id}", headers=admin_headers)
    assert log_res.status_code == 200
    assert log_res.json()["status"] == "TIMEOUT"


def test_transient_error_retry_success(client, admin_headers):
    """Kiểm tra cơ chế retry: lỗi tạm thời 1 lần đầu, tự động thử lại và thành công"""
    payload = {
        "prompt": "Test cơ chế retry tự động với exponential backoff.",
        "simulate_behavior": "retry_success",
    }
    res = client.post("/api/v1/ai/test-generate", json=payload, headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["text_output"] is not None

    # Kiểm tra retry_count trong log = 1
    log_id = data["log_id"]
    log_res = client.get(f"/api/v1/ai/logs/{log_id}", headers=admin_headers)
    assert log_res.status_code == 200
    log_data = log_res.json()
    assert log_data["retry_count"] == 1
    assert log_data["status"] == "SUCCESS"


def test_provider_unavailable_handling(client, admin_headers):
    """Kiểm tra xử lý khi toàn bộ AI provider bị sập (503 Service Unavailable)"""
    payload = {
        "prompt": "Test khi provider không khả dụng.",
        "simulate_behavior": "fail",
    }
    res = client.post("/api/v1/ai/test-generate", json=payload, headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert data["error_message"] is not None

    log_id = data["log_id"]
    log_res = client.get(f"/api/v1/ai/logs/{log_id}", headers=admin_headers)
    assert log_res.status_code == 200
    assert log_res.json()["status"] == "FAILED"


def test_no_raw_pii_guardrail(client, admin_headers):
    """Kiểm tra guardrail bảo vệ quyền riêng tư: Tự động che giấu số điện thoại và email khách hàng"""
    raw_prompt_with_pii = (
        "Khách hàng Nguyễn Văn An, SĐT: 0912345678 và email: nguyenvana@gmail.com "
        "khen salad ngon nhưng giao trễ 10 phút."
    )
    payload = {
        "prompt": raw_prompt_with_pii,
    }
    res = client.post("/api/v1/ai/test-generate", json=payload, headers=admin_headers)
    assert res.status_code == 200
    data = res.json()

    # Dữ liệu prompt đã qua lọc không được chứa SĐT và email thật
    sanitized = data["sanitized_input"]
    assert "0912345678" not in sanitized
    assert "nguyenvana@gmail.com" not in sanitized
    assert "[SĐT_ĐÃ_ẨN]" in sanitized
    assert "[EMAIL_ĐÃ_ẨN]" in sanitized

    # Bản ghi log cũng phải lưu sanitized prompt
    log_id = data["log_id"]
    log_res = client.get(f"/api/v1/ai/logs/{log_id}", headers=admin_headers)
    assert log_res.status_code == 200
    assert "0912345678" not in log_res.json()["input_prompt_sanitized"]


def test_prompt_template_versioning_and_rbac(client, admin_headers):
    """Kiểm tra tạo template, tăng version khi update và kiểm tra RBAC"""
    # 1. Danh sách templates seeded
    res = client.get("/api/v1/ai/templates", headers=admin_headers)
    assert res.status_code == 200
    templates = res.json()["items"]
    assert len(templates) >= 5

    # 2. Tạo template mới
    new_template = {
        "slug": "custom-snack-ad",
        "name": "Quảng cáo snack hạt dinh dưỡng",
        "category": "COPYWRITING",
        "user_prompt_template": "Viết bài giới thiệu {product_name} thơm giòn tự nhiên.",
        "input_variables": ["product_name"],
        "is_active": True,
    }
    create_res = client.post("/api/v1/ai/templates", json=new_template, headers=admin_headers)
    assert create_res.status_code == 201
    tpl_data = create_res.json()
    assert tpl_data["version"] == 1
    tpl_id = tpl_data["id"]

    # 3. Cập nhật và bump version
    update_res = client.put(
        f"/api/v1/ai/templates/{tpl_id}",
        json={"name": "Quảng cáo snack hạt dinh dưỡng V2", "bump_version": True},
        headers=admin_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["version"] == 2

    # 4. Sử dụng template vừa tạo để generate
    gen_res = client.post(
        "/api/v1/ai/test-generate",
        json={
            "prompt": "placeholder",
            "template_slug": "custom-snack-ad",
            "variables": {"product_name": "Granola Yến Mạch Mật Ong"},
        },
        headers=admin_headers,
    )
    assert gen_res.status_code == 200
    assert gen_res.json()["success"] is True

    # 5. Unauthenticated user bị chặn (401)
    unauth_res = client.post("/api/v1/ai/test-generate", json={"prompt": "Hello"})
    assert unauth_res.status_code in (401, 403)
