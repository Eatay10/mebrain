---
name: add-api-endpoint
description: Sözleşmedeki bir operationId için FastAPI endpoint'ini katmanlarıyla, policy'si, audit'i ve testleriyle ekler. Yeni bir backend endpoint'i yazarken kullan.
---

# Tarif: Yeni API endpoint'i

1. `knowledge/contracts/openapi.yaml`'da operationId'yi bul; request/response şemalarını not et. Yoksa DUR (R-API-01).
2. `app/modules/<alan>/schemas.py`: şema adları sözleşmeyle aynı, `model_config = ConfigDict(extra="forbid")`, tüm string'lerde `max_length` (R-SEC-05).
3. `repository.py`: sorguya `visible_<x>_filter(user)` ekle (R-SEC-03). Ham SQL yok.
4. `service.py`: ilk satırda ilgili `policies.can_*` (knowledge/domain/rbac-scope.md); kapsam dışı → `NotFound`, ret → `Forbidden` + `security_event(AUTHZ_DENIED)`; değişiklikte `audit.record(...)`.
5. `router.py`: sadece bağımlılıklar + service çağrısı; `operation_id` sözleşmeyle aynı; response_model.
6. Testler (`tests/<alan>/test_<op>.py`): başarılı, 400, 401, 403/404 (R-TEST-01); `@pytest.mark.ac("TASK-NNN/AC-n")`.
7. Çalıştır: `uv run pytest -q tests/<alan>`, `uv run ruff check`, `uv run mypy app`, `python3 scripts/contract_diff.py`.
