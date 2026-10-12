import pytest
from fastapi.testclient import TestClient


def test_recommendations_overview_and_list(client: TestClient, admin_headers: dict):
    """
    Kiểm tra endpoint tổng quan Overview và danh sách đề xuất AI.
    """
    # 1. Overview
    res = client.get("/api/v1/recommendations/overview", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_recommendations" in data
    assert "pending_count" in data
    assert "high_confidence_count" in data
    assert "active_alerts_count" in data
    assert data["total_recommendations"] >= 4
    assert data["pending_count"] >= 1
    assert data["high_confidence_count"] >= 1
    assert data["active_alerts_count"] >= 1

    # 2. List recommendations
    res_list = client.get("/api/v1/recommendations", headers=admin_headers)
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert "items" in list_data
    assert len(list_data["items"]) >= 4

    first_item = list_data["items"][0]
    assert "id" in first_item
    assert "title" in first_item
    assert "problem_statement" in first_item
    assert "recommended_action" in first_item
    assert "evidence" in first_item
    assert len(first_item["evidence"]) > 0
    # Kiểm tra bằng chứng số học
    assert "metric" in first_item["evidence"][0]
    assert "value" in first_item["evidence"][0]
    assert "source" in first_item["evidence"][0]

    # 3. Filter by type
    res_filter = client.get("/api/v1/recommendations?type=INVENTORY_CLEARANCE", headers=admin_headers)
    assert res_filter.status_code == 200
    filter_data = res_filter.json()
    assert all(it["recommendation_type"] == "INVENTORY_CLEARANCE" for it in filter_data["items"])


def test_recommendation_generate_scanner(client: TestClient, admin_headers: dict):
    """
    Kiểm tra AI Marketing Strategist quét DB thực tế và sinh các khuyến nghị chuẩn xác.
    """
    res = client.post(
        "/api/v1/recommendations/generate",
        json={"force_regenerate": True},
        headers=admin_headers,
    )
    assert res.status_code == 200
    recs = res.json()
    assert len(recs) >= 1

    # Đảm bảo mọi đề xuất đều có evidence thực tế và confidence
    for rec in recs:
        assert rec["confidence_score"] > 0.0
        assert rec["confidence_level"] in ["HIGH", "MEDIUM", "LOW"]
        assert isinstance(rec["evidence"], list)
        assert len(rec["evidence"]) >= 1
        for ev in rec["evidence"]:
            assert "metric" in ev
            assert "value" in ev
            assert "comparison" in ev


def test_1click_convert_to_campaign(client: TestClient, admin_headers: dict):
    """
    Kiểm tra tính năng 1-Click Convert từ Đề xuất AI sang Bản nháp Chiến dịch tiếp thị (Campaign Draft).
    """
    # Lấy danh sách đề xuất pending
    res = client.get("/api/v1/recommendations?status=PENDING", headers=admin_headers)
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) > 0
    target_rec = items[0]

    # Thực hiện 1-Click Convert
    convert_res = client.post(
        f"/api/v1/recommendations/{target_rec['id']}/convert-to-campaign",
        json={"custom_name": "Chiến Dịch Sinh Tự Động Từ AI", "budget": 1500000},
        headers=admin_headers,
    )
    assert convert_res.status_code == 200
    result_data = convert_res.json()
    assert result_data["success"] is True
    assert "campaign_id" in result_data
    campaign_id = result_data["campaign_id"]

    # Kiểm tra trạng thái đề xuất đã cập nhật thành APPLIED
    detail_res = client.get(f"/api/v1/recommendations/{target_rec['id']}", headers=admin_headers)
    assert detail_res.status_code == 200
    rec_detail = detail_res.json()
    assert rec_detail["status"] == "APPLIED"
    assert rec_detail["converted_campaign_id"] == campaign_id
    assert rec_detail["applied_at"] is not None

    # Kiểm tra chiến dịch mới được tạo trong Campaign Hub
    camp_res = client.get(f"/api/v1/campaigns/{campaign_id}", headers=admin_headers)
    assert camp_res.status_code == 200
    camp_detail = camp_res.json()
    assert camp_detail["name"] == "Chiến Dịch Sinh Tự Động Từ AI"
    assert camp_detail["status"] == "DRAFT"
    assert float(camp_detail["budget"]) == 1500000.0


