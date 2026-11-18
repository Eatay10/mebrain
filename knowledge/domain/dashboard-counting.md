# Dashboard sayım algoritması

Gereksinim: ekip bazında başlanmadı / devam ediyor / bloklu / tamamlandı (+ gecikmiş), standart ve proje task'ı ayrımıyla. Sözleşme: `GET /dashboard/summary` → `DashboardSummary`.

Tek sorgu, PostgreSQL `FILTER`:

```sql
SELECT t.team_id,
       t.type,
       count(*) FILTER (WHERE t.status = 'TODO')        AS todo,
       count(*) FILTER (WHERE t.status = 'IN_PROGRESS') AS in_progress,
       count(*) FILTER (WHERE t.status = 'BLOCKED')     AS blocked,
       count(*) FILTER (WHERE t.status = 'DONE')        AS done,
       count(*) FILTER (WHERE t.status <> 'DONE' AND t.due_date < CURRENT_DATE) AS overdue,
       count(*) AS total
FROM tasks t
WHERE t.deleted_at IS NULL
  AND t.recurrence = 'NONE'                 -- şablonlar sayılmaz, örnekleri sayılır
  AND t.team_id = ANY(:visible_team_ids)    -- RBAC kapsamı
  AND (:from IS NULL OR t.created_at >= :from)
  AND (:to   IS NULL OR t.created_at <  :to + 1)
GROUP BY GROUPING SETS ((t.team_id, t.type), (t.team_id), (t.type), ());
```

Eşleme: `(team, type)` → `teams[].standard|project`; `(team)` → `teams[].all`; `(type)` → `totals.standard|project`; `()` → `totals.all`. `mine` = aynı sorgu `assignee_id = :me`.

Değişmez: `todo + in_progress + blocked + done = total`; `overdue ⊆ (todo ∪ in_progress ∪ blocked)`. Bu iki eşitlik test edilir.

Performans: indeks `(team_id, status) WHERE deleted_at IS NULL`; 5.000 task'ta hedef p95 < 50 ms.
