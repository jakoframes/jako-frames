// Builds the clean edit (public/cut.mp4) and timing data (src/data.json) from the source takes.
// Run from the project folder:  node plan/build.mjs [--no-video]
import {execFileSync} from 'node:child_process';
import {writeFileSync} from 'node:fs';

const SRC = 'C:/Users/acer/Downloads/Telegram Desktop';
const clip = (n) => `${SRC}/IMG_${n}.MOV`;

// Kept ranges in source seconds, in story order. Removed: 8987 19.5-24.66 (broken take, then a
// stumbled first "Міндетті түрде"),
// 8991 0-7.5 (first attempt, restarted), plus long pauses inside 8984/8987/8990.
const CUTS = [
  {clip: 8976, in: 1.18, out: 4.36},
  {clip: 8984, in: 1.12, out: 11.75},
  {clip: 8984, in: 12.08, out: 17.06},
  {clip: 8987, in: 1.4, out: 13.88},
  {clip: 8987, in: 14.18, out: 19.62},
  {clip: 8987, in: 24.66, out: 38.62},
  {clip: 8990, in: 0.62, out: 10.53},
  {clip: 8990, in: 10.87, out: 22.4},
  {clip: 8991, in: 7.5, out: 14.55},
];

// Speech islands (silencedetect -38dB, 0.12s) per clip, source seconds.
const ISLANDS = {
  8976: [[1.29, 4.22]],
  8984: [[1.24, 5.73], [6.07, 7.95], [8.23, 9.71], [9.85, 10.16], [10.48, 11.67], [12.18, 14.13], [14.36, 15.63], [15.81, 16.94]],
  8987: [[1.52, 3.1], [3.25, 9.08], [9.22, 9.73], [9.86, 11.82], [12.07, 13.78], [14.28, 15.98], [16.12, 19.54],
    [22.95, 24.59], [24.74, 28.6], [28.76, 29.41], [29.68, 34.1], [34.33, 36.5], [36.94, 38.49]],
  8990: [[0.74, 4.54], [4.86, 9.37], [9.52, 10.43], [10.97, 16.45], [16.82, 17.9], [18.21, 19.63], [19.95, 22.27]],
  8991: [[7.61, 14.38]],
};

// Corrected transcript: [clip, start, end, text]
const LINES = [
  [8976, 1.29, 4.22, 'Қазақстандағы негізгі ипотекалық бағдарламалар туралы айта кетсек.'],
  [8984, 1.24, 7.95, '«7-20-25» туралы айта кететін болсақ, бастапқы жарнасы 20%-дан аз емес, 25 жылға дейін беріледі.'],
  [8984, 8.23, 11.67, 'Өз баспанаңыздың құнының лимиті болады.'],
  [8984, 12.18, 16.94, 'Одан бөлек тұрақты расталған табыс пен осы бағдарламаға расталған сәйкестік керек.'],
  [8987, 1.52, 5.0, 'Екінші айта кетерлік программаның бірі — «Наурыз».'],
  [8987, 5.0, 13.78, 'Ол әлеуметтік осал топтардың ішіне кіретін қатысушыларға жылдық пайызы 7 пайыз болады, ал бастапқы жарнасы 10 пайыз.'],
  [8987, 14.28, 19.54, 'Ал басқа қатысушыларға жылдық пайызы 9, ал бастапқы жарнасы 20 пайыз болады.'],
  [8987, 24.74, 28.6, 'Міндетті түрде депозиттің шотында 2 миллион жатуы тиіс.'],
  [8987, 28.76, 30.95, 'Одан бөлек 19 жылға беріледі.'],
  [8987, 31.0, 38.49, 'Астана мен Алматы қалаларында 36 миллионға дейінгі үйлерді алуға болады, ал басқа қалаларда 30 миллионға дейінгі үйлерді қарастыруға болады.'],
  [8990, 0.74, 4.54, 'Ал «Отау» программасы туралы айта кететін болсақ, дәл сол «Наурыз» секілді.'],
  [8990, 4.86, 10.43, 'Әлеуметтік осал топтарға 7 пайыз, ал басқаларға 9 пайыз жылдық мөлшерлеме.'],
  [8990, 10.97, 16.45, 'Ал бастапқы жарна туралы айта кететін болсақ, бәріне ортақ 20 пайыз болады.'],
  [8990, 16.82, 22.27, 'Жинақ үлесі 50 пайыздан асқаннан кейін несие мөлшерлемесін азайтуды қарастыруға болады.'],
  [8991, 7.61, 14.38, 'Осыған ұқсас көптеген басқа да программалар бар, оның бәрін өзіңіз қарап, бас қатырғыңыз келмесе, Elite Finance компаниясына келіңіздер.'],
];

// ---- edit map: source time -> output time (seconds from start of cut.mp4)
let acc = 0;
const segs = CUTS.map((c) => {
  const s = {...c, start: acc, dur: c.out - c.in};
  acc += s.dur;
  return s;
});
const CUT_DUR = acc;
const toOut = (clipN, t) => {
  for (const s of segs) {
    if (s.clip !== clipN) continue;
    if (t >= s.in && t <= s.out) return s.start + (t - s.in);
  }
  // inside a removed gap: snap to the next kept start of this clip
  const next = segs.find((s) => s.clip === clipN && s.in > t);
  return next ? next.start : null;
};

// ---- word timing: spread words over the speech islands of their line, weighted by spoken length
const spokenWeight = (w) => {
  const digits = (w.match(/\d/g) || []).length;
  const letters = (w.replace(/[^\p{L}]/gu, '') || '').length;
  return Math.max(2, letters + digits * 4 + (w.includes('%') ? 5 : 0));
};

