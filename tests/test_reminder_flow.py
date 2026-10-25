from datetime import UTC, datetime

import pytest

from telegramtodobotreminder.reminder_flow import (
    ReminderInputError,
    parse_reminder_datetime,
    validate_reminder_date,
)


def test_reminder_datetime_uses_user_timezone():
    result = parse_reminder_datetime(
        "2026-10-26",
        "18:30",
        "Europe/Berlin",
        now=datetime(2026, 10, 25, 12, 0, tzinfo=UTC),
    )

    assert result.isoformat() == "2026-10-26T17:30:00+00:00"


@pytest.mark.parametrize(
    ("date_text", "time_text"),
    [("26-10-2026", "18:30"), ("2026-10-26", "invalid")],
)
def test_invalid_date_or_time_is_rejected(date_text, time_text):
    with pytest.raises(ReminderInputError, match="YYYY-MM-DD"):
        parse_reminder_datetime(
            date_text,
            time_text,
            "UTC",
            now=datetime(2026, 10, 25, 12, 0, tzinfo=UTC),
        )


def test_past_reminder_is_rejected():
    with pytest.raises(ReminderInputError, match="future"):
        parse_reminder_datetime(
            "2026-10-25",
            "11:00",
            "UTC",
            now=datetime(2026, 10, 25, 12, 0, tzinfo=UTC),
        )


def test_past_date_is_rejected_before_time_step():
    with pytest.raises(ReminderInputError, match="must not be in the past"):
        validate_reminder_date(
            "2026-10-24",
            "Europe/Berlin",
            now=datetime(2026, 10, 25, 12, 0, tzinfo=UTC),
        )


@pytest.mark.asyncio
async def test_empty_title_is_rejected_by_database(database):
    from telegramtodobotreminder.database.reminders import create
    from telegramtodobotreminder.database.users import create as create_user

    await create_user(database, telegram_id=123, language="en")
    with pytest.raises(ValueError, match="cannot be empty"):
        await create(
            database,
            123,
            "   ",
            datetime(2026, 10, 26, 17, 30, tzinfo=UTC),
        )
