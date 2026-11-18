# Görev panosu

Kaynak: `tasks/TASK-*.md` (frontmatter `status`). `/implement-task` sonunda güncellenir.

| ID | Başlık | Sahip | Agent | Öncelik | Bağımlılık | Durum |
|---|---|---|---|---|---|---|
| [TASK-001](TASK-001.md) | Repo iskeletini ve docker compose ortamını kur | A | backend-implementer | P0 | — | TODO |
| [TASK-002](TASK-002.md) | Veri modelini, migration'ları ve seed'i oluştur | A | backend-implementer | P0 | TASK-001 | TODO |
| [TASK-003](TASK-003.md) | Oturum tabanlı kimlik doğrulamayı uygula | A | backend-implementer | P0 | TASK-002 | TODO |
| [TASK-004](TASK-004.md) | RBAC kapsam ve policy katmanını uygula | A | backend-implementer | P0 | TASK-003 | TODO |
| [TASK-005](TASK-005.md) | Task API'sini uygula (CRUD, geçiş, yorum, geçmiş) | A | backend-implementer | P0 | TASK-004 | TODO |
| [TASK-006](TASK-006.md) | Proje API'sini uygula | A | backend-implementer | P0 | TASK-004 | TODO |
| [TASK-007](TASK-007.md) | Dashboard ve rapor API'lerini uygula | A | backend-implementer | P0 | TASK-005, TASK-006 | TODO |
| [TASK-008](TASK-008.md) | Bildirim, duyuru ve worker işlerini uygula | A | backend-implementer | P0 | TASK-005 | TODO |
| [TASK-009](TASK-009.md) | Etkinlik ve katılım API'sini uygula | A | backend-implementer | P0 | TASK-004 | TODO |
| [TASK-010](TASK-010.md) | Yetkinlik API'sini uygula | A | backend-implementer | P0 | TASK-004 | TODO |
| [TASK-011](TASK-011.md) | API token'ları ve MCP sunucusunu uygula | A | mcp-implementer | P0 | TASK-005, TASK-007 | TODO |
| [TASK-012](TASK-012.md) | Web kabuğunu, oturum akışını ve API client'ı kur | B | frontend-implementer | P0 | TASK-001 | TODO |
| [TASK-013](TASK-013.md) | Dashboard, task ve proje ekranlarını yap | B | frontend-implementer | P0 | TASK-012, TASK-007 | TODO |
| [TASK-014](TASK-014.md) | Etkinlik, yetkinlik, rapor, bildirim ve yönetim ekranlarını yap | B | frontend-implementer | P0 | TASK-012, TASK-008, TASK-009, TASK-010 | TODO |
| [TASK-015](TASK-015.md) | Gözlemlenebilirlik ve güvenlik ekranlarını yap | C | backend-implementer | P0 | TASK-003, TASK-012 | TODO |
| [TASK-016](TASK-016.md) | Agent gate'lerini ve CI'ı kur | C | backend-implementer | P0 | TASK-001 | TODO |
| [TASK-017](TASK-017.md) | E2E ve güvenlik regresyon test paketini yaz | D | qa-implementer | P0 | TASK-013 | TODO |
| [TASK-019](TASK-019.md) | Unit hiyerarşisi, çok kişili task, ilerleme/takip, planlı rapor, yetkinlik puanı | A | backend-implementer | P0 | TASK-005, TASK-013, TASK-014 | REVIEW |
| [TASK-018](TASK-018.md) | Demo senaryolarını ve sunumu hazırla | D | presenter | P1 | TASK-015, TASK-016, TASK-017 | TODO |

## Paralel çalışma dalgaları

| Dalga | A (backend) | B (frontend) | C (sec/obs) | D (QA/sunum) |
|---|---|---|---|---|
| 1 | 001 → 002 → 003 | 012 (mock ile) | 016 | test iskeleti (017 hazırlık) |
| 2 | 004 → 005, 006 | 013 | 015 (backend kısmı) | 017 |
| 3 | 007, 008, 009, 010 | 014 | 015 (ekranlar) | 017 |
| 4 | 011 | entegrasyon | gate tuning | 018 |
