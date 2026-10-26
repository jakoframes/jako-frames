// Mixes the pause-cut voice + SFX onto the silent Remotion render.
// Usage: node mix.mjs <silent-video> <output>
// Cue times come from src/vo.json with the same word lookup as src/timing.ts,
// so sounds land on the same frames as the visuals.
import {spawnSync} from 'node:child_process';
import {existsSync, readFileSync} from 'node:fs';

const FF = 'C:/Users/acer/ffmpeg/ffmpeg-9.0.2-full_build/bin/ffmpeg.exe';
const DL = 'C:/Users/acer/Downloads';
const TG = `${DL}/Telegram Desktop/звуки`;
const DIG = `${TG}/Клик/Digital`;
const vo = JSON.parse(readFileSync(new URL('./src/vo.json', import.meta.url), 'utf8'));
const VO_START = 2.36;
const DUR = 27.5;
const PULL = 1.66, PULL_D = 0.8, LAND = PULL + PULL_D - 0.15;
const CUTS = [0.36, 0.7, 1.04, 1.36]; // montage cuts (CLIPS in src/timing.ts)
const WORDS = vo.words.map((w) => ({...w, s: w.s + VO_START, k: w.w.toLowerCase().replace(/[^a-z0-9']/g, '')}));
const at = (k, n = 0) => {
  let c = 0;
  for (const w of WORDS) if (w.k === k && c++ === n) return w.s;
  throw new Error(`word not found: ${k}`);
};

// peak = target peak in dBFS; gain is derived from each file's measured max
const SFX = {
  swish: {file: `${DL}/fast-swish-transition-noise-352756.mp3`, peak: -17},
  swoosh: {file: `${TG}/Whoosh & Swoosh/SFX- Swoosh02.mp3`, peak: -15, len: 0.8},
  whoosh: {file: `${DL}/whoosh-cinematic-sound-effect-376889.mp3`, peak: -14, len: 1.4},
  impact: {file: `${DL}/cinematic-impact-hit-352702.mp3`, peak: -7, len: 1.6},
  thud: {file: `${DL}/cinematic-impact-hit-352702.mp3`, peak: -14, len: 0.7},
  metal: {file: `${DL}/alexis_gaming_cam-ks-motion-metal-hit-351564.mp3`, peak: -12, len: 1.2},
  hit: {file: `${DL}/hit-metal-153323.mp3`, peak: -14, len: 0.7},
  shutter: {file: `${DL}/camera-shutter-199580.mp3`, peak: -15},
  sparkle: {file: `${DL}/fast-swish-transition-noise-352756.mp3`, peak: -23},
  notify: {file: `${DL}/new-notification-3-398649.mp3`, peak: -13},
  ding: {file: `${DL}/floraphonic-hotel-bell-ding-1-174457.mp3`, peak: -17, len: 1.4},
  click: {file: `${TG}/Клик/Mouse/mouse_click_06.wav`, peak: -10},
  pop1: {file: `${DIG}/dig_click_01.wav`, peak: -17},
  pop2: {file: `${DIG}/dig_click_02.wav`, peak: -17},
  pop3: {file: `${DIG}/dig_click_03.wav`, peak: -17},
  pop4: {file: `${DIG}/dig_click_04.wav`, peak: -17},
  pop5: {file: `${DIG}/dig_click_05.wav`, peak: -17},
  key: {lavfi: 'anoisesrc=d=0.03:c=white:a=0.6,highpass=f=1800,afade=t=out:st=0:d=0.03', peak: -25},
  riser: {lavfi: `anoisesrc=d=${PULL + 0.1}:c=pink:a=0.8,bandpass=f=1800:width_type=h:w=2600,afade=t=in:st=0:d=${PULL - 0.06}:curve=exp,afade=t=out:st=${PULL}:d=0.1`, peak: -21},
  tick: {lavfi: 'sine=f=2400:d=0.05,afade=t=out:st=0:d=0.05', peak: -25},
};
let popN = 0;
const pop = (t) => [`pop${(popN++ % 5) + 1}`, t];
const run = (name, t0, n, gap) => Array.from({length: n}, (_, i) => [name, t0 + i * gap]);

// same keys and nudges as src/timing.ts
const T = {
  claude0: at('claude', 0), opus: at('opus'), five: at('5', 0), is: at('is'), cooking: at('cooking'),
  i0: at('i'), motion0: at('motion', 0), graphic: at('graphic'), just: at('just'), claude1: at('claude', 1), twenty: at('20') - 0.1, minutes: at('minutes'),
  oh: at('oh'), video: at('video'), also: at('also'),
  you0: at('you', 0), designer0: at('designer', 0), you1: at('you', 1), even: at('even'), motion1: at('motion', 1), designer1: at('designer', 1),
  one: at('one') - 0.1, drop: at('drop'), reference: at('reference'), instagram: at('instagram'),
  two: at('two'), send0: at('send', 0), assets: at('assets'), three: at('three') - 0.14, paste: at('paste'), give: at('give'),
  boom: at('boom') + 0.17, professional: at('professional'), saas0: at('saas', 0), animation: at('animation'),
  comment: at('comment'), saas1: at('saas', 1), send1: at('send', 1), prompt: at('prompt'), instructions: at('instructions'),
};
const END = VO_START + vo.duration;

const cues = [
  // hook montage: a hit on frame one, a riser under it, a whip + hit on every cut
  ['impact', 0], ['riser', 0], ...CUTS.flatMap((c) => [['swish', c - 0.07], ['hit', c]]), ['sparkle', CUTS[0] + 0.05],
  // out of the full-screen video, Jako drops in
  ['whoosh', PULL - 0.08], ['swoosh', PULL + 0.1], ['thud', LAND - 0.02], pop(LAND + 0.02),
  pop(T.claude0 - 0.04), pop(T.opus - 0.04), ['tick', T.five], ['swish', T.cooking - 0.04], ['sparkle', T.cooking + 0.08],
  // the panel comes forward, gets selected, Claude types, the timer rolls
  ['swoosh', T.i0 - 0.08], ['click', T.motion0 - 0.05], ...run('tick', T.motion0 + 0.07, 8, 0.03), pop(T.graphic - 0.05),
  ['swish', T.just - 0.12], ...run('key', T.just, 12, 0.055), ['sparkle', T.claude1],
  ['hit', T.twenty - 0.12], ...run('tick', T.twenty - 0.08, 11, 0.04), ['ding', T.twenty + 0.42], pop(T.minutes - 0.05),
  // "this video?": window shrink, stamp, window back
  ['whoosh', T.oh - 0.06], pop(T.video - 0.12), ['thud', T.also - 0.02], ['shutter', T.also], ['swoosh', T.you0 - 0.22],
  // designer → struck, motion designer → struck
  pop(T.you0 - 0.06), ['hit', T.you0 + 0.32], ['swish', T.designer0], ['metal', T.designer0 + 0.02],
  ['swoosh', T.you1 - 0.08], pop(T.you1 - 0.04), ...run('tick', T.even + 0.12, 6, 0.05), ['hit', T.motion1 - 0.08], ['hit', T.motion1 + 0.14],
  ['swish', T.designer1], ['metal', T.designer1 + 0.02],
  // three boards: camera trucks, numbers slam, things land
  ['whoosh', T.one - 0.12], ['impact', T.one - 0.05], ['swish', T.drop - 0.1], ['click', T.reference + 0.16], pop(T.reference + 0.2), ['ding', T.reference + 0.26],
  ['sparkle', T.instagram - 0.05],
  ['whoosh', T.two - 0.16], ['hit', T.two - 0.05], ...Array.from({length: 6}, (_, i) => pop(T.send0 - 0.12 + i * 0.07)), ...run('tick', T.assets - 0.05, 6, 0.05), ['ding', T.assets + 0.25],
  ['whoosh', T.three - 0.16], ['hit', T.three - 0.05], pop(T.paste - 0.3), ['click', T.paste - 0.02], ['swish', T.paste + 0.02], ['click', T.give + 0.35],
  // BOOM
  ['impact', T.boom - 0.02], ['metal', T.boom], ['whoosh', T.boom + 0.02], ['sparkle', T.boom + 0.12], ['swoosh', T.boom + 0.1],
  ['swish', T.professional - 0.14], ['hit', T.saas0 - 0.06], pop(T.animation - 0.08), pop(T.animation + 0.15), pop(T.animation + 0.25),
  // CTA
  ['swoosh', T.comment - 0.14], ['hit', T.comment - 0.08], ['thud', T.saas1 - 0.04], ...run('key', T.saas1 + 0.05, 4, 0.07),
  ['click', T.saas1 + 0.42], ['swish', T.saas1 + 0.44], ['notify', T.send1 - 0.12], pop(T.prompt - 0.05), pop(T.instructions - 0.08), ['ding', T.instructions + 0.05],
  ['swish', END - 0.55],
];

const VIDEO_IN = process.argv[2] ?? 'out/silent.mp4';
const VIDEO_OUT = process.argv[3] ?? 'out/claude-cooking-reel.mp4';
if (!existsSync(VIDEO_IN)) throw new Error(`Render ${VIDEO_IN} first`);

// measure each sample's peak once
const peakOf = (s) => {
  const src = s.lavfi ? ['-f', 'lavfi', '-i', s.lavfi] : ['-i', s.file];
  const r = spawnSync(FF, ['-hide_banner', ...src, '-af', 'volumedetect', '-f', 'null', '-'], {encoding: 'utf8'});
  const m = /max_volume: (-?[\d.]+) dB/.exec(r.stderr);
  return m ? parseFloat(m[1]) : 0;
};
const used = new Set(cues.map(([n]) => n));
for (const [name, s] of Object.entries(SFX)) {
  if (!used.has(name)) continue;
  if (!s.lavfi && !existsSync(s.file)) throw new Error(`missing SFX ${name}: ${s.file}`);
  s.gain = (s.peak - peakOf(s)).toFixed(1);
}

const args = ['-y', '-v', 'error', '-i', VIDEO_IN, '-i', 'public/vo.wav'];
for (const [name] of cues) {
  const s = SFX[name];
  if (s.lavfi) args.push('-f', 'lavfi', '-i', s.lavfi);
  else args.push('-i', s.file);
}
const fmt = 'aformat=sample_rates=48000:channel_layouts=stereo';
const parts = [`[1:a]${fmt},loudnorm=I=-14:TP=-1.5:LRA=11,adelay=${Math.round(VO_START * 1000)}:all=1,apad[voice]`];
const labels = [];
cues.forEach(([name, t], i) => {
  const s = SFX[name];
  const ms = Math.max(0, Math.round(t * 1000));
  const trim = s.len ? `atrim=0:${s.len},afade=t=out:st=${s.len - 0.25}:d=0.25,` : '';
  parts.push(`[${i + 2}:a]${fmt},${trim}volume=${s.gain}dB,adelay=${ms}:all=1[s${i}]`);
  labels.push(`[s${i}]`);
});
parts.push(`${labels.join('')}amix=inputs=${labels.length}:normalize=0[sfx]`);
parts.push(`[voice][sfx]amix=inputs=2:normalize=0,alimiter=limit=0.85:level=false,atrim=0:${DUR}[aout]`);
args.push('-filter_complex', parts.join(';'), '-map', '0:v', '-map', '[aout]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', String(DUR), '-movflags', '+faststart', VIDEO_OUT);

const r = spawnSync(FF, args, {stdio: 'inherit'});
console.log(`${cues.length} cues ->`, VIDEO_OUT);
process.exit(r.status ?? 1);