const words = [];
LINES.forEach(([clipN, a, b, text], li) => {
  const isl = ISLANDS[clipN]
    .map(([x, y]) => [Math.max(x, a), Math.min(y, b)])
    .filter(([x, y]) => y - x > 0.05);
  const speech = isl.reduce((n, [x, y]) => n + (y - x), 0);
  const toks = text.split(/\s+/).filter((t) => t !== '—');
  const total = toks.reduce((n, t) => n + spokenWeight(t), 0);
  // map a position along the concatenated speech timeline back to source time
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
    words.push({w: t, line: li, s: +toOut(clipN, s).toFixed(3), e: +toOut(clipN, e).toFixed(3)});
  });
});

// ---- subtitle chunks: ≤3 words, ≤22 chars, break after punctuation and at line ends
const chunks = [];
let cur = [];
const flush = () => {
  if (cur.length) chunks.push(cur);
  cur = [];
};
words.forEach((w, i) => {
  const next = words[i + 1];
  cur.push(i);
  const len = cur.map((k) => words[k].w).join(' ').length;
  const punct = /[,.!?»—]$/.test(w.w);
  const lineEnd = !next || next.line !== w.line;
  const nextLen = next ? len + 1 + next.w.length : 0;
  if (lineEnd || punct || cur.length >= 3 || nextLen > 22) flush();
});
flush();
const subChunks = chunks.map((ids, i) => {
  const first = words[ids[0]];
  const last = words[ids[ids.length - 1]];
  const nextStart = chunks[i + 1] ? words[chunks[i + 1][0]].s : CUT_DUR;
  const end = Math.min(nextStart, last.e + 0.45);
  return {ids, s: first.s, e: +end.toFixed(3)};
});

// ---- graphic cues: first word matching each pattern, searched in story order
const cue = (re, after = 0) => {
  const w = words.find((x) => x.s >= after && re.test(x.w));
  if (!w) throw new Error('cue not found: ' + re);
  return w.s;
};
const cues = {};
cues.title = cue(/Қазақстандағы/);
cues.p725 = cue(/7-20-25/);
cues.down20 = cue(/20%/, cues.p725);
cues.years25 = cue(/^25$/, cues.p725);
cues.limit = cue(/лимиті/, cues.p725) - 0.6;
cues.income = cue(/табыс/, cues.p725) - 0.4;
cues.match = cue(/сәйкестік/, cues.p725) - 0.5;
cues.nauryz = cue(/Наурыз/);
cues.nauryzVuln = cue(/әлеуметтік/i, cues.nauryz);
cues.nauryz7 = cue(/^7$/, cues.nauryz);
cues.nauryz10 = cue(/^10$/, cues.nauryz);
cues.nauryzOther = cue(/басқа/, cues.nauryz);
cues.nauryz9 = cue(/^9,?$/, cues.nauryz);
cues.nauryz20 = cue(/^20$/, cues.nauryz);
cues.deposit = cue(/депозиттің/);
cues.deposit2m = cue(/^2$/, cues.deposit);
cues.years19 = cue(/^19$/);
cues.cities = cue(/Астана/);
cues.city36 = cue(/^36$/);
cues.city30 = cue(/^30$/);
cues.otau = cue(/Отау/);
cues.otauRates = cue(/Әлеуметтік/, cues.otau);
cues.otau9 = cue(/^9$/, cues.otau);
cues.otauDown = cue(/жарна$/, cues.otau);
cues.otau20 = cue(/^20$/, cues.otau);
cues.savings = cue(/Жинақ/);
cues.savings50 = cue(/^50$/, cues.savings);
cues.savingsDown = cue(/азайтуды/, cues.savings);
cues.cta = cue(/Осыған/);
cues.ctaBrand = cue(/Elite/);

writeFileSync(
  'src/data.json',
  JSON.stringify({cutDur: +CUT_DUR.toFixed(3), segs: segs.map(({start, dur}) => ({start: +start.toFixed(3), dur: +dur.toFixed(3)})), words, chunks: subChunks, cues}, null, 1),
);
console.log('cut duration', CUT_DUR.toFixed(2), 's,', words.length, 'words,', subChunks.length, 'chunks');

// ---- video: trim, normalise to 30fps 1080x1920, short audio fades on every cut, voice polish
if (!process.argv.includes('--no-video')) {
  const inputs = [...new Set(CUTS.map((c) => c.clip))];
  const args = ['-v', 'error', '-y'];
  inputs.forEach((n) => args.push('-i', clip(n)));
  const parts = [];
  CUTS.forEach((c, i) => {
    const k = inputs.indexOf(c.clip);
    const d = (c.out - c.in).toFixed(3);
    parts.push(
      `[${k}:v]trim=${c.in}:${c.out},setpts=PTS-STARTPTS,fps=30,scale=1080:1920,setsar=1[v${i}]`,
      `[${k}:a]atrim=${c.in}:${c.out},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st=${(+d - 0.03).toFixed(3)}:d=0.03[a${i}]`,
    );
  });
  const cat = CUTS.map((_, i) => `[v${i}][a${i}]`).join('');
  parts.push(`${cat}concat=n=${CUTS.length}:v=1:a=1[vc][ac]`);
  parts.push(
    `[ac]highpass=f=80,afftdn=nf=-30,acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=3,loudnorm=I=-15:TP=-1.5:LRA=7,aresample=48000[ao]`,
  );
  args.push('-filter_complex', parts.join(';'), '-map', '[vc]', '-map', '[ao]');
  args.push('-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k', 'public/cut.mp4');
  execFileSync('ffmpeg', args, {stdio: 'inherit'});
  console.log('wrote public/cut.mp4');
}
