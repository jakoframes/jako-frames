import React from 'react';
import {spring, random} from 'remotion';
import {loadFont as loadBricolage} from '@remotion/google-fonts/BricolageGrotesque';
import {loadFont as loadSerif} from '@remotion/google-fonts/InstrumentSerif';
import {loadFont as loadMono} from '@remotion/google-fonts/JetBrainsMono';
import {FPS} from './timing';

export const FONT = {
  display: loadBricolage('normal', {weights: ['500', '700', '800'], subsets: ['latin']}).fontFamily,
  serif: loadSerif('italic', {weights: ['400'], subsets: ['latin']}).fontFamily,
  mono: loadMono('normal', {weights: ['500', '700'], subsets: ['latin']}).fontFamily,
};

// 60 / 30 / 10: warm white studio, ink type, Claude orange.
// Cobalt only for design-tool selections, lime only as a highlighter.
export const C = {
  bg: '#F3F0EA', paper: '#FFFFFF', ink: '#141217', ink2: '#3B3842', muted: '#76717D', line: 'rgba(20,18,23,.09)',
  orange: '#EE6A3A', orangeDeep: '#B5441C', orangeSoft: '#FFE6DA', cobalt: '#3157FF', cobaltSoft: '#E3E8FF', lime: '#DDF55E', green: '#18A957',
};
// one shadow recipe for the whole world: key light above and a little left, so shadows fall down-right
export const SHADOW = '0 2px 4px rgba(46,30,16,.06), 0 18px 36px -10px rgba(46,30,16,.20), 0 46px 80px -24px rgba(46,30,16,.22)';

// ---------- easing ----------
export const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));
export const prog = (t: number, a: number, d: number) => clamp((t - a) / d);
export const outCubic = (p: number) => 1 - Math.pow(1 - p, 3);
export const inCubic = (p: number) => p * p * p;
export const inOutCubic = (p: number) => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2);
export const outExpo = (p: number) => (p >= 1 ? 1 : 1 - Math.pow(2, -10 * p));
export const inOutQuint = (p: number) => (p < 0.5 ? 16 * p ** 5 : 1 - Math.pow(-2 * p + 2, 5) / 2);
export const backOut = (p: number) => {
  const c1 = 1.3, c3 = c1 + 1;
  return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2);
};
export const lerp = (a: number, b: number, p: number) => a + (b - a) * p;
// tight spring, 0 before `a` (seconds)
export const pop = (t: number, a: number, cfg: Record<string, number> = {}) =>
  t < a ? 0 : spring({frame: Math.round((t - a) * FPS), fps: FPS, config: {damping: 18, stiffness: 160, mass: 0.8, ...cfg}});
// value that eases to each new key target as time passes it; keys: [time, value, duration?]
export const seq = (t: number, keys: [number, number, number?][], dur = 0.3, ease = inOutCubic) => {
  let from = keys[0][1], to = keys[0][1], start = -1e9, d = dur;
  for (let i = 1; i < keys.length && keys[i][0] <= t; i++) {
    from = from + (to - from) * ease(Math.min(1, (keys[i][0] - start) / d));
    to = keys[i][1];
    start = keys[i][0];
    d = keys[i][2] ?? dur;
  }
  return from + (to - from) * ease(Math.min(1, (t - start) / d));
};
export const step = <V,>(t: number, keys: [number, V][]): V => {
  let v = keys[0][1];
  for (const [k, kv] of keys) if (t >= k) v = kv;
  return v;
};
export const rnd = (k: string | number) => random(`cc-${k}`);
// damped wobble that starts at `a`: 0 → kicks → settles
export const wobble = (t: number, a: number, freq = 26, decay = 8) => (t < a ? 0 : Math.exp(-(t - a) * decay) * Math.sin((t - a) * freq));

// ---------- 3D object: places children (centered) at a world point ----------
export const O: React.FC<{x?: number; y?: number; z?: number; rx?: number; ry?: number; rz?: number; s?: number; o?: number; anchor?: string; children?: React.ReactNode; style?: React.CSSProperties}> = ({x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0, s = 1, o = 1, anchor = 'translate(-50%,-50%)', children, style}) => {
  if (o <= 0.001) return null;
  return (
    <div style={{position: 'absolute', left: 0, top: 0, transformStyle: 'preserve-3d', transform: `translate3d(${x}px,${y}px,${z}px) rotateY(${ry}deg) rotateX(${rx}deg) rotateZ(${rz}deg) scale(${s})`}}>
      <div style={{position: 'absolute', left: 0, top: 0, transform: anchor, opacity: o, transformStyle: 'preserve-3d', ...style}}>{children}</div>
    </div>
  );
};

