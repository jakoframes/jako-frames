import React from 'react';
import {AbsoluteFill, Audio, OffthreadVideo, Sequence, staticFile, useCurrentFrame} from 'remotion';
import {CUTS, DURATION_S, FPS, PULL, PULL_D, SCENES, T, VO_END, VO_START, env, sceneAt} from './timing';
import {BALLS, Ball, C, Cube, FONT, Mono, O, Ring, Spark, clamp, inCubic, inOutCubic, outCubic, outExpo, prog, rnd, seq} from './ui';
import {BX, FLOOR, Jako, LAND, jakoPos} from './Jako';
import {RefClips, ScreenFX, WorldScenes, refFx} from './Scenes';
import {Subtitles} from './Subtitles';

export {DURATION_S, FPS} from './timing';

const P = 1100; // css perspective (camera distance)
export type Cam = {tx: number; ty: number; tz: number; d: number; yaw: number; pitch: number; roll: number};

// ---------- camera rig: keys are [time, value, duration] ----------
type K = [number, number, number?][];
const CAM: Record<keyof Cam, K> = {
  tx: [[0, 0], [T.you0 - 0.08, -30, 0.45], [T.you1 - 0.05, 30, 0.45], [T.one - 0.1, BX[0], 0.55], [T.two - 0.14, BX[1], 0.55], [T.three - 0.14, BX[2], 0.55]],
  ty: [[0, -600], [PULL, -210, PULL_D], [T.i0 - 0.06, -250, 0.6], [T.oh, -220, 0.5], [T.you0 - 0.08, -230, 0.45], [T.boom - 0.1, -245, 0.3], [T.comment - 0.12, -230, 0.5]],
  tz: [[0, 0]],
  d: [[0, 490], [0.01, 516, PULL - 0.01], [PULL, -40, PULL_D], [PULL + PULL_D, 50, 2.1], [T.i0 - 0.06, 90, 0.6], [T.twenty - 0.08, 130, 0.35],
    [T.oh - 0.04, -60, 0.5], [T.you0 - 0.08, 30, 0.45], [T.designer0 - 0.05, 80, 0.25], [T.you1 - 0.05, 20, 0.45], [T.designer1 - 0.05, 80, 0.25],
    [T.one - 0.1, 20, 0.55], [T.drop, 70, 1.6], [T.two - 0.14, 20, 0.55], [T.send0, 70, 1.2], [T.three - 0.14, 20, 0.55], [T.paste, 80, 1.3],
    [T.boom - 0.42, 150, 0.32], [T.boom - 0.02, -110, 0.28], [T.boom + 0.4, 20, 0.9], [T.comment - 0.12, 0, 0.6], [VO_END, 60, 1.6]],
  yaw: [[0, 0], [PULL, 14, PULL_D], [PULL + PULL_D, 4, 2.2], [T.i0 - 0.06, -3, 0.6], [T.twenty - 0.08, 4, 0.4], [T.oh - 0.04, 0, 0.5],
    [T.you0 - 0.08, -9, 0.45], [T.designer0, -4, 0.6], [T.you1 - 0.05, 7, 0.45], [T.designer1, 3, 0.6],
    [T.one - 0.1, 9, 0.55], [T.two - 0.14, 0, 0.55], [T.three - 0.14, -9, 0.55], [T.boom - 0.1, -3, 0.4], [T.comment - 0.12, 7, 0.6], [VO_END, 2, 1.5]],
  pitch: [[0, 0], [PULL, -4, PULL_D], [T.i0 - 0.06, -2, 0.6], [T.you0 - 0.08, 2, 0.45], [T.one - 0.1, -2, 0.5], [T.boom - 0.1, 3, 0.3], [T.comment - 0.12, -1, 0.6]],
  roll: [[0, 0], [PULL, -2.5, PULL_D * 0.6], [PULL + PULL_D, 0, 0.8], [T.oh, 2, 0.3], [T.you0, 0, 0.4], [T.designer0, -1.5, 0.2], [T.designer1, 1.5, 0.2],
    [T.one, 0, 0.4], [T.boom, -2, 0.15], [T.boom + 0.3, 0, 0.5]],
};
const IMPACTS: [number, number][] = [[LAND, 1], [T.cooking, 0.6], [T.twenty, 0.6], [T.also, 1], [T.designer0, 0.8], [T.designer1, 0.8],
  [T.one, 0.6], [T.two, 0.6], [T.three, 0.6], [T.boom, 2.2], [T.saas1, 0.8]];
