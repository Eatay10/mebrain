# Definition of Done

Bir görev ancak aşağıdakilerin **hepsi** sağlanınca `DONE` olur:

1. Kod `main`'e PR ile merge edildi; en az bir ekip arkadaşı review etti.
2. `/pre-pr` çalıştırıldı; CI'daki `gate` kontrolü yeşil (security-gate, contract-guard, qa-gate, gerekiyorsa ui-verifier).
3. İlgili `ACCEPTANCE.md` kriterlerinin her biri için en az bir **çalıştırılmış** test var ve geçiyor.
4. API değişikliği varsa `knowledge/contracts/openapi.yaml` aynı PR'da güncellendi ve lint temiz.
5. Yazma işlemleri audit log, gerekli yerlerde security event ve metrik üretiyor (`knowledge/OBSERVABILITY.md`).
6. UI değişikliği: loading / empty / error durumları var, 375–1440 px bozulmuyor, console temiz, klavye ile kullanılabiliyor.
7. Secret, gerçek kişisel veri, `TODO` olarak bırakılmış güvenlik kontrolü yok.
8. `docs/TASKS.md`'de durum güncellendi.
