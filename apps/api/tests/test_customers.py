import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient


def test_customer_crud_and_validation(client: TestClient, admin_headers: dict):
    # 1. Create a new customer
    payload = {
        "full_name": "Nguyễn Hoàng Minh",
        "phone": "0977112233",
        "email": "minh.nguyen@example.com",
        "default_address": "123 Cách Mạng Tháng 8, Q3, TP.HCM",
        "source": "ONLINE",
        "tags": ["thich_salad", "eat_clean"],
        "notes": "Khách dị ứng với đậu phộng",
        "consent_marketing": True,
    }
    res = client.post("/api/v1/customers", json=payload, headers=admin_headers)
    assert res.status_code == 201
    cust = res.json()
    assert cust["full_name"] == "Nguyễn Hoàng Minh"
    assert cust["phone"] == "0977112233"
    assert cust["segment"] == "NEW"
    assert cust["loyalty_points"] == 0
    assert cust["order_count"] == 0
    assert cust["total_spent"] == 0.0
    assert "thich_salad" in cust["tags"]
    customer_id = cust["id"]

    # 2. Reject duplicate phone
    dup_res = client.post("/api/v1/customers", json=payload, headers=admin_headers)
    assert dup_res.status_code == 400
    assert "đã tồn tại" in dup_res.json()["detail"]

    # 3. Get customer by ID
    get_res = client.get(f"/api/v1/customers/{customer_id}", headers=admin_headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == customer_id

    # 4. Update customer
    update_res = client.put(
        f"/api/v1/customers/{customer_id}",
        json={
            "full_name": "Nguyễn Hoàng Minh (Updated)",
            "tags": ["thich_salad", "gym_member"],
            "notes": "Đã đổi địa chỉ nhận hàng",
        },
        headers=admin_headers,
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["full_name"] == "Nguyễn Hoàng Minh (Updated)"
    assert "gym_member" in updated["tags"]


def test_customer_sync_and_loyalty_earning(client: TestClient, admin_headers: dict):
    # 1. Get an existing product for ordering
    prod_res = client.get("/api/v1/products?limit=1", headers=admin_headers)
    assert prod_res.status_code == 200
    products = prod_res.json()["items"]
    assert len(products) > 0
    product_id = products[0]["id"]

    phone_test = "0977889911"

    # 2. Create Order 1 via POS manual endpoint
    order1_payload = {
        "customer_name": "Trần Thị Mai",
        "customer_phone": phone_test,
        "customer_email": "mai.tran@example.com",
        "delivery_address": "45 Lê Lợi, Quận 1",
        "source": "WALK_IN",
        "payment_method": "COD",
        "payment_status": "PAID",
        "items": [{"product_id": product_id, "quantity": 2}],
    }
    res_order1 = client.post("/api/v1/orders", json=order1_payload, headers=admin_headers)
    assert res_order1.status_code == 201
    order1 = res_order1.json()

    # 3. Verify Customer was automatically created & points earned (1 pt / 10k VND)
    res_list = client.get(f"/api/v1/customers?search={phone_test}", headers=admin_headers)
    assert res_list.status_code == 200
    items = res_list.json()["items"]
    assert len(items) == 1
    cust = items[0]
    assert cust["phone"] == phone_test
    assert cust["order_count"] == 1
    assert cust["total_spent"] == order1["total_amount"]
    expected_pts = int(order1["total_amount"] // 10000)
    assert cust["loyalty_points"] == expected_pts
    assert cust["segment"] in ("NEW", "ACTIVE")
    customer_id = cust["id"]

    # 4. Create Order 2 for same customer -> segment becomes REPEAT
    order2_payload = {
        "customer_name": "Trần Thị Mai",
        "customer_phone": phone_test,
        "delivery_address": "45 Lê Lợi, Quận 1",
        "source": "WALK_IN",
        "payment_method": "COD",
        "payment_status": "PAID",
        "items": [{"product_id": product_id, "quantity": 1}],
    }
    res_order2 = client.post("/api/v1/orders", json=order2_payload, headers=admin_headers)
    assert res_order2.status_code == 201
    order2 = res_order2.json()

    # 5. Check customer updated: order_count=2, segment=REPEAT, points accumulated
    res_cust2 = client.get(f"/api/v1/customers/{customer_id}", headers=admin_headers)
    assert res_cust2.status_code == 200
    c2 = res_cust2.json()
    assert c2["order_count"] == 2
    assert c2["total_spent"] == order1["total_amount"] + order2["total_amount"]
    assert c2["segment"] == "REPEAT"
    assert c2["loyalty_points"] == expected_pts + int(order2["total_amount"] // 10000)


def test_loyalty_points_adjust_and_balance_guard(client: TestClient, admin_headers: dict):
    # 1. Create customer
    res = client.post(
        "/api/v1/customers",
        json={"full_name": "Lê Văn Điểm", "phone": "0933445577"},
        headers=admin_headers,
    )
    assert res.status_code == 201
    cust_id = res.json()["id"]

    # 2. Add points (+50 Mộc Xu)
    adj_res = client.post(
        f"/api/v1/customers/{cust_id}/loyalty/adjust",
        json={"points": 50, "reason": "Tặng điểm sinh nhật thành viên"},
        headers=admin_headers,
    )
    assert adj_res.status_code == 200
    adj_data = adj_res.json()
    assert adj_data["points"] == 50
    assert adj_data["balance_after"] == 50
    assert adj_data["transaction_type"] == "ADJUSTMENT"

    # 3. Deduct points (-20 Mộc Xu)
    ded_res = client.post(
        f"/api/v1/customers/{cust_id}/loyalty/adjust",
        json={"points": -20, "reason": "Đổi voucher ưu đãi giảm 20k"},
        headers=admin_headers,
    )
    assert ded_res.status_code == 200
    assert ded_res.json()["balance_after"] == 30

    # 4. Guard against negative balance (try deducting 100 when balance is 30)
    neg_res = client.post(
        f"/api/v1/customers/{cust_id}/loyalty/adjust",
        json={"points": -100, "reason": "Thử trừ quá số dư"},
        headers=admin_headers,
    )
    assert neg_res.status_code == 400
    assert "không đủ" in neg_res.json()["detail"]


def test_customer_360_view(client: TestClient, admin_headers: dict):
    # 1. Create a customer
    res = client.post(
        "/api/v1/customers",
        json={
            "full_name": "Phạm 360 Độ",
            "phone": "0966778899",
            "email": "customer360@example.com",
            "tags": ["salad", "smoothie"],
        },
        headers=admin_headers,
    )
    assert res.status_code == 201
    cust_id = res.json()["id"]

    # 2. Add points
    client.post(
        f"/api/v1/customers/{cust_id}/loyalty/adjust",
        json={"points": 25, "reason": "Điểm chào mừng thành viên mới"},
        headers=admin_headers,
    )

    # 3. Query Customer 360 View
    res_360 = client.get(f"/api/v1/customers/{cust_id}/360", headers=admin_headers)
    assert res_360.status_code == 200
    data = res_360.json()
    assert data["id"] == cust_id
    assert data["full_name"] == "Phạm 360 Độ"
    assert data["loyalty_points"] == 25
    assert len(data["recent_loyalty_transactions"]) == 1
    assert data["recent_loyalty_transactions"][0]["points"] == 25
    assert "salad" in data["tags"]


def test_crm_overview_stats(client: TestClient, admin_headers: dict):
    res = client.get("/api/v1/customers/overview", headers=admin_headers)
    assert res.status_code == 200
    stats = res.json()
    assert "total_customers" in stats
    assert "vip_customers" in stats
    assert "at_risk_customers" in stats
    assert "total_loyalty_points_circulating" in stats
    assert stats["total_customers"] >= 1


def test_customer_rbac(client: TestClient):
    # Unauthenticated request
    res = client.get("/api/v1/customers")
    assert res.status_code == 401

    res_post = client.post("/api/v1/customers", json={"full_name": "Test", "phone": "0900000000"})
    assert res_post.status_code == 401
