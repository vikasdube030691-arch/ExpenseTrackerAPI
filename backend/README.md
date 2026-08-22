# ExpenseTrackerAPI — Backend

FastAPI + async MongoDB backend for the AI Expense Tracker.

## Architecture

```
backend/
  app/
    core/
      config.py            Settings (env-driven: Mongo URI, db name, pool sizes, JWT/cookie/CORS/rate-limit config)
      exceptions.py          App-level exceptions (DocumentNotFoundError, DuplicateDocumentError, ...)
      security.py             Password hashing (bcrypt) and refresh-token hashing (sha256)
      jwt.py                    Stateless access-token create/decode (PyJWT), with jti + type claims
      rate_limit.py              slowapi Limiter: default_limits for every route + a stricter override on /auth/login
      logging.py                 JSON log formatter + a contextvar carrying the current request id
      middleware.py               RequestContextMiddleware: assigns/echoes X-Request-ID, logs one line per request
      exception_handlers.py       Maps every exception type to the same {"error": {...}} envelope
    db/
      mongodb.py               Motor client lifecycle: connect_to_mongo / close_mongo_connection / get_database
      collections.py            Collection name constants
      indexes.py                 Index specifications + create_all_indexes()
      init_db.py                  Migration/init script: creates collections, indexes, optional sample data
      sample_data.py                Builds one cross-referenced sample document per collection
    models/                        MongoDB DOCUMENT models (what's actually stored) — Pydantic
    schemas/                       API request/response models — Pydantic, never expose ObjectId or internal fields
      common.py                     PaginationParams / PaginatedResponse — the one pagination shape used everywhere
      error.py                      ErrorDetail / ErrorResponse — the one error shape used everywhere
    repositories/                  One class per collection; every MongoDB query lives here, nowhere else
    services/                      Business logic; the only layer route handlers should call
      auth_service.py               Refresh-token/session persistence + revocation (the `refresh_tokens` collection)
      authentication_service.py     Orchestrates UserService + AuthService + app.core.jwt for register/login/logout/refresh
      ai/chat_completion.py          Placeholder reply generator (no LLM wired up) — swap this to add a real one
    api/
      deps.py                       get_db, get_current_user (Bearer JWT), pagination_params, make_sort_dependency
      v1/api.py                      Aggregates every router under /api/v1
      v1/{auth,accounts,transactions,categories,budgets,dashboard,reports,chat}.py
    agents/, tools/, mcp/          Reserved for a future AI-agent layer (still unused; chat is a plain request/response service)
    main.py                         FastAPI app: lifespan, CORS, request-context + rate-limit middleware, error handlers, routers
  tests/
    conftest.py                    In-memory Mongo (mongomock-motor) fixture — no real server needed for tests
    repositories/                  Repository unit tests
    services/                      Service-layer unit tests
    api/                           Router-level integration tests (FastAPI TestClient + mongomock), incl. error envelope,
                                    request-id propagation, and rate limiting
    test_jwt.py / test_security.py / test_health.py
  Dockerfile
  requirements.txt / requirements-dev.txt
  .env.example
  pytest.ini
```

**Layering rule:** `api` → `services` → `repositories` → MongoDB. Route handlers never touch `motor` or `pymongo` directly; they call a service, which calls one or more repositories. Every dependency a route needs (the current user, the database, pagination params, a sort spec) comes from `app/api/deps.py` via FastAPI's `Depends`, not constructed inline.

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

102 tests, all against `mongomock-motor` (in-memory, no real server needed) — repository tests, service tests, and full HTTP-level router tests (every endpoint below, plus error-envelope shape, request-id propagation, and the login rate limit actually tripping 429).

## API

All endpoints are under `/api/v1`. Interactive docs (OpenAPI/Swagger) at `/docs`, ReDoc at `/redoc`, raw schema at `/openapi.json`, once the server is running.

