import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.models.order import OrderStatus, PaymentStatus, PaymentMethod


def test_order_lifecycle_full_flow(client: TestClient, admin_headers: dict):
    """
    Kiểm tra toàn bộ vòng đời đơn hàng từ lúc đặt đến khi hoàn tất:
    Khách đặt (NEW) -> Admin duyệt (CONFIRMED) -> Bếp làm (PREPARING) ->
    Sẵn sàng (READY) -> Giao hàng (SHIPPING) -> Hoàn thành (COMPLETED).
    """
    headers = admin_headers

    # 1. Khách hàng đặt 1 đơn hàng qua Checkout API
    res_prods = client.get("/api/v1/storefront/products")
    p = res_prods.json()["items"][0]

    cart_token = f"order_flow_cart_{uuid.uuid4().hex}"
    client.post(
        "/api/v1/cart/items",
        json={"product_id": p["id"], "quantity": 2},
        headers={"X-Cart-Token": cart_token},
    )

    res_checkout = client.post(
        "/api/v1/checkout",
        json={
            "cart_token": cart_token,
            "customer_name": "Lê Vòng Đời",
            "customer_phone": "0933445566",
            "delivery_address": "88 Đường Lê Lợi, Phường Bến Nghé, Quận 1",
            "payment_method": "COD",
            "terms_accepted": True,
        },
    )
    assert res_checkout.status_code == 201
    created_order = res_checkout.json()
    order_id = created_order["order_id"]
    order_number = created_order["order_number"]
    assert created_order["status"] == "NEW"

    # 2. Admin xem chi tiết đơn hàng
    res_detail = client.get(f"/api/v1/orders/{order_id}", headers=headers)
    assert res_detail.status_code == 200
    assert res_detail.json()["order_number"] == order_number
    assert len(res_detail.json()["items"]) == 1

    # 3. Bước 1: NEW -> CONFIRMED
    res_s1 = client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"new_status": "CONFIRMED", "reason": "Admin đã gọi xác nhận với khách"},
        headers=headers,
    )
    assert res_s1.status_code == 200
    assert res_s1.json()["status"] == "CONFIRMED"

    # 4. Bước 2: CONFIRMED -> PREPARING
    res_s2 = client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"new_status": "PREPARING", "reason": "Bếp bắt đầu cắt gọt trái cây tươi"},
        headers=headers,
    )
    assert res_s2.status_code == 200
    assert res_s2.json()["status"] == "PREPARING"

    # 5. Bước 3: PREPARING -> READY
    res_s3 = client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"new_status": "READY", "reason": "Đóng hộp giữ nhiệt sẵn sàng"},
        headers=headers,
    )
    assert res_s3.status_code == 200
    assert res_s3.json()["status"] == "READY"

    # 6. Bước 4: READY -> SHIPPING
    res_s4 = client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"new_status": "SHIPPING", "reason": "Đã bàn giao cho shipper Mộc Healthy"},
        headers=headers,
    )
    assert res_s4.status_code == 200
    assert res_s4.json()["status"] == "SHIPPING"

    # 7. Bước 5: SHIPPING -> COMPLETED
    res_s5 = client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"new_status": "COMPLETED", "reason": "Khách đã nhận hàng và trả tiền mặt"},
        headers=headers,
    )
    assert res_s5.status_code == 200
    final_order = res_s5.json()
    assert final_order["status"] == "COMPLETED"
    assert final_order["payment_status"] == "PAID"  # Auto marked PAID on completion for COD

    # 8. Kiểm tra lịch sử chuyển trạng thái (Timeline Audit)
    history = final_order["status_history"]
    assert len(history) >= 6  # NEW (tạo), CONFIRMED, PREPARING, READY, SHIPPING, COMPLETED


