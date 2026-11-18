import { test as setup } from "@playwright/test";
import { ACCOUNTS, loginUi, statePath } from "./helpers";

// Her rol için TEK giriş; oturum dosyası testler arasında paylaşılır (giriş rate limit'i: 10/dk/IP).
for (const role of ["manager", "analyst"] as const) {
  setup(`oturum: ${role}`, async ({ page }) => {
    await loginUi(page, ACCOUNTS[role]);
    await page.context().storageState({ path: statePath(role) });
  });
}
