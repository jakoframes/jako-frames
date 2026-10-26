// World-space scene art. Units are px; y grows down; the floor is at FLOOR (380).
// At the resting camera (ty ≈ -230) world y ≈ screenY - 1190, so the graphics band (screen 260–900) is y ≈ -930…-290.
import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, Sequence, staticFile} from 'remotion';
import M from './character.js';
import {CLIPS, CUTS, DURATION_S, FPS, PULL, PULL_D, SC, T, VO_END} from './timing';
import {BX} from './Jako';
import type {Cam} from './Reel';
import {Ball, Big, C, Card, Cursor, FONT, Flame, Icon, Marker, Mono, O, SHADOW, Spark, Text, clamp, inCubic, inOutCubic, lerp, outCubic, outExpo, pop, prog, rnd, seq, wobble} from './ui';

type R = {t: number; cam: Cam};
type K = [number, number, number?][];

// visible window of a scene, plus k = exit envelope (1 → 0) for every object in it
const win = (t: number, id: string, exit = 0.3) => {
  const sc = SC[id];
  if (t < sc.s - 0.05 || t > sc.e + exit) return null;
  return {s: sc.s, e: sc.e, k: 1 - inCubic(clamp((t - sc.e) / exit))};
};
// enter from depth: z offset / tilt / opacity for an element that appears at `a`
const enter = (t: number, a: number, d = 0.5) => {
  const p = outExpo(prog(t, a, d));
  return {p, dz: -520 * (1 - p), rx: 24 * (1 - p), o: clamp(p * 1.6)};
};
// slam-in: arrives big and soft, lands with a small wobble
const slam = (t: number, a: number, d = 0.26, from = 2.2) => {
  const p = prog(t, a, d);
  return {p, s: lerp(from, 1, outCubic(p)) + wobble(t, a + d, 24, 9) * 0.05, o: clamp(p * 3), blur: (1 - outCubic(p)) * 12};
};
const soft = (b: number) => (b > 0.4 ? {filter: `blur(${b.toFixed(1)}px)`} : undefined);
// an element placed in a parent's pixel space (x, y = its centre), still part of the 3D world
const Free: React.FC<{x: number; y: number; z?: number; rz?: number; s?: number; o?: number; children: React.ReactNode}> = ({x, y, z = 0, rz = 0, s = 1, o = 1, children}) =>
  o <= 0.001 ? null : (
    <div style={{position: 'absolute', left: 0, top: 0, opacity: o, transformStyle: 'preserve-3d', transform: `translate3d(${x}px,${y}px,${z}px) translate(-50%,-50%) rotateZ(${rz}deg) scale(${s})`}}>{children}</div>
  );
const Check: React.FC<{size?: number}> = ({size = 34}) => (
  <div style={{width: size, height: size, borderRadius: '50%', background: C.green, display: 'grid', placeItems: 'center', flex: 'none', boxShadow: '0 4px 10px rgba(24,169,87,.35)'}}>
    <Icon name="check" size={size * 0.6} color="#fff" sw={3} />
  </div>
);
const Chip: React.FC<{children: React.ReactNode; bg?: string; color?: string; size?: number}> = ({children, bg = C.paper, color = C.ink, size = 22}) => (
  <div style={{display: 'inline-flex', alignItems: 'center', gap: 10, padding: '10px 18px', borderRadius: 999, background: bg, boxShadow: SHADOW, fontFamily: FONT.mono, fontWeight: 700, fontSize: size, color, whiteSpace: 'nowrap'}}>{children}</div>
);
const Avatar: React.FC<{size: number}> = ({size}) => (
  <div style={{width: size, height: size, borderRadius: '50%', overflow: 'hidden', flex: 'none', background: '#EFE9DF', boxShadow: `0 0 0 3px #fff, 0 0 0 5px ${C.orange}`}}
    dangerouslySetInnerHTML={{__html: M.svg(M.defs() + M.avatarScene('#efe9df', {glasses: true}), M.AVATAR_VB, `width="${size}" height="${size}"`)}} />
);

