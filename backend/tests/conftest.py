import pytest_asyncio
from mongomock_motor import AsyncMongoMockClient


@pytest_asyncio.fixture
async def database():
    client = AsyncMongoMockClient()
    yield client["expensedb_test"]
