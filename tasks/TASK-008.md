---
id: TASK-008
title: Bildirim, duyuru ve worker işlerini uygula
status: TODO
owner: A
agent: backend-implementer
priority: P0
depends_on: [TASK-005]
requirements: [NTF-01, NTF-02, COM-01, TSK-06]
adr: [0004]
owned_paths:
  - apps/api/app/modules/notifications/
  - apps/api/app/modules/announcements/
  - apps/api/app/worker/
  - apps/api/tests/worker/
estimate: 3h
---

## Amaç
Bildirim, duyuru ve worker işlerini uygula. Gereksinimler: NTF-01, NTF-02, COM-01, TSK-06.

## Bağlam (ajan önce bunları okur)
- `knowledge/REQUIREMENTS.md` (NTF-01, NTF-02, COM-01, TSK-06)
- `knowledge/ARCHITECTURE.md`, `knowledge/DATA_MODEL.md`
- `knowledge/contracts/openapi.yaml`
- adr/0004-*
- `rules/` (CLAUDE.md ile otomatik yüklü)

## Kabul kriterleri
- [ ] AC-1: Bildirim uç noktaları sözleşmeye uyar; kullanıcı sadece kendi bildirimlerini görür
- [ ] AC-2: Duyuru: TEAM yönetici+, ORGANIZATION sadece direktör; hedef kitle bildirim alır
- [ ] AC-3: `generate_recurring_tasks` idempotent: iki kez çalıştırma kopya üretmez (`knowledge/domain/recurrence.md`)
- [ ] AC-4: Son tarih yaklaşan/geçen task'lar için bildirim bir kez üretilir (dedup_key)
- [ ] AC-5: E-postalar Mailpit'e düşer; başarısızlık 3 denemeden sonra FAILED olur

## Kapsam dışı
- `owned_paths` dışındaki dosyalar (gerekirse yeni TASK açılır).

## Uygulama planı
_(task-planner doldurur; insan onaylar)_

## Test planı
- Her AC için en az bir test, `TASK-008/AC-n` etiketiyle (R-TEST-02).
- Güvenlik: kimliksiz, kapsam dışı (404), yetkisiz (403), bozuk/büyük girdi.

## Açık sorular
_(yok)_

## Kayıt
| Zaman | Kim | Olay |
|---|---|---|
| 2026-11-18 | A | Oluşturuldu |
