const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;

const NAV = ['What I do', 'About', 'My work', 'Project stories', 'Contact me'];

async function isLoaded(locator) {
  return locator.evaluate(img => img.complete && img.naturalWidth > 0);
}

test('home content, boosted navigation, head metadata and history', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Consider it done.');
  await expect(page.getByRole('link', { name: 'Text 971-288-3488' })).toHaveAttribute('href', 'sms:+19712883488');
  // The licensing disclosure has to reach every visitor, on every page.
  await expect(page.locator('.footer-disclosure')).toContainText('Not a CCB-licensed contractor');
  const registry = page.locator('.footer-disclosure a');
  await expect(registry).toHaveText('#2249807-97');
  await expect(registry).toHaveAttribute('hx-boost', 'false');
  expect((await page.locator('body').innerText()).toLowerCase()).not.toContain('handyman');
  await expect(page.getByRole('link', { name: 'Call 971-288-3488' }).first()).toHaveAttribute('href', 'tel:+19712883488');
  expect(await isLoaded(page.locator('.hero-photo img'))).toBe(true);
  // A marker on the live document proves later navigation never reloads the page.
  await page.evaluate(() => { window.testDocumentMarker = true; });
  for (const name of NAV) {
    await page.getByRole('navigation').getByRole('link', { name, exact: true }).click();
    await expect(page).toHaveTitle(`${name} · Zip, LLC`);
    await expect(page.locator('nav [aria-current=page]')).toHaveText(name);
    expect(await page.evaluate(() => window.testDocumentMarker)).toBe(true);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    // Boosted swaps replace the body only, so the script keeps head metadata in sync.
    const head = await page.evaluate(() => ({
      description: document.querySelector('meta[name=description]').content,
      canonical: document.querySelector('link[rel=canonical]').href,
      mainDescription: document.querySelector('main').dataset.description,
      mainCanonical: document.querySelector('main').dataset.canonical,
    }));
    expect(head.description).toBe(head.mainDescription);
    expect(head.description.length).toBeGreaterThan(40);
    expect(head.canonical).toBe(head.mainCanonical);
    expect(head.canonical.startsWith('https://ivanpineda.bottah.dev/')).toBe(true);
  }
  await page.getByRole('navigation').getByRole('link', { name: 'Home', exact: true }).click();
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Consider it done.');
  await page.goBack();
  await expect(page).toHaveTitle('Contact me · Zip, LLC');
  await page.goForward();
  await expect(page).toHaveTitle('Home · Zip, LLC');
  await expect(page.getByRole('link', { name: 'What I can take on →' })).toBeVisible();
  await page.screenshot({ path: `../../recovery/${test.info().project.name}.png`, fullPage: true });
  expect(errors).toEqual([]);
});

test('about portrait and contact details', async ({ page }) => {
  await page.goto('/about');
  const portrait = page.locator('.portrait img');
  expect(await isLoaded(portrait)).toBe(true);
  await expect(portrait).toHaveAttribute('alt', /Ivan Pineda/);
  await page.screenshot({ path: `../../recovery/about-${test.info().project.name}.png`, fullPage: true });
  await page.goto('/contact');
  await expect(page.getByRole('link', { name: 'Call 971-288-3488' }).first()).toHaveAttribute('href', 'tel:+19712883488');
  await expect(page.getByRole('link', { name: 'Text 971-288-3488' })).toHaveAttribute('href', 'sms:+19712883488');
  await expect(page.getByText('Forest Grove and surrounding communities').first()).toBeVisible();
  await page.screenshot({ path: `../../recovery/contact-${test.info().project.name}.png`, fullPage: true });
});

test('offered work, declined work and the work-history framing', async ({ page }) => {
  await page.goto('/services');
  await expect(page.locator('.service-card')).toHaveCount(6);
  const offered = (await page.locator('.services-grid').innerText()).toLowerCase();
  // Nothing needing an Oregon CCB or trade license may appear in the offer itself.
  for (const word of ['remodel', 'sheetrock', 'drywall', 'tile', 'flooring', 'plumbing', 'electrical', 'painting', 'shower', 'install', 'repair']) {
    expect(offered, `services grid offers regulated work: ${word}`).not.toContain(word);
  }
  await expect(page.locator('.scope-note')).toContainText('Oregon CCB exam');
  // One line about the license, not a list of what he cannot do.
  await expect(page.locator('.scope-note p')).toHaveCount(1);
  await expect(page.locator('.scope-note li')).toHaveCount(0);
  await page.goto('/portfolio');
  await expect(page.locator('.editorial-note')).toContainText('my work history rather than the services I offer today');
});

test('content pages pass automated accessibility checks', async ({ page }) => {
  for (const path of ['/', '/services', '/about', '/contact']) {
    await page.goto(path);
    const { violations } = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
    expect(violations.map(violation => `${path} ${violation.id}`)).toEqual([]);
  }
});

test('keyboard skip link', async ({ page }) => {
  await page.goto('/');
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Skip to content' })).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(/#main$/);
});
