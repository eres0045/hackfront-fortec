/* Render every impress.js step to a PNG via Playwright chromium. */
const { chromium } = require('playwright-chromium');
const path = require('path');

(async () => {
  const dir = __dirname;
  const browser = await chromium.launch();
  for (let n = 1; n <= 9; n++) {
    const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
    await page.goto('file://' + path.join(dir, 'index.html') + '#/step-' + n, { waitUntil: 'load' });
    await page.waitForTimeout(1600); // impress init + 1s transition
    await page.screenshot({ path: path.join(dir, 'shots', 'step-' + n + '.png') });
    await page.close();
    console.log('shot step-' + n);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
