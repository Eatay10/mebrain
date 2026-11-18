# commands/ — Developer'ın hazır komutları

Claude Code'da `/` ile çağrılır (`.claude/commands/` → bu klasör).

| Komut | Ne yapar |
|---|---|
| `/implement-task <TASK-ID>` | TASK-NNN'i orkestrasyonla uygula: planla, uygula, gate'le, kapat. |
| `/pre-pr ` | PR öncesi gate agent'larını paralel çalıştırıp özetler (salt-okunur). |
| `/new-task <kısa açıklama>` | Yeni bir TASK sözleşmesi oluştur (tasks/_TEMPLATE.md formatında). |
| `/new-adr <karar başlığı>` | Yeni mimari karar kaydı (ADR) oluştur. |
| `/ai-stats [--since YYYY-MM-DD] [--task TASK-NNN]` | AI kullanım ve katkı istatistiklerini göster (model, token, maliyet, AI katkı oranı). |
