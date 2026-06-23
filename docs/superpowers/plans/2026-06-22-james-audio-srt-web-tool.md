# James Audio & Srt Generator Web Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Gradio premium-dashboard MVP for `James Audio & Srt Generator`, focused on Myanmar transcript/text to MP3 + SRT with admin-controlled VIP/lifetime access.

**Architecture:** Add a separate `james_web_tool` package beside the existing desktop package. Keep the generation engine, database/auth, admin actions, and Gradio UI in separate focused modules. Use SQLite for user/job storage and Edge/Azure-style Myanmar voices for the first safe TTS provider.

**Tech Stack:** Python 3.10, Gradio, SQLite, edge-tts, PyAV/media duration helpers, pytest, existing `james_srt_studio` subtitle/text alignment utilities.

---

## File Structure

- Create `src/james_web_tool/__init__.py`
  - Package marker.
- Create `src/james_web_tool/config.py`
  - App name, logo path, output/database paths, admin default settings.
- Create `src/james_web_tool/models.py`
  - Dataclasses and constants for user plans, login results, generation results.
- Create `src/james_web_tool/database.py`
  - SQLite schema, connection helpers, user/job CRUD.
- Create `src/james_web_tool/auth.py`
  - PIN/password login, admin detection, plan expiry checks.
- Create `src/james_web_tool/tts.py`
  - Voice label mapping and MP3 generation wrapper.
- Create `src/james_web_tool/generator.py`
  - Text-to-MP3+SRT orchestration and job recording.
- Create `src/james_web_tool/admin.py`
  - Admin operations: create user, grant VIP/lifetime, revoke, disable, search.
- Create `src/james_web_tool/ui.py`
  - Gradio premium dashboard UI and event handlers.
- Create `run_james_audio_srt_web.py`
  - Local launcher.
- Create `tests/test_web_database.py`
  - Database schema and CRUD tests.
- Create `tests/test_web_auth.py`
  - Login and expiry tests.
- Create `tests/test_web_generator.py`
  - Generation path tests with fake TTS.
- Create `tests/test_web_admin.py`
  - Admin action tests.
- Modify `pyproject.toml`
  - Add `gradio` dependency.

---

### Task 1: Web Package Skeleton and Configuration

**Files:**
- Create: `src/james_web_tool/__init__.py`
- Create: `src/james_web_tool/config.py`
- Create: `src/james_web_tool/models.py`
- Test: `tests/test_web_config.py`

- [ ] **Step 1: Write the failing config/model test**

Create `tests/test_web_config.py`:

```python
from pathlib import Path

from james_web_tool.config import APP_NAME, default_data_dir, default_db_path, default_output_dir
from james_web_tool.models import PlanGrant, PlanTier, voice_display_options


def test_app_name_and_default_paths_are_stable(tmp_path, monkeypatch):
    monkeypatch.setenv("JAMES_WEB_DATA_DIR", str(tmp_path))

    assert APP_NAME == "James Audio & Srt Generator"
    assert default_data_dir() == tmp_path
    assert default_db_path() == tmp_path / "james_web_tool.sqlite3"
    assert default_output_dir() == tmp_path / "outputs"


def test_plan_grant_days_and_tiers():
    assert PlanGrant.ONE_MONTH.days == 30
    assert PlanGrant.THREE_MONTHS.tier == PlanTier.VIP
    assert PlanGrant.SIX_MONTHS.tier == PlanTier.VIP
    assert PlanGrant.ONE_YEAR.days == 365
    assert PlanGrant.LIFETIME.days is None


def test_voice_display_options_include_myanmar_defaults():
    options = voice_display_options()

    assert options["မြမြ"] == "my-MM-NilarNeural"
    assert options["အကိုလေး"] == "my-MM-ThihaNeural"
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
python -m pytest tests/test_web_config.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'james_web_tool'`.

- [ ] **Step 3: Create package marker**

Create `src/james_web_tool/__init__.py`:

```python
from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0"
```

- [ ] **Step 4: Create configuration module**

Create `src/james_web_tool/config.py`:

```python
from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "James Audio & Srt Generator"
DEFAULT_ADMIN_PIN = os.getenv("JAMES_WEB_ADMIN_PIN", "556945")


def default_data_dir() -> Path:
    configured = os.getenv("JAMES_WEB_DATA_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.cwd() / "web_data").resolve()


def default_db_path() -> Path:
    return default_data_dir() / "james_web_tool.sqlite3"


def default_output_dir() -> Path:
    return default_data_dir() / "outputs"
```

