---
id: TASK-011
title: API token'ları ve MCP sunucusunu uygula
status: TODO
owner: A
agent: mcp-implementer
priority: P0
depends_on: [TASK-005, TASK-007]
requirements: [API-01, API-02, API-03]
adr: [0003]
owned_paths:
  - apps/api/app/modules/api_tokens/
  - apps/mcp/
  - apps/api/tests/api_tokens/
estimate: 3h
---

## Amaç
API token'ları ve MCP sunucusunu uygula. Gereksinimler: API-01, API-02, API-03.

## Bağlam (ajan önce bunları okur)
- `knowledge/REQUIREMENTS.md` (API-01, API-02, API-03)
- `knowledge/ARCHITECTURE.md`, `knowledge/DATA_MODEL.md`
- `knowledge/contracts/openapi.yaml`
- adr/0003-*
- `rules/` (CLAUDE.md ile otomatik yüklü)

## Kabul kriterleri
- [ ] AC-1: Token düz metni yalnızca oluşturma yanıtında döner; DB'de SHA-256 hash
- [ ] AC-2: Etkin yetki = scope ∩ rol; scope'u olmayan işlem 403
- [ ] AC-3: İptal edilmiş/süresi dolmuş token 401 + `API_TOKEN_INVALID`
- [ ] AC-4: MCP araçları `knowledge/contracts/mcp-tools.md` ile birebir; silme aracı yok; çıktıda `untrusted_content` var
- [ ] AC-5: Claude Code'dan stdio ile `search_tasks` çalışır (demo senaryosu 2)

## Kapsam dışı
- `owned_paths` dışındaki dosyalar (gerekirse yeni TASK açılır).

## Uygulama planı
_(task-planner doldurur; insan onaylar)_

## Test planı
- Her AC için en az bir test, `TASK-011/AC-n` etiketiyle (R-TEST-02).
- Güvenlik: kimliksiz, kapsam dışı (404), yetkisiz (403), bozuk/büyük girdi.

## Açık sorular
_(yok)_

## Kayıt
| Zaman | Kim | Olay |
|---|---|---|
| 2026-11-18 | A | Oluşturuldu |
