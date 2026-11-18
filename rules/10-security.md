# R-SEC — Güvenlik kuralları

Referans: `adr/0002-auth-and-rbac.md`, `knowledge/THREAT_MODEL.md`. Eşleme: OWASP ASVS 5.0.

| ID | Kural | Kontrol |
|---|---|---|
| R-SEC-01 | Public olmayan her endpoint kimlik doğrulama bağımlılığı (`current_user`) kullanır. | test: `tests/security/test_unauthenticated.py` her route'u dolaşır |
| R-SEC-02 | Her kaynak erişimi service katmanında `policies.py` fonksiyonundan geçer; kapsam dışı → 404, yetkisiz → 403. | security-gate + IDOR testleri |
| R-SEC-03 | Liste sorguları `visible_*_filter(user)` kapsam filtresini uygular. | backend-reviewer + test |
| R-SEC-04 | Ham SQL / string birleştirme ile sorgu yok; sadece SQLAlchemy ifadeleri. | semgrep `python.sqlalchemy.security` |
| R-SEC-05 | Girdi Pydantic şemasıyla doğrulanır (`extra="forbid"`); tüm string alanlarda `max_length`. | contract-guard (sözleşmedeki maxLength ile eşleşme) |
| R-SEC-06 | Hata yanıtı RFC 9457; stack trace / SQL / iç path istemciye dönmez. | test: hata yanıt şeması |
| R-SEC-07 | Parola argon2id; session ID ve API token sadece SHA-256 hash olarak saklanır. | backend-reviewer |
| R-SEC-08 | Cookie ile yapılan durum değiştiren isteklerde CSRF token doğrulanır. | test: `test_csrf.py` |
| R-SEC-09 | Güvenlik olayları (`knowledge/OBSERVABILITY.md` listesi) üretilir. | observability-coverage |
| R-SEC-10 | Log'larda parola, token, cookie, `Authorization` header'ı maskelenir; task açıklaması/yorum gövdesi loglanmaz. | test: log redaksiyon testi |
| R-SEC-11 | Frontend'de `dangerouslySetInnerHTML` yok; token localStorage'a yazılmaz. | eslint kuralı + ui-verifier |
| R-SEC-12 | MCP araçları silme / rol değiştirme yapmaz; kullanıcı içerikleri `untrusted_content` olarak işaretlenir. | contract-guard |
| R-SEC-13 | Kullanıcı kaynaklı metin (task açıklaması, yorum, log alanı) AI'a talimat olarak verilmez. | security-gate (INJ bulguları) |
