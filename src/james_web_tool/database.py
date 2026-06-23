from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import PlanTier


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path) -> None:
    with connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                pin TEXT NOT NULL UNIQUE,
                plan_tier TEXT NOT NULL,
                expires_at TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                input_chars INTEGER NOT NULL,
                voice_label TEXT NOT NULL,
                mp3_path TEXT NOT NULL,
                srt_path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
            """
        )


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def create_user(db_path: Path, pin: str, plan_tier: PlanTier, expires_at: str | None) -> dict[str, Any]:
    user_id = f"J-{uuid.uuid4().hex[:6].upper()}"
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO users (user_id, pin, plan_tier, expires_at, status)
            VALUES (?, ?, ?, ?, 'active')
            """,
            (user_id, pin, plan_tier.value, expires_at),
        )
    user = get_user_by_pin(db_path, pin)
    assert user is not None
    return user


def get_user_by_pin(db_path: Path, pin: str) -> dict[str, Any] | None:
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM users WHERE pin = ?", (pin,)).fetchone()
    return row_to_dict(row)


def get_user_by_id(db_path: Path, user_id: str) -> dict[str, Any] | None:
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    return row_to_dict(row)


def expire_due_users(db_path: Path, now: datetime | None = None) -> int:
    current = now or datetime.now(timezone.utc)
    with connect(db_path) as conn:
        cursor = conn.execute(
            """
            UPDATE users
            SET status = 'expired', updated_at = CURRENT_TIMESTAMP
            WHERE status = 'active'
              AND expires_at IS NOT NULL
              AND expires_at <= ?
            """,
            (current.isoformat(),),
        )
        return cursor.rowcount


def search_users(db_path: Path, query: str) -> list[dict[str, Any]]:
    expire_due_users(db_path)
    like = f"%{query.strip()}%"
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM users
            WHERE user_id LIKE ? OR pin LIKE ?
            ORDER BY created_at DESC
            """,
            (like, like),
        ).fetchall()
    return [dict(row) for row in rows]


def list_users(db_path: Path) -> list[dict[str, Any]]:
    expire_due_users(db_path)
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT users.*, COUNT(jobs.job_id) AS job_count
            FROM users
            LEFT JOIN jobs ON jobs.user_id = users.user_id
            GROUP BY users.user_id
            ORDER BY users.created_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def update_user(db_path: Path, user_id: str, **fields: str | None) -> None:
    allowed = {"pin", "plan_tier", "expires_at", "status"}
    updates = {key: value for key, value in fields.items() if key in allowed}
    if not updates:
        return
    set_clause = ", ".join(f"{key} = ?" for key in updates)
    values = list(updates.values()) + [user_id]
    with connect(db_path) as conn:
        conn.execute(
            f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            values,
        )


def delete_user_by_id(db_path: Path, user_id: str) -> None:
    with connect(db_path) as conn:
        conn.execute("DELETE FROM jobs WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))


def record_job(
    db_path: Path,
    user_id: str,
    input_chars: int,
    voice_label: str,
    mp3_path: str,
    srt_path: str,
    created_at: str,
) -> dict[str, Any]:
    job_id = f"JOB-{uuid.uuid4().hex[:8].upper()}"
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO jobs (job_id, user_id, input_chars, voice_label, mp3_path, srt_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (job_id, user_id, input_chars, voice_label, mp3_path, srt_path, created_at),
        )
        row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    result = row_to_dict(row)
    assert result is not None
    return result
