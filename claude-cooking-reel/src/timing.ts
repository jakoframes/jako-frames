// Word timings come from the untouched take, mapped onto the pause-cut voiceover (public/vo.wav) in vo.json.
// The voice starts at VO_START, right after the full-screen highlight montage of the reference video.
import vo from './vo.json';

export const FPS = 30;
export const VO_START = 2.36;
export const VO_END: number = VO_START + vo.duration;
export const DURATION_S = 27.5;
// voice loudness per video frame (drives the mouth)
export const env = (f: number): number => vo.env[f - Math.round(VO_START * FPS)] ?? 0;

export type Word = {w: string; s: number; e: number; k: string};
export const WORDS: Word[] = vo.words.map((w) => ({w: w.w, s: w.s + VO_START, e: w.e + VO_START, k: w.w.toLowerCase().replace(/[^a-z0-9']/g, '')}));

export const at = (k: string, n = 0): number => {
  let c = 0;
  for (const w of WORDS) if (w.k === k && c++ === n) return w.s;
  throw new Error(`word not found: ${k} #${n}`);
};

// A few onsets are moved onto the loudness onsets in vo.json where whisper is off by more than 0.1 s.
export const T = {
  claude0: at('claude', 0), opus: at('opus'), five: at('5', 0), is: at('is'), cooking: at('cooking'),
  i0: at('i'), motion0: at('motion', 0), graphic: at('graphic'), just: at('just'), claude1: at('claude', 1), twenty: at('20') - 0.1, minutes: at('minutes'),
  oh: at('oh'), video: at('video'), also: at('also'), claude2: at('claude', 2),
  you0: at('you', 0), designer0: at('designer', 0), you1: at('you', 1), even: at('even'), motion1: at('motion', 1), designer1: at('designer', 1),
  one: at('one') - 0.1, drop: at('drop'), reference: at('reference'), found: at('found'), instagram: at('instagram'),
  two: at('two'), send0: at('send', 0), extra: at('extra'), assets: at('assets'),
  three: at('three') - 0.14, paste: at('paste'), prompts: at('prompts'), give: at('give'),
  boom: at('boom') + 0.17, professional: at('professional'), saas0: at('saas', 0), animation: at('animation'),
  comment: at('comment'), saas1: at('saas', 1), send1: at('send', 1), prompt: at('prompt'), full: at('full'), instructions: at('instructions'),
};

// the camera starts pulling back out of the full-screen reference video
export const PULL = 1.66;
export const PULL_D = 0.8;

// The reference, re-timed. While it is full screen: a speed-ramped montage of its most dynamic moments.
// From the pull-back on it simply keeps playing in the floating screen (to its end, then from the top).
// zoom/ox/oy frame a clip inside the screen; dx (% of width) slides it so off-centre action stays in the band
export type Clip = {from: number; src: number; rate: number; zoom?: number; ox?: number; oy?: number; dx?: number};
export const CLIPS: Clip[] = [
  {from: 0, src: 10.15, rate: 1.6},                        // 3D phone, the owl hops along the path
  {from: 0.36, src: 11.95, rate: 1.5, zoom: 1.12, oy: 45}, // the chest bursts into the sun
  {from: 0.7, src: 13.35, rate: 1.8, zoom: 1.18, oy: 58},  // streak flips 0 → 1
  {from: 1.04, src: 16.9, rate: 2, dx: 16},                // Repeat → Animate (the list sits on the left)
  {from: 1.36, src: 18.95, rate: 1.3},                     // the owl's eyes turn red
  {from: PULL, src: 18.95 + (PULL - 1.36) * 1.3, rate: 1},
  {from: PULL + 23 - (18.95 + (PULL - 1.36) * 1.3), src: 0, rate: 1},
];
export const CUTS = CLIPS.slice(0, 5).map((c) => c.from);

const RAW = [
  {id: 'intro', s: 0},
  {id: 'hook', s: PULL},
  {id: 'made', s: T.i0 - 0.06},
  {id: 'meta', s: T.oh - 0.04},
  {id: 'nodesign', s: T.you0 - 0.08},
  {id: 'steps', s: T.one - 0.1},
  {id: 'boom', s: T.boom - 0.1},
  {id: 'cta', s: T.comment - 0.12},
];
export const SCENES = RAW.map((sc, i) => ({...sc, i, e: i + 1 < RAW.length ? RAW[i + 1].s : DURATION_S}));
export const SC = Object.fromEntries(SCENES.map((s) => [s.id, s])) as Record<string, (typeof SCENES)[number]>;
export const sceneAt = (t: number) => {
  let i = 0;
  while (i + 1 < SCENES.length && SCENES[i + 1].s <= t) i++;
  return SCENES[i];
};