// ---------- paper card with a physical edge (stacked layers behind it read as thickness when the camera turns) ----------
export const Card: React.FC<{w: number; h: number; radius?: number; ring?: number; ringColor?: string; depth?: number; style?: React.CSSProperties; children?: React.ReactNode}> = ({w, h, radius = 30, ring = 0, ringColor = C.orange, depth = 12, style, children}) => (
  <div style={{position: 'relative', width: w, height: h, transformStyle: 'preserve-3d'}}>
    {Array.from({length: Math.ceil(depth / 3)}, (_, i) => (
      <div key={i} style={{position: 'absolute', inset: 0, borderRadius: radius, background: i === Math.ceil(depth / 3) - 1 ? '#D3CCC2' : '#E4DED6', transform: `translateZ(${-(i + 1) * 3}px)`}} />
    ))}
    <div style={{position: 'absolute', inset: 0, borderRadius: radius, overflow: 'hidden', boxSizing: 'border-box', background: C.paper, border: `1.5px solid ${C.line}`,
      boxShadow: `${SHADOW}${ring > 0 ? `, 0 0 0 ${(4 * ring).toFixed(2)}px ${ringColor}` : ''}`, ...style}}>{children}</div>
  </div>
);

export const Mono: React.FC<{size?: number; color?: string; w?: number; children: React.ReactNode; style?: React.CSSProperties}> = ({size = 24, color = C.muted, w = 500, children, style}) => (
  <div style={{fontFamily: FONT.mono, fontWeight: w, fontSize: size, color, letterSpacing: '.01em', whiteSpace: 'nowrap', lineHeight: 1.2, fontVariantNumeric: 'tabular-nums', ...style}}>{children}</div>
);

export const Text: React.FC<{size: number; color?: string; w?: number; serif?: boolean; children: React.ReactNode; style?: React.CSSProperties}> = ({size, color = C.ink, w = 700, serif, children, style}) => (
  <div style={{fontFamily: serif ? FONT.serif : FONT.display, fontStyle: serif ? 'italic' : 'normal', fontWeight: serif ? 400 : w, fontSize: size, lineHeight: 1.05,
    letterSpacing: serif ? '-0.005em' : '-0.025em', color, whiteSpace: 'nowrap', ...style}}>{children}</div>
);

// big display type with a short extrusion + a soft cast shadow (reads as a solid slab under camera moves)
export const Big: React.FC<{size: number; color?: string; side?: string; serif?: boolean; depth?: number; children: React.ReactNode; style?: React.CSSProperties}> = ({size, color = C.ink, side, serif, depth = 9, children, style}) => {
  const sd = side ?? (color === C.orange ? C.orangeDeep : color === C.paper ? '#CFC7BC' : '#4A4552');
  const ext = serif ? [] : Array.from({length: depth}, (_, i) => `${((i + 1) * 0.3).toFixed(1)}px ${((i + 1) * 0.85).toFixed(1)}px 0 ${sd}`);
  ext.push(`${Math.round(size * 0.03)}px ${Math.round(size * 0.12)}px ${Math.round(size * 0.16)}px rgba(46,30,16,.20)`);
  return (
    <div style={{fontFamily: serif ? FONT.serif : FONT.display, fontStyle: serif ? 'italic' : 'normal', fontWeight: serif ? 400 : 800, fontSize: size, lineHeight: 0.92,
      letterSpacing: serif ? '-0.01em' : '-0.04em', color, whiteSpace: 'nowrap', textShadow: ext.join(','), ...style}}>{children}</div>
  );
};

