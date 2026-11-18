#!/usr/bin/env python3
"""AI-native gözlemlenebilirlik raporu.

Kaynaklar: logs/ai-usage.jsonl (Stop hook), logs/guard.jsonl (PreToolUse), history/*.jsonl, git log.
Çıktı: model × token × maliyet, TASK başına maliyet, AI katkı oranı (commit/satır), guard ret istatistiği.

Kullanım: python3 scripts/ai_stats.py [--since 2026-11-18] [--task TASK-005] [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def jsonl(path: Path):
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def git_contribution(since: str | None) -> dict:
    args = ["git", "log", "--no-merges", "--numstat", "--format=@@%H%x09%s%x09%b"]
    if since:
        args.append(f"--since={since}")
    try:
        out = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except Exception:
        return {}
    commits, ai_commits, lines, ai_lines = 0, 0, 0, 0
    cur_ai = False
    for line in out.splitlines():
        if line.startswith("@@"):
            commits += 1
            cur_ai = bool(re.search(r"Co-Authored-By:\s*Claude", line, re.I))
            ai_commits += cur_ai
            continue
        m = re.match(r"(\d+)\t(\d+)\t", line)
        if m:
            n = int(m.group(1)) + int(m.group(2))
            lines += n
            ai_lines += n if cur_ai else 0
    return {
        "commits": commits, "ai_commits": ai_commits,
        "lines_changed": lines, "ai_lines_changed": ai_lines,
        "ai_commit_ratio": round(ai_commits / commits, 3) if commits else 0,
        "ai_line_ratio": round(ai_lines / lines, 3) if lines else 0,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since")
    ap.add_argument("--task")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    def keep(r: dict) -> bool:
        return (not a.since or r.get("ts", "") >= a.since) and (not a.task or r.get("task") == a.task)

    by_model: dict[str, Counter] = defaultdict(Counter)
    by_task: dict[str, Counter] = defaultdict(Counter)
    tools: Counter = Counter()
    for r in filter(keep, jsonl(ROOT / "logs" / "ai-usage.jsonl")):
        for k in ("input", "output", "cache_write", "cache_read", "calls"):
            by_model[r["model"]][k] += r.get(k, 0)
        by_model[r["model"]]["cost_usd"] += r.get("cost_usd", 0)
        t = r.get("task") or "(task yok)"
        by_task[t]["cost_usd"] += r.get("cost_usd", 0)
        by_task[t]["output"] += r.get("output", 0)
        tools.update(r.get("tools", {}))

    prompts = [r for d in sorted((ROOT / "history").glob("*.jsonl")) for r in jsonl(d) if keep(r) and r.get("kind") == "prompt"]
    guard = [r for r in jsonl(ROOT / "logs" / "guard.jsonl") if keep(r)]
    denies = Counter(r["reason"] for r in guard if r["decision"] == "deny")

    total_in = sum(c["input"] + c["cache_read"] + c["cache_write"] for c in by_model.values())
    cache_hit = sum(c["cache_read"] for c in by_model.values()) / total_in if total_in else 0
    report = {
        "models": {m: {k: round(v, 4) for k, v in c.items()} for m, c in by_model.items()},
        "total_cost_usd": round(sum(c["cost_usd"] for c in by_model.values()), 4),
        "cache_hit_ratio": round(cache_hit, 3),
        "cost_by_task": {t: round(c["cost_usd"], 4) for t, c in sorted(by_task.items(), key=lambda x: -x[1]["cost_usd"])},
        "prompts": len(prompts),
        "tool_calls": dict(tools.most_common(10)),
        "guard": {"allow": sum(r["decision"] == "allow" for r in guard), "deny": sum(denies.values()), "deny_reasons": dict(denies)},
        "ai_contribution": git_contribution(a.since),
    }
    if a.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    print("== Model kullanımı ==")
    print(f"{'model':22} {'çağrı':>6} {'input':>10} {'output':>9} {'cache_r':>10} {'USD':>9}")
    for m, c in report["models"].items():
        print(f"{m:22} {int(c['calls']):6} {int(c['input']):10} {int(c['output']):9} {int(c['cache_read']):10} {c['cost_usd']:9.4f}")
    print(f"Toplam maliyet: ${report['total_cost_usd']}  ·  cache isabet oranı: {report['cache_hit_ratio']:.0%}  ·  prompt: {report['prompts']}")
    print("\n== TASK başına maliyet ==")
    for t, v in list(report["cost_by_task"].items())[:10]:
        print(f"  {t:14} ${v}")
    print("\n== Guardrail ==")
    g = report["guard"]
    print(f"  izin: {g['allow']}  ret: {g['deny']}  {g['deny_reasons']}")
    c = report["ai_contribution"]
    if c:
        print("\n== AI katkısı (git, Co-Authored-By: Claude) ==")
        print(f"  commit: {c['ai_commits']}/{c['commits']} ({c['ai_commit_ratio']:.0%})  ·  satır: {c['ai_lines_changed']}/{c['lines_changed']} ({c['ai_line_ratio']:.0%})")


if __name__ == "__main__":
    main()
