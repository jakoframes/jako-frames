import React from 'react';
import {useCurrentFrame} from 'remotion';
import {C, FONT, FPS, clamp01, outBack, outExpo} from './theme';

// seconds on the footage timeline (component lives inside the footage <Sequence>)
export const useT = () => useCurrentFrame() / FPS;
export const p = (t: number, a: number, d = 0.45) => clamp01((t - a) / d);

export const Glass: React.FC<{
  top: number;
  height?: number;
  from: number;
  to: number;
  children: React.ReactNode;
}> = ({top, height, from, to, children}) => {
  const t = useT();
  const enter = outExpo(p(t, from, 0.55));
  const exit = outExpo(p(t, to - 0.3, 0.3));
  if (t < from || t > to) return null;
  return (
    <div
      style={{
        position: 'absolute',
        left: 70,
        right: 70,
        top,
        height,
        padding: '34px 40px',
        borderRadius: 34,
        background: 'linear-gradient(160deg, rgba(255,255,255,0.97), rgba(246,244,239,0.95))',
        border: '1.5px solid rgba(255,255,255,0.9)',
        boxShadow: '0 30px 80px rgba(0,0,0,0.35), 0 4px 14px rgba(0,0,0,0.12)',
        backdropFilter: 'blur(22px)',
        fontFamily: FONT,
        color: C.text,
        opacity: enter * (1 - exit),
        transform: `translateY(${(1 - enter) * 70 - exit * 30}px) scale(${0.96 + 0.04 * enter})`,
        overflow: 'hidden',
      }}
    >
      {/* gold edge highlight */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          height: 3,
          width: `${enter * 100}%`,
          background: `linear-gradient(90deg, ${C.gold}, rgba(242,169,59,0))`,
        }}
      />
      {children}
    </div>
  );
};

export const Kicker: React.FC<{children: React.ReactNode; at?: number}> = ({children, at = 0}) => {
  const t = useT();
  const k = outExpo(p(t, at, 0.5));
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 14,
        fontSize: 26,
        fontWeight: 700,
        letterSpacing: 4,
        color: C.accent,
        opacity: k,
        transform: `translateX(${(1 - k) * -20}px)`,
      }}
    >
      <div style={{width: 10, height: 10, borderRadius: 5, background: C.accent}} />
      {children}
    </div>
  );
};

// big program name with a letter-by-letter rise
export const Headline: React.FC<{text: string; at: number; size?: number; color?: string}> = ({
  text,
  at,
  size = 92,
  color = C.text,
}) => {
  const t = useT();
  return (
    <div style={{display: 'flex', fontSize: size, fontWeight: 800, letterSpacing: -1, lineHeight: 1.05, color}}>
      {[...text].map((ch, i) => {
        const k = outExpo(p(t, at + 0.15 + i * 0.03, 0.45));
        return (
          <span
            key={i}
            style={{
              display: 'inline-block',
              whiteSpace: 'pre',
              opacity: k,
              transform: `translateY(${(1 - k) * 40}px)`,
              clipPath: 'inset(-20% -10% -20% -10%)',
            }}
          >
            {ch}
          </span>
        );
      })}
    </div>
  );
};

// counts up to `to` from cue time
export const Count: React.FC<{to: number; at: number; dur?: number; fmt?: (n: number) => string}> = ({
  to,
  at,
  dur = 0.8,
  fmt = (n) => String(Math.round(n)),
}) => {
  const t = useT();
  return <>{fmt(to * outExpo(p(t, at, dur)))}</>;
};

export const Stat: React.FC<{
  at: number;
  value: React.ReactNode;
  label: string;
  accent?: string;
  size?: number;
}> = ({at, value, label, accent = C.accent, size = 96}) => {
  const t = useT();
  const k = outBack(p(t, at, 0.5));
  const o = clamp01(p(t, at, 0.2));
  return (
    <div style={{opacity: o, transform: `translateY(${(1 - k) * 30}px) scale(${0.85 + 0.15 * k})`, transformOrigin: 'left bottom'}}>
      <div style={{fontSize: size, fontWeight: 800, color: accent, letterSpacing: -2, lineHeight: 1}}>{value}</div>
      <div style={{fontSize: 27, fontWeight: 600, color: C.muted, marginTop: 10}}>{label}</div>
    </div>
  );
};

export const Check: React.FC<{at: number; children: React.ReactNode}> = ({at, children}) => {
  const t = useT();
  const k = outExpo(p(t, at, 0.5));
  const draw = outExpo(p(t, at + 0.12, 0.45));
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 22,
        fontSize: 36,
        fontWeight: 700,
        opacity: k,
        transform: `translateX(${(1 - k) * 40}px)`,
      }}
    >
      <svg width={52} height={52} viewBox="0 0 52 52" style={{flex: 'none'}}>
        <circle cx={26} cy={26} r={24} fill="rgba(242,169,59,0.16)" stroke={C.accent} strokeWidth={2} />
        <path
          d="M15 27 L23 34 L37 19"
          fill="none"
          stroke={C.accent}
          strokeWidth={4.5}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray={34}
          strokeDashoffset={34 * (1 - draw)}
        />
      </svg>
      {children}
    </div>
  );
};

// horizontal bar that fills to `frac`
export const Bar: React.FC<{at: number; frac: number; height?: number; color?: string; marker?: number}> = ({
  at,
  frac,
  height = 16,
  color = C.accent,
  marker,
}) => {
  const t = useT();
  const k = outExpo(p(t, at, 0.9));
  return (
    <div style={{position: 'relative', height, borderRadius: height, background: C.line, overflow: 'visible'}}>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          width: `${frac * k * 100}%`,
          borderRadius: height,
          background: `linear-gradient(90deg, ${color}, ${C.gold})`,
          boxShadow: `0 4px 14px rgba(217,138,20,0.35)`,
        }}
      />
      {marker !== undefined && (
        <div
          style={{
            position: 'absolute',
            left: `${marker * 100}%`,
            top: -10,
            bottom: -10,
            width: 3,
            background: C.text,
            borderRadius: 2,
          }}
        />
      )}
    </div>
  );
};

export const Divider: React.FC<{at: number}> = ({at}) => {
  const t = useT();
  return (
    <div
      style={{
        height: 1.5,
        width: `${outExpo(p(t, at, 0.6)) * 100}%`,
        background: 'linear-gradient(90deg, rgba(10,11,18,0.16), rgba(10,11,18,0))',
        margin: '26px 0',
      }}
    />
  );
};

export const HouseIcon: React.FC<{at: number; size?: number}> = ({at, size = 110}) => {
  const t = useT();
  const d = outExpo(p(t, at, 0.9));
  const L = 300;
  return (
    <svg width={size} height={size} viewBox="0 0 100 100">
      <path
        d="M14 48 L50 18 L86 48 M24 40 V84 H76 V40 M42 84 V60 H58 V84"
        fill="none"
        stroke={C.accent}
        strokeWidth={5}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={L}
        strokeDashoffset={L * (1 - d)}
      />
    </svg>
  );
};

export const Pin: React.FC<{size?: number}> = ({size = 40}) => (
  <svg width={size} height={size} viewBox="0 0 40 40" style={{flex: 'none'}}>
    <path d="M20 37 C20 37 7 23 7 15 A13 13 0 0 1 33 15 C33 23 20 37 20 37 Z" fill={C.accent} />
    <circle cx={20} cy={15} r={5} fill="#FFFFFF" />
  </svg>
);