// ---------------------------------------------------------------- the reference video: full screen → floating screen in the studio
const REF_W = 860, REF_H = 484, BEZ = 14;
const SW = REF_W + 2 * BEZ, SH = REF_H + 2 * BEZ;
// feather (0 → 1) softens the top/bottom edges into the blurred fill while the video is full screen
const Screen: React.FC<{bz?: number; feather?: number; children: React.ReactNode}> = ({bz = 1, feather = 0, children}) => {
  const mask = feather > 0.01 ? `linear-gradient(180deg, transparent 0%, #000 ${(9 * feather).toFixed(1)}%, #000 ${(100 - 9 * feather).toFixed(1)}%, transparent 100%)` : undefined;
  return (
    <div style={{position: 'relative', width: SW, height: SH, transformStyle: 'preserve-3d'}}>
      {bz > 0 && [1, 2, 3, 4, 5].map((i) => <div key={i} style={{position: 'absolute', inset: 0, borderRadius: 32, background: i === 5 ? '#CFC8BD' : '#E3DDD4', transform: `translateZ(${-i * 3}px)`, opacity: bz}} />)}
      {bz > 0 && <div style={{position: 'absolute', inset: 0, borderRadius: 32, background: '#fff', boxShadow: SHADOW, opacity: bz}} />}
      <div style={{position: 'absolute', left: BEZ, top: BEZ, width: REF_W, height: REF_H, borderRadius: 18 * bz, overflow: 'hidden', background: feather > 0.5 ? 'transparent' : '#000',
        transform: 'translateZ(0.5px)', maskImage: mask, WebkitMaskImage: mask}}>{children}</div>
    </div>
  );
};
// design-tool selection: drawn box, square handles, size tag and a layer label
const Selection: React.FC<{t: number; a: number; label: number}> = ({t, a, label}) => {
  const w = SW + 24, h = SH + 24, per = 2 * (w + h);
  const draw = outCubic(prog(t, a, 0.4));
  const pts = [[0, 0], [w / 2, 0], [w, 0], [w, h / 2], [w, h], [w / 2, h], [0, h], [0, h / 2]];
  return (
    <div style={{position: 'absolute', left: -12, top: -12, width: w, height: h, transform: 'translateZ(6px)'}}>
      <svg width={w} height={h} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}>
        <rect x={0} y={0} width={w} height={h} fill="none" stroke={C.cobalt} strokeWidth={3.5} strokeDasharray={per} strokeDashoffset={per * (1 - draw)} />
        {pts.map(([x, y], i) => {
          const p = pop(t, a + 0.12 + i * 0.03, {damping: 12, stiffness: 260});
          return <rect key={i} x={x - 10 * p} y={y - 10 * p} width={20 * p} height={20 * p} fill="#fff" stroke={C.cobalt} strokeWidth={3.5} />;
        })}
      </svg>
      {/* layer label above the box, size label centred under it (it gives way when the Claude card arrives) */}
      <div style={{position: 'absolute', left: 0, top: -84, transform: `scale(${label})`, transformOrigin: '0% 100%'}}>
        <div style={{display: 'inline-flex', alignItems: 'center', gap: 14, padding: '12px 26px', borderRadius: 999, background: C.cobalt, boxShadow: SHADOW}}>
          <Icon name="play" size={26} color="#fff" fill="#fff" sw={1.5} />
          <Text size={38} w={800} color="#fff">motion graphic</Text>
        </div>
      </div>
      <div style={{position: 'absolute', left: '50%', bottom: -58, transform: `translateX(-50%) scale(${pop(t, a + 0.2) * (1 - prog(t, T.just - 0.2, 0.15))})`, transformOrigin: '50% 0%'}}>
        <Chip bg={C.cobalt} color="#fff" size={22}>1920 × 1080</Chip>
      </div>
    </div>
  );
};
const RP: Record<'x' | 'y' | 'z' | 'ry' | 'rx', K> = {
  x: [[0, 0], [PULL, 20, PULL_D + 0.1], [T.i0 - 0.06, -30, 0.6], [T.you0 - 0.1, -260, 0.55]],
  y: [[0, -600], [PULL, -660, PULL_D + 0.1], [T.i0 - 0.06, -650, 0.6], [T.oh, -660, 0.5], [T.you0 - 0.1, -1500, 0.55]],
  z: [[0, 0], [PULL, -330, PULL_D + 0.1], [T.i0 - 0.06, -170, 0.6], [T.oh, -200, 0.5], [T.you0 - 0.1, -1000, 0.55]],
  ry: [[0, 0], [PULL, -14, PULL_D + 0.1], [T.i0 - 0.06, -5, 0.6], [T.oh, 0, 0.5], [T.you0 - 0.1, 50, 0.55]],
  rx: [[0, 0], [PULL, 3, PULL_D + 0.1], [T.i0 - 0.06, 0, 0.6], [T.you0 - 0.1, 35, 0.55]],
};
// the re-timed reference (see CLIPS): one Sequence per clip, each speed-ramped and framed on its own
export const RefClips: React.FC<{file: string}> = ({file}) => (
  <>
    {CLIPS.map((c, i) => {
      const a = Math.round(c.from * FPS), b = i + 1 < CLIPS.length ? Math.round(CLIPS[i + 1].from * FPS) : Math.round(DURATION_S * FPS);
      return (
        <Sequence key={i} from={a} durationInFrames={b - a} layout="none">
          <div style={{position: 'absolute', inset: 0, transform: `translateX(${c.dx ?? 0}%) scale(${c.zoom ?? 1})`, transformOrigin: `${c.ox ?? 50}% ${c.oy ?? 50}%`}}>
            <OffthreadVideo src={staticFile(file)} startFrom={Math.round(c.src * FPS)} playbackRate={c.rate} muted style={{width: '100%', height: '100%', display: 'block'}} />
          </div>
        </Sequence>
      );
    })}
  </>
);
// hook effects on every montage cut: punch-in, shake, whip blur into and out of the cut, RGB split
export const refFx = (t: number) => {
  let s = 1, x = 0, y = 0, bx = 0, dx = 0;
  if (t < PULL + 0.3) {
    CUTS.forEach((c, i) => {
      const d = t - c, dir = i % 2 ? 1 : -1;
      if (d >= 0) {
        s += 0.16 * Math.exp(-d * 9);
        dx += (i === 0 ? 7 : 16) * Math.exp(-d * 15); // a lighter split on frame one, the scroll-stopping frame
        if (d < 0.22) {
          const k = 1 - d / 0.22, f = Math.round(t * FPS);
          x += (rnd(`shx${f}`) - 0.5) * 30 * k;
          y += (rnd(`shy${f}`) - 0.5) * 22 * k;
        }
      }
      if (i > 0 && d >= -0.08 && d < 0) { const p = prog(t, c - 0.08, 0.08); bx += 26 * p; x -= 90 * p * dir; }
      if (i > 0 && d >= 0 && d < 0.07) { const q = 1 - d / 0.07; bx += 26 * q; x += 90 * q * dir; }
    });
  }
  return {s, x, y, bx, dx, on: bx > 0.4 || dx > 0.6};
};
const RefFX: React.FC<{id: string; bx: number; dx: number}> = ({id, bx, dx}) => (
  <svg width={0} height={0} style={{position: 'absolute'}}>
    <filter id={id} x="-5%" y="-5%" width="110%" height="110%" colorInterpolationFilters="sRGB">
      <feGaussianBlur in="SourceGraphic" stdDeviation={`${bx.toFixed(1)} 0`} result="b" />
      <feColorMatrix in="b" type="matrix" values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0" result="r" />
      <feOffset in="r" dx={dx.toFixed(1)} dy={0} result="r2" />
      <feColorMatrix in="b" type="matrix" values="0 0 0 0 0  0 1 0 0 0  0 0 0 0 0  0 0 0 1 0" result="g" />
      <feColorMatrix in="b" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0" result="bl" />
      <feOffset in="bl" dx={(-dx).toFixed(1)} dy={0} result="b2" />
      <feBlend in="r2" in2="g" mode="screen" result="rg" />
      <feBlend in="rg" in2="b2" mode="screen" />
    </filter>
  </svg>
);
const RefPanel: React.FC<R> = ({t}) => {
  if (t > T.you0 + 0.45) return null;
  const bz = outCubic(prog(t, PULL - 0.1, 0.5));
  const live = outCubic(prog(t, PULL, 1));
  const o = 1 - prog(t, T.you0 - 0.12, 0.25);
  const selA = T.motion0 - 0.05;
  const selO = 1 - prog(t, T.oh - 0.1, 0.25);
  const fx = refFx(t);
  return (
    <O x={seq(t, RP.x, 0.5)} y={seq(t, RP.y, 0.5) + Math.sin(t * 1.1) * 8 * live} z={seq(t, RP.z, 0.5)} ry={seq(t, RP.ry, 0.5) + Math.sin(t * 0.7) * 2 * live} rx={seq(t, RP.rx, 0.5)} o={o}>
      <Screen bz={bz} feather={1 - prog(t, PULL - 0.1, 0.35)}>
        {fx.on && <RefFX id="reffx" bx={fx.bx} dx={fx.dx} />}
        <div style={{position: 'absolute', inset: 0, transform: `translate(${fx.x.toFixed(1)}px, ${fx.y.toFixed(1)}px) scale(${fx.s.toFixed(4)})`, filter: fx.on ? 'url(#reffx)' : undefined}}>
          <RefClips file="ref.mp4" />
        </div>
      </Screen>
      {t > selA && selO > 0 && <div style={{position: 'absolute', left: 0, top: 0, opacity: selO, transformStyle: 'preserve-3d'}}><Selection t={t} a={selA} label={pop(t, T.graphic - 0.05)} /></div>}
    </O>
  );
};