- [ ] **Step 5: Create model constants**

Create `src/james_web_tool/models.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class PlanTier(str, Enum):
    NONE = "NONE"
    VIP = "VIP"
    LIFETIME = "LIFETIME"
    LIFETIME = "LIFETIME"


class UserStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    EXPIRED = "expired"


@dataclass(frozen=True)
class PlanGrant:
    label: str
    days: int | None
    tier: PlanTier

    ONE_MONTH = None
    THREE_MONTHS = None
    SIX_MONTHS = None
    ONE_YEAR = None
    LIFETIME = None


PlanGrant.ONE_MONTH = PlanGrant("1 month", 30, PlanTier.VIP)
PlanGrant.THREE_MONTHS = PlanGrant("3 months", 90, PlanTier.VIP)
PlanGrant.SIX_MONTHS = PlanGrant("6 months", 180, PlanTier.VIP)
PlanGrant.ONE_YEAR = PlanGrant("1 year", 365, PlanTier.VIP)
PlanGrant.LIFETIME = PlanGrant("lifetime", None, PlanTier.LIFETIME)


@dataclass(frozen=True)
class LoginResult:
    ok: bool
    is_admin: bool
    user_id: str
    message: str
    plan_tier: PlanTier = PlanTier.NONE


@dataclass(frozen=True)
class GenerationResult:
    mp3_path: Path
    srt_path: Path
    message: str


def voice_display_options() -> dict[str, str]:
    return {
        "မြမြ": "my-MM-NilarNeural",
        "အကိုလေး": "my-MM-ThihaNeural",
        "နီလာ": "my-MM-NilarNeural",
        "သီဟ": "my-MM-ThihaNeural",
    }
```

- [ ] **Step 6: Run the test to verify it passes**

Run:

```powershell
python -m pytest tests/test_web_config.py -q
```

Expected: PASS.

- [ ] **Step 7: Checkpoint**

Run:

```powershell
git status --short
```

Expected in current workspace: `fatal: not a git repository...`. Record changed files manually in the handoff because this workspace is not initialized as a git repository.

---

### Task 2: SQLite Database Layer

**Files:**
- Create: `src/james_web_tool/database.py`
- Test: `tests/test_web_database.py`

- [ ] **Step 1: Write failing database tests**

Create `tests/test_web_database.py`:

```python
from datetime import datetime, timezone

from james_web_tool.database import (
    create_user,
    get_user_by_pin,
    init_db,
    list_users,
    record_job,
    search_users,
)
from james_web_tool.models import PlanTier


def test_create_and_find_user_by_pin(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    init_db(db_path)

    user = create_user(db_path, pin="123456", plan_tier=PlanTier.VIP, expires_at="2099-01-01T00:00:00+00:00")
    found = get_user_by_pin(db_path, "123456")

    assert found is not None
    assert found["user_id"] == user["user_id"]
    assert found["plan_tier"] == "VIP"
    assert found["status"] == "active"


def test_search_users_matches_user_id_and_pin(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    init_db(db_path)
    user = create_user(db_path, pin="654321", plan_tier=PlanTier.VIP, expires_at="2099-01-01T00:00:00+00:00")

    assert search_users(db_path, user["user_id"])[0]["pin"] == "654321"
    assert search_users(db_path, "654")[0]["user_id"] == user["user_id"]


def test_record_job_and_list_users(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    init_db(db_path)
    user = create_user(db_path, pin="222222", plan_tier=PlanTier.VIP, expires_at=None)

    record_job(
        db_path,
        user_id=user["user_id"],
        input_chars=42,
        voice_label="မြမြ",
        mp3_path="outputs/test.mp3",
        srt_path="outputs/test.srt",
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    rows = list_users(db_path)
    assert rows[0]["user_id"] == user["user_id"]
    assert rows[0]["job_count"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest tests/test_web_database.py -q
```

Expected: FAIL with `ModuleNotFoundError` or missing functions from `james_web_tool.database`.

- [ ] **Step 3: Implement database module**

Create `src/james_web_tool/database.py`:

```python
from __future__ import annotations

import sqlite3
import uuid
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


def search_users(db_path: Path, query: str) -> list[dict[str, Any]]:
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
```

- [ ] **Step 4: Run database tests**

Run:

```powershell
python -m pytest tests/test_web_database.py -q
```

