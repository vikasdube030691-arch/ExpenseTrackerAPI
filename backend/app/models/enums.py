from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class AccountType(str, Enum):
    CASH = "cash"
    BANK = "bank"
    CREDIT_CARD = "credit_card"
    WALLET = "wallet"
    SAVINGS = "savings"
    OTHER = "other"


class CategoryType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class BudgetPeriod(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class RecurringFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ReportType(str, Enum):
    MONTHLY_SUMMARY = "monthly_summary"
    CATEGORY_BREAKDOWN = "category_breakdown"
    TAX_SUMMARY = "tax_summary"
    CUSTOM = "custom"


class ReportFormat(str, Enum):
    PDF = "pdf"
    CSV = "csv"
    JSON = "json"


class ReportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
