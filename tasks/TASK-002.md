---
id: TASK-002
title: Veri modelini, migration'ları ve seed'i oluştur
status: TODO
owner: A
agent: backend-implementer
priority: P0
depends_on: [TASK-001]
requirements: [TSK-01, PRJ-01, EVT-01, CMP-01]
adr: [0001]
owned_paths:
  - apps/api/app/models/
  - apps/api/migrations/
  - apps/api/app/seed.py
estimate: 3h
---

## Amaç
Veri modelini, migration'ları ve seed'i oluştur. Gereksinimler: TSK-01, PRJ-01, EVT-01, CMP-01.

## Bağlam (ajan önce bunları okur)
- `knowledge/REQUIREMENTS.md` (TSK-01, PRJ-01, EVT-01, CMP-01)
- `knowledge/ARCHITECTURE.md`, `knowledge/DATA_MODEL.md`
- `knowledge/contracts/openapi.yaml`
- adr/0001-*
- `rules/` (CLAUDE.md ile otomatik yüklü)

## Kabul kriterleri
- [ ] AC-1: `alembic upgrade head` tüm tabloları `knowledge/DATA_MODEL.md`'deki kısıtlarla oluşturur; `downgrade base` temiz geri alır
- [ ] AC-2: `type=PROJECT ⇔ project_id NOT NULL` CHECK kısıtı DB'de uygulanır
- [ ] AC-3: Seed: 1 direktör, 3 yönetici, 4 ekip, ~40 çalışan, ~600 task, 15 proje, 20 etkinlik, yetkinlik kataloğu — sentetik ve deterministik
- [ ] AC-4: `audit_logs` tablosunda uygulama DB kullanıcısının UPDATE/DELETE yetkisi yoktur

## Kapsam dışı
- `owned_paths` dışındaki dosyalar (gerekirse yeni TASK açılır).

## Uygulama planı
_(task-planner doldurur; insan onaylar)_

## Test planı
- Her AC için en az bir test, `TASK-002/AC-n` etiketiyle (R-TEST-02).
- Güvenlik: kimliksiz, kapsam dışı (404), yetkisiz (403), bozuk/büyük girdi.

## Açık sorular
_(yok)_

## Kayıt
| Zaman | Kim | Olay |
|---|---|---|
| 2026-11-18 | A | Oluşturuldu |
