import {staticFile} from 'remotion';

export const FPS = 30;
export const W = 1080;
export const H = 1920;

export const C = {
  bg: '#04050B',
  navy: '#0B1020',
  gold: '#F2A93B',
  goldHi: '#FFD27A',
  white: '#FFFFFF',
  ink: '#0A0B12',
  // light info cards
  text: '#0A0B12',
  muted: 'rgba(10,11,18,0.58)',
  accent: '#D98A14',
  line: 'rgba(10,11,18,0.09)',
};

export const FONT = 'MontserratLocal';

export const fontCss = `
@font-face{font-family:${FONT};src:url(${staticFile('montserrat-500.ttf')});font-weight:500;}
@font-face{font-family:${FONT};src:url(${staticFile('montserrat-600.ttf')});font-weight:600;}
@font-face{font-family:${FONT};src:url(${staticFile('montserrat-700.ttf')});font-weight:700;}
@font-face{font-family:${FONT};src:url(${staticFile('montserrat-800.ttf')});font-weight:800;}
`;

export const clamp01 = (v: number) => Math.min(1, Math.max(0, v));
// easeOutExpo / easeInOutCubic on 0..1
export const outExpo = (t: number) => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * clamp01(t)));
export const inOutCubic = (t: number) => {
  const x = clamp01(t);
  return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
};
export const outBack = (t: number) => {
  const x = clamp01(t);
  const c1 = 1.4;
  const c3 = c1 + 1;
  return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2);
};
// progress of frame f through window [a, a+d]
export const prog = (f: number, a: number, d: number) => clamp01((f - a) / d);
