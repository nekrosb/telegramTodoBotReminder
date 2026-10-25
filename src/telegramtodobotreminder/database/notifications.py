from datetime import UTC, datetime, timedelta

import aiosqlite

NOTIFICATION_DELAYS = {
    "1d": 86400,
    "3h": 10800,
    "1h": 3600,
    "15m": 900,
}


def _now() -> datetime:
    return datetime.now(UTC)


async def create_for_reminder(
    connection: aiosqlite.Connection, reminder_id: int, remind_at: datetime, options: dict[str, bool]
) -> None:
    now = _now()
    event_time = remind_at.astimezone(UTC)
    for notification_type, delay in NOTIFICATION_DELAYS.items():
        if not options.get(notification_type, False):
            continue
        if notification_type == "1d" and event_time - now <= timedelta(days=2):
            continue
        scheduled_at = event_time - timedelta(seconds=delay)
        if scheduled_at <= now:
            continue
        await connection.execute(
            """
            INSERT OR IGNORE INTO reminder_notifications
                (reminder_id, notification_type, scheduled_at, status, created_at)
            VALUES (?, ?, ?, 'pending', ?)
            """,
            (reminder_id, notification_type, scheduled_at.isoformat(), now.isoformat()),
        )
    await connection.commit()


async def rebuild_for_reminder(
    connection: aiosqlite.Connection, reminder_id: int, remind_at: datetime
) -> None:
    await connection.execute(
        """
        DELETE FROM reminder_notifications
        WHERE reminder_id = ? AND status = 'pending'
        """,
        (reminder_id,),
    )
    cursor = await connection.execute(
        """
        SELECT notify_1d, notify_3h, notify_1h, notify_15m
        FROM reminders
        WHERE id = ?
        """,
        (reminder_id,),
    )
    options = await cursor.fetchone()
    if options is None:
        await connection.commit()
        return
    await connection.commit()
    await create_for_reminder(
        connection,
        reminder_id,
        remind_at,
        {
            "1d": bool(options[0]),
            "3h": bool(options[1]),
            "1h": bool(options[2]),
            "15m": bool(options[3]),
        },
    )


async def pending_future(
    connection: aiosqlite.Connection,
) -> list[aiosqlite.Row]:
    connection.row_factory = aiosqlite.Row
    cursor = await connection.execute(
        """
        SELECT n.*, r.title, r.remind_at, u.telegram_id, u.language, u.timezone
        FROM reminder_notifications n
        JOIN reminders r ON r.id = n.reminder_id
        JOIN users u ON u.id = r.user_id
        WHERE n.status = 'pending'
          AND r.status = 'scheduled'
          AND n.scheduled_at > ?
        """,
        (_now().isoformat(),),
    )
    return await cursor.fetchall()


async def claim(
    connection: aiosqlite.Connection, notification_id: int
) -> aiosqlite.Row | None:
    await connection.execute(
        """
        UPDATE reminder_notifications
        SET status = 'processing', attempt_count = attempt_count + 1
        WHERE id = ? AND status = 'pending'
        """,
        (notification_id,),
    )
    await connection.commit()
    connection.row_factory = aiosqlite.Row
    cursor = await connection.execute(
        """
        SELECT n.*, r.title, r.remind_at, u.telegram_id, u.language, u.timezone
        FROM reminder_notifications n
        JOIN reminders r ON r.id = n.reminder_id
        JOIN users u ON u.id = r.user_id
        WHERE n.id = ? AND n.status = 'processing'
        """,
        (notification_id,),
    )
    return await cursor.fetchone()


async def mark_sent(connection: aiosqlite.Connection, notification_id: int) -> None:
    await connection.execute(
        "UPDATE reminder_notifications SET status = 'sent', sent_at = ? WHERE id = ?",
        (_now().isoformat(), notification_id),
    )
    await connection.commit()


async def mark_failed(
    connection: aiosqlite.Connection, notification_id: int, error: str
) -> None:
    await connection.execute(
        """
        UPDATE reminder_notifications
        SET status = 'failed', last_error = ?
        WHERE id = ?
        """,
        (error[:500], notification_id),
    )
    await connection.commit()
