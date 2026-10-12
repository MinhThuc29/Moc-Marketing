import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient


def test_ai_content_generation(client: TestClient, admin_headers: dict):
    # 1. Lấy sản phẩm có sẵn
    prod_res = client.get("/api/v1/products?limit=1", headers=admin_headers)
    assert prod_res.status_code == 200
    products = prod_res.json()["items"]
    product_id = products[0]["id"] if products else None

    # 2. Sinh nội dung Facebook Post bằng AI Studio
    ai_payload = {
        "product_id": product_id,
        "channel": "FACEBOOK",
        "content_type": "FACEBOOK_POST",
        "brand_tone": "FRESH_ENERGETIC",
        "custom_instruction": "Tập trung vào lợi ích giảm 2kg lành mạnh trong 14 ngày",
        "num_variants": 2,
    }
    gen_res = client.post("/api/v1/content/generate-ai", json=ai_payload, headers=admin_headers)
    assert gen_res.status_code == 200
    gen_data = gen_res.json()
    assert "variants" in gen_data
    assert len(gen_data["variants"]) == 2
    for var in gen_data["variants"]:
        assert len(var["title"]) > 0
        assert len(var["hook"]) > 0
        assert len(var["body"]) > 0
        assert len(var["cta"]) > 0
        assert isinstance(var["hashtags"], list)
        assert len(var["hashtags"]) > 0
        assert len(var["rationale"]) > 0

    # 3. Sinh kịch bản video ngắn TikTok
    tiktok_payload = {
        "product_id": product_id,
        "channel": "TIKTOK",
        "content_type": "TIKTOK_SCRIPT",
        "brand_tone": "TRENDY_HUMOR",
        "num_variants": 1,
    }
    tt_res = client.post("/api/v1/content/generate-ai", json=tiktok_payload, headers=admin_headers)
    assert tt_res.status_code == 200
    tt_data = tt_res.json()
    assert len(tt_data["variants"]) == 1
    variant = tt_data["variants"][0]
    assert variant["storyboard_suggestion"] is not None


