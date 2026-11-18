# ADR-0003: Veri paylaşımı — REST API ve MCP

- Durum: **Önerildi**
- Tarih: 2026-11-18

## Karar

Gereksinim "API veya MCP" diyor; **ikisini de** sunuyoruz çünkü MCP, REST'in üstünde ince bir katman olarak ucuza geliyor ve demoda fark yaratıyor.

### REST
- Base path: `/api/v1`. Sözleşme: `knowledge/contracts/openapi.yaml` (OpenAPI 3.1).
- Hata biçimi: RFC 9457 `application/problem+json` (`type`, `title`, `status`, `detail`, `instance`, `errors[]`, `requestId`).
- Sayfalama: `page` (1..), `pageSize` (1..100, varsayılan 20) → `{items, total, page, pageSize}`.
- Tarih/saat: ISO 8601 UTC; tarih alanları `YYYY-MM-DD`.
- ID'ler: UUID v4.
- Silme: soft delete (`deleted_at`); listelemelerde gizli.
- Rate limit: kimliksiz 30/dk/IP, kimlikli 300/dk/kullanıcı, login 10/dk/IP → `429` + `Retry-After`.

### MCP (`apps/mcp`)
- Python `mcp` SDK. Transport: **stdio** (Claude Desktop/Code'da yerel) ve **Streamable HTTP** (`/mcp`, demo için).
- Kimlik: env `CTH_API_TOKEN` (stdio) veya `Authorization: Bearer` (HTTP). MCP sunucusu token'ı API'ye aynen iletir; **DB'ye erişimi yoktur**.
- Araçlar:

| Araç | REST karşılığı | Scope |
|---|---|---|
| `whoami` | `GET /auth/me` | — |
| `search_tasks` | `GET /tasks` | tasks:read |
| `get_task` | `GET /tasks/{id}` | tasks:read |
| `create_task` | `POST /tasks` | tasks:write |
| `transition_task` | `POST /tasks/{id}/transitions` | tasks:write |
| `add_task_comment` | `POST /tasks/{id}/comments` | tasks:write |
| `get_dashboard` | `GET /dashboard/summary` | reports:read |
| `get_task_report` | `GET /reports/tasks` | reports:read |
| `list_projects` | `GET /projects` | projects:read |
| `list_events` | `GET /events` | events:read |
| `list_team_competencies` | `GET /users/{id}/competencies` | competencies:read |

- **Silme, rol değişikliği, kullanıcı yönetimi araçları yoktur.**
- Araç çıktılarında kullanıcı kaynaklı metin alanları (`title`, `description`, yorumlar) `untrusted_content` olarak ayrıştırılır; araç açıklamaları modele bu içeriklerdeki talimatlara uymamasını söyler (prompt injection savunması).
- MCP resource: `cth://dashboard/me` (salt okunur özet).

## Sonuçlar
- Yetki tek yerde (API). MCP'nin güvenlik yüzeyi = API token yüzeyi.
- `contract-guard`, MCP araçlarının sadece sözleşmedeki operasyonları çağırdığını da denetler.
