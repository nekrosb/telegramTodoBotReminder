from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


COMMON_TIMEZONES = (
    ("UTC", "UTC"),
    ("Europe/Berlin", "Berlin"),
    ("Europe/Moscow", "Moscow"),
    ("Europe/Zurich", "Zurich"),
    ("America/New_York", "New York"),
    ("Asia/Tokyo", "Tokyo"),
)


class InvalidTimezoneError(ValueError):
    """Raised when a timezone is not a valid IANA timezone identifier."""


class AmbiguousLocalTimeError(ValueError):
    """Raised when a local time occurs twice during a DST transition."""


class NonexistentLocalTimeError(ValueError):
    """Raised when a local time does not occur during a DST transition."""


def get_timezone(identifier: str) -> ZoneInfo:
    try:
        return ZoneInfo(identifier)
    except ZoneInfoNotFoundError as error:
        raise InvalidTimezoneError(f"Unknown IANA timezone: {identifier}") from error


def local_to_utc(value: datetime, timezone: str) -> datetime:
    """Convert a local wall-clock time to UTC, rejecting DST edge cases."""
    if value.tzinfo is not None:
        raise ValueError("local time must not have timezone information")

    zone = get_timezone(timezone)
    candidates = []
    for fold in (0, 1):
        localized = value.replace(tzinfo=zone, fold=fold)
        round_trip = localized.astimezone(UTC).astimezone(zone).replace(tzinfo=None)
        if round_trip == value:
            candidates.append(localized.astimezone(UTC))

    unique_candidates = set(candidates)
    if not unique_candidates:
        raise NonexistentLocalTimeError(f"Local time does not exist: {value}")
    if len(unique_candidates) > 1:
        raise AmbiguousLocalTimeError(f"Local time is ambiguous: {value}")
    return unique_candidates.pop()


def utc_to_local(value: datetime, timezone: str) -> datetime:
    """Convert an aware UTC datetime to the user's local timezone."""
    if value.tzinfo is None:
        raise ValueError("UTC time must have timezone information")
    return value.astimezone(get_timezone(timezone))
