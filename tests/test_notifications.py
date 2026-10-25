from datetime import UTC, datetime, timedelta

import pytest

from telegramtodobotreminder.database.notifications import create_for_reminder
from telegramtodobotreminder.database.reminders import create
from telegramtodobotreminder.database.users import create as create_user


@pytest.mark.asyncio
async def test_all_notification_offsets_are_created_for_distant_event(database):
    await create_user(database, telegram_id=123, language="en")
    event = datetime.now(UTC) + timedelta(days=3)

    reminder_id = await create(database, 123, "Distant event", event)
    cursor = await database.execute(
        "SELECT notification_type FROM reminder_notifications "
        "WHERE reminder_id = ? ORDER BY notification_type",
        (reminder_id,),
    )

    assert [row[0] for row in await cursor.fetchall()] == ["15m", "1d", "1h", "3h"]


@pytest.mark.asyncio
async def test_one_day_notification_is_skipped_within_two_day_threshold(database):
    await create_user(database, telegram_id=123, language="en")
    event = datetime.now(UTC) + timedelta(days=2)

    reminder_id = await create(database, 123, "Near event", event)
    cursor = await database.execute(
        "SELECT notification_type FROM reminder_notifications "
        "WHERE reminder_id = ?",
        (reminder_id,),
    )
    types = {row[0] for row in await cursor.fetchall()}

    assert "1d" not in types
    assert types == {"15m", "1h", "3h"}


@pytest.mark.asyncio
async def test_disabled_notification_is_not_created(database):
    await create_user(database, telegram_id=123, language="en")
    event = datetime.now(UTC) + timedelta(days=3)
    reminder_id = await create(
        database,
        123,
        "Selective event",
        event,
        notify_1d=False,
        notify_1h=False,
    )

    cursor = await database.execute(
        "SELECT notification_type FROM reminder_notifications "
        "WHERE reminder_id = ?",
        (reminder_id,),
    )
    assert {row[0] for row in await cursor.fetchall()} == {"15m", "3h"}


@pytest.mark.asyncio
async def test_global_push_setting_disables_new_notifications(database):
    await create_user(database, telegram_id=123, language="en")
    await database.execute(
        "UPDATE users SET push_notifications = 0 WHERE telegram_id = 123"
    )
    await database.commit()

    reminder_id = await create(
        database, 123, "Silent event", datetime.now(UTC) + timedelta(days=3)
    )
    cursor = await database.execute(
        "SELECT COUNT(*) FROM reminder_notifications WHERE reminder_id = ?",
        (reminder_id,),
    )
    assert (await cursor.fetchone())[0] == 0
