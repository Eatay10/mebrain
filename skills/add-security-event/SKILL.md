---
name: add-security-event
description: Yeni bir güvenlik olayı tipini uçtan uca ekler (enum, sözleşme, üretim noktası, ekran, alarm, test).
---

# Tarif: Güvenlik olayı
1. `knowledge/OBSERVABILITY.md` tablosuna satır ekle (tip, severity, tetikleyici, alarm eşiği).
2. Sözleşmede `SecurityEventType` enum'una ekle → redocly lint.
3. Üretim noktasında `security_event(TYPE, severity, user, ip, details)` — details'ta secret/kişisel veri yok.
4. Alarm kuralı varsa `app/observability/alerts.py`.
5. `scripts/simulate_traffic.py`'ye tetikleyen desen ekle; test: olay DB'ye düşüyor ve ekranda görünüyor.
