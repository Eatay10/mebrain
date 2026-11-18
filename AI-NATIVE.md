# Cyber Task Hub — AI-Native Geliştirme

Değerlendirme başlıklarının her biri aşağıda **repo'daki kanıtına** bağlanmıştır.

## 1. Neden AI-Native? — Problemi adlandırmak

| | AI destekli | AI-native (bu repo) |
|---|---|---|
| Bağlam | Her prompt'ta kişi yeniden anlatır; bilgi sohbette kaybolur | Bağlam repo'da yaşar: `CLAUDE.md` + `rules/` her oturumda otomatik yüklenir; `knowledge/`, `adr/` ajanın referansı |
| İş tanımı | "Şunu yap" serbest metni | `tasks/TASK-NNN.md` sözleşmesi: kabul kriterleri, `owned_paths`, bağımlılıklar |
| Kalite | İnsan sonradan okur | Kurallar ölçülebilir (`R-XXX-NN` + kontrol aracı); hook'lar **kesin** uygular; gate agent'ları PR'ı bloklar |
| Rol | Tek bir genel asistan | Rolü, modeli ve yetkisi sınırlı subagent'lar (`agents/`) |
| Ölçüm | Yok | Her prompt, token, maliyet, guard kararı ve AI katkı oranı kayıtlı (`history/`, `logs/`, `/ai-stats`) |

**Problem:** AI'ın kod üretme hızı, bağlam ve guardrail olmadan tutarsızlık, güvenlik açığı ve doğrulanmamış iş üretir. **Çözüm:** prompt mühendisliğinden **bağlam mühendisliğine** geçmek — ajanın bilmesi gerekeni repo'ya yazmak ve kuralları makineyle zorlamak.

## 2. Repo anatomisi

| Klasör | İçerik | Kanıt |
|---|---|---|
| `rules/` | 7 dosya, ID'li ve **ölçülebilir** kurallar; her kuralın kontrol aracı yazılı | `rules/00-core.md` … `60-git-and-tasks.md`; `CLAUDE.md` `@import` ile her oturumda yükler |
| `adr/` | 4 mimari karar + gerekçe + alternatif | `adr/0001-tech-stack.md` … `0004-background-jobs.md`; `/new-adr` |
| `hooks/` | Claude (SessionStart, UserPromptSubmit, PreToolUse, Stop, SubagentStop) + git (pre-commit, commit-msg, pre-push) | `hooks/README.md`; **`bash scripts/test_hooks.sh` → 15/15** |
| `knowledge/` | Gereksinim, mimari, veri modeli, tehdit modeli; algoritmalar (`domain/`); sözleşmeler (`contracts/openapi.yaml`, `mcp-tools.md`); süreç (`process/`) | `knowledge/INDEX.md` |
| `skills/` | 5 tarif: endpoint ekleme, migration, güvenlik olayı, ekran, gate FAIL triage | `skills/README.md` |
| `commands/` | `/implement-task`, `/pre-pr`, `/new-task`, `/new-adr`, `/ai-stats` | `commands/README.md` |
| `agents/` | 12 subagent; her birinde `model:` ve `tools:` (yetki) + hook ile `owned_paths` sınırı | `agents/README.md` (model seçimi gerekçesiyle) |
| `tasks/` | `_TEMPLATE.md` + TASK-001…018 + `BOARD.md` (paralel dalgalar) | `tasks/TASK-001.md` |
| `history/` | Prompt (redakte) + sonuç özeti, JSONL | `history/README.md` |
| `logs/` | Model, token, USD maliyet, guard kararları, fiyat tablosu | `logs/README.md`, `logs/pricing.json` |

`.claude/{agents,commands,skills}` bu klasörlere sembolik bağdır; Claude Code onları yerel olarak yükler.

## 3. Orkestrasyon — "TASK-001'i implement et" dedikten sonra

Ayrıntılı sıra diyagramı: `knowledge/process/orchestration.md`. Özet:

`/implement-task TASK-001` → bağımlılık kontrolü → aktif TASK işaretlenir (hook'lar `owned_paths`'i buradan okur) → **task-planner** (Opus, salt-okunur) planı TASK'a yazar → **backend/frontend-implementer** paralel uygular (her yazım `pre_tool_guard.py`'den geçer) → **security-gate, contract-guard, qa-gate, ui-verifier** paralel, salt-okunur → `scripts/gate.py` deterministik karar → FAIL ise en fazla 2 düzeltme turu → AC checklist + BOARD güncellenir → commit `TASK-001: …` (`commit-msg` hook) → `Stop` hook maliyeti ve sonucu kaydeder.

## 4. Gözlemlenebilirlik — Ölçmediğinizi iyileştiremezsiniz

| Ne ölçülüyor | Nerede | Nasıl görülür |
|---|---|---|
| Her prompt ve sonucu | `history/*.jsonl` | `session_start` son 5'i bağlama ekler |
| Model, token (input/output/cache), USD | `logs/ai-usage.jsonl` | `/ai-stats` |
| TASK başına maliyet, cache isabeti | aynı | `/ai-stats --task TASK-005` |
| Guardrail izin/ret ve nedenleri | `logs/guard.jsonl` | `/ai-stats` |
| AI katkı oranı (commit / satır) | git `Co-Authored-By: Claude` | `/ai-stats` |
| Gate verdict'leri | `reports/agents/` | `scripts/gate.py` |
| AC test kapsamı | TASK'lar × testler | `scripts/ac_coverage.py` |

Hedefler ve iyileştirme döngüsü: `knowledge/process/ai-observability.md`. Ürünün kendi gözlemlenebilirliği (güvenlik olayları, RED metrikleri): `knowledge/OBSERVABILITY.md`.

## 5. Plugins — hazır olanın sağladığı kolaylık

Cloudflare `security-audit` skill, `archify`, Playwright MCP, Semgrep/Trivy/Gitleaks, Redocly, Claude Code GitHub Action ve **kendi MCP sunucumuz** — hangisi neyi hazır verir ve hangi agent kullanır: `knowledge/tooling/plugins.md`.

## 6. Demo — 4 senaryo

`demo/SCENARIOS.md`: (1) TASK orkestrasyonu, (2) MCP ile ürün verisi, (3) guardrail'lerin ajanı durdurması, (4) ölçüm ve öğrenme döngüsü — ve her klasörün hangi senaryoda göründüğünü gösteren kapsama matrisi.

## Hızlı doğrulama

```bash
bash scripts/setup.sh          # git hook'larını bağlar + 15 guardrail testini koşar
python3 scripts/ai_stats.py    # AI kullanım raporu
python3 scripts/ac_coverage.py --priority P0
```
