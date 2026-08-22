from datetime import datetime, timedelta, timezone

from bson import ObjectId

from app.db.collections import Collections


def _now() -> datetime:
    return datetime.now(timezone.utc)


def build_sample_documents() -> dict[str, list[dict]]:
    """Builds one consistent, cross-referenced sample document per collection.
    Each document is tagged with `_seed: True` so re-running the init script can
    safely clear and reinsert seed data without touching real user data."""
    now = _now()
    user_id = ObjectId()
    account_id = ObjectId()
    category_expense_id = ObjectId()
    category_income_id = ObjectId()
    transaction_id = ObjectId()
    chat_session_id = ObjectId()

    users = [
        {
            "_id": user_id,
            "email": "demo.user@expensetracker.dev",
            "hashed_password": "$2b$12$C6UzMDM.H6dfI/f/IKcEeO9aB0FsMFRPnMh1o.dPWEuJ7iiKlAv3W",
            "full_name": "Demo User",
            "role": "user",
            "is_active": True,
            "is_verified": True,
            "is_deleted": False,
            "deleted_at": None,
            "created_at": now,
            "updated_at": now,
            "_seed": True,
        }
    ]

    accounts = [
        {
            "_id": account_id,
            "user_id": user_id,
            "name": "Primary Checking",
            "account_type": "bank",
            "currency": "USD",
            "balance": 2450.75,
            "is_active": True,
            "is_deleted": False,
            "deleted_at": None,
            "created_at": now,
            "updated_at": now,
            "_seed": True,
        }
    ]

    categories = [
        {
            "_id": category_expense_id,
            "user_id": user_id,
            "name": "Groceries",
            "type": "expense",
            "icon": "shopping-cart",
            "color": "#4CAF50",
            "is_system": False,
            "is_deleted": False,
            "deleted_at": None,
            "created_at": now,
            "updated_at": now,
            "_seed": True,
        },
        {
            "_id": category_income_id,
            "user_id": user_id,
            "name": "Salary",
            "type": "income",
            "icon": "briefcase",
            "color": "#2196F3",
            "is_system": False,
            "is_deleted": False,
            "deleted_at": None,
            "created_at": now,
            "updated_at": now,
            "_seed": True,
        },
    ]

    transactions = [
        {
            "_id": transaction_id,
            "user_id": user_id,
            "account_id": account_id,
            "transaction_type": "expense",
            "amount": 84.32,
            "currency": "USD",
            "category_id": category_expense_id,
            "merchant": "Whole Foods Market",
            "description": "Weekly grocery shopping",
            "transaction_date": now - timedelta(days=1),
            "tags": ["groceries", "recurring"],
            "receipt": {
                "url": "https://storage.expensetracker.dev/receipts/demo-receipt-1.jpg",
                "filename": "receipt-1.jpg",
                "content_type": "image/jpeg",
                "size_bytes": 184320,
                "uploaded_at": now - timedelta(days=1),
            },
            "is_deleted": False,
            "deleted_at": None,
            "created_at": now - timedelta(days=1),
            "updated_at": now - timedelta(days=1),
            "_seed": True,
        }
    ]

    budgets = [
        {
            "_id": ObjectId(),
            "user_id": user_id,
            "category_id": category_expense_id,
            "name": "Monthly groceries budget",
            "amount": 400.0,
            "currency": "USD",
            "period": "monthly",
            "start_date": now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
            "end_date": None,
            "is_deleted": False,
            "deleted_at": None,
            "created_at": now,
            "updated_at": now,
            "_seed": True,
        }
    ]

    recurring_transactions = [
        {
            "_id": ObjectId(),
            "user_id": user_id,
            "account_id": account_id,
            "category_id": category_income_id,
            "transaction_type": "income",
            "amount": 4500.0,
            "currency": "USD",
            "description": "Monthly salary",
            "merchant": "Acme Corp",
            "frequency": "monthly",
            "interval": 1,
            "start_date": now,
            "end_date": None,
            "next_run_date": now + timedelta(days=30),
            "is_active": True,
            "is_deleted": False,
            "deleted_at": None,
            "created_at": now,
            "updated_at": now,
            "_seed": True,
        }
    ]

    chat_sessions = [
        {
            "_id": chat_session_id,
            "user_id": user_id,
            "title": "Budgeting help",
            "is_archived": False,
            "is_deleted": False,
            "deleted_at": None,
            "last_message_at": now,
            "created_at": now,
            "updated_at": now,
            "_seed": True,
        }
    ]

    chat_messages = [
        {
            "_id": ObjectId(),
            "session_id": chat_session_id,
            "user_id": user_id,
            "role": "user",
            "content": "How much did I spend on groceries this month?",
            "metadata": {},
            "created_at": now,
            "_seed": True,
        },
        {
            "_id": ObjectId(),
            "session_id": chat_session_id,
            "user_id": user_id,
            "role": "assistant",
            "content": "You've spent $84.32 on groceries so far this month.",
            "metadata": {"model": "claude-sonnet-5", "tokens": 42},
            "created_at": now,
            "_seed": True,
        },
    ]

    generated_reports = [
        {
            "_id": ObjectId(),
            "user_id": user_id,
            "report_type": "monthly_summary",
            "format": "pdf",
            "status": "completed",
            "period_start": now.replace(day=1),
            "period_end": now,
            "file": {
                "url": "https://storage.expensetracker.dev/reports/demo-report-1.pdf",
                "filename": "monthly-summary-2026-08.pdf",
                "size_bytes": 20480,
            },
            "error_message": None,
            "is_deleted": False,
            "deleted_at": None,
            "created_at": now,
            "updated_at": now,
            "_seed": True,
        }
    ]

    dashboard_preferences = [
        {
            "_id": ObjectId(),
            "user_id": user_id,
            "default_currency": "USD",
            "theme": "system",
            "widgets": ["spending_by_category", "monthly_trend", "budget_progress"],
            "settings": {},
            "created_at": now,
            "updated_at": now,
            "_seed": True,
        }
    ]

    audit_logs = [
        {
            "_id": ObjectId(),
            "user_id": user_id,
            "action": "transaction.create",
            "resource_type": "transaction",
            "resource_id": transaction_id,
            "metadata": {"amount": 84.32, "transaction_type": "expense"},
            "ip_address": "127.0.0.1",
            "user_agent": "sample-seed-script",
            "created_at": now,
            "_seed": True,
        }
    ]

    return {
        Collections.USERS: users,
        Collections.ACCOUNTS: accounts,
        Collections.CATEGORIES: categories,
        Collections.TRANSACTIONS: transactions,
        Collections.BUDGETS: budgets,
        Collections.RECURRING_TRANSACTIONS: recurring_transactions,
        Collections.CHAT_SESSIONS: chat_sessions,
        Collections.CHAT_MESSAGES: chat_messages,
        Collections.GENERATED_REPORTS: generated_reports,
        Collections.DASHBOARD_PREFERENCES: dashboard_preferences,
        Collections.AUDIT_LOGS: audit_logs,
        Collections.REFRESH_TOKENS: [],
    }