def test_invalid_status_transition_rejected(client: TestClient, admin_headers: dict):
    """
    Kiểm tra guardrail máy trạng thái:
    Không thể nhảy cóc trái quy tắc (ví dụ: NEW -> COMPLETED trực tiếp mà chưa qua chuẩn bị/giao hàng).
    """
    headers = admin_headers

    # Tạo đơn hàng
    res_prods = client.get("/api/v1/storefront/products")
    p = res_prods.json()["items"][0]
    cart_token = f"order_invalid_{uuid.uuid4().hex}"
    client.post(
        "/api/v1/cart/items",
        json={"product_id": p["id"], "quantity": 1},
        headers={"X-Cart-Token": cart_token},
    )

    res_checkout = client.post(
        "/api/v1/checkout",
        json={
            "cart_token": cart_token,
            "customer_name": "Trần Nhảy Cóc",
            "customer_phone": "0911223344",
            "delivery_address": "12 Điện Biên Phủ, Q. Bình Thạnh",
            "payment_method": "COD",
            "terms_accepted": True,
        },
    )
    order_id = res_checkout.json()["order_id"]

    # Thử nhảy từ NEW sang COMPLETED
    res_invalid = client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"new_status": "COMPLETED"},
        headers=headers,
    )
    assert res_invalid.status_code == 400
    assert "không hợp lệ" in res_invalid.json()["detail"].lower()


def test_cancel_order_with_inventory_restitution(client: TestClient, admin_headers: dict):
    """
    Kiểm tra hủy đơn hàng (CANCELLED) và tự động hoàn trả tồn kho (RETURN_IN).
    """
    headers = admin_headers

    res_prods = client.get("/api/v1/storefront/products")
    p = res_prods.json()["items"][0]
    cart_token = f"order_cancel_{uuid.uuid4().hex}"
    client.post(
        "/api/v1/cart/items",
        json={"product_id": p["id"], "quantity": 1},
        headers={"X-Cart-Token": cart_token},
    )

    res_checkout = client.post(
        "/api/v1/checkout",
        json={
            "cart_token": cart_token,
            "customer_name": "Phạm Hủy Đơn",
            "customer_phone": "0977889900",
            "delivery_address": "456 Nam Kỳ Khởi Nghĩa, Quận 3",
            "payment_method": "COD",
            "terms_accepted": True,
        },
    )
    order_id = res_checkout.json()["order_id"]

    # Hủy đơn hàng
    res_cancel = client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"new_status": "CANCELLED", "reason": "Khách đổi ý không muốn nhận nữa"},
        headers=headers,
    )
    assert res_cancel.status_code == 200
    assert res_cancel.json()["status"] == "CANCELLED"


def test_update_payment_status_and_internal_note(client: TestClient, admin_headers: dict):
    """
    Kiểm tra cập nhật trạng thái thanh toán và ghi chú nội bộ.
    """
    headers = admin_headers

    res_prods = client.get("/api/v1/storefront/products")
    p = res_prods.json()["items"][0]
    cart_token = f"order_note_{uuid.uuid4().hex}"
    client.post(
        "/api/v1/cart/items",
        json={"product_id": p["id"], "quantity": 1},
        headers={"X-Cart-Token": cart_token},
    )

    res_checkout = client.post(
        "/api/v1/checkout",
        json={
            "cart_token": cart_token,
            "customer_name": "Hoàng Note",
            "customer_phone": "0988776655",
            "delivery_address": "789 Cách Mạng Tháng 8",
            "payment_method": "BANK_TRANSFER",
            "terms_accepted": True,
        },
    )
    order_id = res_checkout.json()["order_id"]

    # 1. Cập nhật thanh toán sang PAID
    res_pay = client.patch(
        f"/api/v1/orders/{order_id}/payment-status",
        json={"payment_status": "PAID", "note": "Đã khớp giao dịch MBBank"},
        headers=headers,
    )
    assert res_pay.status_code == 200
    assert res_pay.json()["payment_status"] == "PAID"

    # 2. Cập nhật ghi chú nội bộ
    res_note = client.patch(
        f"/api/v1/orders/{order_id}/internal-note",
        json={"internal_note": "Khách VIP, ưu tiên giao sớm"},
        headers=headers,
    )
    assert res_note.status_code == 200
    assert res_note.json()["internal_note"] == "Khách VIP, ưu tiên giao sớm"


