# Mimari — Cyber Task Hub

Durum: **Taslak v1**. Kararlar: `adr/`. Sözleşme: `knowledge/contracts/openapi.yaml`.

## 1. Bileşenler

```mermaid
flowchart LR
  subgraph Client["İstemciler (güvenilmez)"]
    B["Tarayıcı<br/>React SPA"]
    AI["AI asistanı<br/>(Claude vb.)"]
    EXT["Dış sistemler<br/>(SIEM, BI)"]
  end

  subgraph Edge["TB1 — Ağ sınırı"]
    W["web<br/>Vite build + nginx"]
  end

  subgraph App["Uygulama katmanı"]
    API["api<br/>FastAPI — REST /api/v1"]
    MCP["mcp<br/>MCP sunucusu<br/>(stdio + Streamable HTTP)"]
    WK["worker<br/>zamanlanmış işler<br/>(tekrarlayan task, son tarih, bildirim)"]
  end

  subgraph Data["TB3 — Veri katmanı"]
    DB[("PostgreSQL 17")]
    MP["Mailpit<br/>(SMTP, dev)"]
  end

  subgraph Obs["Gözlemlenebilirlik"]
    OT["OpenTelemetry"]
  end

  B -- "HTTPS, session cookie + CSRF" --> W
  W -- "/api/*" --> API
  AI -- "MCP (stdio/HTTP)" --> MCP
  MCP -- "Bearer API token (TB2)" --> API
  EXT -- "Bearer API token (TB2)" --> API
  API --> DB
  WK --> DB
  WK --> MP
  API -. "trace/metric/log" .-> OT
  WK -. .-> OT
  MCP -. .-> OT
```

| Bileşen | Sorumluluk | Not |
|---|---|---|
| `apps/web` | SPA: dashboard, task/proje, etkinlik, yetkinlik, rapor, bildirim, duyuru, yönetim, observability ekranları | Sadece `openapi.yaml`'dan üretilmiş client ile API'ye konuşur |
| `apps/api` | Tüm iş kuralları, **tüm yetkilendirme kararları**, audit log, güvenlik olayları, metrik | Tek yetki noktası; web/MCP/dış sistem fark etmez |
| `apps/api` → `worker` (ayrı process, aynı kod tabanı) | Tekrarlayan task üretimi, son tarih yaklaşan/geçen bildirimleri, e-posta gönderimi, (N) haftalık rapor | DB tabanlı iş kuyruğu (ADR-0004) |
| `apps/mcp` | MCP araçlarını REST API çağrılarına çevirir | **DB'ye doğrudan erişmez**; kullanıcının API token'ı ile çalışır |
| PostgreSQL | Kalıcı veri | Tek şema, Alembic migration |
| Mailpit | Geliştirme/demoda e-postaları yakalar | Gerçek SMTP yok |

## 2. Katmanlar (api)

```
routers (HTTP, şema doğrulama, auth bağımlılığı)
   → services (iş kuralları, yetki kararları: policy fonksiyonları)
      → repositories (SQLAlchemy sorguları, kapsam filtreleri)
         → models (SQLAlchemy ORM)
cross-cutting: auth/session, rbac/policies, audit, security_events, notifications, observability
```

Kural: Yetki kontrolü **service katmanında** `policies.py` üzerinden yapılır; repository'ler kapsam filtresini (`visible_task_filter(user)`) her listeleme sorgusuna uygular. Router'da iş kuralı yok.

## 3. Güven sınırları (trust boundaries)

| ID | Sınır | Kimlik | Ana kontroller |
|---|---|---|---|
| TB1 | Tarayıcı → web/api | Session cookie (`HttpOnly`, `Secure`, `SameSite=Lax`) | CSRF token (double submit), CORS allowlist, security header'lar, rate limit |
| TB2 | MCP / dış sistem → api | Kişisel API token (Bearer, hash'li saklanır, scope'lu, süreli) | Scope kontrolü + kullanıcının rol kapsamı, token başına rate limit |
| TB3 | api/worker → DB | DB kullanıcısı (env) | Parametreli sorgular (ORM), en az yetkili DB kullanıcısı |
| TB4 | AI asistanı → MCP | Yerel kullanıcı (stdio) veya token (HTTP) | Task içerikleri **güvenilmez veri** olarak işaretlenir; silme aracı yok; yazma araçları ayrı scope |
| TB5 | worker → e-posta | SMTP | Şablonlarda HTML escape, alıcı = sistemdeki kullanıcı |

