---
id: TASK-018
title: Demo senaryolarını ve sunumu hazırla
status: TODO
owner: D
agent: presenter
priority: P1
depends_on: [TASK-015, TASK-016, TASK-017]
requirements: []
adr: []
owned_paths:
  - demo/
  - docs/presentation/
estimate: 3h
---

## Amaç
Demo senaryolarını ve sunumu hazırla. Gereksinimler: —.

## Bağlam (ajan önce bunları okur)
- `knowledge/REQUIREMENTS.md` (—)
- `knowledge/ARCHITECTURE.md`, `knowledge/DATA_MODEL.md`
- `knowledge/contracts/openapi.yaml`

- `rules/` (CLAUDE.md ile otomatik yüklü)

## Kabul kriterleri
- [ ] AC-1: `demo/SCENARIOS.md`'deki 4 senaryo temiz kurulumda baştan sona çalışır
- [ ] AC-2: `/ai-stats` çıktısı sunuma eklenir (AI katkı oranı, token, maliyet)
- [ ] AC-3: Yedek video kaydı alınır

## Kapsam dışı
- `owned_paths` dışındaki dosyalar (gerekirse yeni TASK açılır).

## Uygulama planı
_(task-planner doldurur; insan onaylar)_

## Test planı
- Her AC için en az bir test, `TASK-018/AC-n` etiketiyle (R-TEST-02).
- Güvenlik: kimliksiz, kapsam dışı (404), yetkisiz (403), bozuk/büyük girdi.

## Açık sorular
_(yok)_

## Kayıt
| Zaman | Kim | Olay |
|---|---|---|
| 2026-11-18 | A | Oluşturuldu |
