// Jako = the Mini Me kit character, untouched. We pose it with the kit rig angles,
// walk it around the stage, swap kit faces for emotion and open the mouth from the voice loudness.
import React from 'react';
import M from './character.js';
import {FPS, PULL, PULL_D, T, VO_END, env} from './timing';
import {O, clamp, prog, outCubic, inCubic, backOut, seq, step, inOutCubic} from './ui';

M.setLook('medium');

// kit face minus its mouth, so we can drive the mouth ourselves
const MOUTH_RE = /<(path|ellipse) (d="M19[1-7],24[0-7][^"]*"|cx="200" cy="248")[^>]*\/>/;
const FACE_CACHE: Record<string, {eyes: string; mouth: string}> = {};
const face = (n: string) => {
  if (!FACE_CACHE[n]) {
    const svg: string = M.FACES[n]();
    const m = svg.match(MOUTH_RE);
    FACE_CACHE[n] = {eyes: m ? svg.replace(m[0], '') : svg, mouth: m ? m[0] : ''};
  }
  return FACE_CACHE[n];
};
const line = (w: number) => `stroke="${M.C.line}" stroke-width="${w}" stroke-linejoin="round" stroke-linecap="round"`;
const talkMouth = (faceName: string, o: number) => {
  if (faceName === 'surprised') return `<ellipse cx="200" cy="248" rx="${5 + 3 * o}" ry="${6.5 + 5 * o}" fill="${M.C.mouth}" ${line(3)}/>`;
  const w = 8 + 4 * o, h = 3 + 10 * o, top = faceName === 'happy' ? 240 : 242.5;
  const d = `M${200 - w},${top} Q200,${top + 1.5} ${200 + w},${top} Q${200 + w - 1},${top + h} 200,${top + h} Q${200 - w + 1},${top + h} ${200 - w},${top} Z`;
  const tongue = o > 0.4 ? `<ellipse cx="200" cy="${top + h - 2.6}" rx="${w * 0.5}" ry="${2.4 * o}" fill="#e2727c"/>` : '';
  return `<path d="${d}" fill="${M.C.mouth}"/>${tongue}<path d="${d}" fill="none" ${line(3)}/>`;
};

// Jako drops in from above as the camera finishes pulling back
export const LAND = PULL + PULL_D - 0.15;
// steps boards sit at these world x positions; Jako stands to the right of each
export const BX = [-1000, 0, 1000];

