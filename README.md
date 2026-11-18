# Cyber Task Hub

Siber güvenlik ekiplerinin günlük iş yönetimi aracı: task'lar (standart + proje), etkinlik ve yetkinlik takibi, rol bazlı yetkilendirme (çalışan / yönetici / direktör), toplu raporlama ve bildirimler, REST API + MCP ile veri paylaşımı.

> Durum: API, worker, web ve MCP çalışır durumda. Organizasyon: Direktör → 9 unit (TEAM-IAM … TEAM-SMA) → ekipler. Devir notları: [docs/HANDOFF.md](docs/HANDOFF.md).

## Hızlı başlangıç

Gerekenler: Docker, [uv](https://docs.astral.sh/uv/), Node 22+ ve pnpm (`corepack enable` ya da `npx pnpm@12.21.0`).

```bash
cp .env.example .env            # yer tutucuları doldur (parolalar dahil)
docker compose up -d            # db, mailpit, api, worker, web, mcp
cd apps/api && uv run python -m app.seed --reset   # demo verisi
```

| Servis | Adres |
|---|---|
| Web | http://localhost:8080 |
| API | http://localhost:8000/api/v1 (sağlık: `/health`, `/ready`) |
| MCP (streamable HTTP) | http://localhost:8001/mcp — `Authorization: Bearer <API token>` |
| Mailpit | http://localhost:8025 |
| PostgreSQL | localhost:5433 |

Demo hesapları (`@demo.local`, parola `.env` → `CTH_SEED_PASSWORD`): `director`, `auditor` (salt okunur), unit yöneticileri `unit.<iam|cdc|mss|is|s|saa|os|sm|sma>`, ekip yöneticileri `manager.<ekip>` (ör. `manager.soc` — SOC + Zafiyet, `manager.csirt`), çalışanlar `analyst.<ekip><n>` (ör. `analyst.soc1`).

MCP için API token'ı web'de **API & MCP** menüsünden alınır. stdio modunda: `cd apps/mcp && CTH_API_TOKEN=… uv run cth-mcp`.

## Testler ve kontroller

```bash
cd apps/api && uv run pytest && uv run ruff check . && uv run mypy app   # API
cd apps/mcp && uv run pytest                                            # MCP
pnpm -C apps/web typecheck                                              # Web
pnpm install && pnpm -C tests/e2e exec playwright install chromium      # E2E (bir kez)
pnpm test:e2e                                                           # E2E (stack ayakta olmalı)
npx @redocly/cli lint knowledge/contracts/openapi.yaml                  # Sözleşme
python3 scripts/ac_coverage.py --priority P0                            # Kabul kriteri ↔ test eşlemesi
```

E2E yalnızca `localhost`'a karşı çalışır (`CTH_E2E_BASE_URL`, varsayılan http://localhost:8080) ve seed parolasını ortamdan ya da `.env`'den okur. Her çalıştırma `[e2e]` önekli task ve etkinlikler oluşturur; temiz başlangıç için seed'i `--reset` ile yeniden çalıştırın.

Sözleşme değişince üretilen kodu yenileyin (elle düzenlemeyin): `apps/api/scripts/gen_contract.sh` (Pydantic) ve `pnpm gen:api` (TS tipleri).

| Doküman | İçerik |
|---|---|
| [knowledge/REQUIREMENTS.md](knowledge/REQUIREMENTS.md) | Gereksinim matrisi, MUST/NICE, varsayımlar |
| [knowledge/ARCHITECTURE.md](knowledge/ARCHITECTURE.md) | Bileşenler, güven sınırları, yetki matrisi, akışlar |
| [adr/](adr/) | Mimari kararlar |
| [knowledge/DATA_MODEL.md](knowledge/DATA_MODEL.md) | Veri modeli |
| [knowledge/contracts/openapi.yaml](knowledge/contracts/openapi.yaml) | API sözleşmesi (OpenAPI 3.1) |
| [knowledge/THREAT_MODEL.md](knowledge/THREAT_MODEL.md) | Tehdit modeli |
| [knowledge/OBSERVABILITY.md](knowledge/OBSERVABILITY.md) | Log, metrik, güvenlik olayları, alarmlar |
| [knowledge/ACCEPTANCE.md](knowledge/ACCEPTANCE.md) | Kabul kriterleri |
| [docs/TASKS.md](docs/TASKS.md) | Görev planı ve dosya sahipliği |
| [knowledge/process/definition-of-done.md](knowledge/process/definition-of-done.md) | Bitti tanımı |
