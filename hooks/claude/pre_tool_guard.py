#!/usr/bin/env python3
"""PreToolUse guardrail'i — kesin çalışır, ajan atlayamaz.

Engeller (exit 2):
  G1  Yazılan içerikte secret (R-CORE-06)
  G2  .env, history/, logs/, .git/ gibi korumalı yollara yazma
  G3  Aktif TASK varken owned_paths dışına yazma (R-CORE-02)
  G4  Tehlikeli shell komutları (force push, --no-verify, rm -rf, curl|sh, main'e push)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import ROOT, active_task, append_jsonl, block, has_secret, now, read_event, task_owned_paths  # noqa: E402

PROTECTED = [r"(^|/)\.env$", r"^history/", r"^logs/(?!pricing\.json$)", r"^\.git/", r"^\.claude/settings\.json$", r"^hooks/"]
ALWAYS_ALLOWED = [r"^tasks/", r"^\.claude/state/"]
DANGEROUS_BASH = [
    (r"git\s+push\s+.*(--force|-f)\b", "force push yasak (R-GIT-03)"),
    (r"git\s+push\s+\S+\s+main\b", "main'e doğrudan push yasak (R-GIT-03)"),
    (r"--no-verify", "git hook'larını atlamak yasak"),
    (r"rm\s+-rf\s+(/|~|\.\s*$|\*)", "geniş kapsamlı rm -rf yasak"),
    (r"curl[^|]*\|\s*(ba)?sh", "internetten script'i doğrudan çalıştırmak yasak"),
    (r"git\s+config\s+.*core\.hooksPath", "hook yolunu değiştirmek yasak"),
]


def rel(path: str) -> str:
    try:
        return str(Path(path).resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return path


def main() -> None:
    ev = read_event()
    tool = ev.get("tool_name", "")
    inp = ev.get("tool_input", {}) or {}

    if tool == "Bash":
        cmd = inp.get("command", "")
        for pat, why in DANGEROUS_BASH:
            if re.search(pat, cmd):
                log("deny", tool, cmd[:200], why)
                block(f"[guard G4] {why}: `{cmd[:120]}`")
        return

    if tool not in {"Write", "Edit", "MultiEdit", "NotebookEdit"}:
        return

    path = rel(inp.get("file_path") or inp.get("notebook_path") or "")
    content = inp.get("content") or inp.get("new_string") or ""
    if tool == "MultiEdit":
        content = "\n".join(e.get("new_string", "") for e in inp.get("edits", []))

    if has_secret(content):
        log("deny", tool, path, "secret")
        block(f"[guard G1] {path} içine secret benzeri değer yazılıyor. Env değişkeni kullan (R-CORE-06).")

    if any(re.search(p, path) for p in PROTECTED):
        log("deny", tool, path, "protected")
        block(f"[guard G2] {path} korumalı; sadece hook'lar/insan değiştirebilir.")

    task = active_task()
    if task and not any(re.search(p, path) for p in ALWAYS_ALLOWED):
        owned = task_owned_paths(task)
        if owned and not any(path == o or path.startswith(o.rstrip("/") + "/") for o in owned):
            log("deny", tool, path, f"outside {task}")
            block(f"[guard G3] {path}, {task} owned_paths dışında: {owned}. Gerekirse TASK'ı güncelle ya da yeni TASK aç (R-CORE-02).")

    log("allow", tool, path, task or "-")


def log(decision: str, tool: str, target: str, why: str) -> None:
    append_jsonl(ROOT / "logs" / "guard.jsonl", {"ts": now(), "decision": decision, "tool": tool, "target": target, "reason": why})


if __name__ == "__main__":
    main()
