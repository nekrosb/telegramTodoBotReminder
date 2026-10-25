import aiosqlite
import pytest
from telegramtodobotreminder.database.users import (
    create,
    get_by_telegram_id,
    update_language,
    update_timezone,
)
@pytest.mark.asyncio
async def test_user_registration_is_persisted(database):
    await create(database, telegram_id=123, language="en")

    user = await get_by_telegram_id(database, telegram_id=123)

    assert user["telegram_id"] == 123
    assert user["language"] == "en"
    assert user["timezone"] == "UTC"


@pytest.mark.asyncio
async def test_duplicate_telegram_id_is_rejected(database):
    await create(database, telegram_id=123, language="ru")

    with pytest.raises(aiosqlite.IntegrityError):
        await create(database, telegram_id=123, language="en")


@pytest.mark.asyncio
async def test_user_language_can_be_updated(database):
    await create(database, telegram_id=123, language="ru")

    await update_language(database, telegram_id=123, language="en")

    user = await get_by_telegram_id(database, telegram_id=123)
    assert user["language"] == "en"


@pytest.mark.asyncio
async def test_user_timezone_can_be_updated(database):
    await create(database, telegram_id=123, language="en")

    await update_timezone(database, telegram_id=123, timezone="Europe/Berlin")

    user = await get_by_telegram_id(database, telegram_id=123)
    assert user["timezone"] == "Europe/Berlin"
