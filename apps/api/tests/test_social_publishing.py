import pytest
from datetime import datetime, timezone, timedelta
from fastapi import status


def test_list_and_get_social_connections(client, admin_headers):
    # 1. List connections
    res = client.get("/api/v1/social/connections", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 5

    platforms = {c["platform"] for c in data}
    assert "FACEBOOK" in platforms
    assert "TIKTOK" in platforms
    assert "WEBSITE_BLOG" in platforms

    # 2. Get specific connection
    first_conn = data[0]
    res_get = client.get(f"/api/v1/social/connections/{first_conn['id']}", headers=admin_headers)
    assert res_get.status_code == status.HTTP_200_OK
    assert res_get.json()["id"] == first_conn["id"]
    assert res_get.json()["account_name"] == first_conn["account_name"]


def test_create_and_update_social_connection(client, admin_headers):
    payload = {
        "platform": "FACEBOOK",
        "account_name": "Chi nhánh Mộc Healthy Cầu Giấy",
        "account_id": "fb_page_cau_giay_02",
        "is_mock": True,
        "metadata_json": {"branch": "Cau Giay", "store_code": "CG01"},
    }
    res = client.post("/api/v1/social/connections", json=payload, headers=admin_headers)
    assert res.status_code == status.HTTP_201_CREATED
    created = res.json()
    conn_id = created["id"]
    assert created["account_name"] == "Chi nhánh Mộc Healthy Cầu Giấy"
    assert created["is_connected"] is True
    assert created["status"] == "CONNECTED"

    # Update connection
    update_payload = {"account_name": "Mộc Healthy Cầu Giấy Flagship"}
    res_up = client.put(f"/api/v1/social/connections/{conn_id}", json=update_payload, headers=admin_headers)
    assert res_up.status_code == status.HTTP_200_OK
    assert res_up.json()["account_name"] == "Mộc Healthy Cầu Giấy Flagship"


def test_connection_test_and_refresh_token(client, admin_headers):
    res_list = client.get("/api/v1/social/connections", headers=admin_headers)
    first_conn = res_list.json()[0]
    conn_id = first_conn["id"]

    # 1. Test connection validation
    res_test = client.post(f"/api/v1/social/connections/{conn_id}/test", headers=admin_headers)
    assert res_test.status_code == status.HTTP_200_OK
    test_data = res_test.json()
    assert test_data["is_valid"] is True
    assert test_data["status"] == "CONNECTED"
    assert "account_info" in test_data

    # 2. Refresh token
    res_ref = client.post(f"/api/v1/social/connections/{conn_id}/refresh", headers=admin_headers)
    assert res_ref.status_code == status.HTTP_200_OK
    ref_data = res_ref.json()
    assert ref_data["success"] is True
    assert ref_data["expires_at"] is not None


def test_publish_content_now_full_flow(client, admin_headers):
    # 1. Create a draft content item
    content_payload = {
        "title": "Ra mắt Salad Cầu Vồng Thanh Nhiệt Mùa Hè",
        "content_type": "FACEBOOK_POST",
        "channel": "FACEBOOK",
        "brand_tone": "FRESH_ENERGETIC",
        "hook": "Trời nắng nóng oi bức làm bạn uể oải? ☀️",
        "body": "Đừng lo, Mộc Healthy mang đến siêu phẩm Salad Cầu Vồng với 7 loại rau củ tươi mọng!",
        "cta": "Inbox ngay để nhận ưu đãi mua 1 tặng 1!",
        "hashtags": ["#mochealthy", "#saladcauvong", "#eatclean"],
    }
    res_create = client.post("/api/v1/content", json=content_payload, headers=admin_headers)
    assert res_create.status_code == status.HTTP_201_CREATED
    content_id = res_create.json()["id"]

    # 2. Submit review and approve
    client.post(f"/api/v1/content/{content_id}/submit-review", headers=admin_headers)
    client.post(f"/api/v1/content/{content_id}/approve", headers=admin_headers)

    # 3. Publish now
    res_pub = client.post(f"/api/v1/social/publish-now/{content_id}", json={}, headers=admin_headers)
    assert res_pub.status_code == status.HTTP_200_OK
    pub_data = res_pub.json()
    assert pub_data["success"] is True

    published_post = pub_data["published_post"]
    assert published_post["content_id"] == content_id
    assert published_post["publish_status"] == "PUBLISHED"
    assert published_post["external_post_id"] is not None
    assert "facebook.com" in published_post["external_post_url"]

    # Verify content item status is updated to PUBLISHED
    res_content = client.get(f"/api/v1/content/{content_id}", headers=admin_headers)
    assert res_content.json()["status"] == "PUBLISHED"
    assert res_content.json()["external_post_id"] == published_post["external_post_id"]


def test_idempotency_guard_prevents_duplicate_publishing(client, admin_headers):
    # Retrieve an already published post
    res_posts = client.get("/api/v1/social/published-posts?status=PUBLISHED", headers=admin_headers)
    assert res_posts.status_code == status.HTTP_200_OK
    items = res_posts.json()["items"]
    assert len(items) > 0

    target_post = items[0]
    content_id = target_post["content_id"]

    # Attempt to publish the same content item again
    res_repub = client.post(f"/api/v1/social/publish-now/{content_id}", json={}, headers=admin_headers)
    assert res_repub.status_code == status.HTTP_200_OK
    repub_data = res_repub.json()
    assert repub_data["success"] is True
    # The external post ID should match the existing one (no second post created)
    assert repub_data["published_post"]["id"] == target_post["id"]
    assert repub_data["published_post"]["external_post_id"] == target_post["external_post_id"]


def test_worker_pickup_due_scheduled_batch(client, admin_headers):
    # 1. Create a content item, approve, and schedule it in the past (due for publish)
    past_schedule = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    content_payload = {
        "title": "Bí quyết chọn bơ sáp Đắk Lắk béo ngậy không đắng",
        "content_type": "WEBSITE_BANNER_COPY",
        "channel": "WEBSITE_BANNER",
        "body": "Bơ sáp loại 1 vỏ mỏng cơm dày giàu chất béo tốt Omega-3...",
        "scheduled_at": past_schedule,
    }
    res_create = client.post("/api/v1/content", json=content_payload, headers=admin_headers)
    content_id = res_create.json()["id"]

    client.post(f"/api/v1/content/{content_id}/submit-review", headers=admin_headers)
    client.post(f"/api/v1/content/{content_id}/approve", headers=admin_headers)
    client.post(f"/api/v1/content/{content_id}/schedule", json={"scheduled_at": past_schedule}, headers=admin_headers)

    # 2. Trigger worker run due batch
    res_worker = client.post("/api/v1/social/worker/run-due-batch?limit=10", headers=admin_headers)
    assert res_worker.status_code == status.HTTP_200_OK
    worker_data = res_worker.json()
    assert worker_data["processed"] >= 1
    assert worker_data["published"] >= 1

    # Verify content item was picked up and transitioned to PUBLISHED
    res_check = client.get(f"/api/v1/content/{content_id}", headers=admin_headers)
    assert res_check.json()["status"] == "PUBLISHED"


def test_sync_post_metrics(client, admin_headers):
    res_posts = client.get("/api/v1/social/published-posts?status=PUBLISHED", headers=admin_headers)
    first_post = res_posts.json()["items"][0]
    post_id = first_post["id"]

    # Sync fresh metrics
    res_sync = client.post(f"/api/v1/social/published-posts/{post_id}/sync-metrics", headers=admin_headers)
    assert res_sync.status_code == status.HTTP_200_OK
    metric = res_sync.json()
    assert metric["published_post_id"] == post_id
    assert metric["impressions"] > 0
    assert metric["reach"] > 0
    assert metric["likes"] >= 0


def test_social_publishing_rbac_protection(client):
    # 1. Unauthenticated request should be rejected
    res_unauth = client.get("/api/v1/social/connections")
    assert res_unauth.status_code == status.HTTP_401_UNAUTHORIZED

    # 2. Publish now unauthenticated should be rejected
    res_pub_unauth = client.post("/api/v1/social/publish-now/fake-id")
    assert res_pub_unauth.status_code == status.HTTP_401_UNAUTHORIZED
