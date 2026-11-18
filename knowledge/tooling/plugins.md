# Plugin'ler, skill'ler ve MCP sunucuları — hazır olanın sağladığı kolaylık

Kendi yazdıklarımız: `agents/`, `skills/`, `commands/`, `hooks/`. Hazır aldıklarımız aşağıda — **tekerleği yeniden icat etmemek** için.

| Hazır bileşen | Tür | Kurulum | Sağladığı | Kim kullanır |
|---|---|---|---|---|
| Cloudflare `security-audit` | skill | `npx skills add https://github.com/cloudflare/security-audit-skill --skill security-audit --agent claude-code --global` | Trust boundary haritalama, doğrulanmış bulgu, ASVS/CWE eşleme, JSON/MD rapor şeması | `security-gate` |
| `archify` | skill | `npx skills add https://archify.si --skill archify --agent claude-code --global` | Repo'dan interaktif mimari/akış diyagramı | `presenter`, ARCHITECTURE |
| Playwright | MCP sunucusu + CLI | `claude mcp add playwright -- npx @playwright/mcp@latest` | Ajanın tarayıcıyı gerçek kullanıcı gibi sürmesi | `ui-verifier`, `frontend-implementer` |
| Semgrep, Trivy, Gitleaks | CLI | `brew install semgrep trivy gitleaks` | Deterministik SAST, bağımlılık/container, secret taraması | `pre-commit`, `security-gate` |
| Redocly CLI | CLI | `npx @redocly/cli` | OpenAPI lint | `pre-commit`, `contract-guard` |
| `code-review` / `security-review` | Claude Code yerleşik komut | — | Diff üzerinde ikinci göz | geliştirici, PR öncesi |
| GitHub CLI + Claude Code GitHub Action | CLI / Action | `gh`, `anthropics/claude-code-action` | PR'da gate agent'larını CI'da koşturma | TASK-016 |
| Kendi MCP sunucumuz (`apps/mcp`) | MCP | `claude mcp add cth -- uv run --project apps/mcp cth-mcp` | Ürünün verisini AI asistanına açmak (ürün özelliği) | son kullanıcı, demo senaryosu 2 |

## Seçim ilkeleri
1. Deterministik iş (lint, secret, CVE) → hazır CLI; LLM sadece triage ve doğrulama yapar.
2. Uzmanlık gerektiren tekrar eden iş (güvenlik denetimi, diyagram) → topluluk skill'i; içeriği kurulumdan önce incelenir (skill'ler ajan yetkisiyle çalışır).
3. Projeye özgü iş → `skills/` altında kendi tarifimiz.
