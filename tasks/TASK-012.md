---
id: TASK-012
title: Web kabuğunu, oturum akışını ve API client'ı kur
status: TODO
owner: B
agent: frontend-implementer
priority: P0
depends_on: [TASK-001]
requirements: [NFR-UX-01, NFR-UX-02]
adr: [0001]
owned_paths:
  - apps/web/
  - packages/api-client/
estimate: 3h
---

## Amaç
Web kabuğunu, oturum akışını ve API client'ı kur. Gereksinimler: NFR-UX-01, NFR-UX-02.

## Bağlam (ajan önce bunları okur)
- `knowledge/REQUIREMENTS.md` (NFR-UX-01, NFR-UX-02)
- `knowledge/ARCHITECTURE.md`, `knowledge/DATA_MODEL.md`
- `knowledge/contracts/openapi.yaml`
- adr/0001-*
- `rules/` (CLAUDE.md ile otomatik yüklü)

## Kabul kriterleri
- [ ] AC-1: `packages/api-client` sözleşmeden üretilir (`pnpm gen:api`)
- [ ] AC-2: Login/logout çalışır; CSRF header'ı otomatik eklenir; 401'de login'e yönlendirir
- [ ] AC-3: Sidebar + topbar layout, açık/koyu tema, rol bazlı menü
- [ ] AC-4: 375/768/1440 px'te taşma yok; axe serious/critical = 0

## Kapsam dışı
- `owned_paths` dışındaki dosyalar (gerekirse yeni TASK açılır).

## Uygulama planı
_(task-planner doldurur; insan onaylar)_

## Test planı
- Her AC için en az bir test, `TASK-012/AC-n` etiketiyle (R-TEST-02).
- Güvenlik: kimliksiz, kapsam dışı (404), yetkisiz (403), bozuk/büyük girdi.

## Açık sorular
_(yok)_

## Kayıt
| Zaman | Kim | Olay |
|---|---|---|
| 2026-11-18 | A | Oluşturuldu |
