REGISTER_PAYLOAD = {
    "email": "jane@example.com",
    "password": "correct-horse-battery",
    "full_name": "Jane Doe",
}


def _register(client):
    return client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)


def _login(client, password="correct-horse-battery"):
    return client.post(
        "/api/v1/auth/login", json={"email": REGISTER_PAYLOAD["email"], "password": password}
    )


async def test_register_returns_user_without_password(client):
    response = _register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "jane@example.com"
    assert "password" not in body
    assert "hashed_password" not in body


async def test_register_duplicate_email_returns_409(client):
    _register(client)

    response = _register(client)

    assert response.status_code == 409


async def test_login_sets_httponly_refresh_cookie_and_returns_access_token(client):
    _register(client)

    response = _login(client)

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert "refresh_token" not in body  # never in the JSON body
    assert "refresh_token" in response.cookies


async def test_login_with_wrong_password_returns_generic_401(client):
    _register(client)

    response = _login(client, password="wrong-password")

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid email or password"


async def test_login_with_unknown_email_returns_the_same_generic_401(client):
    response = client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": "whatever123"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid email or password"


async def test_me_requires_bearer_token(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


async def test_me_returns_current_user_with_valid_token(client):
    _register(client)
    access_token = _login(client).json()["access_token"]

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "jane@example.com"


async def test_refresh_rotates_cookie_and_issues_new_access_token(client):
    _register(client)
    login_response = _login(client)
    old_access_token = login_response.json()["access_token"]
    old_refresh_cookie = login_response.cookies["refresh_token"]

    refresh_response = client.post("/api/v1/auth/refresh")

    assert refresh_response.status_code == 200
    new_access_token = refresh_response.json()["access_token"]
    assert new_access_token != old_access_token
    assert refresh_response.cookies["refresh_token"] != old_refresh_cookie


async def test_refresh_without_cookie_returns_401(client):
    response = client.post("/api/v1/auth/refresh")

    assert response.status_code == 401


async def test_logout_clears_cookie_and_invalidates_session(client):
    _register(client)
    _login(client)

    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 204

    refresh_response = client.post("/api/v1/auth/refresh")
    assert refresh_response.status_code == 401


async def test_logout_all_revokes_every_session(client):
    _register(client)
    first_login = _login(client)
    access_token = first_login.json()["access_token"]

    response = client.post(
        "/api/v1/auth/logout-all", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 204

    refresh_response = client.post("/api/v1/auth/refresh")
    assert refresh_response.status_code == 401


async def test_login_is_rate_limited_after_repeated_attempts(client):
    _register(client)

    responses = [_login(client, password="wrong-password") for _ in range(6)]

    assert responses[-1].status_code == 429
    assert any(r.status_code == 401 for r in responses[:5])