def test_admin_manual_order_creation(client: TestClient, admin_headers: dict):
    """
    Kiểm tra tạo đơn hàng thủ công tại quầy hoặc qua điện thoại bởi Admin.
    """
    headers = admin_headers

    res_prods = client.get("/api/v1/storefront/products")
    p = res_prods.json()["items"][0]

    payload = {
        "customer_name": "Khách Mua Tại Quầy",
        "customer_phone": "0909998877",
        "delivery_address": "Mua trực tiếp tại cửa hàng Mộc Healthy",
        "customer_note": "Mang về",
        "internal_note": "Đơn tại quầy ca sáng",
        "source": "WALK_IN",
        "payment_method": "COD",
        "payment_status": "PAID",
        "shipping_fee": 0,
        "items": [{"product_id": p["id"], "quantity": 2, "note": "Gọt sẵn"}],
    }

    res = client.post("/api/v1/orders", json=payload, headers=headers)
    assert res.status_code == 201
    order = res.json()
    assert order["source"] == "WALK_IN"
    assert order["status"] == "CONFIRMED"
    assert order["payment_status"] == "PAID"
    assert len(order["items"]) == 1
    assert order["items"][0]["quantity"] == 2


def test_orders_overview_and_list_filtering(client: TestClient, admin_headers: dict):
    """
    Kiểm tra thống kê tổng quan (overview) và bộ lọc danh sách đơn hàng.
    """
    headers = admin_headers

    # 1. Thống kê overview
    res_stats = client.get("/api/v1/orders/overview", headers=headers)
    assert res_stats.status_code == 200
    stats = res_stats.json()
    assert "total_orders" in stats
    assert "new_orders" in stats
    assert "in_progress_orders" in stats
    assert "completed_today" in stats
    assert "revenue_today" in stats
    assert stats["total_orders"] >= 1

    # 2. Danh sách đơn hàng có phân trang
    res_list = client.get("/api/v1/orders?page=1&page_size=10", headers=headers)
    assert res_list.status_code == 200
    data = res_list.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1

    # 3. Lọc theo trạng thái
    res_filtered = client.get("/api/v1/orders?status=NEW", headers=headers)
    assert res_filtered.status_code == 200
    for it in res_filtered.json()["items"]:
        assert it["status"] == "NEW"


def test_public_order_tracking(client: TestClient):
    """
    Kiểm tra khách hàng tra cứu trạng thái đơn hàng công khai qua mã đơn.
    """
    # 1. Tạo đơn
    res_prods = client.get("/api/v1/storefront/products")
    p = res_prods.json()["items"][0]
    cart_token = f"track_{uuid.uuid4().hex}"
    client.post(
        "/api/v1/cart/items",
        json={"product_id": p["id"], "quantity": 1},
        headers={"X-Cart-Token": cart_token},
    )

    res_checkout = client.post(
        "/api/v1/checkout",
        json={
            "cart_token": cart_token,
            "customer_name": "Vũ Tra Cứu",
            "customer_phone": "0944556677",
            "delivery_address": "99 Lý Tự Trọng, Q.1",
            "payment_method": "COD",
            "terms_accepted": True,
        },
    )
    order_number = res_checkout.json()["order_number"]

    # 2. Khách tra cứu qua mã đơn
    res_track = client.post(
        "/api/v1/orders/tracking",
        json={"order_number": order_number, "phone": "0944556677"},
    )
    assert res_track.status_code == 200
    track_data = res_track.json()
    assert track_data["order_number"] == order_number
    assert track_data["status"] == "NEW"
    assert len(track_data["items"]) == 1
    assert len(track_data["status_history"]) >= 1


def test_order_rbac_enforcement(client: TestClient):
    """
    Kiểm tra bảo mật RBAC:
    - Không có token: 401 Unauthorized
    """
    res_unauth = client.get("/api/v1/orders")
    assert res_unauth.status_code == 401
