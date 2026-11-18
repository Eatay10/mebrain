# R-PY — Backend (Python / FastAPI)

| ID | Kural | Kontrol |
|---|---|---|
| R-PY-01 | Katmanlar: `routers → services → repositories → models`. Router'da iş kuralı ve DB erişimi yok. | `scripts/check_layers.py` (import yönü) |
| R-PY-02 | Modül yapısı: `app/modules/<alan>/{router,service,repository,schemas,models}.py`. | review |
| R-PY-03 | Tip ipuçları zorunlu; `mypy --strict` hatasız. | mypy (pre-commit) |
| R-PY-04 | `ruff check` + `ruff format` temiz. | pre-commit |
| R-PY-05 | Yapısal log: `structlog`, her log satırında `request_id`. `print` yok. | ruff `T20` |
| R-PY-06 | Her DB değişikliği bir Alembic migration'ı; migration geri alınabilir (`downgrade`). | test: `alembic upgrade head && downgrade -1` |
| R-PY-07 | Konfigürasyon `app/config.py` (pydantic-settings) üzerinden env'den; `.env.example` güncel. | review |
| R-PY-08 | Yetkili işlemler `audit.record(...)` çağırır. | observability-coverage |
