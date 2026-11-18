---
description: TASK-NNN'i orkestrasyonla uygula: planla, uygula, gate'le, kapat.
argument-hint: <TASK-ID>
---

Argüman: $ARGUMENTS (ör. TASK-001). Süreç: knowledge/process/orchestration.md — adımları atlama.

1. `tasks/$ARGUMENTS.md` oku. `depends_on` içindeki her TASK `status: DONE` değilse dur ve söyle.
2. `.claude/state/active-task` dosyasına `$ARGUMENTS` yaz; TASK `status: IN_PROGRESS`; Kayıt tablosuna satır ekle.
3. **task-planner** subagent'ını çağır; planı TASK'ın "Uygulama planı" bölümüne yaz. TASK 3 saatten büyükse planı kullanıcıya göster ve onay bekle.
4. Plan adımlarını TASK'ın `agent` alanındaki subagent'a ver (backend ve frontend adımları bağımsızsa paralel).
5. Implementer bitince **paralel** çalıştır: security-gate, contract-guard, qa-gate (+ apps/web değiştiyse ui-verifier; apps/api değiştiyse backend-reviewer, observability-coverage). Verdict JSON'larını `reports/agents/<agent>/$ARGUMENTS.json` olarak kaydet ve `python3 scripts/gate.py reports/agents/*/$ARGUMENTS.json` çalıştır.
6. FAIL → bulguları implementer'a geri ver (en fazla 2 tur); hâlâ FAIL ise dur ve kullanıcıya özetle.
7. PASS → AC checklist'ini işaretle (her AC için hangi test), TASK `status: REVIEW`, `tasks/BOARD.md` satırını güncelle, `.claude/state/active-task`'ı temizle.
8. Commit önerisi: `TASK-NNN: <özet>` + `Co-Authored-By` trailer'ı. Commit'i kullanıcı onaylar.
