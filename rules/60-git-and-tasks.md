# R-GIT — Git ve iş birimi kuralları

| ID | Kural | Kontrol |
|---|---|---|
| R-GIT-01 | Branch adı: `task/TASK-NNN-kisa-ad`. | `hooks/git/pre-push` |
| R-GIT-02 | Commit mesajı: `TASK-NNN: <emir kipinde özet>`; AI katkısı varsa `Co-Authored-By: Claude …` trailer'ı. | `hooks/git/commit-msg` |
| R-GIT-03 | `main`'e doğrudan push yok; PR + gate'ler yeşil. | branch protection + `hooks/git/pre-push` |
| R-GIT-04 | TASK durumu `tasks/BOARD.md` ve TASK dosyasının `status` alanında güncel. | `/implement-task` sonunda otomatik |
| R-GIT-05 | PR açıklaması: TASK linki, kabul kriterleri checklist'i, gate özetleri. | `/pre-pr` çıktısı |
