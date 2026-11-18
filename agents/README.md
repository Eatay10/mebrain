# agents/ — Subagent tanımları

Her agent: **rol** (description), **model** (maliyet/yetenek dengesi), **yetki sınırı** (tools + hook). Claude Code bunları `.claude/agents/` (→ bu klasöre sembolik bağ) üzerinden yükler.

| Agent | Rol | Model | Araçlar | Yazabilir mi | Ek sınır |
|---|---|---|---|---|---|
| `task-planner` | TASK dosyasını, ilgili knowledge/ ve adr/ belgelerini okuyup adım adım uygulama planı çıkarır. Kod yazmaz. | `claude-opus-5-5` | Read, Grep, Glob | ✗ | salt-okunur; karar gate.py'de |
| `backend-implementer` | Backend TASK'larını (apps/api) plana göre uygular ve testlerini çalıştırır. Yazma yetkisi hook ile owned_paths'e sınırlı. | `claude-opus-5-5` | Read, Grep, Glob, Edit, Write, Bash | ✓ | owned_paths (pre_tool_guard G3) |
| `frontend-implementer` | Frontend TASK'larını (apps/web) uygular, Playwright ile tarayıcıda doğrular. | `claude-opus-5-5` | Read, Grep, Glob, Edit, Write, Bash | ✓ | owned_paths (pre_tool_guard G3) |
| `mcp-implementer` | MCP sunucusunu (apps/mcp) knowledge/contracts/mcp-tools.md'ye birebir uygular. | `claude-sonnet-5-5` | Read, Grep, Glob, Edit, Write, Bash | ✓ | owned_paths (pre_tool_guard G3) |
| `qa-implementer` | E2E ve güvenlik regresyon testlerini yazar (tests/e2e, apps/api/tests/security). | `claude-sonnet-5-5` | Read, Grep, Glob, Edit, Write, Bash | ✓ | owned_paths (pre_tool_guard G3) |
| `security-gate` | PR öncesi ve PR'da salt-okunur güvenlik kapısı: security-audit skill + semgrep/trivy/gitleaks, bulguları doğrular. | `claude-opus-5-5` | Read, Grep, Glob, Bash | ✗ | salt-okunur; karar gate.py'de |
| `contract-guard` | Kod ↔ knowledge/contracts/openapi.yaml ve mcp-tools.md uyumunu denetleyen salt-okunur kapı. | `claude-sonnet-5-5` | Read, Grep, Glob, Bash | ✗ | salt-okunur; karar gate.py'de |
| `qa-gate` | İlgili testleri çalıştırır, AC kapsamını ölçer, eksik test senaryolarını metin olarak listeler. Test yazmaz. | `claude-sonnet-5-5` | Read, Grep, Glob, Bash | ✗ | salt-okunur; karar gate.py'de |
| `ui-verifier` | Değişen ekranları Playwright ile gezer: kırık akış, console hatası, axe, responsive. | `claude-haiku-5-5` | Read, Grep, Glob, Bash | ✗ | salt-okunur; karar gate.py'de |
| `backend-reviewer` | Backend diff'ini katman, validasyon, authz, hata, log ve test varlığı açısından inceler (uyarı). | `claude-sonnet-5-5` | Read, Grep, Glob, Bash | ✗ | salt-okunur; karar gate.py'de |
| `observability-coverage` | Yeni endpoint/aksiyonların gerekli metrik ve güvenlik/audit olaylarını ürettiğini denetler (uyarı). | `claude-haiku-5-5` | Read, Grep, Glob, Bash | ✗ | salt-okunur; karar gate.py'de |
| `presenter` | Demo senaryolarını ve sunumu gerçek çıktılara dayanarak hazırlar; her iddiayı doğrular. | `claude-sonnet-5-5` | Read, Grep, Glob, Bash, Write | ✓ | owned_paths (pre_tool_guard G3) |

**Model seçimi gerekçesi:** muhakeme ağırlıklı (plan, güvenlik, backend kodu) → Opus 5.5; kalıplı ama dikkat isteyen (sözleşme, QA, MCP, sunum) → Sonnet 5.5; mekanik ve çok sayıda çalışan kontroller (UI gezinme, observability kapsamı) → Haiku 5.5. Gerçekleşen maliyet `logs/ai-usage.jsonl`'de ölçülür; seçim veriye göre güncellenir.
