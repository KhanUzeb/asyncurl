"""SQLite persistence for check results, via aiosqlite so writes don't block the loop."""

import aiosqlite

from .models import CheckResult

DB_PATH = "health_checks.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    status TEXT NOT NULL,
    latency_ms REAL,
    ok INTEGER NOT NULL,
    error TEXT,
    checked_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_checks_url ON checks(url);
"""


async def init_db(db_path: str = DB_PATH) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.executescript(SCHEMA)
        await db.commit()


async def save_results(results: list[CheckResult], db_path: str = DB_PATH) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.executemany(
            """INSERT INTO checks (url, status, latency_ms, ok, error, checked_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
            [
                (r.url, str(r.status), r.latency_ms, int(r.ok), r.error, r.checked_at)
                for r in results
            ],
        )
        await db.commit()


async def latest_results(db_path: str = DB_PATH) -> list[dict]:
    """Most recent check per URL, useful for a dashboard's current-status view."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT c.* FROM checks c
            INNER JOIN (
                SELECT url, MAX(id) AS max_id FROM checks GROUP BY url
            ) latest ON c.url = latest.url AND c.id = latest.max_id
            ORDER BY c.url
            """
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def history(url: str, limit: int = 50, db_path: str = DB_PATH) -> list[dict]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM checks WHERE url = ? ORDER BY id DESC LIMIT ?",
            (url, limit),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
