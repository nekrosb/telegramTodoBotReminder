from datetime import UTC, datetime

import aiosqlite

from telegramtodobotreminder.database.notifications import (
    create_for_reminder,
    rebuild_for_reminder,
)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


async def create(
    connection: aiosqlite.Connection,
    telegram_id: int,
    title: str,
    remind_at: datetime,
    notify_1d: bool = True,
    notify_3h: bool = True,
    notify_1h: bool = True,
    notify_15m: bool = True,
) -> int:
    if not title.strip():
        raise ValueError("Reminder title cannot be empty")

    user_cursor = await connection.execute(
        "SELECT id, push_notifications FROM users WHERE telegram_id = ?",
        (telegram_id,),
    )
    user = await user_cursor.fetchone()
    if user is None:
        raise ValueError("Cannot create a reminder for an unregistered user")
    push_enabled = bool(user[1])

    now = _utc_now()
    cursor = await connection.execute(
        """
        INSERT INTO reminders
            (user_id, title, remind_at, status, created_at, updated_at,
             notify_1d, notify_3h, notify_1h, notify_15m)
        VALUES (?, ?, ?, 'scheduled', ?, ?, ?, ?, ?, ?)
        """,
        (
            user[0],
            title,
            remind_at.astimezone(UTC).isoformat(),
            now,
            now,
            notify_1d and push_enabled,
            notify_3h and push_enabled,
            notify_1h and push_enabled,
            notify_15m and push_enabled,
        ),
    )
    await connection.commit()
    await create_for_reminder(
        connection,
        cursor.lastrowid,
        remind_at,
        {
            "1d": notify_1d and push_enabled,
            "3h": notify_3h and push_enabled,
            "1h": notify_1h and push_enabled,
            "15m": notify_15m and push_enabled,
        },
    )
    return cursor.lastrowid


async def list_for_user(
    connection: aiosqlite.Connection, telegram_id: int
) -> list[aiosqlite.Row]:
    connection.row_factory = aiosqlite.Row
    cursor = await connection.execute(
        """
        SELECT reminders.*
        FROM reminders
        JOIN users ON users.id = reminders.user_id
        WHERE users.telegram_id = ?
        ORDER BY reminders.remind_at
        """,
        (telegram_id,),
    )
    return await cursor.fetchall()


async def get_for_user(
    connection: aiosqlite.Connection, telegram_id: int, reminder_id: int
) -> aiosqlite.Row | None:
    connection.row_factory = aiosqlite.Row
    cursor = await connection.execute(
        """
        SELECT reminders.*
        FROM reminders
        JOIN users ON users.id = reminders.user_id
        WHERE users.telegram_id = ? AND reminders.id = ?
        """,
        (telegram_id, reminder_id),
    )
    return await cursor.fetchone()


async def update_for_user(
    connection: aiosqlite.Connection,
    telegram_id: int,
    reminder_id: int,
    title: str,
    remind_at: datetime,
) -> bool:
    if not title.strip():
        raise ValueError("Reminder title cannot be empty")

    cursor = await connection.execute(
        """
        UPDATE reminders
        SET title = ?, remind_at = ?, updated_at = ?
        WHERE id = ? AND user_id = (
            SELECT id FROM users WHERE telegram_id = ?
        )
        """,
        (title, remind_at.astimezone(UTC).isoformat(), _utc_now(), reminder_id, telegram_id),
    )
    await connection.commit()
    updated = cursor.rowcount == 1
    if updated:
        await rebuild_for_reminder(connection, reminder_id, remind_at)
    return updated


async def delete_for_user(
    connection: aiosqlite.Connection, telegram_id: int, reminder_id: int
) -> bool:
    cursor = await connection.execute(
        """
        DELETE FROM reminders
        WHERE id = ? AND user_id = (
            SELECT id FROM users WHERE telegram_id = ?
        )
        """,
        (reminder_id, telegram_id),
    )
    await connection.commit()
    return cursor.rowcount == 1
