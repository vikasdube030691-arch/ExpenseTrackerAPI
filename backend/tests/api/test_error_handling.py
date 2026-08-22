from tests.api.helpers import auth_headers, register_and_login


async def test_not_found_error_uses_the_consistent_envelope(client):
    token = register_and_login(client)

    response = client.get("/api/v1/transactions/507f1f77bcf86cd799439099", headers=auth_headers(token))

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "not_found"
    assert "request_id" in body["error"]


async def test_validation_error_uses_the_consistent_envelope(client):
    token = register_and_login(client)

    response = client.post("/api/v1/accounts/", json={"currency": "US"}, headers=auth_headers(token))

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert isinstance(body["error"]["details"], list)


async def test_response_echoes_a_generated_request_id_header(client):
    response = client.get("/api/v1/accounts/")

    assert "X-Request-ID" in response.headers


async def test_response_echoes_back_a_client_supplied_request_id(client):
    response = client.get("/api/v1/accounts/", headers={"X-Request-ID": "test-request-id-123"})

    assert response.headers["X-Request-ID"] == "test-request-id-123"
