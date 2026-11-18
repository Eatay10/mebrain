#!/usr/bin/env python3
"""R-TEST-02: her TASK kabul kriterinin (AC) en az bir teste bağlı olduğunu ölçer.

Testlerde etiket: Python `@pytest.mark.ac("TASK-005/AC-2")`, TS `annotation: { type: 'ac', description: 'TASK-005/AC-2' }`.
Kullanım: python3 scripts/ac_coverage.py [--priority P0] [--fail-under 1.0]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--priority", default=None)
    ap.add_argument("--fail-under", type=float, default=0.0)
    a = ap.parse_args()

    acs: dict[str, str] = {}
    for f in sorted((ROOT / "tasks").glob("TASK-*.md")):
        text = f.read_text()
        if a.priority and f"priority: {a.priority}" not in text:
            continue
        for m in re.finditer(r"- \[[ x]\] (AC-\d+): (.+)", text):
            acs[f"{f.stem}/{m.group(1)}"] = m.group(2)[:70]

    linked: set[str] = set()
    for src in list(ROOT.glob("apps/**/tests/**/*.py")) + list(ROOT.glob("tests/**/*.ts")) + list(ROOT.glob("apps/**/*.spec.ts")):
        linked |= set(re.findall(r"(TASK-\d{3}/AC-\d+)", src.read_text(errors="ignore")))

    covered = [k for k in acs if k in linked]
    ratio = len(covered) / len(acs) if acs else 1.0
    print(f"AC kapsamı: {len(covered)}/{len(acs)} = {ratio:.0%}")
    for k, v in acs.items():
        if k not in linked:
            print(f"  ✘ {k}: {v}")
    return 1 if ratio < a.fail_under else 0


if __name__ == "__main__":
    raise SystemExit(main())
