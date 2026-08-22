"""Builds untrusted, LLM-shaped generative-UI JSON from a user's real data.

This stands in for what a real LLM would return as structured output
alongside its text reply (see `app/services/ai/chat_completion.py`) — its
output is deliberately treated as untrusted. The caller (`ChatService`) always
runs it through `app.schemas.generative_ui.validate_ui_blocks` before it is
persisted or reaches an API response, exactly as it would for a genuine
model's output.
"""

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.common import utcnow
from app.services.category_service import CategoryService
from app.services.dashboard_service import DashboardService

_SPENDING_KEYWORDS = ("spend", "spent", "expense", "budget", "categor", "afford", "cost")
_MAX_CATEGORIES_SHOWN = 6


async def build_ui_blocks(database: AsyncIOMotorDatabase, user_id: str, user_message: str) -> list[dict[str, Any]]:
    """Returns raw (unvalidated) UI block dicts relevant to the user's
    message, built from their real transactions for the current calendar
    month. Returns `[]` when the message doesn't look finance-related, or the
    account has no transactions yet — a text-only reply is a perfectly valid
    generative UI response.
    """
    lowered = user_message.lower()
    if not any(keyword in lowered for keyword in _SPENDING_KEYWORDS):
        return []

    dashboard = DashboardService(database)
    categories_service = CategoryService(database)

    now = utcnow()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    summary = await dashboard.get_summary(user_id, start_of_month, now)
    if summary["transaction_count"] == 0:
        return []

    analysis = await dashboard.get_category_analysis(user_id, start_of_month, now)
    category_names = {category.id: category.name for category in await categories_service.list_categories(user_id)}
    breakdown = sorted(analysis["breakdown"], key=lambda item: item["total"], reverse=True)[:_MAX_CATEGORIES_SHOWN]

    blocks: list[dict[str, Any]] = [
        {
            "component": "metric_card",
            "title": "Spent this month",
            "value": f"${summary['total_expense']:,.2f}",
            "tone": "negative" if summary["net"] < 0 else "neutral",
            "icon": "trending_down",
        }
    ]

    if breakdown:
        blocks.append(
            {
                "component": "bar_chart",
                "title": "Spending by category this month",
                "categories": [category_names.get(item["category_id"], "Uncategorized") for item in breakdown],
                "series": [{"name": "Spent", "data": [item["total"] for item in breakdown]}],
            }
        )

        top = breakdown[0]
        blocks.append(
            {
                "component": "insight_card",
                "title": "Top category",
                "body": (
                    f"{category_names.get(top['category_id'], 'Uncategorized')} is your biggest expense "
                    f"category so far this month, at ${top['total']:,.2f} across {top['count']} transaction"
                    f"{'s' if top['count'] != 1 else ''}."
                ),
                "icon": "insights",
                "tone": "neutral",
            }
        )

    blocks.append({"component": "action_button", "label": "View all transactions", "action": "navigate_transactions"})

    return blocks
