---
id: TASK-016
title: Agent gate'lerini ve CI'ı kur
status: TODO
owner: C
agent: backend-implementer
priority: P0
depends_on: [TASK-001]
requirements: [NFR-SEC-01]
adr: []
owned_paths:
  - .github/workflows/
  - scripts/gate.py
  - scripts/contract_diff.py
  - scripts/check_layers.py
  - scripts/ac_coverage.py
estimate: 3h
---

## Amaç
Agent gate'lerini ve CI'ı kur. Gereksinimler: NFR-SEC-01.

## Bağlam (ajan önce bunları okur)
- `knowledge/REQUIREMENTS.md` (NFR-SEC-01)
- `knowledge/ARCHITECTURE.md`, `knowledge/DATA_MODEL.md`
- `knowledge/contracts/openapi.yaml`

- `rules/` (CLAUDE.md ile otomatik yüklü)

## Kabul kriterleri
- [ ] AC-1: PR'da security-gate, contract-guard, qa-gate, ui-verifier çalışır; verdict JSON'ları artefakt olur
- [ ] AC-2: `gate.py` şema geçersiz verdict'i FAIL sayar; confirmed Critical/High → FAIL
- [ ] AC-3: Kasıtlı IDOR içeren örnek PR bloklanır (demo senaryosu 3)
- [ ] AC-4: Deterministik tarayıcılar (gitleaks, semgrep, trivy) API'den bağımsız ayrı job

## Kapsam dışı
- `owned_paths` dışındaki dosyalar (gerekirse yeni TASK açılır).

## Uygulama planı
_(task-planner doldurur; insan onaylar)_

## Test planı
- Her AC için en az bir test, `TASK-016/AC-n` etiketiyle (R-TEST-02).
- Güvenlik: kimliksiz, kapsam dışı (404), yetkisiz (403), bozuk/büyük girdi.

## Açık sorular
_(yok)_

## Kayıt
| Zaman | Kim | Olay |
|---|---|---|
| 2026-11-18 | A | Oluşturuldu |
