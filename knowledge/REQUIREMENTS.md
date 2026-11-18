# Gereksinimler — Cyber Task Hub

> Siber Güvenlik ekiplerinin günlük iş yönetimi için task, etkinlik/yetkinlik, raporlama ve veri paylaşımı aracı.
> Kaynak: hackathon gereksinim metni (2026-11-18). Sahibi: A (Architect). Durum: **Taslak v1 — ekip onayı bekliyor**.

## 1. Gereksinim matrisi

Öncelik: **M** = MUST-HAVE (demo için zorunlu), **N** = NICE-TO-HAVE (zaman kalırsa).

| ID | Alan | Gereksinim | Öncelik | Kaynak |
|---|---|---|---|---|
| **TSK-01** | Task | Task oluşturma, düzenleme, silme (soft delete) | M | "Task Yönetimi" |
| TSK-02 | Task | Task'ı bir kişiye atama (assignee) + yedek kişi atama (backup assignee) | M | "yedek işler" (Varsayım A1) |
| TSK-03 | Task | Task türü: **Standart task** veya **Proje task'ı** (proje altında) | M | "Standart task ve proje-taskları" |
| TSK-04 | Task | Durum akışı: Başlanmadı → Devam ediyor → (Bloklu) → Tamamlandı | M | Dashboard metni (Varsayım A2) |
| TSK-05 | Task | Öncelik (Düşük/Orta/Yüksek/Kritik), son tarih, kategori | M | Task takibi |
| TSK-06 | Task | Günlük/haftalık/aylık **tekrarlayan** task'lar (rutin işler) | M | "Günlük işler" (Varsayım A1) |
| TSK-07 | Task | Task yorumları (ekip içi iletişim) | M | "İletişim" |
| TSK-08 | Task | Filtreleme ve arama (ekip, proje, durum, kişi, öncelik, gecikmiş) | M | Takip |
| TSK-09 | Task | Kanban görünümü (sürükle-bırak durum değişimi) | N | — |
| TSK-10 | Task | Dosya eki | N | — |
| **PRJ-01** | Proje | Proje oluşturma/düzenleme/arşivleme; proje altında task'lar | M | "proje-taskları" |
| PRJ-02 | Proje | Proje ilerleme yüzdesi (tamamlanan/toplam task) | M | Dashboard |
| **EVT-01** | Etkinlik | Etkinlik kaydı: konferans, eğitim, CTF, webinar, workshop… | M | "Etkinlik Yönetimi" |
| EVT-02 | Etkinlik | Katılım tipi: **bireysel** veya **kurumsal** | M | "Bireysel ve kurumsal katılım" |
| EVT-03 | Etkinlik | Katılım talebi → yönetici onayı/reddi → katıldı işaretleme | M | "takibi ve yönetimi" |
| EVT-04 | Etkinlik | Etkinlik takvimi görünümü | N | — |
| **CMP-01** | Yetkinlik | Yetkinlik kataloğu (ör. Pentest, SOC, GRC, Cloud Security) | M | "bireysel yetkinlikler" |
| CMP-02 | Yetkinlik | Kişinin yetkinlik seviyesi (1–5) + kanıt; yönetici doğrulaması | M | "takibi ve yönetimi" |
| CMP-03 | Yetkinlik | Sertifika takibi ve bitiş tarihi uyarısı | N | — |
| CMP-04 | Yetkinlik | Ekip yetkinlik matrisi (ısı haritası) | N | — |
| **COM-01** | İletişim | Duyurular: yönetici → ekip, direktör → tüm kurum | M | "İletişim Yönetimi" (Varsayım A3) |
| **AUT-01** | Yetki | Roller: **Çalışan, Yönetici, Direktör, Denetmen** | M | "Yetkilendirme" |
| AUT-02 | Yetki | Kapsam bazlı erişim: çalışan kendi ekibi, yönetici yönettiği ekip(ler), direktör tüm kurum, denetmen tüm kurumu salt-okunur | M | "kullanım yapısı" |
| AUT-03 | Yetki | Giriş/çıkış, oturum yönetimi, brute-force koruması | M | Güvenlik (NFR) |
| AUT-04 | Yetki | Kullanıcı ve ekip yönetimi, rol değişikliği (sadece direktör) | M | — |
| AUT-05 | Yetki | Kurumsal SSO (LDAP/AD, OIDC) | N | Yol haritası |
| **DSH-01** | Dashboard | Ekip bazında task sayıları: başlanmadı / devam ediyor / bloklu / tamamlandı / gecikmiş | M | Dashboard metni |
| DSH-02 | Dashboard | Aynı sayıların **Standart** ve **Proje** task'ı olarak ayrıştırılması | M | Dashboard metni |
| DSH-03 | Dashboard | Role göre kapsam: çalışan kendi ekibi + kişisel, yönetici ekip(ler)i, direktör ve denetmen tüm ekipler | M | AUT-02 |
| DSH-04 | Dashboard | Proje ilerleme kartları, zaman içinde tamamlanma trendi | N | — |
| **RPT-01** | Rapor | Toplu task raporu: ekip / kişi / proje / durum / öncelik bazında, tarih aralığı ile | M | "toplu raporlama" |
| RPT-02 | Rapor | CSV dışa aktarım | M | Raporlama |
| RPT-03 | Rapor | PDF rapor ve zamanlanmış e-posta raporu (haftalık) | N | — |
| **NTF-01** | Bildirim | Uygulama içi bildirim: atama, yedek atama, durum değişimi, yorum, yaklaşan/geçen son tarih, katılım onayı, duyuru | M | "bildirimleri" |
| NTF-02 | Bildirim | E-posta bildirimi (geliştirmede Mailpit) | M | "bildirimleri" |
| NTF-03 | Bildirim | Günlük özet e-postası (digest), bildirim tercihleri | N | — |
| NTF-04 | Bildirim | Teams/Slack webhook | N | — |
| **API-01** | Veri paylaşımı | Versiyonlu REST API, OpenAPI 3.1 sözleşmesi | M | "API veya MCP" |
| API-02 | Veri paylaşımı | Kişisel API token'ları (scope'lu, süreli, iptal edilebilir) | M | API güvenliği |
| API-03 | Veri paylaşımı | **MCP sunucusu**: task, dashboard, rapor, etkinlik araçları; RBAC API üzerinden uygulanır | M | "API veya MCP" (ikisini de yapıyoruz — fark yaratır) |
| API-04 | Veri paylaşımı | Webhook (task olaylarını dış sisteme gönderme) | N | — |
| **AUD-01** | Denetim | Tüm yetkili işlemler için audit log (kim, ne, ne zaman, nereden, önce/sonra) | M | Güvenlik (NFR) |
| OBS-01 | Gözlem | Güvenlik olayları ve sistem sağlığı ekranları | M | Ekip kararı (bkz. `knowledge/OBSERVABILITY.md`) |

