from datetime import datetime

import pytest

from telegramtodobotreminder.timezones import (
    AmbiguousLocalTimeError,
    InvalidTimezoneError,
    NonexistentLocalTimeError,
    local_to_utc,
    utc_to_local,
)


def test_local_time_is_converted_to_utc():
    local = datetime(2026, 1, 15, 12, 0)

    result = local_to_utc(local, "Europe/Berlin")

    assert result.isoformat() == "2026-01-15T11:00:00+00:00"


def test_utc_time_is_converted_to_local():
    from datetime import UTC

    utc = datetime(2026, 7, 1, 10, 0, tzinfo=UTC)

    result = utc_to_local(utc, "Europe/Berlin")

    assert result.isoformat() == "2026-07-01T12:00:00+02:00"


def test_nonexistent_dst_time_is_rejected():
    with pytest.raises(NonexistentLocalTimeError):
        local_to_utc(datetime(2026, 3, 29, 2, 30), "Europe/Berlin")


def test_ambiguous_dst_time_is_rejected():
    with pytest.raises(AmbiguousLocalTimeError):
        local_to_utc(datetime(2026, 10, 25, 2, 30), "Europe/Berlin")


def test_unknown_timezone_is_rejected():
    with pytest.raises(InvalidTimezoneError):
        local_to_utc(datetime(2026, 1, 1, 12, 0), "Not/A_Timezone")
