import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient


SAMPLE_GRAB_CSV = """Order ID,Order Time,Customer Name,Phone,Address,Gross Sales,Merchant Promo,Commission,Net Payout,Items
GF-202610-001,2026-10-07 10:30,Trần Thanh Grab,0912345678,12 Lê Duẩn Q1,150000,10000,30000,110000,Nước Ép Cam Tươi x2; Salad Ức Gà x1
GF-202610-002,2026-10-07 11:15,Nguyễn Thu Hà,0987654321,45 Nguyễn Thị Minh Khai Q3,200000,0,40000,160000,Sinh Tố Bơ Healthy x2
GF-202610-003,2026-10-07 12:00,Lê Văn Tài xế,0933112233,88 Nam Kỳ Khởi Nghĩa,90000,5000,18000,67000,Sữa Chua Trái Cây x1
"""

SAMPLE_SHOPEE_CSV = """Shopee Order ID,Order Time,Customer,Phone,Address,Subtotal,Merchant Discount,Service Fee,Net Settlement,Items
SPF-9988-01,2026-10-07 13:00,Phạm Hùng Shopee,0901234567,100 Hai Bà Trưng Q1,180000,20000,45000,115000,Detox Rau Má x3
SPF-9988-02,2026-10-07 14:30,Đặng Bích Ngọc,0944556677,20 Pasteur Q1,240000,0,60000,180000,Combo Trái Cây 5 Màu x2
"""


def test_grabfood_report_preview_and_execute(client: TestClient, admin_headers: dict):
    # 1. Preview GrabFood import
    res_preview = client.post(
        "/api/v1/omnichannel/imports/preview-raw",
        json={
            "channel": "GRAB",
            "filename": "grab_report_20261007.csv",
            "raw_content": SAMPLE_GRAB_CSV,
            "skip_duplicates": True,
        },
        headers=admin_headers,
    )
    assert res_preview.status_code == 200
    preview = res_preview.json()
    assert preview["channel"] == "GRAB"
    assert preview["total_rows"] == 3
    assert preview["valid_rows"] == 3
    assert preview["duplicate_rows"] == 0
    assert preview["gross_amount_total"] == 440000.0  # 150k + 200k + 90k
    assert preview["platform_fee_total"] == 88000.0   # 30k + 40k + 18k
    assert preview["net_settlement_total"] == 337000.0 # 110k + 160k + 67k
    assert len(preview["preview_items"]) == 3

    # 2. Execute GrabFood import
    res_exec = client.post(
        "/api/v1/omnichannel/imports/execute",
        json={
            "channel": "GRAB",
            "filename": "grab_report_20261007.csv",
            "raw_content": SAMPLE_GRAB_CSV,
            "skip_duplicates": True,
        },
        headers=admin_headers,
    )
    assert res_exec.status_code == 201
    exec_data = res_exec.json()
    assert exec_data["channel"] == "GRAB"
    assert exec_data["imported_rows"] == 3
    assert exec_data["duplicate_rows"] == 0
    assert exec_data["status"] == "COMPLETED"
    import_id = exec_data["id"]

    # 3. Verify created orders exist and have channel="GRAB"
    res_orders = client.get("/api/v1/orders?source=GRAB", headers=admin_headers)
    assert res_orders.status_code == 200
    grab_orders = res_orders.json()["items"]
    assert len(grab_orders) >= 3
    for o in grab_orders:
        assert o["source"] == "GRAB"
        assert o["status"] == "COMPLETED"
        assert o["payment_status"] == "PAID"

    # 4. Check list imports
    res_list_imports = client.get("/api/v1/omnichannel/imports?channel=GRAB", headers=admin_headers)
    assert res_list_imports.status_code == 200
    imports_list = res_list_imports.json()
    assert len(imports_list) >= 1
    assert any(it["id"] == import_id for it in imports_list)


def test_shopeefood_report_preview_and_execute(client: TestClient, admin_headers: dict):
    # 1. Preview ShopeeFood report
    res_preview = client.post(
        "/api/v1/omnichannel/imports/preview-raw",
        json={
            "channel": "SHOPEEFOOD",
            "filename": "shopeefood_statement.csv",
            "raw_content": SAMPLE_SHOPEE_CSV,
            "skip_duplicates": True,
        },
        headers=admin_headers,
    )
    assert res_preview.status_code == 200
    preview = res_preview.json()
    assert preview["channel"] == "SHOPEEFOOD"
    assert preview["total_rows"] == 2
    assert preview["gross_amount_total"] == 420000.0  # 180k + 240k
    assert preview["platform_fee_total"] == 105000.0  # 45k + 60k
    assert preview["net_settlement_total"] == 295000.0 # 115k + 180k

    # 2. Execute ShopeeFood report
    res_exec = client.post(
        "/api/v1/omnichannel/imports/execute",
        json={
            "channel": "SHOPEEFOOD",
            "filename": "shopeefood_statement.csv",
            "raw_content": SAMPLE_SHOPEE_CSV,
            "skip_duplicates": True,
        },
        headers=admin_headers,
    )
    assert res_exec.status_code == 201
    assert res_exec.json()["imported_rows"] == 2


