# R-API — Sözleşme kuralları

Tek kaynak: `knowledge/contracts/openapi.yaml`. Gerekçe: `adr/0003-api-and-mcp.md`.

| ID | Kural | Kontrol |
|---|---|---|
| R-API-01 | Sözleşme önce değişir, kod sonra (aynı PR'da olabilir; sırası commit'te görünür). | contract-guard |
| R-API-02 | `redocly lint` hatasız. | pre-commit + CI |
| R-API-03 | FastAPI'nin ürettiği `/openapi.json`, sözleşmeyle operationId/method/path/şema bazında eşleşir. | `scripts/contract_diff.py` (CI) |
| R-API-04 | Breaking change (alan silme, tip değiştirme, yeni zorunlu alan) yeni ADR ister. | contract-guard |
| R-API-05 | Pydantic şema adı = sözleşmedeki `components/schemas` adı. | contract-guard |
| R-API-06 | Frontend sadece `packages/api-client` (sözleşmeden üretilmiş) ile API çağırır; elle `fetch('/api…')` yok. | eslint `no-restricted-syntax` + contract-guard |
| R-API-07 | Hata: `application/problem+json`; sayfalama `{items,total,page,pageSize}`; tarih ISO 8601 UTC. | contract-guard |
