# RBAC kapsam algoritması

Gerekçe: `adr/0002-auth-and-rbac.md`. Kod yeri: `apps/api/app/auth/policies.py`.

```python
def visible_team_ids(user) -> set[UUID] | ALL:
    if user.role in (DIRECTOR, AUDITOR): return ALL
    teams = {user.team_id} if user.team_id else set()
    if user.role == MANAGER: teams |= {t.id for t in teams_managed_by(user.id)}
    return teams

def managed_team_ids(user) -> set[UUID] | ALL:
    if user.role == DIRECTOR: return ALL
    if user.role == MANAGER: return {t.id for t in teams_managed_by(user.id)}
    return set()

def is_read_only(user) -> bool:          # her yazma policy'sinin ilk satırı
    return user.role == AUDITOR

def visible_task_filter(user):          # her task listeleme sorgusunda
    s = visible_team_ids(user)
    return true() if s is ALL else Task.team_id.in_(s)
```

## Policy tablosu (test matrisi olarak da kullanılır)

| Policy | EMPLOYEE | MANAGER | DIRECTOR | AUDITOR |
|---|---|---|---|---|
| `can_read_task` | team ∈ visible | team ∈ visible | ✓ | ✓ (tümü) |
| `can_create_task(t)` | t.type=STANDARD ∧ t.team=own ∧ assignee∈{self,∅} | t.team ∈ managed | ✓ | ✗ |
| `can_update_task(fields)` | ✗ (sadece transition/yorum) | team ∈ managed | ✓ | ✗ |
| `can_transition` | self ∈ {assignee, backup} (DONE→IN_PROGRESS hariç) | team ∈ managed | ✓ | ✗ |
| `can_delete_task` | ✗ | team ∈ managed | ✓ | ✗ |
| `can_comment` | can_read_task | can_read_task | ✓ | ✗ |
| `can_manage_project` | ✗ | team ∈ managed | ✓ | ✗ |
| `can_create_event(scope)` | INDIVIDUAL | INDIVIDUAL | ✓ | ✗ |
| `can_request_participation(u)` | u = self | u ∈ managed members ∪ self | ✓ | ✗ |
| `can_decide_participation(p)` | CANCELLED ∧ p.user=self | p.user ∈ managed members | ✓ | ✗ |
| `can_verify_competency(u)` | ✗ | u ∈ managed members | ✓ | ✗ |
| `can_announce(scope)` | ✗ | TEAM ∧ team ∈ managed | ✓ | ✗ |
| `can_manage_users / change_role` | ✗ | ✗ | ✓ (kendi rolü hariç) | ✗ |
| `can_read_audit` | ✗ | team ∈ managed | ✓ | ✓ (tümü) |
| `can_read_security` | ✗ | ✗ | ✓ | ✓ (tümü) |

Sonuç kodları: kapsam dışı nesne → **404**; kapsam içi ama policy reddi → **403** + `AUTHZ_DENIED`.


Denetmen: `managed_team_ids` = ∅; tüm yazma policy'leri `is_read_only(user)` ise reddeder. Okuma: task, proje, etkinlik, yetkinlik, kullanıcı/ekip, dashboard, rapor (CSV dahil), audit, güvenlik ekranları — tüm kurum.
