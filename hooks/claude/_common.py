"""Hook'ların ortak yardımcıları. Sadece standart kütüphane."""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).resolve().parents[2]))
STATE = ROOT / ".claude" / "state"
STATE.mkdir(parents=True, exist_ok=True)

SECRET_PATTERNS = [
    re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),            # GitHub token
    re.compile(r"github_pat_[A-Za-z0-9_]{40,}"),
    re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),             # Anthropic key
    re.compile(r"AKIA[0-9A-Z]{16}"),                      # AWS access key
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"cth_[a-z0-9]{8}_[A-Za-z0-9]{20,}"),      # uygulamanın kendi API token'ı
    re.compile(r"(?i)(password|passwd|secret|api[_-]?key)\s*[:=]\s*['\"][^'\"\s]{8,}['\"]"),
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_event() -> dict:
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def redact(text: str) -> str:
    for p in SECRET_PATTERNS:
        text = p.sub("[REDACTED]", text)
    return text


def has_secret(text: str) -> bool:
    return any(p.search(text) for p in SECRET_PATTERNS)


def active_task() -> str | None:
    f = STATE / "active-task"
    return f.read_text().strip() or None if f.exists() else None


def task_owned_paths(task_id: str) -> list[str]:
    """TASK frontmatter'ındaki owned_paths listesini okur (yaml bağımlılığı olmadan)."""
    f = ROOT / "tasks" / f"{task_id}.md"
    if not f.exists():
        return []
    paths, inside = [], False
    for line in f.read_text().splitlines():
        if line.startswith("owned_paths:"):
            inside = True
            continue
        if inside:
            m = re.match(r"\s+-\s+(.+)", line)
            if m:
                paths.append(m.group(1).strip())
            elif line and not line.startswith(" "):
                break
    return paths


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def block(reason: str) -> None:
    """Exit code 2: Claude Code işlemi engeller ve stderr'i ajana geri verir."""
    print(reason, file=sys.stderr)
    sys.exit(2)
