---
id: TASK-001
title: Repo iskeletini ve docker compose ortamını kur
status: TODO
owner: A
agent: backend-implementer
priority: P0
depends_on: []
requirements: [NFR-OPS-01]
adr: [0001]
owned_paths:
  - apps/api/pyproject.toml
  - apps/api/app/main.py
  - apps/api/app/config.py
  - apps/api/Dockerfile
  - apps/web/package.json
  - docker-compose.yml
  - .env.example
  - Makefile
estimate: 2h
---

## Amaç
Repo iskeletini ve docker compose ortamını kur. Gereksinimler: NFR-OPS-01.

## Bağlam (ajan önce bunları okur)
- `knowledge/REQUIREMENTS.md` (NFR-OPS-01)
- `knowledge/ARCHITECTURE.md`, `knowledge/DATA_MODEL.md`
- `knowledge/contracts/openapi.yaml`
- adr/0001-*
- `rules/` (CLAUDE.md ile otomatik yüklü)

## Kabul kriterleri
- [ ] AC-1: `docker compose up` ile db, api, worker, web, mailpit ayağa kalkar; `GET /api/v1/health` 200 döner
- [ ] AC-2: `GET /api/v1/ready` DB erişilemezken 503, erişilebilirken 200 döner
- [ ] AC-3: Her yanıtta `X-Request-ID` header'ı bulunur; log satırları JSON ve `request_id` içerir
- [ ] AC-4: Security header'lar (CSP, X-Content-Type-Options, Referrer-Policy, Frame-Options) her yanıtta set edilir
- [ ] AC-5: `.env.example` dışında secret yok; gitleaks temiz

## Kapsam dışı
- `owned_paths` dışındaki dosyalar (gerekirse yeni TASK açılır).

## Uygulama planı
_(task-planner doldurur; insan onaylar)_

## Test planı
- Her AC için en az bir test, `TASK-001/AC-n` etiketiyle (R-TEST-02).
- Güvenlik: kimliksiz, kapsam dışı (404), yetkisiz (403), bozuk/büyük girdi.

## Açık sorular
_(yok)_

## Kayıt
| Zaman | Kim | Olay |
|---|---|---|
| 2026-11-18 | A | Oluşturuldu |
