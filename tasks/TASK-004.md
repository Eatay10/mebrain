---
id: TASK-004
title: RBAC kapsam ve policy katmanını uygula
status: TODO
owner: A
agent: backend-implementer
priority: P0
depends_on: [TASK-003]
requirements: [AUT-02]
adr: [0002]
owned_paths:
  - apps/api/app/auth/policies.py
  - apps/api/app/auth/scope.py
  - apps/api/tests/auth/test_policies.py
estimate: 2h
---

## Amaç
RBAC kapsam ve policy katmanını uygula. Gereksinimler: AUT-02.

## Bağlam (ajan önce bunları okur)
- `knowledge/REQUIREMENTS.md` (AUT-02)
- `knowledge/ARCHITECTURE.md`, `knowledge/DATA_MODEL.md`
- `knowledge/contracts/openapi.yaml`
- adr/0002-*
- `rules/` (CLAUDE.md ile otomatik yüklü)

## Kabul kriterleri
- [ ] AC-1: `knowledge/domain/rbac-scope.md` policy tablosunun her hücresi parametrik testle doğrulanır
- [ ] AC-2: Kapsam dışı nesne 404, kapsam içi reddedilen işlem 403 + `AUTHZ_DENIED` döner
- [ ] AC-3: `app/auth` ve policies satır kapsamı ≥ %90

## Kapsam dışı
- `owned_paths` dışındaki dosyalar (gerekirse yeni TASK açılır).

## Uygulama planı
_(task-planner doldurur; insan onaylar)_

## Test planı
- Her AC için en az bir test, `TASK-004/AC-n` etiketiyle (R-TEST-02).
- Güvenlik: kimliksiz, kapsam dışı (404), yetkisiz (403), bozuk/büyük girdi.

## Açık sorular
_(yok)_

## Kayıt
| Zaman | Kim | Olay |
|---|---|---|
| 2026-11-18 | A | Oluşturuldu |