Expected: PASS.

---

### Task 3: Authentication and Plan Expiry

**Files:**
- Create: `src/james_web_tool/auth.py`
- Test: `tests/test_web_auth.py`

- [ ] **Step 1: Write failing auth tests**

Create `tests/test_web_auth.py`:

```python
from datetime import datetime, timedelta, timezone

from james_web_tool.auth import login_with_pin, user_has_access
from james_web_tool.config import DEFAULT_ADMIN_PIN
from james_web_tool.database import create_user, init_db
from james_web_tool.models import PlanTier


def test_admin_pin_logs_in_as_admin(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    init_db(db_path)

    result = login_with_pin(db_path, DEFAULT_ADMIN_PIN)

    assert result.ok is True
    assert result.is_admin is True


def test_active_user_can_login(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    init_db(db_path)
    expires = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    create_user(db_path, pin="111111", plan_tier=PlanTier.VIP, expires_at=expires)

    result = login_with_pin(db_path, "111111")

    assert result.ok is True
    assert result.is_admin is False
    assert result.plan_tier == PlanTier.VIP


def test_expired_user_is_blocked(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    init_db(db_path)
    expired = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    user = create_user(db_path, pin="333333", plan_tier=PlanTier.VIP, expires_at=expired)

    assert user_has_access(user) is False
    assert login_with_pin(db_path, "333333").ok is False
```

- [ ] **Step 2: Run auth tests to verify they fail**

Run:

```powershell
python -m pytest tests/test_web_auth.py -q
```

Expected: FAIL with missing `james_web_tool.auth`.

- [ ] **Step 3: Implement auth module**

Create `src/james_web_tool/auth.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import DEFAULT_ADMIN_PIN
from .database import get_user_by_pin
from .models import LoginResult, PlanTier


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def user_has_access(user: dict[str, Any]) -> bool:
    if user.get("status") != "active":
        return False
    if user.get("plan_tier") == PlanTier.LIFETIME.value and user.get("expires_at") is None:
        return True
    expires = parse_datetime(user.get("expires_at"))
    if expires is None:
        return user.get("plan_tier") == PlanTier.LIFETIME.value
    return expires > datetime.now(timezone.utc)


def login_with_pin(db_path: Path, pin: str) -> LoginResult:
    clean_pin = pin.strip()
    if clean_pin == DEFAULT_ADMIN_PIN:
        return LoginResult(True, True, "ADMIN", "Admin login ok", PlanTier.LIFETIME)
    user = get_user_by_pin(db_path, clean_pin)
    if user is None:
        return LoginResult(False, False, "", "Wrong PIN")
    if not user_has_access(user):
        return LoginResult(False, False, user["user_id"], "Expired or disabled")
    return LoginResult(
        True,
        False,
        user["user_id"],
        "Login ok",
        PlanTier(user["plan_tier"]),
    )
```

- [ ] **Step 4: Run auth tests**

Run:

```powershell
python -m pytest tests/test_web_auth.py -q
```

Expected: PASS.

---

### Task 4: Admin Operations

**Files:**
- Create: `src/james_web_tool/admin.py`
- Test: `tests/test_web_admin.py`

- [ ] **Step 1: Write failing admin tests**

Create `tests/test_web_admin.py`:

```python
from james_web_tool.admin import create_paid_user, disable_user, grant_plan, revoke_user
from james_web_tool.database import get_user_by_id, init_db
from james_web_tool.models import PlanGrant, PlanTier


def test_create_paid_user_sets_plan_and_pin(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    init_db(db_path)

    user = create_paid_user(db_path, pin="444444", grant=PlanGrant.ONE_MONTH)

    assert user["pin"] == "444444"
    assert user["plan_tier"] == "VIP"
    assert user["expires_at"] is not None


def test_grant_lifetime_sets_no_expiry(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    init_db(db_path)
    user = create_paid_user(db_path, pin="555555", grant=PlanGrant.ONE_MONTH)

    updated = grant_plan(db_path, user["user_id"], PlanGrant.LIFETIME)

    assert updated["plan_tier"] == PlanTier.LIFETIME.value
    assert updated["expires_at"] is None


def test_revoke_and_disable_user(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    init_db(db_path)
    user = create_paid_user(db_path, pin="666666", grant=PlanGrant.THREE_MONTHS)

    revoked = revoke_user(db_path, user["user_id"])
    assert revoked["plan_tier"] == PlanTier.NONE.value

    disabled = disable_user(db_path, user["user_id"])
    assert disabled["status"] == "disabled"
    assert get_user_by_id(db_path, user["user_id"])["status"] == "disabled"
```

