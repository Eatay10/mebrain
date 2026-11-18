---
id: TASK-009
title: Etkinlik ve katılım API'sini uygula
status: TODO
owner: A
agent: backend-implementer
priority: P0
depends_on: [TASK-004]
requirements: [EVT-01, EVT-02, EVT-03]
adr: []
owned_paths:
  - apps/api/app/modules/events/
  - apps/api/tests/events/
estimate: 2h
---

## Amaç
Etkinlik ve katılım API'sini uygula. Gereksinimler: EVT-01, EVT-02, EVT-03.

## Bağlam (ajan önce bunları okur)
- `knowledge/REQUIREMENTS.md` (EVT-01, EVT-02, EVT-03)
- `knowledge/ARCHITECTURE.md`, `knowledge/DATA_MODEL.md`
- `knowledge/contracts/openapi.yaml`

- `rules/` (CLAUDE.md ile otomatik yüklü)

## Kabul kriterleri
- [ ] AC-1: CORPORATE etkinliği sadece direktör oluşturur; INDIVIDUAL herkes
- [ ] AC-2: Katılım akışı REQUESTED→APPROVED/REJECTED→ATTENDED; geçersiz geçiş 422
- [ ] AC-3: Yönetici sadece kendi ekip üyelerinin katılımına karar verir; karar bildirim üretir
- [ ] AC-4: `url` sadece https kabul eder

## Kapsam dışı
- `owned_paths` dışındaki dosyalar (gerekirse yeni TASK açılır).

## Uygulama planı
_(task-planner doldurur; insan onaylar)_

## Test planı
- Her AC için en az bir test, `TASK-009/AC-n` etiketiyle (R-TEST-02).
- Güvenlik: kimliksiz, kapsam dışı (404), yetkisiz (403), bozuk/büyük girdi.

## Açık sorular
_(yok)_

## Kayıt
| Zaman | Kim | Olay |
|---|---|---|
| 2026-11-18 | A | Oluşturuldu |
