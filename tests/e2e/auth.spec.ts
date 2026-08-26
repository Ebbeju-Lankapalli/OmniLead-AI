import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('unauthenticated user can open login page', async ({ page }) => {
    await page.goto('/login');

    await expect(
      page.getByRole('heading', {
        name: /sign in to your crm workspace/i,
      })
    ).toBeVisible();

    await expect(
      page.getByLabel(/email address/i)
    ).toBeVisible();

    await expect(
      page.getByLabel(/password/i)
    ).toBeVisible();

    await expect(
      page.getByRole('button', {
        name: /sign in/i,
      })
    ).toBeVisible();
  });
});