- [ ] **Step 2: Run test to verify failure**

Run:

```powershell
python -m pytest tests/test_web_admin.py -q
```

Expected: FAIL with missing `james_web_tool.admin`.

- [ ] **Step 3: Implement admin module**

Create `src/james_web_tool/admin.py`:

```python
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from .database import create_user, get_user_by_id, update_user
from .models import PlanGrant, PlanTier


def expiry_for_grant(grant: PlanGrant) -> str | None:
    if grant.days is None:
        return None
    return (datetime.now(timezone.utc) + timedelta(days=grant.days)).isoformat()


def create_paid_user(db_path: Path, pin: str, grant: PlanGrant) -> dict:
    return create_user(db_path, pin=pin, plan_tier=grant.tier, expires_at=expiry_for_grant(grant))


def grant_plan(db_path: Path, user_id: str, grant: PlanGrant) -> dict:
    update_user(
        db_path,
        user_id,
        plan_tier=grant.tier.value,
        expires_at=expiry_for_grant(grant),
        status="active",
    )
    user = get_user_by_id(db_path, user_id)
    assert user is not None
    return user


def revoke_user(db_path: Path, user_id: str) -> dict:
    update_user(db_path, user_id, plan_tier=PlanTier.NONE.value, expires_at=None)
    user = get_user_by_id(db_path, user_id)
    assert user is not None
    return user


def disable_user(db_path: Path, user_id: str) -> dict:
    update_user(db_path, user_id, status="disabled")
    user = get_user_by_id(db_path, user_id)
    assert user is not None
    return user
```

- [ ] **Step 4: Run admin tests**

Run:

```powershell
python -m pytest tests/test_web_admin.py -q
```

Expected: PASS.

---

### Task 5: TTS and Generation Engine

**Files:**
- Create: `src/james_web_tool/tts.py`
- Create: `src/james_web_tool/generator.py`
- Test: `tests/test_web_generator.py`

- [ ] **Step 1: Write failing generation tests with fake TTS**

Create `tests/test_web_generator.py`:

```python
from pathlib import Path

from james_web_tool.admin import create_paid_user
from james_web_tool.database import init_db, list_users
from james_web_tool.generator import generate_for_user
from james_web_tool.models import PlanGrant


def fake_tts(text: str, mp3_path: Path, voice_id: str) -> float:
    mp3_path.write_bytes(b"fake mp3")
    return 2.5


def test_generate_for_user_writes_mp3_srt_and_records_job(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    output_dir = tmp_path / "outputs"
    init_db(db_path)
    user = create_paid_user(db_path, pin="777777", grant=PlanGrant.ONE_MONTH)

    result = generate_for_user(
        db_path=db_path,
        output_dir=output_dir,
        user_id=user["user_id"],
        text="မင်္ဂလာပါ။ နေကောင်းလား။",
        voice_label="မြမြ",
        srt_format="2 Lines",
        file_name="test_output",
        tts_func=fake_tts,
    )

    assert result.mp3_path.exists()
    assert result.srt_path.exists()
    srt = result.srt_path.read_text(encoding="utf-8-sig")
    assert "00:00:00,000" in srt
    assert "မင်္ဂလာပါ။" in srt
    assert list_users(db_path)[0]["job_count"] == 1
```

- [ ] **Step 2: Run test to verify failure**

Run:

```powershell
python -m pytest tests/test_web_generator.py -q
```

Expected: FAIL with missing `james_web_tool.generator`.

- [ ] **Step 3: Implement TTS wrapper**

Create `src/james_web_tool/tts.py`:

```python
from __future__ import annotations

from pathlib import Path

from james_srt_studio.tts_generator import synthesize_and_measure

from .models import voice_display_options


def voice_id_for_label(label: str) -> str:
    voices = voice_display_options()
    if label not in voices:
        return voices["မြမြ"]
    return voices[label]


def generate_mp3(text: str, mp3_path: Path, voice_id: str) -> float:
    _path, duration = synthesize_and_measure(text=text, out_mp3=mp3_path, voice=voice_id)
    return duration
```

- [ ] **Step 4: Implement generation orchestration**

