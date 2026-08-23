"""Tools for the Expense Agent: search, add, update, delete, and categorize
transactions, plus the account/category lookups it needs to resolve names the
user mentions in natural language into the ids these operations require. See
`app/tools/_helpers.py` for the user-scoping contract every tool here follows.
"""

from typing import Annotated, Any

from langchain_core.tools import BaseTool, tool
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.enums import TransactionType
from app.schemas.transaction import TransactionCreate, TransactionFilter, TransactionUpdate
from app.services.account_service import AccountService
from app.services.category_service import CategoryService
from app.services.transaction_service import TransactionService
from app.tools._helpers import as_tool_error, parse_date, to_json


def build_expense_tools(database: AsyncIOMotorDatabase, user_id: str) -> list[BaseTool]:
    transactions = TransactionService(database)
    categories = CategoryService(database)
    accounts = AccountService(database)

    @tool
    async def list_accounts() -> Any:
        """Lists the user's accounts (id, name, type, currency, balance).
        Call this before add_transaction if you don't already know which
        account_id to use."""
        return to_json(await accounts.list_accounts(user_id))

    @tool
    async def list_categories(transaction_type: Annotated[str | None, "'income', 'expense', or omit for both"] = None) -> Any:
        """Lists the user's categories (id, name, type). Call this before
        add_transaction or categorize_transaction to resolve a category name
        the user mentioned (e.g. "groceries") to its category_id."""
        return to_json(await categories.list_categories(user_id, category_type=transaction_type))

    @tool
    async def search_transactions(
        search: Annotated[str | None, "free-text match against merchant or description"] = None,
        transaction_type: Annotated[str | None, "'income' or 'expense'"] = None,
        category_id: str | None = None,
        account_id: str | None = None,
        start_date: Annotated[str | None, "ISO date, e.g. '2026-08-01'"] = None,
        end_date: Annotated[str | None, "ISO date, e.g. '2026-08-31'"] = None,
        min_amount: float | None = None,
        max_amount: float | None = None,
        page: int = 1,
        page_size: Annotated[int, "max 50"] = 20,
    ) -> Any:
        """Searches the user's transactions with optional filters. Use this
        to answer "what did I spend on X", "show my transactions in Y", etc."""
        try:
            filters = TransactionFilter(
                transaction_type=TransactionType(transaction_type) if transaction_type else None,
                category_id=category_id,
                account_id=account_id,
                start_date=parse_date(start_date),
                end_date=parse_date(end_date),
                min_amount=min_amount,
                max_amount=max_amount,
                search=search,
            )
            items, total = await transactions.list_transactions(
                user_id, filters, page=page, page_size=min(page_size, 50)
            )
            return {"items": to_json(items), "total": total, "page": page}
        except Exception as exc:  # noqa: BLE001 - converted to a tool-visible error, not a crash
            return as_tool_error(exc)

    @tool
    async def add_transaction(
        account_id: str,
        transaction_type: Annotated[str, "'income' or 'expense'"],
        amount: Annotated[float, "must be greater than 0"],
        currency: Annotated[str, "3-letter ISO currency code, e.g. 'USD'"],
        category_id: str,
        transaction_date: Annotated[str, "ISO date, e.g. '2026-08-15'"],
        merchant: str | None = None,
        description: str | None = None,
    ) -> Any:
        """Adds a new transaction. Look up account_id and category_id first
        with list_accounts/list_categories if you don't already have them."""
        try:
            parsed_date = parse_date(transaction_date)
            if parsed_date is None:
                return {"error": "transaction_date is required"}
            payload = TransactionCreate(
                account_id=account_id,
                transaction_type=TransactionType(transaction_type),
                amount=amount,
                currency=currency,
                category_id=category_id,
                merchant=merchant,
                description=description,
                transaction_date=parsed_date,
                tags=[],
            )
            created = await transactions.create_transaction(user_id, payload)
            return to_json(created)
        except Exception as exc:  # noqa: BLE001
            return as_tool_error(exc)

    @tool
    async def update_transaction(
        transaction_id: str,
        amount: float | None = None,
        category_id: str | None = None,
        merchant: str | None = None,
        description: str | None = None,
    ) -> Any:
        """Updates fields on an existing transaction. Only pass the fields
        that should change."""
        try:
            payload = TransactionUpdate(amount=amount, category_id=category_id, merchant=merchant, description=description)
            updated = await transactions.update_transaction(user_id, transaction_id, payload)
            return to_json(updated)
        except Exception as exc:  # noqa: BLE001
            return as_tool_error(exc)

    @tool
    async def categorize_transaction(transaction_id: str, category_id: str) -> Any:
        """Changes which category a transaction is assigned to."""
        try:
            updated = await transactions.update_transaction(user_id, transaction_id, TransactionUpdate(category_id=category_id))
            return to_json(updated)
        except Exception as exc:  # noqa: BLE001
            return as_tool_error(exc)

    @tool
    async def delete_transaction(transaction_id: str) -> Any:
        """Permanently deletes a transaction. Confirm with the user before
        calling this — it cannot be undone from the chat."""
        try:
            await transactions.delete_transaction(user_id, transaction_id)
            return {"deleted": True, "transaction_id": transaction_id}
        except Exception as exc:  # noqa: BLE001
            return as_tool_error(exc)

    return [
        list_accounts,
        list_categories,
        search_transactions,
        add_transaction,
        update_transaction,
        categorize_transaction,
        delete_transaction,
    ]
