import { resolve } from "node:path";
import { type Browser, expect, type APIRequestContext, type Page, request } from "@playwright/test";

export const ACCOUNTS = {
  director: "director@demo.local",
  manager: "manager.soc@demo.local",
  analyst: "analyst.soc1@demo.local",
  auditor: "auditor@demo.local",
} as const;

export function seedPassword(): string {
  const p = process.env.CTH_SEED_PASSWORD;
  if (!p) throw new Error("CTH_SEED_PASSWORD ayarlı değil (ortam veya .env).");
  return p;
}

/** Her test için benzersiz ve sonradan tanınabilir başlık. */
export function uniqueTitle(prefix: string): string {
  return `[e2e] ${prefix} ${Date.now().toString(36)}`;
}

export async function loginUi(page: Page, email: string): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("E-posta").fill(email);
  await page.getByLabel("Parola").fill(seedPassword());
  await page.getByRole("button", { name: "Giriş yap" }).click();
  await expect(page.getByRole("heading", { name: /^Merhaba,/ })).toBeVisible();
}

export type Role = "manager" | "analyst";

export function statePath(role: Role): string {
  return resolve(import.meta.dirname, "../.auth", `${role}.json`);
}

/** auth.setup.ts'in kaydettiği oturumla yeni bir sekme açar (yeniden giriş yapmaz). */
export async function pageAs(browser: Browser, role: Role): Promise<Page> {
  const ctx = await browser.newContext({ storageState: statePath(role), locale: "tr-TR", timezoneId: "Europe/Istanbul" });
  const page = await ctx.newPage();
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /^Merhaba,/ })).toBeVisible();
  return page;
}

/** Aynı oturumla API istemcisi (kurulum adımları için); CSRF cookie'den okunur. */
export async function apiAs(baseURL: string, role: Role): Promise<{ api: APIRequestContext; csrf: string }> {
  const api = await request.newContext({ baseURL, storageState: statePath(role) });
  const { cookies } = await api.storageState();
  const csrf = cookies.find((c) => c.name === "cth_csrf")?.value;
  expect(csrf, "CSRF cookie").toBeTruthy();
  return { api, csrf: csrf! };
}

/** Dashboard'daki "Toplam" kartının sayısı. */
export async function dashboardTotal(page: Page): Promise<number> {
  const card = page.locator("div", { has: page.locator("p", { hasText: /^Toplam$/ }) }).last();
  const text = await card.locator("p.tabular").innerText();
  return Number(text.replace(/\D/g, ""));
}
