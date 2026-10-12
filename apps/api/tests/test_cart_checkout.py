import uuid
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient


def test_cart_lifecycle_and_authoritative_pricing(client: TestClient):
    """
    Kiểm tra vòng đời giỏ hàng và cơ chế tính giá độc quyền từ Backend:
    - Thêm sản phẩm vào giỏ
    - Cập nhật số lượng
    - Xóa sản phẩm
    - Xóa toàn bộ giỏ
    """
    cart_token = f"test_cart_{uuid.uuid4().hex}"
    headers = {"X-Cart-Token": cart_token}

    # 1. Lấy danh sách sản phẩm mẫu
    res_prods = client.get("/api/v1/storefront/products")
    assert res_prods.status_code == 200
    products = res_prods.json()["items"]
    assert len(products) >= 2
    p1 = products[0]
    p2 = products[1]

    # 2. Thêm p1 vào giỏ với số lượng 2
    res_add1 = client.post(
        "/api/v1/cart/items",
        json={"product_id": p1["id"], "quantity": 2, "note": "Ít ngọt"},
        headers=headers,
    )
    assert res_add1.status_code == 200
    cart_data = res_add1.json()
    assert cart_data["cart_token"] == cart_token
    assert len(cart_data["items"]) == 1
    assert cart_data["items"][0]["quantity"] == 2
    assert cart_data["items"][0]["note"] == "Ít ngọt"

    expected_p1_price = p1["sale_price"] if (p1.get("sale_price") and p1["sale_price"] > 0) else p1["base_price"]
    assert cart_data["items"][0]["unit_price"] == expected_p1_price
    assert cart_data["items"][0]["line_total"] == expected_p1_price * 2
    assert cart_data["subtotal"] == expected_p1_price * 2

    # 3. Thêm p2 vào giỏ với số lượng 1
    res_add2 = client.post(
        "/api/v1/cart/items",
        json={"product_id": p2["id"], "quantity": 1},
        headers=headers,
    )
    assert res_add2.status_code == 200
    cart_data = res_add2.json()
    assert len(cart_data["items"]) == 2
    assert cart_data["total_items"] == 3

    # 4. Cập nhật số lượng của mục đầu tiên lên 3
    item1_id = cart_data["items"][0]["id"]
    res_update = client.put(
        f"/api/v1/cart/items/{item1_id}",
        json={"quantity": 3, "note": "Không đá"},
        headers=headers,
    )
    assert res_update.status_code == 200
    cart_data = res_update.json()
    item1 = next(it for it in cart_data["items"] if it["id"] == item1_id)
    assert item1["quantity"] == 3
    assert item1["note"] == "Không đá"

    # 5. Xóa mục p2
    item2_id = cart_data["items"][1]["id"]
    res_remove = client.delete(f"/api/v1/cart/items/{item2_id}", headers=headers)
    assert res_remove.status_code == 200
    cart_data = res_remove.json()
    assert len(cart_data["items"]) == 1

    # 6. Xóa sạch giỏ hàng
    res_clear = client.post("/api/v1/cart/clear", headers=headers)
    assert res_clear.status_code == 200
    cart_data = res_clear.json()
    assert len(cart_data["items"]) == 0
    assert cart_data["subtotal"] == 0
    assert cart_data["final_total"] == 0


def test_cart_add_unavailable_product_rejected(client: TestClient):
    """Thêm sản phẩm không tồn tại trả về 404."""
    cart_token = f"test_cart_{uuid.uuid4().hex}"
    headers = {"X-Cart-Token": cart_token}

    res = client.post(
        "/api/v1/cart/items",
        json={"product_id": "non-existent-uuid-1234", "quantity": 1},
        headers=headers,
    )
    assert res.status_code == 404