export const camAt = (t: number): Cam => {
  const v = Object.fromEntries(Object.entries(CAM).map(([k, keys]) => [k, seq(t, keys, 0.4, inOutCubic)])) as Cam;
  // always-alive drift + handheld, off while the reference video is full screen
  const alive = outCubic(prog(t, PULL, 1.6));
  v.yaw += Math.sin(t * 0.6) * 2.5 * alive;
  v.pitch += Math.sin(t * 0.43) * 1.1 * alive;
  v.tx += Math.sin(t * 0.5) * 12 * alive;
  v.roll += (Math.sin(t * 3.1) * 0.22 + Math.sin(t * 5.3) * 0.13) * alive;
  v.ty += (Math.sin(t * 2.7) * 2 + Math.sin(t * 4.9) * 1.2) * alive;
  for (const [h, k] of IMPACTS) {
    const dd = t - h;
    if (dd < 0 || dd > 0.4) continue;
    const a = (1 - dd / 0.4) * 9 * k;
    v.tx += (rnd(`sx${Math.round(t * FPS)}`) - 0.5) * a;
    v.ty += (rnd(`sy${Math.round(t * FPS)}`) - 0.5) * a;
    v.d += 34 * k * Math.exp(-dd * 12);
  }
  return v;
};

// ---------- the studio: warm white cyclorama, floor grid, debossed wall word, floating specks ----------
const WALL_WORD: Record<string, string> = {intro: '', hook: 'COOKING', made: '20 MIN', meta: 'META', nodesign: 'ANYONE', steps: '', boom: 'BOOM', cta: 'COMMENT'};
const STEP_WORD = ['DROP', 'SEND', 'PASTE'];
const Stage: React.FC<{t: number; cam: Cam; on: number}> = ({t, cam, on}) => {
  const sc = sceneAt(t);
  const fade = outCubic(prog(t, sc.s, 0.4));
  const word = sc.id === 'steps' ? STEP_WORD[t < T.two - 0.14 ? 0 : t < T.three - 0.14 ? 1 : 2] : WALL_WORD[sc.id];
  const wordFade = sc.id === 'steps' ? outCubic(prog(t, t < T.two - 0.14 ? sc.s : t < T.three - 0.14 ? T.two - 0.14 : T.three - 0.14, 0.4)) : fade;
  const jp = jakoPos(t);
  const gx = ((-cam.tx % 160) + 160) % 160;
  return (
    <>
      <O x={cam.tx * 0.9} y={-500} z={-1700} o={on}>
        <div style={{width: 7400, height: 4400, background: 'radial-gradient(ellipse at 50% 58%, #FFFFFF 0%, #F7F4EF 34%, #E8E2D9 78%, #DCD5CA 100%)'}} />
      </O>
      <O x={cam.tx * 0.82} y={-660} z={-1650} o={on * wordFade}>
        <div style={{fontFamily: FONT.display, fontWeight: 800, fontSize: 560, letterSpacing: '-0.05em', color: '#EBE6DE', whiteSpace: 'nowrap', lineHeight: 1,
          textShadow: '0 -3px 0 rgba(255,255,255,.95), 0 6px 14px rgba(46,30,16,.10)'}}>{word}</div>
      </O>
      <O x={cam.tx} y={FLOOR} z={-500} rx={90} o={on}>
        <div style={{width: 6400, height: 6400, backgroundColor: 'rgba(255,255,255,.35)',
          backgroundImage: 'repeating-linear-gradient(0deg, rgba(20,18,23,.075) 0 2px, transparent 2px 160px), repeating-linear-gradient(90deg, rgba(20,18,23,.075) 0 2px, transparent 2px 160px)',
          backgroundPosition: `${gx}px 0px`,
          maskImage: 'radial-gradient(circle at 50% 50%, #000 0%, rgba(0,0,0,.55) 22%, transparent 46%)', WebkitMaskImage: 'radial-gradient(circle at 50% 50%, #000 0%, rgba(0,0,0,.55) 22%, transparent 46%)'}} />
      </O>
      {/* warm key-light pool that follows Jako */}
      <O x={jp.x} y={FLOOR - 1} z={jp.z} rx={90} o={on}>
        <div style={{width: 1300, height: 1300, borderRadius: '50%', background: 'radial-gradient(closest-side, rgba(238,106,58,.13), rgba(238,106,58,0))'}} />
      </O>
      {Array.from({length: 60}, (_, i) => {
        const y = -1350 + ((rnd(`py${i}`) * 1750 - t * (14 + rnd(`pv${i}`) * 26)) % 1750 + 1750) % 1750;
        const s = 7 + rnd(`ps${i}`) * 9;
        const kind = i % 4;
        const col = [C.ink, C.orange, C.cobalt, C.ink][i % 4];
        return (
          <O key={i} x={(rnd(`px${i}`) - 0.5) * 5200} y={y} z={-1300 + rnd(`pz${i}`) * 1500} rz={t * 40 * (rnd(`pr${i}`) - 0.5)} o={on * (0.18 + rnd(`po${i}`) * 0.32)}>
            {kind === 3
              ? <svg width={s * 1.6} height={s * 1.6} viewBox="0 0 10 10" style={{display: 'block'}}><path d="M5 1v8M1 5h8" stroke={col} strokeWidth={2} strokeLinecap="round" /></svg>
              : <div style={{width: s, height: s, borderRadius: kind === 1 ? 2 : '50%', background: col}} />}
          </O>
        );
      })}
    </>
  );
};

