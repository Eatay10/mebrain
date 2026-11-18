# hooks/ — Kesin çalışan guardrail'ler

Kurallar (`rules/`) ajana *ne yapması gerektiğini* söyler; hook'lar ajan unutsa ya da yönlendirilse bile *kesin* uygular. Exit code 2 (Claude) / 1 (git) işlemi durdurur.

## Claude Code olayları (`.claude/settings.json` ile bağlı)

| Olay | Script | Ne yapar | Kural |
|---|---|---|---|
| `SessionStart` | `claude/session_start.py` | Aktif TASK, açık iş sayısı, son prompt'ları bağlama ekler | bağlam mühendisliği |
| `UserPromptSubmit` | `claude/prompt_log.py` | Prompt'u redakte edip `history/`'ye yazar | gözlem |
| `PreToolUse` (Write/Edit/MultiEdit/Bash) | `claude/pre_tool_guard.py` | G1 secret · G2 korumalı yol · G3 `owned_paths` dışı · G4 tehlikeli komut → **ret** | R-CORE-02, R-CORE-06, R-GIT-03 |
| `Stop` / `SubagentStop` | `claude/stop_log.py` | Model, token, maliyet, araçlar, değişen dosyalar → `logs/ai-usage.jsonl`; sonuç özeti → `history/` | gözlem |

## Git (`git config core.hooksPath hooks/git`, `scripts/setup.sh` yapar)

| Hook | Ne yapar | Kural |
|---|---|---|
| `pre-commit` | gitleaks, redocly lint, ruff, eslint/tsc; history/logs silme yasağı | R-CORE-06, R-API-02, R-PY-04, R-TS-01 |
| `commit-msg` | `TASK-NNN: …` biçimi ve TASK dosyasının varlığı | R-CORE-01, R-GIT-02 |
| `pre-push` | `main`'e push yok, branch adı `task/TASK-NNN-…` | R-GIT-01, R-GIT-03 |

## Test
`scripts/test_hooks.sh` her guardrail'i örnek olayla tetikler ve beklenen ret/izni doğrular.
