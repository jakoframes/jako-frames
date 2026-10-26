// Jako = the Mini Me kit character, untouched. We pose it with the kit rig angles,
// walk it around the stage, swap kit faces for emotion and open the mouth from the voice loudness.
import React from 'react';
import M from './character.js';
import {ENV, FPS, T} from './timing';
import {C, O, clamp, prog, outCubic, backOut, seq, step, inOutCubic} from './ui';

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

const ARMS: [number, number, number][] = [
  [0, 30, -30], [T.but0, 16, -16], [T.one - 0.06, 14, -155], [T.master - 0.06, 62, -62], [T.and0, 20, -20],
  [T.free - 0.1, 140, -140], [T.here - 0.04, 14, -128], [T.thing, 14, -50], [T.every + 0.1, 14, -14],
  [T.design - 0.06, 115, -14], [T.video - 0.06, 14, -115], [T.code - 0.06, 75, -14], [T.marketing - 0.06, 14, -75],
  [T.needs - 0.06, 55, -55], [T.but1, 50, -50], [T.hours - 0.06, 158, -158], [T.search0 + 0.25, 30, -30],
  [T.this - 0.06, 14, -120], [T.scans, 24, -24], [T.finds - 0.06, 14, -150], [T.skillsNeed, 30, -30],
  [T.its2, 14, -14], [T.find0 - 0.06, 150, -150], [T.skillName + 0.4, 20, -20], [T.grab - 0.1, 14, -105], [T.but2, 14, -95],
  [T.ready - 0.06, 14, -150], [T.just, 14, -110], [T.upload - 0.06, 14, -120], [T.skillsYour, 14, -100],
  [T.done - 0.06, 14, -156], [T.comment - 0.06, 14, -110], [T.find1 + 0.32, 14, -150], [T.send - 0.12, 14, -138],
];
const FACES: [number, string][] = [
  [0, 'surprised'], [T.but0, 'neutral'], [T.one - 0.06, 'happy'], [T.here, 'neutral'], [T.thing + 0.1, 'sideeye'],
  [T.every, 'neutral'], [T.own, 'happy'], [T.but1, 'shy'], [T.right - 0.1, 'sideeye'], [T.this, 'happy'],
  [T.scans, 'surprised'], [T.finds, 'happy'], [T.its2, 'neutral'], [T.find0 - 0.06, 'surprised'], [T.skillName + 0.2, 'happy'],
  [T.grab, 'neutral'], [T.but2, 'happy'], [T.just, 'neutral'], [T.skillsYour, 'happy'],
];
const HEAD: [number, number][] = [
  [0, 0], [T.design, -6], [T.video, 6], [T.code, -5], [T.marketing, 5], [T.needs, 0], [T.but1, -4], [T.this, 5],
  [T.its2, 0], [T.grab, 6], [T.but2, 4], [T.just, 5], [T.upload, 7], [T.skillsYour, 4], [T.comment, 4], [T.send, -3],
];
// where Jako stands on the floor: [time, value, move duration]
const JX: [number, number, number?][] = [
  [0, 0], [T.and0, -170, 0.5], [T.here, 0, 0.4], [T.but1, -330, 0.4], [T.waste + 0.1, 330, 1.9], [T.this, -300, 0.6],
  [T.its2, 0, 0.5], [T.grab - 0.2, -250, 0.5], [T.just, -250, 0.4], [T.comment - 0.1, 0, 0.6],
];
const JZ: [number, number, number?][] = [
  [0, 0], [T.here, 230, 0.35], [T.every, 0, 0.4], [T.just, 110, 0.4], [T.comment - 0.1, 60, 0.6],
];
export const HITS = [T.one, T.master, T.free, T.thing, T.design, T.video, T.code, T.marketing, T.hours, T.finds, T.find0, T.skillName, T.ready, T.done, T.find1];
export const SHADES_OFF = T.thing;
export const SHADES_ON = T.find1 + 0.36;
export const FLOOR = 380;
export const JSCALE = 1.45;

const jumpAt = T.find0 - 0.12;
export const jakoPos = (t: number) => {
  const x = seq(t, JX, 0.5, inOutCubic);
  const z = seq(t, JZ, 0.4, inOutCubic);
  const jp = prog(t, jumpAt, 0.55);
  const y = jp > 0 && jp < 1 ? -170 * Math.sin(Math.PI * jp) : 0;
  return {x, z, y};
};