// ---------------------------------------------------------------- 1. "Claude Opus 5.5 is cooking."
const Hook: React.FC<R> = ({t}) => {
  const w = win(t, 'hook', 0.35);
  if (!w) return null;
  const a = slam(t, T.claude0 - 0.04);
  const b = slam(t, T.opus - 0.04, 0.24, 1.8);
  const n = pop(t, T.five - 0.02, {damping: 11, stiffness: 220});
  const c = enter(t, T.is - 0.04, 0.4);
  const ck = slam(t, T.cooking - 0.04, 0.24, 1.6);
  return (
    <>
      <O x={-436} y={-735} z={80} anchor="translate(0,-50%)" s={a.s} o={a.o * w.k} style={soft(a.blur)}><Big size={200}>Claude</Big></O>
      <O x={362} y={-300} z={120} anchor="translate(-100%,-50%)" s={b.s} o={b.o * w.k} style={soft(b.blur)}>
        <div style={{display: 'flex', alignItems: 'baseline', gap: 28}}>
          <Big size={150} color={C.orange}>Opus</Big>
          <span style={{display: 'inline-block', transform: `scale(${n})`, transformOrigin: '30% 70%'}}><Big size={150} color={C.orange}>5.5</Big></span>
        </div>
      </O>
      <O x={-450} y={-20} z={c.dz} rx={c.rx} o={c.o * w.k} anchor="translate(0,-50%)">
        <div style={{display: 'flex', alignItems: 'center', gap: 20}}>
          <Big size={124} serif>is</Big>
          <span style={{display: 'inline-block', transform: `scale(${ck.s})`, opacity: ck.o, transformOrigin: '0% 60%'}}><Big size={124} serif color={C.orange}>cooking</Big></span>
          <div style={{opacity: ck.o, transform: `translateY(-16px) scale(${pop(t, T.cooking + 0.1, {damping: 10})})`}}><Flame size={70} t={t} /></div>
        </div>
      </O>
    </>
  );
};

// ---------------------------------------------------------------- 2. "I made this motion graphic with just Claude in 20 minutes."
const PROMPT = 'make this a SaaS animation';
const Made: React.FC<R> = ({t}) => {
  const w = win(t, 'made', 0.3);
  if (!w) return null;
  const comp = enter(t, T.just - 0.12, 0.45);
  const typed = PROMPT.slice(0, Math.max(0, Math.floor((t - T.just) / 0.022)));
  const cl = pop(t, T.claude1 - 0.03, {damping: 9, stiffness: 200});
  const tm = slam(t, T.twenty - 0.12, 0.24, 1.7);
  const secs = 1200 * outCubic(prog(t, T.twenty - 0.1, 0.5));
  const mm = String(Math.floor(secs / 60)).padStart(2, '0'), ss = String(Math.floor(secs % 60)).padStart(2, '0');
  const mn = enter(t, T.minutes - 0.05, 0.35);
  return (
    <>
      <O x={-97} y={-303} z={120 + comp.dz} rx={comp.rx} o={comp.o * w.k}>
        <Card w={570} h={150} radius={30}>
          <div style={{display: 'flex', alignItems: 'center', gap: 20, height: '100%', padding: '0 22px 0 26px'}}>
            <div style={{transform: `rotate(${cl * 90}deg) scale(${1 + 0.3 * Math.sin(Math.PI * clamp(cl))})`, flex: 'none'}}><Spark size={58} /></div>
            <div style={{flex: 1, display: 'grid', gap: 6, minWidth: 0}}>
              <Text size={32} w={800}>Claude</Text>
              <div style={{fontFamily: FONT.display, fontWeight: 500, fontSize: 22, color: C.muted, whiteSpace: 'nowrap', overflow: 'hidden'}}>{typed}<span style={{color: C.orange, opacity: Math.floor(t * 4) % 2 ? 0 : 1}}>|</span></div>
            </div>
            <div style={{width: 62, height: 62, borderRadius: '50%', background: C.orange, display: 'grid', placeItems: 'center', flex: 'none'}}><Icon name="up" size={30} color="#fff" sw={2.6} /></div>
          </div>
        </Card>
      </O>
      <O x={162} y={-714} z={200} s={tm.s} rz={-3} o={tm.o * w.k} style={soft(tm.blur)}>
        <Card w={310} h={176} radius={30}>
          <div style={{display: 'grid', justifyItems: 'center', alignContent: 'center', height: '100%', gap: 2}}>
            <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
              <Icon name="clock" size={46} color={C.orange} sw={2.4} />
              <div style={{fontFamily: FONT.display, fontWeight: 800, fontSize: 82, color: C.ink, letterSpacing: '-0.04em', lineHeight: 1, fontVariantNumeric: 'tabular-nums'}}>{mm}:{ss}</div>
            </div>
            <div style={{opacity: mn.o, transform: `translateY(${(1 - mn.p) * 12}px)`}}><Text size={44} serif color={C.orange}>minutes</Text></div>
          </div>
        </Card>
      </O>
    </>
  );
};

// ---------------------------------------------------------------- 3. "Oh, and this video?" (the window + stamp live in Reel.tsx)
const Meta: React.FC<R> = ({t}) => {
  const w = win(t, 'meta', 0.15);
  if (!w) return null;
  const e = slam(t, T.video - 0.12, 0.26, 1.7);
  const mk = outCubic(prog(t, T.video + 0.15, 0.3));
  return (
    <O x={40} y={-330} z={120} s={e.s} o={e.o * w.k} style={soft(e.blur)}>
      <div style={{display: 'flex', alignItems: 'baseline', gap: 26}}>
        <Big size={150} serif>this</Big>
        <Marker p={mk}><Big size={150} serif>video?</Big></Marker>
      </div>
    </O>
  );
};

