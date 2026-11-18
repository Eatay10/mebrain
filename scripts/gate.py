#!/usr/bin/env python3
"""Gate kararı: agent verdict JSON'larını okur, eşiğe göre exit code döner.

Karar agent'ın yazısında değil burada (deterministik). Şema bozuk verdict → FAIL.
Kullanım: python3 scripts/gate.py reports/agents/*/TASK-005.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BLOCKING = {"security-gate", "contract-guard", "qa-gate", "ui-verifier", "release-readiness"}
SEV = ["info", "low", "medium", "high", "critical"]


def valid(v: dict) -> bool:
    return (
        isinstance(v, dict) and v.get("verdict") in {"pass", "warn", "fail"}
        and isinstance(v.get("findings"), list)
        and all(f.get("severity") in SEV and f.get("confidence") in {"confirmed", "likely", "needs-review"} for f in v["findings"])
    )


def main(paths: list[str]) -> int:
    if not paths:
        print("verdict dosyası yok → FAIL")
        return 1
    failed = False
    print(f"{'agent':24} {'verdict':8} {'crit':>4} {'high':>4} {'med':>4}  karar")
    for p in paths:
        try:
            v = json.loads(Path(p).read_text())
        except Exception as e:
            print(f"{p}: okunamadı ({e}) → FAIL")
            failed = True
            continue
        agent = v.get("agent", Path(p).parent.name)
        if not valid(v):
            print(f"{agent:24} {'?':8} şema geçersiz → FAIL")
            failed = True
            continue
        cnt = {s: sum(f["severity"] == s for f in v["findings"]) for s in SEV}
        confirmed_hi = any(f["severity"] in {"high", "critical"} and f["confidence"] == "confirmed" for f in v["findings"])
        block = agent in BLOCKING and (v["verdict"] == "fail" or confirmed_hi)
        failed |= block
        print(f"{agent:24} {v['verdict']:8} {cnt['critical']:4} {cnt['high']:4} {cnt['medium']:4}  {'BLOK' if block else 'ok'}")
    print("SONUÇ:", "FAIL" if failed else "PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
