from app.models.category import CategoryModel
from app.repositories.category_repository import CategoryRepository

USER_ID = "507f1f77bcf86cd799439011"


async def test_name_exists_for_user_is_scoped_by_type(database):
    repo = CategoryRepository(database)
    await repo.create(CategoryModel(user_id=USER_ID, name="Groceries", type="expense"))

    assert await repo.name_exists_for_user(USER_ID, "Groceries", "expense") is True
    assert await repo.name_exists_for_user(USER_ID, "Groceries", "income") is False


async def test_list_for_user_includes_system_categories(database):
    repo = CategoryRepository(database)
    await repo.create(CategoryModel(user_id=None, name="Salary", type="income", is_system=True))
    await repo.create(CategoryModel(user_id=USER_ID, name="Gifts", type="income"))

    categories = await repo.list_for_user(USER_ID, category_type="income")

    assert {c.name for c in categories} == {"Salary", "Gifts"}


async def test_get_by_id_for_user_allows_system_category_access(database):
    repo = CategoryRepository(database)
    system_category = await repo.create(CategoryModel(user_id=None, name="Salary", type="income", is_system=True))

    assert await repo.get_by_id_for_user(system_category.id, USER_ID) is not None
