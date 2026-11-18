# R-TEST — Test kuralları

| ID | Kural | Kontrol |
|---|---|---|
| R-TEST-01 | Her endpoint: en az 1 başarılı, 1 doğrulama hatası, 1 yetki (403/404) testi. | qa-gate (endpoint × test eşlemesi) |
| R-TEST-02 | Her TASK kabul kriteri en az bir teste `@pytest.mark.ac("TASK-NNN/AC-n")` veya Playwright `test.info().annotations` ile bağlanır. | `scripts/ac_coverage.py` |
| R-TEST-03 | Backend satır kapsamı ≥ %70, `app/auth` ve `policies` ≥ %90. | pytest-cov (CI eşiği) |
| R-TEST-04 | Testler deterministik: sabit seed, sabit saat (`freezegun`), dış ağ yok. | CI tekrar çalıştırma |
| R-TEST-05 | Test atlanırsa (`skip`) gerekçe ve TASK numarası yazılır. | qa-gate |
| R-TEST-06 | Hata düzeltmesi önce kırmızı bir regresyon testiyle başlar. | review |