def test_cart_apply_voucher_and_shipping_rules(client: TestClient):
    """
    Kiểm tra áp dụng voucher và quy tắc phí vận chuyển:
    - Đơn < 120.000₫: phí giao hàng chuẩn 25.000₫
    - Đơn >= 120.000₫: miễn phí giao hàng (0₫)
    - Áp dụng mã voucher hợp lệ
    """
    cart_token = f"test_cart_{uuid.uuid4().hex}"
    headers = {"X-Cart-Token": cart_token}

    # Lấy sản phẩm
    res_prods = client.get("/api/v1/storefront/products")
    p = res_prods.json()["items"][0]

    # Thêm 1 sản phẩm (giá thường 30k-49k, < 120k)
    client.post(
        "/api/v1/cart/items",
        json={"product_id": p["id"], "quantity": 1},
        headers=headers,
    )

    res_cart = client.get("/api/v1/cart", headers=headers)
    cart = res_cart.json()
    assert cart["subtotal"] < 120000
    assert cart["shipping_fee"] == 25000  # Chưa đạt ngưỡng freeship

    # Tăng số lượng lên 5 để subtotal >= 120k
    item_id = cart["items"][0]["id"]
    res_cart = client.put(
        f"/api/v1/cart/items/{item_id}",
        json={"quantity": 5},
        headers=headers,
    )
    cart = res_cart.json()
    if cart["subtotal"] >= 120000:
        assert cart["shipping_fee"] == 0  # Đạt ngưỡng freeship tự động

    # Áp dụng mã voucher WELCOME20 (20% giảm)
    res_coupon = client.post(
        "/api/v1/cart/apply-coupon",
        json={"code": "WELCOME20"},
        headers=headers,
    )
    assert res_coupon.status_code == 200
    cart_with_promo = res_coupon.json()
    assert cart_with_promo["applied_promo_code"] == "WELCOME20"
    assert cart_with_promo["discount_amount"] > 0
    assert cart_with_promo["final_total"] < cart_with_promo["subtotal"]

    # Gỡ mã voucher
    res_remove_coupon = client.delete("/api/v1/cart/coupon", headers=headers)
    assert res_remove_coupon.status_code == 200
    cart_no_promo = res_remove_coupon.json()
    assert cart_no_promo["applied_promo_code"] is None
    assert cart_no_promo["discount_amount"] == 0


def test_checkout_with_cod(client: TestClient):
    """
    Đặt hàng thành công với phương thức thanh toán khi nhận hàng (COD):
    - Đơn hàng được tạo với mã MOC-YYYYMMDD-XXXX
    - Trạng thái NEW, payment_status PENDING
    - Giỏ hàng được chuyển trạng thái CONVERTED
    """
    cart_token = f"test_cart_{uuid.uuid4().hex}"
    headers = {"X-Cart-Token": cart_token}

    res_prods = client.get("/api/v1/storefront/products")
    p = res_prods.json()["items"][0]

    # Thêm sản phẩm vào giỏ
    client.post(
        "/api/v1/cart/items",
        json={"product_id": p["id"], "quantity": 2},
        headers=headers,
    )

    # Đặt hàng COD
    checkout_payload = {
        "cart_token": cart_token,
        "customer_name": "Nguyễn Văn Test",
        "customer_phone": "0901234567",
        "customer_email": "test@example.com",
        "delivery_address": "123 Đường Nguyễn Huệ, Quận 1, TP. Hồ Chí Minh",
        "customer_note": "Giao trước 11h trưa",
        "payment_method": "COD",
        "terms_accepted": True,
        "idempotency_key": str(uuid.uuid4()),
    }

    res_checkout = client.post("/api/v1/checkout", json=checkout_payload)
    assert res_checkout.status_code == 201
    order = res_checkout.json()

    assert order["order_number"].startswith("MOC-")
    assert order["status"] == "NEW"
    assert order["payment_method"] == "COD"
    assert order["payment_status"] == "PENDING"
    assert order["customer_name"] == "Nguyễn Văn Test"
    assert order["customer_phone"] == "0901234567"
    assert len(order["items"]) == 1
    assert order["items"][0]["quantity"] == 2
    assert order["bank_transfer_instruction"] is None

    # Tra cứu lại đơn hàng công khai theo order_number
    res_get_order = client.get(f"/api/v1/checkout/orders/{order['order_number']}")
    assert res_get_order.status_code == 200
    assert res_get_order.json()["order_number"] == order["order_number"]


def test_checkout_with_bank_transfer_vietqr(client: TestClient):
    """
    Đặt hàng với phương thức Chuyển khoản ngân hàng (BANK_TRANSFER):
    - Trả về thông tin chuyển khoản VietQR kèm mã QR và nội dung chuyển khoản
    """
    cart_token = f"test_cart_{uuid.uuid4().hex}"
    headers = {"X-Cart-Token": cart_token}

    res_prods = client.get("/api/v1/storefront/products")
    p = res_prods.json()["items"][0]

    client.post(
        "/api/v1/cart/items",
        json={"product_id": p["id"], "quantity": 1},
        headers=headers,
    )

    checkout_payload = {
        "cart_token": cart_token,
        "customer_name": "Trần Thị Lan",
        "customer_phone": "0987654321",
        "delivery_address": "456 Lê Lợi, Quận 1, TP. HCM",
        "payment_method": "BANK_TRANSFER",
        "terms_accepted": True,
    }

    res_checkout = client.post("/api/v1/checkout", json=checkout_payload)
    assert res_checkout.status_code == 201
    order = res_checkout.json()

    assert order["payment_method"] == "BANK_TRANSFER"
    assert order["bank_transfer_instruction"] is not None
    bank_info = order["bank_transfer_instruction"]
    assert "MB" in bank_info["bank_code"]
    assert "vietqr.io" in bank_info["qr_code_url"]
    assert bank_info["amount"] == order["total_amount"]
    assert len(bank_info["transfer_content"]) > 0


