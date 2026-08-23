from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.db.collections import Collections

INDEX_SPECS: dict[str, list[IndexModel]] = {
    Collections.USERS: [
        IndexModel([("email", ASCENDING)], unique=True, name="uniq_email"),
        IndexModel([("is_deleted", ASCENDING)], name="is_deleted"),
    ],
    Collections.REFRESH_TOKENS: [
        IndexModel([("user_id", ASCENDING)], name="user_id"),
        IndexModel([("token_hash", ASCENDING)], unique=True, name="uniq_token_hash"),
        # TTL index: MongoDB automatically deletes expired refresh tokens.
        IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0, name="ttl_expires_at"),
    ],
    Collections.ACCOUNTS: [
        IndexModel([("user_id", ASCENDING), ("is_deleted", ASCENDING)], name="user_active"),
        IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)], name="user_created"),
    ],
    Collections.TRANSACTIONS: [
        IndexModel([("user_id", ASCENDING), ("transaction_date", DESCENDING)], name="user_txn_date"),
        IndexModel([("user_id", ASCENDING), ("transaction_type", ASCENDING)], name="user_txn_type"),
        IndexModel([("user_id", ASCENDING), ("category_id", ASCENDING)], name="user_category"),
        IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)], name="user_created"),
        IndexModel([("user_id", ASCENDING), ("account_id", ASCENDING)], name="user_account"),
        IndexModel(
            [("user_id", ASCENDING), ("transaction_date", DESCENDING), ("transaction_type", ASCENDING)],
            name="user_analytics",
        ),
        IndexModel([("user_id", ASCENDING), ("is_deleted", ASCENDING)], name="user_active"),
        IndexModel([("tags", ASCENDING)], name="tags"),
    ],
    Collections.CATEGORIES: [
        IndexModel(
            [("user_id", ASCENDING), ("name", ASCENDING), ("type", ASCENDING)],
            unique=True,
            name="uniq_user_name_type",
        ),
        IndexModel([("user_id", ASCENDING), ("is_deleted", ASCENDING)], name="user_active"),
    ],
    Collections.BUDGETS: [
        IndexModel([("user_id", ASCENDING), ("period", ASCENDING)], name="user_period"),
        IndexModel([("user_id", ASCENDING), ("category_id", ASCENDING)], name="user_category"),
        IndexModel([("user_id", ASCENDING), ("start_date", DESCENDING)], name="user_start_date"),
    ],
    Collections.RECURRING_TRANSACTIONS: [
        IndexModel([("user_id", ASCENDING), ("is_active", ASCENDING)], name="user_active"),
        IndexModel([("next_run_date", ASCENDING)], name="next_run_date"),
    ],
    Collections.CHAT_SESSIONS: [
        IndexModel([("user_id", ASCENDING), ("last_message_at", DESCENDING)], name="user_recent_sessions"),
        IndexModel([("user_id", ASCENDING), ("is_deleted", ASCENDING)], name="user_active"),
    ],
    Collections.CHAT_MESSAGES: [
        IndexModel([("session_id", ASCENDING), ("created_at", ASCENDING)], name="session_messages"),
        IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)], name="user_created"),
    ],
    Collections.GENERATED_REPORTS: [
        IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)], name="user_created"),
        IndexModel([("user_id", ASCENDING), ("report_type", ASCENDING)], name="user_report_type"),
        IndexModel([("status", ASCENDING)], name="status"),
    ],
    Collections.DASHBOARD_PREFERENCES: [
        IndexModel([("user_id", ASCENDING)], unique=True, name="uniq_user"),
    ],
    Collections.AUDIT_LOGS: [
        IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)], name="user_created"),
        IndexModel([("action", ASCENDING), ("created_at", DESCENDING)], name="action_created"),
        IndexModel([("resource_type", ASCENDING), ("resource_id", ASCENDING)], name="resource_lookup"),
    ],
    Collections.USER_MEMORIES: [
        IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)], name="user_created"),
    ],
}


async def create_all_indexes(database: AsyncIOMotorDatabase) -> dict[str, list[str]]:
    created: dict[str, list[str]] = {}
    for collection_name, index_models in INDEX_SPECS.items():
        names = await database[collection_name].create_indexes(index_models)
        created[collection_name] = names
    return created
