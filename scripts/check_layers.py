#!/usr/bin/env python3
"""R-PY-01: katman import yönünü denetler. routers → services → repositories → models.

İhlal: router'ın repository/models import etmesi, service'in router import etmesi, repository'nin service import etmesi.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "apps" / "api" / "app"
FORBIDDEN = {
    "router": {"repository", "models"},
    "service": {"router"},
    "repository": {"service", "router"},
    "models": {"service", "router", "repository"},
}


def layer(name: str) -> str | None:
    for l in FORBIDDEN:
        if name.split(".")[-1].startswith(l):
            return l
    return None


def main() -> int:
    bad = 0
    for f in ROOT.rglob("*.py") if ROOT.exists() else []:
        me = layer(f.stem)
        if not me:
            continue
        for node in ast.walk(ast.parse(f.read_text())):
            mods = [n.name for n in node.names] if isinstance(node, ast.Import) else [node.module or ""] if isinstance(node, ast.ImportFrom) else []
            for m in mods:
                other = layer(m)
                if other in FORBIDDEN[me]:
                    print(f"✘ {f.relative_to(ROOT.parent)}:{node.lineno} {me} → {other} ({m}) — R-PY-01")
                    bad += 1
    print("katman ihlali:", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
