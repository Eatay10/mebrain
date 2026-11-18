---
id: TASK-014
title: Etkinlik, yetkinlik, rapor, bildirim ve yönetim ekranlarını yap
status: TODO
owner: B
agent: frontend-implementer
priority: P0
depends_on: [TASK-012, TASK-008, TASK-009, TASK-010]
requirements: [EVT-01, EVT-03, CMP-02, RPT-01, NTF-01, COM-01, AUT-04]
adr: []
owned_paths:
  - apps/web/src/features/events/
  - apps/web/src/features/competencies/
  - apps/web/src/features/reports/
  - apps/web/src/features/notifications/
  - apps/web/src/features/admin/
estimate: 5h
---

## Amaç
Etkinlik, yetkinlik, rapor, bildirim ve yönetim ekranlarını yap. Gereksinimler: EVT-01, EVT-03, CMP-02, RPT-01, NTF-01, COM-01, AUT-04.

## Bağlam (ajan önce bunları okur)
- `knowledge/REQUIREMENTS.md` (EVT-01, EVT-03, CMP-02, RPT-01, NTF-01, COM-01, AUT-04)
- `knowledge/ARCHITECTURE.md`, `knowledge/DATA_MODEL.md`
- `knowledge/contracts/openapi.yaml`

- `rules/` (CLAUDE.md ile otomatik yüklü)

## Kabul kriterleri
- [ ] AC-1: Etkinlik listesi + katılım talebi + yönetici onay kuyruğu
- [ ] AC-2: Kişisel yetkinlik profili ve ekip matrisi (ısı haritası)
- [ ] AC-3: Rapor ekranı: groupBy + tarih aralığı + CSV indirme
- [ ] AC-4: Bildirim zili (okunmamış sayısı) ve duyurular
- [ ] AC-5: Direktör için kullanıcı/ekip/rol yönetimi

## Kapsam dışı
- `owned_paths` dışındaki dosyalar (gerekirse yeni TASK açılır).

## Uygulama planı
_(task-planner doldurur; insan onaylar)_

## Test planı
- Her AC için en az bir test, `TASK-014/AC-n` etiketiyle (R-TEST-02).
- Güvenlik: kimliksiz, kapsam dışı (404), yetkisiz (403), bozuk/büyük girdi.

## Açık sorular
_(yok)_

## Kayıt
| Zaman | Kim | Olay |
|---|---|---|
| 2026-11-18 | A | Oluşturuldu |
