from datetime import UTC, datetime

import aiosqlite


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


async def create(
    connection: aiosqlite.Connection,
    telegram_id: int,
    title: str,
    remind_at: datetime,
) -> int:
    if not title.strip():
        raise ValueError("Reminder title cannot be empty")

    user_cursor = await connection.execute(
        "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
    )
    user = await user_cursor.fetchone()
    if user is None:
        raise ValueError("Cannot create a reminder for an unregistered user")

    now = _utc_now()
    cursor = await connection.execute(
        """
        INSERT INTO reminders
            (user_id, title, remind_at, status, created_at, updated_at)
        VALUES (?, ?, ?, 'scheduled', ?, ?)
        """,
        (user[0], title, remind_at.astimezone(UTC).isoformat(), now, now),
    )
    await connection.commit()
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
