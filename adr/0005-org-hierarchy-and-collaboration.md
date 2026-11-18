# ADR-0005: Unit katmanı, çok kişili task'lar ve takip (watch)

- Durum: Kabul edildi (2026-11-18)
- İlgili: ADR-0002 (yetki), TASK-019

## Bağlam
Organizasyon şeması Direktör → Unit → Ekip → Ekip üyesi şeklindedir. Önceki modelde yalnızca ekip ve
ekip yöneticisi vardı. Ayrıca task'larda talep sahibi, birden fazla çalışan, ilerleme yüzdesi, güncelleme
tarihçesi ve takipçi bildirimleri isteniyor.

## Karar
1. `units` tablosu ve `teams.unit_id`; yeni rol **UNIT_MANAGER**. Unit yöneticisi unit'indeki tüm ekipleri
   görür/yönetir (MANAGER policy'leri unit kapsamıyla). Ekip zorunlu değildir.
2. Görünürlük = ekip kapsamı ∪ kişisel dahil olma (sorumlu, yedek, çalışma arkadaşı, talep sahibi,
   oluşturan). Direktör ve denetmen her şeyi görür.
3. Atama zinciri `scope.assignable_filter` içinde tek yerde: direktör → herkes (unit yöneticileri öncelikli),
   unit yöneticisi → unit'indeki yöneticiler ve üyeler, yönetici → ekip üyeleri, çalışan → kendisi.
4. `tasks.progress` (0–100) + yalnızca eklenebilen `task_progress_entries` (timeline, not zorunlu).
   DONE geçişi ilerlemeyi 100'e çeker; TODO'dayken ilerleme > 0 olunca IN_PROGRESS'e geçer.
5. `task_watchers` (yıldız). Yedek sorumlu otomatik takipçidir. Task'taki her güncelleme (ilerleme, durum,
   yorum, alan değişikliği, ek) takipçilere ayrıntılı bildirimle gider: "Ahmet ilerlemeyi %70 yaptı: …".
6. Ekler ve etkinlik fotoğrafları DB'de `bytea` (≤ 10 MB, MIME beyaz listesi, fotoğraflarda imza kontrolü).
   Demo ölçeği için yeterli; nesne depolamaya geçiş ayrı ADR.
7. Yetkinlik puanı (0–100) seviyeden bağımsız tutulur; etkinlik ATTENDED ve sertifika eklenince ilgili
   yetkinliklere puan eklenir. `competency_score_logs` aynı kaynağın iki kez puan vermesini engeller.
   Atama önerisi task kategorisini yetkinlik kategorilerine eşler ve en iyi 3 yetkinliğin ortalamasıyla sıralar.
8. Planlı raporlar (`report_schedules`) worker'da 5 dakikada bir kontrol edilir; haftalık pazartesi 08:00,
   aylık ayın 1'i 08:00 (Europe/Istanbul), önceki dönem için sahibin yetki kapsamıyla CSV e-postalanır.

## Sonuçlar
- Görünürlük sorguları `EXISTS (task_collaborators)` içerir; indeksli (`ix_task_collaborators_user_id`).
- Seed'e 2 unit ve 2 unit yöneticisi eklendi (`unit.defense@`, `unit.offense@demo.local`).
- Migration 0002 mevcut verileri doldurur: DONE task'lar %100, puan = seviye × 20.
