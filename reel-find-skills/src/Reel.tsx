import React from 'react';
import {AbsoluteFill, Audio, staticFile, useCurrentFrame} from 'remotion';
import {FPS, GROUPS, KEYWORDS, SC, T, VO_END, WORDS, sceneAt} from './timing';
import {C, FONT, Mono, O, clamp, inOutCubic, outCubic, outExpo, pop, prog, rnd, seq} from './ui';
import {FLOOR, Jako, jakoPos} from './Jako';
import {WorldScenes} from './Scenes';

export {DURATION_S, FPS} from './timing';

const P = 1100; // css perspective (camera distance)

// ---------- camera rig: keys are [time, value, duration] ----------
type K = [number, number, number?][];
const CAM: Record<'tx' | 'ty' | 'tz' | 'd' | 'yaw' | 'pitch' | 'roll', K> = {
  tx: [[0, 0], [T.and0, -110, 0.5], [T.here, 0, 0.3], [T.design - 0.1, -150, 0.35], [T.video - 0.1, 150, 0.35], [T.code - 0.1, -150, 0.35],
    [T.marketing - 0.1, 150, 0.35], [T.needs, 0, 0.5], [T.but1, -200, 0.4], [T.waste + 0.1, 200, 1.9], [T.this, 90, 0.5], [T.its2, 0, 0.4],
    [T.grab - 0.2, 70, 0.5], [T.just, 40, 0.4], [T.comment - 0.1, 0, 0.6]],
  ty: [[0, -280], [T.here, -130, 0.3], [T.every, -300, 0.45], [T.code - 0.1, -230, 0.35], [T.needs, -300, 0.5], [T.its2, -560, 0.35],
    [T.find0 - 0.05, -330, 0.7], [T.grab - 0.2, -290, 0.5], [T.comment - 0.1, -280, 0.6]],
  tz: [[0, 0], [T.here, 230, 0.3], [T.every, 0, 0.45]],
  d: [[0, 0], [T.but0, 90, 2.4], [T.one - 0.05, 230, 0.3], [T.master - 0.1, 40, 0.6], [T.and0, -70, 0.5], [T.free - 0.1, 70, 0.3],
    [T.here, 430, 0.3], [T.every, -160, 0.45], [T.needs, -230, 0.8], [T.but1, -150, 0.4], [T.this, -170, 0.5], [T.finds, -60, 1.3],
    [T.its2, -540, 0.35], [T.find0 - 0.05, -190, 0.7], [T.grab - 0.2, -130, 0.5], [T.just, -60, 0.4], [T.upload - 0.1, 40, 0.5],
    [T.done, 0, 0.4], [T.comment - 0.1, -170, 0.6], [VO_END, -60, 1.1]],
  yaw: [[0, 22], [0.01, -4, 2.0], [T.but0, 10, 2.5], [T.and0, -20, 0.45], [T.here, 0, 0.3], [T.design - 0.1, 9, 0.35], [T.video - 0.1, -9, 0.35],
    [T.code - 0.1, 11, 0.35], [T.marketing - 0.1, -11, 0.35], [T.needs, 0, 0.5], [T.but1, 14, 0.4], [T.waste + 0.1, -14, 1.9], [T.this, -20, 0.5],
    [T.finds, -6, 1.5], [T.its2, 0, 0.35], [T.grab - 0.2, 16, 0.5], [T.but2, 6, 1.2], [T.just, -8, 0.4], [T.skillsYour - 0.12, 8, 0.45],
    [T.comment - 0.1, 0, 0.6]],
  pitch: [[0, -8], [0.01, 0, 2.2], [T.here, 4, 0.3], [T.every, 0, 0.4], [T.but1, 5, 0.4], [T.this, 0, 0.4], [T.its2, -9, 0.35], [T.find0 - 0.05, 2, 0.7], [T.grab - 0.2, 0, 0.5]],
  roll: [[0, -4], [0.01, 0, 2.2], [T.here, 3, 0.3], [T.every, 0, 0.4], [T.hours, -2, 0.2], [T.this, 0, 0.4], [T.find0, -2, 0.2], [T.skillName, 0, 0.4]],
};
const IMPACTS = [T.one, T.free, T.find0, T.skillName, T.done, T.hours, VO_END + 0.2];
const camAt = (t: number) => {
  const v = Object.fromEntries(Object.entries(CAM).map(([k, keys]) => [k, seq(t, keys, 0.4, inOutCubic)])) as Record<keyof typeof CAM, number>;
  v.d += -750 * (1 - outCubic(prog(t, 0, 2.0))); // hook fly-in
  // always-alive drift + handheld
  const hand = t > SC.waste.s && t < SC.waste.e ? 2.5 : 1;
  v.yaw += Math.sin(t * 0.6) * 3;
  v.pitch += Math.sin(t * 0.43) * 1.2;
  v.tx += Math.sin(t * 0.5) * 12;
  v.roll += (Math.sin(t * 3.1) * 0.25 + Math.sin(t * 5.3) * 0.15) * hand;
  v.ty += (Math.sin(t * 2.7) * 2 + Math.sin(t * 4.9) * 1.2) * hand;
  for (const h of IMPACTS) {
    const dd = t - h;
    if (dd < 0 || dd > 0.35) continue;
    const a = (1 - dd / 0.35) * 10;
    v.tx += (rnd(`sx${Math.round(t * FPS)}`) - 0.5) * a;
    v.ty += (rnd(`sy${Math.round(t * FPS)}`) - 0.5) * a;
    v.d += 40 * Math.exp(-dd * 12);
  }
  return v;
};

