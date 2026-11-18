# Handoff — Cyber Task Hub (2026-11-18, akşam)

Yeni oturum önce bunu, sonra `CLAUDE.md` ve `AI-NATIVE.md`'yi okusun. Kökteki eski `HANDOFF.md` (ana checkout'ta, commit'lenmemiş) bu dosyayla geçersizdir.

## Dallar ve checkout'lar

| Dal | Checkout | Durum |
|---|---|---|
| `main` | `/Users/behlultunc/DEV/cyber-task-hub-019` (worktree) | **Güncel ana dal**: TASK-019 + TASK-001'in 3 commit'i birleştirildi, GitHub'a push'lu. Kullanıcının açık isteğiyle doğrudan push edildi (R-GIT-03 bu seferlik atlandı). Çalışan stack buradan kurulu. |
| `task/TASK-019-org-hierarchy` | — | GitHub'da; `main`'e birleşti. |
| `task/TASK-001-initial-app` | `/Users/behlultunc/DEV/cyber-task-hub` | GitHub'da. TASK-019 dalında **olmayan** 3 commit içerir: `3bd0f3e` (aramadan sonra açık task detayının kapanması), `54ae611` (Playwright E2E, `tests/e2e/`), `8dfc7a3` (README çalıştırma komutları). |

- `main` bu iki dalın birleşimi; `Tasks.tsx` çakışmasında TASK-019 sürümü korundu. Yeni iş `main`'den `task/TASK-NNN-…` dalı açarak yapılmalı.
- E2E testleri eski arayüze göre yazıldı (ör. "Ekiplere göre durum", "Task'lar" menüsü, `Yeni task` düğmesi). TASK-019 arayüzüyle çalışmaları için güncellenmeleri gerekir.
- Bu dala birden fazla oturum commit attı (ör. `36115b1` proje yıldızlama). Aynı anda iki oturum aynı dosyalarda çalışmasın.

## Stack (TASK-019 worktree'den)
- Worktree'de `.env` yok; ana repodaki kullanılır:
  `docker compose --env-file /Users/behlultunc/DEV/cyber-task-hub/.env up -d --build`
