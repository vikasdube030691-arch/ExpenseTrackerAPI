from tests.api.helpers import auth_headers, register_and_login


async def test_send_message_creates_a_new_session_when_none_given(client):
    token = register_and_login(client)

    response = client.post("/api/v1/chat/", json={"message": "How much did I spend?"}, headers=auth_headers(token))

    assert response.status_code == 200
    body = response.json()
    assert body["user_message"]["content"] == "How much did I spend?"
    assert body["assistant_message"]["role"] == "assistant"
    assert body["session_id"]


async def test_send_message_reuses_an_existing_session(client):
    token = register_and_login(client)
    first = client.post("/api/v1/chat/", json={"message": "Hi"}, headers=auth_headers(token)).json()

    second = client.post(
        "/api/v1/chat/",
        json={"session_id": first["session_id"], "message": "Follow-up"},
        headers=auth_headers(token),
    ).json()

    assert second["session_id"] == first["session_id"]


async def test_list_sessions_and_get_session_detail(client):
    token = register_and_login(client)
    sent = client.post("/api/v1/chat/", json={"message": "Hi there"}, headers=auth_headers(token)).json()

    sessions = client.get("/api/v1/chat/sessions", headers=auth_headers(token)).json()
    detail = client.get(f"/api/v1/chat/sessions/{sent['session_id']}", headers=auth_headers(token))

    assert sessions["total"] == 1
    assert detail.status_code == 200
    body = detail.json()
    assert len(body["messages"]) == 2
    assert body["messages"][0]["role"] == "user"
    assert body["messages"][1]["role"] == "assistant"


async def test_stream_message_emits_sse_events(client):
    token = register_and_login(client)

    with client.stream(
        "POST", "/api/v1/chat/stream", json={"message": "Stream this"}, headers=auth_headers(token)
    ) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())

    assert "event: session" in body
    assert "event: delta" in body
    assert "event: done" in body


async def test_chat_requires_authentication(client):
    response = client.post("/api/v1/chat/", json={"message": "Hi"})

    assert response.status_code == 401


async def test_chat_sessions_are_isolated_between_users(client):
    token_a = register_and_login(client, email="alice@example.com")
    client.post("/api/v1/chat/", json={"message": "Hi"}, headers=auth_headers(token_a))
    token_b = register_and_login(client, email="bob@example.com")

    sessions = client.get("/api/v1/chat/sessions", headers=auth_headers(token_b)).json()

    assert sessions["total"] == 0
