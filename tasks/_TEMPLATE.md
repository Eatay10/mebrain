---
id: TASK-NNN
title: <emir kipinde kısa başlık>
status: TODO            # TODO | IN_PROGRESS | REVIEW | DONE | BLOCKED
owner: A                # A | B | C | D (insan sahibi)
agent: backend-implementer   # uygulayacak subagent (agents/)
priority: P0            # P0 demo için şart | P1 | P2
depends_on: []          # [TASK-001, ...]
requirements: []        # knowledge/REQUIREMENTS.md ID'leri
adr: []                 # ilgili ADR'ler
owned_paths:            # hook bu listenin dışına yazmayı engeller
  - apps/api/app/modules/<alan>/
estimate: 2h
---

## Amaç
Tek paragraf: neden var, kime değer üretir.

## Bağlam (ajan önce bunları okur)
- knowledge/…
- adr/…
- knowledge/contracts/openapi.yaml → operationId: …

## Kabul kriterleri
- [ ] AC-1: Given … When … Then …
- [ ] AC-2: …
(Her AC en az bir teste `TASK-NNN/AC-n` etiketiyle bağlanır — R-TEST-02.)

## Kapsam dışı
- …

## Uygulama planı
_(task-planner doldurur; insan onaylar)_

## Test planı
- Birim: …
- API: …
- Güvenlik: yetkisiz / kapsam dışı / bozuk girdi
- E2E: …

## Açık sorular
_(ajan belirsizlikte buraya yazar ve durur — R-CORE-10)_

## Kayıt
| Zaman | Kim | Olay |
|---|---|---|