// ---------- the stage: floor grid, back wall with a giant word, dust ----------
const WALL_WORD: Record<string, string> = {hook: 'SKILLS', one: 'ONE', free: 'FREE', thing: 'REAL TALK', fields: 'EVERY FIELD', waste: 'HOURS', scan: 'SEARCH', reveal: 'FIND SKILLS', file: 'READY', install: 'INSTALL', cta: 'COMMENT'};
const GLOW: Record<string, string> = {waste: '240,82,82', scan: '110,139,255'};
const Stage: React.FC<{t: number}> = ({t}) => {
  const sc = sceneAt(t);
  const fade = outCubic(prog(t, sc.s, 0.35));
  const glow = GLOW[sc.id] ?? '240,122,72';
  const jp = jakoPos(t);
  return (
    <>
      <O x={0} y={-500} z={-1700}>
        <div style={{width: 7000, height: 4200, background: `radial-gradient(ellipse at 50% 55%, rgba(${glow},.30), rgba(${glow},.06) 35%, rgba(0,0,0,0) 60%), ${C.bg0}`}} />
      </O>
      <O x={0} y={-640} z={-1650} o={fade}>
        <div style={{fontFamily: FONT.display, fontWeight: 800, fontSize: 620, letterSpacing: '-0.05em', color: 'transparent', WebkitTextStroke: '3px rgba(244,238,230,.09)', whiteSpace: 'nowrap', lineHeight: 1}}>{WALL_WORD[sc.id]}</div>
      </O>
      <O x={0} y={FLOOR} z={-400} rx={90}>
        <div style={{width: 6000, height: 6000, background: `radial-gradient(circle at 50% 50%, rgba(${glow},.22), rgba(0,0,0,0) 30%), repeating-linear-gradient(0deg, rgba(255,255,255,.07) 0 2px, transparent 2px 160px), repeating-linear-gradient(90deg, rgba(255,255,255,.07) 0 2px, transparent 2px 160px)`,
          maskImage: 'radial-gradient(circle at 50% 50%, #000 0%, rgba(0,0,0,.6) 25%, transparent 50%)', WebkitMaskImage: 'radial-gradient(circle at 50% 50%, #000 0%, rgba(0,0,0,.6) 25%, transparent 50%)'}} />
      </O>
      {/* warm key light pool that follows Jako */}
      <O x={jp.x} y={FLOOR - 1} z={jp.z} rx={90}>
        <div style={{width: 1100, height: 1100, borderRadius: '50%', background: `radial-gradient(closest-side, rgba(${glow},.28), rgba(0,0,0,0))`}} />
      </O>
      {Array.from({length: 70}, (_, i) => {
        const y = -1300 + ((rnd(`py${i}`) * 1800 - t * (20 + rnd(`pv${i}`) * 40)) % 1800 + 1800) % 1800;
        const s = 4 + rnd(`ps${i}`) * 7;
        return (
          <O key={i} x={(rnd(`px${i}`) - 0.5) * 3000} y={y} z={-1300 + rnd(`pz${i}`) * 1900}>
            <div style={{width: s, height: s, borderRadius: '50%', background: C.cream, opacity: 0.12 + rnd(`po${i}`) * 0.3, boxShadow: `0 0 ${s * 2}px rgba(255,220,200,.6)`}} />
          </O>
        );
      })}
    </>
  );
};

