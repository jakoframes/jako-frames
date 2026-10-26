import React from 'react';
import {AbsoluteFill, Easing, interpolate, random, spring, useCurrentFrame} from 'remotion';
import timing from './warp.json';
import {loadFont as loadHeavy} from '@remotion/google-fonts/InterTight';
import {loadFont as loadSerif} from '@remotion/google-fonts/InstrumentSerif';
import {loadFont as loadMono} from '@remotion/google-fonts/IBMPlexMono';

const HEAVY = loadHeavy('normal', {weights: ['400', '500', '600', '700', '900'], subsets: ['latin']}).fontFamily;
loadSerif('normal', {weights: ['400'], subsets: ['latin']});
const SERIF = loadSerif('italic', {weights: ['400'], subsets: ['latin']}).fontFamily;
const MONO = loadMono('normal', {weights: ['400', '500', '600'], subsets: ['latin']}).fontFamily;

export const FPS = 30;
export const DURATION_S = timing.duration;

// Scene times below are in seconds on the first voiceover's timeline ("old" time).
// The current voiceover differs slightly, so the root maps each real frame back to
// old time through the word anchors in warp.json and serves it via ClockCtx.
const ANCHORS = timing.anchors as [number, number][];
const OLD = ANCHORS.map((a) => a[0]);
const NEW = ANCHORS.map((a) => a[1]);
const toOld = (s: number) => interpolate(s, NEW, OLD, {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

const ClockCtx = React.createContext<number | null>(null);
const useFrame = () => {
  const real = useCurrentFrame();
  const override = React.useContext(ClockCtx);
  return override ?? real;
};

const f = (s: number) => Math.round(s * FPS);
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const eo = Easing.out(Easing.cubic);

const P = {
  ink: '#0C0C0E',
  cream: '#F1ECE4',
  paper: '#ECE8E0',
  orange: '#FF5B1F',
  lime: '#D9F53B',
  hl: '#E8F43A',
  violet: '#6C5CF5',
  deep: '#15122E',
  claude: '#D97757',
};
const TILE_COLORS = [P.orange, P.lime, P.violet, P.cream, P.cream];

type SpringCfg = {damping?: number; stiffness?: number; mass?: number};
const sp = (frame: number, at: number, cfg: SpringCfg = {}) =>
  spring({frame: frame - f(at), fps: FPS, config: {damping: 14, stiffness: 190, mass: 0.6, ...cfg}});

// ---------- type ----------

type Kind = 'heavy' | 'serif' | 'mono';
const fontFor = (k: Kind): React.CSSProperties =>
  k === 'heavy'
    ? {fontFamily: HEAVY, fontWeight: 900, letterSpacing: '-0.045em', lineHeight: 0.86}
    : k === 'serif'
      ? {fontFamily: SERIF, fontStyle: 'italic', fontWeight: 400, letterSpacing: '-0.01em', lineHeight: 1}
      : {fontFamily: MONO, fontWeight: 500, letterSpacing: '0.2em', lineHeight: 1.2};

type WProps = {
  at: number;
  children: React.ReactNode;
  size: number;
  color?: string;
  kind?: Kind;
  anim?: 'pop' | 'mask' | 'slam' | 'stretch';
  strike?: number;
  strikeColor?: string;
  style?: React.CSSProperties;
};

const W: React.FC<WProps> = ({at, children, size, color = P.cream, kind = 'heavy', anim = 'pop', strike, strikeColor = P.ink, style}) => {
  const frame = useFrame();
  const visible = frame >= f(at);
  const p = sp(frame, at, {damping: 11, stiffness: 240, mass: 0.5});
  const lin = interpolate(frame, [f(at), f(at) + 7], [0, 1], {...clamp, easing: eo});
  let transform = '';
  let filter: string | undefined;
  if (anim === 'pop') {
    transform = `scale(${interpolate(p, [0, 1], [1.45, 1])})`;
    const b = interpolate(p, [0, 1], [12, 0], clamp);
    filter = b > 0.3 ? `blur(${b}px)` : undefined;
  } else if (anim === 'slam') {
    transform = `scale(${interpolate(p, [0, 1], [2.4, 1])})`;
  } else if (anim === 'stretch') {
    transform = `scaleX(${interpolate(p, [0, 1], [2.1, 1])}) scaleY(${interpolate(p, [0, 1], [0.6, 1])})`;
  }
  const strikeP = strike !== undefined ? interpolate(frame, [f(strike), f(strike) + 6], [0, 1], {...clamp, easing: eo}) : 0;
  const base: React.CSSProperties = {...fontFor(kind), fontSize: size, color, display: 'inline-block', position: 'relative', whiteSpace: 'nowrap', ...style};
  const strikeBar =
    strike !== undefined ? (
      <span style={{position: 'absolute', left: '-3%', top: '46%', height: '0.13em', width: `${strikeP * 106}%`, background: strikeColor}} />
    ) : null;
  if (anim === 'mask') {
    return (
      <span style={{...base, overflow: 'hidden', verticalAlign: 'bottom', paddingBottom: '0.08em', marginBottom: '-0.08em'}}>
        <span style={{display: 'inline-block', transform: `translateY(${(1 - lin) * 105}%)`, opacity: visible ? 1 : 0}}>{children}</span>
        {strikeBar}
      </span>
    );
  }
  return (
    <span style={{...base, opacity: visible ? Math.min(1, p * 2.5) : 0, transform, filter, transformOrigin: '50% 60%'}}>
      {children}
      {strikeBar}
    </span>
  );
};

const Row: React.FC<{children: React.ReactNode; gap?: number; style?: React.CSSProperties}> = ({children, gap = 28, style}) => (
  <div style={{display: 'flex', alignItems: 'baseline', justifyContent: 'center', gap, ...style}}>{children}</div>
);

const Center: React.FC<{children: React.ReactNode; gap?: number; style?: React.CSSProperties}> = ({children, gap = 0, style}) => (
  <AbsoluteFill style={{display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', gap, ...style}}>
    {children}
  </AbsoluteFill>
);

// Outline copies behind a heavy word, as in the "THINGS" frame of the reference.
const Ghosts: React.FC<{text: string; size: number; color: string; at: number}> = ({text, size, color, at}) => {
  const frame = useFrame();
  const p = interpolate(frame, [f(at), f(at) + 18], [0, 1], {...clamp, easing: eo});
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
      {[1.5, 1.28, 1.12].map((s, i) => (
        <div
          key={s}
          style={{
            position: 'absolute',
            ...fontFor('heavy'),
            fontSize: size,
            color: 'transparent',
            WebkitTextStroke: `2px ${color}`,
            opacity: frame >= f(at) ? 0.18 + i * 0.08 : 0,
            transform: `scale(${1 + (s - 1) * p})`,
          }}
        >
          {text}
        </div>
      ))}
    </AbsoluteFill>
  );
};

// ---------- scene shell, HUD, shake ----------

const Scene: React.FC<{from: number; to: number; bg?: string; children: React.ReactNode}> = ({from, to, bg, children}) => {
  const frame = useFrame();
  if (frame < f(from) || frame >= f(to)) return null;
  const pin = interpolate(frame, [f(from), f(from) + 6], [0, 1], {...clamp, easing: eo});
  return (
    <AbsoluteFill style={{background: bg}}>
      <AbsoluteFill style={{transform: `scale(${1.05 - 0.05 * pin})`}}>{children}</AbsoluteFill>
    </AbsoluteFill>
  );
};

const SECTIONS: [number, string][] = [
  [0, '00 / IGNITION'],
  [1.6, '01 / KINETIC TYPE'],
  [4.25, '02 / INTERFACE'],
  [7.75, '03 / RHYTHM'],
  [9.2, '04 / PARTICLES'],
  [11.0, '05 / PROMPT · 3D'],
  [23.3, '06 / DEPTH'],
  [25.4, '07 / GEOMETRY'],
  [28.45, '08 / INTERFACE'],
  [30.4, '09 / CODE'],
  [32.3, '10 / EVERYTHING'],
  [36.2, '11 / CODE'],
  [37.8, '12 / RHYTHM'],
  [40.9, '13 / IDENTITY'],
];
const LIGHT: [number, number][] = [
  [0.25, 1.6],
  [2.6, 4.25],
  [5.46, 7.75],
  [28.45, 30.4],
  [34.25, 39.65],
];

const Hud: React.FC = () => {
  const frame = useCurrentFrame();
  const t = useFrame() / FPS;
  const light = LIGHT.some(([a, b]) => t >= a && t < b);
  const c = light ? 'rgba(12,12,14,0.55)' : 'rgba(241,236,228,0.5)';
  const label = [...SECTIONS].reverse().find(([s]) => t >= s)![1];
  const sec = Math.floor(frame / FPS);
  const tc = `TC 00:00:${String(sec).padStart(2, '0')}:${String(frame % FPS).padStart(2, '0')}`;
  const txt: React.CSSProperties = {position: 'absolute', fontFamily: MONO, fontSize: 15, letterSpacing: '0.22em', color: c, fontWeight: 500};
  const bracket = (style: React.CSSProperties) => <div style={{position: 'absolute', width: 26, height: 26, borderColor: c, borderStyle: 'solid', borderWidth: 0, ...style}} />;
  const progress = frame / FPS / DURATION_S;
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      {bracket({left: 34, top: 34, borderLeftWidth: 2, borderTopWidth: 2})}
      {bracket({right: 34, top: 34, borderRightWidth: 2, borderTopWidth: 2})}
      {bracket({left: 34, bottom: 34, borderLeftWidth: 2, borderBottomWidth: 2})}
      {bracket({right: 34, bottom: 34, borderRightWidth: 2, borderBottomWidth: 2})}
      <div style={{...txt, left: 72, top: 40}}>JAKO.FRAMES &nbsp;/&nbsp; MOTION REEL 2026</div>
      <div style={{...txt, right: 72, top: 40}}>{tc}</div>
      <div style={{position: 'absolute', left: 72, right: 72, bottom: 66, height: 1, background: c}} />
      {Array.from({length: 45}, (_, i) => (
        <div key={i} style={{position: 'absolute', left: 72 + i * 40.5, bottom: 66, width: 1, height: i % 5 === 0 ? 12 : 6, background: c}} />
      ))}
      <div style={{position: 'absolute', left: 72 + progress * 1776 - 1, bottom: 60, width: 3, height: 22, background: P.orange}} />
      <div style={{...txt, left: 72, bottom: 38}}>{label}</div>
      <div style={{...txt, right: 72, bottom: 38}}>1920 × 1080 &nbsp;/&nbsp; 30 FPS</div>
    </AbsoluteFill>
  );
};

const IMPACTS = [0.76, 2.6, 7.3, 8.75, 9.74, 24.08, 28.0, 29.24, 31.56, 36.26, 39.12, 40.28];
const shake = (frame: number) => {
  let x = 0;
  let y = 0;
  for (const s of IMPACTS) {
    const d = frame - f(s);
    if (d >= 0 && d < 10) {
      const a = (1 - d / 10) ** 2;
      x += Math.sin(d * 2.4) * 12 * a;
      y += Math.cos(d * 3.2) * 9 * a;
    }
  }
  return {x, y};
};

// ---------- reusable elements from the reference ----------

const Spark: React.FC<{size: number; color?: string; rot?: number}> = ({size, color = P.claude, rot = 0}) => (
  <svg width={size} height={size} viewBox="-50 -50 100 100" style={{transform: `rotate(${rot}deg)`, overflow: 'visible', display: 'block'}}>
    {Array.from({length: 12}, (_, i) => {
      const len = [44, 34, 40, 30][i % 4];
      return <rect key={i} x={-4.5} y={-len} width={9} height={len} rx={4.5} fill={color} transform={`rotate(${i * 30 + (i % 3) * 4})`} />;
    })}
  </svg>
);

const DotO: React.FC<{size: number; rot: number}> = ({size, rot}) => (
  <div style={{width: size, height: size, borderRadius: '50%', background: P.ink, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', verticalAlign: 'middle'}}>
    <div style={{display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: size * 0.06, transform: `rotate(${rot}deg)`}}>
      {[P.cream, P.lime, P.cream, P.cream, P.cream, P.violet, P.lime, P.cream, P.orange].map((c, i) => (
        <div key={i} style={{width: size * 0.13, height: size * 0.13, borderRadius: '50%', background: c}} />
      ))}
    </div>
  </div>
);

const Glass: React.FC<{x: number; y: number; r: number; sx?: number; rot?: number}> = ({x, y, r, sx = 1, rot = 0}) => (
  <div
    style={{
      position: 'absolute',
      left: x - r,
      top: y - r,
      width: 2 * r,
      height: 2 * r,
      borderRadius: '50%',
      transform: `rotate(${rot}deg) scaleX(${sx})`,
      background: [
        'radial-gradient(circle at 32% 26%, rgba(255,255,255,0.95) 0 3%, rgba(255,255,255,0.35) 9%, transparent 22%)',
        'radial-gradient(circle at 72% 76%, rgba(255,110,90,0.9), transparent 42%)',
        'radial-gradient(circle at 22% 72%, rgba(80,220,255,0.75), transparent 45%)',
        'radial-gradient(circle at 80% 30%, rgba(217,245,59,0.45), transparent 35%)',
        'radial-gradient(circle at 50% 50%, #3a2f8f 0%, #1a1440 70%, #0d0a24 100%)',
      ].join(','),
      boxShadow: `inset -${r * 0.15}px -${r * 0.2}px ${r * 0.4}px rgba(0,0,0,0.5), inset ${r * 0.08}px ${r * 0.08}px ${r * 0.25}px rgba(255,255,255,0.3), 0 ${r * 0.35}px ${r * 0.7}px rgba(0,0,0,0.5)`,
    }}
  />
);

const SHAPES = [
  [[0, 0], [100, 0], [100, 100], [0, 100]],
  [[50, 0], [100, 50], [50, 100], [0, 50]],
  [[50, 0], [50, 0], [100, 100], [0, 100]],
];
const Morph: React.FC<{size: number; t: number; color: string}> = ({size, t, color}) => {
  const seg = ((t % 3) + 3) % 3;
  const i = Math.floor(seg);
  const k = Easing.inOut(Easing.cubic)(seg - i);
  const a = SHAPES[i];
  const b = SHAPES[(i + 1) % 3];
  const poly = a.map((p, j) => `${p[0] + (b[j][0] - p[0]) * k}% ${p[1] + (b[j][1] - p[1]) * k}%`).join(',');
  return <div style={{width: size, height: size, background: color, clipPath: `polygon(${poly})`}} />;
};

// ---------- 00 IGNITION ----------

const S0Ignition: React.FC = () => {
  const frame = useFrame();
  const pill = interpolate(frame, [2, 9], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  return (
    <Scene from={0} to={1.6} bg={P.ink}>
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
        <div style={{position: 'absolute', width: 240, height: 240, borderRadius: '50%', border: '2px solid #ffffff33', opacity: 1 - pill}} />
        <div
          style={{
            position: 'absolute',
            width: interpolate(pill, [0, 1], [16, 2000]),
            height: interpolate(pill, [0, 1], [16, 1140]),
            borderRadius: interpolate(pill, [0, 1], [8, 0]),
            background: frame < 2 ? P.cream : P.orange,
          }}
        />
      </AbsoluteFill>
      <Center>
        <Row gap={40}>
          <W at={0.1} size={230} color={P.ink} anim="slam">
            WHAT
          </W>
          <W at={0.44} size={230} color={P.ink} anim="slam">
            THE
          </W>
        </Row>
        <W at={0.76} size={290} color={P.ink} anim="stretch" style={{marginTop: 10}}>
          HEEECK<span style={{fontFamily: SERIF, fontStyle: 'italic', fontWeight: 400, letterSpacing: 0, color: P.violet}}>?!</span>
        </W>
      </Center>
    </Scene>
  );
};

// ---------- 01 KINETIC TYPE ----------

const S1World: React.FC = () => {
  const frame = useFrame();
  return (
    <>
      <Scene from={1.6} to={2.6} bg={P.ink}>
        <Center gap={10}>
          <W at={1.64} size={120} kind="mono" color="#ffffff66" anim="mask">
            THE
          </W>
          <W at={2.06} size={300} anim="mask">
            WORLD
          </W>
          <W at={2.3} size={170} kind="serif" color={P.orange} anim="mask">
            was
          </W>
        </Center>
      </Scene>
      <Scene from={2.6} to={3.04} bg={P.lime}>
        <Ghosts text="NOT" size={520} color={P.ink} at={2.6} />
        <Center>
          <W at={2.6} size={520} color={P.ink} anim="slam">
            NOT
          </W>
        </Center>
      </Scene>
      <Scene from={3.04} to={4.25} bg={P.orange}>
        <Center>
          <div style={{display: 'flex', alignItems: 'center'}}>
            {'READY'.split('').map((ch, i) => {
              const p = sp(frame, 3.04 + i * 0.04, {damping: 10, stiffness: 220});
              const tilt = [-8, 6, -4, 9, -6][i];
              return (
                <span
                  key={i}
                  style={{
                    ...fontFor('heavy'),
                    fontSize: 380,
                    color: P.ink,
                    display: 'inline-block',
                    transform: `translateY(${(1 - p) * -500}px) rotate(${tilt * p + (1 - p) * -40}deg)`,
                    opacity: frame >= f(3.04 + i * 0.04) ? 1 : 0,
                  }}
                >
                  {ch}
                </span>
              );
            })}
            <div style={{width: 70, height: 70, borderRadius: 35, background: P.ink, marginLeft: 20, alignSelf: 'flex-end', marginBottom: 60, transform: `scale(${sp(frame, 3.3)})`}} />
          </div>
          <Row gap={22} style={{marginTop: 10}}>
            <W at={3.32} size={130} kind="serif" color={P.ink} anim="mask">
              for
            </W>
            <W at={3.56} size={130} kind="serif" color={P.ink} anim="mask">
              this.
            </W>
          </Row>
        </Center>
      </Scene>
    </>
  );
};

// ---------- 02 INTERFACE / AFTER EFFECTS ----------

const Cursor: React.FC<{x: number; y: number; press?: boolean}> = ({x, y, press}) => (
  <svg width={44} height={44} viewBox="0 0 24 24" style={{position: 'absolute', left: x, top: y, transform: `scale(${press ? 0.85 : 1})`, filter: 'drop-shadow(0 4px 8px rgba(0,0,0,0.4))'}}>
    <path d="M3 2 L3 19 L8 14.5 L11 21 L14 19.6 L11 13.4 L17.5 13.4 Z" fill="#111" stroke="#fff" strokeWidth={1.4} />
  </svg>
);

const AeCard: React.FC = () => {
  const frame = useFrame();
  const t = frame / FPS;
  const p = sp(frame, 6.1, {damping: 15, stiffness: 150});
  const rows = [
    {name: 'POSITION', keys: [0.08, 0.14, 0.2, 0.42]},
    {name: 'SCALE', keys: [0.3, 0.38, 0.46, 0.55, 0.63]},
    {name: 'OPACITY', keys: [0.62, 0.7, 0.78, 0.9]},
  ];
  const play = interpolate(t, [6.2, 7.3], [0.05, 0.92], clamp);
  const cx = interpolate(t, [6.4, 6.95], [700, 1110], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const cy = interpolate(t, [6.4, 6.95], [520, 352], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const press = t >= 7.0 && t < 7.1;
  const x = interpolate(frame, [f(7.3), f(7.3) + 6], [0, 1], {...clamp, easing: eo});
  return (
    <div
      style={{
        position: 'absolute',
        left: 260,
        top: 400,
        width: 1400,
        height: 430,
        borderRadius: 28,
        background: P.violet,
        transform: `translateY(${(1 - p) * 700}px) rotate(${(1 - p) * 6 + (x > 0 ? Math.sin(frame) * 0.6 : 0)}deg)`,
        boxShadow: '0 40px 80px rgba(40,30,120,0.35)',
        overflow: 'hidden',
      }}
    >
      <div style={{position: 'absolute', left: 50, top: 50}}>
        <div style={{display: 'flex', gap: 22}}>
          <W at={6.64} size={92} kind="serif" anim="mask">
            After
          </W>
          <W at={6.96} size={92} kind="serif" anim="mask">
            Effects
          </W>
        </div>
        <div style={{fontFamily: MONO, fontSize: 16, letterSpacing: '0.2em', color: '#ffffffaa', marginTop: 22}}>TIMELINE &nbsp;/&nbsp; 47 KEYS</div>
      </div>
      <div style={{position: 'absolute', left: 600, top: 70, right: 50, height: 260}}>
        {rows.map((r, ri) => (
          <div key={r.name} style={{position: 'absolute', top: ri * 82, left: 0, right: 0, height: 60, display: 'flex', alignItems: 'center'}}>
            <span style={{width: 130, fontFamily: MONO, fontSize: 15, letterSpacing: '0.2em', color: '#ffffff99'}}>{r.name}</span>
            <div style={{position: 'absolute', left: 140, right: 0, top: 29, height: 2, background: '#ffffff30'}} />
            {r.keys.map((k, ki) => {
              const kp = sp(frame, 6.2 + (ri * 5 + ki) * 0.03, {damping: 9, stiffness: 320});
              return (
                <div
                  key={ki}
                  style={{position: 'absolute', left: 140 + k * 580, top: 19, width: 22, height: 22, background: ri === 1 ? P.lime : P.cream, transform: `rotate(45deg) scale(${kp})`}}
                />
              );
            })}
          </div>
        ))}
        <div style={{position: 'absolute', left: 140 + play * 580, top: -20, width: 3, height: 270, background: P.orange}} />
      </div>
      <div style={{position: 'absolute', right: 50, bottom: 40, padding: '12px 30px', borderRadius: 30, background: press ? P.lime : P.cream, fontFamily: MONO, fontSize: 18, letterSpacing: '0.2em', color: P.ink}}>RENDER</div>
      {t >= 6.4 && <Cursor x={cx} y={cy} press={press} />}
      {x > 0 &&
        [38, -38].map((a) => (
          <div key={a} style={{position: 'absolute', left: '50%', top: '50%', width: 1600 * x, height: 40, background: P.orange, transform: `translate(-50%,-50%) rotate(${a / 2.4}deg)`}} />
        ))}
    </div>
  );
};

const S2AfterEffects: React.FC = () => {
  const frame = useFrame();
  const t = frame / FPS;
  const up = interpolate(t, [6.0, 6.35], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const iP = sp(frame, 4.3, {damping: 12, stiffness: 200});
  return (
    <>
      <Scene from={4.25} to={5.46} bg={P.ink}>
        <AbsoluteFill style={{flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 60}}>
          <div style={{width: 120, height: 560, background: P.cream, transform: `scaleY(${iP})`, transformOrigin: '50% 100%'}} />
          <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 20}}>
            <Row gap={30}>
              <W at={4.4} size={190} anim="mask">
                MADE
              </W>
              <W at={4.56} size={190} anim="mask">
                THIS
              </W>
            </Row>
            <Row gap={24}>
              <W at={4.78} size={170} kind="serif" color={P.lime} anim="mask">
                motion
              </W>
              <W at={5.06} size={170} kind="serif" color={P.lime} anim="mask">
                graphic
              </W>
            </Row>
          </div>
        </AbsoluteFill>
      </Scene>
      <Scene from={5.46} to={7.75} bg={P.paper}>
        <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
          <div style={{transform: `translateY(${-up * 360}px) scale(${1 - up * 0.55})`}}>
            <W at={5.46} size={330} color={P.ink} anim="slam">
              WITHOUT
            </W>
          </div>
        </AbsoluteFill>
        {t >= 6.05 && <AeCard />}
      </Scene>
    </>
  );
};

// ---------- 03 RHYTHM / HIGGSFIELD ----------

const S3Higgsfield: React.FC = () => {
  const frame = useFrame();
  const fall = (i: number) => {
    const d = frame - f(8.8);
    if (d < 0) return '';
    const r = random(`h${i}`);
    return `translateY(${d * d * 0.9 * (0.5 + r)}px) rotate(${(r - 0.5) * d * 3}deg)`;
  };
  return (
    <Scene from={7.75} to={9.2} bg={P.orange}>
      <AbsoluteFill
        style={{
          background: `repeating-linear-gradient(45deg, ${P.orange} 0 90px, ${P.ink} 90px 180px)`,
          backgroundPosition: `${frame * 9}px 0`,
          backgroundSize: '254px 254px',
        }}
      />
      <Center gap={14}>
        <Row gap={20}>
          <W at={7.82} size={120} kind="serif" anim="mask" style={{textShadow: '0 6px 30px rgba(0,0,0,0.6)'}}>
            not
          </W>
          <W at={7.96} size={120} kind="serif" anim="mask" style={{textShadow: '0 6px 30px rgba(0,0,0,0.6)'}}>
            even
          </W>
        </Row>
        <div style={{position: 'relative', padding: '10px 40px', background: P.ink}}>
          <div style={{display: 'flex'}}>
            {'HIGGSFIELD'.split('').map((ch, i) => (
              <span key={i} style={{display: 'inline-block', transform: fall(i)}}>
                <W at={8.24 + i * 0.02} size={220} anim="slam">
                  {ch}
                </W>
              </span>
            ))}
          </div>
          <div
            style={{
              position: 'absolute',
              left: 20,
              top: '48%',
              height: 26,
              width: `${interpolate(frame, [f(8.75), f(8.75) + 5], [0, 100], clamp)}%`,
              background: P.orange,
            }}
          />
        </div>
      </Center>
    </Scene>
  );
};

// ---------- 04 PARTICLES ----------

const ParticleMorph: React.FC<{from: number; morphAt: number}> = ({from, morphAt}) => {
  const frame = useFrame();
  const ref = React.useRef<HTMLCanvasElement>(null);
  const pts = React.useMemo(() => {
    const N = 3200;
    const off = document.createElement('canvas');
    off.width = 1500;
    off.height = 380;
    const c = off.getContext('2d')!;
    c.fillStyle = '#fff';
    c.font = '900 330px "Arial Black", Arial, sans-serif';
    c.textAlign = 'center';
    c.textBaseline = 'middle';
    c.fillText('CLAUDE', 750, 200);
    const data = c.getImageData(0, 0, 1500, 380).data;
    const tp: [number, number][] = [];
    for (let y = 0; y < 380; y += 5) for (let x = 0; x < 1500; x += 5) if (data[(y * 1500 + x) * 4 + 3] > 128) tp.push([x - 750, y - 190]);
    return Array.from({length: N}, (_, i) => {
      const yy = 1 - (i / (N - 1)) * 2;
      const r = Math.sqrt(1 - yy * yy);
      const th = i * 2.399963;
      return {s: [Math.cos(th) * r, yy, Math.sin(th) * r], t: tp[Math.floor((i * tp.length) / N)] ?? [0, 0], d: random(`pd${i}`), i};
    });
  }, []);
  React.useLayoutEffect(() => {
    const cv = ref.current;
    if (!cv) return;
    const ctx = cv.getContext('2d')!;
    ctx.clearRect(0, 0, 1920, 1080);
    const t = frame / FPS;
    const rot = (t - from) * 1.1;
    const R = 300;
    for (const p of pts) {
      const k = Easing.inOut(Easing.cubic)(Math.min(1, Math.max(0, (t - morphAt - p.d * 0.3) / 0.5)));
      const [x0, y0, z0] = p.s;
      const x1 = x0 * Math.cos(rot) - z0 * Math.sin(rot);
      const z1 = x0 * Math.sin(rot) + z0 * Math.cos(rot);
      const y1 = y0 * Math.cos(0.35) - z1 * Math.sin(0.35);
      const z2 = y0 * Math.sin(0.35) + z1 * Math.cos(0.35);
      const persp = 1200 / (1200 + z2 * R);
      const sx = 960 + x1 * R * persp;
      const sy = 540 + y1 * R * persp;
      const tx = 960 + p.t[0];
      const ty = 560 + p.t[1] + Math.sin(t * 3 + p.d * 10) * 2;
      const px = sx + (tx - sx) * k + Math.sin(p.d * 40) * 140 * Math.sin(Math.PI * k);
      const py = sy + (ty - sy) * k + Math.cos(p.d * 40) * 140 * Math.sin(Math.PI * k);
      const size = (1.4 + 1.6 * persp) * (1 - k) + 2.6 * k;
      ctx.globalAlpha = (0.25 + 0.75 * ((1 - z2) / 2)) * (1 - k) + 0.95 * k;
      ctx.fillStyle = p.i % 17 === 0 ? P.orange : p.i % 23 === 0 ? P.lime : P.cream;
      ctx.fillRect(px, py, size, size);
    }
    ctx.globalAlpha = 1;
  }, [frame, pts, from, morphAt]);
  return <canvas ref={ref} width={1920} height={1080} style={{position: 'absolute', left: 0, top: 0}} />;
};

const S4Particles: React.FC = () => (
  <Scene from={9.2} to={11.0} bg={`radial-gradient(circle at 50% 52%, #2C2566 0%, ${P.deep} 45%, #08080D 100%)`}>
    <ParticleMorph from={9.2} morphAt={9.62} />
    <AbsoluteFill style={{alignItems: 'center', paddingTop: 100}}>
      <W at={9.34} size={110} kind="serif" anim="mask">
        only...
      </W>
    </AbsoluteFill>
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'flex-end', paddingBottom: 190}}>
      <W at={10.2} size={18} kind="mono" color="#ffffffaa" anim="mask">
        3,200 PARTICLES &nbsp;/&nbsp; ONE PROMPT
      </W>
    </AbsoluteFill>
  </Scene>
);

// ---------- 05 PROMPT · 3D ----------

type Tok = {w: string; at: number; hl?: boolean};
const PROMPT: Tok[] = [
  {w: 'Make', at: 14.1},
  {w: 'me', at: 14.16},
  {w: 'a', at: 14.36},
  {w: '15-second,', at: 14.54, hl: true},
  {w: 'PREMIUM,', at: 15.4, hl: true},
  {w: 'DYNAMIC', at: 16.18, hl: true},
  {w: 'motion', at: 16.94},
  {w: 'graphic', at: 17.4},
  {w: '—', at: 17.7},
  {w: 'with', at: 17.86},
  {w: 'smooth', at: 18.26, hl: true},
  {w: '3D', at: 18.64, hl: true},
  {w: 'camera', at: 19.04, hl: true},
  {w: 'movements,', at: 19.34, hl: true},
  {w: 'morphing', at: 20.2, hl: true},
  {w: 'shapes...', at: 20.52, hl: true},
  {w: 'and', at: 21.18},
  {w: 'glow,', at: 21.4, hl: true},
  {w: 'to', at: 21.72},
  {w: 'make', at: 22.06},
  {w: 'it', at: 22.2},
  {w: 'look', at: 22.32},
  {w: 'premium.', at: 22.46},
];
const SEND_AT = 22.8;

const TypedPrompt: React.FC = () => {
  const frame = useFrame();
  const t = frame / FPS;
  let last = -1;
  const spans = PROMPT.map((tok, i) => {
    if (t < tok.at) return null;
    const next = PROMPT[i + 1]?.at ?? tok.at + 0.3;
    const dur = Math.max(0.05, Math.min(0.22, next - tok.at));
    const n = Math.ceil(tok.w.length * Math.min(1, (t - tok.at) / dur));
    last = i;
    const mark = tok.hl ? interpolate(t, [tok.at + dur, tok.at + dur + 0.16], [0, 100], clamp) : 0;
    return (
      <React.Fragment key={i}>
        <span
          style={{
            background: tok.hl ? `linear-gradient(90deg, ${P.hl} ${mark}%, transparent ${mark}%)` : undefined,
            fontWeight: tok.hl && mark > 0 ? 700 : 400,
            borderRadius: 6,
            padding: tok.hl ? '0 4px' : undefined,
          }}
        >
          {tok.w.slice(0, n)}
        </span>{' '}
      </React.Fragment>
    );
  });
  const caretOn = Math.floor(frame / 8) % 2 === 0 || (last >= 0 && t < PROMPT[last].at + 0.3);
  return (
    <div style={{fontFamily: HEAVY, fontSize: 36, lineHeight: 1.5, color: '#1F1E1D', minHeight: 170, textAlign: 'left'}}>
      {last < 0 && <span style={{color: '#A3A099'}}>How can I help you today?</span>}
      {spans}
      {t < SEND_AT && <span style={{display: 'inline-block', width: 3, height: 40, background: P.claude, verticalAlign: 'middle', opacity: caretOn ? 1 : 0}} />}
    </div>
  );
};

const ClaudeWindow: React.FC<{glow: number}> = ({glow}) => {
  const frame = useFrame();
  const send = interpolate(frame, [f(SEND_AT), f(SEND_AT) + 3, f(SEND_AT) + 7], [1, 0.82, 1], clamp);
  const hasText = frame >= f(PROMPT[0].at);
  const Wd = 1100;
  const Ht = 650;
  return (
    <div style={{position: 'absolute', left: 0, top: 0, transformStyle: 'preserve-3d', transform: `translate(-50%, -50%)`, width: Wd, height: Ht}}>
      <div style={{position: 'absolute', inset: 0, borderRadius: 36, background: '#B9B4A7', transform: 'translateZ(-18px)'}} />
      <div style={{position: 'absolute', inset: 0, borderRadius: 36, background: '#CFCABD', transform: 'translateZ(-9px)'}} />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          borderRadius: 36,
          background: '#F5F4EE',
          overflow: 'hidden',
          fontFamily: HEAVY,
          boxShadow: `0 0 ${glow * 90}px ${glow * 10}px rgba(232,244,58,${glow * 0.55})`,
        }}
      >
        <div style={{height: 84, display: 'flex', alignItems: 'center', gap: 14, padding: '0 34px', borderBottom: '1px solid #E6E3D8'}}>
          <Spark size={34} />
          <span style={{fontFamily: SERIF, fontStyle: 'normal', fontSize: 38, color: '#3D3929'}}>Claude</span>
          <div style={{flex: 1}} />
          <span style={{fontFamily: MONO, fontSize: 16, letterSpacing: '0.2em', color: '#9A968A'}}>NEW CHAT</span>
        </div>
        <div style={{marginTop: 52, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 20}}>
          <Spark size={56} rot={frame * 0.6} />
          <span style={{fontFamily: SERIF, fontStyle: 'normal', fontSize: 64, color: '#3D3929'}}>Evening, Jako</span>
        </div>
        <div style={{margin: '40px 46px 0', background: '#FFFFFF', borderRadius: 30, border: `2px solid ${frame >= f(SEND_AT) ? P.claude : '#E8E6DC'}`, boxShadow: '0 10px 34px rgba(0,0,0,0.07)', padding: '28px 34px 22px'}}>
          <TypedPrompt />
          <div style={{display: 'flex', alignItems: 'center', marginTop: 10, gap: 16}}>
            <div style={{width: 50, height: 50, borderRadius: 25, border: '2px solid #DDD9CC', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 32, color: '#6B6960'}}>+</div>
            <div style={{flex: 1}} />
            <span style={{fontSize: 26, color: '#6B6960'}}>Opus 5.5 ⌄</span>
            <div
              style={{
                width: 58,
                height: 58,
                borderRadius: 16,
                background: P.claude,
                opacity: hasText ? 1 : 0.45,
                transform: `scale(${send})`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: 32,
                fontWeight: 700,
              }}
            >
              ↑
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

type Orbiter = {a0: number; speed: number; y: number; el: (t: number) => React.ReactNode};
const ORBITERS: Orbiter[] = [
  {
    a0: 0,
    speed: 14,
    y: -330,
    el: (t) => (
      <div style={{display: 'grid', gridTemplateColumns: 'repeat(4, 34px)', gap: 12}}>
        {Array.from({length: 16}, (_, i) => (
          <div key={i} style={{width: 34, height: 34, borderRadius: 8 + 9 * (0.5 + 0.5 * Math.sin(t * 3 + i)), background: TILE_COLORS[Math.floor(random(`ot${i}`) * 5)], transform: `rotate(${Math.sin(t * 2 + i * 0.5) * 30}deg)`}} />
        ))}
      </div>
    ),
  },
  {a0: 55, speed: 14, y: 380, el: () => <div style={{padding: '18px 34px', borderRadius: 50, background: P.lime, fontFamily: MONO, fontSize: 22, letterSpacing: '0.2em', color: P.ink, whiteSpace: 'nowrap'}}>EASE-OUT · 420MS</div>},
  {
    a0: 115,
    speed: 14,
    y: -250,
    el: (t) => (
      <div style={{width: 380, padding: '22px 26px', borderRadius: 22, background: P.orange, display: 'flex', alignItems: 'center', justifyContent: 'space-between', boxShadow: '0 20px 40px rgba(0,0,0,0.35)'}}>
        <span style={{fontFamily: HEAVY, fontWeight: 700, fontSize: 32, color: P.ink, letterSpacing: '-0.02em'}}>Motion system</span>
        <div style={{width: 70, height: 38, borderRadius: 19, background: P.ink, position: 'relative'}}>
          <div style={{position: 'absolute', top: 5, left: Math.sin(t * 2) > 0 ? 37 : 5, width: 28, height: 28, borderRadius: 14, background: Math.sin(t * 2) > 0 ? P.lime : P.cream}} />
        </div>
      </div>
    ),
  },
  {
    a0: 175,
    speed: 14,
    y: 330,
    el: (t) => {
      const v = Math.round(60 + 39 * (0.5 + 0.5 * Math.sin(t)));
      return (
        <div style={{width: 260, height: 150, borderRadius: 22, background: P.ink, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 20, border: '1px solid #ffffff22'}}>
          <svg width={70} height={70} viewBox="0 0 70 70">
            <circle cx={35} cy={35} r={28} fill="none" stroke="#ffffff22" strokeWidth={8} />
            <circle cx={35} cy={35} r={28} fill="none" stroke={P.orange} strokeWidth={8} strokeDasharray={`${(v / 100) * 176} 176`} transform="rotate(-90 35 35)" />
          </svg>
          <span style={{fontFamily: HEAVY, fontWeight: 900, fontSize: 52, color: P.cream, letterSpacing: '-0.04em'}}>{v}%</span>
        </div>
      );
    },
  },
  {a0: 235, speed: 14, y: -380, el: () => <span style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 130, color: P.cream}}>form.</span>},
  {
    a0: 290,
    speed: 14,
    y: 300,
    el: (t) => (
      <div style={{width: 360, padding: '20px 24px', borderRadius: 22, background: P.violet}}>
        <div style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 40, color: P.cream}}>Keyframes are a language.</div>
        <div style={{display: 'flex', gap: 16, marginTop: 12}}>
          {Array.from({length: 7}, (_, i) => (
            <div key={i} style={{width: 14, height: 14, background: i === Math.floor((t * 4) % 7) ? P.lime : P.cream, transform: 'rotate(45deg)'}} />
          ))}
        </div>
      </div>
    ),
  },
  {a0: 330, speed: 14, y: -60, el: () => <div style={{width: 200, height: 200, position: 'relative'}}><Glass x={100} y={100} r={100} /></div>},
];

