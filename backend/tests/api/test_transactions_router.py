from datetime import datetime, timedelta, timezone

from tests.api.helpers import auth_headers, create_account, create_category, register_and_login


def _create_transaction(client, token, account_id, category_id, **overrides):
    payload = {
        "account_id": account_id,
        "transaction_type": "expense",
        "amount": 25.0,
        "currency": "USD",
        "category_id": category_id,
        "transaction_date": datetime.now(timezone.utc).isoformat(),
        "tags": [],
    }
    payload.update(overrides)
    return client.post("/api/v1/transactions/", json=payload, headers=auth_headers(token))


async def _setup(client):
    token = register_and_login(client)
    account = create_account(client, token)
    category = create_category(client, token)
    return token, account, category


async def test_create_get_update_delete_transaction(client):
    token, account, category = await _setup(client)

    created = _create_transaction(client, token, account["id"], category["id"], amount=42.5).json()
    assert created["amount"] == 42.5

    fetched = client.get(f"/api/v1/transactions/{created['id']}", headers=auth_headers(token))
    assert fetched.status_code == 200
    assert fetched.json()["id"] == created["id"]

    updated = client.put(
        f"/api/v1/transactions/{created['id']}", json={"amount": 99.0}, headers=auth_headers(token)
    )
    assert updated.json()["amount"] == 99.0

    deleted = client.delete(f"/api/v1/transactions/{created['id']}", headers=auth_headers(token))
    assert deleted.status_code == 204

    missing = client.get(f"/api/v1/transactions/{created['id']}", headers=auth_headers(token))
    assert missing.status_code == 404


async def test_create_transaction_rejects_unowned_account(client):
    token = register_and_login(client)
    category = create_category(client, token)

    response = _create_transaction(client, token, "507f1f77bcf86cd799439099", category["id"])

    assert response.status_code == 404


async def test_transaction_updates_account_balance(client):
    token, account, category = await _setup(client)
    _create_transaction(client, token, account["id"], category["id"], transaction_type="expense", amount=30.0)

    accounts = client.get("/api/v1/accounts/", headers=auth_headers(token)).json()

    assert accounts[0]["balance"] == -30.0


async def test_list_transactions_paginates(client):
    token, account, category = await _setup(client)
    for i in range(3):
        _create_transaction(client, token, account["id"], category["id"], amount=10.0 + i)

    page1 = client.get(
        "/api/v1/transactions/?page=1&page_size=2", headers=auth_headers(token)
    ).json()
    page2 = client.get(
        "/api/v1/transactions/?page=2&page_size=2", headers=auth_headers(token)
    ).json()

    assert page1["total"] == 3
    assert len(page1["items"]) == 2
    assert len(page2["items"]) == 1


async def test_list_transactions_filters_by_type_and_amount(client):
    token, account, category = await _setup(client)
    income_category = create_category(client, token, name="Salary", category_type="income")
    _create_transaction(client, token, account["id"], category["id"], transaction_type="expense", amount=15.0)
    _create_transaction(
        client, token, account["id"], income_category["id"], transaction_type="income", amount=2000.0
    )

    expenses = client.get(
        "/api/v1/transactions/?transaction_type=expense", headers=auth_headers(token)
    ).json()

    assert expenses["total"] == 1
    assert expenses["items"][0]["transaction_type"] == "expense"


async def test_list_transactions_date_range_filter(client):
    token, account, category = await _setup(client)
    now = datetime.now(timezone.utc)
    _create_transaction(
        client, token, account["id"], category["id"], transaction_date=(now - timedelta(days=10)).isoformat()
    )
    _create_transaction(client, token, account["id"], category["id"], transaction_date=now.isoformat())

    start_date = (now - timedelta(days=1)).isoformat()
    recent = client.get(
        "/api/v1/transactions/", params={"start_date": start_date}, headers=auth_headers(token)
    ).json()

    assert recent["total"] == 1


async def test_list_transactions_search(client):
    token, account, category = await _setup(client)
    _create_transaction(client, token, account["id"], category["id"], merchant="Whole Foods Market")
    _create_transaction(client, token, account["id"], category["id"], merchant="Gas Station")

    results = client.get("/api/v1/transactions/?search=whole", headers=auth_headers(token)).json()

    assert results["total"] == 1
    assert results["items"][0]["merchant"] == "Whole Foods Market"


async def test_list_transactions_sorting(client):
    token, account, category = await _setup(client)
    _create_transaction(client, token, account["id"], category["id"], amount=5.0)
    _create_transaction(client, token, account["id"], category["id"], amount=50.0)

    ascending = client.get("/api/v1/transactions/?sort=amount", headers=auth_headers(token)).json()

    assert [item["amount"] for item in ascending["items"]] == [5.0, 50.0]


async def test_sorting_rejects_unknown_field(client):
    token, account, category = await _setup(client)

    response = client.get("/api/v1/transactions/?sort=hacked_field", headers=auth_headers(token))

    assert response.status_code == 422


async def test_transactions_are_isolated_between_users(client):
    token_a, account_a, category_a = await _setup(client)
    _create_transaction(client, token_a, account_a["id"], category_a["id"])
    token_b = register_and_login(client, email="bob@example.com")

    results = client.get("/api/v1/transactions/", headers=auth_headers(token_b)).json()

    assert results["total"] == 0
