import playwright from './video_deps/node_modules/playwright-core/index.js';
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve('.');
const { chromium } = playwright;
const out = path.join(root, 'docs', 'video_securecommerce', 'screens');
fs.mkdirSync(out, { recursive: true });

const envText = fs.readFileSync(path.join(root, '.env'), 'utf8');
const match = envText.match(/^DEMO_PASSWORD=(.*)$/m);
if (!match) throw new Error('DEMO_PASSWORD no está definido en .env');
const password = match[1].trim().replace(/^['"]|['"]$/g, '');

const browser = await chromium.launch({
  executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
  headless: true,
});
const context = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
const page = await context.newPage();
page.on('response', async (response) => { if (response.status() >= 400) console.error(response.status(), response.url(), await response.text()); });

async function shot(name, url, wait = 1200) {
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForTimeout(wait);
  await page.screenshot({ path: path.join(out, `${name}.png`) });
}

await shot('01_inicio', 'http://localhost:8080/');
await shot('02_login', 'http://localhost:8080/login');
await shot('02a_registro_empresa', 'http://localhost:8080/registro');
await page.goto('http://localhost:8080/login', { waitUntil: 'networkidle' });
await page.locator('input[type="email"]').fill('administrador@demo.local');
await page.locator('input[type="password"]').fill(password);
await page.locator('button[type="submit"]').click();
await page.waitForTimeout(1000);
if (!page.url().endsWith('/panel')) {
  await page.screenshot({ path: path.join(out, '02b_selector_empresa.png') });
  await page.getByRole('button', { name: /Comercializadora Maya/ }).click();
}
await page.waitForURL('**/panel');
await page.waitForTimeout(1800);
await page.screenshot({ path: path.join(out, '03_panel.png') });
await shot('04_activos', 'http://localhost:8080/activos');
await shot('05_evaluaciones', 'http://localhost:8080/evaluaciones');
await shot('06_riesgos', 'http://localhost:8080/riesgos');
await shot('07_recomendaciones', 'http://localhost:8080/recomendaciones');
await shot('08_incidentes', 'http://localhost:8080/incidentes');
await shot('09_auditoria', 'http://localhost:8080/auditoria');
await shot('10_reportes', 'http://localhost:8080/reportes');
await shot('11_cumplimiento', 'http://localhost:8080/cumplimiento');
await shot('12_mis_empresas', 'http://localhost:8080/organizaciones');
await shot('13_plataforma', 'http://localhost:8080/plataforma');

await browser.close();
console.log(out);
