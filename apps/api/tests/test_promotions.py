from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient


def test_list_promotions(client: TestClient, marketing_headers: dict):
    """Kiểm tra danh sách khuyến mãi trả về đầy đủ các chương trình đã seed."""
    response = client.get("/api/v1/promotions", headers=marketing_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 4
    codes = [p["code"] for p in data["items"] if p["code"]]
    assert "WELCOME20" in codes
    assert "FREESHIP" in codes


def test_create_and_update_promotion(client: TestClient, marketing_headers: dict):
    """Kiểm tra tạo mới và cập nhật khuyến mãi kèm validation ngày bắt đầu / kết thúc."""
    now = datetime.now(timezone.utc)

    # 1. Validation error nếu end_at <= start_at
    invalid_payload = {
        "title": "Khuyến mãi lỗi ngày",
        "code": "INVALID_DATE",
        "type": "FIXED_DISCOUNT",
        "value": 20000.0,
        "start_at": (now + timedelta(days=2)).isoformat(),
        "end_at": (now + timedelta(days=1)).isoformat(),
    }
    res_err = client.post("/api/v1/promotions", json=invalid_payload, headers=marketing_headers)
    assert res_err.status_code == 422

    # 2. Tạo khuyến mãi hợp lệ
    valid_payload = {
        "title": "Khuyến mãi test tạo mới",
        "code": f"TEST_CODE_{int(datetime.now().timestamp())}",
        "type": "PERCENT_DISCOUNT",
        "value": 15.0,
        "min_order_value": 150000.0,
        "max_discount": 30000.0,
        "start_at": now.isoformat(),
        "end_at": (now + timedelta(days=10)).isoformat(),
    }
    res_create = client.post("/api/v1/promotions", json=valid_payload, headers=marketing_headers)
    assert res_create.status_code == 201
    created_promo = res_create.json()
    promo_id = created_promo["id"]
    assert created_promo["value"] == 15.0

    # 3. Tạm dừng khuyến mãi (PATCH status)
    res_status = client.patch(
        f"/api/v1/promotions/{promo_id}/status",
        json={"status": "PAUSED"},
        headers=marketing_headers,
    )
    assert res_status.status_code == 200
    assert res_status.json()["status"] == "PAUSED"


def test_percent_discount_with_max_cap(client: TestClient):
    """
    Kiểm tra giảm giá theo phần trăm có áp dụng trần max_discount:
    Voucher WELCOME20: 20%, max 40.000đ, min order 100.000đ.
    Đơn hàng 300.000đ -> 20% là 60.000đ -> Phải giới hạn ở trần 40.000đ!
    """
    payload = {
        "items": [
            {"product_id": "prod-1", "quantity": 3, "unit_price": 100000.0, "name": "Hộp Quà Trái Cây"}
        ],
        "promo_code": "WELCOME20",
        "shipping_fee": 25000.0,
        "is_new_customer": True,
    }
    response = client.post("/api/v1/promotions/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_code_valid"] is True
    assert data["subtotal"] == 300000.0
    assert data["discount_amount"] == 40000.0  # Max cap 40k instead of 60k
    assert data["final_total"] == 285000.0  # 300k - 40k + 25k ship = 285k


def test_fixed_discount_and_min_order_rejection(client: TestClient):
    """
    Kiểm tra giảm cố định HEALTHY30K (giảm 30.000đ cho đơn từ 180.000đ):
    - Đơn 150.000đ: từ chối do chưa đạt min order
    - Đơn 200.000đ: giảm đúng 30.000đ
    """
    # 1. Đơn chưa đạt min order (150.000đ < 180.000đ)
    res_fail = client.post(
        "/api/v1/promotions/calculate",
        json={
            "items": [{"product_id": "prod-1", "quantity": 3, "unit_price": 50000.0}],
            "promo_code": "HEALTHY30K",
            "shipping_fee": 20000.0,
        },
    )
    assert res_fail.status_code == 200
    data_fail = res_fail.json()
    assert data_fail["is_code_valid"] is False
    assert len(data_fail["rejection_reasons"]) > 0
    assert "tối thiểu" in data_fail["rejection_reasons"][0].lower()
    assert data_fail["discount_amount"] == 0.0

    # 2. Đơn đạt min order (200.000đ >= 180.000đ)
    res_ok = client.post(
        "/api/v1/promotions/calculate",
        json={
            "items": [{"product_id": "prod-1", "quantity": 4, "unit_price": 50000.0}],
            "promo_code": "HEALTHY30K",
            "shipping_fee": 20000.0,
        },
    )
    assert res_ok.status_code == 200
    data_ok = res_ok.json()
    assert data_ok["is_code_valid"] is True
    assert data_ok["discount_amount"] == 30000.0
    assert data_ok["final_total"] == 190000.0  # 200k - 30k + 20k ship = 190k


def test_expired_promotion_never_applies(client: TestClient, marketing_headers: dict):
    """Kiểm tra tuyệt đối không bao giờ áp dụng mã đã hết hạn."""
    now = datetime.now(timezone.utc)
    expired_code = f"EXPIRED_{int(datetime.now().timestamp())}"

    # Tạo 1 mã đã hết hạn từ hôm qua
    client.post(
        "/api/v1/promotions",
        json={
            "title": "Voucher Hết Hạn",
            "code": expired_code,
            "type": "PERCENT_DISCOUNT",
            "value": 50.0,
            "start_at": (now - timedelta(days=5)).isoformat(),
            "end_at": (now - timedelta(days=1)).isoformat(),
        },
        headers=marketing_headers,
    )

    # Thử áp dụng mã hết hạn
    response = client.post(
        "/api/v1/promotions/calculate",
        json={
            "items": [{"product_id": "prod-1", "quantity": 2, "unit_price": 60000.0}],
            "promo_code": expired_code,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_code_valid"] is False
    assert any("kết thúc" in r.lower() for r in data["rejection_reasons"])
    assert data["discount_amount"] == 0.0


def test_free_shipping_discount(client: TestClient):
    """
    Kiểm tra FREESHIP (giảm tối đa 30.000đ tiền ship cho đơn từ 120.000đ):
    - Phí ship 25.000đ -> giảm 25.000đ (tiền ship về 0đ)
    - Phí ship 40.000đ -> giảm tối đa 30.000đ (còn 10.000đ tiền ship)
    """
    response = client.post(
        "/api/v1/promotions/calculate",
        json={
            "items": [{"product_id": "p1", "quantity": 3, "unit_price": 50000.0}],  # 150k subtotal
            "promo_code": "FREESHIP",
            "shipping_fee": 40000.0,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_code_valid"] is True
    assert data["shipping_discount"] == 30000.0
    assert data["final_total"] == 160000.0  # 150k + (40k - 30k) = 160k


def test_buy_x_get_y_promotion(client: TestClient, marketing_headers: dict):
    """Kiểm tra khuyến mãi MUA2TANG1 (Mua 2 hộp tặng 1 hộp)."""
    # Lấy thông tin Táo NZ
    prods = client.get("/api/v1/products?search=Táo", headers=marketing_headers).json()["items"]
    tao_prod = next(p for p in prods if "FRUIT-TAO-NZ" in p["sku"])

    response = client.post(
        "/api/v1/promotions/calculate",
        json={
            "items": [
                {
                    "product_id": tao_prod["id"],
                    "quantity": 2,
                    "unit_price": tao_prod["base_price"],
                    "name": tao_prod["name"],
                }
            ],
            "promo_code": "MUA2TANG1",
            "shipping_fee": 0.0,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_code_valid"] is True
    assert len(data["free_items"]) == 1
    gift = data["free_items"][0]
    assert gift["product_id"] == tao_prod["id"]
    assert gift["quantity"] == 1


def test_promotion_rbac_protection(client: TestClient, inventory_headers: dict):
    """Kiểm tra phân quyền: tài khoản Kho (inventory) không có quyền campaign.create sẽ bị 403 khi tạo khuyến mãi."""
    payload = {
        "title": "Khuyến mãi hack",
        "code": "HACK_PROMO",
        "type": "FIXED_DISCOUNT",
        "value": 999999.0,
        "start_at": datetime.now(timezone.utc).isoformat(),
        "end_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
    }
    response = client.post("/api/v1/promotions", json=payload, headers=inventory_headers)
    assert response.status_code == 403
