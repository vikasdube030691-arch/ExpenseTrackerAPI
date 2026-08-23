"""The critical security property of the entire tool layer: `user_id` is
bound into each tool factory by the caller (ChatService, from the
authenticated request) and must never appear as an argument an LLM's tool
call could set. This test sweeps every tool from every factory and asserts
that structurally, rather than trusting each tool module to get it right on
its own.
"""

from app.tools.analytics_tools import build_analytics_tools
from app.tools.budget_tools import build_budget_tools
from app.tools.expense_tools import build_expense_tools
from app.tools.memory_tools import build_memory_tools
from app.tools.report_tools import build_report_tools

USER_ID = "507f1f77bcf86cd799439011"

ALL_FACTORIES = [
    build_expense_tools,
    build_analytics_tools,
    build_budget_tools,
    build_report_tools,
    build_memory_tools,
]


def test_no_tool_accepts_user_id_as_an_argument(database):
    for factory in ALL_FACTORIES:
        for t in factory(database, USER_ID):
            assert "user_id" not in t.args, f"{t.name} exposes user_id in its args schema"


def test_no_tool_accepts_database_or_internal_args(database):
    for factory in ALL_FACTORIES:
        for t in factory(database, USER_ID):
            for forbidden in ("database", "db", "collection"):
                assert forbidden not in t.args, f"{t.name} exposes '{forbidden}' in its args schema"


async def test_memory_tools_are_isolated_per_user(database):
    user_a_tools = build_memory_tools(database, "507f1f77bcf86cd799439011")
    user_b_tools = build_memory_tools(database, "507f1f77bcf86cd799439099")

    remember_a = next(t for t in user_a_tools if t.name == "remember")
    recall_a = next(t for t in user_a_tools if t.name == "recall_memories")
    recall_b = next(t for t in user_b_tools if t.name == "recall_memories")

    await remember_a.ainvoke({"content": "Prefers budgets in EUR"})

    memories_a = await recall_a.ainvoke({})
    memories_b = await recall_b.ainvoke({})

    assert len(memories_a) == 1
    assert memories_b == []


async def test_expense_tool_add_transaction_validates_transaction_type(database):
    from app.services.account_service import AccountService
    from app.services.category_service import CategoryService
    from app.schemas.account import AccountCreate
    from app.schemas.category import CategoryCreate

    account = await AccountService(database).create_account(
        USER_ID, AccountCreate(name="Checking", account_type="bank", currency="USD", balance=0.0)
    )
    category = await CategoryService(database).create_category(
        USER_ID, CategoryCreate(name="Groceries", type="expense")
    )

    tools = build_expense_tools(database, USER_ID)
    add_transaction = next(t for t in tools if t.name == "add_transaction")

    result = await add_transaction.ainvoke(
        {
            "account_id": account.id,
            "transaction_type": "not-a-real-type",
            "amount": 10.0,
            "currency": "USD",
            "category_id": category.id,
            "transaction_date": "2026-08-01",
        }
    )

    assert "error" in result


async def test_budget_tool_get_budget_usage_reflects_real_spending(database):
    from app.services.account_service import AccountService
    from app.services.budget_service import BudgetService
    from app.services.category_service import CategoryService
    from app.services.transaction_service import TransactionService
    from app.schemas.account import AccountCreate
    from app.schemas.budget import BudgetCreate
    from app.schemas.category import CategoryCreate
    from app.schemas.transaction import TransactionCreate
    from datetime import datetime, timezone

    account = await AccountService(database).create_account(
        USER_ID, AccountCreate(name="Checking", account_type="bank", currency="USD", balance=0.0)
    )
    category = await CategoryService(database).create_category(
        USER_ID, CategoryCreate(name="Groceries", type="expense")
    )
    await BudgetService(database).create_budget(
        USER_ID,
        BudgetCreate(category_id=category.id, amount=200.0, currency="USD", start_date=datetime.now(timezone.utc)),
    )
    await TransactionService(database).create_transaction(
        USER_ID,
        TransactionCreate(
            account_id=account.id,
            transaction_type="expense",
            amount=50.0,
            currency="USD",
            category_id=category.id,
            transaction_date=datetime.now(timezone.utc),
            tags=[],
        ),
    )

    tools = build_budget_tools(database, USER_ID)
    get_budget_usage = next(t for t in tools if t.name == "get_budget_usage")

    usage = await get_budget_usage.ainvoke({})

    assert len(usage) == 1
    assert usage[0]["spent"] == 50.0
    assert usage[0]["remaining"] == 150.0
