---
id: TASK-010
title: Yetkinlik API'sini uygula
status: TODO
owner: A
agent: backend-implementer
priority: P0
depends_on: [TASK-004]
requirements: [CMP-01, CMP-02]
adr: []
owned_paths:
  - apps/api/app/modules/competencies/
  - apps/api/tests/competencies/
estimate: 2h
---

## Amaç
Yetkinlik API'sini uygula. Gereksinimler: CMP-01, CMP-02.

## Bağlam (ajan önce bunları okur)
- `knowledge/REQUIREMENTS.md` (CMP-01, CMP-02)
- `knowledge/ARCHITECTURE.md`, `knowledge/DATA_MODEL.md`
- `knowledge/contracts/openapi.yaml`

- `rules/` (CLAUDE.md ile otomatik yüklü)

## Kabul kriterleri
- [ ] AC-1: Kullanıcı kendi seviyesini 1–5 arası girer; `verified=true` göndermesi 403
- [ ] AC-2: Yönetici ekip üyesini doğrular; `verifiedBy/verifiedAt` set edilir
- [ ] AC-3: `getCompetencyMatrix` ekip × yetkinlik matrisini döner

## Kapsam dışı
- `owned_paths` dışındaki dosyalar (gerekirse yeni TASK açılır).

## Uygulama planı
_(task-planner doldurur; insan onaylar)_

## Test planı
- Her AC için en az bir test, `TASK-010/AC-n` etiketiyle (R-TEST-02).
- Güvenlik: kimliksiz, kapsam dışı (404), yetkisiz (403), bozuk/büyük girdi.

## Açık sorular
_(yok)_

## Kayıt
| Zaman | Kim | Olay |
|---|---|---|
| 2026-11-18 | A | Oluşturuldu |
