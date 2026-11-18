#!/usr/bin/env python3
"""R-API-03: çalışan API'nin /openapi.json'u ile sözleşmeyi operationId + method + path bazında karşılaştırır.

Kullanım: python3 scripts/contract_diff.py [--url http://localhost:8000/api/v1/openapi.json]
Sözleşme YAML'ı okumak için PyYAML gerekir (apps/api ortamında var): `uv run --project apps/api python scripts/contract_diff.py`.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METHODS = {"get", "post", "put", "patch", "delete"}


def ops(spec: dict) -> dict[str, tuple[str, str]]:
    out = {}
    for path, item in spec.get("paths", {}).items():
        for m, op in item.items():
            if m in METHODS:
                out[op.get("operationId", f"{m} {path}")] = (m.upper(), path)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000/api/v1/openapi.json")
    a = ap.parse_args()
    import yaml  # type: ignore

    contract = ops(yaml.safe_load((ROOT / "knowledge/contracts/openapi.yaml").read_text()))
    try:
        live = ops(json.load(urllib.request.urlopen(a.url, timeout=5)))
    except Exception as e:
        print(f"API'ye ulaşılamadı ({e}); kontrol atlandı")
        return 0
    missing = sorted(set(contract) - set(live))
    extra = sorted(set(live) - set(contract))
    moved = sorted(k for k in set(contract) & set(live) if contract[k] != live[k])
    for k in missing:
        print(f"• uygulanmamış: {k} {contract[k]}")
    for k in extra:
        print(f"✘ sözleşmede yok: {k} {live[k]}  (R-CORE-04)")
    for k in moved:
        print(f"✘ method/path farklı: {k} sözleşme={contract[k]} canlı={live[k]}")
    print(f"sözleşme {len(contract)} · canlı {len(live)} · fazla {len(extra)} · uyumsuz {len(moved)}")
    return 1 if extra or moved else 0


if __name__ == "__main__":
    sys.exit(main())
