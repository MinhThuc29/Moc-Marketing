import pytest
from fastapi.testclient import TestClient


def test_get_storefront_home_unauthenticated(client: TestClient):
    """Khách vãng lai có thể truy cập trang chủ storefront không cần token."""
    response = client.get("/api/v1/storefront/home")
    assert response.status_code == 200
    data = response.json()

    assert "categories" in data
    assert "featured_products" in data
    assert "banners" in data
    assert "active_vouchers" in data
    assert "category_sections" in data

    assert len(data["categories"]) >= 5
    assert len(data["featured_products"]) >= 1


def test_list_storefront_products_public(client: TestClient):
    """Khách hàng duyệt danh sách sản phẩm công khai, chỉ thấy sản phẩm ACTIVE."""
    response = client.get("/api/v1/storefront/products")
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert data["total"] >= 10
    for item in data["items"]:
        assert item["status"] == "ACTIVE"
        # Bảo mật: không lộ giá vốn nội bộ
        assert "cost_price" not in item


def test_storefront_products_search_and_filter(client: TestClient):
    """Tìm kiếm sản phẩm theo từ khóa và lọc theo danh mục slug."""
    # 1. Tìm kiếm theo tên
    res_search = client.get("/api/v1/storefront/products?q=táo")
    assert res_search.status_code == 200
    search_data = res_search.json()
    assert search_data["total"] >= 1
    for p in search_data["items"]:
        assert "táo" in p["name"].lower() or "táo" in (p["short_description"] or "").lower()

    # 2. Lọc theo category slug
    res_cat = client.get("/api/v1/storefront/products?category_slug=trai-cay-tuoi")
    assert res_cat.status_code == 200
    cat_data = res_cat.json()
    assert cat_data["total"] >= 1
    for p in cat_data["items"]:
        assert p["category_slug"] == "trai-cay-tuoi"


def test_storefront_product_detail_by_slug(client: TestClient):
    """Xem chi tiết sản phẩm theo slug kèm danh sách gợi ý liên quan."""
    response = client.get("/api/v1/storefront/products/tao-new-zealand-gion-ngot")
    assert response.status_code == 200
    data = response.json()

    assert data["slug"] == "tao-new-zealand-gion-ngot"
    assert data["name"] == "Táo New Zealand giòn ngọt"
    assert "related_products" in data
    assert isinstance(data["related_products"], list)


def test_storefront_product_not_found(client: TestClient):
    """Truy vấn sản phẩm không tồn tại trả về 404."""
    response = client.get("/api/v1/storefront/products/non-existent-product-slug-xyz")
    assert response.status_code == 404
    assert "Không tìm thấy" in response.json()["detail"]


def test_storefront_categories_list(client: TestClient):
    """Lấy danh mục sản phẩm công khai kèm số lượng sản phẩm."""
    response = client.get("/api/v1/storefront/categories")
    assert response.status_code == 200
    categories = response.json()

    assert len(categories) >= 5
    slugs = [c["slug"] for c in categories]
    assert "trai-cay-tuoi" in slugs
    assert "nuoc-ep-nguyen-chat" in slugs

    # Mỗi danh mục có product_count >= 0
    for c in categories:
        assert c["product_count"] >= 0


def test_storefront_promotions_list(client: TestClient):
    """Lấy danh sách ưu đãi và voucher đang kích hoạt công khai."""
    response = client.get("/api/v1/storefront/promotions")
    assert response.status_code == 200
    promos = response.json()

    assert len(promos) >= 3
    codes = [p["code"] for p in promos if p["code"]]
    assert "WELCOME20" in codes or "FREESHIP" in codes
