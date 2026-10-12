import { expect, Page, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function accessible(page: Page) {
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  expect(results.violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
}

test("workspace owner researches an account and reopens evidence after reload", async ({ page }) => {
  await page.goto("/");
  await accessible(page);
  await page.getByRole("button", { name: "Need a workspace? Register" }).click();
  await page.getByLabel("Name", { exact: true }).fill("Browser Owner");
  await page.getByLabel("Workspace", { exact: true }).fill("Browser Workspace");
  await page.getByLabel("Email").fill(`browser-${Date.now()}@example.com`);
  await page.getByLabel("Password").fill("offline-browser-password");
  await page.getByRole("button", { name: "Create account", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Target accounts" })).toBeVisible();
  await accessible(page);
  const newTarget = page.getByRole("button", { name: "New target", exact: true });
  await newTarget.focus();
  await page.keyboard.press("Enter");
  await page.getByLabel("Company name").fill("Example");
  await page.getByLabel("Official website").fill("https://example.com");
  await page.getByRole("button", { name: "Create target", exact: true }).click();
  await page.getByRole("button", { name: "Seller catalog", exact: true }).click();
  await page.getByRole("button", { name: "Add offering", exact: true }).click();
  await page.getByLabel("Name", { exact: true }).fill("Cloud review");
  await page.getByLabel("Description", { exact: true }).fill("Cloud infrastructure review");
  await page.getByLabel("Approved for agent matching").check();
  await page.getByRole("button", { name: "Save offering" }).click();
  await expect(page.getByText("Approved for matching", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Accounts", exact: true }).click();
  await page.getByRole("button", { name: "Research", exact: true }).click();
  await page.getByLabel("Maximum cost USD").fill("1");
  await page.getByRole("button", { name: "Queue research" }).click();
  await page.getByRole("button", { name: "View report", exact: true }).click({ timeout: 15000 });
  await expect(page.getByRole("navigation", { name: "Report sections" }).getByRole("link")).toHaveCount(12);
  await expect(page.getByText("verified · supported", { exact: true })).toBeVisible();
  await expect(page.getByText("Example provides cloud software.", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Gaps and limitations" })).toBeVisible();
  await accessible(page);
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download Markdown" }).click();
  expect((await download).suggestedFilename()).toMatch(/^octodig-.*\.md$/);
  await page.reload();
  await page.getByRole("button", { name: "Reports", exact: true }).click();
  await page.getByRole("button", { name: "Read report", exact: true }).click();
  await expect(page.getByText("verified · supported", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Settings", exact: true }).click();
  await expect(page.getByText("Workspace role: owner", { exact: true })).toBeVisible();
});
