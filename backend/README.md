# ExpenseTrackerAPI — Backend

FastAPI + async MongoDB backend for the AI Expense Tracker.

## Architecture

```
backend/
  app/
    core/
      config.py            Settings (env-driven: Mongo URI, db name, pool sizes, ...)
      exceptions.py          App-level exceptions (DocumentNotFoundError, DuplicateDocumentError, ...)
      security.py             Password hashing (bcrypt) and refresh-token hashing (sha256)
    db/
      mongodb.py               Motor client lifecycle: connect_to_mongo / close_mongo_connection / get_database
      collections.py            Collection name constants
      indexes.py                 Index specifications + create_all_indexes()
      init_db.py                  Migration/init script: creates collections, indexes, optional sample data
      sample_data.py                Builds one cross-referenced sample document per collection
    models/                        MongoDB DOCUMENT models (what's actually stored) — Pydantic
    schemas/                       API request/response models — Pydantic, never expose ObjectId or internal fields
    repositories/                  One class per collection; every MongoDB query lives here, nowhere else
    services/                      Business logic; the only layer route handlers should call
    api/, agents/, tools/, mcp/    Reserved for the FastAPI routers and AI chat/agent feature (not built in this task)
    main.py                         FastAPI app; wires Mongo connect/disconnect into the app lifespan
  tests/
    conftest.py                    In-memory Mongo (mongomock-motor) fixture — no real server needed for tests
    repositories/                  Repository unit tests
  Dockerfile
  requirements.txt / requirements-dev.txt
  .env.example
  pytest.ini
```

**Layering rule:** `api` → `services` → `repositories` → MongoDB. Route handlers never touch `motor` or `pymongo` directly; they call a service, which calls one or more repositories.

## Collections

| Collection | Purpose | Soft delete? |
|---|---|---|
| `users` | Account records, hashed password, role | yes |
| `refresh_tokens` | Hashed opaque refresh tokens; TTL-indexed, auto-expire | no (revoked flag + TTL) |
| `accounts` | Bank/cash/card accounts a user tracks balances in | yes |
| `transactions` | Income/expense records (the core entity) | yes |
| `categories` | User-defined + shared system categories | yes |
| `budgets` | Spending limits per category/period | yes |
| `recurring_transactions` | Templates that generate future transactions | yes |
| `chat_sessions` / `chat_messages` | AI chat history | sessions: yes, messages: append-only |
| `generated_reports` | Async-generated report metadata + file reference | yes |
| `dashboard_preferences` | One document per user; widget layout, theme, default currency | no (single mutable doc) |
| `audit_logs` | Immutable action trail | no (append-only, never deleted) |

Soft delete is a boolean `is_deleted` + `deleted_at` on documents users can meaningfully "undo" or that need an audit trail. `audit_logs` and `chat_messages` are append-only by design (`CreatedAtDocument` — only `created_at`, no `updated_at`), so soft delete doesn't apply.

## User isolation

Every domain repository (accounts, categories, transactions, budgets, recurring transactions, chat, reports, audit logs) exposes a `get_by_id_for_user(id, user_id)` / `list_for_user(user_id, ...)` method that filters by `user_id` in the query itself — not as a post-fetch check. Services always use these methods, never the generic `get_by_id`, so cross-user access is structurally prevented rather than relied upon.

## Indexes

Defined in `app/db/indexes.py`, applied by `init_db.py`. Highlights:

- `transactions`: compound indexes on `(user_id, transaction_date)`, `(user_id, transaction_type)`, `(user_id, category_id)`, `(user_id, created_at)`, `(user_id, account_id)`, and an analytics index `(user_id, transaction_date, transaction_type)` for dashboard queries.
- `chat_sessions`: `(user_id, last_message_at)` for "recent conversations" lookups.
- `chat_messages`: `(session_id, created_at)` for paginated session history.
- `refresh_tokens`: TTL index on `expires_at` (MongoDB auto-deletes expired tokens) plus a unique index on `token_hash`.
- `users`: unique index on `email`.
- `categories`: unique `(user_id, name, type)` to prevent duplicate categories per user.
- `dashboard_preferences`: unique `(user_id)` — one document per user.

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt   # includes test dependencies
copy .env.example .env                # adjust MONGODB_URI / MONGODB_DB_NAME if needed
```

Requires a local MongoDB server (tested against MongoDB 8.2 running as a Windows service on `mongodb://localhost:27017`).

## Initialize the database (`expensedb`)

```bash
python -m app.db.init_db                 # create collections + indexes
python -m app.db.init_db --with-samples  # also seed one sample document per collection
```

The script is idempotent: collections are only created if missing, indexes are declared by name (re-creating is a no-op), and sample documents are tagged `_seed: true` so re-running with `--with-samples` clears and reinserts them without touching real data.

## Run the API

```bash
uvicorn app.main:app --reload
```

## Tests

```bash
pytest
```

Repository tests run against `mongomock-motor`, an in-memory MongoDB-compatible driver — no real server required. 23 tests cover base CRUD, soft delete, user-isolation, currency/tag normalization, filtering, and aggregation (`sum_by_type`, `sum_by_category`).

## Known limitations / follow-ups

- **No multi-document transactions.** `TransactionService` adjusts an account's balance as a second write after inserting a transaction. This is sequential, not atomic, because MongoDB multi-document transactions require a replica set (a standalone `mongod` — the default local dev setup — rejects `session.start_transaction()`). For production, run MongoDB as a (single-node) replica set and wrap these calls in a client session transaction.
- **No FastAPI routers yet.** This task scoped the database layer (models → schemas → repositories → services). The `api/` folder is scaffolded but empty; routers should be added there and must call services only, never repositories directly.
- **No JWT issuance.** `AuthService` persists and rotates opaque refresh tokens (the `refresh_tokens` collection) but does not sign access tokens — that's an auth-layer concern layered on top of this DB layer.