## 2. Fonksiyonel olmayan gereksinimler

| ID | Gereksinim | Ölçüt |
|---|---|---|
| NFR-SEC-01 | OWASP ASVS 5.0 L1 + yetkilendirme için L2 | Doğrulanmış Critical/High bulgu yok |
| NFR-SEC-02 | Nesne seviyesi yetki kontrolü her uç noktada | IDOR testleri yeşil |
| NFR-SEC-03 | Parolalar argon2id; secret'lar sadece env | Gitleaks temiz |
| NFR-SEC-04 | Giriş denemesi rate limit + geçici kilit | 5 hatalı deneme / 15 dk |
| NFR-PRF-01 | Liste ve dashboard p95 < 300 ms (demo verisi: ~10 ekip, ~100 kişi, ~5.000 task) | Metrik ekranı |
| NFR-UX-01 | Responsive (375 / 768 / 1440 px), WCAG AA, açık/koyu tema | ui-verifier |
| NFR-UX-02 | Arayüz dili Türkçe (i18n altyapısı ile İngilizce eklenebilir) | — |
| NFR-OPS-01 | Tek komutla ayağa kalkma (`docker compose up`) + seed | release-readiness |
| NFR-PRV-01 | Sadece sentetik veri; kişisel veri minimizasyonu (KVKK) | Seed incelemesi |
| NFR-OBS-01 | Yapısal log, metrik, trace; güvenlik olayları | observability-coverage |

