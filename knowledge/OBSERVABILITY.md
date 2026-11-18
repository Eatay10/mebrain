# Observability — Cyber Task Hub

Sahibi: C. Yaklaşım: **uygulama içi ekranlar** (varsayılan) + opsiyonel Grafana stack. Agent: `observability-coverage` bu dosyayı referans alır.

## 1. Log

- structlog, JSON, stdout. Her satırda: `ts`, `level`, `service` (api/worker/mcp), `request_id`, `user_id` (varsa), `route`, `method`, `status`, `duration_ms`.
- `X-Request-ID` gelen istekten alınır ya da üretilir; yanıta ve tüm log/audit/security_event kayıtlarına yazılır.
- **Asla loglanmaz:** parola, session ID, CSRF token, API token, `Authorization`/`Cookie` header'ları, task açıklaması/yorum gövdesi (sadece uzunluk).

## 2. Metrikler (prometheus-client, `/metrics` — sadece iç ağ)

| Metrik | Tip | Etiketler |
|---|---|---|
| `http_requests_total` | counter | method, route (şablon), status |
| `http_request_duration_seconds` | histogram | method, route |
| `security_events_total` | counter | type, severity |
| `auth_logins_total` | counter | result (success/failed/locked) |
| `tasks_transitions_total` | counter | from, to |
| `notifications_sent_total` | counter | channel (in_app/email), result |
| `job_runs_total` / `job_duration_seconds` | counter / histogram | job, result |
| `db_pool_in_use` | gauge | |

Uygulama içi ekran için `GET /api/v1/system/metrics-summary` bu metriklerin pencere özetini döner.

## 3. Trace

OpenTelemetry SDK; FastAPI, SQLAlchemy, httpx (MCP→API) otomatik enstrümantasyon. `trace_id` log'a eklenir. Exporter: OTLP (stack açıksa) veya kapalı.

## 4. Audit olayları (`audit_logs`)

`auth.login`, `auth.logout`, `user.create`, `user.update`, `user.role_change`, `user.deactivate`, `team.create`, `team.update`, `project.create|update|delete`, `task.create|update|transition|delete`, `comment.create`, `event.create|update|delete`, `participation.request|decide`, `competency.create`, `user_competency.upsert|verify|delete`, `announcement.create|delete`, `api_token.create|revoke`, `report.export`, `audit.export`.

## 5. Güvenlik olayları (`security_events`)

| Tip | Severity | Ne zaman |
|---|---|---|
| LOGIN_SUCCESS | INFO | Başarılı giriş |
| LOGIN_FAILED | LOW | Hatalı parola / bilinmeyen kullanıcı |
| ACCOUNT_LOCKED | MEDIUM | 5. hatalı denemede |
| LOGOUT / SESSION_EXPIRED | INFO | |
| CSRF_REJECTED | MEDIUM | Eksik/yanlış CSRF token |
| AUTHZ_DENIED | MEDIUM | Policy reddi (403) |
| NOT_FOUND_PROBE | LOW | Kapsam dışı kaynağa erişim denemesi (404 olarak dönen) |
| VALIDATION_REJECTED | INFO | 400 (sadece alan adları, değer yok) |
| PAYLOAD_TOO_LARGE | LOW | 413 |
| RATE_LIMITED | LOW | 429 |
| ROLE_CHANGED | HIGH | Rol değişikliği |
| USER_DEACTIVATED | MEDIUM | |
| API_TOKEN_CREATED / API_TOKEN_REVOKED | INFO | |
| API_TOKEN_INVALID | MEDIUM | Geçersiz/süresi dolmuş/iptal token |
| BULK_EXPORT | MEDIUM | CSV rapor / audit export |

## 6. Alarm kuralları (`/security/summary.openAlerts`)

| Kural | Koşul | Severity |
|---|---|---|
| `brute_force` | Aynı IP'den 1 dk'da ≥ 5 LOGIN_FAILED | HIGH |
| `account_lockout` | ACCOUNT_LOCKED | MEDIUM |
| `authz_burst` | Aynı kullanıcıdan 5 dk'da ≥ 10 AUTHZ_DENIED veya NOT_FOUND_PROBE (IDOR taraması) | HIGH |
| `privilege_change` | ROLE_CHANGED → DIRECTOR | HIGH |
| `token_abuse` | Aynı IP'den 5 dk'da ≥ 10 API_TOKEN_INVALID | HIGH |
| `mass_export` | Aynı kullanıcıdan 1 saatte ≥ 5 BULK_EXPORT | MEDIUM |

## 7. Ekranlar (web, sadece direktör)

1. **Sistem Sağlığı** — servis durumu, uptime, iş (job) durumları
2. **API Performansı** — route bazında istek, hata oranı, p50/p95/p99
3. **Güvenlik Olayları** — zaman çizelgesi, tipe göre dağılım, en çok tetikleyen IP'ler, filtreler
4. **Audit Trail** — arama, filtre, CSV export
5. **Alarmlar** — açık alarm listesi

## 8. Trafik simülatörü

`scripts/simulate_traffic.py` — sadece `localhost` ve seed hesaplarıyla: normal kullanım + brute force + IDOR taraması + büyük payload + rate limit patlaması + geçersiz token. Her alarm kuralını en az bir kez tetikler; demo ve QA için.
