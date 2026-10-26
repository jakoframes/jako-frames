// Word timings come from the pause-cut voiceover (public/vo.wav) transcribed into vo.json.
import vo from './vo.json';

export const FPS = 30;
export const DURATION_S = 30;
export const VO_END: number = vo.duration;
export const ENV: number[] = vo.env;

export type Word = {w: string; s: number; e: number; k: string};
export const WORDS: Word[] = vo.words.map((w) => ({...w, k: w.w.toLowerCase().replace(/[^a-z0-9']/g, '')}));

export const at = (k: string, n = 0): number => {
  let c = 0;
  for (const w of WORDS) if (w.k === k && c++ === n) return w.s;
  throw new Error(`word not found: ${k} #${n}`);
};

export const T = {
  but0: at('but', 0), only: at('only'), one: at('one', 0), master: at('masterpiece'),
  and0: at('and', 0), totally: at('totally'), free: at('free'),
  here: at("here's"), thing: at('thing'),
  every: at('every'), design: at('design'), video: at('video'), code: at('code'), marketing: at('marketing'),
  needs: at('needs'), own: at('own'), skillOwn: at('skill', 0),
  but1: at('but', 1), waste: at('waste'), hours: at('hours'), search0: at('searching', 0), right: at('right'),
  this: at('this'), search1: at('searching', 1), scans: at('scans'), internet: at('internet'),
  finds: at('finds'), exactly: at('exactly'), skillsNeed: at('skills', 1), need: at('need', 1),
  its2: at("it's", 1), called: at('called'), find0: at('find', 0), skillName: at('skill', 2),
  grab: at('grab'), online: at('online'), but2: at('but', 2), prepared: at('prepared'), ready: at('ready'), file: at('file'),
  just: at('just'), download: at('download'), upload: at('upload'), skillsYour: at('skills', 2), done: at('done'),
  comment: at('comment'), find1: at('find', 1), send: at('send'),
};

// bg = scene color, accent = color of the spoken word in the caption
const RAW = [
  {id: 'hook', s: 0, bg: '#FFD23F', accent: '#FF3D8B'},
  {id: 'one', s: T.but0 - 0.06, bg: '#4CC9F0', accent: '#FFE14D'},
  {id: 'free', s: T.and0 - 0.08, bg: '#A3E635', accent: '#FF3D8B'},
  {id: 'thing', s: T.here - 0.08, bg: '#FF5DA2', accent: '#FFE14D'},
  {id: 'fields', s: T.every - 0.06, bg: '#B69CFF', accent: '#FFE14D'},
  {id: 'waste', s: T.but1 - 0.06, bg: '#FF7A3D', accent: '#FFE14D'},
  {id: 'scan', s: T.this - 0.06, bg: '#2EE6C5', accent: '#FF3D8B'},
  {id: 'reveal', s: T.its2 - 0.06, bg: '#5B2BE0', accent: '#FFE14D'},
  {id: 'file', s: T.grab - 0.3, bg: '#FFB627', accent: '#FF3D8B'},
  {id: 'install', s: T.just - 0.06, bg: '#3D8BFF', accent: '#FFE14D'},
  {id: 'cta', s: T.comment - 0.14, bg: '#FFD23F', accent: '#FF3D8B'},
];
export const SCENES = RAW.map((sc, i) => ({...sc, i, e: i + 1 < RAW.length ? RAW[i + 1].s : DURATION_S}));
export const SC = Object.fromEntries(SCENES.map((s) => [s.id, s])) as Record<string, (typeof SCENES)[number]>;
export const sceneAt = (t: number) => {
  let i = 0;
  while (i + 1 < SCENES.length && SCENES[i + 1].s <= t) i++;
  return SCENES[i];
};

// Caption groups: word counts in spoken order (96 words total).
const GROUP_SIZES = [3, 3, 2, 3, 2, 3, 1, 2, 2, 3, 2, 1, 1, 1, 1, 3, 1, 3, 1, 2, 3, 3, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 3, 2, 3, 2, 2, 3, 2, 3, 3, 1, 1, 2, 4];
export const GROUPS: number[][] = (() => {
  const out: number[][] = [];
  let i = 0;
  for (const n of GROUP_SIZES) {
    out.push(Array.from({length: n}, (_, j) => i + j).filter((k) => k < WORDS.length));
    i += n;
  }
  if (i < WORDS.length) out.push(Array.from({length: WORDS.length - i}, (_, j) => i + j));
  return out.filter((g) => g.length);
})();
export const KEYWORDS = new Set([2, 4, 5, 12, 16, 20, 23, 26, 27, 28, 29, 32, 33, 36, 37, 47, 53, 56, 63, 64, 69, 75, 76, 78, 80, 87, 88, 89]);
