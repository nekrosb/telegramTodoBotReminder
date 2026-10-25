from pathlib import Path

import aiosqlite


async def connect(database_path: str | Path) -> aiosqlite.Connection:
    """Open a SQLite connection and enable foreign key enforcement."""
    database = Path(database_path)
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = await aiosqlite.connect(database)
    await connection.execute("PRAGMA foreign_keys = ON")
    await connection.execute("PRAGMA journal_mode = WAL")
    await connection.commit()
    return connection


async def initialize(connection: aiosqlite.Connection) -> None:
    """Create the current database schema if it does not exist."""
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL UNIQUE,
            language TEXT NOT NULL CHECK (language IN ('ru', 'en')),
            timezone TEXT NOT NULL DEFAULT 'UTC',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL CHECK (length(trim(title)) > 0),
            remind_at TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('scheduled', 'completed', 'cancelled')),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    for column in (
        "notify_3h INTEGER NOT NULL DEFAULT 1",
        "notify_1h INTEGER NOT NULL DEFAULT 1",
        "notify_15m INTEGER NOT NULL DEFAULT 1",
        "notify_1d INTEGER NOT NULL DEFAULT 1",
    ):
        name = column.split()[0]
        cursor = await connection.execute("PRAGMA table_info(reminders)")
        columns = {row[1] for row in await cursor.fetchall()}
        if name not in columns:
            await connection.execute(f"ALTER TABLE reminders ADD COLUMN {column}")
    cursor = await connection.execute("PRAGMA table_info(users)")
    user_columns = {row[1] for row in await cursor.fetchall()}
    if "push_notifications" not in user_columns:
        await connection.execute(
            "ALTER TABLE users ADD COLUMN push_notifications INTEGER NOT NULL DEFAULT 1"
        )
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reminder_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reminder_id INTEGER NOT NULL REFERENCES reminders(id) ON DELETE CASCADE,
            notification_type TEXT NOT NULL CHECK (
                notification_type IN ('1d', '3h', '1h', '15m')
            ),
            scheduled_at TEXT NOT NULL,
            status TEXT NOT NULL CHECK (
                status IN ('pending', 'processing', 'sent', 'failed', 'cancelled')
            ),
            sent_at TEXT,
            attempt_count INTEGER NOT NULL DEFAULT 0,
            last_error TEXT,
            created_at TEXT NOT NULL,
            UNIQUE (reminder_id, notification_type)
        )
        """
    )
    await connection.commit()
