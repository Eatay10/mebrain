---
id: TASK-006
title: Proje API'sini uygula
status: TODO
owner: A
agent: backend-implementer
priority: P0
depends_on: [TASK-004]
requirements: [PRJ-01, PRJ-02]
adr: []
owned_paths:
  - apps/api/app/modules/projects/
  - apps/api/tests/projects/
estimate: 2h
---

## Amaç
Proje API'sini uygula. Gereksinimler: PRJ-01, PRJ-02.

## Bağlam (ajan önce bunları okur)
- `knowledge/REQUIREMENTS.md` (PRJ-01, PRJ-02)
- `knowledge/ARCHITECTURE.md`, `knowledge/DATA_MODEL.md`
- `knowledge/contracts/openapi.yaml`

- `rules/` (CLAUDE.md ile otomatik yüklü)

## Kabul kriterleri
- [ ] AC-1: Yönetici sadece yönettiği ekipte proje oluşturur; çalışan 403
- [ ] AC-2: `progress` alanı proje task'larının durum sayılarını doğru verir
- [ ] AC-3: Açık task'ı olan proje silinemez (409)

## Kapsam dışı
- `owned_paths` dışındaki dosyalar (gerekirse yeni TASK açılır).

## Uygulama planı
_(task-planner doldurur; insan onaylar)_

## Test planı
- Her AC için en az bir test, `TASK-006/AC-n` etiketiyle (R-TEST-02).
- Güvenlik: kimliksiz, kapsam dışı (404), yetkisiz (403), bozuk/büyük girdi.

## Açık sorular
_(yok)_

## Kayıt
| Zaman | Kim | Olay |
|---|---|---|
| 2026-11-18 | A | Oluşturuldu |