Create `src/james_web_tool/generator.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from james_srt_studio.subtitle_formatter import build_srt
from james_srt_studio.text_aligner import align_text_to_duration

from .database import get_user_by_id, record_job
from .models import GenerationResult
from .tts import generate_mp3, voice_id_for_label

TtsFunc = Callable[[str, Path, str], float]


def safe_file_stem(file_name: str) -> str:
    allowed = "".join(ch for ch in file_name.strip() if ch.isalnum() or ch in (" ", "-", "_"))
    return allowed.strip() or "james_output"


def generate_for_user(
    db_path: Path,
    output_dir: Path,
    user_id: str,
    text: str,
    voice_label: str,
    srt_format: str,
    file_name: str,
    tts_func: TtsFunc = generate_mp3,
) -> GenerationResult:
    clean_text = text.strip()
    if not clean_text:
        raise ValueError("Text is empty.")
    user = get_user_by_id(db_path, user_id)
    if user is None:
        raise ValueError("User not found.")

    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    stem = f"{safe_file_stem(file_name)}_{stamp}"
    mp3_path = output_dir / f"{stem}.mp3"
    srt_path = output_dir / f"{stem}.srt"

    voice_id = voice_id_for_label(voice_label)
    duration = tts_func(clean_text, mp3_path, voice_id)
    max_chars = 42 if srt_format == "2 Lines" else 25
    segments = align_text_to_duration(clean_text, duration=duration, max_chars=max_chars)
    srt_path.write_text(build_srt(segments, max_chars=80), encoding="utf-8-sig")

    record_job(
        db_path,
        user_id=user_id,
        input_chars=len(clean_text),
        voice_label=voice_label,
        mp3_path=str(mp3_path),
        srt_path=str(srt_path),
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    return GenerationResult(mp3_path=mp3_path, srt_path=srt_path, message="Generated MP3 and SRT.")
```

- [ ] **Step 5: Run generation tests**

Run:

```powershell
python -m pytest tests/test_web_generator.py -q
```

Expected: PASS.

---

### Task 6: Gradio Dependency and Launcher

**Files:**
- Modify: `pyproject.toml`
- Create: `run_james_audio_srt_web.py`
- Create: `src/james_web_tool/ui.py`
- Test: `tests/test_web_ui_smoke.py`

- [ ] **Step 1: Add Gradio dependency test**

Create `tests/test_web_ui_smoke.py`:

```python
from james_web_tool.ui import build_app


def test_build_app_returns_gradio_blocks(tmp_path, monkeypatch):
    monkeypatch.setenv("JAMES_WEB_DATA_DIR", str(tmp_path))

    app = build_app()

    assert app is not None
    assert app.__class__.__name__ == "Blocks"
```

- [ ] **Step 2: Modify dependencies**

Modify `pyproject.toml` dependencies to include:

```toml
  "gradio>=4.44.1",
```

- [ ] **Step 3: Implement Gradio UI**

Create `src/james_web_tool/ui.py`:

