// 把 out/*.html 渲染成 PDF，并给封面和每张卡出 PNG 预览图（商品主图用）。
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const out = path.join(__dirname, 'out');
const dist = path.join(__dirname, 'dist');
fs.mkdirSync(dist, { recursive: true });

const names = {
  bundle: 'tathr-concept-cards-vol1',
  '01': 'tathr-card-01-neural-network', '02': 'tathr-card-02-blockchain', '03': 'tathr-card-03-compound-interest',
  '04': 'tathr-card-04-curved-spacetime', '05': 'tathr-card-05-fourier-transform', '06': 'tathr-card-06-entropy',
};

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 794, height: 1123 }, deviceScaleFactor: 2 });
  for (const key of [...Object.keys(names), 'cover']) {
    await page.goto('file://' + path.join(out, key + '.html'), { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    if (names[key]) await page.pdf({ path: path.join(dist, names[key] + '.pdf'), format: 'A4', printBackground: true });
    if (key !== 'bundle') await page.screenshot({ path: path.join(dist, 'preview-' + key + '.png'), fullPage: false });
  }
  await browser.close();
  console.log('done');
})();
