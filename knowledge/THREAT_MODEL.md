# Threat Model — Cyber Task Hub

Sahibi: C (taslak A). Yöntem: güven sınırı başına STRIDE. Sınırlar: `knowledge/ARCHITECTURE.md` §3. Her kontrol bir task'a (`docs/TASKS.md`) ve en az bir teste (`knowledge/ACCEPTANCE.md`) bağlıdır.

## 1. Varlıklar

| Varlık | Neden önemli |
|---|---|
| Task / proje içerikleri | Olay müdahale, zafiyet, pentest detayları → **hassas operasyonel bilgi** |
| Kullanıcı rolleri ve ekip atamaları | Yetki yükseltme hedefi |
| Session'lar ve API token'ları | Hesap ele geçirme |
| Audit log | İnkâr edilemezlik, soruşturma |
| Yetkinlik / etkinlik verileri | Kişisel veri (KVKK) |

## 2. Tehditler ve kontroller

| ID | Sınır | STRIDE | Tehdit | Kontrol | Task | Test |
|---|---|---|---|---|---|---|
| T01 | TB1 | S | Parola deneme / credential stuffing | Rate limit (10/dk/IP), 5 hata → 15 dk kilit, genel hata mesajı, argon2id | BE-03 | SEC-AUTH-01..03 |
| T02 | TB1 | S | Session hijacking / fixation | HttpOnly+Secure+SameSite cookie, girişte ID yenileme, hareketsizlik süresi, sunucu tarafı iptal | BE-03 | SEC-AUTH-04 |
| T03 | TB1 | T | CSRF ile durum değiştirme | Double-submit CSRF token, SameSite=Lax, CORS allowlist | BE-03 | SEC-CSRF-01 |
| T04 | TB1/TB2 | E | **IDOR**: başka ekibin task/proje/kullanıcısına erişim | Kapsam filtresi her sorguda, policy her işlemde, kapsam dışı → 404 | BE-04 | SEC-AUTHZ-01..06 |
| T05 | TB1/TB2 | E | Yetki yükseltme: çalışanın `assigneeId`/`teamId`/`role` alanlarını değiştirmesi (mass assignment) | `additionalProperties: false`, alan seviyesi policy, rol değişikliği sadece direktör | BE-04, BE-05 | SEC-AUTHZ-07..09 |
| T06 | TB1 | T/I | Stored XSS: task başlığı, açıklama, yorum, duyuru | React varsayılan escape, `dangerouslySetInnerHTML` yasak, Markdown render'da sanitize, CSP | FE-01 | SEC-XSS-01 |
| T07 | TB3 | T | SQL injection (arama `q`, sıralama) | ORM + bind param, `sort` allowlist enum | BE-04 | SEC-INJ-01 |
| T08 | TB1 | I | CSV injection (rapor dışa aktarım) | `=`, `+`, `-`, `@`, tab, CR ile başlayan hücrelere `'` öneki | BE-09 | SEC-CSV-01 |
| T09 | TB2 | S/E | API token sızıntısı / aşırı yetki | Hash'li saklama, tek seferlik gösterim, scope ∩ rol, süre ≤ 90 gün, iptal, `last_used_at` | BE-11 | SEC-TOKEN-01..04 |
| T10 | TB4 | T/E | **Prompt injection**: task açıklamasına yazılmış talimatın AI asistanını yönlendirmesi | MCP'de silme/rol aracı yok, yazma araçları ayrı scope, içerik `untrusted_content` olarak işaretli, araç açıklamalarında uyarı | MCP-01 | SEC-MCP-01 |
| T11 | TB1/TB2 | D | Büyük payload / sayfalama istismarı / pahalı rapor | Body limit 256 KB, `pageSize ≤ 100`, rapor tarih aralığı ≤ 366 gün, rate limit | BE-04, BE-09 | SEC-DOS-01..02 |
| T12 | TB1 | I | Kullanıcı numaralandırma (login, 404 farkları) | Aynı hata ve benzer süre, kapsam dışı = 404 | BE-03 | SEC-AUTH-05 |
| T13 | Tümü | R | Kim ne yaptı inkârı | Append-only audit log (DB yetkisiyle zorlanır), request ID korelasyonu | BE-06 | SEC-AUD-01 |
| T14 | TB1 | I | Hata mesajlarında iç bilgi sızıntısı | Problem+json, stack trace yok, debug kapalı | BE-01 | SEC-ERR-01 |
| T15 | TB5 | T | E-posta şablonunda HTML enjeksiyonu / phishing benzeri içerik | Şablon escape, link sadece uygulama domain'i | BE-10 | SEC-MAIL-01 |
| T16 | Tümü | I | Log'larda secret/kişisel veri | Yapısal log alan allowlist'i, parola/token maskeleme | OB-01 | SEC-LOG-01 |
| T17 | Tedarik | T | Zafiyetli bağımlılık / container | Trivy, kilit dosyaları, slim/alpine image, root olmayan kullanıcı | OPS-02 | CI scanner |
| T18 | Repo | I | Secret commit | Gitleaks (pre-commit + CI), `.env.example` | OPS-02 | CI scanner |
| T19 | TB1 | T | Clickjacking | `X-Frame-Options: DENY` / CSP `frame-ancestors 'none'` | FE-01 | SEC-HDR-01 |
| T20 | TB1 | E | Etkinlik `url` alanında `javascript:` şeması | Şema `^https://` + sunucu doğrulaması | BE-08 | SEC-XSS-02 |

## 3. Güvenlik başlıkları (api ve web)

`Content-Security-Policy: default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'`
`X-Content-Type-Options: nosniff` · `Referrer-Policy: strict-origin-when-cross-origin` · `Permissions-Policy: camera=(), microphone=(), geolocation=()` · `Strict-Transport-Security` (TLS'li ortamda) · `Cache-Control: no-store` (API yanıtları)

## 4. Kabul edilen riskler (demo)

| Risk | Gerekçe |
|---|---|
| TLS yok (localhost) | Demo ortamı; üretimde reverse proxy + TLS |
| MFA yok | Yol haritası (SSO ile birlikte) |
| Dosya eki yok | Zararlı dosya yüzeyi bilinçli olarak kapsam dışı |
