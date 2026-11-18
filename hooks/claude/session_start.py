#!/usr/bin/env python3
"""SessionStart: oturuma dinamik bağlam enjekte eder (stdout → ajanın bağlamına eklenir).

Statik bağlam CLAUDE.md + rules/ ile gelir; bu hook değişen durumu ekler:
aktif TASK, panodaki açık işler, son 5 history kaydı.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import ROOT, active_task  # noqa: E402


def main() -> None:
    out = ["## Oturum bağlamı (hooks/claude/session_start.py)"]
    task = active_task()
    out.append(f"- Aktif TASK: **{task}** → `tasks/{task}.md` dosyasını oku." if task else "- Aktif TASK yok. İşe başlamadan `/implement-task TASK-NNN` kullan.")

    board = ROOT / "tasks" / "BOARD.md"
    if board.exists():
        rows = [l for l in board.read_text().splitlines() if re.match(r"\| \[TASK-", l) and "| DONE |" not in l]
        out.append(f"- Açık TASK sayısı: {len(rows)} (`tasks/BOARD.md`)")

    hist = sorted((ROOT / "history").glob("*.jsonl"))
    if hist:
        lines = hist[-1].read_text().splitlines()[-5:]
        out.append("- Son prompt'lar:")
        for l in lines:
            try:
                r = json.loads(l)
                out.append(f"  - {r.get('ts','')[:16]} [{r.get('task') or '-'}] {r.get('prompt','')[:90]}")
            except json.JSONDecodeError:
                pass
    print("\n".join(out))


if __name__ == "__main__":
    main()
