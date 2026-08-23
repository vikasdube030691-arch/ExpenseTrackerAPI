"""Tools for the Analytics Agent: monthly summaries, period comparisons,
trends, top categories, and savings — all read-only, all backed by
`DashboardService`'s existing user-scoped aggregation queries.
"""

from typing import Annotated, Any

from langchain_core.tools import BaseTool, tool
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.category_service import CategoryService
from app.services.dashboard_service import DashboardService
from app.tools._helpers import as_tool_error, current_month_range, parse_date, to_json


def build_analytics_tools(database: AsyncIOMotorDatabase, user_id: str) -> list[BaseTool]:
    dashboard = DashboardService(database)
    categories_service = CategoryService(database)

    async def _category_names() -> dict[str, str]:
        return {category.id: category.name for category in await categories_service.list_categories(user_id)}

    @tool
    async def get_summary(
        start_date: Annotated[str | None, "ISO date; defaults to the start of the current month"] = None,
        end_date: Annotated[str | None, "ISO date; defaults to today"] = None,
    ) -> Any:
        """Returns total income, total expense, net, and transaction count
        for a period. Omit both dates for the current calendar month."""
        try:
            default_start, default_end = current_month_range()
            start = parse_date(start_date, default=default_start)
            end = parse_date(end_date, default=default_end)
            return to_json(await dashboard.get_summary(user_id, start, end))
        except Exception as exc:  # noqa: BLE001
            return as_tool_error(exc)

    @tool
    async def compare_periods(
        period_a_start: Annotated[str, "ISO date"],
        period_a_end: Annotated[str, "ISO date"],
        period_b_start: Annotated[str, "ISO date"],
        period_b_end: Annotated[str, "ISO date"],
    ) -> Any:
        """Compares two date ranges (e.g. this month vs last month) and
        returns both summaries plus the change in expense and income."""
        try:
            a_start, a_end = parse_date(period_a_start), parse_date(period_a_end)
            b_start, b_end = parse_date(period_b_start), parse_date(period_b_end)
            if not (a_start and a_end and b_start and b_end):
                return {"error": "all four dates are required"}
            summary_a = await dashboard.get_summary(user_id, a_start, a_end)
            summary_b = await dashboard.get_summary(user_id, b_start, b_end)
            return {
                "period_a": to_json(summary_a),
                "period_b": to_json(summary_b),
                "expense_change": summary_b["total_expense"] - summary_a["total_expense"],
                "income_change": summary_b["total_income"] - summary_a["total_income"],
            }
        except Exception as exc:  # noqa: BLE001
            return as_tool_error(exc)

    @tool
    async def get_trends(
        granularity: Annotated[str, "'day' or 'month'"] = "month",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> Any:
        """Returns income/expense totals per period (day or month) over a
        date range, for spotting trends over time."""
        try:
            default_start, default_end = current_month_range()
            start = parse_date(start_date, default=default_start)
            end = parse_date(end_date, default=default_end)
            return to_json(await dashboard.get_trends(user_id, start, end, granularity))
        except Exception as exc:  # noqa: BLE001
            return as_tool_error(exc)

    @tool
    async def get_top_categories(
        start_date: str | None = None,
        end_date: str | None = None,
        limit: Annotated[int, "max 20"] = 5,
    ) -> Any:
        """Returns the top spending categories (by total expense) for a
        period, with category names already resolved."""
        try:
            default_start, default_end = current_month_range()
            start = parse_date(start_date, default=default_start)
            end = parse_date(end_date, default=default_end)
            analysis = await dashboard.get_category_analysis(user_id, start, end)
            names = await _category_names()
            ranked = sorted(analysis["breakdown"], key=lambda item: item["total"], reverse=True)[: min(limit, 20)]
            return [
                {"category": names.get(item["category_id"], "Uncategorized"), "total": item["total"], "count": item["count"]}
                for item in ranked
            ]
        except Exception as exc:  # noqa: BLE001
            return as_tool_error(exc)

    @tool
    async def get_savings_analysis(start_date: str | None = None, end_date: str | None = None) -> Any:
        """Returns income, expense, net savings, and savings rate (net /
        income) for a period. Useful for "how much am I saving" questions."""
        try:
            default_start, default_end = current_month_range()
            start = parse_date(start_date, default=default_start)
            end = parse_date(end_date, default=default_end)
            summary = await dashboard.get_summary(user_id, start, end)
            income = summary["total_income"]
            savings_rate = (summary["net"] / income * 100) if income > 0 else None
            return {**to_json(summary), "savings_rate_percent": savings_rate}
        except Exception as exc:  # noqa: BLE001
            return as_tool_error(exc)

    return [get_summary, compare_periods, get_trends, get_top_categories, get_savings_analysis]