// ---------------------------------------------------------------- 4. "You don't need to be a designer. You don't even need to be a motion designer."
const Strike: React.FC<{p: number; rot?: number}> = ({p, rot = -3}) => (
  <div style={{position: 'absolute', left: -24, right: -24, top: '46%', height: 20, borderRadius: 10, background: C.orange, transform: `rotate(${rot}deg) scaleX(${p})`, transformOrigin: 'left center', boxShadow: '0 8px 18px rgba(181,68,28,.35)'}} />
);
const PenCurve: React.FC<{p: number}> = ({p}) => (
  <svg width={760} height={220} viewBox="0 0 760 220" style={{display: 'block', overflow: 'visible'}}>
    <path d="M20,160 C180,20 330,220 480,110 S700,40 740,90" fill="none" stroke={C.cobalt} strokeWidth={4} strokeDasharray={1000} strokeDashoffset={1000 * (1 - p)} strokeLinecap="round" />
    {p > 0.5 && <><line x1={380} y1={40} x2={580} y2={180} stroke={C.cobalt} strokeWidth={2.5} /><circle cx={380} cy={40} r={8} fill={C.cobalt} /><circle cx={580} cy={180} r={8} fill={C.cobalt} /></>}
    {[[20, 160, 0], [480, 110, 0.5], [740, 90, 0.95]].map(([x, y, at], i) => p > at && <rect key={i} x={x - 10} y={y - 10} width={20} height={20} fill="#fff" stroke={C.cobalt} strokeWidth={3.5} />)}
  </svg>
);
const Easing: React.FC<{p: number}> = ({p}) => (
  <Card w={260} h={210} radius={26}>
    <svg width={260} height={210} viewBox="0 0 260 210" style={{display: 'block'}}>
      <path d="M36,30 L36,176 L230,176" fill="none" stroke="rgba(20,18,23,.18)" strokeWidth={2.5} />
      <path d="M36,176 C120,176 120,40 226,36" fill="none" stroke={C.orange} strokeWidth={5} strokeLinecap="round" strokeDasharray={320} strokeDashoffset={320 * (1 - p)} />
      <line x1={36} y1={176} x2={120} y2={176} stroke={C.ink} strokeWidth={2} /><circle cx={120} cy={176} r={8} fill={C.ink} />
      <line x1={226} y1={36} x2={120} y2={40} stroke={C.ink} strokeWidth={2} /><circle cx={120} cy={40} r={8} fill={C.ink} />
    </svg>
  </Card>
);
const NoDesign: React.FC<R> = ({t}) => {
  const w = win(t, 'nodesign', 0.3);
  if (!w) return null;
  // group A: "You don't need to be a" → "Designer", struck as the voice lands on it
  const aOut = 1 - inCubic(prog(t, T.you1 - 0.14, 0.18));
  const l1 = enter(t, T.you0 - 0.06, 0.4);
  const d1 = slam(t, T.you0 + 0.32, 0.26, 1.6);
  const st1 = outCubic(prog(t, T.designer0 + 0.02, 0.2));
  const sel = outCubic(prog(t, T.you0 + 0.5, 0.3));
  const fall1 = inCubic(prog(t, T.designer0 + 0.08, 0.7));
  // group B: "not even a" → "Motion Designer", struck again
  const l2 = enter(t, T.you1 - 0.04, 0.4);
  const m1 = slam(t, T.motion1 - 0.08, 0.24, 1.7);
  const d2 = slam(t, T.motion1 + 0.14, 0.24, 1.7);
  const st2 = outCubic(prog(t, T.designer1 + 0.02, 0.2));
  const fall2 = inCubic(prog(t, T.designer1 + 0.08, 0.7));
  const kf = prog(t, T.even, 0.9);
  return (
    <>
      {aOut > 0 && (
        <>
          <O x={0} y={-850} z={l1.dz} rx={l1.rx} o={l1.o * aOut * w.k}><Text size={58} w={700} color={C.ink2}>You don't need to be a</Text></O>
          <O x={0} y={-690} z={40} s={d1.s} o={d1.o * aOut * w.k} style={soft(d1.blur)}>
            <div style={{position: 'relative', opacity: 1 - 0.55 * st1}}>
              <Big size={170}>Designer</Big>
              {sel > 0 && st1 < 1 && (
                <div style={{position: 'absolute', left: -22, right: -22, top: -14, bottom: -18, border: `3px solid ${C.cobalt}`, opacity: sel * (1 - st1)}}>
                  {[[0, 0], [100, 0], [0, 100], [100, 100]].map(([x, y], i) => <span key={i} style={{position: 'absolute', left: `${x}%`, top: `${y}%`, width: 18, height: 18, marginLeft: -9, marginTop: -9, background: '#fff', border: `3px solid ${C.cobalt}`}} />)}
                </div>
              )}
            </div>
            <Strike p={st1} />
          </O>
          <O x={30} y={-470 + fall1 * 1300} z={70} rz={fall1 * 30} o={pop(t, T.you0 + 0.4) * aOut * w.k}><PenCurve p={prog(t, T.you0 + 0.45, 0.7)} /></O>
          <O x={-360} y={-400 + fall1 * 1500} z={150} rz={-10 + fall1 * 80} o={pop(t, T.you0 + 0.55) * aOut * w.k}>
            <div style={{width: 96, height: 96, borderRadius: 26, background: C.paper, boxShadow: SHADOW, display: 'grid', placeItems: 'center'}}><Icon name="pen" size={52} color={C.cobalt} sw={2} /></div>
          </O>
          <O x={-300} y={-130 + fall1 * 1400} z={100} rz={8 - fall1 * 60} o={pop(t, T.you0 + 0.65) * aOut * w.k}>
            <div style={{display: 'flex', gap: 10, padding: 14, borderRadius: 999, background: C.paper, boxShadow: SHADOW}}>
              {[C.orange, C.cobalt, C.lime, C.ink].map((c) => <span key={c} style={{width: 40, height: 40, borderRadius: '50%', background: c}} />)}
            </div>
          </O>
        </>
      )}
      {t > T.you1 - 0.1 && (
        <>
          <O x={0} y={-880} z={l2.dz} rx={l2.rx} o={l2.o * w.k}><Big size={84} serif color={C.orange}>not even a</Big></O>
          <O x={0} y={-725} z={40} s={m1.s} o={m1.o * w.k * (1 - 0.55 * st2)} style={soft(m1.blur)}><Big size={160} color={C.orange}>Motion</Big></O>
          <O x={0} y={-575} z={40} s={d2.s} o={d2.o * w.k} style={soft(d2.blur)}>
            <div style={{position: 'relative'}}>
              <div style={{opacity: 1 - 0.55 * st2}}><Big size={160}>Designer</Big></div>
              <Strike p={st2} rot={-4} />
            </div>
          </O>
          <O x={130} y={-410 + fall2 * 1300} z={90} rz={fall2 * -25} o={pop(t, T.even + 0.1) * w.k}>
            <div style={{position: 'relative', width: 520, height: 44}}>
              <div style={{position: 'absolute', left: 0, right: 0, top: 20, height: 4, borderRadius: 2, background: 'rgba(20,18,23,.16)'}} />
              <div style={{position: 'absolute', left: 0, width: `${kf * 100}%`, top: 20, height: 4, borderRadius: 2, background: C.orange}} />
              {[0.02, 0.22, 0.4, 0.63, 0.81, 0.98].map((x, i) => (
                <span key={i} style={{position: 'absolute', left: `${x * 100}%`, top: 22, width: 28, height: 28, marginLeft: -14, marginTop: -14, background: kf >= x ? C.orange : C.paper,
                  border: `3px solid ${kf >= x ? C.orangeDeep : C.ink}`, transform: `rotate(45deg) scale(${pop(t, T.even + 0.12 + i * 0.05)})`, boxShadow: '0 4px 8px rgba(46,30,16,.2)'}} />
              ))}
            </div>
          </O>
          <O x={-300} y={-330 + fall2 * 1400} z={150} rz={-6 + fall2 * 70} o={pop(t, T.even + 0.25) * w.k}><Easing p={prog(t, T.even + 0.3, 0.6)} /></O>
        </>
      )}
    </>
  );
};

