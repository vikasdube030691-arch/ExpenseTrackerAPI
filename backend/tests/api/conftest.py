import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi.middleware import SlowAPIMiddleware

from app.api.deps import get_db
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.core.middleware import RequestContextMiddleware
from app.core.rate_limit import limiter


@pytest_asyncio.fixture
async def client(database):
    app = FastAPI()
    app.state.limiter = limiter
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(SlowAPIMiddleware)
    register_exception_handlers(app)
    app.include_router(api_router)
    app.dependency_overrides[get_db] = lambda: database

    # TestClient talks to the app over plain http://testserver; a real browser would
    # get this over https, but here force cookie_secure off so the Secure flag
    # doesn't stop httpx's cookie jar from round-tripping the refresh cookie.
    original_cookie_secure = settings.cookie_secure
    settings.cookie_secure = False

    limiter.reset()
    with TestClient(app) as test_client:
        yield test_client
    limiter.reset()
    settings.cookie_secure = original_cookie_secure
