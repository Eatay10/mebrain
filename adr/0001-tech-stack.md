# ADR-0001: Teknoloji yığını

- Durum: **Önerildi** (A onayı bekliyor)
- Tarih: 2026-11-18

## Bağlam

4 kişilik ekip, ~24 saat, güvenlik odaklı bir web uygulaması + REST API + MCP sunucusu. Sözleşme-önce (contract-first) çalışacağız. Ekipte Python deneyimi baskın; frontend için playbook React + TypeScript öngörüyor.

## Karar

| Katman | Seçim | Gerekçe |
|---|---|---|
| Backend | **Python 3.12 + FastAPI**, Pydantic v2 | Hızlı geliştirme, yerleşik şema doğrulama, ekip deneyimi |
| ORM / migration | SQLAlchemy 2 + Alembic | Parametreli sorgu varsayılan, olgun |
| DB | PostgreSQL 17 | İlişkisel model, `FILTER` ile hızlı dashboard sayımları |
| Worker | Aynı kod tabanı, ayrı process; APScheduler + DB tabanlı `jobs` tablosu | Redis gerektirmez, tek bağımlılık |
| Auth | Sunucu tarafı session (DB) + HttpOnly cookie; API için kişisel token; argon2id | Token sızıntısı/XSS riskini azaltır, iptal kolay |
| Frontend | React + TypeScript (strict) + Vite, TanStack Query, React Router, react-hook-form + zod, Tailwind + shadcn/ui, Recharts | Playbook ile uyumlu |
| API client | `openapi-typescript` + `openapi-fetch` (`packages/api-client`) | Sözleşmeden tip üretimi, uydurma endpoint imkânsız |
| MCP | Python `mcp` SDK (FastMCP), stdio + Streamable HTTP | Backend ile aynı dil; API'yi httpx ile çağırır |
| E-posta | aiosmtplib → Mailpit | Demo güvenli |
| Gözlem | structlog (JSON), prometheus-client, OpenTelemetry | `knowledge/OBSERVABILITY.md` |
| Test | pytest + httpx (API), Vitest (web), Playwright (E2E) | |
| Paket | uv (Python), pnpm (JS) | Hızlı, kilit dosyalı |

## Sözleşme uyumu

`knowledge/contracts/openapi.yaml` tek kaynaktır. FastAPI'nin ürettiği `/openapi.json` CI'da sözleşmeyle karşılaştırılır (contract-guard + deterministik diff). Pydantic şemaları sözleşmedeki `components/schemas` ile birebir adlandırılır.

## Alternatif

Node/TypeScript (Fastify + Prisma) — uçtan uca tek dil avantajı; ekibin Python deneyimi nedeniyle ikinci tercih. Karar değişirse sadece `apps/api` ve `apps/mcp` etkilenir; sözleşme ve dokümanlar aynı kalır.