def test_idempotent_duplicate_prevention(client: TestClient, admin_headers: dict):
    """
    Tải lại cùng một file báo cáo GrabFood:
    Hệ thống phát hiện duplicate 100% và không tạo thêm đơn trùng.
    """
    # Preview lại
    res_preview = client.post(
        "/api/v1/omnichannel/imports/preview-raw",
        json={
            "channel": "GRAB",
            "filename": "grab_dup_test.csv",
            "raw_content": SAMPLE_GRAB_CSV,
            "skip_duplicates": True,
        },
        headers=admin_headers,
    )
    assert res_preview.status_code == 200
    preview = res_preview.json()
    assert preview["duplicate_rows"] == 3
    assert preview["valid_rows"] == 0

    # Execute lại với skip_duplicates=True
    res_exec = client.post(
        "/api/v1/omnichannel/imports/execute",
        json={
            "channel": "GRAB",
            "filename": "grab_dup_test.csv",
            "raw_content": SAMPLE_GRAB_CSV,
            "skip_duplicates": True,
        },
        headers=admin_headers,
    )
    assert res_exec.status_code == 201
    exec_data = res_exec.json()
    assert exec_data["imported_rows"] == 0
    assert exec_data["duplicate_rows"] == 3


def test_settlement_creation_and_reconciliation(client: TestClient, admin_headers: dict):
    """
    Kiểm tra tạo kỳ quyết toán sàn và chạy thuật toán đối soát tự động.
    """
    now = datetime.now(timezone.utc)
    start_date = (now - timedelta(days=2)).isoformat()
    end_date = (now + timedelta(days=2)).isoformat()

    # 1. Tạo kỳ quyết toán cho Grab
    res_create = client.post(
        "/api/v1/omnichannel/settlements",
        json={
            "channel": "GRAB",
            "external_settlement_id": "GRAB-PAYOUT-OCT2026-01",
            "period_start": start_date,
            "period_end": end_date,
            "gross_amount": 440000.0,
            "platform_fee": 88000.0,
            "merchant_discount": 15000.0,
            "other_fee": 0.0,
            "notes": "Quyết toán tuần 1 tháng 10 từ Grab",
        },
        headers=admin_headers,
    )
    assert res_create.status_code == 201
    settlement = res_create.json()
    settlement_id = settlement["id"]
    assert settlement["channel"] == "GRAB"
    assert settlement["status"] == "UNMATCHED"
    assert settlement["net_amount"] == 337000.0

    # 2. Chạy đối soát tự động
    res_rec = client.post(
        f"/api/v1/omnichannel/settlements/{settlement_id}/reconcile",
        headers=admin_headers,
    )
    assert res_rec.status_code == 200
    rec_result = res_rec.json()
    assert rec_result["settlement_id"] == settlement_id
    assert rec_result["matched_orders"] >= 3
    assert rec_result["total_orders_net"] == 337000.0
    assert rec_result["status"] == "MATCHED"
    assert rec_result["discrepancy"] == 0.0


def test_channel_pnl_analytics(client: TestClient, admin_headers: dict):
    """
    Kiểm tra báo cáo phân tích P&L đa kênh (Website vs Grab vs ShopeeFood).
    """
    res = client.get("/api/v1/omnichannel/analytics/channel-pnl", headers=admin_headers)
    assert res.status_code == 200
    pnl = res.json()
    assert "channels" in pnl
    assert "totals" in pnl

    channels = {c["channel"]: c for c in pnl["channels"]}
    assert "GRAB" in channels
    assert "SHOPEEFOOD" in channels

    grab = channels["GRAB"]
    assert grab["order_count"] >= 3
    assert grab["gross_revenue"] >= 440000.0
    assert grab["platform_fees"] >= 88000.0
    assert grab["net_settlement"] >= 337000.0
    assert grab["net_margin_percentage"] > 70.0  # Net margin around 76.6%

    shopee = channels["SHOPEEFOOD"]
    assert shopee["order_count"] >= 2
    assert shopee["gross_revenue"] >= 420000.0
    assert shopee["platform_fees"] >= 105000.0
    assert shopee["net_settlement"] >= 295000.0

    # Totals verification
    totals = pnl["totals"]
    assert totals["gross_revenue"] >= 860000.0
    assert totals["platform_fees"] >= 193000.0


def test_omnichannel_rbac_enforcement(client: TestClient):
    """
    Kiểm tra bảo mật RBAC: Không có token bị chặn 401.
    """
    res = client.get("/api/v1/omnichannel/analytics/channel-pnl")
    assert res.status_code == 401

    res_post = client.post("/api/v1/omnichannel/imports/execute", json={})
    assert res_post.status_code == 401