export const Jako: React.FC<{t: number; f: number; yaw: number}> = ({t, f, yaw}) => {
  const {x, z, y} = jakoPos(t);
  const prev = jakoPos(t - 1 / FPS);
  const speed = Math.hypot(x - prev.x, z - prev.z) * FPS;
  const walk = clamp(speed / 260);
  const w = t * ((2 * Math.PI) / 0.62);

  let armL = seq(t, ARMS.map(([k, l]) => [k, l]), 0.26, backOut) + Math.sin(t * 4.4) * 3 + walk * 17 * Math.cos(w);
  let armR = seq(t, ARMS.map(([k, , r]) => [k, r]), 0.26, backOut) - Math.sin(t * 4.4 + 0.6) * 3 + walk * 17 * Math.cos(w);
  if (t > T.send - 0.12) armR += Math.sin((t - T.send) * 15) * 20;
  let head = seq(t, HEAD, 0.3) + Math.sin(t * 2.2) * 2.5;
  if (t > T.search0 && t < T.right) head += Math.sin(t * 22) * 4;
  const legL = walk * 8 * Math.cos(w), legR = -walk * 8 * Math.cos(w);
  const legLy = -walk * 9 * Math.max(0, Math.sin(w)), legRy = -walk * 9 * Math.max(0, -Math.sin(w));
  const bodyY = -walk * 4 * Math.abs(Math.sin(w)) + Math.sin(t * 4.4) * 2;
  const faceName = step(t, FACES);

  // squash & stretch on hit words and on the landing of the jump
  let bump = 0;
  for (const h of [...HITS, jumpAt + 0.55]) {
    const d = t - h;
    if (d >= 0 && d < 0.6) bump += Math.exp(-d * 8) * Math.cos(d * 26) * 0.05;
  }
  const sx = 1 + bump * 0.7, sy = 1 - bump;

  // mouth: loudness on twos, 4 steps
  const f2 = f - (f % 2);
  const env = Math.max(ENV[f2] ?? 0, (ENV[f2 - 1] ?? 0) * 0.7);
  const open = Math.round(clamp((env - 0.1) / 0.55) * 3) / 3;
  const shadesOn = t < SHADES_OFF || t >= SHADES_ON;
  const blinking = !shadesOn && ['neutral', 'sideeye', 'surprised'].includes(faceName) && f % 87 < 3;
  const fc = face(blinking ? 'blink' : faceName);
  const mouth = open > 0 ? talkMouth(faceName, open) : face(faceName).mouth;
  (M.FACES as any).__talk = () => fc.eyes + mouth;

  let gx = 0, gy = 0, gr = 0, go = 1;
  if (t >= SHADES_OFF && t < SHADES_ON) {
    const p = prog(t, SHADES_OFF, 0.6);
    gx = 260 * p; gy = -420 * outCubic(p); gr = 420 * p; go = 1 - prog(t, SHADES_OFF + 0.4, 0.2);
  } else if (t >= SHADES_ON) {
    gy = -300 * (1 - backOut(prog(t, SHADES_ON, 0.3)));
  }
  const glasses = go > 0 ? `<g opacity="${go}" transform="rotate(${head} 200 262) translate(${gx} ${gy}) rotate(${gr} 200 206)"><g filter="url(#ink)">${M.glassesPart()}</g></g>` : '';
  const svg = `${M.defs()}<g transform="translate(0 ${bodyY}) translate(200 470) scale(${sx} ${sy}) translate(-200 -470)">${M.character({armL, armR, head, legL, legR, legLy, legRy, face: '__talk', glasses: false})}${glasses}</g>`;

  const s = JSCALE;
  const air = clamp(-y / 170);
  return (
    <>
      {/* contact shadow on the floor */}
      <O x={x} y={FLOOR - 2} z={z} rx={90} o={1 - air * 0.6}>
        <div style={{width: 340 * (1 - air * 0.3), height: 340 * (1 - air * 0.3), borderRadius: '50%', background: 'radial-gradient(closest-side, rgba(0,0,0,.75), rgba(0,0,0,0))'}} />
      </O>
      {/* billboard: mostly faces the camera, a little parallax left in */}
      <O x={x} y={FLOOR + y} z={z} ry={-yaw * 0.8} anchor={`translate(${-300 * s}px, ${-697 * s}px)`}>
        <svg viewBox="-100 -200 600 720" width={600 * s} height={720 * s} style={{display: 'block', overflow: 'visible', filter: `drop-shadow(0 0 1.5px ${C.orangeHi}) drop-shadow(0 0 26px rgba(240,122,72,.35))`}}
          dangerouslySetInnerHTML={{__html: svg}} />
      </O>
    </>
  );
};