| Module | Endpoints |
|---|---|
| **auth** | `POST /auth/{register,login,logout,refresh,logout-all}`, `GET /auth/me` |
| **accounts**¹ | `GET/POST /accounts`, `PUT/DELETE /accounts/{id}` |
| **transactions** | `GET/POST /transactions`, `GET/PUT/DELETE /transactions/{id}` |
| **categories** | `GET/POST /categories`, `PUT/DELETE /categories/{id}` |
| **budgets** | `GET/POST /budgets`, `PUT/DELETE /budgets/{id}` |
| **dashboard** | `GET /dashboard` (overview), `/summary`, `/category-analysis`, `/trends`, `GET/PUT /dashboard/preferences`² |
| **reports** | `POST /reports/generate`, `GET /reports`, `GET /reports/{id}` |
| **chat** | `POST /chat`, `POST /chat/stream` (SSE), `GET /chat/sessions`, `GET /chat/sessions/{id}` |
| **health** | `GET /health` (liveness, unversioned), `GET /ready` (readiness — pings MongoDB, unversioned) |

¹ Not one of the originally-specified modules — added because `transactions` requires an owned `account_id` and there was otherwise no way to obtain one through the API.
² Added for the frontend's Settings page (theme, default currency, widget layout) — the `dashboard_preferences` collection and service already existed from the DB-layer task, this just exposes it.

Every endpoint except `/auth/register`, `/auth/login`, `/auth/refresh`, `/health`, and `/ready` requires `Authorization: Bearer <access_token>` and only ever operates on the calling user's own data (see "User isolation" above — the same repository-level guarantee applies through the whole API, not just auth).

### Transactions: pagination, sorting, filtering

`GET /transactions` accepts:
- **Pagination** — `page` (default 1), `page_size` (default 20, max 100). Every list endpoint that can grow unbounded returns the same `PaginatedResponse` shape: `{items, total, page, page_size}` (`total_pages` is a computed property).
- **Sorting** — `sort=field` or `sort=-field` (descending), comma-separated for multiple fields, e.g. `sort=-transaction_date,amount`. Restricted to a per-endpoint whitelist (`transaction_date`, `amount`, `created_at`) — an unlisted field is a `422`, not a silent no-op or an unindexed collection scan.
- **Filtering** — `transaction_type` (income/expense), `account_id`, `category_id`, `start_date`/`end_date`, `min_amount`/`max_amount`, `tags`, and `search` (case-insensitive match against merchant or description).

`PUT /transactions/{id}` behaves as a partial update (only fields present in the body change) despite the verb, matching the schema already built for it; changing `amount`, `transaction_type`, or `account_id` reconciles the affected account balance(s) the same way create/delete do.

### Dashboard

- `GET /dashboard` — current-month summary + 5 most recent transactions + spent-vs-budget progress for every active budget, in one call.
- `GET /dashboard/summary`, `/category-analysis`, `/trends` — each accepts `start_date`/`end_date` (defaulting to the current calendar month); `/trends` also takes `granularity=month|day`.

### Reports

`POST /reports/generate` runs synchronously (no background worker exists) and returns the completed report. There's no PDF/CSV writer or object storage yet, so `file` stays null; the actual computed numbers (income/expense totals, or a category breakdown) are always returned in `data`, regardless of the requested `format`. Wire in a real writer + storage to start populating `file` without changing the schema.

### AI Chat

`ChatService` persists real sessions/messages, but no LLM is wired up — `app/services/ai/chat_completion.py` is a placeholder that echoes a canned response. `POST /chat/stream` demonstrates the real Server-Sent-Events contract the frontend should expect (`event: session` with the session id, then one `event: delta` per chunk, then `event: done`) using that placeholder; swap `generate_reply`/`stream_reply` for a real provider (e.g. the Claude API) without touching `ChatService` or the router.

## Cross-cutting concerns

- **Consistent responses.** Every error, from any source — a domain exception, a bad request body, an unhandled bug, a tripped rate limit — comes back as `{"error": {"code", "message", "request_id", "details"}}` (`app/core/exception_handlers.py`, `app/schemas/error.py`). Every list endpoint that isn't a small fixed set (categories, budgets) returns the same `PaginatedResponse` shape.
- **Request IDs.** `RequestContextMiddleware` assigns a `uuid4` (or reuses a client-supplied `X-Request-ID`), echoes it in the response header, and threads it into both structured logs and error responses — a client-reported error can be traced to one log line.
- **Structured logging.** One JSON line per request (method, path, status, duration, request_id) plus a full traceback line for unhandled exceptions (`app/core/logging.py`). `configure_logging()` runs at app startup.
- **Rate limiting.** `slowapi`'s `default_limits=["120/minute"]` applies to every route via `SlowAPIMiddleware`; `/auth/login` overrides it with a stricter `5/minute` per client IP. In-memory and per-process — a multi-instance deployment needs `Limiter(storage_uri="redis://...")` so the limit is shared.
- **Health vs. readiness.** `/health` never touches MongoDB (liveness: is the process up); `/ready` pings it (readiness: can it actually serve requests) and returns `503` if the ping fails or the connection was never established.

