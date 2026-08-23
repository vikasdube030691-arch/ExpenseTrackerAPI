"""Tools for the Budget Agent: list/create/update/delete budgets, and surface
usage/overspending using the same spent-vs-budget computation the dashboard
overview already exposes (`DashboardService.get_overview`) rather than
recomputing it separately.
"""

from datetime import datetime, timezone
from typing import Annotated, Any

from langchain_core.tools import BaseTool, tool
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.enums import BudgetPeriod
from app.schemas.budget import BudgetCreate, BudgetUpdate
from app.services.budget_service import BudgetService
from app.services.category_service import CategoryService
from app.services.dashboard_service import DashboardService
from app.tools._helpers import as_tool_error, parse_date, to_json


def build_budget_tools(database: AsyncIOMotorDatabase, user_id: str) -> list[BaseTool]:
    budgets = BudgetService(database)
    dashboard = DashboardService(database)
    categories = CategoryService(database)

    @tool
    async def list_budgets() -> Any:
        """Lists the user's budgets (id, name, category_id, amount, period)."""
        return to_json(await budgets.list_budgets(user_id))

    @tool
    async def list_categories(transaction_type: Annotated[str | None, "'income', 'expense', or omit for both"] = None) -> Any:
        """Lists the user's categories (id, name, type). Call this to resolve
        a category name the user mentioned before create_budget."""
        return to_json(await categories.list_categories(user_id, category_type=transaction_type))

    @tool
    async def get_budget_usage() -> Any:
        """Returns spent/remaining amounts for every active budget this
        month. Use this to answer "how am I doing on my budgets" or to find
        which budgets are overspent."""
        try:
            overview = await dashboard.get_overview(user_id)
            return to_json(overview["budget_progress"])
        except Exception as exc:  # noqa: BLE001
            return as_tool_error(exc)

    @tool
    async def get_overspending_alerts() -> Any:
        """Returns only the budgets that are currently over their limit
        (spent > amount), with how much over each one is."""
        try:
            overview = await dashboard.get_overview(user_id)
            over = [item for item in overview["budget_progress"] if item["spent"] > item["amount"]]
            return [
                {**to_json(item), "over_by": item["spent"] - item["amount"]}
                for item in over
            ]
        except Exception as exc:  # noqa: BLE001
            return as_tool_error(exc)

    @tool
    async def create_budget(
        amount: Annotated[float, "must be greater than 0"],
        currency: Annotated[str, "3-letter ISO currency code, e.g. 'USD'"],
        period: Annotated[str, "'weekly', 'monthly', 'yearly', or 'custom'"] = "monthly",
        category_id: Annotated[str | None, "omit for an overall (all-category) budget"] = None,
        name: str | None = None,
        start_date: Annotated[str | None, "ISO date; defaults to today"] = None,
        end_date: str | None = None,
    ) -> Any:
        """Creates a new budget. Look up category_id first with
        list_categories if the user named a category."""
        try:
            start = parse_date(start_date, default=datetime.now(timezone.utc))
            payload = BudgetCreate(
                category_id=category_id,
                name=name,
                amount=amount,
                currency=currency,
                period=BudgetPeriod(period),
                start_date=start,
                end_date=parse_date(end_date),
            )
            return to_json(await budgets.create_budget(user_id, payload))
        except Exception as exc:  # noqa: BLE001
            return as_tool_error(exc)

    @tool
    async def update_budget(
        budget_id: str,
        amount: float | None = None,
        name: str | None = None,
        end_date: Annotated[str | None, "ISO date"] = None,
    ) -> Any:
        """Updates a budget's name, amount, or end date."""
        try:
            payload = BudgetUpdate(amount=amount, name=name, end_date=parse_date(end_date))
            return to_json(await budgets.update_budget(user_id, budget_id, payload))
        except Exception as exc:  # noqa: BLE001
            return as_tool_error(exc)

    @tool
    async def delete_budget(budget_id: str) -> Any:
        """Deletes a budget."""
        try:
            await budgets.delete_budget(user_id, budget_id)
            return {"deleted": True, "budget_id": budget_id}
        except Exception as exc:  # noqa: BLE001
            return as_tool_error(exc)

    return [
        list_budgets,
        list_categories,
        get_budget_usage,
        get_overspending_alerts,
        create_budget,
        update_budget,
        delete_budget,
    ]