```python
from __future__ import annotations

import gradio as gr

from .admin import create_paid_user, disable_user, grant_plan, revoke_user
from .auth import login_with_pin
from .config import APP_NAME, default_db_path, default_output_dir
from .database import init_db, list_users, search_users
from .generator import generate_for_user
from .models import PlanGrant, voice_display_options

CSS = """
.gradio-container { background: #050508 !important; color: #f7f2ff !important; }
.james-hero { padding: 18px; border-radius: 20px; background: linear-gradient(135deg,#090913,#120a22); border: 1px solid rgba(255,209,41,.25); }
.james-title { color: #ffd129; font-size: 30px; font-weight: 900; }
.james-subtitle { color: #cfc8ff; }
button.primary { background: linear-gradient(90deg,#ffd129,#7b43ff) !important; color: #050505 !important; }
"""


def _users_table(rows: list[dict]) -> list[list[str]]:
    return [
        [
            row["user_id"],
            row["pin"],
            row["plan_tier"],
            row["expires_at"] or "lifetime/none",
            row["status"],
            str(row.get("job_count", 0)),
        ]
        for row in rows
    ]


def build_app() -> gr.Blocks:
    db_path = default_db_path()
    output_dir = default_output_dir()
    init_db(db_path)

    with gr.Blocks(css=CSS, title=APP_NAME) as app:
        session_user_id = gr.State("")
        session_is_admin = gr.State(False)

        gr.HTML(
            f"""
            <div class='james-hero'>
              <div class='james-title'>{APP_NAME}</div>
              <div class='james-subtitle'>Myanmar transcript ကို MP3 အသံ + SRT subtitle အဖြစ်ထုတ်ပေးမယ်</div>
            </div>
            """
        )

        with gr.Tab("Login"):
            pin = gr.Textbox(label="PIN / Admin Password", type="password")
            login_btn = gr.Button("🚀 Login", variant="primary")
            login_status = gr.Markdown("Login ဝင်ရန် PIN ထည့်ပါ။")

        with gr.Tab("Generator"):
            current_user = gr.Markdown("Not logged in")
            transcript = gr.Textbox(label="Myanmar Transcript", lines=12)
            with gr.Row():
                voice = gr.Dropdown(choices=list(voice_display_options().keys()), value="မြမြ", label="Voice")
                srt_format = gr.Radio(choices=["Single Line", "2 Lines"], value="2 Lines", label="SRT Format")
                file_name = gr.Textbox(value="james_output", label="File Name")
            generate_btn = gr.Button("Generate MP3 & SRT", variant="primary")
            generate_status = gr.Markdown("")
            audio_out = gr.Audio(label="Output Audio")
            mp3_file = gr.File(label="MP3 Download")
            srt_file = gr.File(label="SRT Download")

        with gr.Tab("Admin"):
            admin_status = gr.Markdown("Admin login required.")
            with gr.Row():
                new_pin = gr.Textbox(label="New User PIN")
                plan = gr.Dropdown(
                    choices=["1 month", "3 months", "6 months", "1 year", "lifetime"],
                    value="1 month",
                    label="Plan",
                )
                create_btn = gr.Button("Create / Grant User", variant="primary")
            search = gr.Textbox(label="Search User ID or PIN")
            refresh_btn = gr.Button("Refresh Users")
            users = gr.Dataframe(headers=["User ID", "PIN", "Plan", "Expires", "Status", "Jobs"], datatype=["str"] * 6)
            selected_user_id = gr.Textbox(label="Target User ID")
            with gr.Row():
                grant_1m = gr.Button("Grant 1M VIP")
                grant_3m = gr.Button("Grant 3M VIP")
                grant_6m = gr.Button("Grant 6M VIP")
                grant_1y = gr.Button("Grant 1Y VIP")
                grant_life = gr.Button("Grant Lifetime")
            with gr.Row():
                revoke_btn = gr.Button("Revoke")
                disable_btn = gr.Button("Disable")

        def do_login(pin_value: str):
            result = login_with_pin(db_path, pin_value)
            if not result.ok:
                return result.message, "", False, "Not logged in", "Admin login required.", []
            admin_text = "Admin panel ready." if result.is_admin else "Admin login required."
            user_text = f"Logged in: {result.user_id} • {result.plan_tier.value}"
            return result.message, result.user_id, result.is_admin, user_text, admin_text, _users_table(list_users(db_path))

        login_btn.click(
            do_login,
            inputs=[pin],
            outputs=[login_status, session_user_id, session_is_admin, current_user, admin_status, users],
        )

        def do_generate(user_id: str, text: str, voice_label: str, fmt: str, name: str):
            if not user_id or user_id == "ADMIN":
                raise gr.Error("User login required.")
            result = generate_for_user(db_path, output_dir, user_id, text, voice_label, fmt, name)
            return result.message, str(result.mp3_path), str(result.mp3_path), str(result.srt_path)

        generate_btn.click(
            do_generate,
            inputs=[session_user_id, transcript, voice, srt_format, file_name],
            outputs=[generate_status, audio_out, mp3_file, srt_file],
        )

        grant_map = {
            "1 month": PlanGrant.ONE_MONTH,
            "3 months": PlanGrant.THREE_MONTHS,
            "6 months": PlanGrant.SIX_MONTHS,
            "1 year": PlanGrant.ONE_YEAR,
            "lifetime": PlanGrant.LIFETIME,
        }

        def require_admin(is_admin: bool):
            if not is_admin:
                raise gr.Error("Admin login required.")

        def do_create(is_admin: bool, pin_value: str, plan_label: str):
            require_admin(is_admin)
            create_paid_user(db_path, pin_value.strip(), grant_map[plan_label])
            return _users_table(list_users(db_path)), "User created."

        create_btn.click(do_create, inputs=[session_is_admin, new_pin, plan], outputs=[users, admin_status])

        def do_search(is_admin: bool, query: str):
            require_admin(is_admin)
            rows = search_users(db_path, query) if query.strip() else list_users(db_path)
            return _users_table(rows)

        refresh_btn.click(do_search, inputs=[session_is_admin, search], outputs=[users])

        def grant_action(is_admin: bool, user_id: str, grant: PlanGrant):
            require_admin(is_admin)
            grant_plan(db_path, user_id.strip(), grant)
            return _users_table(list_users(db_path)), f"Updated {user_id}"

        grant_1m.click(lambda a, u: grant_action(a, u, PlanGrant.ONE_MONTH), [session_is_admin, selected_user_id], [users, admin_status])
        grant_3m.click(lambda a, u: grant_action(a, u, PlanGrant.THREE_MONTHS), [session_is_admin, selected_user_id], [users, admin_status])
        grant_6m.click(lambda a, u: grant_action(a, u, PlanGrant.SIX_MONTHS), [session_is_admin, selected_user_id], [users, admin_status])
        grant_1y.click(lambda a, u: grant_action(a, u, PlanGrant.ONE_YEAR), [session_is_admin, selected_user_id], [users, admin_status])
        grant_life.click(lambda a, u: grant_action(a, u, PlanGrant.LIFETIME), [session_is_admin, selected_user_id], [users, admin_status])

        def do_revoke(is_admin: bool, user_id: str):
            require_admin(is_admin)
            revoke_user(db_path, user_id.strip())
            return _users_table(list_users(db_path)), f"Revoked {user_id}"

        def do_disable(is_admin: bool, user_id: str):
            require_admin(is_admin)
            disable_user(db_path, user_id.strip())
            return _users_table(list_users(db_path)), f"Disabled {user_id}"

        revoke_btn.click(do_revoke, [session_is_admin, selected_user_id], [users, admin_status])
        disable_btn.click(do_disable, [session_is_admin, selected_user_id], [users, admin_status])

    return app


def main() -> None:
    build_app().queue().launch()
```

