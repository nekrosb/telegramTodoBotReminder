from datetime import UTC, datetime

import pytest

from telegramtodobotreminder.database.reminders import create, list_for_user
from telegramtodobotreminder.database.users import create as create_user


@pytest.mark.asyncio
async def test_reminder_is_stored_for_the_owner(database):
    await create_user(database, telegram_id=123, language="en")
    event = datetime(2026, 10, 26, 17, 30, tzinfo=UTC)

    reminder_id = await create(database, 123, "Team meeting", event)
    reminders = await list_for_user(database, 123)

    assert reminder_id == 1
    assert reminders[0]["title"] == "Team meeting"
    assert reminders[0]["remind_at"] == event.isoformat()
    assert reminders[0]["status"] == "scheduled"


@pytest.mark.asyncio
async def test_reminder_requires_registered_owner(database):
    with pytest.raises(ValueError, match="unregistered"):
        await create(
            database,
            123,
            "Team meeting",
            datetime(2026, 10, 26, 17, 30, tzinfo=UTC),
        )
