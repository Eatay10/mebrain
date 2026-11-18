# ADR-0002: Kimlik doğrulama ve yetkilendirme

- Durum: **Önerildi**
- Tarih: 2026-11-18

## Karar

### Kimlik doğrulama
- **Web:** `POST /auth/login` → sunucu tarafı session (`sessions` tablosu, rastgele 256-bit ID, sadece hash'i saklanır). Cookie: `cth_session`, `HttpOnly; Secure; SameSite=Lax; Path=/`. Süre: 8 saat, 30 dk hareketsizlikte sona erer. Girişte session ID yenilenir (fixation koruması).
- **CSRF:** Durum değiştiren her cookie'li istek `X-CSRF-Token` header'ı taşır; değer `GET /auth/me` yanıtında ve `cth_csrf` cookie'sinde (HttpOnly değil) verilir; sunucu session'a bağlı değeri karşılaştırır.
- **API token:** `POST /me/api-tokens` → `cth_<prefix>_<secret>` biçiminde, düz metin **yalnızca bir kez** döner; DB'de SHA-256 hash. Scope'lar: `tasks:read`, `tasks:write`, `projects:read`, `reports:read`, `events:read`, `events:write`, `competencies:read`. Maks. 90 gün, iptal edilebilir, `last_used_at` tutulur.
- **Parola:** argon2id; min. 12 karakter; 5 hatalı deneme → 15 dk kilit + güvenlik olayı.

### Yetkilendirme
- Roller: `EMPLOYEE`, `MANAGER`, `DIRECTOR`, `AUDITOR` (`users.role`).
- **Kapsam (scope) fonksiyonu**, tüm kararların tek kaynağı:
  - `EMPLOYEE` → `{user.team_id}`
  - `MANAGER` → `{t.id | t.manager_id = user.id}` ∪ `{user.team_id}`
  - `DIRECTOR` → tüm ekipler
  - `AUDITOR` → tüm ekipler, **salt-okunur** (her yazma policy'si ret; audit log ve güvenlik olaylarını okur)
- **Policy fonksiyonları** (`app/auth/policies.py`): `can_read_task`, `can_create_task`, `can_update_task(fields)`, `can_transition`, `can_delete_task`, `can_manage_project`, `can_approve_participation`, `can_verify_competency`, `can_change_role` … Her service metodu ilgili policy'yi çağırır; ret → `403` + `security_event(AUTHZ_DENIED)`.
- **Nesne seviyesi:** Kapsam dışı kaynak için `404` döner (varlık bilgisi sızdırmamak için); kapsam içi ama yetkisiz işlem için `403`.
- **Alan seviyesi:** Çalışan task'ta sadece `status` (geçişle) ve yorum değiştirebilir; `assignee_id`, `team_id`, `priority`, `due_date` yönetici+.
- **Rol değişikliği:** Sadece direktör; kendi rolünü değiştiremez; audit + güvenlik olayı (`ROLE_CHANGED`).
- **Denetmen:** `team_id` null; durum değiştiren her istek → `403` + `AUTHZ_DENIED`; CSV/audit export'ları `BULK_EXPORT` güvenlik olayı üretir. Denetmen rolü sadece direktör tarafından atanır ve kaldırılır; denetmen hesabının kendisi audit log'da ayrıca izlenir.
- **API token etkin yetkisi** = token scope'ları ∩ kullanıcının rol yetkileri.

### Durum geçişleri

| Kimden → Kime | Kim |
|---|---|
| TODO → IN_PROGRESS | assignee, backup, yönetici+ |
| IN_PROGRESS → DONE | assignee, backup, yönetici+ |
| TODO/IN_PROGRESS ↔ BLOCKED | assignee, backup, yönetici+ (BLOCKED için `reason` zorunlu) |
| DONE → IN_PROGRESS (yeniden açma) | yönetici+ |

`started_at` ilk IN_PROGRESS'te, `completed_at` DONE'da set edilir. Eşzamanlılık: `version` alanı ile optimistic locking (`409 Conflict`).

## Sonuçlar
- Tüm istemciler (web, MCP, dış sistem) aynı policy'lerden geçer; MCP'ye ayrı yetki mantığı yazılmaz.
- QA ve security-gate, policy tablosunu test matrisi olarak kullanır (`knowledge/ACCEPTANCE.md` §AUT).
