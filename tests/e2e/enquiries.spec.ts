import { test, expect } from '@playwright/test';

const TEST_EMAIL = 'omnilead.e2e.test@example.com';
const TEST_PASSWORD = 'E2ETestPassword123!';

test.describe('Enquiries', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');

    await page.getByLabel(/email address/i).fill(TEST_EMAIL);
    await page.getByLabel(/password/i).fill(TEST_PASSWORD);

    await page.getByRole('button', {
      name: /sign in/i,
    }).click();

    await expect(page).toHaveURL(/\/app\/dashboard/);
  });

  test('admin can open enquiries inbox', async ({ page }) => {
    await page.goto('/app/enquiries');

    await expect(
      page.getByRole('heading', {
        name: /omnichannel enquiries inbox/i,
      })
    ).toBeVisible();

    await expect(
      page.getByText(
        /inbound customer messages from whatsapp, instagram, and meta ads/i
      )
    ).toBeVisible();

    await expect(
      page.getByRole('button', {
        name: /refresh inbox/i,
      })
    ).toBeVisible();
  });

  test('admin can view and classify an enquiry as general enquiry', async ({
    page,
    request,
  }) => {
    const uniqueId = `e2e-enquiry-${Date.now()}`;
    const customerName = `E2E Enquiry Customer ${Date.now()}`;

    const accessToken = await page.evaluate(() => {
      return localStorage.getItem('omnilead_access_token');
    });

    expect(accessToken).toBeTruthy();

    const createResponse = await request.post(
      '/api/v1/enquiries',
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        data: {
          source: 'WHATSAPP',
          external_reference_id: uniqueId,
          customer_name_raw: customerName,
          contact_raw: '+1 555 010 5678',
          message_text:
            'E2E test enquiry - this is a general product question.',
        },
      }
    );

    expect(
      createResponse.ok(),
      `Create enquiry failed: ${createResponse.status()} ${await createResponse.text()}`
    ).toBeTruthy();

    const enquiry = await createResponse.json();

    expect(enquiry.id).toBeTruthy();

    await page.goto('/app/enquiries');

    await expect(
      page.getByText(
        'E2E test enquiry - this is a general product question.'
      ).first()
    ).toBeVisible();

    await expect(
      page.getByText(customerName)
    ).toBeVisible();

    const enquiryCard = page
      .locator('div')
      .filter({
        hasText:
          'E2E test enquiry - this is a general product question.',
      })
      .filter({
        has: page.getByText(customerName),
      })
      .first();

    await expect(enquiryCard).toBeVisible();

    await enquiryCard
      .getByRole('button', {
        name: /general enquiry/i,
      })
      .first()
      .click();

    await expect(
      page.getByText(/enquiry status updated/i)
    ).toBeVisible();

    await expect(
      enquiryCard.getByRole('button', {
        name: /general enquiry/i,
      }).first()
    ).toBeVisible();
  });
});
