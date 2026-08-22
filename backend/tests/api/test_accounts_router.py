from tests.api.helpers import auth_headers, create_account, register_and_login


async def test_create_and_list_accounts(client):
    token = register_and_login(client)

    created = create_account(client, token, name="Checking")
    list_response = client.get("/api/v1/accounts/", headers=auth_headers(token))

    assert created["name"] == "Checking"
    assert created["currency"] == "USD"
    accounts = list_response.json()
    assert len(accounts) == 1
    assert accounts[0]["id"] == created["id"]


async def test_accounts_require_authentication(client):
    response = client.get("/api/v1/accounts/")

    assert response.status_code == 401


async def test_update_and_delete_account(client):
    token = register_and_login(client)
    account = create_account(client, token)

    updated = client.put(
        f"/api/v1/accounts/{account['id']}", json={"name": "Renamed"}, headers=auth_headers(token)
    )
    assert updated.json()["name"] == "Renamed"

    deleted = client.delete(f"/api/v1/accounts/{account['id']}", headers=auth_headers(token))
    assert deleted.status_code == 204

    accounts = client.get("/api/v1/accounts/", headers=auth_headers(token)).json()
    assert accounts == []


async def test_accounts_are_isolated_between_users(client):
    token_a = register_and_login(client, email="alice@example.com")
    token_b = register_and_login(client, email="bob@example.com")
    create_account(client, token_a)

    accounts_for_b = client.get("/api/v1/accounts/", headers=auth_headers(token_b)).json()

    assert accounts_for_b == []
