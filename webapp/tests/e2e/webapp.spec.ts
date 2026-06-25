import { expect, test } from "@playwright/test";

test("renders first paint without overlapping core controls", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("status")).toHaveAttribute("aria-label", "IDLE");
  await expect(page.locator(".wake")).toBeVisible();
});
