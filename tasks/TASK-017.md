---
id: TASK-017
title: E2E ve güvenlik regresyon test paketini yaz
status: TODO
owner: D
agent: qa-implementer
priority: P0
depends_on: [TASK-013]
requirements: [NFR-SEC-02]
adr: []
owned_paths:
  - tests/e2e/
  - apps/api/tests/security/
estimate: 4h
---

## Amaç
E2E ve güvenlik regresyon test paketini yaz. Gereksinimler: NFR-SEC-02.

## Bağlam (ajan önce bunları okur)
- `knowledge/REQUIREMENTS.md` (NFR-SEC-02)
- `knowledge/ARCHITECTURE.md`, `knowledge/DATA_MODEL.md`
- `knowledge/contracts/openapi.yaml`

- `rules/` (CLAUDE.md ile otomatik yüklü)

## Kabul kriterleri
- [ ] AC-1: Kritik yolculuklar: login → task oluştur → ata → durum değiştir → dashboard'da sayının değiştiğini gör
- [ ] AC-2: Her route için kimliksiz erişim testi (otomatik route keşfi)
- [ ] AC-3: IDOR matrisi: her rol × başka ekibin kaynağı → 404
- [ ] AC-4: `scripts/ac_coverage.py` tüm P0 TASK AC'lerinin testle eşlendiğini raporlar

## Kapsam dışı
- `owned_paths` dışındaki dosyalar (gerekirse yeni TASK açılır).

## Uygulama planı
_(task-planner doldurur; insan onaylar)_

## Test planı
- Her AC için en az bir test, `TASK-017/AC-n` etiketiyle (R-TEST-02).
- Güvenlik: kimliksiz, kapsam dışı (404), yetkisiz (403), bozuk/büyük girdi.

## Açık sorular
_(yok)_

## Kayıt
| Zaman | Kim | Olay |
|---|---|---|
| 2026-11-18 | A | Oluşturuldu |
