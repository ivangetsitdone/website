const { test, expect } = require('@playwright/test');
const catalog = require('../../app/data/portfolio.json');
const AxeBuilder = require('@axe-core/playwright').default;

async function expectLoaded(image) {
  await expect(image).toBeVisible();
  await expect.poll(() => image.evaluate(el => el.complete && el.naturalWidth > 0)).toBe(true);
}

test('portfolio filters, modal controls, keyboard focus and empty state', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/portfolio');
  await expect(page.locator('[data-count]')).toHaveText(`${catalog.photos.length} of ${catalog.photos.length} photos`);
  await expectLoaded(page.locator('[data-photo] img').first());
  const first = page.locator('[data-photo]').first();
  await first.focus();
  await page.keyboard.press('Enter');
  const dialog = page.getByRole('dialog');
  await expect(dialog).toBeVisible();
  await expect(page.getByRole('button', { name: 'Close photo viewer' })).toBeFocused();
  await expectLoaded(dialog.locator('img'));
  await expect(dialog.locator('#viewer-title')).toHaveText(catalog.photos[0].title);
  await page.keyboard.press('ArrowRight');
  await expect(dialog.locator('#viewer-title')).toHaveText(catalog.photos[1].title);
  await dialog.getByRole('button', { name: 'Previous photo' }).click();
  await expect(dialog.locator('#viewer-title')).toHaveText(catalog.photos[0].title);
  await page.keyboard.press('ArrowLeft');
  await expect(dialog.locator('#viewer-title')).toHaveText(catalog.photos.at(-1).title);
  await page.getByRole('button', { name: 'Close photo viewer' }).focus();
  await page.keyboard.press('Shift+Tab');
  expect(await page.evaluate(() => !!document.activeElement.closest('dialog'))).toBe(true);
  await page.keyboard.press('Escape');
  await expect(dialog).not.toBeVisible();
  await expect(first).toBeFocused();
  await page.getByLabel('Project type').selectOption('Showers & tile');
  await page.getByLabel('Photo stage', { exact: true }).selectOption('In progress');
  const matching = catalog.photos.filter(p => p.category === 'Showers & tile' && p.stage === 'In progress');
  await expect(page.locator('[data-photo-card]:visible')).toHaveCount(matching.length);
  await page.locator('[data-photo-card]:visible [data-photo]').first().click();
  await expect(dialog.locator('[data-viewer-count]')).toHaveText(`1 / ${matching.length}`);
  await dialog.getByRole('button', { name: 'Next photo' }).click();
  await expect(dialog.locator('#viewer-title')).toHaveText(matching[1].title);
  await dialog.getByRole('button', { name: 'Close photo viewer' }).click();
  await page.getByLabel('Photo stage', { exact: true }).selectOption('After');
  await expect(page.locator('[data-empty]')).toBeVisible();
  await expect(page.locator('[data-photo-card]:visible')).toHaveCount(0);
  await page.getByRole('button', { name: 'Reset filters' }).click();
  await expect(page.locator('[data-photo-card]:visible')).toHaveCount(catalog.photos.length);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  const selectors = await page.locator('.gallery-filters select').evaluateAll(elements => elements.map(el => ({
    right: el.getBoundingClientRect().right, parentRight: el.parentElement.getBoundingClientRect().right,
  })));
  expect(selectors.every(el => el.right <= el.parentRight + 1)).toBe(true);
  await page.screenshot({ path: `../../recovery/portfolio-${test.info().project.name}.png` });
  expect(errors).toEqual([]);
});

test('gallery survives boosted navigation and back/forward restoration', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  await page.getByRole('navigation').getByRole('link', { name: 'My work', exact: true }).click();
  await page.locator('[data-photo]').first().click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.keyboard.press('Escape');
  await page.getByRole('link', { name: 'Project stories, before and after' }).click();
  await expect(page.locator('.project-sequence')).toHaveCount(catalog.pairs.length);
  await page.locator('[data-photo]').first().click();
  await expectLoaded(page.getByRole('dialog').locator('img'));
  await page.getByRole('button', { name: 'Close photo viewer' }).click();
  await page.goBack();
  await expect(page).toHaveURL(/\/portfolio$/);
  await page.getByLabel('Project type').selectOption('Fencing');
  await page.locator('[data-photo-card]:visible [data-photo]').first().click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.getByRole('button', { name: 'Next photo' }).click();
  await expect(page.locator('[data-viewer-count]')).toContainText('2 /');
  await page.keyboard.press('Escape');
  await page.goForward();
  await expect(page).toHaveURL(/\/before-after$/);
  await page.locator('[data-photo]').first().click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.getByRole('button', { name: 'Next photo' }).click();
  // The before/after viewer walks every photo in every project, however long the projects grow.
  const sequenceTotal = catalog.pairs.reduce((total, pair) => total + pair.photos.length, 0);
  await expect(page.locator('[data-viewer-count]')).toHaveText(`2 / ${sequenceTotal}`);
  expect(errors).toEqual([]);
});

test('all thumbnails decode and sequences preserve progress labels', async ({ page }) => {
  await page.goto('/portfolio');
  // Force lazy thumbnails to load for coverage, not normal browsing behavior.
  await page.locator('[data-photo] img').evaluateAll(images => images.forEach(image => image.loading = 'eager'));
  await expect.poll(() => page.locator('[data-photo] img').evaluateAll(images => images.every(image => image.complete && image.naturalWidth > 0))).toBe(true);
  await page.goto('/before-after');
  const shower = page.locator('.project-sequence').filter({ hasText: 'From the original shower to new tile' });
  await expect(shower.locator('.stage')).toHaveText(['Before', 'Before', 'In progress', 'In progress', 'In progress']);
  await expect(page.locator('.sequence-grid').first().locator('.stage')).toHaveText(['Before', 'After']);
  await page.screenshot({ path: `../../recovery/sequences-${test.info().project.name}.png` });
});

test('photo links and captions work without JavaScript', async ({ browser, baseURL }) => {
  const context = await browser.newContext({ javaScriptEnabled: false, viewport: test.info().project.use.viewport });
  const page = await context.newPage();
  await page.goto(`${baseURL}/portfolio`);
  await expect(page.locator('[data-filters]')).not.toBeVisible();
  await expect(page.locator('figcaption')).toHaveCount(catalog.photos.length);
  await page.locator('[data-photo]').first().click();
  await expect(page).toHaveURL(/\/media\/p12-full.webp$/);
  await context.close();
});


test('gallery and open viewer pass automated accessibility checks', async ({ page }) => {
  await page.goto('/portfolio');
  const audit = () => new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
  expect((await audit()).violations).toEqual([]);
  await page.locator('[data-photo]').first().click();
  await expectLoaded(page.getByRole('dialog').locator('img'));
  expect((await audit()).violations).toEqual([]);
  await page.screenshot({ path: `../../recovery/viewer-${test.info().project.name}.png` });
});

test('single-photo filter and image failure remain usable', async ({ page }) => {
  await page.goto('/portfolio');
  await page.getByLabel('Project type').selectOption('Fencing');
  await page.getByLabel('Photo stage', { exact: true }).selectOption('In progress');
  await expect(page.locator('[data-photo-card]:visible')).toHaveCount(1);
  await page.route('**/media/*-full.webp', route => route.abort());
  await page.locator('[data-photo-card]:visible [data-photo]').click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await expect(page.locator('[data-image-error]')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Next photo' })).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Previous photo' })).toBeDisabled();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).not.toBeVisible();
});
