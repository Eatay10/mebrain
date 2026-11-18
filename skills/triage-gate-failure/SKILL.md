---
name: triage-gate-failure
description: Gate agent'ı FAIL verdiğinde bulguyu doğrular, düzeltme TASK'ını ve regresyon testini planlar.
---

# Tarif: Gate FAIL triage
1. `reports/agents/<agent>/*.json` oku; bulgunun `confidence` değerine bak.
2. `needs-review` ise elle doğrula; yanlış alarmsa gerekçesini PR'a yaz ve agent prompt'u için `agents/<agent>.md` iyileştirme notu ekle.
3. Gerçekse: önce kırmızı regresyon testi (R-TEST-06), sonra düzeltme; aynı TASK kapsamı dışındaysa `/new-task`.