// arms: armL lifts toward screen-left, armR toward screen-right (14 / -14 = at rest)
const ARMS: [number, number, number][] = [
  [0, 150, -150], [LAND, 70, -70], [LAND + 0.2, 26, -26], [T.claude0 - 0.06, 140, -20], [T.opus - 0.06, 20, -150], [T.is, 70, -20], [T.cooking - 0.06, 152, -152],
  [T.i0, 26, -26], [T.motion0 - 0.06, 140, -18], [T.just - 0.06, 100, -18], [T.twenty - 0.06, 18, -152], [T.minutes + 0.35, 30, -30],
  [T.oh - 0.04, 40, -40], [T.also - 0.06, 18, -132], [T.claude2 + 0.35, 28, -28],
  [T.you0 - 0.06, 112, -18], [T.designer0 - 0.06, 52, -52], [T.you1, 20, -20], [T.motion1 - 0.06, 66, -66], [T.designer1 + 0.35, 22, -22],
  [T.one - 0.06, 152, -18], [T.drop + 0.1, 108, -18], [T.instagram + 0.25, 28, -28], [T.two - 0.06, 18, -152], [T.extra, 108, -18], [T.assets + 0.3, 26, -26],
  [T.three - 0.06, 152, -18], [T.paste, 104, -18], [T.give, 30, -30],
  [T.boom - 0.07, 156, -156], [T.professional, 30, -112], [T.animation + 0.35, 26, -26],
  [T.comment - 0.06, 18, -124], [T.send1 - 0.06, 26, -100], [T.full, 22, -62], [VO_END + 0.05, 18, -142],
];
const FACES: [number, string][] = [
  [0, 'surprised'], [LAND + 0.08, 'happy'], [T.i0, 'neutral'], [T.just, 'happy'], [T.twenty, 'surprised'], [T.minutes + 0.25, 'happy'],
  [T.oh, 'surprised'], [T.also, 'happy'], [T.you0, 'neutral'], [T.designer0, 'sideeye'], [T.you1, 'neutral'], [T.designer1, 'sideeye'],
  [T.one, 'happy'], [T.drop, 'neutral'], [T.instagram, 'happy'], [T.two, 'neutral'], [T.assets, 'happy'], [T.three, 'neutral'], [T.give, 'happy'],
  [T.boom, 'surprised'], [T.boom + 0.45, 'happy'], [T.comment, 'neutral'], [T.saas1, 'happy'], [T.send1, 'neutral'], [T.full, 'happy'],
];
const HEAD: [number, number][] = [
  [0, 0], [T.claude0, 5], [T.opus, -4], [T.cooking, 6], [T.i0, -5], [T.just, 6], [T.twenty, -6], [T.oh, 0], [T.also, -5], [T.you0, 5],
  [T.you1, -4], [T.one, 5], [T.two, -5], [T.three, 5], [T.boom, 0], [T.professional, -5], [T.comment, -4], [T.send1, 3], [VO_END, -4],
];
// where Jako stands on the floor: [time, value, move duration]
const JX: [number, number, number?][] = [
  [0, 240], [T.i0 - 0.04, 220, 0.6], [T.oh, 40, 0.5], [T.you0 - 0.06, 250, 0.5],
  [T.one - 0.1, BX[0] + 240, 0.55], [T.two - 0.14, BX[1] + 240, 0.55], [T.three - 0.14, BX[2] + 240, 0.55], [T.give - 0.1, BX[2] - 270, 0.6],
];
const JZ: [number, number, number?][] = [[0, 0], [T.oh, 60, 0.5], [T.you0 - 0.06, 0, 0.5], [T.boom, 40, 0.5]];
const JUMPS: [number, number, number][] = [[T.boom - 0.06, 0.62, 230]];
export const HITS = [LAND, T.claude0, T.cooking, T.twenty, T.also, T.designer0, T.designer1, T.one, T.two, T.three, T.instagram, T.assets, T.professional, T.saas1];
export const SHADES_OFF = T.oh;
export const SHADES_ON = T.boom + 0.32;
export const FLOOR = 380;
export const JSCALE = 1.32;

export const jakoPos = (t: number) => {
  const x = seq(t, JX, 0.5, inOutCubic);
  const z = seq(t, JZ, 0.4, inOutCubic);
  let y = 0;
  for (const [a, d, h] of JUMPS) {
    const jp = prog(t, a, d);
    if (jp > 0 && jp < 1) y -= h * Math.sin(Math.PI * jp);
  }
  // the drop-in: falls from above the frame and lands at LAND
  if (t < LAND) y -= 1500 * (1 - inCubic(prog(t, LAND - 0.4, 0.4)));
  return {x, z, y};
};