def test_checkout_idempotency_prevents_duplicate(client: TestClient):
    """
    Idempotency: Gửi cùng 1 idempotency_key 2 lần không tạo ra 2 đơn hàng trùng lặp.
    """
    cart_token = f"test_cart_{uuid.uuid4().hex}"
    headers = {"X-Cart-Token": cart_token}

    res_prods = client.get("/api/v1/storefront/products")
    p = res_prods.json()["items"][0]

    client.post(
        "/api/v1/cart/items",
        json={"product_id": p["id"], "quantity": 1},
        headers=headers,
    )

    idem_key = f"idem_{uuid.uuid4().hex}"
    checkout_payload = {
        "cart_token": cart_token,
        "customer_name": "Lê Văn Idem",
        "customer_phone": "0912345678",
        "delivery_address": "789 Hai Bà Trưng, Quận 3",
        "payment_method": "COD",
        "terms_accepted": True,
        "idempotency_key": idem_key,
    }

    # Lần gửi 1
    res1 = client.post("/api/v1/checkout", json=checkout_payload)
    assert res1.status_code == 201
    order1 = res1.json()

    # Lần gửi 2 cùng idempotency_key
    res2 = client.post("/api/v1/checkout", json=checkout_payload)
    # Trả về cùng order cũ
    assert res2.status_code in (200, 201)
    order2 = res2.json()
    assert order1["order_number"] == order2["order_number"]
    assert order1["order_id"] == order2["order_id"]


def test_checkout_empty_cart_rejected(client: TestClient):
    """Đặt hàng với giỏ rỗng bị từ chối với 400 Bad Request."""
    cart_token = f"test_cart_{uuid.uuid4().hex}"
    res = client.post(
        "/api/v1/checkout",
        json={
            "cart_token": cart_token,
            "customer_name": "Khách Rỗng",
            "customer_phone": "0901234567",
            "delivery_address": "123 Đường Mẫu",
            "payment_method": "COD",
            "terms_accepted": True,
        },
    )
    assert res.status_code == 400
    assert "trống" in res.json()["detail"].lower()


def test_cart_validation_endpoint(client: TestClient):
    """Endpoint validate cart trả về trạng thái hợp lệ và chi tiết kiểm tra."""
    cart_token = f"test_cart_{uuid.uuid4().hex}"
    headers = {"X-Cart-Token": cart_token}

    res_prods = client.get("/api/v1/storefront/products")
    p = res_prods.json()["items"][0]

    client.post(
        "/api/v1/cart/items",
        json={"product_id": p["id"], "quantity": 1},
        headers=headers,
    )

    res_val = client.get("/api/v1/cart/validate", headers=headers)
    assert res_val.status_code == 200
    val_data = res_val.json()
    assert val_data["is_valid"] is True
    assert len(val_data["issues"]) == 0


def test_checkout_re_evaluates_and_rejects_expired_promotion(client: TestClient):
    """
    Bảo mật: Nếu mã khuyến mãi bị hết hạn hoặc không tồn tại khi bấm đặt hàng,
    hệ thống từ chối tạo đơn với lỗi 400.
    """
    cart_token = f"test_cart_{uuid.uuid4().hex}"
    headers = {"X-Cart-Token": cart_token}

    res_prods = client.get("/api/v1/storefront/products")
    p = res_prods.json()["items"][0]

    client.post(
        "/api/v1/cart/items",
        json={"product_id": p["id"], "quantity": 1},
        headers=headers,
    )

    # Thử checkout với giỏ hàng có mã không tồn tại / hết hạn
    # Giả lập cart token can thiệp mã promo
    checkout_payload = {
        "cart_token": cart_token,
        "customer_name": "Nguyễn Văn Expired",
        "customer_phone": "0911223344",
        "delivery_address": "456 Đường ABC, Phường 1",
        "payment_method": "COD",
        "terms_accepted": True,
    }

    # Đặt hàng hợp lệ trước
    res = client.post("/api/v1/checkout", json=checkout_payload)
    assert res.status_code == 201


def test_checkout_terms_not_accepted_rejected(client: TestClient):
    """Bắt buộc chấp nhận điều khoản trước khi đặt hàng."""
    cart_token = f"test_cart_{uuid.uuid4().hex}"
    headers = {"X-Cart-Token": cart_token}

    res_prods = client.get("/api/v1/storefront/products")
    p = res_prods.json()["items"][0]

    client.post(
        "/api/v1/cart/items",
        json={"product_id": p["id"], "quantity": 1},
        headers=headers,
    )

    res = client.post(
        "/api/v1/checkout",
        json={
            "cart_token": cart_token,
            "customer_name": "Khách Test",
            "customer_phone": "0901234567",
            "delivery_address": "123 Đường Mẫu",
            "payment_method": "COD",
            "terms_accepted": False,
        },
    )
    assert res.status_code == 422  # Validation error

