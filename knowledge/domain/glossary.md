# Sözlük

| Türkçe (UI) | İngilizce | Kod / enum |
|---|---|---|
| Çalışan / Yönetici / Direktör / Denetmen | Employee / Manager / Director / Auditor | `Role.EMPLOYEE / MANAGER / DIRECTOR / AUDITOR` |
| Standart task | Standard task | `TaskType.STANDARD` |
| Proje task'ı | Project task | `TaskType.PROJECT` (zorunlu `project_id`) |
| Başlanmadı | To do | `TaskStatus.TODO` |
| Devam ediyor | In progress | `TaskStatus.IN_PROGRESS` |
| Bloklu | Blocked | `TaskStatus.BLOCKED` (+ `blocked_reason`) |
| Tamamlandı | Done | `TaskStatus.DONE` |
| Gecikmiş | Overdue | türetilmiş: `due_date < today AND status != DONE` |
| Yedek sorumlu | Backup assignee | `backup_assignee_id` |
| Rutin (tekrarlayan) iş | Recurring task template | `recurrence != NONE` |
| Bireysel / Kurumsal etkinlik | Individual / Corporate event | `EventScope.INDIVIDUAL / CORPORATE` |
| Katılım talebi | Participation request | `ParticipationStatus.REQUESTED` |
| Yetkinlik seviyesi | Competency level | `1..5` (1 Farkındalık, 2 Temel, 3 Yetkin, 4 İleri, 5 Uzman) |
| Kapsam | Scope | `visible_team_ids(user)` |
| Güvenlik olayı | Security event | `security_events` |
