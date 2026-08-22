def register_and_login(client, email: str = "jane@example.com", password: str = "correct-horse-battery") -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Jane Doe"},
    )
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return response.json()["access_token"]


def auth_headers(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}"}


def create_account(client, access_token: str, *, name: str = "Checking", currency: str = "USD") -> dict:
    response = client.post(
        "/api/v1/accounts/",
        json={"name": name, "account_type": "bank", "currency": currency, "balance": 0.0},
        headers=auth_headers(access_token),
    )
    return response.json()


def create_category(client, access_token: str, *, name: str = "Groceries", category_type: str = "expense") -> dict:
    response = client.post(
        "/api/v1/categories/",
        json={"name": name, "type": category_type},
        headers=auth_headers(access_token),
    )
    return response.json()