- [ ] **Step 4: Create launcher**

Create `run_james_audio_srt_web.py`:

```python
from __future__ import annotations

from james_web_tool.ui import main


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run UI smoke test**

Run:

```powershell
python -m pytest tests/test_web_ui_smoke.py -q
```

Expected: PASS.

---

### Task 7: Full Verification and Local Launch

**Files:**
- Modify only if verification exposes failures.

- [ ] **Step 1: Run all tests**

Run:

```powershell
python -m pytest tests -q
```

Expected: all tests pass, including existing desktop tests and new web tests.

- [ ] **Step 2: Launch local web app**

Run:

```powershell
python run_james_audio_srt_web.py
```

Expected: terminal prints a Gradio local URL such as `http://127.0.0.1:7860`.

- [ ] **Step 3: Manual admin test**

In browser:

1. Open the Gradio URL.
2. Login with admin PIN `556945`.
3. Create user with PIN `123456`, plan `1 month`.
4. Confirm user appears with plan `VIP`.

Expected: user table shows the created user.

- [ ] **Step 4: Manual user generation test**

In browser:

1. Login with user PIN `123456`.
2. Paste `မင်္ဂလာပါ။ နေကောင်းလား။`
3. Select voice `မြမြ`.
4. Select SRT format `2 Lines`.
5. Set file name `sample`.
6. Click `Generate MP3 & SRT`.

Expected:

- MP3 file download appears.
- SRT file download appears.
- SRT contains `00:00:00,000`.
- SRT contains Myanmar text.

- [ ] **Step 5: Stop the server**

Press `Ctrl+C` in the terminal running Gradio.

Expected: server exits cleanly.

---

## Self-Review Checklist

- Spec coverage:
  - Premium dashboard: Task 6 UI/CSS.
  - VIP/lifetime plans: Tasks 1, 3, 4, 6.
  - Admin panel: Tasks 4 and 6.
  - Myanmar transcript to MP3 + SRT: Task 5.
  - SQLite storage: Task 2.
  - Safe non-scraping TTS provider: Task 5.
  - Testing and local launch: Task 7.
- Placeholder scan:
  - No unfinished placeholder markers.
  - No deferred implementation notes.
  - No undefined planned modules without a task.
- Type consistency:
  - `PlanGrant`, `PlanTier`, `LoginResult`, `GenerationResult` are introduced before use.
  - `db_path`, `output_dir`, `user_id`, `voice_label`, and `srt_format` names are consistent across database, generator, and UI tasks.
