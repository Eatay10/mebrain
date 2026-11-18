#!/usr/bin/env python3
"""Stop (ve SubagentStop): her yanıt turunun sonunda

  1) logs/ai-usage.jsonl  ← model, token (input/output/cache), maliyet (USD), süre, araç sayıları
  2) history/<gün>.jsonl  ← prompt'un sonucunun özeti (son asistan metni, değişen dosyalar)

Transcript JSONL'ini okur; aynı mesajı iki kez saymamak için oturum başına ofset tutar.
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import ROOT, STATE, active_task, append_jsonl, now, read_event, redact  # noqa: E402

PRICING = json.loads((ROOT / "logs" / "pricing.json").read_text())["models"]


def price(model: str, u: dict) -> float:
    p = next((v for k, v in PRICING.items() if model.startswith(k)), None)
    if not p:
        return 0.0
    return (
        u["input"] * p["input"] + u["output"] * p["output"]
        + u["cache_write"] * p["cache_write"] + u["cache_read"] * p["cache_read"]
    ) / 1_000_000


def main() -> None:
    ev = read_event()
    tpath = Path(ev.get("transcript_path", ""))
    sid = (ev.get("session_id") or "")[:8]
    event = ev.get("hook_event_name", "Stop")
    if not tpath.exists():
        return

    off_file = STATE / f"offset-{sid}-{event}"
    start = int(off_file.read_text()) if off_file.exists() else 0
    lines = tpath.read_text(encoding="utf-8", errors="ignore").splitlines()
    off_file.write_text(str(len(lines)))

    usage: dict[str, dict] = defaultdict(lambda: Counter(input=0, output=0, cache_write=0, cache_read=0, calls=0))
    tools: Counter = Counter()
    edited: set[str] = set()
    last_text = ""
    seen_ids: set[str] = set()
    for raw in lines[start:]:
        try:
            r = json.loads(raw)
        except json.JSONDecodeError:
            continue
        msg = r.get("message") or {}
        if msg.get("role") != "assistant":
            continue
        mid = msg.get("id")
        u = msg.get("usage") or {}
        if u and mid not in seen_ids:
            seen_ids.add(mid)
            m = usage[msg.get("model", "unknown")]
            m["input"] += u.get("input_tokens", 0)
            m["output"] += u.get("output_tokens", 0)
            m["cache_write"] += u.get("cache_creation_input_tokens", 0)
            m["cache_read"] += u.get("cache_read_input_tokens", 0)
            m["calls"] += 1
        for block in msg.get("content") or []:
            if block.get("type") == "tool_use":
                tools[block.get("name")] += 1
                fp = (block.get("input") or {}).get("file_path")
                if fp and block.get("name") in {"Write", "Edit", "MultiEdit"}:
                    edited.add(fp.replace(str(ROOT) + "/", ""))
            elif block.get("type") == "text" and block.get("text"):
                last_text = block["text"]

    task = active_task()
    ts = now()
    for model, u in usage.items():
        append_jsonl(ROOT / "logs" / "ai-usage.jsonl", {
            "ts": ts, "session": sid, "event": event, "task": task, "model": model,
            **{k: u[k] for k in ("input", "output", "cache_write", "cache_read", "calls")},
            "cost_usd": round(price(model, u), 6),
            "tools": dict(tools), "files_edited": sorted(edited),
        })

    if event == "Stop":
        append_jsonl(ROOT / "history" / f"{ts[:10]}.jsonl", {
            "ts": ts, "kind": "result", "session": sid, "task": task,
            "prompt_sha": (STATE / f"last-prompt-{sid}").read_text() if (STATE / f"last-prompt-{sid}").exists() else None,
            "summary": redact(last_text)[:600],
            "files_edited": sorted(edited),
            "tool_calls": sum(tools.values()),
            "cost_usd": round(sum(price(m, u) for m, u in usage.items()), 6),
            "diffstat": _diffstat(),
        })


def _diffstat() -> str:
    try:
        return subprocess.run(["git", "diff", "--shortstat"], cwd=ROOT, capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return ""


if __name__ == "__main__":
    main()
