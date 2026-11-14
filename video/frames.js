const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const D = process.argv[2], FPS = 30;
  const TL = JSON.parse(fs.readFileSync(`${D}/timeline.json`));
  fs.mkdirSync(`${D}/frames`, { recursive: true });
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.addInitScript(tl => { window.TL = tl; }, TL);
  await p.goto(`file://${D}/intro.html`); await p.evaluate(() => document.fonts.ready);
  fs.writeFileSync(`${D}/ecg.json`, JSON.stringify(await p.evaluate(() => ecgEvents())));
  const n = Math.ceil(TL._total * FPS);
  for (let i = 0; i < n; i++) {
    await p.evaluate(t => render(t), i / FPS);
    await p.screenshot({ path: `${D}/frames/f${String(i).padStart(5, '0')}.jpg`, type: 'jpeg', quality: 93 });
  }
  console.log('frames', n, 'errors', errs); await b.close();
})();
