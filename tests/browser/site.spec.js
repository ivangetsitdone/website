const { test, expect } = require('@playwright/test');

test('greeting, Vue lifecycle, boosted navigation and history', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'Say hello', exact: true })).toBeVisible();
  await page.evaluate(() => window.testDocumentMarker = true);
  await page.getByRole('button', { name: 'Hello from the server' }).click();
  await expect(page.locator('#greeting')).toContainText('UTC');
  await page.getByRole('button', { name: 'Say hello', exact: true }).click();
  await expect(page.locator('.demo [role=status]')).toHaveText('1 hello');
  for (const name of ['Services', 'About', 'Portfolio', 'Before & after', 'Contact']) {
    await page.getByRole('navigation').getByRole('link', { name, exact: true }).click();
    await expect(page).toHaveTitle(`${name} · Contractor Studio`);
    await expect(page.locator('nav [aria-current=page]')).toHaveText(name);
    expect(await page.evaluate(() => window.testDocumentMarker)).toBe(true);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  }
  await page.getByRole('navigation').getByRole('link', { name: 'Home', exact: true }).click();
  await expect(page.locator('.demo [role=status]')).toHaveText('0 hellos');
  await page.getByRole('button', { name: 'Say hello', exact: true }).click();
  await expect(page.locator('.demo [role=status]')).toHaveText('1 hello');
  await page.goBack();
  await expect(page).toHaveTitle('Contact · Contractor Studio');
  await page.goForward();
  await expect(page).toHaveTitle('Home · Contractor Studio');
  const restoredCount = parseInt(await page.locator('.demo [role=status]').innerText(), 10);
  await page.getByRole('button', { name: 'Say hello', exact: true }).click();
  await expect(page.locator('.demo [role=status]')).toHaveText(`${restoredCount + 1} hello${restoredCount + 1 === 1 ? '' : 's'}`);
  await page.screenshot({ path: `../../recovery/${test.info().project.name}.png`, fullPage: true });
  expect(errors).toEqual([]);
});

test('keyboard skip link', async ({ page }) => {
  await page.goto('/');
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Skip to content' })).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(/#main$/);
});
