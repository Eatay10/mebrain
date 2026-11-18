# AI gözlemlenebilirliği — Ölçmediğinizi iyileştiremezsiniz

İki katman: **ürünün** gözlemlenebilirliği (`knowledge/OBSERVABILITY.md`) ve **AI ile geliştirme sürecinin** gözlemlenebilirliği (bu dosya).

## Veri kaynakları (hepsi hook'larla otomatik; elle yazılmaz)

| Dosya | Üreten | Bir satır = | Alanlar |
|---|---|---|---|
| `history/YYYY-MM-DD.jsonl` (`kind: prompt`) | `UserPromptSubmit` | Girilen prompt | ts, session, task, prompt (redakte, ≤1000), sha |
| `history/YYYY-MM-DD.jsonl` (`kind: result`) | `Stop` | Prompt'un sonucu | prompt_sha, summary, files_edited, tool_calls, cost_usd, diffstat |
| `logs/ai-usage.jsonl` | `Stop`, `SubagentStop` | Tur × model | model, input, output, cache_write, cache_read, calls, cost_usd, tools, files_edited, task |
| `logs/guard.jsonl` | `PreToolUse` | Araç çağrısı kararı | decision (allow/deny), tool, target, reason |
| `reports/agents/<agent>/<ref>.json` | gate agent'ları | Verdict | şema aşağıda |
| git log | geliştirici + `Co-Authored-By: Claude` | Commit | AI katkı oranı |

Fiyatlar: `logs/pricing.json` (USD / 1M token).

## Metrikler (`/ai-stats` → `scripts/ai_stats.py`)

| Metrik | Neden önemli | Hedef |
|---|---|---|
| Toplam ve TASK başına maliyet | Hangi iş pahalı? Plan mı kötü, TASK mı büyük? | TASK başına < $3 |
| Model dağılımı | Doğru işe doğru model mi? (`agents/README.md` gerekçesi) | Haiku/Sonnet payı ≥ %40 |
| Cache isabet oranı | Bağlam (CLAUDE.md + rules) stabil mi? | ≥ %70 |
| AI katkı oranı (commit / satır) | AI-native çalışmanın kanıtı | raporlanır |
| Guard ret sayısı ve nedeni | Ajan hangi kuralı zorluyor? → rules/agents iyileştirmesi | trend ↓ |
| Gate FAIL oranı ve tur sayısı | İlk seferde doğru üretim | ilk tur PASS ≥ %60 |
| AC kapsamı (`scripts/ac_coverage.py`) | Doğrulanmış iş | P0 için %100 |

## İyileştirme döngüsü
Her sync'te `/ai-stats` → en pahalı TASK ve en sık guard reddi konuşulur → `rules/`, `skills/` veya `agents/` güncellenir → bir sonraki ölçümde etkisi görülür.

## Verdict şeması (gate agent'ları)

```json
{
  "agent": "security-gate",
  "ref": "TASK-005",
  "verdict": "pass | warn | fail",
  "findings": [{
    "id": "SEC-001", "severity": "critical|high|medium|low|info",
    "title": "...", "location": "apps/api/...:58", "evidence": "...",
    "refs": ["CWE-639", "ASVS 8.2.2", "R-SEC-02"], "recommendation": "...",
    "confidence": "confirmed|likely|needs-review"
  }],
  "skipped_checks": [{"check": "trivy", "reason": "not installed"}],
  "summary": "..."
}
```

## Gizlilik
Prompt'lar kaydedilmeden önce `_common.redact()` ile secret kalıpları silinir; `history/` ve `logs/` commit'lenir ama silinemez (pre-commit). Gerçek kişisel veri prompt'a yazılmaz (R-CORE-07).
