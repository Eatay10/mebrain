# RBAC kapsam algoritması

Gerekçe: `adr/0002-auth-and-rbac.md`. Kod yeri: `apps/api/app/auth/policies.py`.

Organizasyon (ADR-0005): **Direktör → Unit (UNIT_MANAGER) → Ekip (MANAGER) → Ekip üyesi (EMPLOYEE)**; AUDITOR salt-okunur.

```python
def managed_team_ids(user) -> set[UUID] | ALL:
    if user.role == DIRECTOR: return ALL
    teams = {t.id for t in teams_managed_by(user.id)} if user.role in (MANAGER, UNIT_MANAGER) else set()
    if user.role == UNIT_MANAGER: teams |= {t.id for t in teams_in_units_managed_by(user.id)}
    return teams

def visible_team_ids(user) -> set[UUID] | ALL:
    if user.role in (DIRECTOR, AUDITOR): return ALL
    teams = {user.team_id} if user.team_id else set()
    return teams | managed_team_ids(user)

def is_read_only(user) -> bool:          # her yazma policy'sinin ilk satırı
    return user.role == AUDITOR

def visible_task_filter(user):          # her task listeleme sorgusunda
    s = visible_team_ids(user)
    if s is ALL: return true()
    # ekip kapsamı VEYA kişisel dahil olma (sorumlu, yedek, çalışma arkadaşı, talep sahibi, oluşturan)
    return or_(Task.team_id.in_(s), involved(user.id))

def assignable(user):                   # task atanabilecek kişiler (sorumlu/yedek/çalışma arkadaşı)
    DIRECTOR     -> aktif herkes (denetmen hariç); öncelikle unit yöneticileri
    UNIT_MANAGER -> unit'indeki ekiplerin yöneticileri ve üyeleri
    MANAGER      -> yönettiği ekiplerin üyeleri
    EMPLOYEE     -> kendisi (çalışma arkadaşı olarak ekip arkadaşları)
```

## Policy tablosu (test matrisi olarak da kullanılır)

| Policy | EMPLOYEE | MANAGER / UNIT_MANAGER¹ | DIRECTOR | AUDITOR |
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

¹ UNIT_MANAGER, MANAGER ile aynı policy'lere sahiptir; "yönettiği ekipler" kümesi unit'indeki tüm ekiplerdir.

### TASK-019 ek policy'leri

| Policy | Kim |
|---|---|
| İlerleme güncelle (`updateTaskProgress`) | yönetici+ (kapsamda) veya sorumlu/yedek/çalışma arkadaşı; denetmen 403 |
| Yıldız (`watchTask`) | task'ı görebilen herkes (kendisi için) |
| Ek yükle | yönetici+ veya sorumlu/yedek/çalışma arkadaşı/talep sahibi; sil: yükleyen veya yönetici+ |
| Sertifika ekle | kişinin kendisi, yöneticisi veya direktör |
| Etkinlik fotoğrafı | oluşturan, direktör veya onaylı/katılmış katılımcı; sil: yükleyen, oluşturan, direktör |
| Planlı rapor | yönetici+, denetmen; yalnızca kendi planlarını görür, rapor sahibin kapsamıyla üretilir |
| Proje paydaşı | proje ekibini yöneten (yönetici+) |
| Unit yönetimi | direktör |