// ---------- captions: fixed, always on, current word on an orange marker ----------
const label = (i: number) => {
  if (i === 64) return 'Skills';
  if (i === 63) return 'Find';
  if (i === 89) return 'FIND';
  if (WORDS[i].k === 'called') return 'called…';
  return WORDS[i].w.replace(/[.,!?]/g, '');
};
const Caption: React.FC<{t: number}> = ({t}) => {
  let gi = 0;
  while (gi + 1 < GROUPS.length && WORDS[GROUPS[gi + 1][0]].s - 0.05 <= t) gi++;
  const g = GROUPS[gi];
  const gs = gi === 0 ? 0 : WORDS[g[0]].s - 0.05;
  const enter = outExpo(prog(t, gs, 0.25));
  return (
    <div style={{position: 'absolute', left: 50, right: 50, top: 862, transform: `translateY(calc(-50% + ${(1 - enter) * 14}px))`, opacity: 0.4 + 0.6 * enter,
      display: 'flex', flexWrap: 'wrap', justifyContent: 'center', alignItems: 'baseline', columnGap: 18}}>
      {g.map((wi) => {
        const w = WORDS[wi];
        const next = WORDS[wi + 1];
        const spoken = t >= w.s - 0.03;
        const current = spoken && (!next || t < next.s - 0.03);
        const key = KEYWORDS.has(wi);
        const hit = current ? pop(t, w.s - 0.03, {damping: 14, stiffness: 260}) : 0;
        // sans words get an orange marker; serif keywords just turn orange with a glow
        const marker = current && !key;
        return (
          <span key={wi} style={{position: 'relative', display: 'inline-block', fontFamily: key ? FONT.serif : FONT.display, fontStyle: key ? 'italic' : 'normal', fontWeight: key ? 400 : 800,
            fontSize: key ? 96 : 76, letterSpacing: key ? '-0.01em' : '-0.035em', lineHeight: 1.15, padding: key ? '0 14px 0 6px' : '0 10px',
            color: marker ? C.bg0 : key && spoken ? C.orange : C.cream, opacity: spoken ? 1 : 0.32,
            textShadow: marker ? 'none' : current ? `0 0 34px rgba(240,122,72,.9), 0 6px 30px rgba(0,0,0,.8)` : '0 6px 30px rgba(0,0,0,.8)', transform: `translateY(${-6 * hit}px) scale(${1 + (key ? 0.08 : 0) * hit})`}}>
            {marker && <span style={{position: 'absolute', left: 0, right: 0, top: '12%', bottom: '6%', borderRadius: 14, background: C.orange, transform: `scaleX(${0.6 + 0.4 * hit})`, zIndex: -1, boxShadow: '0 10px 30px rgba(240,122,72,.45)'}} />}
            {label(wi)}
          </span>
        );
      })}
    </div>
  );
};

