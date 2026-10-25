from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from telegramtodobotreminder.timezones import local_to_utc


class ReminderInputError(ValueError):
    """Raised when reminder input is invalid."""


def validate_reminder_date(
    date_text: str, timezone: str, now: datetime | None = None
) -> date:
    try:
        value = datetime.strptime(date_text.strip(), "%Y-%m-%d").date()
    except ValueError as error:
        raise ReminderInputError("Use the date format YYYY-MM-DD.") from error

    current_time = now or datetime.now(UTC)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=UTC)
    current_date = current_time.astimezone(ZoneInfo(timezone)).date()
    if value < current_date:
        raise ReminderInputError("The reminder date must not be in the past.")
    return value


def parse_reminder_datetime(
    date_text: str, time_text: str, timezone: str, now: datetime | None = None
) -> datetime:
    try:
        local_value = datetime.strptime(
            f"{date_text.strip()} {time_text.strip()}",
            "%Y-%m-%d %H:%M",
        )
    except ValueError as error:
        raise ReminderInputError(
            "Use the date format YYYY-MM-DD and the time format HH:MM."
        ) from error

    try:
        remind_at = local_to_utc(local_value, timezone)
    except ValueError as error:
        raise ReminderInputError(str(error)) from error

    current_time = now or datetime.now(UTC)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=UTC)
    if remind_at <= current_time.astimezone(UTC):
        raise ReminderInputError("The reminder time must be in the future.")
    return remind_at
