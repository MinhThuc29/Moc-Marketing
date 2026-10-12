import pytest
from fastapi.testclient import TestClient


def test_automation_crud_and_validation(client: TestClient, admin_headers: dict):
    # 1. Create a custom workflow
    payload = {
        "name": "Kịch bản tri ân khách hàng thân thiết VIP",
        "code": "WF-CUSTOM-VIP-01",
        "description": "Tự động gửi lời chúc và voucher sinh nhật",
        "trigger_type": "CUSTOMER_INACTIVE",
        "trigger_config": {"inactive_days": 15},
        "conditions": [
            {"field": "segment", "operator": "eq", "value": "VIP"},
            {"field": "total_spent", "operator": "gte", "value": 500000},
        ],
        "actions": [
            {
                "type": "SEND_ZALO_MOCK",
                "template": "vip_tribute",
                "message": "Kính chào {customer_name}, Mộc Healthy tri ân khách hàng VIP!",
            },
            {
                "type": "ADD_LOYALTY_POINTS",
                "points": 50,
            },
            {
                "type": "ISSUE_PROMOTION",
                "promotion_code": "HEALTHY30K",
            },
        ],
        "status": "ACTIVE",
        "is_system_template": False,
    }
    res = client.post("/api/v1/automation/workflows", json=payload, headers=admin_headers)
    assert res.status_code == 201
    wf = res.json()
    assert wf["code"] == "WF-CUSTOM-VIP-01"
    assert wf["status"] == "ACTIVE"
    assert len(wf["conditions"]) == 2
    assert len(wf["actions"]) == 3
    wf_id = wf["id"]

    # 2. Reject duplicate code
    dup_res = client.post("/api/v1/automation/workflows", json=payload, headers=admin_headers)
    assert dup_res.status_code == 400
    assert "đã tồn tại" in dup_res.json()["detail"]

    # 3. Get workflow detail
    get_res = client.get(f"/api/v1/automation/workflows/{wf_id}", headers=admin_headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == wf_id
    assert "recent_runs" in get_res.json()

    # 4. Update workflow
    update_res = client.put(
        f"/api/v1/automation/workflows/{wf_id}",
        json={"name": "Kịch bản VIP Cập nhật", "description": "Mô tả mới đã chỉnh sửa"},
        headers=admin_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Kịch bản VIP Cập nhật"

    # 5. Delete custom workflow
    del_res = client.delete(f"/api/v1/automation/workflows/{wf_id}", headers=admin_headers)
    assert del_res.status_code == 200

    # 6. Verify 404 after deletion
    get_after_del = client.get(f"/api/v1/automation/workflows/{wf_id}", headers=admin_headers)
    assert get_after_del.status_code == 404


def test_automation_status_toggle_and_protected_templates(client: TestClient, admin_headers: dict):
    # 1. Query seeded system templates
    list_res = client.get("/api/v1/automation/workflows?limit=10", headers=admin_headers)
    assert list_res.status_code == 200
    workflows = list_res.json()["items"]
    assert len(workflows) >= 5

    welcome_wf = next((w for w in workflows if w["code"] == "WF-WELCOME-01"), None)
    assert welcome_wf is not None
    assert welcome_wf["is_system_template"] is True
    wf_id = welcome_wf["id"]

    # 2. Toggle status to PAUSED
    pause_res = client.patch(
        f"/api/v1/automation/workflows/{wf_id}/status",
        json={"status": "PAUSED"},
        headers=admin_headers,
    )
    assert pause_res.status_code == 200
    assert pause_res.json()["status"] == "PAUSED"

    # 3. Toggle back to ACTIVE
    active_res = client.patch(
        f"/api/v1/automation/workflows/{wf_id}/status",
        json={"status": "ACTIVE"},
        headers=admin_headers,
    )
    assert active_res.status_code == 200
    assert active_res.json()["status"] == "ACTIVE"

    # 4. Attempting to delete system template must be rejected
    del_res = client.delete(f"/api/v1/automation/workflows/{wf_id}", headers=admin_headers)
    assert del_res.status_code == 400
    assert "Không thể xóa kịch bản hệ thống" in del_res.json()["detail"]


def test_trigger_dispatch_and_execution_flow(client: TestClient, admin_headers: dict):
    # 1. Dispatch CUSTOMER_CREATED with consent=True -> should trigger WF-WELCOME-01
    payload_match = {
        "trigger_type": "CUSTOMER_CREATED",
        "source_id": "cust-test-auto-01",
        "context": {
            "customer_name": "Đặng Lan Anh",
            "customer_phone": "0988001122",
            "customer_email": "lananh@example.com",
            "consent_marketing": True,
        },
    }
    dispatch_res = client.post("/api/v1/automation/triggers/dispatch", json=payload_match, headers=admin_headers)
    assert dispatch_res.status_code == 200
    res_data = dispatch_res.json()
    assert res_data["trigger_type"] == "CUSTOMER_CREATED"
    assert res_data["matched_workflows_count"] >= 1
    assert res_data["executed_runs_count"] >= 1
    assert len(res_data["run_ids"]) >= 1

    run_id = res_data["run_ids"][0]

    # 2. Check the created run details
    run_res = client.get(f"/api/v1/automation/runs/{run_id}", headers=admin_headers)
    assert run_res.status_code == 200
    run_detail = run_res.json()
    assert run_detail["id"] == run_id
    assert run_detail["status"] == "SUCCESS"
    assert len(run_detail["step_runs"]) >= 3
    assert run_detail["step_runs"][0]["action_type"] == "SEND_ZALO_MOCK"

    # 3. Dispatch CUSTOMER_CREATED with consent=False -> condition fails, 0 runs executed
    payload_no_consent = {
        "trigger_type": "CUSTOMER_CREATED",
        "source_id": "cust-test-no-consent",
        "context": {
            "customer_name": "Khách không nhận tin",
            "customer_phone": "0988001133",
            "consent_marketing": False,
        },
    }
    dispatch_no_match = client.post("/api/v1/automation/triggers/dispatch", json=payload_no_consent, headers=admin_headers)
    assert dispatch_no_match.status_code == 200
    no_match_data = dispatch_no_match.json()
    assert no_match_data["executed_runs_count"] == 0


def test_test_run_dry_run_endpoint(client: TestClient, admin_headers: dict):
    # 1. Query WF-ABANDONED-CART-01
    list_res = client.get("/api/v1/automation/workflows?trigger_type=CART_ABANDONED", headers=admin_headers)
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert len(items) > 0
    wf_id = items[0]["id"]

    # 2. Test-run with cart_total >= 80,000 (Pass condition)
    pass_payload = {
        "test_context": {
            "customer_name": "Phan Hoài Nam",
            "customer_phone": "0911223399",
            "cart_total": 150000,
        }
    }
    test_res = client.post(f"/api/v1/automation/workflows/{wf_id}/test-run", json=pass_payload, headers=admin_headers)
    assert test_res.status_code == 200
    test_data = test_res.json()
    assert test_data["workflow_id"] == wf_id
    assert test_data["conditions_passed"] is True
    assert test_data["status"] == "SUCCESS"
    assert len(test_data["step_runs"]) > 0

    # 3. Test-run with cart_total < 80,000 (Fail condition)
    fail_payload = {
        "test_context": {
            "customer_name": "Phan Hoài Nam",
            "customer_phone": "0911223399",
            "cart_total": 45000,
        }
    }
    test_fail_res = client.post(f"/api/v1/automation/workflows/{wf_id}/test-run", json=fail_payload, headers=admin_headers)
    assert test_fail_res.status_code == 200
    test_fail_data = test_fail_res.json()
    assert test_fail_data["conditions_passed"] is False
    assert test_fail_data["status"] == "CONDITIONS_UNMET"
    assert len(test_fail_data["step_runs"]) == 0


def test_automation_overview_and_runs_list(client: TestClient, admin_headers: dict):
    # 1. Get overview stats
    stats_res = client.get("/api/v1/automation/overview", headers=admin_headers)
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_workflows"] >= 5
    assert stats["active_workflows"] >= 1
    assert stats["total_runs"] >= 0
    assert 0.0 <= stats["success_rate"] <= 100.0

    # 2. List execution runs with pagination
    runs_res = client.get("/api/v1/automation/runs?page=1&limit=10", headers=admin_headers)
    assert runs_res.status_code == 200
    runs_data = runs_res.json()
    assert "items" in runs_data
    assert "total" in runs_data
    assert runs_data["total"] >= 1


def test_automation_rbac_protection(client: TestClient):
    # 1. Unauthenticated requests should return 401
    assert client.get("/api/v1/automation/overview").status_code == 401
    assert client.get("/api/v1/automation/workflows").status_code == 401
    assert client.post("/api/v1/automation/workflows", json={}).status_code == 401
    assert client.get("/api/v1/automation/runs").status_code == 401
