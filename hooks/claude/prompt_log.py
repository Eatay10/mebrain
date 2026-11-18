#!/usr/bin/env python3
"""UserPromptSubmit: girilen prompt'u history/YYYY-MM-DD.jsonl'e kaydeder (secret'lar redakte)."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import ROOT, STATE, active_task, append_jsonl, now, read_event, redact  # noqa: E402


def main() -> None:
    ev = read_event()
    prompt = redact(ev.get("prompt", ""))
    sid = ev.get("session_id", "")
    rec = {
        "ts": now(),
        "kind": "prompt",
        "session": sid[:8],
        "task": active_task(),
        "prompt": prompt[:1000],
        "prompt_chars": len(prompt),
        "sha": hashlib.sha256(prompt.encode()).hexdigest()[:12],
    }
    append_jsonl(ROOT / "history" / f"{rec['ts'][:10]}.jsonl", rec)
    (STATE / f"last-prompt-{sid[:8]}").write_text(rec["sha"])


if __name__ == "__main__":
    main()