// ---------- solid décor floating around the stage (world-fixed, so camera moves give real parallax) ----------
type D = [kind: 'ball' | 'cube' | 'ring' | 'spark', tone: string, x: number, y: number, z: number, size: number];
const DECOR: D[] = [
  ['ball', 'orange', -640, -1080, -760, 170], ['ball', 'cobalt', 720, -1000, -980, 120], ['cube', 'ink', -780, -300, -840, 120], ['ring', 'orange', 800, -330, -1040, 230],
  ['spark', 'orange', 560, -1180, -620, 120], ['ball', 'white', -470, -120, -560, 100], ['ball', 'lime', 880, 40, -760, 84], ['ball', 'ink', -980, -760, -1240, 140],
  ['cube', 'orange', 300, -1240, -1300, 110], ['ball', 'cobalt', -1560, -980, -900, 150], ['ring', 'cobalt', -1320, -280, -1100, 200], ['spark', 'ink', -1700, -560, -700, 100],
  ['ball', 'orange', -1250, 80, -650, 90], ['cube', 'white', -1900, -1150, -1200, 140], ['ball', 'white', 1500, -1100, -820, 160], ['ball', 'ink', 1720, -420, -900, 110],
  ['cube', 'cobalt', 1320, -40, -760, 100], ['spark', 'orange', 1880, -900, -1100, 130], ['ring', 'ink', 1150, -1300, -1300, 180], ['ball', 'lime', 2050, -150, -1000, 120],
  ['ball', 'orange', 2300, -800, -1400, 200], ['ball', 'cobalt', -2250, -500, -1350, 180],
];
// a few out-of-focus objects close to the lens
const NEAR: [string, number, number, number, number][] = [['orange', -600, -980, 430, 120], ['cobalt', 640, 260, 400, 90], ['white', 1580, -760, 440, 130], ['ink', -1480, 120, 420, 80], ['lime', 420, -1180, 470, 70]];
const Decor: React.FC<{t: number; cam: Cam; on: number}> = ({t, cam, on}) => (
  <>
    {DECOR.map(([kind, tone, x, y, z, size], i) => {
      const bob = Math.sin(t * (0.7 + (i % 5) * 0.13) + i) * 22;
      const spin = t * (18 + (i % 4) * 9) * (i % 2 ? 1 : -1);
      const bb = {ry: -cam.yaw, rx: -cam.pitch};
      return (
        <O key={i} x={x} y={y + bob} z={z} o={on} {...(kind === 'ball' || kind === 'spark' ? bb : {})}
          {...(kind === 'cube' ? {rx: spin * 0.7 + i * 20, ry: spin + i * 33} : kind === 'ring' ? {rx: 62 + Math.sin(t + i) * 8, rz: spin * 0.3} : {})}>
          {kind === 'ball' && <Ball size={size} tone={tone} />}
          {kind === 'cube' && <Cube s={size} tone={tone} />}
          {kind === 'ring' && <Ring size={size} tone={tone} />}
          {kind === 'spark' && <Spark size={size} color={BALLS[tone]?.[1] ?? C.orange} rot={spin} />}
        </O>
      );
    })}
    {NEAR.map(([tone, x, y, z, size], i) => (
      <O key={`n${i}`} x={x} y={y + Math.sin(t * 0.9 + i) * 18} z={z} ry={-cam.yaw} rx={-cam.pitch} o={on} style={{filter: 'blur(9px)'}}>
        <Ball size={size} tone={tone} />
      </O>
    ))}
  </>
);