// lime highlighter swipe behind a word (p: 0 → 1)
export const Marker: React.FC<{p: number; color?: string; children: React.ReactNode}> = ({p, color = C.lime, children}) => (
  <span style={{position: 'relative', display: 'inline-block'}}>
    <span style={{position: 'absolute', left: '-5%', right: '-5%', top: '22%', bottom: '2%', background: color, borderRadius: 12, transform: `scaleX(${p}) rotate(-1.5deg)`, transformOrigin: 'left center'}} />
    <span style={{position: 'relative'}}>{children}</span>
  </span>
);

// ---------- icons: one 24-grid stroke family ----------
const PATHS: Record<string, string> = {
  upload: 'M12 15V4 M7.5 8.5 12 4l4.5 4.5 M4 15v3.5A1.5 1.5 0 0 0 5.5 20h13a1.5 1.5 0 0 0 1.5-1.5V15',
  image: 'M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z M21 15l-5-5L5 21 M9 10.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z',
  clip: 'M21.4 11.1l-9.2 9.2a6 6 0 0 1-8.5-8.5l9.2-9.2a4 4 0 0 1 5.7 5.7l-9.2 9.2a2 2 0 0 1-2.8-2.8l8.5-8.5',
  file: 'M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z M14 3v5h5 M9 13h6 M9 17h4',
  clock: 'M12 21a8 8 0 1 0 0-16 8 8 0 0 0 0 16z M12 9v4l2.5 2 M10 2h4 M12 2v3 M19 5l1.5 1.5',
  pen: 'M12 19l7-7 3 3-7 7-3-3z M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z M2 2l7.6 7.6 M11 13a2 2 0 1 0 0-4 2 2 0 0 0 0 4z',
  layers: 'M12 2 2 7l10 5 10-5-10-5z M2 17l10 5 10-5 M2 12l10 5 10-5',
  up: 'M12 19V5 M5 12l7-7 7 7',
  check: 'M20 6 9 17l-5-5',
  heart: 'M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1.1L12 21l7.8-7.8 1-1.1a5.5 5.5 0 0 0 0-7.8z',
  chat: 'M21 11.5a8.4 8.4 0 0 1-9 8.4 8.6 8.6 0 0 1-3.8-.9L3 21l1.9-5.7A8.4 8.4 0 0 1 12 3a8.5 8.5 0 0 1 9 8.5z',
  plane: 'M22 2 11 13 M22 2l-7 20-4-9-9-4 20-7z',
  music: 'M9 18V5l12-2v13 M6 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M18 19a3 3 0 1 0 0-6 3 3 0 0 0 0 6z',
  shapes: 'M8.5 10 12 3.5l3.5 6.5z M14 14h7v7h-7z M6.5 21.5a4 4 0 1 0 0-8 4 4 0 0 0 0 8z',
  zip: 'M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z M14 3v5h5 M10 5h2 M10 8h2 M10 11h2 M10 14h2v3h-2z',
  play: 'M7 4.5v15l12-7.5z',
  x: 'M18 6 6 18 M6 6l12 12',
};
export const Icon: React.FC<{name: keyof typeof PATHS | string; size?: number; color?: string; sw?: number; fill?: string}> = ({name, size = 32, color = C.ink, sw = 2, fill = 'none'}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" style={{display: 'block', flex: 'none', overflow: 'visible'}}>
    <path d={PATHS[name]} fill={fill} stroke={color} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const Cursor: React.FC<{size?: number}> = ({size = 64}) => (
  <svg width={size} height={size} viewBox="0 0 60 60" style={{overflow: 'visible', display: 'block', filter: 'drop-shadow(2px 6px 6px rgba(46,30,16,.35))'}}>
    <path d="M6,4 L50,30 L30,34 L40,54 L32,58 L22,38 L8,50 Z" fill={C.ink} stroke="#fff" strokeWidth={3.5} strokeLinejoin="round" />
  </svg>
);

// Claude-style spark (asterisk with uneven tapered rays)
const RAYS: [number, number, number][] = [[0, 46, 6.5], [36, 37, 5.5], [72, 44, 6.5], [108, 35, 5.5], [144, 46, 6.5], [180, 39, 5.5], [216, 45, 6.5], [252, 36, 5.5], [288, 44, 6.5], [324, 38, 5.5]];
export const Spark: React.FC<{size: number; color?: string; rot?: number}> = ({size, color = C.orange, rot = 0}) => (
  <svg width={size} height={size} viewBox="-50 -50 100 100" style={{display: 'block', overflow: 'visible', transform: `rotate(${rot}deg)`}}>
    {RAYS.map(([a, l, w], i) => <path key={i} d={`M0,${-w} L${l - w},${-w * 0.42} Q${l + 1},0 ${l - w},${w * 0.42} L0,${w} Z`} transform={`rotate(${a - 90})`} fill={color} />)}
    <circle r={8} fill={color} />
  </svg>
);

export const Flame: React.FC<{size: number; t: number}> = ({size, t}) => {
  const f = Math.sin(t * 19) * 0.04 + Math.sin(t * 31) * 0.03;
  return (
    <svg width={size} height={size * 1.3} viewBox="0 0 40 52" style={{display: 'block', overflow: 'visible'}}>
      <defs>
        <linearGradient id="fl" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stopColor={C.orangeDeep} /><stop offset=".55" stopColor={C.orange} /><stop offset="1" stopColor="#FFB48C" /></linearGradient>
      </defs>
      <g transform={`translate(20 50) scale(${1 - f} ${1 + f * 2}) translate(-20 -50)`}>
        <path d="M20,2 C26,12 36,20 36,33 C36,43 29,50 20,50 C11,50 4,43 4,33 C4,25 9,20 12,13 C14,19 16,21 19,22 C18,14 18,8 20,2 Z" fill="url(#fl)" />
        <path d="M20,26 C24,31 28,35 28,40 C28,45 24.5,48 20,48 C15.5,48 12,45 12,40 C12,36 15,33 17,30 C18,33 19,34 21,34 C20,31 20,29 20,26 Z" fill="#FFE1CF" />
      </g>
    </svg>
  );
};

// ---------- solid-looking décor: glossy balls (always face the camera), cubes, rings ----------
export const BALLS: Record<string, [string, string, string]> = {
  orange: ['#FFC9AE', C.orange, '#A9390F'],
  cobalt: ['#B9C7FF', C.cobalt, '#152BA3'],
  ink: ['#8D8894', '#26232B', '#040305'],
  white: ['#FFFFFF', '#F1EDE7', '#C8C0B4'],
  lime: ['#F8FFD2', C.lime, '#93AD12'],
};
export const Ball: React.FC<{size: number; tone: keyof typeof BALLS | string}> = ({size, tone}) => {
  const [hi, mid, lo] = BALLS[tone] ?? BALLS.white;
  return <div style={{width: size, height: size, borderRadius: '50%', background: `radial-gradient(circle at 33% 27%, ${hi} 0%, ${mid} 36%, ${lo} 100%)`, boxShadow: `0 ${size * 0.18}px ${size * 0.3}px -${size * 0.08}px rgba(46,30,16,.28)`}} />;
};
export const Cube: React.FC<{s: number; tone: keyof typeof BALLS | string}> = ({s, tone}) => {
  const [hi, mid, lo] = BALLS[tone] ?? BALLS.white;
  const face = (tf: string, bg: string) => <div style={{position: 'absolute', left: -s / 2, top: -s / 2, width: s, height: s, borderRadius: s * 0.14, background: bg, transform: `${tf} translateZ(${s / 2}px)`, backfaceVisibility: 'hidden'}} />;
  return (
    <div style={{position: 'relative', width: 0, height: 0, transformStyle: 'preserve-3d'}}>
      {face('', mid)}{face('rotateY(180deg)', lo)}{face('rotateY(90deg)', lo)}{face('rotateY(-90deg)', hi)}{face('rotateX(90deg)', hi)}{face('rotateX(-90deg)', lo)}
    </div>
  );
};
export const Ring: React.FC<{size: number; tone: keyof typeof BALLS | string; thick?: number}> = ({size, tone, thick = 0.16}) => {
  const [hi, mid, lo] = BALLS[tone] ?? BALLS.white;
  const b = size * thick;
  return <div style={{width: size, height: size, borderRadius: '50%', boxSizing: 'border-box', border: `${b}px solid ${mid}`, boxShadow: `inset 0 ${b * 0.3}px ${b * 0.5}px ${hi}, inset 0 -${b * 0.3}px ${b * 0.5}px ${lo}, 0 ${b * 0.4}px ${b}px rgba(46,30,16,.22)`}} />;
};
