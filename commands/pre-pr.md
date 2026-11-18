---
description: PR öncesi gate agent'larını paralel çalıştırıp özetler (salt-okunur).
---

Mevcut branch'i origin/main'e karşı değerlendir. Paralel subagent'lar: security-gate, contract-guard, qa-gate; apps/web değiştiyse ui-verifier; apps/api değiştiyse backend-reviewer ve observability-coverage.
Dosya değiştirme. Verdict'leri `reports/agents/<agent>/local.json` olarak kaydet, `python3 scripts/gate.py reports/agents/*/local.json` çalıştır.
Rapor: PASS/FAIL (gate.py exit code), agent × verdict × severity tablosu, bloklayan bulgular (konum + öneri), PR açıklaması taslağı (R-GIT-05).
