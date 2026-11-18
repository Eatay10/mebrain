# Orkestrasyon — "TASK-001'i implement et" dedikten sonra ne oluyor?

Tetikleyici: `/implement-task TASK-001` (`commands/implement-task.md`). Ana oturum **orkestratördür**; kodu ve kontrolleri rolleri ve yetkileri sınırlı subagent'lara (`agents/`) dağıtır.

```mermaid
sequenceDiagram
  autonumber
  actor Dev as Geliştirici
  participant O as Orkestratör (ana oturum)
  participant H as hooks/
  participant P as task-planner
  participant BI as backend-implementer
  participant FI as frontend-implementer
  participant G as Gate agent'ları
  participant L as history/ + logs/

  Dev->>O: /implement-task TASK-001
  H->>L: UserPromptSubmit → prompt kaydı (redakte)
  O->>O: TASK-001 oku; deps DONE mu? status=IN_PROGRESS; .claude/state/active-task yaz
  O->>P: planla (TASK + knowledge + adr)
  P-->>O: adım planı, dokunulacak dosyalar ⊆ owned_paths, AC→test eşlemesi
  par Paralel uygulama
    O->>BI: backend adımları
    BI->>H: Edit/Write → PreToolUse: owned_paths & secret kontrolü
    H-->>BI: izin / ret (exit 2)
    BI-->>O: diff + çalışan testler
  and
    O->>FI: frontend adımları
    FI-->>O: diff + Playwright sonucu
  end
  O->>G: security-gate, contract-guard, qa-gate, ui-verifier (paralel, salt-okunur)
  G-->>O: JSON verdict'ler → scripts/gate.py
  alt gate FAIL
    O->>BI: bulguları düzelt (en fazla 2 tur)
  end
  O->>O: AC checklist'i doldur; TASK status=REVIEW; BOARD.md güncelle
  O->>Dev: özet + commit önerisi (TASK-001: …)
  H->>L: Stop → model, token, maliyet, değişen satırlar → logs/ai-usage.jsonl
```

## Adımlar ve garantiler

| # | Adım | Kim | Garanti (deterministik) |
|---|---|---|---|
| 1 | TASK okunur, bağımlılıklar kontrol edilir | orkestratör | `depends_on` DONE değilse durur |
| 2 | Aktif task işaretlenir | orkestratör | `.claude/state/active-task` → hook'lar `owned_paths`'i buradan okur |
| 3 | Plan | `task-planner` (salt-okunur) | Plan TASK'a "Uygulama planı" olarak yazılır |
| 4 | Uygulama | `backend-implementer` / `frontend-implementer` / `mcp-implementer` | `pre_tool_guard.py`: owned_paths dışı yazma, secret, yasak dosya → **ret** |
| 5 | Test | implementer | Testler çalıştırılmadan adım tamam sayılmaz (R-CORE-05) |
| 6 | Gate'ler | salt-okunur gate agent'ları | Karar `scripts/gate.py` (agent yazısı değil) |
| 7 | Düzeltme döngüsü | implementer | Maks. 2 tur; sonra insana eskalasyon |
| 8 | Kapanış | orkestratör | AC checklist, BOARD, `history/` özeti |
| 9 | Commit | geliştirici onayıyla | `commit-msg` hook `TASK-NNN:` zorunlu |
| 10 | Ölçüm | hook | `logs/ai-usage.jsonl` satırı |

## İnsanın karar noktaları
- Plan onayı (3 sonrası, büyük TASK'larda)
- Gate FAIL 2 turda çözülmezse
- Commit ve PR
