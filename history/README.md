# history/ — Prompt'lar ve sonuçlarının özet kaydı

`hooks/claude/prompt_log.py` (UserPromptSubmit) ve `hooks/claude/stop_log.py` (Stop) tarafından **otomatik** yazılır; elle düzenlenmez, silinemez (pre-commit). Günlük dosya: `YYYY-MM-DD.jsonl`.

```json
{"ts":"2026-11-18T13:40:02+00:00","kind":"prompt","session":"a1b2c3d4","task":"TASK-005","prompt":"/implement-task TASK-005","sha":"9f2c…"}
{"ts":"2026-11-18T13:52:41+00:00","kind":"result","session":"a1b2c3d4","task":"TASK-005","prompt_sha":"9f2c…","summary":"5/5 AC yeşil…","files_edited":["apps/api/app/modules/tasks/service.py"],"tool_calls":37,"cost_usd":1.42,"diffstat":"6 files changed, 412 insertions(+)"}
```

Secret kalıpları kayıttan önce `[REDACTED]` olur. Format ve metrikler: `knowledge/process/ai-observability.md`.
