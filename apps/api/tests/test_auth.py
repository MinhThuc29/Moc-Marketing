def test_login_success(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@mochhealthy.vn", "password": "Password@123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


def test_login_wrong_password(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@mochhealthy.vn", "password": "WrongPassword123"},
    )
    assert response.status_code == 401
    assert "Email hoặc mật khẩu không chính xác" in response.json()["detail"]


def test_login_nonexistent_email(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@mochhealthy.vn", "password": "Password@123"},
    )
    assert response.status_code == 401


def test_login_inactive_user(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@mochhealthy.vn", "password": "Password@123"},
    )
    assert response.status_code == 403
    assert "vô hiệu hóa" in response.json()["detail"]


def test_refresh_token_rotation(client):
    # 1. Login to get initial pair
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@mochhealthy.vn", "password": "Password@123"},
    )
    assert login_res.status_code == 200
    initial_tokens = login_res.json()
    first_refresh = initial_tokens["refresh_token"]

    # 2. Refresh with first token
    refresh_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": first_refresh},
    )
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()
    second_refresh = new_tokens["refresh_token"]
    assert new_tokens["access_token"] != initial_tokens["access_token"]
    assert second_refresh != first_refresh

    # 3. Try to reuse the first (already rotated/revoked) refresh token -> must fail with 401!
    reuse_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": first_refresh},
    )
    assert reuse_res.status_code == 401


def test_refresh_invalid_token(client):
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid.jwt.token"},
    )
    assert response.status_code == 401


def test_get_me_profile(client):
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "marketing@mochhealthy.vn", "password": "Password@123"},
    )
    token = login_res.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "marketing@mochhealthy.vn"
    assert "MARKETING" in data["roles"]
    assert "campaign.create" in data["permissions"]
    assert "product.write" not in data["permissions"]


def test_get_me_unauthorized(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_permission_enforcement_allowed_for_admin(client):
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@mochhealthy.vn", "password": "Password@123"},
    )
    token = login_res.json()["access_token"]

    # Admin has all permissions -> access granted
    res = client.get(
        "/api/v1/auth/protected-action",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["success"] is True


def test_permission_enforcement_denied_for_insufficient_permission(client):
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "marketing@mochhealthy.vn", "password": "Password@123"},
    )
    token = login_res.json()["access_token"]

    # Marketing role does NOT have 'product.write' -> 403 Forbidden!
    res = client.get(
        "/api/v1/auth/protected-action",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    assert "Thiếu quyền hạn 'product.write'" in res.json()["detail"]


def test_logout_revokes_refresh_tokens(client):
    # 1. Login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "inventory@mochhealthy.vn", "password": "Password@123"},
    )
    tokens = login_res.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # 2. Logout
    logout_res = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_res.status_code == 200
    assert logout_res.json()["success"] is True

    # 3. Refresh with the previous refresh token should now fail with 401
    refresh_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 401