- Servisler: web http://localhost:8080 · API :8000 · MCP http://localhost:8001/mcp · Mailpit :8025 · Postgres :5433. Hepsi aynı compose proje adını (`cyber-task-hub`) kullanır; hangi checkout'tan `up` yapılırsa o kurulur.
- DB migration `0003`'te (`0002` unit + çok kişili task'lar, `0003` proje yıldızları). Ana daldaki kod bu şemayla çalışmaz; ana dala dönmek için `docker compose down -v` + seed.
- Seed (worktree'den, hostta):
  `cd apps/api && set -a && . ../../../cyber-task-hub/.env && set +a && DATABASE_URL=${DATABASE_URL/@db:5432/@localhost:5433} MIGRATION_DATABASE_URL=${MIGRATION_DATABASE_URL/@db:5432/@localhost:5433} uv run python -m app.seed --reset`
- Testler aynı ortam değişkenleriyle: `uv run pytest` → **85 passed** (son çalıştırma). Web: `pnpm -C apps/web typecheck` temiz.

## Organizasyon (seed)
Direktör → 9 unit → 19 ekip. Unit adı = kod; açılımlar açıklamada ve **tahmindir** (kullanıcı doğrulamadı):

| Unit | Açılım (tahmin) | Ekipler |
|---|---|---|
| TEAM-IAM | Kimlik ve Erişim Yönetimi | IAM Operasyon, Ayrıcalıklı Erişim Yönetimi |
| TEAM-CDC | Siber Savunma Merkezi | SOC, Olay Müdahale (CSIRT), Tehdit İstihbaratı |
| TEAM-MSS | Yönetilen Güvenlik Hizmetleri | Ağ ve Çevre Güvenliği, Uç Nokta Güvenliği |
| TEAM-IS | Bilgi Güvenliği | Veri Güvenliği ve DLP, Güvenlik Farkındalığı |
| TEAM-S | Güvenlik Stratejisi ve Programı | Strateji ve Program Yönetimi, Güvenlik Metrikleri ve Raporlama |
| TEAM-SAA | Güvenlik Mimarisi ve Uygulama Güvenliği | Güvenlik Mimarisi, Uygulama Güvenliği (AppSec) |
| TEAM-OS | Ofansif Güvenlik | Pentest, Kırmızı Takım |
| TEAM-SM | Güvenlik Yönetişimi, Risk ve Uyum | GRC, Üçüncü Taraf Risk Yönetimi |
| TEAM-SMA | Zafiyet ve Saldırı Yüzeyi Yönetimi | Zafiyet Yönetimi, Saldırı Yüzeyi Yönetimi |

Hesaplar (`@demo.local`, parola `.env` → `CTH_SEED_PASSWORD`): `director`, `auditor`, unit yöneticileri `unit.<iam|cdc|mss|is|s|saa|os|sm|sma>`, ekip yöneticileri `manager.<ekip>` (ör. `manager.csirt`; eski `manager.soc` SOC + Zafiyet, `manager.pentest`, `manager.grc`), çalışanlar `analyst.<ekip><n>` (ör. `analyst.soc1`, `analyst.csirt1`). 129 kullanıcı, ~1.500 task.

## Bu oturumda yapılanlar (TASK-019 dalı, hepsi doğrulandı)
- **Seed:** 9 unit, unit ve ekip yöneticileri (`31e5710`).
- **Derleme/çalışma:** web imajı (`vite.config.ts` → `process` tipi) ve nginx (upload regex'i tırnaksız) düzeltildi (`71eac0b`).
- **Rol bazlı dashboard kırılımı** (`327b2ca`, `90fc9c8`): çalışan → yok; yönetici → çalışan bazında; unit yöneticisi → ekip yöneticisi başına satır + **puan**; direktör/denetmen → unit bazında. Puan = 0,5 × tamamlanma % + 0,5 × ort. ilerleme − gecikmiş % (0–100) — kullanıcıyla netleştirilmedi.
  - Recharts, Fragment içindeki `<Bar>`'ları görmez; çocuklar dizi olarak verilmeli.
- **Raporlar** (`e9396e9`): `groupBy=unit`, `unitId` filtresi (kapsam dışı → 404); tüm ekip seçicileri ekipleri unit başlıkları altında gösterir (`components/TeamOptions.tsx`).
- **Genel Bakış yeniden tasarımı** (`ad1cfe6`, `c277a44`), kullanıcının verdiği görsele göre:
  - Lacivert/sarı tema; kenar çubuğu, konum bilgili üst bar, arama, kullanıcı menüsü.
  - Kartlar: Bugünkü görevler (çalışan: kendi; diğer roller: kapsam), Tamamlanan, Onay bekleyen (katılım talepleri).
  - Öncelikli görevler (Bugün/Bu hafta, devam eden görevi tek tıkla tamamlama), Yedekleri tamamla (`GET /tasks?hasBackup=false`), Yaklaşan etkinlik, Ekip/Unit/Çalışan durumu.
  - Eski rol bazlı grafik + tablo "Ayrıntılı durum" bölümünde.
  - Grafikler `--chart-*` token'larını kullanır (lacivert–mavi–sarı); rozetler eski `--todo/--progress/--blocked/--done` renklerinde.

## Kalan işler (öncelik sırası)
1. **Parola rotasyonu (kullanıcı):** eski bir commit kısa süre GitHub'da açık kaldı. `.env` parolalarını değiştir → `docker compose down -v` → up + seed. Agent `.env` yazamaz.
2. GitHub'da varsayılan dal hâlâ `task/TASK-001-initial-app` olabilir; repo ayarlarından `main` yapılmalı (kullanıcı). `main` için branch protection kurulmalı. PR akışı için `gh auth login`.
3. **E2E testlerini** TASK-019 arayüzüne göre güncelle (`tests/e2e/specs/journeys.spec.ts`), sonra `pnpm test:e2e`.
4. **Netleştirilecekler (kullanıcı):** unit kısaltmalarının doğru açılımları; puan formülü; tasarımdaki "Ekip Panosu" menüsünün neye karşılık geldiği (şimdilik eklenmedi); görevlerde saat alanı (tasarımda saat var, modelde yalnızca tarih).
5. Görev listesinde **unit filtresi** yok; dashboard'daki unit satırlarından task listesine bağlantı bu yüzden yok.
6. `scripts/simulate_traffic.py` — kullanıcı kararıyla yapılmıyor.
7. Görev numaralandırması çakışması: `docs/TASKS.md` (BE-/FE-/…) vs `tasks/TASK-NNN.md` — kullanıcı karar verecek.

## Dikkat
- Compose API `--forwarded-allow-ips='*'` ile çalışıyor: istemci `X-Forwarded-For` ile IP sahteleyip IP bazlı rate limit ve `brute_force` alarmını atlatabilir. Üretimde yalnızca güvenilen proxy verilmeli.
- Giriş rate limit'i dakikada 10/IP; arka arkaya çok giriş yapan betikler 429 alır.
- Uygulama kendi iç kaydırma alanını kullanır; Playwright `fullPage` ekran görüntüleri kesik çıkar, kart bazında (`section` + başlık) görüntü alın.
- Commit mesajı `TASK-NNN: …` + `Co-Authored-By` satırı; force push yok.
