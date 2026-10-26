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
const DUR = 30;
const WORDS = vo.words.map((w) => ({...w, k: w.w.toLowerCase().replace(/[^a-z0-9']/g, '')}));
const at = (k, n = 0) => {
  let c = 0;
  for (const w of WORDS) if (w.k === k && c++ === n) return w.s;
  throw new Error(`word not found: ${k}`);
};

// peak = target true-ish peak in dBFS; gain is derived from each file's measured max
const SFX = {
  swish: {file: `${DL}/fast-swish-transition-noise-352756.mp3`, peak: -17},
  swoosh: {file: `${TG}/Whoosh & Swoosh/SFX- Swoosh02.mp3`, peak: -15, len: 0.8},
  whoosh: {file: `${DL}/whoosh-cinematic-sound-effect-376889.mp3`, peak: -15, len: 1.4},
  impact: {file: `${DL}/cinematic-impact-hit-352702.mp3`, peak: -7, len: 1.6},
  metal: {file: `${DL}/alexis_gaming_cam-ks-motion-metal-hit-351564.mp3`, peak: -11, len: 1.2},
  hit: {file: `${DL}/hit-metal-153323.mp3`, peak: -12, len: 0.8},
  shutter: {file: `${DL}/camera-shutter-199580.mp3`, peak: -14},
  sparkle: {file: `${DL}/fast-swish-transition-noise-352756.mp3`, peak: -22},
  notify: {file: `${DL}/new-notification-3-398649.mp3`, peak: -12},
  clock: {file: `${DL}/clock-clock-sound-clock-clock-time-10343.mp3`, peak: -18, len: 1.4},
  ding: {file: `${DL}/floraphonic-hotel-bell-ding-1-174457.mp3`, peak: -16, len: 1.4},
  click: {file: `${TG}/Клик/Mouse/mouse_click_06.wav`, peak: -10},
  // UI clicks for panels landing (clean digital, not cartoon pops)
  pop1: {file: `${DIG}/dig_click_01.wav`, peak: -17},
  pop2: {file: `${DIG}/dig_click_02.wav`, peak: -17},
  pop3: {file: `${DIG}/dig_click_03.wav`, peak: -17},
  pop4: {file: `${DIG}/dig_click_04.wav`, peak: -17},
  pop5: {file: `${DIG}/dig_click_05.wav`, peak: -17},
  key: {lavfi: 'anoisesrc=d=0.03:c=white:a=0.6,highpass=f=1800,afade=t=out:st=0:d=0.03', peak: -24},
  tick: {lavfi: 'sine=f=2400:d=0.05,afade=t=out:st=0:d=0.05', peak: -24},
};
let popN = 0;
const pop = (t) => [`pop${(popN++ % 5) + 1}`, t];

const T = {
  but0: at('but', 0), only: at('only'), one: at('one', 0), master: at('masterpiece'), and0: at('and', 0), free: at('free'),
  here: at("here's"), thing: at('thing'), every: at('every'), design: at('design'), video: at('video'), code: at('code'),
  marketing: at('marketing'), own: at('own'), but1: at('but', 1), waste: at('waste'), hours: at('hours'),
  this: at('this'), search1: at('searching', 1), scans: at('scans'), finds: at('finds'), exactly: at('exactly'),
  its2: at("it's", 1), find0: at('find', 0), skillName: at('skill', 2), grab: at('grab'), online: at('online'),
  but2: at('but', 2), prepared: at('prepared'), ready: at('ready'), just: at('just'), download: at('download'),
  upload: at('upload'), skillsYour: at('skills', 2), done: at('done'), comment: at('comment'), find1: at('find', 1), send: at('send'),
};
const END = vo.duration + 0.02;
const SCENE_STARTS = [T.but0 - 0.06, T.and0 - 0.08, T.here - 0.08, T.every - 0.06, T.but1 - 0.06, T.this - 0.06, T.its2 - 0.06, T.grab - 0.3, T.just - 0.06, T.comment - 0.14];

const cues = [
  // hook: camera fly-in + counter roll
  ['impact', 0], ['whoosh', 0], ...Array.from({length: 14}, (_, i) => ['tick', 0.02 + i * 0.07]), ['hit', 1.03],
  // iris wipes between scenes
  ...SCENE_STARTS.map((t) => ['swoosh', Math.max(0, t - 0.04)]),
  ['swish', T.only], ['impact', T.one - 0.04], ['sparkle', T.one + 0.02],
  ['metal', T.master - 0.04], ['sparkle', T.master + 0.05],
  pop(T.and0), ['impact', T.free - 0.04], ['ding', T.free + 0.05],
  pop(T.here - 0.05), ['swish', T.thing], pop(T.thing + 0.05),
  ...[0, 1, 2, 3].map((i) => pop(T.every - 0.06 + i * 0.06)),
  ...[T.design, T.video, T.code, T.marketing].map((t) => ['hit', t - 0.05]),
  ...[0, 1, 2, 3].map((i) => pop(T.own + i * 0.07)),
  pop(T.but1 - 0.06), ...Array.from({length: 15}, (_, i) => ['key', T.but1 + i * 0.08]),
  ...Array.from({length: 7}, (_, i) => pop(T.waste - 0.05 + i * 0.16)), ['clock', T.waste], ['hit', T.hours - 0.03],
  ['whoosh', T.this - 0.06], pop(T.search1 - 0.1), pop(T.scans - 0.12), ['swish', T.scans + 0.2],
  ['sparkle', T.finds], pop(T.exactly - 0.05), ...[0, 1, 2].map((i) => ['tick', T.exactly + 0.1 + i * 0.32]),
  ...[0, 1, 2].map((i) => pop(T.exactly + 0.1 + i * 0.32)),
  ...[0, 0.12, 0.24].map((d) => ['tick', T.its2 + 0.05 + d]), ['impact', T.find0 - 0.03], ['metal', T.skillName - 0.03], ['sparkle', T.find0 + 0.05],
  pop(T.grab - 0.27), pop(T.online), ['swish', T.but2 - 0.02], pop(T.but2 + 0.08), pop(T.prepared), ['hit', T.ready - 0.04], ['sparkle', T.ready],
  pop(T.just - 0.06), ...Array.from({length: 6}, (_, i) => ['tick', T.download + i * 0.1]), ['ding', T.download + 0.6],
  ['swoosh', T.upload - 0.06], ['swish', T.upload + 0.02], pop(T.upload + 0.28), ['click', T.upload + 0.42],
  ['shutter', T.skillsYour - 0.1], pop(T.skillsYour + 0.02), ['impact', T.done - 0.04], ['ding', T.done],
  pop(T.comment - 0.12), ...Array.from({length: 4}, (_, i) => ['key', T.comment + 0.02 + (i + 1) * 0.06]),
  ['click', T.find1 + 0.32], ['swish', T.find1 + 0.34], ['swish', T.find1 + 0.36], ['notify', T.send - 0.06],
  ['whoosh', END], ['impact', END + 0.05], ['metal', END + 0.18], pop(END + 0.35),
];

const VIDEO_IN = process.argv[2] ?? 'out/silent.mp4';
const VIDEO_OUT = process.argv[3] ?? 'out/find-skills-reel.mp4';
if (!existsSync(VIDEO_IN)) throw new Error(`Render ${VIDEO_IN} first`);

// measure each sample's peak once
const peakOf = (s) => {
  const src = s.lavfi ? ['-f', 'lavfi', '-i', s.lavfi] : ['-i', s.file];
  const r = spawnSync(FF, ['-hide_banner', ...src, '-af', 'volumedetect', '-f', 'null', '-'], {encoding: 'utf8'});
  const m = /max_volume: (-?[\d.]+) dB/.exec(r.stderr);
  return m ? parseFloat(m[1]) : 0;
};
for (const [name, s] of Object.entries(SFX)) {
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
const parts = [`[1:a]${fmt},loudnorm=I=-14:TP=-1.5:LRA=11,apad[voice]`];
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
