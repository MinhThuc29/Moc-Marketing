import pytest


# ==============================================================================
# CATEGORY TESTS
# ==============================================================================

def test_list_categories(client, admin_headers):
    res = client.get("/api/v1/categories", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 5
    slugs = [c["slug"] for c in data]
    assert "trai-cay-tuoi" in slugs
    assert "nuoc-ep-nguyen-chat" in slugs
    assert "tra-matcha-thanh-nhiet" in slugs


def test_get_category_by_slug(client, admin_headers):
    res = client.get("/api/v1/categories/trai-cay-tuoi", headers=admin_headers)
    assert res.status_code == 200
    cat = res.json()
    assert cat["name"] == "Trái cây tươi"
    assert cat["slug"] == "trai-cay-tuoi"
    assert cat["active"] is True


def test_create_category_success(client, admin_headers):
    payload = {
        "name": "Bánh healthy & Hạt dinh dưỡng",
        "slug": "banh-healthy-hat-dinh-duong",
        "description": "Bánh ăn kiêng và hạt sấy tự nhiên",
        "sort_order": 10,
        "active": True,
    }
    res = client.post("/api/v1/categories", json=payload, headers=admin_headers)
    assert res.status_code == 201
    created = res.json()
    assert created["name"] == payload["name"]
    assert created["slug"] == payload["slug"]
    assert created["sort_order"] == 10


def test_create_category_duplicate_slug_rejected(client, admin_headers):
    payload = {
        "name": "Trái cây tươi trùng lặp",
        "slug": "trai-cay-tuoi",
    }
    res = client.post("/api/v1/categories", json=payload, headers=admin_headers)
    assert res.status_code == 409
    assert "đã tồn tại" in res.json()["detail"]


def test_update_category(client, admin_headers):
    # First create a temporary category
    c_res = client.post(
        "/api/v1/categories",
        json={"name": "Temp Cat", "slug": "temp-cat-to-update"},
        headers=admin_headers,
    )
    cat_id = c_res.json()["id"]

    # Update it
    update_res = client.put(
        f"/api/v1/categories/{cat_id}",
        json={"name": "Temp Cat Updated", "sort_order": 99},
        headers=admin_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Temp Cat Updated"
    assert update_res.json()["sort_order"] == 99


def test_delete_category(client, admin_headers):
    c_res = client.post(
        "/api/v1/categories",
        json={"name": "Temp Cat To Delete", "slug": "temp-cat-to-delete"},
        headers=admin_headers,
    )
    cat_id = c_res.json()["id"]

    del_res = client.delete(f"/api/v1/categories/{cat_id}", headers=admin_headers)
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Ensure not found
    get_res = client.get(f"/api/v1/categories/{cat_id}", headers=admin_headers)
    assert get_res.status_code == 404


# ==============================================================================
# PRODUCT SEARCH, FILTER, PAGINATION TESTS
# ==============================================================================

def test_list_products_seeded(client, admin_headers):
    res = client.get("/api/v1/products", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 10
    assert len(data["items"]) >= 10


def test_search_product_by_name(client, admin_headers):
    res = client.get("/api/v1/products?q=Táo", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    names = [p["name"] for p in data["items"]]
    assert any("Táo" in n for n in names)


def test_search_product_by_sku(client, admin_headers):
    res = client.get("/api/v1/products?q=TEA-TRA-DAU", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["sku"] == "TEA-TRA-DAU"
    assert data["items"][0]["name"] == "Trà dâu tây"


def test_filter_product_by_featured(client, admin_headers):
    res = client.get("/api/v1/products?featured=true", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    for item in data["items"]:
        assert item["featured"] is True


def test_sort_products_by_price(client, admin_headers):
    res_asc = client.get("/api/v1/products?sort_by=price_asc", headers=admin_headers)
    assert res_asc.status_code == 200
    prices_asc = [p["base_price"] for p in res_asc.json()["items"]]
    assert prices_asc == sorted(prices_asc)

    res_desc = client.get("/api/v1/products?sort_by=price_desc", headers=admin_headers)
    assert res_desc.status_code == 200
    prices_desc = [p["base_price"] for p in res_desc.json()["items"]]
    assert prices_desc == sorted(prices_desc, reverse=True)


def test_pagination(client, admin_headers):
    res = client.get("/api/v1/products?page=1&page_size=3", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["page"] == 1
    assert data["page_size"] == 3
    assert len(data["items"]) == 3
    assert data["total"] >= 10
    assert data["total_pages"] >= 4


def test_get_product_detail_by_slug(client, admin_headers):
    res = client.get("/api/v1/products/tra-dau-tay", headers=admin_headers)
    assert res.status_code == 200
    prod = res.json()
    assert prod["sku"] == "TEA-TRA-DAU"
    assert prod["name"] == "Trà dâu tây"
    assert prod["base_price"] == 30000.0
    assert prod["sale_price"] == 25000.0
    assert prod["category"] is not None
    assert prod["category"]["slug"] == "tra-matcha-thanh-nhiet"
    assert len(prod["price_logs"]) >= 1


def test_get_product_not_found(client, admin_headers):
    res = client.get("/api/v1/products/non-existent-product-slug", headers=admin_headers)
    assert res.status_code == 404
    assert "Không tìm thấy" in res.json()["detail"]


# ==============================================================================
# PRICE VALIDATION & AUDIT LOGGING TESTS
# ==============================================================================

def test_create_product_sale_price_greater_than_base_price_rejected(client, admin_headers):
    invalid_payload = {
        "sku": "INVALID-PRICE-01",
        "name": "Sản phẩm giá sai",
        "base_price": 30000.0,
        "sale_price": 35000.0,  # Invalid: sale_price > base_price
        "unit": "ly",
    }
    res = client.post("/api/v1/products", json=invalid_payload, headers=admin_headers)
    assert res.status_code == 422
    assert "sale_price" in str(res.json()).lower() or "giá" in str(res.json()).lower()


def test_update_product_sale_price_greater_than_base_price_rejected(client, admin_headers):
    # Fetch existing product
    res = client.get("/api/v1/products/tra-dau-tay", headers=admin_headers)
    prod_id = res.json()["id"]

    # Try setting sale_price higher than current base_price (30000)
    update_res = client.put(
        f"/api/v1/products/{prod_id}",
        json={"sale_price": 40000.0},
        headers=admin_headers,
    )
    assert update_res.status_code == 422
    assert "sale_price" in str(update_res.json()).lower() or "giá" in str(update_res.json()).lower()


def test_price_audit_log_created_on_price_change(client, admin_headers):
    # 1. Create a fresh product
    payload = {
        "sku": "AUDIT-PROD-01",
        "name": "Sản phẩm kiểm toán giá",
        "base_price": 40000.0,
        "sale_price": 35000.0,
        "unit": "phần",
    }
    create_res = client.post("/api/v1/products", json=payload, headers=admin_headers)
    assert create_res.status_code == 201
    prod = create_res.json()
    prod_id = prod["id"]

    # 2. Update price
    update_payload = {
        "base_price": 45000.0,
        "sale_price": 38000.0,
        "change_reason": "Điều chỉnh theo giá nguyên liệu biến động",
    }
    update_res = client.put(
        f"/api/v1/products/{prod_id}",
        json=update_payload,
        headers=admin_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["base_price"] == 45000.0
    assert update_res.json()["sale_price"] == 38000.0

    # 3. Verify price audit history
    history_res = client.get(
        f"/api/v1/products/{prod_id}/price-history",
        headers=admin_headers,
    )
    assert history_res.status_code == 200
    logs = history_res.json()
    assert len(logs) == 2  # initial + 1 update

    latest_log = logs[0]
    assert latest_log["old_base_price"] == 40000.0
    assert latest_log["new_base_price"] == 45000.0
    assert latest_log["old_sale_price"] == 35000.0
    assert latest_log["new_sale_price"] == 38000.0
    assert latest_log["change_reason"] == "Điều chỉnh theo giá nguyên liệu biến động"


# ==============================================================================
# PERMISSION & RBAC ENFORCEMENT TESTS
# ==============================================================================

def test_unauthenticated_cannot_access_products(client):
    res = client.get("/api/v1/products")
    assert res.status_code == 401


def test_marketing_role_can_read_products(client, marketing_headers):
    # Marketing has 'product.read' -> can view products
    res = client.get("/api/v1/products", headers=marketing_headers)
    assert res.status_code == 200
    assert res.json()["total"] >= 10


def test_marketing_role_cannot_create_product(client, marketing_headers):
    # Marketing does NOT have 'product.write' -> 403 Forbidden
    payload = {
        "sku": "MKT-TEST-01",
        "name": "Marketing không được tạo",
        "base_price": 50000.0,
        "unit": "phần",
    }
    res = client.post("/api/v1/products", json=payload, headers=marketing_headers)
    assert res.status_code == 403
    assert "product.write" in res.json()["detail"]


def test_marketing_role_cannot_update_product(client, marketing_headers, admin_headers):
    # Get a product ID
    list_res = client.get("/api/v1/products", headers=admin_headers)
    prod_id = list_res.json()["items"][0]["id"]

    # Attempt update with marketing role
    res = client.put(
        f"/api/v1/products/{prod_id}",
        json={"name": "Hacking Name"},
        headers=marketing_headers,
    )
    assert res.status_code == 403
    assert "product.write" in res.json()["detail"]


def test_marketing_role_cannot_delete_product(client, marketing_headers, admin_headers):
    list_res = client.get("/api/v1/products", headers=admin_headers)
    prod_id = list_res.json()["items"][0]["id"]

    res = client.delete(f"/api/v1/products/{prod_id}", headers=marketing_headers)
    assert res.status_code == 403
    assert "product.write" in res.json()["detail"]


def test_marketing_role_cannot_bulk_update_status(client, marketing_headers):
    res = client.patch(
        "/api/v1/products/bulk-status",
        json={"ids": ["some-id"], "status": "ACTIVE"},
        headers=marketing_headers,
    )
    assert res.status_code == 403
    assert "product.write" in res.json()["detail"]


# ==============================================================================
# BULK STATUS & SOFT DELETE / ARCHIVING TESTS
# ==============================================================================

def test_bulk_status_update(client, admin_headers):
    # Create two test products
    p1 = client.post(
        "/api/v1/products",
        json={"sku": "BULK-01", "name": "Bulk Prod 1", "base_price": 10000.0},
        headers=admin_headers,
    ).json()
    p2 = client.post(
        "/api/v1/products",
        json={"sku": "BULK-02", "name": "Bulk Prod 2", "base_price": 20000.0},
        headers=admin_headers,
    ).json()

    # Bulk update to OUT_OF_STOCK
    bulk_res = client.patch(
        "/api/v1/products/bulk-status",
        json={"ids": [p1["id"], p2["id"]], "status": "OUT_OF_STOCK"},
        headers=admin_headers,
    )
    assert bulk_res.status_code == 200
    assert bulk_res.json()["updated_count"] == 2
    assert bulk_res.json()["status"] == "OUT_OF_STOCK"

    # Verify status changed
    check1 = client.get(f"/api/v1/products/{p1['id']}", headers=admin_headers).json()
    check2 = client.get(f"/api/v1/products/{p2['id']}", headers=admin_headers).json()
    assert check1["status"] == "OUT_OF_STOCK"
    assert check2["status"] == "OUT_OF_STOCK"


def test_soft_delete_archives_product(client, admin_headers):
    p = client.post(
        "/api/v1/products",
        json={"sku": "ARCHIVE-01", "name": "Prod To Archive", "base_price": 15000.0},
        headers=admin_headers,
    ).json()
    prod_id = p["id"]

    del_res = client.delete(f"/api/v1/products/{prod_id}", headers=admin_headers)
    assert del_res.status_code == 200
    assert "ARCHIVED" in del_res.json()["message"]

    # Verify product still exists in DB but with ARCHIVED status
    check = client.get(f"/api/v1/products/{prod_id}", headers=admin_headers).json()
    assert check["status"] == "ARCHIVED"
