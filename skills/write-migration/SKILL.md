---
name: write-migration
description: Alembic migration'ı DATA_MODEL.md ile tutarlı, geri alınabilir şekilde yazar. Model veya tablo değişikliğinde kullan.
---

# Tarif: Migration
1. `knowledge/DATA_MODEL.md`'yi güncelle (önce doküman).
2. `uv run alembic revision --autogenerate -m "<özet>"`; üretileni oku: enum, CHECK, partial index, citext autogenerate'te eksik kalır — elle ekle.
3. `downgrade()` gerçekten geri alır.
4. Doğrula: `uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head` (R-PY-06).