// ---------------------------------------------------------------- 5. three boards: drop a reference → send assets → paste the prompt
const BOARD_Y = -600, BW = 820, BH = 600;
const Board: React.FC<{title: string; sub: React.ReactNode; children?: React.ReactNode}> = ({title, sub, children}) => (
  <Card w={BW} h={BH} radius={40} depth={15}>
    <div style={{position: 'absolute', left: 42, top: 36, display: 'grid', gap: 10}}>
      <Text size={54} w={800} style={{letterSpacing: '-0.035em'}}>{title}</Text>
      <div style={{fontFamily: FONT.display, fontWeight: 500, fontSize: 27, color: C.muted, whiteSpace: 'nowrap'}}>{sub}</div>
    </div>
    {children}
  </Card>
);
const Shot: React.FC<{src: string}> = ({src}) => (
  <div style={{width: 300, height: 258, borderRadius: 18, overflow: 'hidden', border: '5px solid #fff', boxShadow: SHADOW, background: '#0b0d12'}}>
    <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover', display: 'block'}} />
  </div>
);
const IG = [
  {src: 'ig-a.png', tx: 225, ty: 345, tr: -5, fx: 990, fy: -150, fr: 16, d: 0},
  {src: 'ig-b.png', tx: 592, ty: 345, tr: 4, fx: 1110, fy: -60, fr: 24, d: 0.1},
];
const DropBoard: React.FC<{t: number}> = ({t}) => {
  const a0 = T.drop - 0.1, land = T.reference + 0.16;
  const dropped = pop(t, land + 0.08, {damping: 14, stiffness: 220});
  const mk = outCubic(prog(t, T.instagram - 0.05, 0.3));
  const pos = IG.map((g) => {
    const p = inOutCubic(prog(t, a0 + g.d, land - a0));
    return {p, x: lerp(g.fx, g.tx, p), y: lerp(g.fy, g.ty, p) - Math.sin(Math.PI * p) * 90, z: lerp(260, 6, p), rz: lerp(g.fr, g.tr, p),
      s: p >= 1 ? 1 + wobble(t, land + g.d, 20, 10) * 0.05 : lerp(1.12, 1, p)};
  });
  const away = outCubic(prog(t, land + 0.05, 0.45));
  return (
    <>
      <Board title="Drop your reference" sub={<>the one you found on <Marker p={mk}>Instagram</Marker></>}>
        <div style={{position: 'absolute', left: 40, top: 160, width: 740, height: 400, borderRadius: 26, background: dropped > 0.01 ? C.orangeSoft : '#FAF8F5'}}>
          <svg width={740} height={400} style={{position: 'absolute', left: 0, top: 0}}>
            <rect x={2} y={2} width={736} height={396} rx={25} fill="none" stroke={dropped > 0.01 ? C.orange : '#C9C2B8'} strokeWidth={dropped > 0.01 ? 4 : 3} strokeDasharray={dropped > 0.01 ? 'none' : '14 10'} />
          </svg>
          {t < land && (
            <div style={{position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', alignContent: 'center', gap: 14}}>
              <Icon name="upload" size={56} color={C.muted} sw={2} />
              <Text size={30} w={600} color={C.muted}>Drop it here</Text>
            </div>
          )}
          {dropped > 0.01 && (
            <div style={{position: 'absolute', left: 0, right: 0, bottom: 22, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 12, transform: `scale(${dropped})`}}>
              <Check size={36} /><Text size={28} w={700} color={C.orangeDeep}>2 references added</Text>
            </div>
          )}
        </div>
      </Board>
      {pos.map((p, i) => <Free key={i} x={p.x} y={p.y} z={p.z} rz={p.rz} s={p.s} o={clamp(prog(t, a0 + IG[i].d - 0.05, 0.12))}><Shot src={IG[i].src} /></Free>)}
      <Free x={pos[0].x + 130 + away * 260} y={pos[0].y + 100 + away * 220} z={pos[0].z + 30} o={clamp(prog(t, a0 - 0.05, 0.1)) * (1 - prog(t, land + 0.3, 0.2))}><Cursor size={70} /></Free>
    </>
  );
};
const ASSETS = [
  {name: 'logo.svg', size: '4 KB', kind: 'logo'}, {name: 'mini-me.png', size: '1.2 MB', kind: 'avatar'}, {name: 'font.otf', size: '96 KB', kind: 'font'},
  {name: 'palette.json', size: '1 KB', kind: 'palette'}, {name: 'voice.mp3', size: '457 KB', kind: 'audio'}, {name: 'Mini Me Kit.zip', size: '43 KB', kind: 'zip'},
];
const AssetPreview: React.FC<{kind: string; t: number}> = ({kind, t}) => {
  if (kind === 'logo') return <div style={{width: '100%', height: '100%', background: C.cobaltSoft, display: 'grid', placeItems: 'center'}}><Icon name="shapes" size={52} color={C.cobalt} sw={2.2} /></div>;
  if (kind === 'avatar') return <div style={{width: '100%', height: '100%', background: C.orangeSoft, display: 'grid', placeItems: 'center'}}><Avatar size={70} /></div>;
  if (kind === 'font') return <div style={{width: '100%', height: '100%', background: '#F3F0EA', display: 'grid', placeItems: 'center'}}><Text size={64} serif>Aa</Text></div>;
  if (kind === 'palette') return <div style={{width: '100%', height: '100%', display: 'flex'}}>{[C.orange, C.cobalt, C.lime, C.ink].map((c) => <div key={c} style={{flex: 1, background: c}} />)}</div>;
  if (kind === 'audio') return (
    <div style={{width: '100%', height: '100%', background: '#FFF3EC', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 5}}>
      {Array.from({length: 18}, (_, i) => <span key={i} style={{width: 5, height: 12 + Math.abs(Math.sin(i * 1.7 + t * 6)) * 46, borderRadius: 3, background: C.orange}} />)}
    </div>
  );
  return <div style={{width: '100%', height: '100%', background: '#EEEAE4', display: 'grid', placeItems: 'center'}}><Icon name="zip" size={52} color={C.ink} sw={2} /></div>;
};
const AssetsBoard: React.FC<{t: number}> = ({t}) => {
  const att = pop(t, T.assets + 0.25);
  return (
    <Board title="Send your extra assets" sub="logo, character, fonts, colours, audio">
      {ASSETS.map((a, i) => {
        const p = pop(t, T.send0 - 0.12 + i * 0.07, {damping: 13, stiffness: 190});
        const ok = pop(t, T.assets - 0.05 + i * 0.05, {damping: 11, stiffness: 240});
        const c = i % 3, r = Math.floor(i / 3);
        return (
          <div key={a.name} style={{position: 'absolute', left: 40 + c * 250, top: 168 + r * 172, width: 230, height: 154, borderRadius: 20, overflow: 'hidden', background: C.paper,
            border: `1.5px solid ${C.line}`, boxShadow: '0 10px 22px -8px rgba(46,30,16,.25)', opacity: clamp(p * 2), transform: `translateY(${(1 - p) * 70}px) scale(${0.75 + 0.25 * p})`}}>
            <div style={{height: 96}}><AssetPreview kind={a.kind} t={t} /></div>
            <div style={{padding: '10px 14px', display: 'grid', gap: 2}}>
              <div style={{fontFamily: FONT.display, fontWeight: 700, fontSize: 20, color: C.ink, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'}}>{a.name}</div>
              <Mono size={15}>{a.size}</Mono>
            </div>
            {ok > 0.01 && <div style={{position: 'absolute', right: 8, top: 8, transform: `scale(${ok})`}}><Check size={32} /></div>}
          </div>
        );
      })}
      {att > 0.01 && (
        <div style={{position: 'absolute', left: 40, bottom: 26, display: 'flex', alignItems: 'center', gap: 12, transform: `scale(${att})`, transformOrigin: '0% 50%'}}>
          <Icon name="clip" size={30} color={C.orangeDeep} sw={2.2} /><Text size={28} w={700} color={C.orangeDeep}>6 files attached</Text>
        </div>
      )}
    </Board>
  );
};
const PASTE = 'Recreate this reference as a SaaS animation. Use my assets: logo, Mini Me, font, colours. 1080×1920, 30 fps, smooth easing, 3D camera moves, sound design.';
const Key: React.FC<{label: string; w: number; down: number}> = ({label, w, down}) => (
  <div style={{width: w, height: 70, borderRadius: 16, background: C.paper, border: `1.5px solid ${C.line}`, borderBottom: `${7 - 5 * down}px solid #D6CFC5`, boxSizing: 'border-box',
    transform: `translateY(${5 * down}px)`, display: 'grid', placeItems: 'center', boxShadow: '0 10px 18px -8px rgba(46,30,16,.3)'}}>
    <Text size={28} w={700}>{label}</Text>
  </div>
);
const PromptBoard: React.FC<{t: number}> = ({t}) => {
  const keys = pop(t, T.paste - 0.3);
  const down = t >= T.paste - 0.02 && t < T.paste + 0.16 ? 1 : 0;
  const pasted = t >= T.paste + 0.02;
  const selFade = 1 - prog(t, T.paste + 0.25, 0.5);
  const flash = pasted ? 1 - prog(t, T.paste + 0.02, 0.35) : 0;
  const cur = outCubic(prog(t, T.give - 0.15, 0.4));
  const click = T.give + 0.35;
  const pressed = t >= click && t < click + 0.12;
  const ring = prog(t, click, 0.5);
  const sent = t >= click;
  return (
    <Board title="Paste my prompt" sub="the one I'll send you">
      <div style={{position: 'absolute', right: 42, top: 52, display: 'flex', gap: 12, opacity: clamp(keys * 2), transform: `scale(${0.8 + 0.2 * keys})`}}>
        <Key label="Ctrl" w={108} down={down} /><Key label="V" w={74} down={down} />
      </div>
      <div style={{position: 'absolute', left: 40, top: 170, width: 740, height: 390, borderRadius: 28, background: '#FBFAF8', boxSizing: 'border-box',
        border: `2px solid ${sent ? C.orange : C.line}`, boxShadow: `inset 0 2px 6px rgba(46,30,16,.05)${flash > 0 ? `, 0 0 0 ${6 * flash}px ${C.cobaltSoft}` : ''}`}}>
        <div style={{position: 'absolute', left: 30, top: 28, right: 30}}>
          {pasted ? (
            <div style={{fontFamily: FONT.display, fontWeight: 500, fontSize: 27, lineHeight: 1.42, color: C.ink}}>
              <span style={{background: `rgba(49,87,255,${0.16 * selFade})`, borderRadius: 4}}>{PASTE}</span>
            </div>
          ) : (
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}><Spark size={34} /><Text size={28} w={500} color={C.muted}>Message Claude…</Text></div>
          )}
        </div>
        <div style={{position: 'absolute', left: 26, right: 26, bottom: 22, display: 'flex', alignItems: 'center', gap: 12}}>
          <Icon name="clip" size={30} color={C.muted} sw={2.2} />
          {['6 files', '2 references'].map((s) => <div key={s} style={{padding: '8px 16px', borderRadius: 999, background: '#EFEBE5', fontFamily: FONT.display, fontWeight: 600, fontSize: 21, color: C.ink2}}>{s}</div>)}
          <div style={{flex: 1}} />
          <div style={{position: 'relative', width: 66, height: 66}}>
            {ring > 0 && ring < 1 && <div style={{position: 'absolute', inset: 0, borderRadius: '50%', border: `4px solid ${C.orange}`, transform: `scale(${1 + ring * 1.6})`, opacity: 1 - ring}} />}
            <div style={{width: 66, height: 66, borderRadius: '50%', background: C.orange, display: 'grid', placeItems: 'center', transform: `scale(${pressed ? 0.86 : 1})`, boxShadow: '0 8px 18px rgba(238,106,58,.4)'}}>
              <Icon name="up" size={32} color="#fff" sw={2.6} />
            </div>
          </div>
        </div>
      </div>
      {cur > 0 && t < click + 0.5 && (
        <div style={{position: 'absolute', left: lerp(560, 712, cur), top: lerp(470, 525, cur), transform: `scale(${pressed ? 0.88 : 1})`, opacity: 1 - prog(t, click + 0.3, 0.2)}}><Cursor size={62} /></div>
      )}
    </Board>
  );
};
const Steps: React.FC<R> = ({t}) => {
  const w = win(t, 'steps', 0.5);
  if (!w) return null;
  const nums = [T.one, T.two, T.three];
  const rise = [SC.steps.s, T.two - 0.45, T.three - 0.45]; // each board rises as the camera arrives at it
  const gone = [T.two + 0.7, T.three + 0.7, 1e9];
  const blow = outCubic(prog(t, T.boom - 0.04, 0.5));
  return (
    <>
      {[0, 1, 2].map((i) => {
        if (t > gone[i] || t < rise[i]) return null;
        const p = outExpo(prog(t, rise[i], 0.6));
        const b = i === 2 ? blow : 0;
        const sl = slam(t, nums[i] - 0.05, 0.24, 2.1);
        return (
          <React.Fragment key={i}>
            <O x={BX[i]} y={BOARD_Y + 320 * (1 - p) + Math.sin(t * 1.2 + i) * 6} z={-1100 * b} ry={[-4, 0, 4][i] + 50 * b} rx={35 * (1 - p)} o={clamp(p * 2) * (1 - prog(b, 0.15, 0.6))}>
              {i === 0 && <DropBoard t={t} />}
              {i === 1 && <AssetsBoard t={t} />}
              {i === 2 && <PromptBoard t={t} />}
            </O>
            <O x={BX[i] - 330} y={-300} z={150 - 900 * b} s={sl.s} o={sl.o * (1 - prog(b, 0, 0.3))} style={soft(sl.blur)}><Big size={290} color={C.orange} depth={12}>{i + 1}</Big></O>
          </React.Fragment>
        );
      })}
    </>
  );
};

// ---------------------------------------------------------------- 6. "And BOOM! A professional SaaS animation."
const X3 = BX[2];
const Boom: React.FC<R> = ({t, cam}) => {
  const w = win(t, 'boom', 0.4);
  if (!w) return null;
  const b = slam(t, T.boom - 0.02, 0.18, 2.6);
  const bOut = inCubic(prog(t, T.professional - 0.2, 0.3));
  const tt = t - T.boom;
  const pro = enter(t, T.professional - 0.14, 0.4);
  const sa = slam(t, T.saas0 - 0.06, 0.24, 1.8);
  const an = enter(t, T.animation - 0.08, 0.35);
  const mk = outCubic(prog(t, T.saas0 + 0.12, 0.3));
  // the headline clears out before "Comment" lands in the same band
  const out = inCubic(prog(t, T.comment - 0.32, 0.22));
  return (
    <>
      {/* shockwave rings */}
      {[0, 1, 2].map((i) => {
        const p = prog(t, T.boom + i * 0.07, 0.65);
        if (p <= 0 || p >= 1) return null;
        return <O key={i} x={X3} y={-560} z={60} ry={-cam.yaw} o={1 - p}><div style={{width: 1700 * outCubic(p) + 120, height: 1700 * outCubic(p) + 120, borderRadius: '50%', border: `${14 - i * 4}px solid ${[C.orange, C.cobalt, C.ink][i]}`}} /></O>;
      })}
      {/* burst: the studio's own objects thrown out by the hit */}
      {tt > 0 && tt < 1.5 && Array.from({length: 28}, (_, i) => {
        const a = rnd(`ba${i}`) * Math.PI * 2, el = (rnd(`be${i}`) - 0.5) * 1.2, sp = 800 + rnd(`bs${i}`) * 1000;
        const e = 1 - Math.exp(-tt * 3.2);
        const x = X3 + Math.cos(a) * sp * e * 0.9, y = -560 + Math.sin(a) * sp * e * 0.7 + 700 * tt * tt, z = 80 + el * sp * e;
        const size = 26 + rnd(`bz${i}`) * 56;
        const tone = ['orange', 'cobalt', 'ink', 'white', 'lime'][i % 5];
        return (
          <O key={i} x={x} y={y} z={z} ry={-cam.yaw} rz={tt * 300 * (rnd(`br${i}`) - 0.5)} o={1 - prog(tt, 0.9, 0.6)}>
            {i % 4 === 3 ? <Spark size={size * 1.2} color={tone === 'white' ? C.orange : tone === 'lime' ? C.cobalt : tone === 'ink' ? C.ink : C.orange} /> : <Ball size={size} tone={tone} />}
          </O>
        );
      })}
      {bOut < 1 && (
        <O x={X3} y={-600} z={120 + bOut * 900} s={b.s} o={b.o * (1 - bOut)} style={soft(b.blur)}>
          <div style={{position: 'relative'}}>
            {[3, 2, 1].map((k) => <div key={k} style={{position: 'absolute', left: 0, top: 0, transform: `translate(${k * 9}px, ${k * 14}px)`, opacity: 0.5 - k * 0.12}}><Big size={230} color={C.orange} depth={0}>BOOM.</Big></div>)}
            <Big size={230} depth={14}>BOOM.</Big>
          </div>
        </O>
      )}
      <O x={X3} y={-835 - out * 260} z={60 + pro.dz} rx={pro.rx} o={pro.o * w.k * (1 - out)}><Big size={96} serif color={C.orange}>a professional</Big></O>
      <O x={X3} y={-722 - out * 260} z={60} o={w.k * (1 - out)}>
        <div style={{display: 'flex', alignItems: 'baseline', gap: 26}}>
          <span style={{display: 'inline-block', transform: `scale(${sa.s})`, opacity: sa.o}}><Marker p={mk}><Big size={116}>SaaS</Big></Marker></span>
          <span style={{display: 'inline-block', opacity: an.o, transform: `translateY(${(1 - an.p) * 40}px)`}}><Big size={116}>animation</Big></span>
        </div>
      </O>
    </>
  );
};
// the result: the reference flies back in as a finished screen, with its other moments fanned behind it
const STILLS: [string, number, number, number, number, number][] = [['still-a.jpg', -330, 20, -170, 30, -6], ['still-b.jpg', 330, 20, -170, -30, 6], ['still-c.jpg', 0, -170, -280, 0, 0]];
const Reprise: React.FC<R> = ({t}) => {
  const a = T.boom + 0.1;
  if (t < a || t > T.comment + 0.6) return null;
  const p = outExpo(prog(t, a, 0.6));
  const out = inCubic(prog(t, T.comment - 0.1, 0.5));
  const chips = [pop(t, T.animation + 0.15), pop(t, T.animation + 0.25)];
  return (
    <O x={X3} y={-449 - out * 700} z={-40 - 1300 * (1 - p) - out * 1100} rx={18 * (1 - p)} ry={-12 * (1 - p) + Math.sin(t * 0.8) * 2} o={clamp(p * 2) * (1 - out)}>
      {STILLS.map(([src, x, y, z, ry, rz], i) => {
        const q = outExpo(prog(t, a + 0.15 + i * 0.07, 0.55));
        return (
          <div key={src} style={{position: 'absolute', left: SW / 2, top: SH / 2, transformStyle: 'preserve-3d', transform: `translate3d(${x * q}px,${y * q}px,${z}px) translate(-50%,-50%) rotateY(${ry * q}deg) rotateZ(${rz * q}deg)`}}>
            <div style={{width: 600, height: 338, borderRadius: 22, overflow: 'hidden', border: '8px solid #fff', boxShadow: SHADOW}}><Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover', display: 'block'}} /></div>
          </div>
        );
      })}
      <Screen>
        <Sequence from={Math.round(a * FPS)} layout="none"><OffthreadVideo src={staticFile('ref.mp4')} startFrom={8 * FPS} muted style={{width: '100%', height: '100%', display: 'block'}} /></Sequence>
      </Screen>
      <Free x={SW - 120} y={-6} z={30} s={chips[0]}><Chip>1920 × 1080</Chip></Free>
      <Free x={110} y={SH + 4} z={30} s={chips[1]}><Chip bg={C.ink} color="#fff">60 fps</Chip></Free>
    </O>
  );
};

// ---------------------------------------------------------------- 7. "Comment SaaS and I'll send you the prompt and the full instructions."
const Cta: React.FC<R> = ({t}) => {
  const w = win(t, 'cta');
  if (!w) return null;
  const c1 = slam(t, T.comment - 0.08, 0.24, 1.8);
  const c2 = slam(t, T.saas1 - 0.04, 0.26, 2.2);
  const bar = enter(t, T.comment + 0.05, 0.45);
  const typed = 'SaaS'.slice(0, Math.max(0, Math.floor((t - T.saas1 + 0.02) / 0.07)));
  const sendAt = T.saas1 + 0.42;
  const sp = prog(t, sendAt, 0.5);
  const dm = enter(t, T.send1 - 0.12, 0.45);
  const files: [string, number][] = [['prompt.md', T.prompt - 0.05], ['instructions.pdf', T.instructions - 0.08]];
  return (
    <>
      <O x={X3} y={-805} z={60} s={c1.s} o={c1.o} style={soft(c1.blur)}><Big size={170}>Comment</Big></O>
      <O x={X3 + 20} y={-628} z={60} s={c2.s} o={c2.o} style={soft(c2.blur)}><Big size={250} serif color={C.orange}>“SaaS”</Big></O>
      <O x={X3} y={-430} z={80 + bar.dz} rx={bar.rx} o={bar.o}>
        <Card w={780} h={124} radius={62} depth={9}>
          <div style={{display: 'flex', alignItems: 'center', gap: 18, height: '100%', padding: '0 20px'}}>
            <Avatar size={80} />
            <div style={{flex: 1, height: 80, borderRadius: 40, background: '#F4F1EC', display: 'flex', alignItems: 'center', padding: '0 26px', fontFamily: FONT.display, fontWeight: 800, fontSize: 44, color: C.ink}}>
              {t < sendAt ? typed : ''}<span style={{fontWeight: 500, color: C.orange, opacity: Math.floor(t * 4) % 2 ? 0 : 1}}>|</span>
              {(t >= sendAt || !typed) && <span style={{fontWeight: 500, fontSize: 30, color: C.muted}}>Add a comment…</span>}
            </div>
            <div style={{width: 80, height: 80, borderRadius: '50%', background: C.orange, display: 'grid', placeItems: 'center', flex: 'none', transform: `scale(${t > sendAt && t < sendAt + 0.12 ? 0.85 : 1})`}}>
              <Icon name="plane" size={38} color="#fff" sw={2.4} />
            </div>
          </div>
        </Card>
      </O>
      {sp > 0 && sp < 1 && (
        <O x={X3 + lerp(330, 620, sp)} y={-430 - Math.sin(sp * Math.PI) * 260 - sp * 200} z={160} rz={-20 + 50 * sp} o={1 - prog(t, sendAt + 0.35, 0.15)}><Icon name="plane" size={70} color={C.orange} sw={2.6} /></O>
      )}
      <O x={X3 + 10} y={-282} z={100 + dm.dz} rx={dm.rx} o={dm.o}>
        <Card w={700} h={150} radius={30}>
          <div style={{display: 'flex', alignItems: 'center', gap: 20, height: '100%', padding: '0 24px'}}>
            <Avatar size={70} />
            <div style={{display: 'grid', gap: 12}}>
              <Text size={24} w={500} color={C.muted}>@jako.frames sent you</Text>
              <div style={{display: 'flex', gap: 12}}>
                {files.map(([name, at]) => {
                  const q = pop(t, at, {damping: 12, stiffness: 230});
                  return (
                    <div key={name} style={{display: 'flex', alignItems: 'center', gap: 10, padding: '10px 16px 10px 12px', borderRadius: 16, background: '#F4F1EC', opacity: clamp(q * 2), transform: `scale(${0.6 + 0.4 * q})`}}>
                      <Icon name="file" size={28} color={C.orangeDeep} sw={2.1} />
                      <Text size={25} w={700}>{name}</Text>
                      {q > 0.6 && <Check size={26} />}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </Card>
      </O>
    </>
  );
};

// screen-space: after the last word, an arrow points at Instagram's comment button
export const ScreenFX: React.FC<{t: number}> = ({t}) => {
  const p = outCubic(prog(t, VO_END - 0.55, 0.45));
  if (p <= 0) return null;
  const bob = Math.sin(Math.max(0, t - VO_END) * 6) * 8;
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <svg width={1080} height={1920} style={{position: 'absolute', left: 0, top: bob}}>
        <path d="M770,1040 C900,1060 975,1150 968,1262" fill="none" stroke={C.orange} strokeWidth={10} strokeLinecap="round" strokeDasharray={330} strokeDashoffset={330 * (1 - p)} />
        {p > 0.9 && <path d="M938,1228 L968,1270 L998,1230" fill="none" stroke={C.orange} strokeWidth={10} strokeLinecap="round" strokeLinejoin="round" />}
      </svg>
    </AbsoluteFill>
  );
};

export const WorldScenes: React.FC<R> = ({t, cam}) => (
  <>
    <RefPanel t={t} cam={cam} /><Hook t={t} cam={cam} /><Made t={t} cam={cam} /><Meta t={t} cam={cam} /><NoDesign t={t} cam={cam} />
    <Steps t={t} cam={cam} /><Boom t={t} cam={cam} /><Reprise t={t} cam={cam} /><Cta t={t} cam={cam} />
  </>
);
