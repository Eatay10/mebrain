---
id: TASK-015
title: Gözlemlenebilirlik ve güvenlik ekranlarını yap
status: TODO
owner: C
agent: backend-implementer
priority: P0
depends_on: [TASK-003, TASK-012]
requirements: [OBS-01, AUD-01]
adr: []
owned_paths:
  - apps/api/app/observability/
  - apps/api/app/modules/security/
  - apps/web/src/features/observability/
  - scripts/simulate_traffic.py
estimate: 4h
---

## Amaç
Gözlemlenebilirlik ve güvenlik ekranlarını yap. Gereksinimler: OBS-01, AUD-01.

## Bağlam (ajan önce bunları okur)
- `knowledge/REQUIREMENTS.md` (OBS-01, AUD-01)
- `knowledge/ARCHITECTURE.md`, `knowledge/DATA_MODEL.md`
- `knowledge/contracts/openapi.yaml`

- `rules/` (CLAUDE.md ile otomatik yüklü)

## Kabul kriterleri
- [ ] AC-1: `knowledge/OBSERVABILITY.md`'deki güvenlik olaylarının hepsi üretilir
- [ ] AC-2: Güvenlik ekranı: zaman serisi, olay tipi dağılımı, en çok tetikleyen IP'ler, açık alarmlar
- [ ] AC-3: Sistem ekranı: endpoint bazlı istek/hata oranı/p95, worker iş durumu
- [ ] AC-4: `scripts/simulate_traffic.py` brute-force, IDOR, büyük payload ve rate-limit desenlerini lokalde üretir; her alarm kuralı tetiklenir

## Kapsam dışı
- `owned_paths` dışındaki dosyalar (gerekirse yeni TASK açılır).

## Uygulama planı
_(task-planner doldurur; insan onaylar)_

## Test planı
- Her AC için en az bir test, `TASK-015/AC-n` etiketiyle (R-TEST-02).
- Güvenlik: kimliksiz, kapsam dışı (404), yetkisiz (403), bozuk/büyük girdi.

## Açık sorular
_(yok)_

## Kayıt
| Zaman | Kim | Olay |
|---|---|---|
| 2026-11-18 | A | Oluşturuldu |
