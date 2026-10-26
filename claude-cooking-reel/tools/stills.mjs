// Render stills from one bundle and one browser, then tile them into a contact sheet.
// Usage: node tools/stills.mjs <outdir> <scale> <frame> [frame...]
import {bundle} from '@remotion/bundler';
import {openBrowser, renderStill, selectComposition} from '@remotion/renderer';
import {spawnSync} from 'node:child_process';
import {mkdirSync} from 'node:fs';
import path from 'node:path';

const [outDir, scale, ...frames] = process.argv.slice(2);
mkdirSync(outDir, {recursive: true});
const browserExecutable = path.resolve('.browser/chrome-headless-shell-win64/chrome-headless-shell.exe');
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
const browser = await openBrowser('chrome', {browserExecutable});
const composition = await selectComposition({serveUrl, id: 'Reel', puppeteerInstance: browser});
const files = [];
for (const f of frames) {
  const output = path.join(outDir, `f${String(f).padStart(4, '0')}.png`);
  await renderStill({serveUrl, composition, frame: Number(f), output, puppeteerInstance: browser, scale: Number(scale)});
  files.push(output);
  console.log('frame', f);
}
await browser.close({silent: true});
const cols = Math.min(files.length, 5);
const rows = Math.ceil(files.length / cols);
spawnSync('ffmpeg', ['-v', 'error', '-y', ...files.flatMap((p) => ['-i', p]), '-filter_complex',
  `${files.map((_, i) => `[${i}]`).join('')}xstack=inputs=${files.length}:layout=${files.map((_, i) => `${(i % cols) === 0 ? '0' : Array.from({length: i % cols}, () => 'w0').join('+')}_${Math.floor(i / cols) === 0 ? '0' : Array.from({length: Math.floor(i / cols)}, () => 'h0').join('+')}`).join('|')}:fill=black`,
  path.join(outDir, 'sheet.png')], {stdio: 'inherit'});
console.log('sheet', path.join(outDir, 'sheet.png'), `${cols}x${rows}`);
