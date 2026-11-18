# R-CORE — Temel kurallar

Her kural **ölçülebilir**: "Kontrol" sütunu kuralı hangi araç/hook/agent'ın doğruladığını söyler.

| ID | Kural | Kontrol |
|---|---|---|
| R-CORE-01 | Her kod değişikliği bir `tasks/TASK-NNN.md`'ye bağlıdır; commit mesajı `TASK-NNN:` ile başlar. | `hooks/git/commit-msg` |
| R-CORE-02 | Sadece TASK dosyasının `owned_paths` listesindeki dosyalar değiştirilir. | `hooks/claude/pre_tool_guard.py` (aktif TASK varken) |
| R-CORE-03 | Mimari karar değişikliği önce `adr/` altında yeni ADR ile yapılır; kod ADR'ye referans verir. | contract-guard / review |
| R-CORE-04 | API sözleşmesinde olmayan endpoint yazılmaz/çağrılmaz. | contract-guard |
| R-CORE-05 | Bir iş "bitti" denmeden önce TASK'ın kabul kriterlerinin her biri çalıştırılmış bir testle doğrulanır. | qa-gate |
| R-CORE-06 | Gizli bilgi (parola, token, anahtar) repoya, log'a, prompt geçmişine yazılmaz. | gitleaks (pre-commit) + `hooks/claude/prompt_log.py` redaksiyonu |
| R-CORE-07 | Sadece sentetik veri; gerçek kişi/IP/kurum verisi yok (KVKK). | security-gate |
| R-CORE-08 | Dosya başına en fazla 400 satır, fonksiyon başına en fazla 50 satır (istisna gerekçesiyle). | ruff (PLR0915), eslint `max-lines` |
| R-CORE-09 | Yeni bağımlılık eklemek için TASK'ta gerekçe yazılır; lisansı MIT/Apache/BSD olmalı. | security-gate (trivy license) |
| R-CORE-10 | Ajan, belirsizlikte tahmin etmez: TASK'ın "Açık sorular" bölümüne yazar ve durur. | review |
