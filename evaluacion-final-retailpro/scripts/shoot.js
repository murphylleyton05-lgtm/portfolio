const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage({ deviceScaleFactor: 2 });
  const [html, out] = process.argv.slice(2);
  await page.goto('file://' + html);
  const el = await page.$(".app");
  await el.screenshot({ path: out });
  console.log('WROTE', out);
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
