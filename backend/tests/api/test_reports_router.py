from datetime import datetime, timedelta, timezone

from tests.api.helpers import auth_headers, create_account, create_category, register_and_login


async def test_generate_monthly_summary_report(client):
    token = register_and_login(client)
    account = create_account(client, token)
    category = create_category(client, token)
    now = datetime.now(timezone.utc)
    client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account["id"],
            "transaction_type": "expense",
            "amount": 75.0,
            "currency": "USD",
            "category_id": category["id"],
            "transaction_date": now.isoformat(),
            "tags": [],
        },
        headers=auth_headers(token),
    )

    response = client.post(
        "/api/v1/reports/generate",
        json={
            "report_type": "monthly_summary",
            "format": "json",
            "period_start": (now - timedelta(days=1)).isoformat(),
            "period_end": (now + timedelta(days=1)).isoformat(),
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert body["data"]["total_expense"] == 75.0


async def test_generate_report_rejects_invalid_period(client):
    token = register_and_login(client)
    now = datetime.now(timezone.utc)

    response = client.post(
        "/api/v1/reports/generate",
        json={
            "report_type": "monthly_summary",
            "period_start": now.isoformat(),
            "period_end": (now - timedelta(days=1)).isoformat(),
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 422


async def test_list_and_get_report(client):
    token = register_and_login(client)
    now = datetime.now(timezone.utc)
    generated = client.post(
        "/api/v1/reports/generate",
        json={
            "report_type": "category_breakdown",
            "period_start": (now - timedelta(days=1)).isoformat(),
            "period_end": (now + timedelta(days=1)).isoformat(),
        },
        headers=auth_headers(token),
    ).json()

    listing = client.get("/api/v1/reports/", headers=auth_headers(token)).json()
    fetched = client.get(f"/api/v1/reports/{generated['id']}", headers=auth_headers(token))

    assert listing["total"] == 1
    assert fetched.status_code == 200
    assert fetched.json()["report_type"] == "category_breakdown"


async def test_reports_are_isolated_between_users(client):
    token_a = register_and_login(client, email="alice@example.com")
    now = datetime.now(timezone.utc)
    client.post(
        "/api/v1/reports/generate",
        json={
            "report_type": "monthly_summary",
            "period_start": (now - timedelta(days=1)).isoformat(),
            "period_end": now.isoformat(),
        },
        headers=auth_headers(token_a),
    )
    token_b = register_and_login(client, email="bob@example.com")

    listing = client.get("/api/v1/reports/", headers=auth_headers(token_b)).json()

    assert listing["total"] == 0
