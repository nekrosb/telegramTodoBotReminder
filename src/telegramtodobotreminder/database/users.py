from datetime import UTC, datetime

import aiosqlite


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


async def get_by_telegram_id(
    connection: aiosqlite.Connection, telegram_id: int
) -> aiosqlite.Row | None:
    connection.row_factory = aiosqlite.Row
    cursor = await connection.execute(
        "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
    )
    return await cursor.fetchone()


async def create(
    connection: aiosqlite.Connection, telegram_id: int, language: str
) -> None:
    now = _utc_now()
    await connection.execute(
        """
        INSERT INTO users (telegram_id, language, timezone, created_at, updated_at)
        VALUES (?, ?, 'UTC', ?, ?)
        """,
        (telegram_id, language, now, now),
    )
    await connection.commit()


async def update_language(
    connection: aiosqlite.Connection, telegram_id: int, language: str
) -> None:
    await connection.execute(
        """
        UPDATE users
        SET language = ?, updated_at = ?
        WHERE telegram_id = ?
        """,
        (language, _utc_now(), telegram_id),
    )
    await connection.commit()


async def update_timezone(
    connection: aiosqlite.Connection, telegram_id: int, timezone: str
) -> None:
    await connection.execute(
        """
        UPDATE users
        SET timezone = ?, updated_at = ?
        WHERE telegram_id = ?
        """,
        (timezone, _utc_now(), telegram_id),
    )
    await connection.commit()
