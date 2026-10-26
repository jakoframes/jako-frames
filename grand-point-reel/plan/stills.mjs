// Preview stills of Main, then one contact sheet.
// Args are seconds of the final video, or cue+offset on the footage timeline: node plan/stills.mjs 1.2 down20+1.2
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import {execFileSync} from 'node:child_process';
import {readFileSync} from 'node:fs';
import path from 'node:path';

const VSTART_S = 0;
const {cues} = JSON.parse(readFileSync('src/data.json', 'utf8'));
const toSec = (a) => {
  const m = a.match(/^([a-zA-Z0-9]+)([+-][\d.]+)?$/);
  if (m && cues[m[1]] !== undefined) return VSTART_S + cues[m[1]] + Number(m[2] || 0);
  return Number(a);
};

const browserExecutable = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
const composition = await selectComposition({serveUrl, id: 'Main', browserExecutable});
const outs = [];
for (const a of process.argv.slice(2)) {
  const frame = Math.min(composition.durationInFrames - 1, Math.round(toSec(a) * composition.fps));
  const output = `cache/still_${outs.length}.png`;
  await renderStill({serveUrl, composition, frame, output, scale: 0.5, browserExecutable});
  outs.push(output);
}
const ins = outs.flatMap((o) => ['-i', o]);
const filter = outs.length > 1 ? `hstack=inputs=${outs.length}` : 'null';
execFileSync('ffmpeg', ['-v', 'error', '-y', ...ins, '-filter_complex', filter, 'cache/sheet_main.png']);
console.log('sheet: cache/sheet_main.png (' + outs.length + ' frames)');
