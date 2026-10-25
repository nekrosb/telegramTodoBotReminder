from telegramtodobotreminder.handlers import _format_local_event


def test_event_display_uses_user_timezone_without_utc_suffix():
    assert _format_local_event(
        "2026-10-26T05:30:00+00:00", "Europe/Zurich"
    ) == "26.10.2026 06:30 (Europe/Zurich)"
