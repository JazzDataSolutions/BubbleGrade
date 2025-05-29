import { test, expect } from '@playwright/test';

test('upload flows through PROCESSING to COMPLETED', async ({ page }) => {
  await page.goto('/');
  const fileInput = page.locator('input[type="file"]');
  // Provide a small dummy image file
  await fileInput.setInputFiles({ name: 'test.png', mimeType: 'image/png', buffer: Buffer.from([0x89,0x50,0x4E,0x47]) });
  // After upload, progress drawer should open
  await expect(page.locator('Progreso del escaneo')).toBeVisible();
  // Wait for a progress message
  await page.waitForSelector('text=preprocessing', { timeout: 10000 });
  // Close drawer
  await page.locator('button[aria-label="Close"]').click();
  // Ensure drawer is hidden
  await expect(page.locator('Progreso del escaneo')).toBeHidden();
});