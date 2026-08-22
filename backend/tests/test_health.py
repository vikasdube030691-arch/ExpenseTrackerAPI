from unittest.mock import AsyncMock

from app.db import mongodb as mongodb_module
from app.main import health_check, readiness_check


async def test_health_check_is_always_ok():
    result = await health_check()

    assert result == {"status": "ok"}


async def test_readiness_check_reports_not_ready_without_a_connection(monkeypatch):
    monkeypatch.setattr(mongodb_module.mongodb, "client", None)

    response = await readiness_check()

    assert response.status_code == 503


async def test_readiness_check_reports_ready_when_ping_succeeds(monkeypatch):
    fake_client = AsyncMock()
    fake_client.admin.command = AsyncMock(return_value={"ok": 1})
    monkeypatch.setattr(mongodb_module.mongodb, "client", fake_client)

    response = await readiness_check()

    assert response.status_code == 200


async def test_readiness_check_reports_not_ready_when_ping_fails(monkeypatch):
    fake_client = AsyncMock()
    fake_client.admin.command = AsyncMock(side_effect=Exception("connection refused"))
    monkeypatch.setattr(mongodb_module.mongodb, "client", fake_client)

    response = await readiness_check()

    assert response.status_code == 503
