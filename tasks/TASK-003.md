---
id: TASK-003
title: Oturum tabanlı kimlik doğrulamayı uygula
status: TODO
owner: A
agent: backend-implementer
priority: P0
depends_on: [TASK-002]
requirements: [AUT-01, AUT-03]
adr: [0002]
owned_paths:
  - apps/api/app/auth/
  - apps/api/app/modules/auth/
  - apps/api/tests/auth/
estimate: 3h
---

## Amaç
Oturum tabanlı kimlik doğrulamayı uygula. Gereksinimler: AUT-01, AUT-03.

## Bağlam (ajan önce bunları okur)
- `knowledge/REQUIREMENTS.md` (AUT-01, AUT-03)
- `knowledge/ARCHITECTURE.md`, `knowledge/DATA_MODEL.md`
- `knowledge/contracts/openapi.yaml`
- adr/0002-*
- `rules/` (CLAUDE.md ile otomatik yüklü)

## Kabul kriterleri
- [ ] AC-1: Doğru kimlik bilgisiyle `login` 200 + `cth_session` (HttpOnly, SameSite=Lax) ve `cth_csrf` cookie'leri döner
- [ ] AC-2: Yanlış parola 401 döner ve hangi alanın yanlış olduğunu söylemez; `LOGIN_FAILED` olayı yazılır
- [ ] AC-3: 15 dk içinde 5 hatalı deneme hesabı kilitler (423) ve `ACCOUNT_LOCKED` olayı yazılır
- [ ] AC-4: CSRF token'sız durum değiştiren cookie isteği 403 + `CSRF_REJECTED` olur
- [ ] AC-5: Giriş sonrası session ID yenilenir; logout session'ı DB'den siler

## Kapsam dışı
- `owned_paths` dışındaki dosyalar (gerekirse yeni TASK açılır).

## Uygulama planı
_(task-planner doldurur; insan onaylar)_

## Test planı
- Her AC için en az bir test, `TASK-003/AC-n` etiketiyle (R-TEST-02).
- Güvenlik: kimliksiz, kapsam dışı (404), yetkisiz (403), bozuk/büyük girdi.

## Açık sorular
_(yok)_

## Kayıt
| Zaman | Kim | Olay |
|---|---|---|
| 2026-11-18 | A | Oluşturuldu |