export const Jako: React.FC<{t: number; f: number; yaw: number}> = ({t, f, yaw}) => {
  if (t < LAND - 0.42) return null;
  const {x, z, y} = jakoPos(t);
  const prev = jakoPos(t - 1 / FPS);
  const speed = t > LAND + 0.1 ? Math.hypot(x - prev.x, z - prev.z) * FPS : 0;
  const walk = clamp(speed / 260);
  const w = t * ((2 * Math.PI) / 0.5);

  let armL = seq(t, ARMS.map(([k, l]) => [k, l]), 0.26, backOut) + Math.sin(t * 4.4) * 3 + walk * 18 * Math.cos(w);
  let armR = seq(t, ARMS.map(([k, , r]) => [k, r]), 0.26, backOut) - Math.sin(t * 4.4 + 0.6) * 3 + walk * 18 * Math.cos(w);
  if (t > VO_END + 0.05) armR += Math.sin((t - VO_END) * 14) * 20;
  let head = seq(t, HEAD, 0.3) + Math.sin(t * 2.2) * 2.5;
  // "no, no" head shake on each crossed-out word
  for (const a of [T.designer0, T.designer1]) if (t > a && t < a + 0.6) head += Math.sin((t - a) * 30) * 7 * (1 - (t - a) / 0.6);
  const legL = walk * 9 * Math.cos(w), legR = -walk * 9 * Math.cos(w);
  const legLy = -walk * 10 * Math.max(0, Math.sin(w)), legRy = -walk * 10 * Math.max(0, -Math.sin(w));
  const bodyY = -walk * 5 * Math.abs(Math.sin(w)) + Math.sin(t * 4.4) * 2;
  const faceName = step(t, FACES);

  // squash & stretch on hit words and on landings
  let bump = 0;
  for (const h of [...HITS, ...JUMPS.map(([a, d]) => a + d)]) {
    const d = t - h;
    if (d >= 0 && d < 0.6) bump += Math.exp(-d * 8) * Math.cos(d * 26) * (h === LAND ? 0.14 : 0.05);
  }
  if (t < LAND) bump = -0.06 * prog(t, LAND - 0.4, 0.4); // stretched while falling
  const sx = 1 + bump * 0.7, sy = 1 - bump;

  // mouth: loudness on twos, 4 steps
  const f2 = f - (f % 2);
  const e = Math.max(env(f2), env(f2 - 1) * 0.7);
  const open = Math.round(clamp((e - 0.1) / 0.55) * 3) / 3;
  const shadesOn = t < SHADES_OFF || t >= SHADES_ON;
  const blinking = !shadesOn && ['neutral', 'sideeye', 'surprised'].includes(faceName) && f % 87 < 3;
  const fc = face(blinking ? 'blink' : faceName);
  const mouth = open > 0 ? talkMouth(faceName, open) : face(faceName).mouth;
  (M.FACES as any).__talk = () => fc.eyes + mouth;

  let gx = 0, gy = 0, gr = 0, go = 1;
  if (t >= SHADES_OFF && t < SHADES_ON) {
    const p = prog(t, SHADES_OFF, 0.6);
    gx = -260 * p; gy = -420 * outCubic(p); gr = -420 * p; go = 1 - prog(t, SHADES_OFF + 0.4, 0.2);
  } else if (t >= SHADES_ON) {
    gy = -300 * (1 - backOut(prog(t, SHADES_ON, 0.3)));
  }
  const glasses = go > 0 ? `<g opacity="${go}" transform="rotate(${head} 200 262) translate(${gx} ${gy}) rotate(${gr} 200 206)"><g filter="url(#ink)">${M.glassesPart()}</g></g>` : '';
  const body = `<g transform="translate(0 ${bodyY}) translate(200 470) scale(${sx} ${sy}) translate(-200 -470)">${M.character({armL, armR, head, legL, legR, legLy, legRy, face: '__talk', glasses: false})}${glasses}</g>`;
  const svg = `${M.defs()}${body}`;

  const s = JSCALE;
  const air = clamp(-y / 230);
  return (
    <>
      {/* cast shadow: the silhouette laid flat on the floor, thrown back and right by the key light */}
      <O x={x} y={FLOOR - 1} z={z} rx={90} o={(1 - air * 0.85) * 0.2} anchor={`translate(${-300 * s}px, ${-697 * s}px) skewX(-28deg) scaleY(.62)`}
        style={{transformOrigin: `${300 * s}px ${697 * s}px`}}>
        <svg viewBox="-100 -200 600 720" width={600 * s} height={720 * s} style={{display: 'block', overflow: 'visible', filter: 'brightness(0) blur(7px)'}} dangerouslySetInnerHTML={{__html: svg}} />
      </O>
      {/* contact shadow */}
      <O x={x} y={FLOOR - 2} z={z} rx={90} o={1 - air * 0.7}>
        <div style={{width: 300 * (1 - air * 0.3), height: 300 * (1 - air * 0.3), borderRadius: '50%', background: 'radial-gradient(closest-side, rgba(46,30,16,.42), rgba(46,30,16,.12) 55%, rgba(46,30,16,0))'}} />
      </O>
      {/* billboard: mostly faces the camera, a little parallax left in */}
      <O x={x} y={FLOOR + y} z={z} ry={-yaw * 0.8} anchor={`translate(${-300 * s}px, ${-697 * s}px)`}>
        <svg viewBox="-100 -200 600 720" width={600 * s} height={720 * s} style={{display: 'block', overflow: 'visible', filter: 'drop-shadow(0 2px 2px rgba(46,30,16,.18))'}}
          dangerouslySetInnerHTML={{__html: svg}} />
      </O>
    </>
  );
};