// ---------- opening: the montage's own colours, blurred, fill the frame around it; a warm light leak drifts across ----------
const IntroFill: React.FC<{t: number}> = ({t}) => {
  const o = 1 - prog(t, PULL - 0.05, 0.5);
  if (o <= 0) return null;
  return (
    <AbsoluteFill style={{opacity: o}}>
      <div style={{position: 'absolute', left: (1080 - 3413) / 2, top: 0, width: 3413, height: 1920, filter: 'blur(34px) saturate(1.15)', transform: `scale(${refFx(t).s.toFixed(4)})`}}>
        <RefClips file="ref-small.mp4" />
      </div>
      <AbsoluteFill style={{background: 'rgba(255,255,255,.12)'}} />
    </AbsoluteFill>
  );
};
const LightLeak: React.FC<{t: number}> = ({t}) => {
  const o = 1 - prog(t, PULL, 0.45);
  if (o <= 0) return null;
  return (
    <AbsoluteFill style={{mixBlendMode: 'screen', opacity: 0.5 * o,
      background: `radial-gradient(ellipse 70% 38% at ${-25 + t * 75}% ${34 + Math.sin(t * 3) * 10}%, rgba(255,150,90,.95), rgba(255,90,130,.4) 42%, rgba(0,0,0,0) 72%)`}} />
  );
};