def test_1click_convert_to_automation(client: TestClient, admin_headers: dict):
    """
    Kiểm tra tính năng 1-Click Convert từ Đề xuất AI sang Kịch bản Tự động hóa (Automation Workflow).
    """
    # Lấy một đề xuất PENDING khác
    res = client.get("/api/v1/recommendations?status=PENDING", headers=admin_headers)
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) > 0
    target_rec = items[0]

    # Convert to automation workflow
    convert_res = client.post(
        f"/api/v1/recommendations/{target_rec['id']}/convert-to-automation",
        json={"custom_name": "Quy Trình Tự Động Từ Khuyến Nghị AI"},
        headers=admin_headers,
    )
    assert convert_res.status_code == 200
    result_data = convert_res.json()
    assert result_data["success"] is True
    assert "workflow_id" in result_data
    wf_id = result_data["workflow_id"]

    # Kiểm tra đề xuất đã chuyển sang APPLIED
    detail_res = client.get(f"/api/v1/recommendations/{target_rec['id']}", headers=admin_headers)
    assert detail_res.json()["status"] == "APPLIED"
    assert detail_res.json()["converted_workflow_id"] == wf_id

    # Kiểm tra workflow tồn tại trong Automation Module
    wf_res = client.get(f"/api/v1/automation/workflows/{wf_id}", headers=admin_headers)
    assert wf_res.status_code == 200
    wf_detail = wf_res.json()
    assert wf_detail["name"] == "Quy Trình Tự Động Từ Khuyến Nghị AI"
    assert wf_detail["status"] == "ACTIVE"


def test_dismiss_recommendation(client: TestClient, admin_headers: dict):
    """
    Kiểm tra chức năng bỏ qua đề xuất (Dismiss) kèm ghi chú lý do.
    """
    # Lấy 1 đề xuất PENDING
    res = client.get("/api/v1/recommendations?status=PENDING", headers=admin_headers)
    items = res.json()["items"]
    assert len(items) > 0
    target_rec = items[0]

    dismiss_res = client.post(
        f"/api/v1/recommendations/{target_rec['id']}/dismiss",
        json={"reason": "Không ưu tiên thực hiện trong tuần này"},
        headers=admin_headers,
    )
    assert dismiss_res.status_code == 200
    dismissed_data = dismiss_res.json()
    assert dismissed_data["status"] == "DISMISSED"
    assert dismissed_data["dismiss_reason"] == "Không ưu tiên thực hiện trong tuần này"


def test_smart_alerts_workflow(client: TestClient, admin_headers: dict):
    """
    Kiểm tra vòng đời Cảnh báo Thông minh (Smart Alerts):
    Summary -> List -> Trigger Scan -> Acknowledge -> Resolve.
    """
    # 1. Summary
    res_sum = client.get("/api/v1/alerts/summary", headers=admin_headers)
    assert res_sum.status_code == 200
    summary = res_sum.json()
    assert "critical" in summary
    assert "warning" in summary
    assert "total_active" in summary
    assert summary["total_active"] >= 1

    # 2. List alerts
    res_list = client.get("/api/v1/alerts?status=ACTIVE", headers=admin_headers)
    assert res_list.status_code == 200
    alerts = res_list.json()["items"]
    assert len(alerts) >= 1
    first_alert = alerts[0]
    alert_id = first_alert["id"]

    # 3. Trigger alert scanner
    res_scan = client.post("/api/v1/alerts/scan", headers=admin_headers)
    assert res_scan.status_code == 200

    # 4. Acknowledge alert
    res_ack = client.post(f"/api/v1/alerts/{alert_id}/acknowledge", headers=admin_headers)
    assert res_ack.status_code == 200
    assert res_ack.json()["status"] == "ACKNOWLEDGED"
    assert res_ack.json()["acknowledged_at"] is not None

    # 5. Resolve alert
    res_res = client.post(f"/api/v1/alerts/{alert_id}/resolve", headers=admin_headers)
    assert res_res.status_code == 200
    assert res_res.json()["status"] == "RESOLVED"
    assert res_res.json()["resolved_at"] is not None


def test_recommendations_rbac_enforcement(client: TestClient):
    """
    Kiểm tra phân quyền: Không được phép truy cập khi chưa đăng nhập.
    """
    res = client.get("/api/v1/recommendations/overview")
    assert res.status_code in [401, 403]

    res_post = client.post("/api/v1/recommendations/generate")
    assert res_post.status_code in [401, 403]
