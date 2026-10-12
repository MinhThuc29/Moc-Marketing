import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient


def test_campaign_crud_and_validation(client: TestClient, admin_headers: dict):
    now = datetime.now(timezone.utc)
    start_time = now + timedelta(days=1)
    end_time = now + timedelta(days=15)

    # 1. Lấy sản phẩm có sẵn để gắn vào chiến dịch
    prod_res = client.get("/api/v1/products?limit=2", headers=admin_headers)
    assert prod_res.status_code == 200
    prod_items = prod_res.json()["items"]
    product_id = prod_items[0]["id"] if prod_items else None

    # 2. Tạo chiến dịch mới
    payload = {
        "name": "Chiến dịch Năng Lượng Xanh Mùa Thu",
        "code": "CAMP-AUTUMN-2026",
        "objective": "CONVERSION",
        "start_at": start_time.isoformat(),
        "end_at": end_time.isoformat(),
        "budget": 15000000,
        "target_audience": ["VIP", "ACTIVE", "REPEAT"],
        "landing_page": "https://mochanh.vn/collections/autumn-green",
        "utm_source": "facebook",
        "utm_medium": "cpc",
        "utm_campaign": "autumn_green",
        "notes": "Chiến dịch trọng điểm tháng 10 đẩy mạnh dòng sữa hạt mè đen",
        "channels": [
            {
                "channel": "FACEBOOK",
                "channel_budget": 8000000,
                "target_metric": "500 conversions",
                "notes": "Target tệp nhân viên văn phòng 25-40 tuổi",
            },
            {
                "channel": "ZALO",
                "channel_budget": 4000000,
                "target_metric": "300 Zalo OA clicks",
                "notes": "Gửi ZNS cho khách hàng cũ",
            },
            {
                "channel": "TIKTOK",
                "channel_budget": 3000000,
                "target_metric": "50k video views",
                "notes": "Book 3 KOC healthy lifestyle",
            },
        ],
        "products": [
            {
                "product_id": product_id,
                "is_hero_product": True,
                "special_price": 55000,
            }
        ] if product_id else [],
    }

    create_res = client.post("/api/v1/campaigns", json=payload, headers=admin_headers)
    assert create_res.status_code == 201
    camp = create_res.json()
    assert camp["name"] == "Chiến dịch Năng Lượng Xanh Mùa Thu"
    assert camp["code"] == "CAMP-AUTUMN-2026"
    assert camp["status"] == "DRAFT"
    assert camp["budget"] == 15000000
    assert len(camp["channels"]) == 3
    if product_id:
        assert len(camp["products"]) == 1
        assert camp["products"][0]["is_hero_product"] is True
    camp_id = camp["id"]

    # 3. Kiểm tra mã chiến dịch trùng lặp
    dup_res = client.post("/api/v1/campaigns", json=payload, headers=admin_headers)
    assert dup_res.status_code == 400
    assert "đã tồn tại" in dup_res.json()["detail"]

    # 4. Kiểm tra validation ngày kết thúc trước ngày bắt đầu
    invalid_dates_payload = {
        **payload,
        "code": "CAMP-INVALID-DATES",
        "start_at": (now + timedelta(days=5)).isoformat(),
        "end_at": (now + timedelta(days=2)).isoformat(),
    }
    invalid_res = client.post("/api/v1/campaigns", json=invalid_dates_payload, headers=admin_headers)
    assert invalid_res.status_code == 400
    assert "sau thời gian bắt đầu" in invalid_res.json()["detail"]

    # 5. Lấy chi tiết chiến dịch
    get_res = client.get(f"/api/v1/campaigns/{camp_id}", headers=admin_headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == camp_id

    # 6. Cập nhật thông tin chiến dịch
    update_res = client.put(
        f"/api/v1/campaigns/{camp_id}",
        json={
            "name": "Chiến dịch Năng Lượng Xanh Mùa Thu (Mở Rộng)",
            "budget": 20000000,
        },
        headers=admin_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Chiến dịch Năng Lượng Xanh Mùa Thu (Mở Rộng)"
    assert update_res.json()["budget"] == 20000000


def test_campaign_workflow_review_approve_and_status(client: TestClient, admin_headers: dict):
    now = datetime.now(timezone.utc)
    start_time = now + timedelta(days=2)
    end_time = now + timedelta(days=10)

    # 1. Tạo campaign mới
    create_res = client.post(
        "/api/v1/campaigns",
        json={
            "name": "Chiến dịch Tri Ân Khách Hàng VIP Q4",
            "code": "CAMP-VIP-Q4",
            "objective": "LOYALTY",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "budget": 10000000,
            "target_audience": ["VIP"],
        },
        headers=admin_headers,
    )
    assert create_res.status_code == 201
    camp = create_res.json()
    camp_id = camp["id"]
    assert camp["status"] == "DRAFT"

    # 2. Gửi duyệt kế hoạch (DRAFT -> READY_FOR_REVIEW)
    review_res = client.post(f"/api/v1/campaigns/{camp_id}/submit-review", headers=admin_headers)
    assert review_res.status_code == 200
    assert review_res.json()["status"] == "READY_FOR_REVIEW"

    # 3. Gửi duyệt lần 2 khi đang READY_FOR_REVIEW sẽ báo lỗi
    repeat_review = client.post(f"/api/v1/campaigns/{camp_id}/submit-review", headers=admin_headers)
    assert repeat_review.status_code == 400

    # 4. Phê duyệt chiến dịch (READY_FOR_REVIEW -> APPROVED)
    approve_res = client.post(f"/api/v1/campaigns/{camp_id}/approve", headers=admin_headers)
    assert approve_res.status_code == 200
    approved_camp = approve_res.json()
    assert approved_camp["status"] == "APPROVED"
    assert approved_camp["approved_by_user_id"] is not None
    assert approved_camp["approved_at"] is not None

    # 5. Kích hoạt chiến dịch chạy (APPROVED -> ACTIVE)
    active_res = client.post(
        f"/api/v1/campaigns/{camp_id}/status",
        json={"status": "ACTIVE"},
        headers=admin_headers,
    )
    assert active_res.status_code == 200
    assert active_res.json()["status"] == "ACTIVE"

    # 6. Kiểm tra không thể xóa chiến dịch ACTIVE
    del_active_res = client.delete(f"/api/v1/campaigns/{camp_id}", headers=admin_headers)
    assert del_active_res.status_code == 400

    # 7. Tạm dừng (ACTIVE -> PAUSED) rồi hoàn thành (PAUSED -> COMPLETED)
    pause_res = client.post(
        f"/api/v1/campaigns/{camp_id}/status",
        json={"status": "PAUSED"},
        headers=admin_headers,
    )
    assert pause_res.status_code == 200
    assert pause_res.json()["status"] == "PAUSED"

    complete_res = client.post(
        f"/api/v1/campaigns/{camp_id}/status",
        json={"status": "COMPLETED"},
        headers=admin_headers,
    )
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "COMPLETED"


def test_campaign_overview_and_filtering(client: TestClient, admin_headers: dict):
    # 1. Lấy danh sách chiến dịch
    list_res = client.get("/api/v1/campaigns?page=1&page_size=10", headers=admin_headers)
    assert list_res.status_code == 200
    data = list_res.json()
    assert "items" in data
    assert "total" in data
    assert data["page"] == 1

    # 2. Lọc theo trạng thái
    filter_res = client.get("/api/v1/campaigns?status=COMPLETED", headers=admin_headers)
    assert filter_res.status_code == 200
    for item in filter_res.json()["items"]:
        assert item["status"] == "COMPLETED"

    # 3. Lấy số liệu thống kê tổng quan
    overview_res = client.get("/api/v1/campaigns/overview", headers=admin_headers)
    assert overview_res.status_code == 200
    overview = overview_res.json()
    assert "active_campaigns" in overview
    assert "ready_for_review_campaigns" in overview
    assert "total_budget_approved" in overview
    assert "total_revenue_attributed" in overview
    assert "average_roi_percentage" in overview


def test_campaign_delete_draft(client: TestClient, admin_headers: dict):
    now = datetime.now(timezone.utc)
    create_res = client.post(
        "/api/v1/campaigns",
        json={
            "name": "Chiến dịch thử nghiệm xóa",
            "code": "CAMP-TEST-DEL",
            "objective": "AWARENESS",
            "start_at": (now + timedelta(days=1)).isoformat(),
            "end_at": (now + timedelta(days=3)).isoformat(),
            "budget": 1000000,
        },
        headers=admin_headers,
    )
    assert create_res.status_code == 201
    camp_id = create_res.json()["id"]

    del_res = client.delete(f"/api/v1/campaigns/{camp_id}", headers=admin_headers)
    assert del_res.status_code == 200
    assert "Đã xóa chiến dịch thành công" in del_res.json()["message"]

    # Verify 404
    get_res = client.get(f"/api/v1/campaigns/{camp_id}", headers=admin_headers)
    assert get_res.status_code == 404


def test_campaign_roi_and_metric_attribute(client: TestClient, admin_headers: dict):
    now = datetime.now(timezone.utc)
    create_res = client.post(
        "/api/v1/campaigns",
        json={
            "name": "Chiến dịch Đo lường Hiệu quả ROI",
            "code": "CAMP-ROI-METRIC",
            "objective": "CONVERSION",
            "start_at": (now + timedelta(days=1)).isoformat(),
            "end_at": (now + timedelta(days=10)).isoformat(),
            "budget": 10000000,
        },
        headers=admin_headers,
    )
    assert create_res.status_code == 201
    camp = create_res.json()
    assert camp["roi_percentage"] == 0.0

    # Lấy overview thống kê
    ov_res = client.get("/api/v1/campaigns/overview", headers=admin_headers)
    assert ov_res.status_code == 200
    ov_data = ov_res.json()
    assert isinstance(ov_data["active_campaigns"], int)
    assert isinstance(ov_data["total_budget_approved"], float)

