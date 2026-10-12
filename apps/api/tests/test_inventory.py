from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient


def test_inventory_overview(client: TestClient, inventory_headers: dict):
    """Kiểm tra API tổng quan tồn kho trả về các chỉ số thống kê chính xác."""
    response = client.get("/api/v1/inventory/overview", headers=inventory_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_products" in data
    assert "total_batches" in data
    assert "total_stock_units" in data
    assert "low_stock_products_count" in data
    assert "expiring_soon_batches_count" in data
    assert "critical_batches_count" in data
    assert "expired_batches_count" in data
    assert "total_inventory_value" in data
    assert data["total_batches"] > 0
    assert data["total_stock_units"] > 0


def test_product_stock_summaries(client: TestClient, inventory_headers: dict):
    """Kiểm tra danh sách tồn kho theo từng sản phẩm F&B kèm cảnh báo định mức."""
    response = client.get("/api/v1/inventory/products", headers=inventory_headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) > 0

    first = items[0]
    assert "product_id" in first
    assert "product_name" in first
    assert "sku" in first
    assert "total_available" in first
    assert "batch_count" in first
    assert "is_low_stock" in first


def test_product_stock_summaries_filter_low_stock(client: TestClient, inventory_headers: dict):
    """Kiểm tra bộ lọc sản phẩm dưới định mức (low stock)."""
    response = client.get("/api/v1/inventory/products?low_stock_only=true", headers=inventory_headers)
    assert response.status_code == 200
    items = response.json()
    for item in items:
        assert item["is_low_stock"] is True


def test_receive_batch_and_movement_math(client: TestClient, inventory_headers: dict):
    """Kiểm tra luồng nhập kho lô mới và ghi nhận sổ cái luân chuyển (movement math)."""
    # 1. Lấy 1 sản phẩm
    prods = client.get("/api/v1/products", headers=inventory_headers).json()["items"]
    product = prods[0]

    now = datetime.now(timezone.utc)
    expiry = now + timedelta(days=3)

    payload = {
        "product_id": product["id"],
        "batch_code": "BATCH-TEST-MATH-001",
        "quantity_received": 50,
        "cost_per_unit": 20000.0,
        "supplier": "Nông trại Mộc Xanh",
        "expiry_at": expiry.isoformat(),
        "note": "Nhập lô kiểm thử toán học luân chuyển",
    }

    # 2. Tạo lô hàng mới
    res_batch = client.post("/api/v1/inventory/batches", json=payload, headers=inventory_headers)
    assert res_batch.status_code == 201
    batch_data = res_batch.json()
    batch_id = batch_data["id"]
    assert batch_data["batch_code"] == "BATCH-TEST-MATH-001"
    assert batch_data["quantity_received"] == 50
    assert batch_data["quantity_available"] == 50
    assert batch_data["status"] == "ACTIVE"

    # 3. Kiểm tra movement PURCHASE_IN được sinh ra tự động
    res_mov = client.get(f"/api/v1/inventory/movements?batch_id={batch_id}", headers=inventory_headers)
    assert res_mov.status_code == 200
    movements = res_mov.json()
    assert len(movements) >= 1
    m_in = next(m for m in movements if m["movement_type"] == "PURCHASE_IN")
    assert m_in["quantity"] == 50
    assert m_in["previous_quantity"] == 0
    assert m_in["new_quantity"] == 50


def test_negative_stock_protection(client: TestClient, inventory_headers: dict):
    """Kiểm tra cơ chế chặn tồn kho âm (Negative stock protection)."""
    # 1. Tạo 1 lô nhỏ 10 đơn vị
    prods = client.get("/api/v1/products", headers=inventory_headers).json()["items"]
    product = prods[0]
    now = datetime.now(timezone.utc)

    payload = {
        "product_id": product["id"],
        "batch_code": "BATCH-TEST-NEG-001",
        "quantity_received": 10,
        "expiry_at": (now + timedelta(days=2)).isoformat(),
    }
    res_batch = client.post("/api/v1/inventory/batches", json=payload, headers=inventory_headers)
    assert res_batch.status_code == 201
    batch_id = res_batch.json()["id"]

    # 2. Thử xuất hủy 15 đơn vị (lớn hơn 10 khả dụng) -> Phải bị từ chối 400 Bad Request
    adj_payload = {
        "batch_id": batch_id,
        "movement_type": "WASTE_OUT",
        "quantity": 15,
        "reason": "Thử nghiệm xuất vượt số lượng",
    }
    res_adj = client.post("/api/v1/inventory/adjustments", json=adj_payload, headers=inventory_headers)
    assert res_adj.status_code == 400
    assert "vượt quá" in res_adj.json()["detail"].lower()

    # 3. Xuất đúng 6 đơn vị -> Thành công, còn lại 4
    adj_ok = {
        "batch_id": batch_id,
        "movement_type": "WASTE_OUT",
        "quantity": 6,
        "reason": "Xuất hủy trái cây dập nhẹ",
    }
    res_ok = client.post("/api/v1/inventory/adjustments", json=adj_ok, headers=inventory_headers)
    assert res_ok.status_code == 200
    movement = res_ok.json()
    assert movement["previous_quantity"] == 10
    assert movement["new_quantity"] == 4

    # 4. Kiểm tra lại lô
    batch_check = client.get(f"/api/v1/inventory/batches/{batch_id}", headers=inventory_headers).json()
    assert batch_check["quantity_available"] == 4


def test_fefo_allocation_algorithm(client: TestClient, inventory_headers: dict, admin_headers: dict):
    """Kiểm tra thuật toán phân bổ xuất kho FEFO (First Expired First Out)."""
    # 1. Tạo 1 sản phẩm riêng để test FEFO
    cat = client.get("/api/v1/categories", headers=inventory_headers).json()[0]
    sku_test = f"FEFO-TEST-{int(datetime.now().timestamp())}"
    res_prod = client.post(
        "/api/v1/products",
        json={
            "sku": sku_test,
            "slug": sku_test.lower(),
            "name": "Nước Ép Test FEFO",
            "category_id": cat["id"],
            "base_price": 50000.0,
            "cost_price": 20000.0,
            "unit": "chai",
            "status": "ACTIVE",
        },
        headers=admin_headers,
    )
    assert res_prod.status_code == 201
    prod_id = res_prod.json()["id"]

    now = datetime.now(timezone.utc)
    # 2. Tạo 3 lô với hạn dùng khác nhau:
    # Lô A: hết hạn sau 1 ngày (10 chai) - cận date nhất!
    # Lô B: hết hạn sau 3 ngày (20 chai)
    # Lô C: hết hạn sau 7 ngày (30 chai)
    batch_a = client.post(
        "/api/v1/inventory/batches",
        json={
            "product_id": prod_id,
            "batch_code": f"FEFO-A-{sku_test}",
            "quantity_received": 10,
            "expiry_at": (now + timedelta(days=1)).isoformat(),
        },
        headers=inventory_headers,
    ).json()

    batch_b = client.post(
        "/api/v1/inventory/batches",
        json={
            "product_id": prod_id,
            "batch_code": f"FEFO-B-{sku_test}",
            "quantity_received": 20,
            "expiry_at": (now + timedelta(days=3)).isoformat(),
        },
        headers=inventory_headers,
    ).json()

    batch_c = client.post(
        "/api/v1/inventory/batches",
        json={
            "product_id": prod_id,
            "batch_code": f"FEFO-C-{sku_test}",
            "quantity_received": 30,
            "expiry_at": (now + timedelta(days=7)).isoformat(),
        },
        headers=inventory_headers,
    ).json()

    # 3. Yêu cầu xuất 15 chai theo FEFO:
    # Thuật toán FEFO phải lấy:
    # - Hết 10 chai từ Lô A (hết hạn sau 1 ngày)
    # - 5 chai từ Lô B (hết hạn sau 3 ngày)
    # - Lô C nguyên vẹn (0 chai)
    fefo_req = {
        "product_id": prod_id,
        "quantity": 15,
        "reference_id": "ORDER-FEFO-001",
        "note": "Kiểm tra phân bổ FEFO đơn hàng khách đặt",
    }

    # Thử mô phỏng trước (Simulate - dry run)
    sim_res = client.post("/api/v1/inventory/fefo/simulate", json=fefo_req, headers=inventory_headers)
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert sim_data["allocated_quantity"] == 15
    assert len(sim_data["allocations"]) == 2
    assert sim_data["allocations"][0]["batch_id"] == batch_a["id"]
    assert sim_data["allocations"][0]["allocated_quantity"] == 10
    assert sim_data["allocations"][1]["batch_id"] == batch_b["id"]
    assert sim_data["allocations"][1]["allocated_quantity"] == 5

    # 4. Thực thi xuất kho thật (Execute FEFO allocation)
    alloc_res = client.post("/api/v1/inventory/fefo/allocate", json=fefo_req, headers=inventory_headers)
    assert alloc_res.status_code == 200
    alloc_data = alloc_res.json()
    assert alloc_data["is_fully_allocated"] is True

    # 5. Kiểm tra tồn kho thực tế của các lô sau khi xuất
    check_a = client.get(f"/api/v1/inventory/batches/{batch_a['id']}", headers=inventory_headers).json()
    assert check_a["quantity_available"] == 0
    assert check_a["status"] == "DEPLETED"

    check_b = client.get(f"/api/v1/inventory/batches/{batch_b['id']}", headers=inventory_headers).json()
    assert check_b["quantity_available"] == 15  # 20 - 5 = 15
    assert check_b["status"] == "ACTIVE"

    check_c = client.get(f"/api/v1/inventory/batches/{batch_c['id']}", headers=inventory_headers).json()
    assert check_c["quantity_available"] == 30  # Nguyên vẹn


def test_expiry_alerts_and_classification(client: TestClient, inventory_headers: dict):
    """Kiểm tra danh sách cảnh báo hạn dùng và phân cấp mức độ khẩn cấp (CRITICAL, WARNING, v.v.)."""
    response = client.get("/api/v1/inventory/expiry-alerts", headers=inventory_headers)
    assert response.status_code == 200
    alerts = response.json()
    assert isinstance(alerts, list)
    if len(alerts) > 0:
        first = alerts[0]
        assert "urgency" in first
        assert first["urgency"] in ["EXPIRED", "CRITICAL", "WARNING", "ATTENTION"]
        assert "estimated_waste_cost" in first
        assert "hours_to_expiry" in first


def test_inventory_rbac_protection(client: TestClient, marketing_headers: dict):
    """Kiểm tra phân quyền: tài khoản marketing không có quyền inventory.write không được nhập kho/điều chỉnh."""
    payload = {
        "product_id": "dummy-id",
        "batch_code": "BATCH-HACK-001",
        "quantity_received": 100,
        "expiry_at": datetime.now(timezone.utc).isoformat(),
    }
    # Thử nhập kho bằng marketing role -> 403 Forbidden
    res = client.post("/api/v1/inventory/batches", json=payload, headers=marketing_headers)
    assert res.status_code == 403

    # Thử điều chỉnh kho -> 403 Forbidden
    res_adj = client.post(
        "/api/v1/inventory/adjustments",
        json={"batch_id": "dummy", "movement_type": "WASTE_OUT", "quantity": 1, "reason": "test"},
        headers=marketing_headers,
    )
    assert res_adj.status_code == 403
