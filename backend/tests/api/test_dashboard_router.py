from datetime import datetime, timezone

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


async def test_summary_reflects_income_and_expense(client):
    token = register_and_login(client)
    account = create_account(client, token)
    expense_category = create_category(client, token, name="Groceries", category_type="expense")
    income_category = create_category(client, token, name="Salary", category_type="income")
    _create_transaction(client, token, account["id"], expense_category["id"], transaction_type="expense", amount=100.0)
    _create_transaction(
        client, token, account["id"], income_category["id"], transaction_type="income", amount=1000.0
    )

    summary = client.get("/api/v1/dashboard/summary", headers=auth_headers(token)).json()

    assert summary["total_income"] == 1000.0
    assert summary["total_expense"] == 100.0
    assert summary["net"] == 900.0
    assert summary["transaction_count"] == 2


async def test_category_analysis_breaks_down_spending(client):
    token = register_and_login(client)
    account = create_account(client, token)
    category = create_category(client, token)
    _create_transaction(client, token, account["id"], category["id"], amount=40.0)

    analysis = client.get("/api/v1/dashboard/category-analysis", headers=auth_headers(token)).json()

    assert len(analysis["breakdown"]) == 1
    assert analysis["breakdown"][0]["category_id"] == category["id"]
    assert analysis["breakdown"][0]["total"] == 40.0


async def test_trends_groups_by_month(client):
    token = register_and_login(client)
    account = create_account(client, token)
    category = create_category(client, token)
    _create_transaction(client, token, account["id"], category["id"], amount=20.0)

    trends = client.get("/api/v1/dashboard/trends?granularity=month", headers=auth_headers(token)).json()

    assert trends["granularity"] == "month"
    assert len(trends["points"]) == 1
    assert trends["points"][0]["expense"] == 20.0


async def test_overview_includes_summary_recent_transactions_and_budget_progress(client):
    token = register_and_login(client)
    account = create_account(client, token)
    category = create_category(client, token)
    _create_transaction(client, token, account["id"], category["id"], amount=50.0)
    # Budget start_date is the beginning of the current month (not "now") so it
    # covers the transaction just created above regardless of creation order.
    start_of_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    client.post(
        "/api/v1/budgets/",
        json={
            "category_id": category["id"],
            "amount": 200.0,
            "currency": "USD",
            "period": "monthly",
            "start_date": start_of_month.isoformat(),
        },
        headers=auth_headers(token),
    )

    overview = client.get("/api/v1/dashboard/", headers=auth_headers(token)).json()

    assert overview["summary"]["total_expense"] == 50.0
    assert len(overview["recent_transactions"]) == 1
    assert len(overview["budget_progress"]) == 1
    assert overview["budget_progress"][0]["spent"] == 50.0
    assert overview["budget_progress"][0]["remaining"] == 150.0


async def test_dashboard_requires_authentication(client):
    response = client.get("/api/v1/dashboard/summary")

    assert response.status_code == 401
