import { expect, test } from "@playwright/test";
import { ACCOUNTS, apiAs, dashboardTotal, loginUi, pageAs, uniqueTitle } from "./helpers";

const ac = (...ids: string[]) => ({ annotation: ids.map((description) => ({ type: "ac", description })) });

test.describe("Kritik kullanıcı yolculukları", () => {
  test("giriş: hatalı parola reddedilir, doğru parolayla dashboard açılır", ac("TASK-012/AC-2"), async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/\/login$/);

    await page.getByLabel("E-posta").fill("nobody@demo.local");
    await page.getByLabel("Parola").fill("yanlis-parola");
    await page.getByRole("button", { name: "Giriş yap" }).click();
    await expect(page.getByRole("alert")).toHaveText("E-posta veya parola hatalı.");

    await loginUi(page, ACCOUNTS.manager);
    await expect(page.getByText("Ekiplere göre durum")).toBeVisible();
  });

  test(
    "task yaşam döngüsü: oluştur → ata → başla → yorum → tamamla, dashboard sayısı artar",
    ac("TASK-017/AC-1", "TASK-013/AC-2"),
    async ({ browser }) => {
      const title = uniqueTitle("yaşam döngüsü");
      const page = await pageAs(browser, "manager");
      const before = await dashboardTotal(page);

      // Oluştur + ata
      await page.getByRole("link", { name: "Task'lar" }).first().click();
      await page.getByRole("button", { name: "Yeni task" }).click();
      const form = page.getByRole("dialog", { name: "Yeni task" });
      const team = form.getByLabel("Ekip");
      const socTeam = await team.locator("option", { hasText: "SOC" }).first().getAttribute("value");
      await team.selectOption(socTeam!);
      await form.getByLabel("Başlık").fill(title);
      await form.getByLabel("Açıklama").fill("Playwright E2E tarafından oluşturuldu.");
      const assignee = form.getByLabel("Sorumlu", { exact: true });
      const firstMember = await assignee.locator("option").nth(1).getAttribute("value");
      expect(firstMember, "ekipte en az bir üye olmalı").toBeTruthy();
      await assignee.selectOption(firstMember!);
      await form.getByRole("button", { name: "Oluştur" }).click();
      await expect(page.getByText("Task oluşturuldu.")).toBeVisible();

      // Listede bul ve aç
      await page.getByLabel("Task ara").fill(title);
      await page.getByRole("button", { name: title }).click();
      const detail = page.getByRole("dialog", { name: title });
      await expect(detail.getByText("Başlanmadı").first()).toBeVisible();

      // Durum geçişleri + yorum
      await detail.getByRole("button", { name: "Başla" }).click();
      await expect(detail.getByText("Devam ediyor").first()).toBeVisible();
      await detail.getByLabel("Yorum").fill("E2E yorumu");
      await detail.getByRole("button", { name: "Gönder" }).click();
      await expect(detail.getByText("E2E yorumu")).toBeVisible();
      await detail.getByRole("button", { name: "Tamamla" }).click();
      await expect(detail.getByText("Tamamlandı").first()).toBeVisible();
      await page.keyboard.press("Escape");

      // Dashboard sayısı arttı
      await page.goto("/");
      await expect.poll(() => dashboardTotal(page)).toBe(before + 1);
    },
  );

  test("rapor: CSV indirilir ve başlık satırı içerir", ac("TASK-014/AC-3"), async ({ browser }) => {
    const page = await pageAs(browser, "manager");
    await page.goto("/reports");
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.getByRole("link", { name: "CSV indir" }).click(),
    ]);
    expect(download.suggestedFilename()).toMatch(/\.csv$/);
    const stream = await download.createReadStream();
    let csv = "";
    for await (const chunk of stream) csv += chunk.toString();
    const [header, ...rows] = csv.trim().split(/\r?\n/);
    expect(header.split(",").length).toBeGreaterThan(1);
    expect(rows.length).toBeGreaterThan(0);
  });

  test("etkinlik: çalışan katılım talep eder, yönetici onaylar", ac("TASK-014/AC-1"), async ({ browser, baseURL }) => {
    // Kurulum: çalışan adına gelecekte bir bireysel etkinlik (API ile).
    const title = uniqueTitle("etkinlik");
    const { api, csrf } = await apiAs(baseURL!, "analyst");
    const starts = new Date(Date.now() + 14 * 86_400_000);
    const ends = new Date(starts.getTime() + 8 * 3_600_000);
    const created = await api.post("/api/v1/events", {
      headers: { "x-csrf-token": csrf },
      data: { title, type: "TRAINING", scope: "INDIVIDUAL", startsAt: starts.toISOString(), endsAt: ends.toISOString() },
    });
    expect(created.status(), await created.text()).toBe(201);
    await api.dispose();

    // Çalışan talep eder
    const page = await pageAs(browser, "analyst");
    await page.goto("/events");
    await page.getByText(title).click();
    const dlg = page.getByRole("dialog", { name: title });
    await dlg.getByRole("button", { name: "Katılım talep et" }).click();
    await expect(page.getByText("Katılım talebiniz yöneticinize iletildi.")).toBeVisible();
    await expect(dlg.getByText("Katılım durumunuz")).toBeVisible();

    // Yönetici onaylar
    const mpage = await pageAs(browser, "manager");
    await mpage.goto("/events");
    await mpage.getByText(title).click();
    const mdlg = mpage.getByRole("dialog", { name: title });
    await mdlg.getByRole("button", { name: "Onayla" }).click();
    await expect(mdlg.getByRole("button", { name: "Onayla" })).toHaveCount(0);
    await expect(mdlg.getByText("Onaylandı")).toBeVisible();
  });
});
