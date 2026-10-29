// Screenshot every reveal.js slide via hash navigation.
const puppeteer = require('/home/hatch/workspace/harness-safepay/node_modules/puppeteer');
const fs = require('fs');
const path = require('path');

(async () => {
  const outDir = path.join(__dirname, 'shots');
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: '/home/hatch/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome',
    args: ['--no-sandbox', '--disable-gpu', '--hide-scrollbars'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });
  const base = 'http://127.0.0.1:8899/index.html';
  for (let i = 0; i < 9; i++) {
    await page.goto(`${base}#/${i}`, { waitUntil: 'networkidle0', timeout: 30000 });
    await new Promise(r => setTimeout(r, 1500));
    const title = await page.evaluate(() => {
      const s = document.querySelector('.slides section.present');
      return s ? (s.innerText || '').split('\n')[0] : '(no present slide)';
    });
    await page.screenshot({ path: path.join(outDir, `slide-${i + 1}.png`) });
    console.log(`slide ${i + 1} (hash #/${i}): ${title.slice(0, 60)}`);
  }
  await browser.close();
  console.log('done');
})().catch(e => { console.error('FAILED:', e.message); process.exit(1); });