def test_content_crud_and_validation(client: TestClient, admin_headers: dict):
    # 1. Tạo bài viết thủ công
    payload = {
        "title": "Bí quyết nạp năng lượng xanh cho tuần làm việc mới",
        "content_type": "FACEBOOK_POST",
        "channel": "FACEBOOK",
        "brand_tone": "FRESH_ENERGETIC",
        "hook": "Thứ 2 thức dậy uể oải? Đây là giải pháp cho bạn!",
        "body": "Bắt đầu ngày mới với một chai nước ép cần tây táo xanh tươi mát của Mộc Healthy. Giúp thanh lọc cơ thể và duy trì tỉnh táo suốt cả ngày làm việc căng thẳng.",
        "cta": "Inbox ngay để đặt giao tận bàn văn phòng lúc 9h sáng nhé!",
        "hashtags": ["#MocHealthy", "#NangLuongXanh", "#EatClean"],
    }
    create_res = client.post("/api/v1/content", json=payload, headers=admin_headers)
    assert create_res.status_code == 201
    item = create_res.json()
    assert item["title"] == payload["title"]
    assert item["status"] == "DRAFT"
    assert item["channel"] == "FACEBOOK"
    assert len(item["hashtags"]) == 3
    content_id = item["id"]

    # 2. Xem chi tiết bài viết
    get_res = client.get(f"/api/v1/content/{content_id}", headers=admin_headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == content_id

    # 3. Cập nhật bài viết
    update_res = client.put(
        f"/api/v1/content/{content_id}",
        json={
            "title": "Bí quyết nạp năng lượng xanh cho tuần làm việc mới (Cập nhật)",
            "hook": "Bữa sáng dinh dưỡng chỉ trong 3 phút!",
        },
        headers=admin_headers,
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["title"] == "Bí quyết nạp năng lượng xanh cho tuần làm việc mới (Cập nhật)"
    assert updated["hook"] == "Bữa sáng dinh dưỡng chỉ trong 3 phút!"


def test_content_review_and_approval_workflow(client: TestClient, admin_headers: dict):
    # 1. Tạo bài viết DRAFT
    create_res = client.post(
        "/api/v1/content",
        json={
            "title": "Ra mắt dòng sản phẩm Sữa hạt Mè Đen",
            "content_type": "INSTAGRAM_POST",
            "channel": "INSTAGRAM",
            "brand_tone": "NUTRITION_EXPERT",
            "body": "Sữa hạt mè đen giàu canxi tự nhiên, thơm ngon béo ngậy mà không ngấy.",
        },
        headers=admin_headers,
    )
    assert create_res.status_code == 201
    content_id = create_res.json()["id"]

    # 2. Gửi duyệt (DRAFT -> IN_REVIEW)
    review_res = client.post(f"/api/v1/content/{content_id}/submit-review", headers=admin_headers)
    assert review_res.status_code == 200
    assert review_res.json()["status"] == "IN_REVIEW"

    # 3. Phê duyệt bài viết (IN_REVIEW -> APPROVED)
    approve_res = client.post(f"/api/v1/content/{content_id}/approve", headers=admin_headers)
    assert approve_res.status_code == 200
    approved_item = approve_res.json()
    assert approved_item["status"] == "APPROVED"
    assert approved_item["approved_by_user_id"] is not None
    assert approved_item["approved_at"] is not None


def test_content_schedule_and_instant_publish(client: TestClient, admin_headers: dict):
    # 1. Tạo và duyệt bài viết
    create_res = client.post(
        "/api/v1/content",
        json={
            "title": "Flash Sale Giờ Vàng 14h - Giảm 30% Set Detox",
            "content_type": "ZALO_MESSAGE",
            "channel": "ZALO",
            "brand_tone": "WARM_FRIENDLY",
            "body": "Ưu đãi chớp nhoáng chỉ trong 2 tiếng buổi chiều cho các tín đồ mê nước ép tươi.",
        },
        headers=admin_headers,
    )
    assert create_res.status_code == 201
    content_id = create_res.json()["id"]

    client.post(f"/api/v1/content/{content_id}/submit-review", headers=admin_headers)
    client.post(f"/api/v1/content/{content_id}/approve", headers=admin_headers)

    # 2. Lên lịch xuất bản (SCHEDULED)
    now = datetime.now(timezone.utc)
    schedule_time = now + timedelta(days=2)
    sch_res = client.post(
        f"/api/v1/content/{content_id}/schedule",
        json={"scheduled_at": schedule_time.isoformat()},
        headers=admin_headers,
    )
    assert sch_res.status_code == 200
    assert sch_res.json()["status"] == "SCHEDULED"
    assert sch_res.json()["scheduled_at"] is not None

    # 3. Xuất bản ngay sang mạng xã hội (PUBLISHED)
    pub_res = client.post(f"/api/v1/content/{content_id}/publish", headers=admin_headers)
    assert pub_res.status_code == 200
    published_item = pub_res.json()
    assert published_item["status"] == "PUBLISHED"
    assert published_item["external_post_id"] is not None
    assert published_item["external_post_url"] is not None
    assert published_item["published_at"] is not None
    assert isinstance(published_item["metrics"], dict)

    # 4. Kiểm tra không cho phép xóa bài đã PUBLISHED
    del_res = client.delete(f"/api/v1/content/{content_id}", headers=admin_headers)
    assert del_res.status_code == 400
    assert "đã xuất bản" in del_res.json()["detail"]


def test_content_calendar_and_overview_stats(client: TestClient, admin_headers: dict):
    # 1. Lấy danh sách nội dung
    list_res = client.get("/api/v1/content?page=1&page_size=10", headers=admin_headers)
    assert list_res.status_code == 200
    data = list_res.json()
    assert "items" in data
    assert "total" in data

    # 2. Lấy dữ liệu Content Calendar
    cal_res = client.get("/api/v1/content/calendar", headers=admin_headers)
    assert cal_res.status_code == 200
    assert isinstance(cal_res.json(), list)

    # 3. Lấy thống kê tổng quan
    overview_res = client.get("/api/v1/content/overview", headers=admin_headers)
    assert overview_res.status_code == 200
    stats = overview_res.json()
    assert "total_items" in stats
    assert "published_items" in stats
    assert "scheduled_items" in stats
    assert "in_review_items" in stats
    assert "ai_generated_items" in stats


def test_content_delete_draft(client: TestClient, admin_headers: dict):
    # 1. Tạo bản nháp
    create_res = client.post(
        "/api/v1/content",
        json={
            "title": "Bản nháp thử nghiệm xóa",
            "body": "Nội dung bài viết tạm thời để kiểm thử chức năng xóa bài.",
        },
        headers=admin_headers,
    )
    assert create_res.status_code == 201
    content_id = create_res.json()["id"]

    # 2. Xóa bài viết
    del_res = client.delete(f"/api/v1/content/{content_id}", headers=admin_headers)
    assert del_res.status_code == 200
    assert "Đã xóa bài viết thành công" in del_res.json()["message"]

    # 3. Kiểm tra 404
    get_res = client.get(f"/api/v1/content/{content_id}", headers=admin_headers)
    assert get_res.status_code == 404
