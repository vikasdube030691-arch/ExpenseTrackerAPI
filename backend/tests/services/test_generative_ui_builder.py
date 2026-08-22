from datetime import datetime, timezone

from app.schemas.account import AccountCreate
from app.schemas.category import CategoryCreate
from app.schemas.generative_ui import validate_ui_blocks
from app.schemas.transaction import TransactionCreate
from app.services.account_service import AccountService
from app.services.ai.generative_ui_builder import build_ui_blocks
from app.services.category_service import CategoryService
from app.services.transaction_service import TransactionService

USER_ID = "507f1f77bcf86cd799439011"


async def test_returns_no_blocks_for_a_non_financial_message(database):
    blocks = await build_ui_blocks(database, USER_ID, "hello there")

    assert blocks == []


async def test_returns_no_blocks_when_user_has_no_transactions(database):
    blocks = await build_ui_blocks(database, USER_ID, "how much did I spend this month?")

    assert blocks == []


async def test_returns_real_data_driven_blocks_that_pass_validation(database):
    account = await AccountService(database).create_account(
        USER_ID, AccountCreate(name="Checking", account_type="bank", currency="USD", balance=0.0)
    )
    category = await CategoryService(database).create_category(
        USER_ID, CategoryCreate(name="Groceries", type="expense")
    )
    await TransactionService(database).create_transaction(
        USER_ID,
        TransactionCreate(
            account_id=account.id,
            transaction_type="expense",
            amount=42.5,
            currency="USD",
            category_id=category.id,
            transaction_date=datetime.now(timezone.utc),
            tags=[],
        ),
    )

    raw_blocks = await build_ui_blocks(database, USER_ID, "how much did I spend on groceries this month?")

    assert raw_blocks
    result = validate_ui_blocks(raw_blocks)
    assert result.rejected == []
    assert any(block.component == "metric_card" for block in result.blocks)
    assert any(block.component == "bar_chart" for block in result.blocks)
