---
id: TASK-019
title: Unit hiyerarşisi, çok kişili task'lar, ilerleme/takip, planlı raporlar ve yetkinlik puanı ekle
status: REVIEW
owner: A
agent: backend-implementer
priority: P0
depends_on: [TASK-005, TASK-009, TASK-010, TASK-013, TASK-014]
requirements: []
adr: [ADR-0005]
owned_paths:
  - apps/api/
  - apps/web/src/
  - knowledge/contracts/openapi.yaml
  - packages/api-client/src/schema.d.ts
estimate: 2d
---

## Amaç
Organizasyonu Direktör → Unit → Ekip → Ekip üyesi olarak modellemek; task'larda talep sahibi, ana/yedek
sorumlu, çalışma arkadaşları, ilerleme yüzdesi + tarihçe, yıldızla takip ve ekleri desteklemek; haftalık/aylık
planlı rapor; etkinlik/sertifika ile artan yetkinlik puanı ve atama önerisi; proje organizasyon ağacı.

## Kabul kriterleri
- [x] AC-1: Direktör/denetmen tüm ekipleri, unit yöneticisi unit'indeki ekipleri, diğerleri kendi + ekibinin
  (ve dahil oldukları) task'larını görür. Unit yönetimi direktördedir.
- [x] AC-2: Direktör → unit yöneticisi, unit yöneticisi → ekip yöneticileri/üyeleri, yönetici → ekip üyeleri
  atar; task'ta talep sahibi, sorumlu, yedek ve çalışma arkadaşları bulunur.
- [x] AC-3: İlerleme notla güncellenir, timeline oluşur, dashboard'da ortalama % görünür; yıldız koyanlara
  "X ilerlemeyi %N yaptı: not" bildirimi gider; yedek otomatik takipçidir.
- [x] AC-4: Task'a dosya eklenir/indirilir/silinir (≤ 10 MB, tür kısıtı).
- [x] AC-5: Etkinlik katılımı (ATTENDED) ve sertifika ilgili yetkinlik puanını artırır; task formunda en
  yetkin kişi önerilir; konferansa not ve fotoğraf eklenir.
- [x] AC-6: Haftalık/aylık rapor planlanır, worker CSV'yi e-postalar; "şimdi gönder" çalışır.
- [x] AC-7: Proje detayında organizasyon ağacı ve paydaşlar görünür, yönetici paydaş ekler/kaldırır.

Testler: `apps/api/tests/test_org_collaboration.py` (`TASK-019/AC-n`).

## Kayıt
| Zaman | Kim | Olay |
|---|---|---|
| 2026-11-18 | A | Oluşturuldu ve uygulandı (66 test geçti) |
