# Görev Planı — Cyber Task Hub

Sahibi: A. Kurallar: her görev bir sahibe ve **dosya/dizin listesine** bağlıdır; başkasının dizinine PR'sız dokunulmaz. Durum: `TODO` · `DOING` · `REVIEW` · `DONE` · `BLOCKED`. Branch: `feat/<kişi>-<görev-id>`. PR öncesi `/pre-pr`.

Ekip: **A** Tech Lead + Backend · **B** Frontend · **C** Security + Observability (+ MCP, API token, audit) · **D** QA + Sunum (+ seed, etkinlik/yetkinlik backend'i)

## Kilometre taşları (24 saate göre; süreye oranla)

| Taş | Zaman | Çıkış kriteri |
|---|---|---|
| **M0** Sözleşmeler | 0–2 sa | Bu dokümanlar ekipçe onaylı; stack kararı (ADR-0001) kesin |
| **M1** İskelet | 2–6 sa | `docker compose up` → login çalışır, boş dashboard açılır, CI + gate'ler yeşil |
| **M2** Dikey dilim | 6–10 sa | Task oluştur → ata → durum değiştir → dashboard sayısı değişir (web + API + test) |
| **M3** Tüm MUST'lar | 10–15 sa | REQUIREMENTS'taki tüm M maddeleri uçtan uca |
| **M4** Entegrasyon | ~15 sa | Seed'li tam demo akışı, MCP canlı, güvenlik ekranı canlı |
| **M5** Freeze | ~20 sa | `release-readiness` yeşil, yeni özellik yok |
| **M6** Sunum | 20–24 sa | Prova ×2, yedek video, `pitch-fact-checker` temiz |

## Görevler

### A — Backend çekirdeği

| ID | Görev | Dosyalar | Bağımlılık | Kabul | Taş | Durum |
|---|---|---|---|---|---|---|
| BE-01 | FastAPI iskeleti: config (env), problem+json hata işleyici, request ID, security header'lar, body limit 256 KB, CORS allowlist, `/health` `/ready`, structlog | `apps/api/pyproject.toml`, `apps/api/app/main.py`, `apps/api/app/core/**` | — | SEC-ERR-01, SEC-HDR-01 | M1 | TODO |
| BE-02 | SQLAlchemy modelleri + Alembic ilk migration (DATA_MODEL.md'nin tamamı), audit_logs için kısıtlı DB yetkisi | `apps/api/app/models/**`, `apps/api/migrations/**`, `infra/db/init.sql` | BE-01 | AUD-01-b | M1 | TODO |
| BE-03 | Auth: login/logout/me, sunucu tarafı session, CSRF, argon2id, kilitleme, login rate limit | `apps/api/app/auth/session.py`, `apps/api/app/auth/csrf.py`, `apps/api/app/auth/passwords.py`, `apps/api/app/modules/auth/**` | BE-02 | AUT-01-a, AUT-03-* | M1 | TODO |
| BE-04 | **RBAC policy + kapsam filtreleri**; Tasks CRUD, transitions, comments, history, filtre/sıralama, optimistic locking | `apps/api/app/auth/policies.py`, `apps/api/app/auth/scope.py`, `apps/api/app/modules/tasks/**` | BE-03 | TSK-*, AUT-02-* | M2 | TODO |
| BE-05 | Users & Teams uç noktaları, rol değişikliği kuralları, pasifleştirmede session iptali | `apps/api/app/modules/users/**`, `apps/api/app/modules/teams/**` | BE-04 | AUT-04-* | M3 | TODO |
| BE-07 | Projects (ilerleme hesaplı) + Announcements | `apps/api/app/modules/projects/**`, `apps/api/app/modules/announcements/**` | BE-04 | PRJ-*, COM-* | M3 | TODO |
| BE-09 | Dashboard summary (tek sorguda `COUNT FILTER`) + Reports (JSON/CSV, CSV injection koruması) | `apps/api/app/modules/dashboard/**`, `apps/api/app/modules/reports/**` | BE-04 | DSH-*, RPT-* | M2/M3 | TODO |
| A-DOC | Sözleşme bakımı, ADR'ler, PR review, entegrasyon (M4), `release-readiness` sahibi | `docs/**` | — | contract-guard yeşil | sürekli | DOING |

### B — Frontend

| ID | Görev | Dosyalar | Bağımlılık | Kabul | Taş | Durum |
|---|---|---|---|---|---|---|
| FE-00 | `packages/api-client`: openapi.yaml'dan tip + client üretimi (`pnpm gen:api`) | `packages/api-client/**` | M0 | API-01-a | M1 | TODO |
| FE-01 | SPA iskeleti: Vite + TS strict, router, layout (sidebar/topbar), tema (açık/koyu), auth akışı + CSRF, rol bazlı menü, error boundary, toast, CSP uyumlu build, MSW mock'ları (`src/mocks`, demo build'de kapalı) | `apps/web/**` (aşağıdaki sayfalar hariç), `apps/web/src/app/**`, `apps/web/src/components/ui/**` | FE-00 | NFR-UX-01, SEC-XSS-01 | M1 | TODO |
| FE-02 | **Dashboard**: ekip kartları (todo/devam/bloklu/tamam/gecikmiş), Standart/Proje sekmesi, kişisel özet, proje ilerleme kartları, sayıya tıkla → filtreli liste | `apps/web/src/pages/dashboard/**` | FE-01, BE-09 | DSH-* | M2 | TODO |
| FE-03 | **Task'lar**: liste (filtre, arama, sıralama, sayfalama), detay, oluştur/düzenle formu, durum geçişi, yorumlar, geçmiş, rutin şablonlar | `apps/web/src/pages/tasks/**` | FE-01, BE-04 | TSK-* | M2 | TODO |
| FE-04 | Projeler: liste + detay (proje task'ları, ilerleme) + form | `apps/web/src/pages/projects/**` | BE-07 | PRJ-* | M3 | TODO |
| FE-05 | Etkinlikler: liste (bireysel/kurumsal filtre), detay, katılım talebi, onay kuyruğu (yönetici) | `apps/web/src/pages/events/**` | BE-08 | EVT-* | M3 | TODO |
| FE-06 | Yetkinlikler: profilim (seviye/kanıt), ekip matrisi (yönetici), doğrulama | `apps/web/src/pages/competencies/**` | BE-08 | CMP-* | M3 | TODO |
| FE-07 | Raporlar: groupBy + tarih aralığı, tablo + grafik, CSV indir | `apps/web/src/pages/reports/**` | BE-09 | RPT-* | M3 | TODO |
| FE-08 | Bildirim zili (okunmamış sayısı, liste, okundu) + Duyurular sayfası | `apps/web/src/pages/notifications/**`, `apps/web/src/pages/announcements/**` | BE-10, BE-07 | NTF-01-c, COM-* | M3 | TODO |
| FE-09 | Yönetim: kullanıcılar, ekipler, rol değiştirme (direktör); Profil → API token'ları | `apps/web/src/pages/admin/**`, `apps/web/src/pages/settings/**` | BE-05, BE-11 | AUT-04-*, API-02-a | M3 | TODO |

### C — Security, Observability, Entegrasyon yüzeyi

| ID | Görev | Dosyalar | Bağımlılık | Kabul | Taş | Durum |
|---|---|---|---|---|---|---|
| OPS-01 | Monorepo, `docker-compose.yml` (db, api, worker, web, mcp-http, mailpit), Dockerfile'lar (root olmayan kullanıcı), `.env.example`, Makefile | `docker-compose.yml`, `apps/*/Dockerfile`, `.env.example`, `Makefile` | — | NFR-OPS-01 | M1 | TODO |
| OPS-02 | CI + agent altyapısı: lint/typecheck/test, gitleaks/semgrep/trivy, `.claude/agents/*`, `/pre-pr`, `agents.yml`, `scripts/gate.py`, branch protection | `.github/**`, `.claude/**`, `scripts/gate.py`, `scripts/save-verdict.sh`, `.pre-commit-config.yaml` | OPS-01 | Kötü PR örneği bloklanır | M1 | TODO |
| BE-06 | Audit log + security_events altyapısı (middleware/servis), task history | `apps/api/app/audit/**`, `apps/api/app/security_events/**` | BE-02 | AUD-01-*, SEC-AUD-01 | M2 | TODO |
| BE-11 | API token'ları: oluştur/listele/iptal, Bearer auth, scope ∩ rol | `apps/api/app/auth/tokens.py`, `apps/api/app/modules/api_tokens/**` | BE-03 | API-02-* | M3 | TODO |
| BE-10 | Bildirimler (servis + uç noktalar) + **worker** (tekrarlayan task, due soon, overdue, e-posta, session temizliği) | `apps/api/app/modules/notifications/**`, `apps/api/app/worker/**`, `apps/api/app/email/**` | BE-04 | NTF-*, TSK-06-* | M3 | TODO |
| MCP-01 | MCP sunucusu (stdio + Streamable HTTP), ADR-0003 araç listesi, untrusted içerik işaretleme | `apps/mcp/**` | BE-11 | API-03-* | M4 | TODO |
| OB-01 | Metrikler, OTel, log maskeleme, `/security/events`, `/security/summary` (alarm kuralları), `/system/metrics-summary` | `apps/api/app/observability/**`, `apps/api/app/modules/security/**` | BE-06 | OBS-01-*, SEC-LOG-01 | M3 | TODO |
| OB-02 | Observability ekranları (B'nin UI kit'iyle) | `apps/web/src/pages/observability/**` | OB-01, FE-01 | OBS-01-a | M4 | TODO |
| OB-03 | `scripts/simulate_traffic.py` | `scripts/simulate_traffic.py` | OB-01 | OBS-01-a | M4 | TODO |
| SEC-01 | THREAT_MODEL bakımı, security-gate sahipliği, %60'ta tam denetim, güvenlik regresyon testleri | `docs/THREAT_MODEL.md`, `tests/security/**` | — | Açık Critical/High yok | sürekli | TODO |

### D — QA, Seed, Etkinlik/Yetkinlik backend'i, Sunum

| ID | Görev | Dosyalar | Bağımlılık | Kabul | Taş | Durum |
|---|---|---|---|---|---|---|
| QA-01 | Test altyapısı: pytest fixture'ları (rol başına client), Playwright projesi, traceability matrisi | `apps/api/tests/conftest.py`, `tests/e2e/**`, `reports/qa/TRACEABILITY.md` | BE-01 | — | M1 | TODO |
| SEED-01 | Deterministik seed: 4 ekip, 1 direktör, 3 yönetici, ~40 çalışan, ~600 task (standart + proje + rutin), 15 proje, 20 etkinlik, yetkinlik kataloğu | `apps/api/app/seed/**` | BE-02 | DSH-01-a | M2 | TODO |
| BE-08 | Events + participations + competencies + matrix uç noktaları | `apps/api/app/modules/events/**`, `apps/api/app/modules/competencies/**` | BE-04 | EVT-*, CMP-* | M3 | TODO |
| QA-02 | API testleri: ACCEPTANCE.md'deki tüm M kriterleri (yetki matrisi öncelikli) | `apps/api/tests/**` (conftest hariç) | modüller | qa-gate | M2–M4 | TODO |
| QA-03 | E2E: login → dashboard → task yaşam döngüsü → rapor CSV → etkinlik onayı → MCP sorgusu | `tests/e2e/**` | M3 | — | M4 | TODO |
| PRS-01 | Demo script, pitch, Archify diyagramı, yedek video | `docs/presentation/**` | M4 | pitch-fact-checker | M5–M6 | TODO |

> BE-08'i D yazdığı için bu modülün testlerini C çapraz gözden geçirir (QA bağımsızlığı).

## Kritik yol

`BE-01 → BE-02 → BE-03 → BE-04 → BE-09 → FE-02` (dashboard) — gecikirse M2'yi ve demoyu doğrudan etkiler. A önce bu zinciri tamamlar; B bu sürede MSW mock'larıyla FE-01/02/03'ü ilerletir.

## Kapsam kesme sırası (zaman yetmezse, önce kesilen en üstte)

1. FE-06 ekip matrisi görünümü (profil ekranı kalır)
2. OB-02'de API performans ekranı (güvenlik ekranı kalır)
3. Duyurular (bildirimler kalır)
4. E-posta bildirimi (uygulama içi kalır)
5. MCP Streamable HTTP (stdio kalır)
