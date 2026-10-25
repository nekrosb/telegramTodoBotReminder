import aiosqlite
import pytest_asyncio

from telegramtodobotreminder.database.connection import initialize


@pytest_asyncio.fixture
async def database():
    connection = await aiosqlite.connect(":memory:")
    await initialize(connection)
    yield connection
    await connection.close()