// ---------- screen overlays ----------
const CHAPTER: Record<string, string> = {hook: 'claude skills', one: 'one skill', free: 'price', thing: 'real talk', fields: 'every field', waste: 'the problem', scan: 'the fix', reveal: 'the name', file: 'the file', install: 'install', cta: 'get it'};
const Overlays: React.FC<{t: number; f: number}> = ({t, f}) => {
  const sc = sceneAt(t);
  const sweepAt = [...Object.values(SC).map((s) => s.s).filter((s) => s > 0), T.find0, T.done];
  let sweep = 0, sx = 0;
  for (const a of sweepAt) {
    const p = prog(t, a, 0.45);
    if (p > 0 && p < 1) { sweep = Math.sin(p * Math.PI); sx = -600 + p * 2300; }
  }
  const flash = [T.find0, VO_END + 0.2].reduce((m, h) => Math.max(m, t >= h && t < h + 0.18 ? 0.5 * (1 - (t - h) / 0.18) : 0), 0);
  return (
    <>
      {sweep > 0 && <div style={{position: 'absolute', left: sx, top: -400, width: 380, height: 2800, transform: 'rotate(18deg)', background: 'linear-gradient(90deg, rgba(255,190,150,0), rgba(255,190,150,.16), rgba(255,190,150,0))', opacity: sweep}} />}
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 46%, rgba(0,0,0,0) 45%, rgba(0,0,0,.62) 100%)'}} />
      <div style={{position: 'absolute', left: 64, top: 246, display: 'flex', alignItems: 'center', gap: 14}}>
        <span style={{width: 12, height: 12, borderRadius: '50%', background: C.orange, opacity: 0.5 + 0.5 * Math.sin(t * 6)}} />
        <Mono size={24} color={C.cream} w={700}>{String(sc.i + 1).padStart(2, '0')}<span style={{color: C.muted}}> / 11 — {CHAPTER[sc.id].toUpperCase()}</span></Mono>
      </div>
      <div style={{position: 'absolute', left: 64, right: 64, top: 290, height: 3, borderRadius: 2, background: 'rgba(255,255,255,.1)'}}>
        <div style={{width: `${clamp(t / 30) * 100}%`, height: '100%', borderRadius: 2, background: C.orange}} />
      </div>
      {flash > 0 && <AbsoluteFill style={{background: '#FFE8DA', opacity: flash}} />}
      <AbsoluteFill style={{opacity: 0.09, mixBlendMode: 'overlay',
        backgroundImage: 'url("data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22300%22 height=%22300%22><filter id=%22n%22><feTurbulence type=%22fractalNoise%22 baseFrequency=%22.9%22 numOctaves=%222%22/></filter><rect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23n)%22/></svg>")',
        backgroundPosition: `${Math.round(rnd(`gx${f >> 1}`) * 300)}px ${Math.round(rnd(`gy${f >> 1}`) * 300)}px`}} />
    </>
  );
};

export const Reel: React.FC = () => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const cam = camAt(t);
  const prev = camAt(t - 1 / FPS);
  const speed = Math.abs(cam.yaw - prev.yaw) * 2.2 + Math.abs(cam.tx - prev.tx) / 14 + Math.abs(cam.d - prev.d) / 30 + Math.abs(cam.ty - prev.ty) / 14;
  const blur = clamp((speed - 2.5) * 0.6, 0, 3.5);
  const world = `translateZ(${cam.d}px) rotateZ(${cam.roll}deg) rotateX(${cam.pitch}deg) rotateY(${cam.yaw}deg) translate3d(${-cam.tx}px,${-cam.ty}px,${-cam.tz}px)`;
  return (
    <AbsoluteFill style={{background: C.bg0, overflow: 'hidden'}}>
      <AbsoluteFill style={{perspective: P, perspectiveOrigin: '540px 960px', filter: blur > 0.3 ? `blur(${blur.toFixed(1)}px)` : undefined}}>
        <div style={{position: 'absolute', left: 540, top: 960, width: 0, height: 0, transformStyle: 'preserve-3d', transform: world}}>
          <Stage t={t} />
          <WorldScenes t={t} />
          <Jako t={t} f={f} yaw={cam.yaw} />
        </div>
      </AbsoluteFill>
      <Overlays t={t} f={f} />
      <Caption t={t} />
      <Audio src={staticFile('vo.wav')} />
    </AbsoluteFill>
  );
};
