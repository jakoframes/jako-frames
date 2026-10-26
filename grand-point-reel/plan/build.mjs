// Builds the clean edit (public/cut.mp4: rotated camera picture + lav audio) and src/data.json.
// Run from the project folder:  node plan/build.mjs [--no-video]
import {execFileSync} from 'node:child_process';
import {writeFileSync} from 'node:fs';

const VIDEO = 'C:/Users/acer/Downloads/Telegram Desktop/MAH01607.MP4';
const LAV = 'C:/Users/acer/Downloads/Telegram Desktop/Grand Point Hotel 4 3.m4a';
const LAV_OFFSET = 5.915; // lav time = camera time + offset (cross-correlated, drift < 1 ms over 60 s)

// Kept camera-time ranges. Removed: false starts (0-18.6), off-script talk and broken takes
// (23.5-53.6), "Грамотно!" restart (60.9-71.9), "Норм?" at the end.
const CUTS = [
  {in: 18.62, out: 22.4},
  {in: 22.82, out: 23.5},
  {in: 53.58, out: 60.85},
  {in: 71.95, out: 78.95},
];

// speech islands (silencedetect -38dB, 0.12 s) in camera time
const ISLANDS = [[18.73, 20.75], [20.88, 22.2], [22.92, 23.31], [53.69, 55.0], [55.29, 57.15], [57.35, 60.71], [72.05, 74.69], [74.9, 78.0], [78.16, 78.83]];

const LINES = [
  [18.73, 22.2, 'Думаете, если раньше не брали кредит, то банк вам обязательно одобрит?'],
  [22.92, 23.31, 'Это миф.'],
  [53.69, 57.15, 'Банк оценивает доход, обязательства и другие факторы.'],
  [57.35, 60.71, 'И то, что у вас нет кредитной истории, ещё не гарантирует вам одобрения.'],
  [72.05, 73.05, 'Так что же вам поможет?'],
  [73.13, 76.45, 'Грамотно заполненная анкета и заранее продуманная тактика.'],
  [76.61, 78.83, 'А с этим можем помочь вам мы — Elite Finance.'],
];

let acc = 0;
const segs = CUTS.map((c) => {
  const s = {...c, start: acc, dur: c.out - c.in};
  acc += s.dur;
  return s;
});
const CUT_DUR = acc;
const toOut = (t) => {
  for (const s of segs) if (t >= s.in && t <= s.out) return s.start + (t - s.in);
  const next = segs.find((s) => s.in > t);
  return next ? next.start : CUT_DUR;
};

const spokenWeight = (w) => {
  const letters = w.replace(/[^\p{L}\d]/gu, '').length;
  return Math.max(2, letters);
};

const words = [];
const lines = [];
LINES.forEach(([a, b, text], li) => {
  const isl = ISLANDS.map(([x, y]) => [Math.max(x, a), Math.min(y, b)]).filter(([x, y]) => y - x > 0.05);
  const speech = isl.reduce((n, [x, y]) => n + (y - x), 0);
  const toks = text.split(/\s+/).filter((t) => t !== '—');
  const total = toks.reduce((n, t) => n + spokenWeight(t), 0);
  const at = (p) => {
    let rest = p * speech;
    for (const [x, y] of isl) {
      if (rest <= y - x + 1e-6) return x + rest;
      rest -= y - x;
    }
    return isl[isl.length - 1][1];
  };
  let cum = 0;
  toks.forEach((t) => {
    const s = at(cum / total);
    cum += spokenWeight(t);
    const e = at(cum / total);
    words.push({w: t, line: li, s: +toOut(s).toFixed(3), e: +toOut(e).toFixed(3)});
  });
  lines.push({s: +toOut(a).toFixed(3), e: +toOut(b).toFixed(3)});
});

// subtitle chunks: ≤3 words, ≤20 chars
const chunks = [];
let cur = [];
words.forEach((w, i) => {
  const next = words[i + 1];
  cur.push(i);
  const len = cur.map((k) => words[k].w).join(' ').length;
  const lineEnd = !next || next.line !== w.line;
  if (lineEnd || /[,.!?]$/.test(w.w) || cur.length >= 3 || (next && len + 1 + next.w.length > 20)) {
    chunks.push(cur);
    cur = [];
  }
});
const subChunks = chunks.map((ids, i) => {
  const nextStart = chunks[i + 1] ? words[chunks[i + 1][0]].s : CUT_DUR;
  const end = Math.min(nextStart, words[ids[ids.length - 1]].e + 0.4);
  return {ids, s: words[ids[0]].s, e: +end.toFixed(3)};
});

const cue = (re, after = 0) => {
  const w = words.find((x) => x.s >= after && re.test(x.w));
  if (!w) throw new Error('cue not found: ' + re);
  return w.s;
};
const cues = {};
cues.hook = cue(/Думаете/);
cues.credit = cue(/кредит,/);
cues.approve = cue(/одобрит/);
cues.myth = cue(/миф/);
cues.bank = cue(/Банк/);
cues.income = cue(/доход/);
cues.oblig = cue(/обязательства/);
cues.factors = cue(/факторы/);
cues.noKi = cue(/нет/, cues.factors);
cues.guarantee = cue(/гарантирует/);
cues.help = cue(/Так/);
cues.form = cue(/Грамотно/);
cues.tactic = cue(/продуманная/);
cues.us = cue(/^А$/, cues.tactic);
cues.brand = cue(/Elite/);

writeFileSync(
  'src/data.json',
  JSON.stringify({cutDur: +CUT_DUR.toFixed(3), segs: segs.map(({start, dur}) => ({start: +start.toFixed(3), dur: +dur.toFixed(3)})), lines, words, chunks: subChunks, cues}, null, 1),
);
console.log('cut duration', CUT_DUR.toFixed(2), 's,', words.length, 'words,', subChunks.length, 'chunks');

if (!process.argv.includes('--no-video')) {
  const args = ['-v', 'error', '-y', '-i', VIDEO, '-i', LAV];
  const parts = [];
  CUTS.forEach((c, i) => {
    const d = c.out - c.in;
    parts.push(
      `[0:v]trim=${c.in}:${c.out},setpts=PTS-STARTPTS,scale=1920:1080,setsar=1,transpose=2,fps=30,curves=all='0/0.03 0.15/0.27 0.35/0.5 0.6/0.72 1/1'[v${i}]`,
      `[1:a]atrim=${(c.in + LAV_OFFSET).toFixed(3)}:${(c.out + LAV_OFFSET).toFixed(3)},asetpts=PTS-STARTPTS,aresample=48000,afade=t=in:d=0.02,afade=t=out:st=${(d - 0.03).toFixed(3)}:d=0.03[a${i}]`,
    );
  });
  parts.push(`${CUTS.map((_, i) => `[v${i}][a${i}]`).join('')}concat=n=${CUTS.length}:v=1:a=1[vc][ac]`);
  parts.push(
    '[ac]pan=mono|c0=0.5*c0+0.5*c1,highpass=f=80,afftdn=nf=-30,acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=3,loudnorm=I=-15:TP=-1.5:LRA=7,aresample=48000[ao]',
  );
  args.push('-filter_complex', parts.join(';'), '-map', '[vc]', '-map', '[ao]');
  args.push('-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k', 'public/cut.mp4');
  execFileSync('ffmpeg', args, {stdio: 'inherit'});
  console.log('wrote public/cut.mp4');
}