const CHIPS = [
  {label: '15 SEC', at: 14.54, color: P.lime},
  {label: 'PREMIUM', at: 15.4, color: P.orange},
  {label: 'DYNAMIC', at: 16.18, color: P.violet},
  {label: '3D CAMERA', at: 18.64, color: P.cream},
  {label: 'MORPHING', at: 20.2, color: P.lime},
  {label: 'GLOW', at: 21.4, color: P.orange},
];
const CHIP_SLOTS = [
  [640, -200],
  [-610, -200],
  [650, -60],
  [-620, -60],
  [660, 80],
  [-630, 80],
];

const Stage3D: React.FC = () => {
  const frame = useFrame();
  const t = frame / FPS;
  const entry = sp(frame, 12.0, {damping: 18, stiffness: 70, mass: 1});
  const swing = t >= 19.04 && t < 20.3 ? Math.sin((Math.PI * (t - 19.04)) / 1.26) : 0;
  const ry = (1 - entry) * 60 + interpolate(t, [12.0, 23.0], [-18, 8], clamp) + swing * 26;
  const rx = (1 - entry) * -20 + interpolate(t, [12.0, 23.0], [10, 4], clamp) + Math.sin(t * 0.9) * 1.5;
  const push = interpolate(t, [22.85, 23.3], [0, 1], {...clamp, easing: Easing.in(Easing.cubic)});
  const camZ = (1 - entry) * -2800 + push * 1550 + interpolate(t, [13, 22.8], [80, 180], clamp);
  const glow = interpolate(t, [21.4, 21.8], [0, 1], clamp);
  const bill = `rotateY(${-ry}deg) rotateX(${-rx}deg)`;
  return (
    <AbsoluteFill style={{perspective: 1800, perspectiveOrigin: '50% 50%'}}>
      <div style={{position: 'absolute', left: 960, top: 540, transformStyle: 'preserve-3d', transform: `translateZ(${camZ}px) rotateX(${rx}deg) rotateY(${ry}deg)`}}>
        <div
          style={{
            position: 'absolute',
            left: 0,
            top: 0,
            width: 3600,
            height: 3600,
            transform: 'translate3d(0, 470px, 0) rotateX(90deg) translate(-50%, -50%)',
            backgroundImage: 'radial-gradient(circle, rgba(241,236,228,0.22) 2.5px, transparent 3px)',
            backgroundSize: '70px 70px',
            WebkitMaskImage: 'radial-gradient(circle, black 15%, transparent 55%)',
          }}
        />
        {[-330, 340].map((y) => (
          <div
            key={y}
            style={{
              position: 'absolute',
              left: 0,
              top: 0,
              width: 2000,
              height: 1040,
              borderRadius: '50%',
              border: '2px solid rgba(241,236,228,0.16)',
              transform: `translate3d(0, ${y}px, 0) rotateX(90deg) translate(-50%, -50%)`,
            }}
          />
        ))}
        <ClaudeWindow glow={glow} />
        {ORBITERS.map((o, i) => {
          const a = ((o.a0 + t * o.speed) * Math.PI) / 180;
          const x = 1000 * Math.sin(a);
          const z = 520 * Math.cos(a);
          const p = sp(frame, 12.3 + i * 0.07, {damping: 12});
          return (
            <div
              key={i}
              style={{
                position: 'absolute',
                left: 0,
                top: 0,
                transform: `translate3d(${x}px, ${o.y}px, ${z}px) ${bill} scale(${p}) translate(-50%, -50%)`,
                filter: glow > 0 ? `drop-shadow(0 0 ${glow * 26}px rgba(232,244,58,0.6))` : undefined,
              }}
            >
              {o.el(t)}
            </div>
          );
        })}
        {t >= 20.2 && (
          <div style={{position: 'absolute', left: 0, top: 0, transform: `translate3d(0px, -470px, 220px) ${bill} scale(${sp(frame, 20.2)}) translate(-50%, -50%)`, filter: `drop-shadow(0 0 24px ${P.lime})`}}>
            <Morph size={130} t={t * 1.4} color={P.lime} />
          </div>
        )}
        {CHIPS.map((c, i) => {
          if (t < c.at) return null;
          const p = sp(frame, c.at, {damping: 13, stiffness: 120});
          const [sx, sy] = CHIP_SLOTS[i];
          const x = interpolate(p, [0, 1], [0, sx]);
          const y = interpolate(p, [0, 1], [120, sy]) + Math.sin(t * 2 + i) * 8;
          const z = interpolate(p, [0, 1], [40, 110]);
          return (
            <div
              key={c.label}
              style={{
                position: 'absolute',
                left: 0,
                top: 0,
                transform: `translate3d(${x}px, ${y}px, ${z}px) ${bill} scale(${0.4 + 0.6 * Math.min(1, p)}) translate(-50%, -50%)`,
                padding: '16px 30px',
                borderRadius: 40,
                background: c.color,
                color: c.color === P.violet ? P.cream : P.ink,
                fontFamily: MONO,
                fontWeight: 600,
                fontSize: 26,
                letterSpacing: '0.18em',
                whiteSpace: 'nowrap',
                boxShadow: `0 16px 34px rgba(0,0,0,0.4), 0 0 ${glow * 40}px ${c.color}`,
              }}
            >
              {c.label}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const S5Prompt: React.FC = () => {
  const frame = useFrame();
  const t = frame / FPS;
  const fly = interpolate(t, [11.95, 12.3], [0, 1], {...clamp, easing: Easing.in(Easing.cubic)});
  return (
    <Scene from={11.0} to={23.3} bg={`radial-gradient(circle at 50% 45%, #1C1A2E 0%, ${P.ink} 60%)`}>
      {t >= 11.9 && <Stage3D />}
      {t < 12.3 && (
        <Center style={{transform: `scale(${1 + fly * 3})`, opacity: 1 - fly, filter: fly > 0 ? `blur(${fly * 16}px)` : undefined}}>
          <Row gap={40}>
            <W at={11.14} size={300} anim="slam">
              HERE&apos;S
            </W>
            <W at={11.42} size={300} kind="serif" color={P.lime} anim="slam">
              how.
            </W>
          </Row>
        </Center>
      )}
      <div style={{position: 'absolute', left: 80, top: 80, display: 'flex', alignItems: 'baseline', gap: 16, background: t >= 12.08 ? 'rgba(12,12,14,0.92)' : undefined, padding: '8px 26px 16px', borderRadius: 18}}>
        {t >= 12.08 && t < 13.32 && (
          <>
            <W at={12.08} size={64} kind="serif" anim="mask">
              I opened
            </W>
            <W at={12.56} size={64} color={P.claude} anim="mask">
              CLAUDE
            </W>
          </>
        )}
        {t >= 13.32 && (
          <W at={13.32} size={64} kind="serif" color={P.lime} anim="mask">
            and typed:
          </W>
        )}
      </div>
    </Scene>
  );
};

// ---------- 06 DEPTH ----------

const S6Depth: React.FC = () => {
  const frame = useFrame();
  const t = frame / FPS;
  const burst = 1 + 0.25 * sp(frame, 24.08, {damping: 8});
  const blob = (i: number, r: number, cx: number, cy: number, sx = 1) => {
    const x = 960 + (cx - 960) * burst + Math.sin(t * 1.3 + i * 2) * 60;
    const y = 540 + (cy - 540) * burst + Math.cos(t * 1.1 + i) * 50;
    return <Glass key={i} x={x} y={y} r={r} sx={sx} rot={i * 37 + t * 20} />;
  };
  return (
    <Scene from={23.3} to={25.4} bg={`radial-gradient(circle at 50% 40%, #2E2A6E 0%, ${P.deep} 55%, #07070C 100%)`}>
      {blob(1, 120, 420, 330)}
      {blob(2, 70, 1500, 260)}
      <AbsoluteFill style={{alignItems: 'center', paddingTop: 150}}>
        <Row gap={24}>
          <W at={23.48} size={110} kind="serif" anim="mask">
            and
          </W>
          <W at={23.68} size={110} kind="serif" color={P.claude} anim="mask">
            Claude...
          </W>
        </Row>
      </AbsoluteFill>
      <Center style={{paddingTop: 120}}>
        <W at={24.08} size={420} anim="slam">
          DID IT!
        </W>
      </Center>
      {blob(3, 150, 1380, 720, 1.9)}
      {blob(4, 95, 600, 800)}
      {blob(5, 60, 1000, 300)}
    </Scene>
  );
};

// ---------- 07 GEOMETRY ----------

const TileField: React.FC<{fillFrom: number; swirlFrom: number}> = ({fillFrom, swirlFrom}) => {
  const frame = useFrame();
  const t = frame / FPS;
  const cols = 26;
  const rows = 15;
  const gap = 76;
  const swirl = interpolate(t, [swirlFrom, swirlFrom + 1.2], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  return (
    <AbsoluteFill>
      {Array.from({length: cols * rows}, (_, i) => {
        const cx0 = 960 + ((i % cols) - (cols - 1) / 2) * gap;
        const cy0 = 540 + (Math.floor(i / cols) - (rows - 1) / 2) * gap;
        const dx = cx0 - 960;
        const dy = cy0 - 540;
        const d = Math.hypot(dx, dy);
        const ang = swirl * (1 - Math.min(1, d / 1300)) * 0.9;
        const cx = 960 + dx * Math.cos(ang) - dy * Math.sin(ang);
        const cy = 540 + dx * Math.sin(ang) + dy * Math.cos(ang);
        const on = t >= fillFrom + random(`tf${i}`) * 1.8;
        const pill = Math.max(0, Math.sin(t * 2.4 + d * 0.01));
        const w = 48 * (1 + 0.7 * pill * swirl);
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: cx - w / 2,
              top: cy - 24,
              width: w,
              height: 48,
              borderRadius: on ? 10 + 14 * (0.5 + 0.5 * Math.sin(t * 3 + d * 0.02)) : 8,
              background: on ? TILE_COLORS[Math.floor(random(`tc${i}`) * 5)] : 'transparent',
              border: on ? 'none' : '2px solid #ffffff14',
              transform: `rotate(${Math.sin(t * 2 + d * 0.012) * 35 + ang * 57}deg) scale(${on ? 1 : 0.8})`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

// This line was re-recorded with different words, so the scene runs on real
// (current-voiceover) time instead of the warped old timeline.
const S7Geometry: React.FC = () => {
  const real = useCurrentFrame();
  return (
    <ClockCtx.Provider value={real}>
      <S7Inner />
    </ClockCtx.Provider>
  );
};

const S7Inner: React.FC = () => {
  const frame = useFrame();
  const t = frame / FPS;
  const count = Math.floor(interpolate(t, [26.7, 31.42], [1, 2400], clamp));
  const word = t >= 30.52 ? ['FRAME.', 30.52] : t >= 29.98 ? ['SINGLE.', 29.98] : t >= 29.42 ? ['EVERY.', 29.42] : null;
  return (
    <Scene from={25.89} to={31.42} bg={P.ink}>
      <TileField fillFrom={26.7} swirlFrom={29.98} />
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(12,12,14,0.85) 0%, rgba(12,12,14,0.35) 40%, transparent 70%)'}} />
      <div style={{position: 'absolute', left: 110, top: 110, display: 'flex', flexDirection: 'column', gap: 10, background: P.ink, padding: '16px 32px 24px', borderRadius: 18}}>
        <div style={{display: 'flex', alignItems: 'baseline', gap: 22}}>
          <W at={25.96} size={90} kind="serif" anim="mask">
            see,
          </W>
          <W at={26.7} size={84} anim="mask">
            SEEDANCE
          </W>
          <W at={26.94} size={84} color={P.lime} anim="mask">
            2.5
          </W>
        </div>
        <div style={{display: 'flex', alignItems: 'baseline', gap: 20}}>
          <W at={27.76} size={64} kind="serif" anim="mask">
            and other
          </W>
          <W at={28.24} size={64} anim="mask">
            AI
          </W>
          <W at={28.58} size={64} anim="mask">
            TOOLS
          </W>
          <W at={28.9} size={64} color={P.orange} anim="mask">
            GENERATE
          </W>
        </div>
      </div>
      {word && (
        <Center>
          <div key={word[0] as string} style={{background: P.ink, padding: '20px 60px 34px', borderRadius: 30}}>
            <W at={word[1] as number} size={300} color={P.cream} anim="slam">
              {word[0]}
            </W>
          </div>
        </Center>
      )}
      {t >= 26.7 && (
        <div style={{position: 'absolute', right: 110, bottom: 120, fontFamily: MONO, fontSize: 26, letterSpacing: '0.2em', color: P.cream, background: P.ink, padding: '10px 20px', borderRadius: 10}}>
          FRAME {String(count).padStart(4, '0')} / ∞
        </div>
      )}
    </Scene>
  );
};

// ---------- 08 INTERFACE / EXPENSIVE ----------

const card: React.CSSProperties = {position: 'absolute', borderRadius: 26, overflow: 'hidden', boxShadow: '0 24px 60px rgba(0,0,0,0.12)'};
const label: React.CSSProperties = {fontFamily: MONO, fontSize: 15, letterSpacing: '0.22em'};

const S8Expensive: React.FC = () => {
  const frame = useFrame();
  const t = frame / FPS;
  const pop = (i: number) => {
    const p = sp(frame, 28.5 + i * 0.07, {damping: 13});
    return {transform: `translateY(${(1 - p) * 80}px) scale(${0.9 + 0.1 * p})`, opacity: Math.min(1, p * 2)};
  };
  const cost = interpolate(t, [29.24, 30.3], [0, 1240], {...clamp, easing: eo});
  const line = interpolate(t, [28.7, 30.3], [0, 1], {...clamp, easing: eo});
  const toggled = t >= 29.1;
  const credits = interpolate(t, [29.24, 30.3], [100, 1], {...clamp, easing: eo});
  const pts = Array.from({length: 12}, (_, i) => [40 + i * 60, 220 - Math.pow(i / 11, 2.4) * 180 + Math.sin(i * 1.7) * 10]);
  const path = pts.map((p, i) => `${i ? 'L' : 'M'}${p[0]} ${p[1]}`).join(' ');
  const cx = interpolate(t, [28.6, 29.05], [1500, 1238], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const cy = interpolate(t, [28.6, 29.05], [950, 598], {...clamp, easing: Easing.inOut(Easing.cubic)});
  return (
    <Scene from={28.45} to={30.4} bg={P.paper}>
      <div style={{position: 'absolute', left: 120, top: 92, display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 8}}>
        <Row gap={22} style={{justifyContent: 'flex-start'}}>
          <W at={28.5} size={110} kind="serif" color={P.ink} anim="mask">
            and
          </W>
          <W at={28.98} size={110} kind="serif" color={P.ink} anim="mask">
            that&apos;s
          </W>
        </Row>
        <W at={29.24} size={230} color={P.orange} anim="slam" style={{transformOrigin: '0 60%'}}>
          EXPENSIVE.
        </W>
      </div>
      <div style={{...card, left: 120, top: 470, width: 640, height: 490, background: 'white', ...pop(0)}}>
        <div style={{...label, position: 'absolute', left: 36, top: 34, color: '#8C877C'}}>COST / VIDEO</div>
        <div style={{position: 'absolute', left: 36, top: 66, fontFamily: HEAVY, fontWeight: 900, fontSize: 84, letterSpacing: '-0.04em', color: P.ink}}>+${Math.round(cost).toLocaleString('en-US')}</div>
        <svg width={780} height={260} viewBox="0 0 780 260" style={{position: 'absolute', left: -40, bottom: 10, transform: 'scale(0.85)', transformOrigin: '0 100%'}}>
          <path d={path} fill="none" stroke={P.orange} strokeWidth={5} strokeDasharray={1200} strokeDashoffset={1200 * (1 - line)} />
        </svg>
      </div>
      <div style={{...card, left: 790, top: 470, width: 560, height: 230, background: P.orange, ...pop(1)}}>
        <div style={{position: 'absolute', left: 34, top: 40, fontFamily: HEAVY, fontWeight: 700, fontSize: 44, letterSpacing: '-0.03em', color: P.ink, width: 330, lineHeight: 1.05}}>Generate every frame</div>
        <div style={{...label, position: 'absolute', left: 36, bottom: 30, color: '#00000088'}}>AI VIDEO TOOLS &nbsp;/&nbsp; GPU</div>
        <div style={{position: 'absolute', right: 40, top: 100, width: 110, height: 60, borderRadius: 30, background: P.ink}}>
          <div style={{position: 'absolute', top: 8, left: toggled ? 58 : 8, width: 44, height: 44, borderRadius: 22, background: toggled ? P.lime : P.cream}} />
        </div>
      </div>
      <div style={{...card, left: 1380, top: 470, width: 420, height: 230, background: P.ink, ...pop(2)}}>
        <div style={{...label, position: 'absolute', left: 32, top: 30, color: '#ffffff88'}}>CREDITS LEFT</div>
        <svg width={130} height={130} viewBox="0 0 70 70" style={{position: 'absolute', left: 30, top: 70}}>
          <circle cx={35} cy={35} r={28} fill="none" stroke="#ffffff22" strokeWidth={7} />
          <circle cx={35} cy={35} r={28} fill="none" stroke={P.orange} strokeWidth={7} strokeDasharray={`${(credits / 100) * 176} 176`} transform="rotate(-90 35 35)" />
        </svg>
        <div style={{position: 'absolute', left: 190, top: 100, fontFamily: HEAVY, fontWeight: 900, fontSize: 70, letterSpacing: '-0.04em', color: P.cream}}>{Math.round(credits)}%</div>
      </div>
      <div style={{...card, left: 1380, top: 730, width: 420, height: 230, background: P.lime, ...pop(3)}}>
        <div style={{...label, position: 'absolute', left: 32, top: 30, color: '#00000088'}}>GPU HOURS</div>
        <div style={{position: 'absolute', left: 32, right: 32, bottom: 28, height: 130, display: 'flex', alignItems: 'flex-end', gap: 14}}>
          {Array.from({length: 7}, (_, i) => (
            <div key={i} style={{flex: 1, borderRadius: 6, background: P.ink, height: `${interpolate(t, [28.7 + i * 0.05, 29.6 + i * 0.08], [8, 30 + i * 11], clamp)}%`}} />
          ))}
        </div>
      </div>
      <div style={{...card, left: 790, top: 730, width: 560, height: 230, background: P.violet, ...pop(4)}}>
        <div style={{position: 'absolute', left: 36, top: 40, fontFamily: SERIF, fontStyle: 'italic', fontSize: 64, color: P.cream}}>Every frame costs.</div>
        <div style={{position: 'absolute', left: 40, bottom: 44, display: 'flex', gap: 14}}>
          {Array.from({length: 10}, (_, i) => (
            <div key={i} style={{width: 18, height: 18, background: Math.floor(frame) % 10 === i ? P.lime : P.cream, transform: 'rotate(45deg)'}} />
          ))}
        </div>
      </div>
      {t >= 28.6 && <Cursor x={cx} y={cy} press={t >= 29.05 && t < 29.15} />}
    </Scene>
  );
};

// ---------- 09 CODE ----------

const CODE = [
  'const frame = useFrame();',
  'const glow = spring({ frame, fps });',
  'return (',
  '  <Camera3D orbit={glow * 25}>',
  '    <Morph from="circle" to="star" />',
  '    <Glow intensity={0.9} />',
  '  </Camera3D>',
  ');',
];
const highlight = (s: string) =>
  s.split(/("[^"]*"?|<\/?[A-Za-z0-9]+|\b(?:const|return)\b|\b\d+(?:\.\d+)?\b)/g).map((part, i) => {
    let color = '#E6E3DC';
    if (/^"/.test(part)) color = P.lime;
    else if (/^<\/?[A-Za-z]/.test(part)) color = '#9E93FF';
    else if (/^(const|return)$/.test(part)) color = P.orange;
    else if (/^\d/.test(part)) color = P.claude;
    return (
      <span key={i} style={{color}}>
        {part}
      </span>
    );
  });

const S9Code: React.FC = () => {
  const frame = useFrame();
  const t = frame / FPS;
  let budget = Math.floor(interpolate(t, [30.7, 32.2], [0, CODE.join('').length], clamp));
  const p = sp(frame, 30.5, {damping: 16, stiffness: 120});
  return (
    <Scene from={30.4} to={32.3} bg={P.ink}>
      <div style={{position: 'absolute', left: 120, top: 250, display: 'flex', flexDirection: 'column', gap: 26}}>
        <W at={30.62} size={170} kind="serif" color={P.claude} anim="mask">
          Claude?
        </W>
        <Row gap={20} style={{justifyContent: 'flex-start'}}>
          <W at={31.02} size={84} anim="mask">
            IT
          </W>
          <W at={31.16} size={84} anim="mask">
            JUST
          </W>
          <W at={31.3} size={84} anim="mask">
            WRITES
          </W>
        </Row>
        <W at={31.56} size={260} color={P.lime} anim="slam" style={{transformOrigin: '0 60%'}}>
          CODE.
        </W>
      </div>
      <AbsoluteFill style={{perspective: 1600}}>
        <div
          style={{
            position: 'absolute',
            left: 930,
            top: 230,
            width: 880,
            borderRadius: 24,
            background: '#141418',
            border: '1px solid #ffffff1c',
            transform: `rotateY(${-22 + (1 - p) * -30 + Math.sin(t) * 3}deg) rotateX(${8}deg) translateZ(${(1 - p) * -600}px)`,
            boxShadow: '-40px 40px 100px rgba(0,0,0,0.6)',
            overflow: 'hidden',
          }}
        >
          <div style={{height: 56, background: '#1C1C22', display: 'flex', alignItems: 'center', gap: 10, padding: '0 22px'}}>
            {['#FF5F57', '#FEBC2E', '#28C840'].map((c) => (
              <div key={c} style={{width: 15, height: 15, borderRadius: 8, background: c}} />
            ))}
            <span style={{marginLeft: 14, ...label, color: '#ffffff77'}}>REEL.TSX</span>
          </div>
          <div style={{padding: '24px 28px 30px', fontFamily: MONO, fontSize: 30, lineHeight: 1.6, whiteSpace: 'pre'}}>
            {CODE.map((line, i) => {
              const shown = line.slice(0, Math.max(0, budget));
              budget -= line.length;
              return (
                <div key={i} style={{minHeight: 48}}>
                  <span style={{color: '#55555E', marginRight: 22}}>{String(i + 1).padStart(2, ' ')}</span>
                  {highlight(shown)}
                </div>
              );
            })}
          </div>
        </div>
      </AbsoluteFill>
    </Scene>
  );
};

// ---------- 10 EVERYTHING ----------

const Halftone: React.FC = () => {
  const frame = useFrame();
  const t = frame / FPS;
  return (
    <AbsoluteFill>
      {Array.from({length: 48 * 27}, (_, i) => {
        const x = (i % 48) * 40 + 20;
        const y = Math.floor(i / 48) * 40 + 20;
        const d = Math.hypot(x - 960, y - 540);
        const r = 2 + 13 * (0.5 + 0.5 * Math.cos(d * 0.03 - t * 7));
        return <div key={i} style={{position: 'absolute', left: x - r, top: y - r, width: 2 * r, height: 2 * r, borderRadius: '50%', background: 'rgba(241,236,228,0.75)'}} />;
      })}
    </AbsoluteFill>
  );
};

const S10Every: React.FC = () => {
  const frame = useFrame();
  const t = frame / FPS;
  const burst = interpolate(t, [33.52, 33.9], [0, 1], {...clamp, easing: eo});
  return (
    <>
      <Scene from={32.3} to={33.3} bg={P.violet}>
        <Halftone />
        <Center>
          <W at={32.4} size={130} kind="serif" anim="mask" style={{textShadow: '0 6px 30px rgba(40,20,120,0.6)'}}>
            every
          </W>
          <div style={{background: P.violet, padding: '0 40px 20px', borderRadius: 24}}>
            <W at={32.6} size={360} anim="slam">
              FRAME
            </W>
          </div>
        </Center>
      </Scene>
      <Scene from={33.3} to={34.25} bg={P.ink}>
        <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
          <div style={{width: 900 * burst + 200, height: 900 * burst + 200, borderRadius: '50%', background: `radial-gradient(circle, ${P.lime} 0%, ${P.orange}88 35%, transparent 65%)`, opacity: 0.9 - burst * 0.4}} />
          <svg width={1400} height={1400} viewBox="-700 -700 1400 1400" style={{position: 'absolute'}}>
            {Array.from({length: 24}, (_, i) => {
              const a = (i / 24) * Math.PI * 2;
              return <line key={i} x1={Math.cos(a) * 200 * burst} y1={Math.sin(a) * 200 * burst} x2={Math.cos(a) * 640 * burst} y2={Math.sin(a) * 640 * burst} stroke={i % 2 ? P.lime : P.cream} strokeWidth={6} strokeLinecap="round" opacity={0.7} />;
            })}
          </svg>
        </AbsoluteFill>
        <Center>
          <W at={33.34} size={130} kind="serif" anim="mask">
            every
          </W>
          <W at={33.52} size={360} anim="slam" style={{textShadow: `0 0 60px ${P.lime}`}}>
            EFFECT
          </W>
        </Center>
      </Scene>
      <Scene from={34.25} to={35.2} bg={P.orange}>
        <Center>
          <W at={34.28} size={130} kind="serif" color={P.ink} anim="mask">
            every
          </W>
          <div style={{display: 'flex', alignItems: 'center'}}>
            {'MOTION'.split('').map((ch, i) => {
              const p = sp(frame, 34.46 + i * 0.035, {damping: 10, stiffness: 230});
              const tilt = [-9, 0, 7, -5, 0, 10][i];
              const shown = frame >= f(34.46 + i * 0.035);
              return (
                <span key={i} style={{display: 'inline-block', margin: '0 -4px', transform: `translateY(${(1 - p) * 400}px) rotate(${tilt * p}deg)`, opacity: shown ? 1 : 0}}>
                  {ch === 'O' ? <DotO size={250} rot={t * 120} /> : <span style={{...fontFor('heavy'), fontSize: 340, color: P.ink}}>{ch}</span>}
                </span>
              );
            })}
          </div>
        </Center>
      </Scene>
      <Scene from={35.2} to={36.2} bg={P.lime}>
        <Ghosts text="DESIGN" size={360} color={P.ink} at={35.42} />
        <Center>
          <W at={35.26} size={130} kind="serif" color={P.ink} anim="mask">
            every
          </W>
          <W at={35.42} size={360} color={P.ink} anim="slam">
            DESIGN
          </W>
        </Center>
      </Scene>
    </>
  );
};

// ---------- 11 ALL MADE WITH CODE ----------

const S11All: React.FC = () => (
  <Scene from={36.2} to={37.8} bg={P.paper}>
    <AbsoluteFill style={{flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 50}}>
      <W at={36.26} size={600} color={P.ink} anim="slam">
        ALL
      </W>
      <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 10}}>
        <Row gap={22} style={{justifyContent: 'flex-start'}}>
          <W at={36.54} size={130} kind="serif" color={P.ink} anim="mask">
            made
          </W>
          <W at={36.82} size={130} kind="serif" color={P.ink} anim="mask">
            with
          </W>
        </Row>
        <Row gap={24} style={{justifyContent: 'flex-start', alignItems: 'center'}}>
          <W at={37.04} size={120} kind="mono" color={P.violet} anim="pop" style={{letterSpacing: 0}}>
            &lt;/&gt;
          </W>
          <W at={37.04} size={200} color={P.orange} anim="slam">
            CODE.
          </W>
        </Row>
      </div>
    </AbsoluteFill>
  </Scene>
);

// ---------- 12 MONEY / TIME ----------

const MoneyRain: React.FC<{from: number}> = ({from}) => {
  const frame = useFrame();
  return (
    <AbsoluteFill>
      {Array.from({length: 26}, (_, i) => {
        const start = f(from) + random(`d${i}`) * 16;
        const d = frame - start;
        if (d < 0) return null;
        const x = random(`x${i}`) * 1900 - 60;
        const y = -240 + d * (30 + random(`v${i}`) * 22);
        const rot = (random(`r${i}`) - 0.5) * 90 + d * (random(`w${i}`) - 0.5) * 12;
        const c = [P.cream, P.lime, P.ink][i % 3];
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: x,
              top: y,
              width: 250,
              height: 120,
              borderRadius: 14,
              background: c,
              border: `5px solid ${c === P.ink ? P.cream : P.ink}`,
              transform: `rotate(${rot}deg) rotateY(${Math.sin(d / 4 + i) * 55}deg)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              ...fontFor('heavy'),
              fontSize: 76,
              color: c === P.ink ? P.cream : P.ink,
            }}
          >
            $
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const DotClock: React.FC<{from: number}> = ({from}) => {
  const frame = useFrame();
  const d = frame - f(from);
  const p = sp(frame, from, {damping: 12});
  const lit = (d * 2) % 60;
  return (
    <svg width={560} height={560} viewBox="-280 -280 560 560" style={{transform: `scale(${p}) rotate(${(1 - p) * -90}deg)`}}>
      {Array.from({length: 60}, (_, i) => {
        const a = (i / 60) * Math.PI * 2 - Math.PI / 2;
        const on = i <= lit;
        return <circle key={i} cx={Math.cos(a) * 240} cy={Math.sin(a) * 240} r={i % 5 === 0 ? 13 : 8} fill={on ? P.lime : 'rgba(241,236,228,0.35)'} />;
      })}
      <line x1={0} y1={0} x2={0} y2={-130} stroke={P.cream} strokeWidth={18} strokeLinecap="round" transform={`rotate(${d * 4})`} />
      <line x1={0} y1={0} x2={0} y2={-190} stroke={P.orange} strokeWidth={10} strokeLinecap="round" transform={`rotate(${d * 40})`} />
      <circle r={18} fill={P.cream} />
    </svg>
  );
};

const S12MoneyTime: React.FC = () => (
  <>
    <Scene from={37.8} to={39.65} bg={P.orange}>
      <MoneyRain from={39.0} />
      <div style={{position: 'absolute', left: 120, top: 150}}>
        <Row gap={22} style={{justifyContent: 'flex-start'}}>
          <W at={37.84} size={110} kind="serif" color={P.ink} anim="mask">
            so
          </W>
          <W at={37.98} size={110} kind="serif" color={P.ink} anim="mask">
            bro —
          </W>
        </Row>
      </div>
      <Center style={{paddingTop: 80}}>
        <Row gap={34}>
          <W at={38.52} size={170} color={P.cream} anim="slam" style={{background: P.ink, padding: '0 24px 10px', borderRadius: 14}}>
            DON&apos;T
          </W>
          <W at={38.76} size={170} color={P.ink} anim="slam">
            WASTE
          </W>
          <W at={38.92} size={170} color={P.ink} anim="slam">
            YOUR
          </W>
        </Row>
        <W at={39.12} size={380} color={P.cream} anim="slam" style={{textShadow: '0 20px 60px rgba(0,0,0,0.25)'}}>
          MONEY.
        </W>
      </Center>
    </Scene>
    <Scene from={39.65} to={40.9} bg={P.violet}>
      <AbsoluteFill style={{flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 80}}>
        <DotClock from={39.68} />
        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-start'}}>
          <Row gap={26} style={{justifyContent: 'flex-start'}}>
            <W at={39.7} size={130} color={P.violet} anim="slam" style={{background: P.cream, padding: '0 20px 8px', borderRadius: 12}}>
              DON&apos;T
            </W>
            <W at={39.92} size={130} anim="slam">
              WASTE
            </W>
          </Row>
          <W at={40.06} size={130} anim="mask" style={{marginTop: 14}}>
            YOUR
          </W>
          <W at={40.28} size={340} color={P.lime} anim="slam">
            TIME.
          </W>
        </div>
      </AbsoluteFill>
    </Scene>
  </>
);

// ---------- 13 IDENTITY ----------

const S13Identity: React.FC = () => {
  const frame = useFrame();
  const t = frame / FPS;
  const word = '"CLAUDE"';
  const typed = Math.ceil(word.length * interpolate(t, [41.34, 41.75], [0, 1], clamp));
  const line = interpolate(t, [41.9, 42.4], [0, 1], {...clamp, easing: eo});
  const end = interpolate(t, [44.0, 44.4], [0, 1], {...clamp, easing: Easing.in(Easing.cubic)});
  const orbit = (rx: number, ry: number, rot: number, speed: number, color: string) => {
    const a = t * speed;
    return (
      <div style={{position: 'absolute', left: 960 - rx, top: 520 - ry, width: rx * 2, height: ry * 2, transform: `rotate(${rot}deg)`}}>
        <div style={{position: 'absolute', inset: 0, borderRadius: '50%', border: '1.5px solid rgba(241,236,228,0.22)'}} />
        <div style={{position: 'absolute', left: rx + Math.cos(a) * rx - 9, top: ry + Math.sin(a) * ry - 9, width: 18, height: 18, borderRadius: 9, background: color, boxShadow: `0 0 20px ${color}`}} />
      </div>
    );
  };
  return (
    <Scene from={40.9} to={DURATION_S + 1} bg={`radial-gradient(circle at 50% 45%, #2A1A12 0%, #120D0B 55%, #08070A 100%)`}>
      <AbsoluteFill style={{opacity: 1 - end}}>
        {t >= 41.2 && (
          <>
            {orbit(640, 170, -8, 2.2, P.lime)}
            {orbit(700, 210, 6, -1.6, P.orange)}
          </>
        )}
        <AbsoluteFill style={{alignItems: 'center', paddingTop: 170}}>
          <W at={41.08} size={110} kind="serif" anim="mask">
            comment
          </W>
        </AbsoluteFill>
        <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', perspective: 900}}>
          <div style={{display: 'flex', marginTop: -40}}>
            {'CLAUDE'.split('').map((ch, i) => {
              const at = 41.34 + i * 0.06;
              const p = sp(frame, at, {damping: 11, stiffness: 150});
              const r = random(`c${i}`);
              return (
                <span
                  key={i}
                  style={{
                    ...fontFor('heavy'),
                    fontSize: 300,
                    color: P.cream,
                    display: 'inline-block',
                    opacity: frame >= f(at) ? 1 : 0,
                    transform: `translateY(${(1 - p) * -420}px) rotateX(${(1 - p) * (r * 160 - 80)}deg) rotateY(${(1 - p) * (90 - r * 180)}deg) rotateZ(${(1 - p) * (r * 70 - 35)}deg)`,
                  }}
                >
                  {ch}
                </span>
              );
            })}
          </div>
          <div style={{width: 1100, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginTop: 18}}>
            <div style={{display: 'flex', gap: 14}}>
              {['AND', "I'LL", 'SEND', 'YOU'].map((w, i) => (
                <W key={w} at={[41.86, 42.34, 42.48, 42.62][i]} size={22} kind="mono" anim="mask">
                  {w}
                </W>
              ))}
            </div>
            <Row gap={16}>
              <W at={42.76} size={80} kind="serif" anim="mask">
                the
              </W>
              <W at={42.88} size={80} kind="serif" color={P.lime} anim="mask">
                instructions
              </W>
            </Row>
          </div>
        </AbsoluteFill>
        <div style={{position: 'absolute', left: 960 - 550, top: 690, width: 1100 * line, height: 4, background: P.orange}} />
        <div
          style={{
            position: 'absolute',
            left: 960 - 330,
            top: 800,
            width: 660,
            height: 84,
            borderRadius: 42,
            background: '#ffffff10',
            border: `2px solid ${t >= 41.85 ? P.lime : '#ffffff26'}`,
            display: 'flex',
            alignItems: 'center',
            gap: 18,
            padding: '0 18px',
            opacity: interpolate(t, [41.0, 41.2], [0, 1], clamp),
          }}
        >
          <div style={{width: 52, height: 52, borderRadius: 26, background: P.lime, display: 'flex', alignItems: 'center', justifyContent: 'center', ...fontFor('heavy'), fontSize: 30, color: P.ink}}>J</div>
          <div style={{flex: 1, textAlign: 'left', fontFamily: HEAVY, fontWeight: 700, fontSize: 34, color: typed > 0 ? P.lime : '#ffffff66'}}>{typed > 0 ? word.slice(0, typed) : 'Add a comment...'}</div>
          <div style={{fontFamily: MONO, fontSize: 18, letterSpacing: '0.2em', color: P.lime}}>POST</div>
        </div>
        <AbsoluteFill style={{alignItems: 'center', justifyContent: 'flex-end', paddingBottom: 110}}>
          <W at={43.4} size={20} kind="mono" color="#ffffffaa" anim="mask">
            @JAKO.FRAMES &nbsp;/&nbsp; SHOWREEL 2026
          </W>
        </AbsoluteFill>
      </AbsoluteFill>
      {end > 0 && <div style={{position: 'absolute', left: 960 - 300, top: 539, width: 600, height: 3, background: P.orange}} />}
    </Scene>
  );
};

export const ReelWide: React.FC = () => {
  const real = useCurrentFrame();
  const frame = toOld(real / FPS) * FPS;
  const s = shake(frame);
  return (
    <ClockCtx.Provider value={frame}>
    <AbsoluteFill style={{background: P.ink, overflow: 'hidden'}}>
      <AbsoluteFill style={{transform: `translate(${s.x}px, ${s.y}px)`}}>
        <S0Ignition />
        <S1World />
        <S2AfterEffects />
        <S3Higgsfield />
        <S4Particles />
        <S5Prompt />
        <S6Depth />
        <S7Geometry />
        <S8Expensive />
        <S9Code />
        <S10Every />
        <S11All />
        <S12MoneyTime />
        <S13Identity />
      </AbsoluteFill>
      <AbsoluteFill style={{pointerEvents: 'none', opacity: 0.06, backgroundImage: 'repeating-radial-gradient(circle at 17% 32%, #fff 0 1px, transparent 1px 3px)', mixBlendMode: 'overlay'}} />
      <Hud />
    </AbsoluteFill>
    </ClockCtx.Provider>
  );
};
