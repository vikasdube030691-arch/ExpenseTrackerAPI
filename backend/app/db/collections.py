class Collections:
    USERS = "users"
    REFRESH_TOKENS = "refresh_tokens"
    ACCOUNTS = "accounts"
    TRANSACTIONS = "transactions"
    CATEGORIES = "categories"
    BUDGETS = "budgets"
    RECURRING_TRANSACTIONS = "recurring_transactions"
    CHAT_SESSIONS = "chat_sessions"
    CHAT_MESSAGES = "chat_messages"
    GENERATED_REPORTS = "generated_reports"
    DASHBOARD_PREFERENCES = "dashboard_preferences"
    AUDIT_LOGS = "audit_logs"

    @classmethod
    def all(cls) -> list[str]:
        return [
            cls.USERS,
            cls.REFRESH_TOKENS,
            cls.ACCOUNTS,
            cls.TRANSACTIONS,
            cls.CATEGORIES,
            cls.BUDGETS,
            cls.RECURRING_TRANSACTIONS,
            cls.CHAT_SESSIONS,
            cls.CHAT_MESSAGES,
            cls.GENERATED_REPORTS,
            cls.DASHBOARD_PREFERENCES,
            cls.AUDIT_LOGS,
        ]
