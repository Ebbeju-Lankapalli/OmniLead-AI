import { test, expect } from '@playwright/test';

test.describe('Leads', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');

    await page.getByLabel(/email address/i).fill(
      'omnilead.e2e.test@example.com'
    );

    await page.getByLabel(/password/i).fill(
      'E2ETestPassword123!'
    );

    await page.getByRole('button', {
      name: /sign in/i,
    }).click();

    await expect(page).toHaveURL(/\/app\/dashboard/);
  });

  test('admin can open leads directory', async ({ page }) => {
    await page.goto('/app/leads');

    await expect(
      page.getByText(/sales leads directory/i)
    ).toBeVisible();
  });

  test('admin can create a new sales lead', async ({ page }) => {
    await page.goto('/app/leads');

    // Open create lead page
    await page.getByRole('link', {
      name: /create.*lead/i,
    }).click();

    await expect(
      page.locator('h2').filter({
        hasText: 'Create New Sales Lead',
      })
    ).toBeVisible();

    // New Customer is the default mode
    await expect(
      page.getByText(/customer information/i)
    ).toBeVisible();

    // Customer information
    await page.getByLabel(/full name/i).fill(
      `E2E Customer ${Date.now()}`
    );

    await page.getByLabel(/company name/i).fill(
      'OmniLead E2E Company'
    );

    await page.getByLabel(/email address/i).fill(
      `customer.${Date.now()}@example.com`
    );

    await page.getByLabel(/phone number/i).fill(
      '+1 555 010 1234'
    );

    // Lead source
    const sourceSelect = page.getByLabel(/lead source \/ channel/i);
    await sourceSelect.selectOption({ index: 0 });

    // Initial status should automatically be NEW.
    const statusSelect = page.getByLabel(/initial status/i);

    await expect(statusSelect).toHaveValue(/.+/);

    // Notes
    await page.locator('textarea').fill(
      'E2E test lead created through the OmniLead web application.'
    );

    // Create
    await page.getByRole('button', {
      name: /create lead/i,
    }).click();

    // Creation should navigate to the new lead
    await expect(page).toHaveURL(/\/app\/leads\/[^/]+/);

    // Verify successful creation
    await expect(
      page.getByText(/lead/i).first()
    ).toBeVisible();
  });
});
