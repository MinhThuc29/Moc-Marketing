import io
import pytest
from PIL import Image


def create_test_image(format="PNG", size=(200, 200), color=(34, 139, 34)):
    """Creates an in-memory image for upload testing"""
    file_obj = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(file_obj, format=format)
    file_obj.seek(0)
    return file_obj.getvalue()


def test_upload_single_image_success(client, admin_headers):
    image_bytes = create_test_image(format="JPEG", size=(400, 300))
    files = [
        ("files", ("test_fresh_apple.jpg", image_bytes, "image/jpeg"))
    ]
    data = {
        "folder": "products",
        "tags": "fresh, apple, organic",
    }

    res = client.post(
        "/api/v1/media/upload",
        files=files,
        data=data,
        headers=admin_headers,
    )

    assert res.status_code == 201
    assets = res.json()
    assert len(assets) == 1

    asset = assets[0]
    assert asset["original_name"] == "test_fresh_apple.jpg"
    assert asset["mime_type"] == "image/jpeg"
    assert asset["folder"] == "products"
    assert asset["width"] == 400
    assert asset["height"] == 300
    assert asset["file_size"] > 0
    assert asset["url"].startswith("/uploads/products/")
    assert asset["thumbnail_url"].endswith(".webp")
    assert "fresh" in asset["tags"]


def test_upload_invalid_mime_type_rejected(client, admin_headers):
    fake_executable = b"MZ\x90\x00\x03\x00\x00\x00"
    files = [
        ("files", ("malware.exe", fake_executable, "application/x-msdownload"))
    ]

    res = client.post(
        "/api/v1/media/upload",
        files=files,
        headers=admin_headers,
    )
    assert res.status_code == 400
    assert "không được hỗ trợ" in res.json()["detail"]


def test_upload_unauthenticated_rejected(client):
    image_bytes = create_test_image()
    files = [
        ("files", ("test.png", image_bytes, "image/png"))
    ]
    res = client.post("/api/v1/media/upload", files=files)
    assert res.status_code == 401


def test_upload_insufficient_permission_rejected(client, marketing_headers):
    image_bytes = create_test_image()
    files = [
        ("files", ("test.png", image_bytes, "image/png"))
    ]
    res = client.post("/api/v1/media/upload", files=files, headers=marketing_headers)
    assert res.status_code == 403
    assert "product.write" in res.json()["detail"]


def test_list_media_assets(client, admin_headers):
    # Ensure at least 1 image uploaded
    image_bytes = create_test_image(size=(100, 100))
    client.post(
        "/api/v1/media/upload",
        files=[("files", ("banana.png", image_bytes, "image/png"))],
        headers=admin_headers,
    )

    res = client.get("/api/v1/media", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


def test_get_media_asset_detail(client, admin_headers):
    image_bytes = create_test_image(size=(150, 150))
    upload_res = client.post(
        "/api/v1/media/upload",
        files=[("files", ("orange_juice.png", image_bytes, "image/png"))],
        headers=admin_headers,
    )
    asset_id = upload_res.json()[0]["id"]

    res = client.get(f"/api/v1/media/{asset_id}", headers=admin_headers)
    assert res.status_code == 200
    detail = res.json()
    assert detail["id"] == asset_id
    assert detail["original_name"] == "orange_juice.png"


def test_update_media_asset(client, admin_headers):
    image_bytes = create_test_image()
    upload_res = client.post(
        "/api/v1/media/upload",
        files=[("files", ("item_to_rename.png", image_bytes, "image/png"))],
        headers=admin_headers,
    )
    asset_id = upload_res.json()[0]["id"]

    update_res = client.put(
        f"/api/v1/media/{asset_id}",
        json={
            "original_name": "renamed_item.png",
            "tags": ["updated", "renamed"],
        },
        headers=admin_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["original_name"] == "renamed_item.png"
    assert "updated" in update_res.json()["tags"]


def test_delete_media_asset(client, admin_headers):
    image_bytes = create_test_image()
    upload_res = client.post(
        "/api/v1/media/upload",
        files=[("files", ("to_delete.png", image_bytes, "image/png"))],
        headers=admin_headers,
    )
    asset_id = upload_res.json()[0]["id"]

    del_res = client.delete(f"/api/v1/media/{asset_id}", headers=admin_headers)
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Ensure 404 after deletion
    get_res = client.get(f"/api/v1/media/{asset_id}", headers=admin_headers)
    assert get_res.status_code == 404
