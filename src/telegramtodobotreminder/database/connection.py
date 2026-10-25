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
    await connection.commit()
