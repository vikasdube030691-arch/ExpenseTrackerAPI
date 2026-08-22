from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.core.rate_limit import limiter
from app.db.mongodb import close_mongo_connection, connect_to_mongo, mongodb


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await connect_to_mongo()
    yield
    await close_mongo_connection()


tags_metadata = [
    {"name": "auth", "description": "Registration, login, logout, and token refresh."},
    {"name": "accounts", "description": "Bank/cash/card accounts a user tracks balances in."},
    {"name": "transactions", "description": "Income/expense records."},
    {"name": "categories", "description": "User and shared system categories."},
    {"name": "budgets", "description": "Spending limits per category and period."},
    {"name": "dashboard", "description": "Aggregated analytics for the current user."},
    {"name": "reports", "description": "Generated report requests and history."},
    {"name": "chat", "description": "AI assistant chat sessions and messages."},
    {"name": "health", "description": "Liveness and readiness probes."},
]

app = FastAPI(
    title="ExpenseTrackerAPI",
    description="REST API for the AI Expense Tracker.",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=tags_metadata,
)

app.state.limiter = limiter

# Order matters: Starlette wraps middleware in reverse of registration order, so the
# *first* one added ends up outermost. CORS goes first so it still adds headers to
# responses produced by anything below it (including our own exception handlers).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)
# Applies `limiter`'s `default_limits` to every route; per-route `@limiter.limit(...)`
# decorators (e.g. login's stricter limit) still override it for that route.
app.add_middleware(SlowAPIMiddleware)

register_exception_handlers(app)

app.include_router(api_router)


@app.get("/health", tags=["health"], summary="Liveness check")
async def health_check() -> dict:
    return {"status": "ok"}


@app.get("/ready", tags=["health"], summary="Readiness check")
async def readiness_check() -> JSONResponse:
    if mongodb.client is None:
        return JSONResponse(status_code=503, content={"status": "not_ready", "reason": "database not connected"})
    try:
        await mongodb.client.admin.command("ping")
    except Exception:
        return JSONResponse(status_code=503, content={"status": "not_ready", "reason": "database unreachable"})
    return JSONResponse(status_code=200, content={"status": "ready"})
