from datetime import datetime, timezone

from tests.api.helpers import auth_headers, create_category, register_and_login


def _create_budget(client, token, category_id=None, **overrides):
    payload = {
        "category_id": category_id,
        "amount": 500.0,
        "currency": "USD",
        "period": "monthly",
        "start_date": datetime.now(timezone.utc).isoformat(),
    }
    payload.update(overrides)
    return client.post("/api/v1/budgets/", json=payload, headers=auth_headers(token))


async def test_create_and_list_budgets(client):
    token = register_and_login(client)
    category = create_category(client, token)

    created = _create_budget(client, token, category["id"]).json()
    budgets = client.get("/api/v1/budgets/", headers=auth_headers(token)).json()

    assert created["amount"] == 500.0
    assert len(budgets) == 1


async def test_create_budget_rejects_unowned_category(client):
    token = register_and_login(client)

    response = _create_budget(client, token, "507f1f77bcf86cd799439099")

    assert response.status_code == 404


async def test_update_and_delete_budget(client):
    token = register_and_login(client)
    category = create_category(client, token)
    budget = _create_budget(client, token, category["id"]).json()

    updated = client.put(
        f"/api/v1/budgets/{budget['id']}", json={"amount": 750.0}, headers=auth_headers(token)
    )
    assert updated.json()["amount"] == 750.0

    deleted = client.delete(f"/api/v1/budgets/{budget['id']}", headers=auth_headers(token))
    assert deleted.status_code == 204

    budgets = client.get("/api/v1/budgets/", headers=auth_headers(token)).json()
    assert budgets == []
