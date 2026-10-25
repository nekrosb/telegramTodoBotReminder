from datetime import UTC, datetime, timedelta

import pytest

from telegramtodobotreminder.database.reminders import (
    create,
    delete_for_user,
    get_for_user,
    list_for_user,
    update_for_user,
)
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


@pytest.mark.asyncio
async def test_reminder_operations_are_limited_to_owner(database):
    await create_user(database, telegram_id=123, language="en")
    await create_user(database, telegram_id=456, language="en")
    reminder_id = await create(
        database, 123, "Private reminder", datetime(2026, 10, 26, 17, 30, tzinfo=UTC)
    )

    assert await get_for_user(database, 456, reminder_id) is None
    assert not await update_for_user(
        database,
        456,
        reminder_id,
        "Changed by another user",
        datetime(2026, 10, 27, 17, 30, tzinfo=UTC),
    )
    assert not await delete_for_user(database, 456, reminder_id)
    assert (await get_for_user(database, 123, reminder_id))["title"] == "Private reminder"


@pytest.mark.asyncio
async def test_owner_can_update_and_delete_reminder(database):
    await create_user(database, telegram_id=123, language="en")
    reminder_id = await create(
        database, 123, "Original", datetime(2026, 10, 26, 17, 30, tzinfo=UTC)
    )

    assert await update_for_user(
        database,
        123,
        reminder_id,
        "Updated",
        datetime(2026, 10, 27, 17, 30, tzinfo=UTC),
    )
    assert (await get_for_user(database, 123, reminder_id))["title"] == "Updated"
    assert await delete_for_user(database, 123, reminder_id)
    assert await get_for_user(database, 123, reminder_id) is None


@pytest.mark.asyncio
async def test_updating_reminder_rebuilds_pending_notifications(database):
    await create_user(database, telegram_id=123, language="en")
    old_event = datetime.now(UTC) + timedelta(days=3)
    reminder_id = await create(database, 123, "Original", old_event)

    new_event = datetime.now(UTC) + timedelta(days=4)
    assert await update_for_user(database, 123, reminder_id, "Updated", new_event)

    cursor = await database.execute(
        """
        SELECT scheduled_at
        FROM reminder_notifications
        WHERE reminder_id = ? AND notification_type = '3h'
        """,
        (reminder_id,),
    )
    scheduled_at = datetime.fromisoformat((await cursor.fetchone())[0])
    assert scheduled_at == new_event - timedelta(hours=3)