## 3. Varsayımlar ve belirsizlikler

| # | Belirsizlik | Varsayım (karar) | Etkisi değişirse |
|---|---|---|---|
| A1 | "Günlük ve yedek işler" ne demek? | İki anlam birlikte karşılanıyor: **günlük işler** = tekrarlayan rutin task'lar (TSK-06); **yedek** = her task'ta yedek sorumlu (backup assignee) alanı — asıl kişi izinliyse yedek devralır (TSK-02). | Sadece "yedekleme (backup) işleri" kastediliyorsa bu bir task kategorisi olur; model değişmez. |
| A2 | Dashboard metninde "devam ediyor" iki kez geçiyor | Durumlar: **Başlanmadı (TODO)**, **Devam ediyor (IN_PROGRESS)**, **Bloklu (BLOCKED)**, **Tamamlandı (DONE)**; ek olarak türetilmiş **Gecikmiş** (son tarihi geçmiş ve DONE değil). | Bloklu istenmezse UI'da gizlenir. |
| A3 | "İletişim yönetimi" kapsamı | Task yorumları + duyurular + bildirimler. Ayrı bir mesajlaşma/chat yok. | Chat istenirse NICE olarak eklenir. |
| A4 | Bir kişi kaç ekipte? | Her çalışan tek ekipte; bir yönetici birden fazla ekibi yönetebilir; direktör tüm ekiplere erişir. | Çoklu ekip üyeliği gerekirse `team_members` tablosu. |
| A9 | Denetmen rolü ne yapar? | Bağımsız iç denetim / uyum rolü: tüm ekiplerin task, proje, etkinlik, yetkinlik, dashboard, rapor, **audit log ve güvenlik olaylarını** okur ve dışa aktarır; **hiçbir kaydı oluşturamaz, değiştiremez, silemez** (yorum dahil). Ekibe bağlı değildir. API token'ları sadece `:read` scope'lu olabilir. | Yorum/bulgu yazma istenirse ayrı `audit_findings` modülü (NICE). |
| A5 | Sistem yöneticisi rolü | Ayrı admin rolü yok; kullanıcı/ekip yönetimini direktör yapar. Seed ile ilk direktör oluşturulur. | — |
| A6 | Kimlik doğrulama | Yerel kullanıcı/parola (demo). LDAP/AD/OIDC yol haritası (AUT-05). | Kurum SSO zorunlu tutarsa OIDC adaptörü. |
| A7 | MCP kullanım senaryosu | Çalışan/yönetici kendi AI asistanından (Claude vb.) task sorgular, durum günceller, rapor alır. MCP sunucusu kullanıcının API token'ı ile çalışır, **silme aracı yoktur**. | — |
| A8 | Çalışanın task oluşturması | Çalışan sadece kendine atanmış standart task açabilir; başkasına atama ve proje task'ı yönetici+ yetkisi. | — |

## 4. Kapsam dışı (demo için)

Mobil uygulama, çoklu kiracı (multi-tenant), gerçek kurum dizini entegrasyonu, gerçek e-posta gönderimi (Mailpit yakalar), dosya virüs taraması.

## 5. Jüri için fark yaratacak noktalar

1. **MCP + REST birlikte** — "Bu hafta ekibimde geciken kritik task'lar neler?" sorusunu AI asistanına sorup canlı cevap alma.
2. **Güvenlik baştan tasarımda** — RBAC + nesne seviyesi yetki, audit trail, güvenlik olay ekranı, canlı saldırı denemesinin ekranda görünmesi.
3. **Agentic geliştirme süreci** — PR'larda çalışan security-gate / qa-gate agent'larının yakaladığı gerçek bulgular.