## 4. Yetkilendirme modeli (özet — detay ADR-0002)

| Kaynak | Çalışan | Yönetici | Direktör | Denetmen |
|---|---|---|---|---|
| Task okuma | Kendi ekibi | Yönettiği ekipler | Tümü | Tümü |
| Task oluşturma | Sadece kendine, standart | Ekip(ler)inde, her tür | Tümü | — |
| Task güncelleme | Assignee/backup olduğu task'ın durumu + yorum | Ekip(ler)indeki tüm alanlar | Tümü | — |
| Task silme | — | Ekip(ler)inde | Tümü | — |
| Proje | Okuma (kendi ekibi) | CRUD (ekip(ler)i) | CRUD (tümü) | Okuma (tümü) |
| Dashboard / rapor | Kendi ekibi + kişisel | Ekip(ler)i | Tüm kurum | Tüm kurum (okuma + CSV) |
| Etkinlik | Okuma, bireysel etkinlik oluşturma, kendine katılım talebi | + ekip üyelerinin katılımını onaylama | + kurumsal etkinlik, tüm onaylar | Okuma |
| Yetkinlik | Kendi seviyesini girme | Ekip üyelerini doğrulama, katalog ekleme | Tümü | Okuma (tümü) |
| Duyuru | Okuma | Ekibine yayınlama | Kuruma yayınlama | Okuma |
| Kullanıcı / ekip / rol | Kendi profili | Ekip üyelerini okuma | CRUD + rol değişikliği | Okuma (tümü) |
| Audit log | — | Ekip(ler)i | Tümü | Tümü |
| Güvenlik olayları ekranı | — | — | Tümü | Tümü |

## 5. Temel akışlar

### 5.1 Task durum değişikliği

```mermaid
sequenceDiagram
  actor U as Çalışan
  participant W as web
  participant A as api
  participant D as DB
  participant K as worker
  U->>W: "Devam ediyor" seç
  W->>A: POST /api/v1/tasks/{id}/transitions {to: IN_PROGRESS} + CSRF
  A->>A: session → user; policy.can_transition(user, task, to)
  A->>D: UPDATE task SET status, started_at, version+1 WHERE id AND version
  A->>D: INSERT audit_log, notification (oluşturan + yönetici)
  A-->>W: 200 Task
  K->>D: (periyodik) e-posta bildirimlerini gönder
```

### 5.2 MCP ile sorgu

```mermaid
sequenceDiagram
  actor U as Kullanıcı
  participant AI as AI asistanı
  participant M as mcp
  participant A as api
  U->>AI: "Ekibimde geciken kritik task'lar?"
  AI->>M: tool: search_tasks {overdue: true, priority: CRITICAL}
  M->>A: GET /api/v1/tasks?overdue=true&priority=CRITICAL (Bearer token)
  A->>A: token → user + scope; rol kapsamı filtresi
  A-->>M: 200 sayfalı liste
  M-->>AI: yapılandırılmış sonuç (içerik "untrusted" etiketli)
```

## 6. Dağıtım (demo)

`docker compose up` → `db`, `api`, `worker`, `web`, `mcp-http`, `mailpit` (+ opsiyonel observability stack). Seed: 1 direktör, 1 denetmen, 3 yönetici, 4 ekip (SOC, Pentest, GRC, Zafiyet Yönetimi), ~40 çalışan, ~600 task, 15 proje, 20 etkinlik, yetkinlik kataloğu. Tüm veriler sentetik.

## 7. Repo yapısı

```
apps/
  api/        FastAPI + worker   (sahip: A)
  web/        React SPA          (sahip: B)
  mcp/        MCP sunucusu       (sahip: A, destek C)
packages/
  api-client/ openapi.yaml'dan üretilen TS client (sahip: B, üretim script'i)
docs/         sözleşmeler (sahip: A)
tests/
  e2e/        Playwright         (sahip: D)
  security/   güvenlik regresyon testleri (sahip: C/D)
scripts/      seed, simulate-traffic, gate.py
.claude/      agent tanımları, /pre-pr
.github/      CI + agent workflow'ları
```