// ---------- "this video?": the whole reel shrinks into an editor window ----------
const metaAmt = (t: number) => outExpo(prog(t, T.oh, 0.5)) * (1 - inOutCubic(prog(t, T.you0 - 0.2, 0.4)));
const META_S = 0.72;
const BARS = 72;
const BAR_H = Array.from({length: BARS}, (_, i) => {
  let m = 0;
  for (let f = Math.floor((i / BARS) * DURATION_S * FPS); f < ((i + 1) / BARS) * DURATION_S * FPS; f++) m = Math.max(m, env(f));
  return m;
});
const MetaChrome: React.FC<{t: number; m: number}> = ({t, m}) => {
  const s = 1 - (1 - META_S) * m;
  const w = 1080 * s, h = 1920 * s, left = (1080 - w) / 2, top = (1920 - h) / 2;
  const stamp = clamp((t - T.also + 0.02) / 0.22);
  const stampS = stamp < 1 ? 2.4 - 1.4 * outCubic(stamp) : 1;
  return (
    <>
      {/* title bar */}
      <div style={{position: 'absolute', left, width: w, top: top - 64 * m, height: 64, opacity: m, display: 'flex', alignItems: 'center', padding: '0 24px', boxSizing: 'border-box', gap: 12}}>
        {['#FF5F57', '#FEBC2E', '#28C840'].map((c) => <span key={c} style={{width: 18, height: 18, borderRadius: '50%', background: c}} />)}
        <div style={{flex: 1, textAlign: 'center', fontFamily: FONT.display, fontWeight: 700, fontSize: 28, color: '#F3F0EA', letterSpacing: '-0.01em'}}>this-video.mp4</div>
        <Spark size={30} color={C.orange} rot={t * 40} />
      </div>
      {/* timeline strip over the bottom of the window: the real voice waveform and a live playhead */}
      <div style={{position: 'absolute', left: left + 26, width: w - 52, top: top + h - 150, height: 124, opacity: m, borderRadius: 22, background: 'rgba(20,18,23,.86)',
        boxShadow: '0 20px 40px rgba(0,0,0,.35)', padding: '14px 18px', boxSizing: 'border-box', display: 'grid', gap: 10}}>
        <div style={{display: 'flex', gap: 4, height: 30}}>
          {SCENES.map((sc) => <div key={sc.id} style={{flex: sc.e - sc.s, borderRadius: 6, background: sc.id === 'meta' ? C.orange : 'rgba(255,255,255,.16)'}} />)}
        </div>
        <div style={{display: 'flex', alignItems: 'center', gap: 3, height: 52}}>
          {BAR_H.map((v, i) => <div key={i} style={{flex: 1, height: `${12 + v * 70}%`, borderRadius: 3, background: (i + 0.5) / BARS < t / DURATION_S ? C.orange : 'rgba(255,255,255,.35)'}} />)}
        </div>
        <div style={{position: 'absolute', top: 6, bottom: 6, left: 18 + (w - 52 - 36) * (t / DURATION_S), width: 4, borderRadius: 2, background: '#fff', boxShadow: '0 0 10px rgba(255,255,255,.6)'}} />
      </div>
      {stamp > 0 && (
        <div style={{position: 'absolute', left: left + w - 470, top: top + 120, transform: `rotate(-8deg) scale(${stampS})`, transformOrigin: '50% 50%', opacity: m * clamp(stamp * 3)}}>
          <div style={{border: `7px solid ${C.orange}`, borderRadius: 20, padding: 8, background: 'rgba(255,255,255,.92)', boxShadow: '0 20px 40px rgba(46,30,16,.28)'}}>
            <div style={{border: `2.5px solid ${C.orange}`, borderRadius: 12, padding: '14px 26px', display: 'flex', alignItems: 'center', gap: 18}}>
              <Spark size={70} color={C.orange} rot={-20} />
              <div style={{fontFamily: FONT.display, fontWeight: 800, fontSize: 62, lineHeight: 0.95, letterSpacing: '-0.02em', color: C.orange}}>MADE BY<br />CLAUDE</div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

// ---------- screen overlays ----------
const Overlays: React.FC<{t: number; f: number}> = ({t, f}) => {
  const hits: [number, number, number][] = [[T.boom, 0.85, 0.2], [LAND, 0.25, 0.2], ...CUTS.map((c, i): [number, number, number] => [c, i === 0 ? 0.3 : 0.5, 0.1])];
  const flash = hits.reduce((m, [h, a, d]) => Math.max(m, t >= h && t < h + d ? a * (1 - (t - h) / d) : 0), 0);
  return (
    <>
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 44%, rgba(120,80,40,0) 52%, rgba(120,80,40,.16) 100%)'}} />
      {flash > 0 && <AbsoluteFill style={{background: '#FFFFFF', opacity: flash}} />}
      <AbsoluteFill style={{opacity: 0.06,
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
  const on = outCubic(prog(t, PULL - 0.05, 0.6)); // studio fades in as the camera pulls back
  const m = metaAmt(t);
  const s = 1 - (1 - META_S) * m;
  return (
    <AbsoluteFill style={{background: m > 0 ? C.ink : C.bg, overflow: 'hidden'}}>
      {m > 0 && <AbsoluteFill style={{opacity: m, backgroundImage: 'radial-gradient(rgba(255,255,255,.10) 1.6px, transparent 1.6px)', backgroundSize: '30px 30px'}} />}
      {m > 0 && <AbsoluteFill style={{opacity: m, background: 'radial-gradient(ellipse at 50% 50%, rgba(238,106,58,.30), rgba(238,106,58,0) 60%)'}} />}
      <div style={{position: 'absolute', left: 0, top: 0, width: 1080, height: 1920, transform: `scale(${s})`, transformOrigin: '50% 50%', borderRadius: 52 * m / s, overflow: 'hidden',
        background: C.bg, boxShadow: m > 0 ? `0 40px 120px rgba(0,0,0,${0.55 * m})` : undefined}}>
        <IntroFill t={t} />
        <AbsoluteFill style={{perspective: P, perspectiveOrigin: '540px 960px', filter: blur > 0.3 ? `blur(${blur.toFixed(1)}px)` : undefined}}>
          <div style={{position: 'absolute', left: 540, top: 960, width: 0, height: 0, transformStyle: 'preserve-3d', transform: world}}>
            <Stage t={t} cam={cam} on={on} />
            <Decor t={t} cam={cam} on={on} />
            <WorldScenes t={t} cam={cam} />
            <Jako t={t} f={f} yaw={cam.yaw} />
          </div>
        </AbsoluteFill>
        <LightLeak t={t} />
        <ScreenFX t={t} />
        <Overlays t={t} f={f} />
      </div>
      {m > 0 && <MetaChrome t={t} m={m} />}
      <Subtitles t={t} />
      <Sequence from={Math.round(VO_START * FPS)}><Audio src={staticFile('vo.wav')} /></Sequence>
    </AbsoluteFill>
  );
};
