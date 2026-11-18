# ADR-0004: Arka plan işleri

- Durum: **Önerildi**
- Tarih: 2026-11-18

## Karar

`worker` ayrı bir process (`python -m app.worker`), API ile aynı kod tabanını ve DB'yi kullanır. Zamanlama APScheduler; iş kalıcılığı `jobs` tablosu (`SELECT … FOR UPDATE SKIP LOCKED`). Redis yok.

| İş | Sıklık | Ne yapar |
|---|---|---|
| `generate_recurring_tasks` | Her gün 00:05 (+ başlangıçta) | `recurrence != NONE` şablon task'lardan o günün örneklerini üretir (idempotent: `recurrence_parent_id + occurrence_date` unique) |
| `due_soon_notifications` | Saatte bir | 24 saat içinde son tarihi gelen, DONE olmayan task'lar için assignee + backup'a bildirim (task başına bir kez) |
| `overdue_notifications` | Her gün 09:00 | Gecikmiş task'lar için assignee + yönetici bildirimi |
| `send_email_notifications` | Dakikada bir | `notifications.email_status = PENDING` olanları gönderir; 3 deneme, sonra FAILED |
| `cleanup_sessions` | Saatte bir | Süresi dolmuş session'ları siler |
| (N) `weekly_report` | Pazartesi 08:00 | Yönetici/direktöre haftalık özet e-postası |
| (N) `certificate_expiry` | Her gün | 30 gün içinde biten sertifikalar için bildirim |

## Kurallar
- Her iş idempotent; yeniden çalışması kopya üretmez.
- Her çalışma `job_runs` metriği ve yapısal log üretir (süre, işlenen kayıt, hata).
- Worker hiçbir zaman kullanıcı yetkisiyle değil, **sistem aktörü** (`actor = system`) olarak audit log yazar.
