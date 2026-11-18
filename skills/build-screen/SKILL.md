---
name: build-screen
description: React ekranını standart durumlar, erişilebilirlik ve doğrulama adımlarıyla kurar. Yeni bir sayfa/ekran yaparken kullan.
---

# Tarif: Ekran
1. Veri: `src/api/hooks/use<Op>.ts` (TanStack Query, `packages/api-client`).
2. Bileşen: `features/<alan>/<Ekran>.tsx`; durumlar: `<Loading/> <Empty/> <ErrorState/>` ortak bileşenleri.
3. Metinler `i18n/tr.json`; renkler token'lardan.
4. Route + rol bazlı menü görünürlüğü.
5. Doğrula: `pnpm typecheck && pnpm test && pnpm exec playwright test features/<alan>`; axe; 3 viewport ekran görüntüsü.
