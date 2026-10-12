import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient


def test_tracking_event_ingestion(client: TestClient):
    # 1. Single event ingestion (Public)
    payload = {
        "event_name": "product_view",
        "anonymous_id": "anon_test_12345",
        "session_id": "sess_test_99999",
        "page_url": "https://mochanh.vn/products/tao-new-zealand",
        "referrer": "https://facebook.com",
        "utm_source": "facebook",
        "utm_medium": "cpc",
        "utm_campaign": "autumn_green_2026",
        "event_metadata": {"screen_width": 1920},
    }
    res = client.post("/api/v1/tracking/events", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["event_name"] == "product_view"
    assert data["channel"] == "FACEBOOK"
    assert data["utm_source"] == "facebook"

    # 2. Batch events ingestion
    batch_payload = {
        "events": [
            {
                "event_name": "add_to_cart",
                "anonymous_id": "anon_test_12345",
                "session_id": "sess_test_99999",
                "utm_source": "facebook",
            },
            {
                "event_name": "begin_checkout",
                "anonymous_id": "anon_test_12345",
                "session_id": "sess_test_99999",
                "utm_source": "facebook",
            },
        ]
    }
    batch_res = client.post("/api/v1/tracking/batch", json=batch_payload)
    assert batch_res.status_code == 201
    assert batch_res.json()["recorded_count"] == 2


def test_order_attribution_computation(client: TestClient, admin_headers: dict):
    # 1. Lấy danh sách sản phẩm để tạo đơn hàng
    prod_res = client.get("/api/v1/products?limit=1", headers=admin_headers)
    assert prod_res.status_code == 200
    prod_id = prod_res.json()["items"][0]["id"]

    # 2. Tạo đơn hàng mới qua Order API
    order_payload = {
        "customer_name": "Trần Thị Ánh",
        "customer_phone": "0988776655",
        "delivery_address": "88 Hàm Nghi, Q1, TP.HCM",
        "source": "STOREFRONT_WEB",
        "payment_method": "COD",
        "applied_promo_code": "CAMP-COMBO-OCT",
        "items": [
            {
                "product_id": prod_id,
                "quantity": 2,
                "unit_price": 120000.0,
            }
        ],
    }
    create_res = client.post("/api/v1/orders", json=order_payload, headers=admin_headers)
    assert create_res.status_code == 201
    order = create_res.json()
    order_id = order["id"]

    # 3. Ghi nhận tracking clickstream liên kết với order
    client.post(
        "/api/v1/tracking/events",
        json={
            "event_name": "campaign_click",
            "anonymous_id": "anon_cust_888",
            "session_id": "sess_cust_888",
            "order_id": order_id,
            "utm_source": "tiktok",
            "utm_medium": "video",
            "utm_campaign": "CAMP-COMBO-OCT",
        },
    )

    client.post(
        "/api/v1/tracking/events",
        json={
            "event_name": "purchase",
            "anonymous_id": "anon_cust_888",
            "session_id": "sess_cust_888",
            "order_id": order_id,
            "utm_source": "tiktok",
            "utm_medium": "video",
            "utm_campaign": "CAMP-COMBO-OCT",
        },
    )

    # 4. Trigger tính toán attribution cho đơn hàng
    attr_res = client.post(
        f"/api/v1/analytics/orders/{order_id}/compute-attribution",
        headers=admin_headers,
    )
    assert attr_res.status_code == 200
    attributions = attr_res.json()
    assert len(attributions) >= 2

    models = [a["attribution_model"] for a in attributions]
    assert "FIRST_TOUCH" in models
    assert "LAST_TOUCH" in models

    first_touch = next(a for a in attributions if a["attribution_model"] == "FIRST_TOUCH")
    assert first_touch["order_id"] == order_id
    assert first_touch["confidence"] in ("DETERMINISTIC", "INFERRED")
    assert first_touch["attributed_revenue"] > 0


def test_inferred_attribution_via_promo_code(client: TestClient, admin_headers: dict):
    # 1. Tạo đơn hàng với mã khuyến mại chiến dịch mà không có cookie clickstream
    prod_res = client.get("/api/v1/products?limit=1", headers=admin_headers)
    prod_id = prod_res.json()["items"][0]["id"]

    order_payload = {
        "customer_name": "Lê Văn Bách",
        "customer_phone": "0911223388",
        "delivery_address": "45 Nguyễn Huệ, Q1, TP.HCM",
        "source": "STOREFRONT_WEB",
        "payment_method": "BANK_TRANSFER",
        "applied_promo_code": "CAMP-CLEARANCE-OCT",
        "items": [
            {
                "product_id": prod_id,
                "quantity": 1,
                "unit_price": 95000.0,
            }
        ],
    }
    create_res = client.post("/api/v1/orders", json=order_payload, headers=admin_headers)
    assert create_res.status_code == 201
    order_id = create_res.json()["id"]

    # 2. Lấy attribution
    attr_res = client.get(
        f"/api/v1/analytics/orders/{order_id}/attribution",
        headers=admin_headers,
    )
    assert attr_res.status_code == 200
    attributions = attr_res.json()
    assert len(attributions) >= 1

    last_touch = next(a for a in attributions if a["attribution_model"] == "LAST_TOUCH")
    assert last_touch["campaign_code"] == "CAMP-CLEARANCE-OCT"
    assert last_touch["confidence"] in ("INFERRED", "DETERMINISTIC")


def test_analytics_overview_dashboard(client: TestClient, admin_headers: dict):
    res = client.get("/api/v1/analytics/overview?period=30d", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()

    # Kiểm tra cấu trúc KPIs
    assert "kpis" in data
    kpis = data["kpis"]
    assert "gross_revenue" in kpis
    assert "net_revenue" in kpis
    assert "roas" in kpis
    assert "mer" in kpis
    assert "cac" in kpis
    assert "ltv" in kpis
    assert "ltv_to_cac_ratio" in kpis

    # Kiểm tra Channel Breakdown
    assert "channel_breakdown" in data
    assert len(data["channel_breakdown"]) >= 4

    # Kiểm tra Campaign Comparison
    assert "campaign_attributions" in data
    assert isinstance(data["campaign_attributions"], list)

    # Kiểm tra Funnel
    assert "funnel" in data
    assert len(data["funnel"]) == 5
    assert data["funnel"][0]["step_key"] == "page_view"
    assert data["funnel"][4]["step_key"] == "purchase"

    # Kiểm tra AI Insights Box
    assert "ai_insights" in data
    assert len(data["ai_insights"]) > 0


def test_channel_and_campaign_endpoints(client: TestClient, admin_headers: dict):
    res_ch = client.get("/api/v1/analytics/channels?period=30d", headers=admin_headers)
    assert res_ch.status_code == 200
    assert isinstance(res_ch.json(), list)

    res_camp = client.get("/api/v1/analytics/campaigns?period=30d", headers=admin_headers)
    assert res_camp.status_code == 200
    assert isinstance(res_camp.json(), list)

    res_funnel = client.get("/api/v1/analytics/funnel?period=30d", headers=admin_headers)
    assert res_funnel.status_code == 200
    assert len(res_funnel.json()) == 5


def test_analytics_rbac_protection(client: TestClient):
    # Request without token should be 401 Unauthorized
    res = client.get("/api/v1/analytics/overview")
    assert res.status_code == 401
