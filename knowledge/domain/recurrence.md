# Tekrarlayan task algoritması

Gerekçe: `adr/0004-background-jobs.md`. İş: `generate_recurring_tasks` (her gün 00:05).

```
for tpl in tasks where recurrence != NONE and deleted_at is null:
    for d in occurrences(tpl, last_generated(tpl), today):
        # DAILY: her iş günü (Pzt–Cum) · WEEKLY: tpl.created_at haftanın günü · MONTHLY: ayın aynı günü (ay sonuna kırp)
        insert task(
            type=tpl.type, team_id=tpl.team_id, project_id=tpl.project_id,
            title=tpl.title, description=tpl.description, priority, category,
            assignee_id=tpl.assignee_id, backup_assignee_id=tpl.backup_assignee_id,
            due_date=d, recurrence=NONE,
            recurrence_parent_id=tpl.id, occurrence_date=d,
            created_by=SYSTEM)
        ON CONFLICT (recurrence_parent_id, occurrence_date) DO NOTHING   # idempotent
        notify(TASK_ASSIGNED, assignee)
```

- Worker kapalı kaldıysa geriye dönük en fazla 7 gün üretir (`last_generated` ile).
- Şablon silinirse gelecekteki örnekler üretilmez; mevcut örnekler kalır.
- Assignee pasifse örnek backup'a atanır; ikisi de pasifse atanmadan üretilir ve yöneticiye bildirim gider.