## Authentication

`POST /api/v1/auth/{register,login,logout,refresh,logout-all}`, `GET /api/v1/auth/me`. Interactive docs (OpenAPI/Swagger) at `/docs` once the server is running.

**Token model:**
- **Access token** — a short-lived (15 min default) stateless JWT (`app/core/jwt.py`), returned in the JSON response body. The frontend keeps it in memory only (never localStorage) and sends it as `Authorization: Bearer <token>`.
- **Refresh token** — a long-lived (30 days default) opaque random token. Only its SHA-256 hash is stored, in the `refresh_tokens` collection, alongside `user_agent`/`ip_address`/`expires_at`/`revoked` (this *is* the session record — one document per logged-in device). The raw token is set as an **HttpOnly, Secure, SameSite=Lax** cookie scoped to `/api/v1/auth`, so it is never readable by JavaScript and never appears in a JSON body — an XSS bug can't exfiltrate it.
- **Rotation.** Every `/refresh` call revokes the presented refresh token and issues a new one (`AuthService.rotate_refresh_token`); a stolen-then-reused refresh token fails on its second use.
- **Revocation.** `/logout` revokes the one session tied to the request's cookie. `/logout-all` (needs a valid access token) revokes every refresh token for that user — every other device is logged out immediately, since access tokens are short-lived and the next refresh attempt on those devices will fail.
- **Password hashing** — bcrypt (`app/core/security.py`), random per-password salt.
- **Generic errors** — wrong password and unknown email both return the identical `401 "Invalid email or password"`, so the endpoint never confirms which emails are registered.
- **Rate limiting** — `POST /login` is limited (default `5/minute` per client IP, `app/core/rate_limit.py`, `slowapi`); in-memory and per-process, so a multi-instance deployment needs a shared backend (e.g. `Limiter(storage_uri="redis://...")`).

**Why a cookie instead of the more common "put the refresh token in the JSON body" pattern:** an HttpOnly cookie can't be read by JavaScript at all, which is strictly safer against XSS than anything the frontend stores itself (localStorage, a JS variable, IndexedDB). The tradeoff is that non-browser API clients (curl, mobile apps) need a cookie jar to use `/refresh` and `/logout` — acceptable here since the Angular app is the only intended client.

Local dev note: the Angular dev server proxies `/api/*` to this backend (see `frontend/proxy.conf.json`), so the browser sees everything as same-origin and the cookie's `SameSite=Lax` works without any cross-site cookie complications. `main.py` still configures CORS (`cors_origins` setting, default `http://localhost:4200`) with `allow_credentials=True` for the case where frontend and backend are served from genuinely different origins.

## Known limitations / follow-ups

- **No multi-document transactions.** `TransactionService` adjusts an account's balance as a second (and on update, sometimes third) write after the transaction write itself. This is sequential, not atomic, because MongoDB multi-document transactions require a replica set (a standalone `mongod` — the default local dev setup — rejects `session.start_transaction()`). For production, run MongoDB as a (single-node) replica set and wrap these calls in a client session transaction.
- **In-memory rate limiting.** Fine for one instance; a multi-instance deployment needs `slowapi`'s Redis-backed storage so the limit is shared across processes.
- **No AI provider wired up.** `/chat` and `/chat/stream` work end-to-end (persistence, SSE) but reply with a canned placeholder — see "AI Chat" above.
- **No report file export.** `/reports/generate` returns real computed numbers in `data`, but never populates `file` (no PDF/CSV writer or object storage exists yet) — see "Reports" above.
- **`recurring_transactions` has no API.** The model/repository/service exist (from the earlier DB-layer task) but nothing schedules them into actual transactions yet, and no router was requested for this task.
