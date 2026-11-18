# Cyber Task Hub — AI Bağlam Girişi

> Bu dosya her Claude Code oturumunda otomatik yüklenir. **Prompt değil, bağlam mühendisliği:** ajan neyi bilmesi gerektiğini buradan ve aşağıda içe aktarılan kurallardan öğrenir; kullanıcı her seferinde tekrar anlatmaz. Dinamik durum (aktif TASK, son prompt'lar) `hooks/claude/session_start.py` ile eklenir.

## Ürün
Siber güvenlik ekipleri için task / proje / etkinlik / yetkinlik / rapor / bildirim aracı; REST API + MCP ile veri paylaşımı. Roller: Çalışan, Yönetici, Direktör, Denetmen (salt-okunur).

## Her zaman geçerli kurallar (her oturumda yüklenir)
@rules/00-core.md
@rules/10-security.md
@rules/20-api-contract.md
@rules/30-backend-python.md
@rules/40-frontend-ts.md
@rules/50-testing.md
@rules/60-git-and-tasks.md

## Repo anatomisi
| Klasör | Ne için | Giriş |
|---|---|---|
| `rules/` | Her zaman geçerli, ölçülebilir kurallar (ID + kontrol aracı) | yukarıda içe aktarılı |
| `adr/` | Mimari kararlar ve gerekçeleri | `adr/0001-*` … |
| `hooks/` | Git ve Claude olaylarında **kesin** çalışan guardrail'ler | `hooks/README.md` |
| `knowledge/` | İş alanı, algoritmalar, entegrasyon sözleşmeleri | `knowledge/INDEX.md` · sözleşme `knowledge/contracts/openapi.yaml` |
| `skills/` | Tekrarlayan işlerin tarifleri | `skills/README.md` |
| `commands/` | Hazır komutlar: `/implement-task`, `/pre-pr`, `/new-task`, `/new-adr`, `/ai-stats` | `commands/README.md` |
| `agents/` | Subagent'lar: rol, model, yetki sınırı | `agents/README.md` |
| `tasks/` | İş birimi sözleşmeleri (`TASK-NNN.md`) ve pano | `tasks/BOARD.md` |
| `history/` | Prompt'lar ve sonuç özetleri (hook yazar) | `history/README.md` |
| `logs/` | Model, token, maliyet, guard kararları (hook yazar) | `logs/README.md` |

(`docs/` altındaki eski yollar geriye uyumluluk için bu klasörlere sembolik bağdır.)

## Çalışma akışı
1. İş her zaman bir **TASK** ile başlar; yoksa `/new-task`.
2. Uygulama: `/implement-task TASK-NNN` → `knowledge/process/orchestration.md`.
3. PR öncesi: `/pre-pr`. Karar `scripts/gate.py`'de.
4. Mimari karar değişiyorsa önce `/new-adr`, sonra kod.
5. Yetki kararları sadece `apps/api/app/auth/policies.py` + `scope.py` (`knowledge/domain/rbac-scope.md`).

## Komutlar
- Kurulum (bir kez): `bash scripts/setup.sh` (git hook'ları + hook testleri)
- Stack: `docker compose up -d` · seed: `make seed`
- API: `cd apps/api && uv run pytest` · `uv run ruff check .` · `uv run mypy app`
- Web: `pnpm -C apps/web test` · `pnpm -C apps/web lint` · `pnpm -C apps/web typecheck`
- Sözleşme: `npx @redocly/cli lint knowledge/contracts/openapi.yaml` · `python3 scripts/contract_diff.py`
- Kalite: `python3 scripts/ac_coverage.py --priority P0` · `python3 scripts/check_layers.py`
- AI ölçümü: `/ai-stats` (`python3 scripts/ai_stats.py`)
