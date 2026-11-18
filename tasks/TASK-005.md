---
id: TASK-005
title: Task API'sini uygula (CRUD, geçiş, yorum, geçmiş)
status: TODO
owner: A
agent: backend-implementer
priority: P0
depends_on: [TASK-004]
requirements: [TSK-01, TSK-02, TSK-03, TSK-04, TSK-05, TSK-07, TSK-08]
adr: [0002]
owned_paths:
  - apps/api/app/modules/tasks/
  - apps/api/tests/tasks/
estimate: 4h
---

## Amaç
Task API'sini uygula (CRUD, geçiş, yorum, geçmiş). Gereksinimler: TSK-01, TSK-02, TSK-03, TSK-04, TSK-05, TSK-07, TSK-08.

## Bağlam (ajan önce bunları okur)
- `knowledge/REQUIREMENTS.md` (TSK-01, TSK-02, TSK-03, TSK-04, TSK-05, TSK-07, TSK-08)
- `knowledge/ARCHITECTURE.md`, `knowledge/DATA_MODEL.md`
- `knowledge/contracts/openapi.yaml`
- adr/0002-*
- `rules/` (CLAUDE.md ile otomatik yüklü)

## Kabul kriterleri
- [ ] AC-1: `listTasks` tüm filtreleri (status çoklu, priority, type, team, project, assignee=me, overdue, q) ve sıralamayı destekler; sonuç rol kapsamıyla sınırlıdır
- [ ] AC-2: PROJECT task'ı projectId olmadan 400; çalışan başkasına atanmış task açamaz (403)
- [ ] AC-3: Durum geçişleri `knowledge/domain/task-lifecycle.md` tablosuna uyar; geçersiz geçiş 422, eski version 409
- [ ] AC-4: Her değişiklik audit log'a alan bazlı diff ile yazılır; `getTaskHistory` bunu döner
- [ ] AC-5: Atama ve durum değişikliği doğru kişilere bildirim üretir

## Kapsam dışı
- `owned_paths` dışındaki dosyalar (gerekirse yeni TASK açılır).

## Uygulama planı
_(task-planner doldurur; insan onaylar)_

## Test planı
- Her AC için en az bir test, `TASK-005/AC-n` etiketiyle (R-TEST-02).
- Güvenlik: kimliksiz, kapsam dışı (404), yetkisiz (403), bozuk/büyük girdi.

## Açık sorular
_(yok)_

## Kayıt
| Zaman | Kim | Olay |
|---|---|---|
| 2026-11-18 | A | Oluşturuldu |
