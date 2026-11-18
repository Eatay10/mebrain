# R-TS — Frontend (React / TypeScript)

| ID | Kural | Kontrol |
|---|---|---|
| R-TS-01 | `tsconfig` strict; `any` yok. | `pnpm typecheck` + eslint `no-explicit-any` |
| R-TS-02 | Sunucu verisi sadece TanStack Query hook'ları ile (`src/api/hooks/*`). | review |
| R-TS-03 | Her ekran loading / empty / error / success durumunu gösterir. | ui-verifier |
| R-TS-04 | Formlar react-hook-form + zod; zod şemaları sözleşmedeki kısıtları yansıtır. | review |
| R-TS-05 | Renk/boşluk/tipografi sadece design token'lardan (`src/styles/tokens.css`); hard-coded renk yok. | stylelint |
| R-TS-06 | Erişilebilirlik: axe serious/critical ihlali 0; tüm kontroller klavye ile erişilebilir. | ui-verifier |
| R-TS-07 | Mock'lar sadece `src/mocks/` altında ve `VITE_USE_MOCKS=true` iken. | ui-verifier |
| R-TS-08 | Metinler `src/i18n/tr.json` üzerinden (Türkçe varsayılan). | review |
