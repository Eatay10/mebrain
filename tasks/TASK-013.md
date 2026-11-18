---
id: TASK-013
title: Dashboard, task ve proje ekranlarını yap
status: TODO
owner: B
agent: frontend-implementer
priority: P0
depends_on: [TASK-012, TASK-007]
requirements: [DSH-01, DSH-02, TSK-01, TSK-08, PRJ-01]
adr: []
owned_paths:
  - apps/web/src/features/dashboard/
  - apps/web/src/features/tasks/
  - apps/web/src/features/projects/
estimate: 5h
---

## Amaç
Dashboard, task ve proje ekranlarını yap. Gereksinimler: DSH-01, DSH-02, TSK-01, TSK-08, PRJ-01.

## Bağlam (ajan önce bunları okur)
- `knowledge/REQUIREMENTS.md` (DSH-01, DSH-02, TSK-01, TSK-08, PRJ-01)
- `knowledge/ARCHITECTURE.md`, `knowledge/DATA_MODEL.md`
- `knowledge/contracts/openapi.yaml`

- `rules/` (CLAUDE.md ile otomatik yüklü)

## Kabul kriterleri
- [ ] AC-1: Dashboard: ekip kartları başlanmadı/devam/bloklu/tamamlandı/gecikmiş sayılarını standart/proje sekmeleriyle gösterir
- [ ] AC-2: Task listesi filtreleri URL'de tutulur; task detayında durum geçişi, yorum, geçmiş
- [ ] AC-3: Proje listesi ilerleme çubuğu ile; proje detayında proje task'ları
- [ ] AC-4: Her ekranda loading/empty/error durumları; console hatası yok

## Kapsam dışı
- `owned_paths` dışındaki dosyalar (gerekirse yeni TASK açılır).

## Uygulama planı
_(task-planner doldurur; insan onaylar)_

## Test planı
- Her AC için en az bir test, `TASK-013/AC-n` etiketiyle (R-TEST-02).
- Güvenlik: kimliksiz, kapsam dışı (404), yetkisiz (403), bozuk/büyük girdi.

## Açık sorular
_(yok)_

## Kayıt
| Zaman | Kim | Olay |
|---|---|---|
| 2026-11-18 | A | Oluşturuldu |
