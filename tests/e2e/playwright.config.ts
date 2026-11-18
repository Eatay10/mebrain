import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { defineConfig, devices } from "@playwright/test";

// Seed parolası ortamdan; yoksa repo kökündeki .env'den okunur (asla koda yazılmaz).
if (!process.env.CTH_SEED_PASSWORD) {
  try {
    const env = readFileSync(resolve(import.meta.dirname, "../../.env"), "utf8");
    const m = env.match(/^CTH_SEED_PASSWORD=(.*)$/m);
    if (m) process.env.CTH_SEED_PASSWORD = m[1].trim().replace(/^['"]|['"]$/g, "");
  } catch {
    /* CI'da ortam değişkeni verilir */
  }
}

const baseURL = process.env.CTH_E2E_BASE_URL ?? "http://localhost:8080";
if (!/^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(baseURL)) {
  throw new Error(`E2E yalnızca yerel ortama karşı çalışır: ${baseURL}`);
}

export default defineConfig({
  testDir: "./specs",
  // Testler aynı seed verisini ve giriş rate limit'ini (10/dk/IP) paylaşır: sırayla çalış.
  workers: 1,
  fullyParallel: false,
  retries: 0,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL,
    locale: "tr-TR",
    timezoneId: "Europe/Istanbul",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "setup", testMatch: /auth\.setup\.ts/ },
    { name: "chromium", use: { ...devices["Desktop Chrome"] }, dependencies: ["setup"] },
  ],
});
