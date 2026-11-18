---
id: TASK-007
title: Dashboard ve rapor API'lerini uygula
status: TODO
owner: A
agent: backend-implementer
priority: P0
depends_on: [TASK-005, TASK-006]
requirements: [DSH-01, DSH-02, DSH-03, RPT-01, RPT-02]
adr: []
owned_paths:
  - apps/api/app/modules/dashboard/
  - apps/api/app/modules/reports/
  - apps/api/tests/dashboard/
estimate: 3h
---

## Amaç
Dashboard ve rapor API'lerini uygula. Gereksinimler: DSH-01, DSH-02, DSH-03, RPT-01, RPT-02.

## Bağlam (ajan önce bunları okur)
- `knowledge/REQUIREMENTS.md` (DSH-01, DSH-02, DSH-03, RPT-01, RPT-02)
- `knowledge/ARCHITECTURE.md`, `knowledge/DATA_MODEL.md`
- `knowledge/contracts/openapi.yaml`

- `rules/` (CLAUDE.md ile otomatik yüklü)

## Kabul kriterleri
- [ ] AC-1: `getDashboardSummary` ekip bazında todo/inProgress/blocked/done/overdue/total sayılarını standard/project ayrımıyla döner
- [ ] AC-2: `todo+inProgress+blocked+done = total` ve overdue ⊆ açık task'lar değişmezleri test edilir
- [ ] AC-3: Çalışan sadece kendi ekibini, yönetici yönettiklerini, direktör tümünü görür
- [ ] AC-4: `getTaskReport` groupBy değerlerinin hepsini destekler; `format=csv` geçerli CSV döner ve `BULK_EXPORT` olayı yazılır; CSV formula injection'a karşı hücreler escape edilir
- [ ] AC-5: Seed verisiyle p95 < 300 ms

## Kapsam dışı
- `owned_paths` dışındaki dosyalar (gerekirse yeni TASK açılır).

## Uygulama planı
_(task-planner doldurur; insan onaylar)_

## Test planı
- Her AC için en az bir test, `TASK-007/AC-n` etiketiyle (R-TEST-02).
- Güvenlik: kimliksiz, kapsam dışı (404), yetkisiz (403), bozuk/büyük girdi.

## Açık sorular
_(yok)_

## Kayıt
| Zaman | Kim | Olay |
|---|---|---|
| 2026-11-18 | A | Oluşturuldu |
