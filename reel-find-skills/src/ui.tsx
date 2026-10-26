import React from 'react';
import {spring, random} from 'remotion';
import {loadFont as loadBricolage} from '@remotion/google-fonts/BricolageGrotesque';
import {loadFont as loadSerif} from '@remotion/google-fonts/InstrumentSerif';
import {loadFont as loadMono} from '@remotion/google-fonts/JetBrainsMono';
import {FPS} from './timing';

export const FONT = {
  display: loadBricolage('normal', {weights: ['500', '800'], subsets: ['latin']}).fontFamily,
  serif: loadSerif('italic', {weights: ['400'], subsets: ['latin']}).fontFamily,
  mono: loadMono('normal', {weights: ['500', '700'], subsets: ['latin']}).fontFamily,
};

// 60 / 30 / 10: near-black stage, warm cream type, Claude-orange accent
export const C = {
  bg0: '#09080C', bg1: '#15121A', cream: '#F4EEE6', muted: '#8E8698', line: 'rgba(255,255,255,.12)',
  orange: '#F07A48', orangeHi: '#FFB38A', yellow: '#FFD23F', green: '#4ADE80', red: '#F05252', blue: '#6E8BFF',
};

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
export const rnd = (k: string | number) => random(`fs-${k}`);
// enter/exit envelope for an element living between a and b
export const life = (t: number, a: number, b = 1e9, inD = 0.45, outD = 0.25) => outExpo(prog(t, a, inD)) * (1 - inCubic(prog(t, b, outD)));

// ---------- 3D object: places children (centered) at a world point ----------
export const O: React.FC<{x?: number; y?: number; z?: number; rx?: number; ry?: number; rz?: number; s?: number; o?: number; anchor?: string; children?: React.ReactNode; style?: React.CSSProperties}> = ({x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0, s = 1, o = 1, anchor = 'translate(-50%,-50%)', children, style}) => {
  if (o <= 0.001) return null;
  return (
    <div style={{position: 'absolute', left: 0, top: 0, transformStyle: 'preserve-3d', transform: `translate3d(${x}px,${y}px,${z}px) rotateY(${ry}deg) rotateX(${rx}deg) rotateZ(${rz}deg) scale(${s})`}}>
      <div style={{position: 'absolute', left: 0, top: 0, transform: anchor, opacity: o, transformStyle: 'preserve-3d', ...style}}>{children}</div>
    </div>
  );
};

// ---------- dark glass panel ----------
export const Panel: React.FC<{w: number; h: number; accent?: number; glow?: string; radius?: number; style?: React.CSSProperties; children?: React.ReactNode}> = ({w, h, accent = 0, glow = C.orange, radius = 26, style, children}) => (
  <div style={{width: w, height: h, borderRadius: radius, position: 'relative', overflow: 'hidden', boxSizing: 'border-box',
    background: 'linear-gradient(180deg, rgba(40,35,48,.94), rgba(20,18,26,.94))',
    border: `2px solid ${accent > 0 ? `rgba(240,122,72,${0.25 + 0.75 * accent})` : C.line}`,
    boxShadow: `0 40px 90px rgba(0,0,0,.6), inset 0 1px 0 rgba(255,255,255,.09)${accent > 0 ? `, 0 0 ${60 * accent}px ${glow}55` : ''}`, ...style}}>{children}</div>
);

export const Mono: React.FC<{size?: number; color?: string; w?: number; children: React.ReactNode; style?: React.CSSProperties}> = ({size = 26, color = C.muted, w = 500, children, style}) => (
  <div style={{fontFamily: FONT.mono, fontWeight: w, fontSize: size, color, letterSpacing: '.02em', whiteSpace: 'nowrap', lineHeight: 1.2, ...style}}>{children}</div>
);

// big display type with a short dark extrusion (reads as a 3D slab under camera moves)
export const Big: React.FC<{size: number; color?: string; serif?: boolean; depth?: number; glow?: string; children: React.ReactNode; style?: React.CSSProperties}> = ({size, color = C.cream, serif, depth = 10, glow, children, style}) => {
  const ext = Array.from({length: depth}, (_, i) => `${i * 0.6}px ${i + 1}px 0 ${i < depth - 1 ? '#2A2430' : '#0d0b10'}`);
  if (glow) ext.push(`0 0 ${size * 0.35}px ${glow}`);
  return (
    <div style={{fontFamily: serif ? FONT.serif : FONT.display, fontStyle: serif ? 'italic' : 'normal', fontWeight: serif ? 400 : 800, fontSize: size, lineHeight: 0.95, letterSpacing: serif ? '-0.01em' : '-0.045em',
      color, whiteSpace: 'nowrap', textShadow: ext.join(','), ...style}}>{children}</div>
  );
};

export const Check: React.FC<{size?: number; color?: string}> = ({size = 44, color = C.green}) => (
  <div style={{width: size, height: size, borderRadius: '50%', background: color, display: 'grid', placeItems: 'center', flex: 'none'}}>
    <svg width={size * 0.55} height={size * 0.55} viewBox="0 0 34 34"><path d="M5,18 L14,27 L30,7" fill="none" stroke="#0B0A0F" strokeWidth={5} strokeLinecap="round" strokeLinejoin="round" /></svg>
  </div>
);

export const Cursor: React.FC<{size?: number}> = ({size = 70}) => (
  <svg width={size} height={size} viewBox="0 0 60 60" style={{overflow: 'visible', display: 'block', filter: 'drop-shadow(0 6px 10px rgba(0,0,0,.6))'}}>
    <path d="M6,4 L50,30 L30,34 L40,54 L32,58 L22,38 L8,50 Z" fill="#fff" stroke="#0B0A0F" strokeWidth={3.5} strokeLinejoin="round" />
  </svg>
);

export const ZipIcon: React.FC<{size?: number}> = ({size = 120}) => (
  <svg width={size} height={size * 1.25} viewBox="0 0 96 120" style={{display: 'block'}}>
    <path d="M8,4 L64,4 L90,30 L90,116 L8,116 Z" fill={C.orange} />
    <path d="M64,4 L64,30 L90,30" fill="#C85A2E" />
    {Array.from({length: 6}, (_, i) => <rect key={i} x={i % 2 ? 40 : 32} y={10 + i * 11} width={12} height={8} rx={2} fill="#0B0A0F" />)}
    <rect x={30} y={78} width={24} height={20} rx={5} fill="none" stroke="#0B0A0F" strokeWidth={4} />
  </svg>
);
