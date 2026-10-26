// Mixes voice + ducked music + SFX and muxes them onto the silent Remotion render.
// Usage: node mix.mjs <silent-video> <output>
// Voice and timing come from src/warp.json: cue times are written on the first
// voiceover's timeline and mapped to the current voiceover through its anchors.
import {spawnSync} from 'node:child_process';
import {existsSync, readFileSync} from 'node:fs';

const FF = 'C:/Users/acer/ffmpeg/ffmpeg-9.0.2-full_build/bin/ffmpeg.exe';
const DL = 'C:/Users/acer/Downloads';
const timing = JSON.parse(readFileSync(new URL('./src/warp.json', import.meta.url), 'utf8'));
const DUR = timing.duration;
const VOICE = `${DL}/${timing.voice}`;
const warp = (s) => {
  const a = timing.anchors;
  if (s <= a[0][0]) return s;
  for (let i = 1; i < a.length; i++) {
    if (s <= a[i][0]) return a[i - 1][1] + ((s - a[i - 1][0]) / (a[i][0] - a[i - 1][0])) * (a[i][1] - a[i - 1][1]);
  }
  return a[a.length - 1][1] + (s - a[a.length - 1][0]);
};
const MUSIC = `${DL}/tienanh109_HDN_MC_K3_-_X-COOL_(mp3.pm).mp3`;
const MUSIC_START = 32;

// gain values bring each file's peak to a target level well under the voice
const SFX = {
  swish: {file: `${DL}/fast-swish-transition-noise-352756.mp3`, gain: -17},
  whoosh: {file: `${DL}/whoosh-cinematic-sound-effect-376889.mp3`, gain: -16, len: 1.6},
  impact: {file: `${DL}/cinematic-impact-hit-352702.mp3`, gain: -9},
  metal: {file: `${DL}/alexis_gaming_cam-ks-motion-metal-hit-351564.mp3`, gain: -3},
  hit: {file: `${DL}/hit-metal-153323.mp3`, gain: -9},
  shutter: {file: `${DL}/camera-shutter-199580.mp3`, gain: -12},
  sparkle: {file: `${DL}/freesound_community-cartoon_wink_magic_sparkle-6896.mp3`, gain: 10},
  notify: {file: `${DL}/new-notification-3-398649.mp3`, gain: -13},
  cash: {file: `${DL}/applepay.mp3`, gain: -1},
  clock: {file: `${DL}/clock-clock-sound-clock-clock-time-10343.mp3`, gain: -11, len: 1.1},
  ding: {file: `${DL}/floraphonic-hotel-bell-ding-1-174457.mp3`, gain: -16, len: 1.5},
  key: {lavfi: 'anoisesrc=d=0.035:c=white:a=0.6,highpass=f=1800,afade=t=out:st=0:d=0.035', gain: -14},
  tick: {lavfi: 'sine=f=2400:d=0.06,afade=t=out:st=0:d=0.06', gain: -20},
};

// Cue times follow the visuals in src/ReelWide.tsx (the 16:9 version).
const CUTS = [0.05, 1.6, 4.25, 5.46, 7.75, 9.2, 25.4, 28.45, 30.4, 32.3, 33.3, 34.25, 35.2, 36.2, 37.8, 39.65, 40.9];
const PROMPT_TIMES = [14.1, 14.16, 14.36, 14.54, 15.4, 16.18, 16.94, 17.4, 17.7, 17.86, 18.26, 18.64, 19.04, 19.34, 20.2, 20.52, 21.18, 21.4, 21.72, 22.06, 22.2, 22.32, 22.46];
const CHIP_TIMES = [14.54, 15.4, 16.18, 18.64, 20.2, 21.4];

const cues = [
  ...CUTS.map((c) => ['swish', Math.max(0, c - 0.18)]),
  ['whoosh', 10.75],
  ['whoosh', 11.85],
  ['whoosh', 19.0],
  ['whoosh', 22.95],
  ...[0.76, 9.74, 24.08, 36.26].map((t) => ['impact', t]),
  ...[2.6, 29.24, 31.56, 40.28].map((t) => ['metal', t]),
  ['hit', 7.3],
  ['hit', 8.75],
  ['shutter', 32.6],
  ...[9.62, 21.4, 33.52].map((t) => ['sparkle', t]),
  ['notify', 12.1],
  ['notify', 22.8],
  ['cash', 39.12],
  ['clock', 39.72],
  ['ding', 41.85],
  ...PROMPT_TIMES.map((t) => ['key', t]),
  ...[7.0, 29.07].map((t) => ['key', t]),
  ...[30.75, 30.95, 31.15, 31.4, 31.75, 31.95, 41.34, 41.45, 41.56, 41.66].map((t) => ['key', t]),
  ...CHIP_TIMES.map((t) => ['tick', t + 0.05]),
  ...Array.from({length: 7}, (_, i) => ['tick', 6.2 + i * 0.07]),
  ...Array.from({length: 6}, (_, i) => ['tick', 41.34 + i * 0.06 + 0.15]),
];

// The "Seedance 2.5 and other AI tools" line runs on real time (see S7 in ReelWide.tsx).
const realCues = [
  ...[29.42, 29.98, 30.52].map((t) => ['shutter', t]),
  ...[26.7, 26.94, 27.76, 28.24, 28.9].map((t) => ['tick', t + 0.04]),
];
for (const c of cues) c[1] = warp(c[1]);
cues.push(...realCues);

const VIDEO_IN = process.argv[2] ?? 'out/video-silent.mp4';
const VIDEO_OUT = process.argv[3] ?? 'out/what-the-heck-reel.mp4';
const args = ['-y', '-v', 'error', '-i', VIDEO_IN, '-i', VOICE, '-ss', String(MUSIC_START), '-t', String(DUR), '-i', MUSIC];
for (const [name] of cues) {
  const s = SFX[name];
  if (s.lavfi) args.push('-f', 'lavfi', '-i', s.lavfi);
  else args.push('-i', s.file);
}

const fmt = 'aformat=sample_rates=48000:channel_layouts=stereo';
const parts = [
  `[1:a]${fmt},loudnorm=I=-15:TP=-1.5:LRA=11,asplit=2[voice][vkey]`,
  `[2:a]${fmt},volume=-25dB,afade=t=in:d=0.4,afade=t=out:st=${DUR - 1.6}:d=1.6[mus]`,
  `[vkey]apad[vkeyp]`,
  `[mus][vkeyp]sidechaincompress=threshold=0.03:ratio=4:attack=20:release=350[musd]`,
];
const labels = [];
cues.forEach(([name, t], i) => {
  const s = SFX[name];
  const ms = Math.max(0, Math.round(t * 1000));
  const trim = s.len ? `atrim=0:${s.len},afade=t=out:st=${s.len - 0.3}:d=0.3,` : '';
  parts.push(`[${i + 3}:a]${fmt},${trim}volume=${s.gain}dB,adelay=${ms}:all=1[s${i}]`);
  labels.push(`[s${i}]`);
});
parts.push(`${labels.join('')}amix=inputs=${labels.length}:normalize=0[sfx]`);
parts.push(`[voice][musd][sfx]amix=inputs=3:normalize=0,alimiter=limit=0.84:level=false,atrim=0:${DUR}[aout]`);

args.push('-filter_complex', parts.join(';'), '-map', '0:v', '-map', '[aout]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', String(DUR), '-movflags', '+faststart', VIDEO_OUT);

if (!existsSync(VIDEO_IN)) throw new Error(`Render ${VIDEO_IN} first`);
const r = spawnSync(FF, args, {stdio: 'inherit'});
process.exit(r.status ?? 1);
