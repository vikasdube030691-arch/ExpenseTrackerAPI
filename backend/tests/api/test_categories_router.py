from tests.api.helpers import auth_headers, create_category, register_and_login


async def test_create_and_list_categories(client):
    token = register_and_login(client)

    created = create_category(client, token, name="Groceries", category_type="expense")
    response = client.get("/api/v1/categories/", headers=auth_headers(token))

    assert created["name"] == "Groceries"
    categories = response.json()
    assert len(categories) == 1
    assert categories[0]["id"] == created["id"]


async def test_list_categories_filters_by_type(client):
    token = register_and_login(client)
    create_category(client, token, name="Groceries", category_type="expense")
    create_category(client, token, name="Salary", category_type="income")

    expense_only = client.get("/api/v1/categories/?type=expense", headers=auth_headers(token)).json()

    assert len(expense_only) == 1
    assert expense_only[0]["name"] == "Groceries"


async def test_duplicate_category_name_and_type_returns_409(client):
    token = register_and_login(client)
    create_category(client, token, name="Groceries", category_type="expense")

    response = client.post(
        "/api/v1/categories/", json={"name": "Groceries", "type": "expense"}, headers=auth_headers(token)
    )

    assert response.status_code == 409


async def test_update_and_delete_category(client):
    token = register_and_login(client)
    category = create_category(client, token)

    updated = client.put(
        f"/api/v1/categories/{category['id']}", json={"name": "Food"}, headers=auth_headers(token)
    )
    assert updated.json()["name"] == "Food"

    deleted = client.delete(f"/api/v1/categories/{category['id']}", headers=auth_headers(token))
    assert deleted.status_code == 204
