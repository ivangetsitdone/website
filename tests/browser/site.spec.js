const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;

// The header carries four links; the logo is the home link and the work-history
// pages share "My work". Nav labels and page titles differ for Contact.
const NAV = [
  { link: 'What I do', title: 'What I do' },
  { link: 'My work', title: 'My work' },
  { link: 'About', title: 'About' },
  { link: 'Contact', title: 'Contact me' },
];
const mainNav = page => page.getByRole('navigation', { name: 'Main navigation' });

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
  expect(await isLoaded(page.locator('.brand-mark'))).toBe(true);
  // A marker on the live document proves later navigation never reloads the page.
  await page.evaluate(() => { window.testDocumentMarker = true; });
  for (const { link, title } of NAV) {
    await mainNav(page).getByRole('link', { name: link, exact: true }).click();
    await expect(page).toHaveTitle(`${title} · Zip, LLC`);
    await expect(mainNav(page).locator('[aria-current=page]')).toHaveText(link);
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
    expect(head.canonical.startsWith('https://ivangetsitdone.com/')).toBe(true);
  }
  await page.getByRole('link', { name: 'Zip, LLC home' }).click();
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
  expect(await isLoaded(page.locator('.business-card img'))).toBe(true);
  await expect(page.getByRole('link', { name: 'Call 971-288-3488' }).first()).toHaveAttribute('href', 'tel:+19712883488');
  await expect(page.getByRole('link', { name: 'Text 971-288-3488' })).toHaveAttribute('href', 'sms:+19712883488');
  await expect(page.getByText('Forest Grove and surrounding communities').first()).toBeVisible();
  // The printable list is a link to the sheet itself, opened in its own tab.
  const sheet = page.locator('.print-note img');
  await sheet.scrollIntoViewIfNeeded();
  expect(await isLoaded(sheet)).toBe(true);
  const sheetLink = page.locator('.print-note a');
  await expect(sheetLink).toHaveAttribute('href', /\/print\/honey-do-list\.svg(\?|$)/);
  await expect(sheetLink).toHaveAttribute('target', '_blank');
  await expect(sheetLink).toHaveAttribute('rel', 'noopener');
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
  // Cost is described as character, not as a price list.
  const promise = page.locator('.promise');
  await expect(promise.getByRole('heading', { name: /big mystery/ })).toBeVisible();
  await expect(promise).toContainText('I’ll check with you first');
  expect(await promise.innerText()).not.toContain('$');
  // The licensing position lives with the profile now: one line, not a list of
  // what he cannot do.
  await page.goto('/about');
  await expect(page.locator('.scope-note')).toContainText('Oregon CCB exam');
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

test('the navigation and the footer contact buttons fit the viewport', async ({ page }) => {
  await page.goto('/services');
  const boxes = locator => locator.evaluateAll(els => els.map(el => {
    const box = el.getBoundingClientRect();
    return { x: Math.round(box.x), y: Math.round(box.y), width: Math.round(box.width), height: Math.round(box.height) };
  }));

  // The four header links hold one row at every width, including a 320px phone,
  // which is the whole reason the navigation is four links and not six.
  const links = await boxes(page.locator('.site-nav a'));
  expect(links).toHaveLength(NAV.length);
  expect([...new Set(links.map(link => link.y))]).toHaveLength(1);
  expect(Math.min(...links.map(link => link.height))).toBeGreaterThanOrEqual(44);
  await page.setViewportSize({ width: 320, height: 720 });
  expect([...new Set((await boxes(page.locator('.site-nav a'))).map(link => link.y))]).toHaveLength(1);
  await page.setViewportSize(test.info().project.use.viewport);

  // Nothing is hidden: the footer lists every page, the work pages share a header
  // link, and they carry their own section tabs.
  await expect(page.getByRole('navigation', { name: 'All pages' }).getByRole('link')).toHaveCount(6);
  await page.goto('/before-after');
  await expect(mainNav(page).getByRole('link', { name: 'My work' })).toHaveAttribute('aria-current', 'true');
  const tabs = page.getByRole('navigation', { name: 'Work history' });
  await expect(tabs.getByRole('link', { name: 'Before and after' })).toHaveAttribute('aria-current', 'page');
  await tabs.getByRole('link', { name: 'All photos' }).click();
  await expect(page).toHaveTitle('My work · Zip, LLC');

  // Call and text sit side by side and share the width evenly.
  const [call, text] = await boxes(page.locator('.footer-contact a'));
  expect(call.y).toBe(text.y);
  expect(Math.abs(call.width - text.width)).toBeLessThanOrEqual(1);
  expect(text.x).toBeGreaterThanOrEqual(call.x + call.width);
  expect(Math.min(call.height, text.height)).toBeGreaterThanOrEqual(44);

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(0);
});
