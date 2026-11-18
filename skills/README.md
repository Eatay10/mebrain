# skills/ — Tekrarlayan işlerin tarifleri

Ajan bir işi her seferinde yeniden keşfetmez; tarif buradan yüklenir (`.claude/skills/` → bu klasör). Proje dışı hazır skill'ler: `knowledge/tooling/plugins.md`.

| Skill | Ne zaman |
|---|---|
| `add-api-endpoint` | Sözleşmedeki bir operationId için FastAPI endpoint'ini katmanlarıyla, policy'si, audit'i ve testleriyle ekler. Yeni bir backend endpoint'i yazarken kullan. |
| `write-migration` | Alembic migration'ı DATA_MODEL.md ile tutarlı, geri alınabilir şekilde yazar. Model veya tablo değişikliğinde kullan. |
| `add-security-event` | Yeni bir güvenlik olayı tipini uçtan uca ekler (enum, sözleşme, üretim noktası, ekran, alarm, test). |
| `build-screen` | React ekranını standart durumlar, erişilebilirlik ve doğrulama adımlarıyla kurar. Yeni bir sayfa/ekran yaparken kullan. |
| `triage-gate-failure` | Gate agent'ı FAIL verdiğinde bulguyu doğrular, düzeltme TASK'ını ve regresyon testini planlar. |
