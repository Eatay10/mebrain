# logs/ — Model, token, maliyet ve AI katkı istatistikleri

| Dosya | Üreten | İçerik |
|---|---|---|
| `ai-usage.jsonl` | `Stop` / `SubagentStop` hook | Tur × model: input/output/cache token, USD maliyet, araç sayıları, değişen dosyalar, TASK |
| `guard.jsonl` | `PreToolUse` hook | Her araç çağrısının izin/ret kararı ve nedeni |
| `pricing.json` | insan | Model fiyatları (USD / 1M token) |

Rapor: `/ai-stats` veya `python3 scripts/ai_stats.py [--since …] [--task …] [--json]` — model dağılımı, toplam ve TASK başına maliyet, cache isabeti, guard retleri, git'ten AI katkı oranı (`Co-Authored-By: Claude` trailer'lı commit/satır).
