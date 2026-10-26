import React from 'react';
import {AbsoluteFill, Easing, interpolate, random, spring, useCurrentFrame} from 'remotion';
import {loadFont as loadAnton} from '@remotion/google-fonts/Anton';
import {loadFont as loadInter} from '@remotion/google-fonts/Inter';
import {loadFont as loadMono} from '@remotion/google-fonts/JetBrainsMono';
import {loadFont as loadSerif} from '@remotion/google-fonts/SourceSerif4';

const ANTON = loadAnton('normal', {weights: ['400'], subsets: ['latin']}).fontFamily;
const INTER = loadInter('normal', {weights: ['400', '500', '600', '700', '800'], subsets: ['latin']}).fontFamily;
const MONO = loadMono('normal', {weights: ['400', '700'], subsets: ['latin']}).fontFamily;
const SERIF = loadSerif('normal', {weights: ['400', '500'], subsets: ['latin']}).fontFamily;

export const FPS = 30;
export const DURATION_S = 44.6;

// All times below are in seconds and come from word timestamps of the voiceover.
const f = (s: number) => Math.round(s * FPS);

const C = {
  bg: '#09090B',
  fg: '#F5F5F0',
  y: '#FFE135',
  pink: '#FF3D6E',
  claude: '#D97757',
  dim: '#8A8A93',
  money: '#5CFF8A',
};

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

type SpringCfg = {damping?: number; stiffness?: number; mass?: number};
const sp = (frame: number, at: number, cfg: SpringCfg = {}) =>
  spring({frame: frame - f(at), fps: FPS, config: {damping: 13, stiffness: 200, mass: 0.6, ...cfg}});

// ---------- building blocks ----------

type WordProps = {
  at: number;
  children: React.ReactNode;
  color?: string;
  size?: number;
  font?: string;
  bg?: string;
  strike?: number;
  glow?: boolean;
  stretch?: boolean;
  style?: React.CSSProperties;
};

const Word: React.FC<WordProps> = ({at, children, color = C.fg, size, font = ANTON, bg, strike, glow, stretch, style}) => {
  const frame = useCurrentFrame();
  const p = sp(frame, at, {damping: 10, stiffness: 260, mass: 0.5});
  const visible = frame >= f(at);
  const scale = interpolate(p, [0, 1], [stretch ? 2.4 : 1.7, 1]);
  const sx = stretch ? interpolate(p, [0, 1], [1.8, 1]) : 1;
  const blur = interpolate(p, [0, 1], [14, 0], clamp);
  const struck = strike !== undefined && frame >= f(strike);
  const strikeP = strike !== undefined ? interpolate(frame, [f(strike), f(strike) + 6], [0, 1], clamp) : 0;
  const glitch = struck && frame < f(strike!) + 8 ? `${8 * Math.sin(frame * 3)}px 0 ${C.pink}, ${-8 * Math.sin(frame * 3)}px 0 #35D6FF` : undefined;
  return (
    <span
      style={{
        display: 'inline-block',
        position: 'relative',
        opacity: visible ? Math.min(1, p * 2.5) : 0,
        transform: `scale(${scale}) scaleX(${sx})`,
        filter: blur > 0.2 ? `blur(${blur}px)` : undefined,
        color: struck ? '#6E6E76' : color,
        fontFamily: font,
        fontSize: size,
        padding: bg ? '0 0.14em' : undefined,
        background: bg,
        borderRadius: bg ? '0.08em' : undefined,
        margin: '0 0.09em',
        textShadow: glitch ?? (glow ? `0 0 50px ${color}99, 0 0 12px ${color}66` : undefined),
        ...style,
      }}
    >
      {children}
      {strike !== undefined && (
        <span
          style={{
            position: 'absolute',
            left: '-4%',
            top: '50%',
            height: '0.11em',
            width: `${strikeP * 108}%`,
            background: C.pink,
            boxShadow: `0 0 30px ${C.pink}`,
          }}
        />
      )}
    </span>
  );
};

const Scene: React.FC<{from: number; to: number; children: React.ReactNode}> = ({from, to, children}) => {
  const frame = useCurrentFrame();
  if (frame < f(from) || frame >= f(to)) return null;
  const pin = interpolate(frame, [f(from), f(from) + 5], [0, 1], clamp);
  const pout = interpolate(frame, [f(to) - 4, f(to)], [0, 1], clamp);
  const scale = interpolate(pin, [0, 1], [1.12, 1]) * interpolate(pout, [0, 1], [1, 0.9]);
  const push = interpolate(frame, [f(from), f(to)], [1, 1.05]);
  return (
    <AbsoluteFill
      style={{
        opacity: pin * (1 - pout),
        transform: `scale(${scale * push})`,
        filter: pout > 0.05 ? `blur(${pout * 10}px)` : undefined,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

const Col: React.FC<{children: React.ReactNode; top?: number; gap?: number}> = ({children, top, gap = 0}) => (
  <AbsoluteFill
    style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: top === undefined ? 'center' : 'flex-start',
      paddingTop: top,
      textAlign: 'center',
      gap,
      color: C.fg,
    }}
  >
    {children}
  </AbsoluteFill>
);

const Line: React.FC<{size: number; font?: string; children: React.ReactNode; style?: React.CSSProperties}> = ({size, font = ANTON, children, style}) => (
  <div style={{fontFamily: font, fontSize: size, lineHeight: 1, whiteSpace: 'nowrap', ...style}}>{children}</div>
);

const Spark: React.FC<{size: number; color?: string; rot?: number}> = ({size, color = C.claude, rot = 0}) => (
  <svg width={size} height={size} viewBox="-50 -50 100 100" style={{transform: `rotate(${rot}deg)`, overflow: 'visible'}}>
    {Array.from({length: 12}, (_, i) => {
      const len = [44, 34, 40, 30][i % 4];
      return <rect key={i} x={-4.5} y={-len} width={9} height={len} rx={4.5} fill={color} transform={`rotate(${i * 30 + (i % 3) * 4})`} />;
    })}
  </svg>
);

const SHAPES = [
  [[0, 0], [100, 0], [100, 100], [0, 100]],
  [[50, 0], [100, 50], [50, 100], [0, 50]],
  [[50, 0], [50, 0], [100, 100], [0, 100]],
];

const Morph: React.FC<{size: number; t: number; color: string}> = ({size, t, color}) => {
  const seg = ((t % SHAPES.length) + SHAPES.length) % SHAPES.length;
  const i = Math.floor(seg);
  const k = Easing.inOut(Easing.cubic)(seg - i);
  const a = SHAPES[i];
  const b = SHAPES[(i + 1) % SHAPES.length];
  const poly = a.map((p, j) => `${p[0] + (b[j][0] - p[0]) * k}% ${p[1] + (b[j][1] - p[1]) * k}%`).join(',');
  return (
    <div style={{filter: `drop-shadow(0 0 22px ${color})`}}>
      <div style={{width: size, height: size, background: color, clipPath: `polygon(${poly})`}} />
    </div>
  );
};

// ---------- global layers ----------

const Background: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{background: C.bg}}>
      <AbsoluteFill
        style={{
          backgroundImage: 'linear-gradient(#ffffff0b 1px, transparent 1px), linear-gradient(90deg, #ffffff0b 1px, transparent 1px)',
          backgroundSize: '90px 90px',
          backgroundPosition: `0 ${(frame * 0.8) % 90}px`,
        }}
      />
      <AbsoluteFill style={{background: `radial-gradient(circle at 50% ${45 + Math.sin(frame / 40) * 6}%, rgba(255,225,53,0.10), transparent 55%)`}} />
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, transparent 45%, rgba(0,0,0,0.8) 100%)'}} />
    </AbsoluteFill>
  );
};

const IMPACTS = [0.76, 2.6, 7.3, 8.75, 9.74, 24.08, 28.0, 29.24, 31.56, 36.26, 39.12, 40.28, 41.34];
export const CUTS = [1.6, 4.25, 7.75, 9.2, 11.0, 23.3, 25.4, 28.45, 30.4, 32.3, 33.3, 34.25, 35.2, 36.2, 37.8, 39.65, 40.9];

const shake = (frame: number) => {
  let x = 0;
  let y = 0;
  let r = 0;
  for (const s of IMPACTS) {
    const d = frame - f(s);
    if (d >= 0 && d < 12) {
      const a = (1 - d / 12) ** 2;
      x += Math.sin(d * 2.3) * 20 * a;
      y += Math.cos(d * 3.1) * 16 * a;
      r += Math.sin(d * 1.7) * 0.9 * a;
    }
  }
  return {x, y, r};
};

// A glowing comet that whips across the frame on every cut.
const Comet: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      {CUTS.map((cut, i) => {
        const d = frame - (f(cut) - 5);
        if (d < 0 || d >= 11) return null;
        const p = Easing.inOut(Easing.cubic)(d / 10);
        const flip = i % 2 === 0;
        const x = interpolate(p, [0, 1], flip ? [-300, 1380] : [1380, -300]);
        const y = interpolate(p, [0, 1], [1450, 450]);
        const ang = flip ? -31 : 211;
        const flash = Math.max(0, 1 - Math.abs(d - 5) / 4) * 0.18;
        return (
          <React.Fragment key={cut}>
            <AbsoluteFill style={{background: `rgba(255,240,180,${flash})`}} />
            <div style={{position: 'absolute', left: x, top: y, transform: `rotate(${ang}deg)`, transformOrigin: '0 50%'}}>
              <div
                style={{
                  position: 'absolute',
                  right: 0,
                  top: -6,
                  width: 520,
                  height: 12,
                  borderRadius: 6,
                  background: `linear-gradient(90deg, transparent, ${C.y})`,
                  filter: 'blur(1px)',
                  boxShadow: `0 0 30px ${C.y}`,
                }}
              />
              <div style={{position: 'absolute', left: -20, top: -20, width: 40, height: 40, borderRadius: 20, background: '#FFFBE0', boxShadow: `0 0 40px 14px ${C.y}`}} />
            </div>
          </React.Fragment>
        );
      })}
    </AbsoluteFill>
  );
};

// ---------- scenes ----------

const S1Heck: React.FC = () => (
  <Scene from={0} to={1.6}>
    <Col>
      <Line size={250}>
        <Word at={0}>WHAT</Word>
      </Line>
      <Line size={250}>
        <Word at={0.44}>THE</Word>
      </Line>
      <Line size={230}>
        <Word at={0.76} color={C.y} glow stretch>
          HEEECK?!
        </Word>
      </Line>
    </Col>
  </Scene>
);

const Globe: React.FC<{size: number}> = ({size}) => {
  const frame = useCurrentFrame();
  const r = size / 2;
  return (
    <svg width={size} height={size} viewBox={`${-r - 4} ${-r - 4} ${size + 8} ${size + 8}`}>
      <g fill="none" stroke={C.y} strokeWidth={3}>
        <circle r={r} />
        {Array.from({length: 6}, (_, i) => (
          <ellipse key={i} rx={Math.abs(Math.cos(frame / 18 + (i * Math.PI) / 6)) * r} ry={r} />
        ))}
        {[-0.66, -0.33, 0, 0.33, 0.66].map((k) => {
          const yy = k * r;
          const rr = Math.sqrt(r * r - yy * yy);
          return <ellipse key={k} cy={yy} rx={rr} ry={rr * 0.16} />;
        })}
      </g>
    </svg>
  );
};

const S2Ready: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <Scene from={1.6} to={4.25}>
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', opacity: 0.35}}>
        <div style={{transform: `scale(${interpolate(frame, [f(1.6), f(4.25)], [0.85, 1.15])})`}}>
          <Globe size={860} />
        </div>
      </AbsoluteFill>
      <Col>
        <Line size={150}>
          <Word at={1.64}>THE</Word>
          <Word at={2.06}>WORLD</Word>
        </Line>
        <Line size={150} style={{marginTop: 16}}>
          <Word at={2.3}>WAS</Word>
          <Word at={2.6} bg={C.pink}>
            NOT
          </Word>
        </Line>
        <Line size={310} style={{lineHeight: 1.05}}>
          <Word at={3.04} color={C.y} glow>
            READY
          </Word>
        </Line>
        <Line size={64} font={INTER} style={{fontWeight: 800, letterSpacing: 8}}>
          <Word at={3.32} font={INTER}>
            FOR
          </Word>
          <Word at={3.56} font={INTER}>
            THIS.
          </Word>
        </Line>
      </Col>
    </Scene>
  );
};

const Timeline: React.FC<{at: number; crossAt: number}> = ({at, crossAt}) => {
  const frame = useCurrentFrame();
  const p = sp(frame, at, {damping: 15});
  const layers = ['Camera 3D', 'Glow', 'Morph Shape', 'Title Text', 'Null Control'];
  const keys = [
    [0.12, 0.4, 0.7],
    [0.2, 0.55, 0.85],
    [0.1, 0.3, 0.5, 0.75],
    [0.25, 0.45, 0.9],
    [0.15, 0.6, 0.8],
  ];
  const play = interpolate(frame, [f(at), f(crossAt)], [0.05, 0.8], clamp);
  const cross = interpolate(frame, [f(crossAt), f(crossAt) + 6], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  const W = 940;
  const NAME = 270;
  return (
    <div style={{perspective: 1400}}>
      <div
        style={{
          width: W,
          height: 560,
          background: '#141418',
          border: '2px solid #2A2A31',
          borderRadius: 26,
          position: 'relative',
          overflow: 'hidden',
          fontFamily: INTER,
          opacity: Math.min(1, p * 2),
          transform: `translateY(${(1 - p) * 420}px) rotateX(${(1 - p) * 35}deg)`,
          boxShadow: '0 30px 90px rgba(0,0,0,0.6)',
        }}
      >
        <div style={{height: 76, background: '#1C1C23', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 30px', fontSize: 28}}>
          <span style={{color: C.fg, fontWeight: 700}}>Timeline · Comp 1</span>
          <span style={{color: C.y, fontFamily: MONO}}>0:00:{String(Math.floor(play * 15)).padStart(2, '0')}:{String(frame % 30).padStart(2, '0')}</span>
        </div>
        {layers.map((name, row) => (
          <div key={name} style={{height: 96, borderBottom: '1px solid #24242B', display: 'flex', alignItems: 'center', position: 'relative'}}>
            <div style={{width: NAME, paddingLeft: 30, color: '#C9C9D1', fontSize: 27, fontWeight: 500}}>{name}</div>
            <div style={{position: 'absolute', left: NAME, right: 20, height: 34, borderRadius: 8, background: '#262630'}} />
            {keys[row].map((kx, k) => {
              const kp = sp(frame, at + 0.15 + (row * 3 + k) * 0.035, {damping: 9, stiffness: 300});
              return (
                <div
                  key={k}
                  style={{
                    position: 'absolute',
                    left: NAME + kx * (W - NAME - 40),
                    width: 26,
                    height: 26,
                    background: C.y,
                    transform: `rotate(45deg) scale(${kp})`,
                    boxShadow: `0 0 18px ${C.y}`,
                  }}
                />
              );
            })}
          </div>
        ))}
        <div style={{position: 'absolute', top: 76, bottom: 0, left: NAME + play * (W - NAME - 40), width: 4, background: C.pink, boxShadow: `0 0 16px ${C.pink}`}} />
        {cross > 0 &&
          [45, -45].map((a) => (
            <div
              key={a}
              style={{
                position: 'absolute',
                left: '50%',
                top: '50%',
                width: 1100 * cross,
                height: 22,
                borderRadius: 11,
                background: C.pink,
                boxShadow: `0 0 40px ${C.pink}`,
                transform: `translate(-50%, -50%) rotate(${a}deg)`,
              }}
            />
          ))}
      </div>
    </div>
  );
};

const S3AfterEffects: React.FC = () => (
  <Scene from={4.25} to={7.75}>
    <Col top={170}>
      <Line size={96}>
        <Word at={4.3}>I</Word>
        <Word at={4.4}>MADE</Word>
        <Word at={4.56}>THIS</Word>
      </Line>
      <Line size={150} style={{marginTop: 14}}>
        <Word at={4.78} color={C.y} glow>
          MOTION
        </Word>
        <Word at={5.06} color={C.y} glow>
          GRAPHIC
        </Word>
      </Line>
      <Line size={190} style={{marginTop: 14, marginBottom: 40}}>
        <Word at={5.46} bg={C.pink}>
          WITHOUT
        </Word>
      </Line>
      <Timeline at={6.1} crossAt={7.3} />
      <Line size={130} style={{marginTop: 40}}>
        <Word at={6.64}>AFTER</Word>
        <Word at={6.96} strike={7.3}>
          EFFECTS
        </Word>
      </Line>
    </Col>
  </Scene>
);

const S4Higgsfield: React.FC = () => (
  <Scene from={7.75} to={9.2}>
    <Col>
      <Line size={90} font={INTER} style={{fontWeight: 800, letterSpacing: 10}}>
        <Word at={7.82} font={INTER}>
          NOT
        </Word>
        <Word at={7.96} font={INTER}>
          EVEN
        </Word>
      </Line>
      <Line size={200} style={{marginTop: 20}}>
        <Word at={8.24} strike={8.75}>
          HIGGSFIELD
        </Word>
      </Line>
    </Col>
  </Scene>
);

const S5Claude: React.FC = () => {
  const frame = useCurrentFrame();
  const p = sp(frame, 9.62, {damping: 9, stiffness: 160});
  return (
    <Scene from={9.2} to={11.0}>
      <Col gap={30}>
        <Line size={140}>
          <Word at={9.34}>ONLY...</Word>
        </Line>
        <div style={{transform: `scale(${p})`, filter: `drop-shadow(0 0 50px ${C.claude})`}}>
          <Spark size={280} rot={frame * 1.5} />
        </div>
        <Line size={250}>
          <Word at={9.74} color={C.claude} glow>
            CLAUDE.
          </Word>
        </Line>
      </Col>
    </Scene>
  );
};

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
export const PROMPT_TIMES = PROMPT.map((t) => t.at);
const SEND_AT = 22.8;

const TypedPrompt: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  let last = -1;
  const spans = PROMPT.map((tok, i) => {
    if (t < tok.at) return null;
    const next = PROMPT[i + 1]?.at ?? tok.at + 0.3;
    const dur = Math.max(0.05, Math.min(0.22, next - tok.at));
    const n = Math.ceil(tok.w.length * Math.min(1, (t - tok.at) / dur));
    last = i;
    const done = t >= tok.at + dur;
    const mark = tok.hl ? interpolate(t, [tok.at + dur, tok.at + dur + 0.18], [0, 100], clamp) : 0;
    return (
      <React.Fragment key={i}>
        <span
          style={{
            background: tok.hl ? `linear-gradient(90deg, ${C.y} ${mark}%, transparent ${mark}%)` : undefined,
            fontWeight: tok.hl && done ? 700 : 400,
            borderRadius: 6,
            padding: tok.hl ? '0 4px' : undefined,
            boxDecorationBreak: 'clone',
          }}
        >
          {tok.w.slice(0, n)}
        </span>{' '}
      </React.Fragment>
    );
  });
  const caretOn = Math.floor(frame / 8) % 2 === 0 || (last >= 0 && t < PROMPT[last].at + 0.3);
  return (
    <div style={{fontFamily: INTER, fontSize: 46, lineHeight: 1.5, color: '#1F1E1D', minHeight: 300, textAlign: 'left'}}>
      {last < 0 && <span style={{color: '#A3A099'}}>How can I help you today?</span>}
      {spans}
      {t < SEND_AT && <span style={{display: 'inline-block', width: 4, height: 52, background: C.claude, verticalAlign: 'middle', opacity: caretOn ? 1 : 0}} />}
    </div>
  );
};

const ClaudeChat: React.FC = () => {
  const frame = useCurrentFrame();
  const p = sp(frame, 12.08, {damping: 15, stiffness: 150});
  const zoom = interpolate(frame, [f(14), f(22.6)], [1, 1.07], {...clamp, easing: Easing.inOut(Easing.quad)});
  const send = interpolate(frame, [f(SEND_AT), f(SEND_AT) + 3, f(SEND_AT) + 7], [1, 0.82, 1], clamp);
  const hasText = frame >= f(PROMPT[0].at);
  return (
    <div
      style={{
        position: 'absolute',
        left: 60,
        top: 470,
        width: 960,
        height: 1010,
        background: '#F5F4EE',
        borderRadius: 44,
        overflow: 'hidden',
        opacity: Math.min(1, p * 2),
        transform: `translateY(${(1 - p) * 700}px) scale(${(0.85 + 0.15 * p) * zoom})`,
        boxShadow: '0 40px 140px rgba(0,0,0,0.7), 0 0 0 2px #ffffff14',
        fontFamily: INTER,
      }}
    >
      <div style={{height: 96, display: 'flex', alignItems: 'center', gap: 16, padding: '0 40px', borderBottom: '1px solid #E6E3D8'}}>
        <Spark size={40} />
        <span style={{fontFamily: SERIF, fontSize: 40, color: '#3D3929'}}>Claude</span>
      </div>
      <div style={{marginTop: 80, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 22}}>
        <Spark size={64} rot={frame * 0.6} />
        <span style={{fontFamily: SERIF, fontSize: 66, color: '#3D3929'}}>Evening, Jako</span>
      </div>
      <div
        style={{
          margin: '60px 40px 0',
          background: '#FFFFFF',
          borderRadius: 34,
          border: `2px solid ${frame >= f(SEND_AT) ? C.claude : '#E8E6DC'}`,
          boxShadow: '0 10px 34px rgba(0,0,0,0.07)',
          padding: '34px 38px 28px',
        }}
      >
        <TypedPrompt />
        <div style={{display: 'flex', alignItems: 'center', marginTop: 18, gap: 18}}>
          <div style={{width: 58, height: 58, borderRadius: 29, border: '2px solid #DDD9CC', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 38, color: '#6B6960'}}>+</div>
          <div style={{flex: 1}} />
          <span style={{fontSize: 30, color: '#6B6960'}}>Opus 5.5 ⌄</span>
          <div
            style={{
              width: 66,
              height: 66,
              borderRadius: 18,
              background: C.claude,
              opacity: hasText ? 1 : 0.45,
              transform: `scale(${send})`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontSize: 38,
              fontWeight: 700,
            }}
          >
            ↑
          </div>
        </div>
      </div>
    </div>
  );
};

const S6Chat: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  return (
    <Scene from={11.0} to={23.3}>
      <Col top={200}>
        {t < 12.08 && (
          <Line size={200} style={{marginTop: 360}}>
            <Word at={11.14} color={C.y} glow>
              HERE&apos;S
            </Word>
            <Word at={11.42} color={C.y} glow>
              HOW.
            </Word>
          </Line>
        )}
        {t >= 12.08 && t < 13.32 && (
          <Line size={130}>
            <Word at={12.08}>I</Word>
            <Word at={12.26}>OPENED</Word>
            <Word at={12.56} color={C.claude} glow>
              CLAUDE
            </Word>
          </Line>
        )}
        {t >= 13.32 && (
          <Line size={130}>
            <Word at={13.32}>AND</Word>
            <Word at={13.32} color={C.y} glow>
              TYPED:
            </Word>
          </Line>
        )}
      </Col>
      {t >= 12.0 && <ClaudeChat />}
    </Scene>
  );
};

const S7DidIt: React.FC = () => {
  const frame = useCurrentFrame();
  const p = sp(frame, 24.08, {damping: 11, stiffness: 140});
  const think = frame < f(24.08);
  const burst = interpolate(frame, [f(24.08), f(24.08) + 10], [1, 2.6], clamp);
  const burstO = interpolate(frame, [f(24.08), f(24.08) + 10], [1, 0], clamp);
  return (
    <Scene from={23.3} to={25.4}>
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
        {[0, 1, 2, 3].map((i) => {
          const a = frame / 14 + (i * Math.PI) / 2;
          return (
            <div key={i} style={{position: 'absolute', transform: `translate(${Math.cos(a) * 400}px, ${Math.sin(a) * 600}px) rotate(${frame * 3}deg)`, opacity: p * 0.9}}>
              <Morph size={90} t={frame / 12 + i} color={i % 2 ? C.y : C.claude} />
            </div>
          );
        })}
      </AbsoluteFill>
      <Col gap={20}>
        <Line size={130}>
          <Word at={23.48}>AND</Word>
          <Word at={23.68} color={C.claude} glow>
            CLAUDE...
          </Word>
        </Line>
        <div style={{height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
          <div style={{opacity: think ? 1 : burstO, transform: `scale(${think ? 1 : burst})`, filter: `drop-shadow(0 0 40px ${C.claude})`}}>
            <Spark size={170} rot={frame * 9} />
          </div>
        </div>
        <div style={{perspective: 1200}}>
          <div style={{transform: `rotateY(${(1 - p) * -75 + Math.sin(frame / 6) * 7}deg) rotateX(${Math.cos(frame / 7) * 6}deg)`}}>
            <Line size={290}>
              <Word at={24.08} color={C.y} glow>
                DID IT!
              </Word>
            </Line>
          </div>
        </div>
      </Col>
    </Scene>
  );
};

const FrameGrid: React.FC<{from: number}> = ({from}) => {
  const frame = useCurrentFrame();
  const cols = 6;
  const rows = 11;
  return (
    <AbsoluteFill style={{display: 'flex', flexWrap: 'wrap', alignContent: 'center', justifyContent: 'center', gap: 14, padding: 30, opacity: 0.32}}>
      {Array.from({length: cols * rows}, (_, i) => {
        const on = frame >= f(from) + i * 0.9;
        const hue = Math.floor(random(i) * 60) + 30;
        return (
          <div
            key={i}
            style={{
              width: 150,
              height: 150,
              borderRadius: 10,
              border: '2px solid #ffffff22',
              background: on ? `linear-gradient(135deg, hsl(${hue},90%,55%), #111)` : 'transparent',
              transform: `scale(${on ? 1 : 0.6})`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

const S8aEveryFrame: React.FC = () => {
  const frame = useCurrentFrame();
  const count = Math.floor(interpolate(frame, [f(26.4), f(28.45)], [1, 2400], clamp));
  return (
    <Scene from={25.4} to={28.45}>
      {frame >= f(26.4) && <FrameGrid from={26.4} />}
      <Col top={220}>
        <Line size={70} font={INTER} style={{fontWeight: 800, letterSpacing: 8}}>
          <Word at={25.52} font={INTER}>
            SEE,
          </Word>
        </Line>
        <Line size={150} style={{marginTop: 24}}>
          <Word at={26.14}>HIGGSFIELD</Word>
        </Line>
        <Line size={150}>
          <Word at={26.4}>GENERATES</Word>
        </Line>
        <div style={{height: 50}} />
        <Line size={230}>
          <Word at={26.88} color={C.y} glow>
            EVERY.
          </Word>
        </Line>
        <Line size={230}>
          <Word at={27.46} color={C.y} glow>
            SINGLE.
          </Word>
        </Line>
        <Line size={230}>
          <Word at={28.0} color={C.y} glow>
            FRAME.
          </Word>
        </Line>
        {frame >= f(26.4) && (
          <div style={{marginTop: 30, fontFamily: MONO, fontSize: 44, color: C.fg, background: '#000000aa', padding: '8px 22px', borderRadius: 12}}>
            FRAME {String(count).padStart(4, '0')}
          </div>
        )}
      </Col>
    </Scene>
  );
};

const S8bExpensive: React.FC = () => {
  const frame = useCurrentFrame();
  const cost = interpolate(frame, [f(29.24), f(30.3)], [0, 1240], clamp);
  const bar = interpolate(frame, [f(28.5), f(30.2)], [1, 0.04], clamp);
  return (
    <Scene from={28.45} to={30.4}>
      <Col>
        <Line size={80} font={INTER} style={{fontWeight: 800, letterSpacing: 6}}>
          <Word at={28.5} font={INTER}>
            AND
          </Word>
          <Word at={28.98} font={INTER}>
            THAT&apos;S
          </Word>
        </Line>
        <Line size={230} style={{marginTop: 20}}>
          <Word at={29.24} color={C.pink} glow>
            EXPENSIVE.
          </Word>
        </Line>
        <div style={{marginTop: 60, width: 760, fontFamily: INTER, textAlign: 'left'}}>
          <div style={{display: 'flex', justifyContent: 'space-between', fontSize: 34, color: C.dim, fontWeight: 600}}>
            <span>CREDITS</span>
            <span style={{color: C.pink, fontFamily: MONO}}>-${cost.toFixed(2)}</span>
          </div>
          <div style={{marginTop: 14, height: 34, borderRadius: 17, background: '#26262C', overflow: 'hidden'}}>
            <div style={{width: `${bar * 100}%`, height: '100%', background: bar < 0.3 ? C.pink : C.y, boxShadow: `0 0 24px ${bar < 0.3 ? C.pink : C.y}`}} />
          </div>
        </div>
      </Col>
    </Scene>
  );
};

const CODE = [
  'const frame = useCurrentFrame();',
  'const glow = spring({ frame, fps });',
  'return (',
  '  <Camera3D rotateY={glow * 25}>',
  '    <Morph from="circle" to="star" />',
  '    <Glow intensity={0.9} />',
  '  </Camera3D>',
  ');',
];

const highlight = (s: string) =>
  s.split(/("[^"]*"?|<\/?[A-Za-z0-9]+|\b(?:const|return)\b|\b\d+(?:\.\d+)?\b)/g).map((part, i) => {
    let color = '#E6E6E6';
    if (/^"/.test(part)) color = C.y;
    else if (/^<\/?[A-Za-z]/.test(part)) color = '#7FD1FF';
    else if (/^(const|return)$/.test(part)) color = C.pink;
    else if (/^\d/.test(part)) color = '#B58CFF';
    return (
      <span key={i} style={{color}}>
        {part}
      </span>
    );
  });

const CodeEditor: React.FC<{from: number; to: number; width?: number; fontSize?: number}> = ({from, to, width = 940, fontSize = 34}) => {
  const frame = useCurrentFrame();
  const total = CODE.join('').length;
  let budget = Math.floor(interpolate(frame, [f(from), f(to)], [0, total], clamp));
  return (
    <div style={{width, background: '#0F0F13', border: '2px solid #2A2A31', borderRadius: 24, overflow: 'hidden', textAlign: 'left', boxShadow: '0 30px 90px rgba(0,0,0,0.6)'}}>
      <div style={{height: 60, background: '#18181E', display: 'flex', alignItems: 'center', gap: 12, padding: '0 24px'}}>
        {['#FF5F57', '#FEBC2E', '#28C840'].map((c) => (
          <div key={c} style={{width: 18, height: 18, borderRadius: 9, background: c}} />
        ))}
        <span style={{marginLeft: 16, fontFamily: MONO, fontSize: 24, color: C.dim}}>Reel.tsx</span>
      </div>
      <div style={{padding: '24px 28px', fontFamily: MONO, fontSize, lineHeight: 1.55, whiteSpace: 'pre'}}>
        {CODE.map((line, i) => {
          const shown = line.slice(0, Math.max(0, budget));
          budget -= line.length;
          return (
            <div key={i} style={{minHeight: fontSize * 1.55}}>
              <span style={{color: '#55555E', marginRight: 22}}>{String(i + 1).padStart(2, ' ')}</span>
              {highlight(shown)}
            </div>
          );
        })}
      </div>
    </div>
  );
};

const S9Code: React.FC = () => (
  <Scene from={30.4} to={32.3}>
    <Col top={170} gap={30}>
      <Line size={170}>
        <Word at={30.62} color={C.claude} glow>
          CLAUDE?
        </Word>
      </Line>
      <CodeEditor from={30.7} to={32.2} />
      <Line size={70} font={INTER} style={{fontWeight: 800, letterSpacing: 4}}>
        <Word at={31.02} font={INTER}>
          IT
        </Word>
        <Word at={31.16} font={INTER}>
          JUST
        </Word>
        <Word at={31.3} font={INTER}>
          WRITES
        </Word>
      </Line>
      <Line size={250}>
        <Word at={31.56} color={C.y} glow>
          CODE.
        </Word>
      </Line>
    </Col>
  </Scene>
);

const FilmFrame: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <svg width={520} height={380} viewBox="0 0 520 380">
      <rect x={10} y={10} width={500} height={360} rx={18} fill="none" stroke={C.y} strokeWidth={8} />
      {Array.from({length: 9}, (_, i) => (
        <React.Fragment key={i}>
          <rect x={40 + i * 52} y={26} width={28} height={22} rx={4} fill={C.y} />
          <rect x={40 + i * 52} y={332} width={28} height={22} rx={4} fill={C.y} />
        </React.Fragment>
      ))}
      <circle cx={130 + ((frame * 12) % 260)} cy={190} r={40} fill={C.fg} />
    </svg>
  );
};

const EffectBurst: React.FC<{at: number}> = ({at}) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [f(at), f(at) + 14], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  return (
    <svg width={520} height={380} viewBox="-260 -190 520 380" style={{overflow: 'visible'}}>
      {Array.from({length: 16}, (_, i) => {
        const a = (i / 16) * Math.PI * 2;
        return <line key={i} x1={Math.cos(a) * 60 * p} y1={Math.sin(a) * 60 * p} x2={Math.cos(a) * 200 * p} y2={Math.sin(a) * 200 * p} stroke={C.y} strokeWidth={8} strokeLinecap="round" />;
      })}
      <circle r={50 + Math.sin(frame / 3) * 6} fill={C.y} style={{filter: `drop-shadow(0 0 40px ${C.y})`}} />
    </svg>
  );
};

const MotionPath: React.FC<{at: number}> = ({at}) => {
  const frame = useCurrentFrame();
  const pt = (u: number) => {
    const x = -220 + 440 * u;
    const y = 120 - 4 * 240 * u * (1 - u);
    return [x, y];
  };
  const u = ((frame - f(at)) / 26) % 1;
  return (
    <svg width={520} height={380} viewBox="-260 -190 520 380">
      <path d="M -220 120 Q 0 -360 220 120" fill="none" stroke="#ffffff44" strokeWidth={5} strokeDasharray="14 14" />
      {[0.12, 0.08, 0.04].map((lag, i) => {
        const [x, y] = pt(Math.max(0, u - lag));
        return <circle key={i} cx={x} cy={y} r={30} fill={C.y} opacity={0.15 + i * 0.15} />;
      })}
      {(() => {
        const [x, y] = pt(Math.max(0, u));
        return <circle cx={x} cy={y} r={34} fill={C.y} style={{filter: `drop-shadow(0 0 30px ${C.y})`}} />;
      })()}
    </svg>
  );
};

const DesignGrid: React.FC<{at: number}> = ({at}) => {
  const frame = useCurrentFrame();
  const s = (k: number) => sp(frame, at + k * 0.08, {damping: 10, stiffness: 240});
  return (
    <svg width={520} height={380} viewBox="0 0 520 380">
      {[1, 2].map((i) => (
        <React.Fragment key={i}>
          <line x1={(520 / 3) * i} y1={0} x2={(520 / 3) * i} y2={380} stroke="#ffffff33" strokeWidth={3} />
          <line x1={0} y1={(380 / 3) * i} x2={520} y2={(380 / 3) * i} stroke="#ffffff33" strokeWidth={3} />
        </React.Fragment>
      ))}
      <circle cx={87} cy={190} r={60 * s(0)} fill={C.y} />
      <rect x={260 - 60 * s(1)} y={190 - 60 * s(1)} width={120 * s(1)} height={120 * s(1)} rx={10} fill={C.fg} />
      <polygon points="433,120 493,250 373,250" fill={C.pink} transform={`translate(433 190) scale(${s(2)}) translate(-433 -190)`} />
    </svg>
  );
};

const EVERY: {from: number; to: number; every: number; at: number; word: string; vis: (at: number) => React.ReactNode}[] = [
  {from: 32.3, to: 33.3, every: 32.4, at: 32.6, word: 'FRAME', vis: () => <FilmFrame />},
  {from: 33.3, to: 34.25, every: 33.34, at: 33.52, word: 'EFFECT', vis: (at) => <EffectBurst at={at} />},
  {from: 34.25, to: 35.2, every: 34.28, at: 34.46, word: 'MOTION', vis: (at) => <MotionPath at={at} />},
  {from: 35.2, to: 36.2, every: 35.26, at: 35.42, word: 'DESIGN', vis: (at) => <DesignGrid at={at} />},
];

const S10Every: React.FC = () => (
  <>
    {EVERY.map((e) => (
      <Scene key={e.word} from={e.from} to={e.to}>
        <Col gap={30}>
          {e.vis(e.at)}
          <Line size={80} font={INTER} style={{fontWeight: 800, letterSpacing: 16}}>
            <Word at={e.every} font={INTER}>
              EVERY
            </Word>
          </Line>
          <Line size={250}>
            <Word at={e.at} color={C.y} glow>
              {e.word}
            </Word>
          </Line>
        </Col>
      </Scene>
    ))}
  </>
);

const CodeRain: React.FC = () => {
  const frame = useCurrentFrame();
  const chars = '{}<>/=;()01constfnreturn';
  return (
    <AbsoluteFill style={{opacity: 0.18, fontFamily: MONO, fontSize: 34, color: C.y}}>
      {Array.from({length: 14}, (_, c) => {
        const speed = 10 + random(`s${c}`) * 14;
        const y = ((frame * speed + random(`o${c}`) * 2000) % 2600) - 700;
        const str = Array.from({length: 18}, (_, k) => chars[Math.floor(random(`${c}-${k}`) * chars.length)]).join('\n');
        return (
          <div key={c} style={{position: 'absolute', left: 20 + c * 77, top: y, whiteSpace: 'pre', lineHeight: 1.2}}>
            {str}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const S11AllCode: React.FC = () => (
  <Scene from={36.2} to={37.8}>
    <CodeRain />
    <Col>
      <Line size={480} style={{lineHeight: 0.95}}>
        <Word at={36.26} color={C.y} glow>
          ALL
        </Word>
      </Line>
      <Line size={140}>
        <Word at={36.54}>MADE</Word>
        <Word at={36.82}>WITH</Word>
      </Line>
      <Line size={220} style={{marginTop: 10}}>
        <Word at={37.04} font={MONO} color={C.claude} size={150}>
          &lt;/&gt;
        </Word>
        <Word at={37.04} color={C.y} glow>
          CODE.
        </Word>
      </Line>
    </Col>
  </Scene>
);

const MoneyRain: React.FC<{from: number}> = ({from}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      {Array.from({length: 18}, (_, i) => {
        const start = f(from) + random(`d${i}`) * 18;
        const d = frame - start;
        if (d < 0) return null;
        const x = random(`x${i}`) * 1000 - 60;
        const y = -260 + d * (38 + random(`v${i}`) * 26);
        const rot = (random(`r${i}`) - 0.5) * 80 + d * (random(`w${i}`) - 0.5) * 14;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: x,
              top: y,
              width: 230,
              height: 110,
              borderRadius: 10,
              background: 'linear-gradient(135deg, #3FA35A, #1E6B35)',
              border: '4px solid #8FE3A4',
              transform: `rotate(${rot}deg) rotateY(${Math.sin(d / 4 + i) * 50}deg)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontFamily: ANTON,
              fontSize: 70,
              color: '#D9FFE2',
              opacity: 0.85,
            }}
          >
            $
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const S12aMoney: React.FC = () => (
  <Scene from={37.8} to={39.65}>
    <MoneyRain from={38.95} />
    <Col>
      <Line size={80} font={INTER} style={{fontWeight: 800, letterSpacing: 6}}>
        <Word at={37.84} font={INTER}>
          SO
        </Word>
        <Word at={37.98} font={INTER}>
          BRO —
        </Word>
      </Line>
      <Line size={170} style={{marginTop: 30}}>
        <Word at={38.52} bg={C.pink}>
          DON&apos;T
        </Word>
        <Word at={38.76}>WASTE</Word>
      </Line>
      <Line size={130} style={{marginTop: 10}}>
        <Word at={38.92}>YOUR</Word>
      </Line>
      <Line size={280}>
        <Word at={39.12} color={C.money} glow>
          MONEY
        </Word>
      </Line>
    </Col>
  </Scene>
);

const Clock: React.FC<{from: number}> = ({from}) => {
  const frame = useCurrentFrame();
  const d = frame - f(from);
  const p = sp(frame, from, {damping: 12});
  return (
    <svg width={440} height={440} viewBox="-220 -220 440 440" style={{transform: `scale(${p})`, filter: `drop-shadow(0 0 30px ${C.y}55)`}}>
      <circle r={200} fill="#ffffff08" stroke={C.fg} strokeWidth={10} />
      {Array.from({length: 12}, (_, i) => (
        <line key={i} x1={0} y1={-170} x2={0} y2={i % 3 === 0 ? -140 : -155} stroke={C.fg} strokeWidth={i % 3 === 0 ? 10 : 6} strokeLinecap="round" transform={`rotate(${i * 30})`} />
      ))}
      <line x1={0} y1={0} x2={0} y2={-110} stroke={C.fg} strokeWidth={14} strokeLinecap="round" transform={`rotate(${d * 3})`} />
      <line x1={0} y1={0} x2={0} y2={-160} stroke={C.y} strokeWidth={8} strokeLinecap="round" transform={`rotate(${d * 36})`} />
      <circle r={14} fill={C.y} />
    </svg>
  );
};

const S12bTime: React.FC = () => (
  <Scene from={39.65} to={40.9}>
    <Col gap={20}>
      <Clock from={39.68} />
      <Line size={170}>
        <Word at={39.7} bg={C.pink}>
          DON&apos;T
        </Word>
        <Word at={39.92}>WASTE</Word>
      </Line>
      <Line size={130}>
        <Word at={40.06}>YOUR</Word>
      </Line>
      <Line size={280}>
        <Word at={40.28} color={C.y} glow>
          TIME.
        </Word>
      </Line>
    </Col>
  </Scene>
);

const S13Comment: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const bar = sp(frame, 41.1, {damping: 14});
  const word = '"CLAUDE"';
  const n = Math.ceil(word.length * interpolate(t, [41.34, 41.75], [0, 1], clamp));
  const posted = sp(frame, 41.85, {damping: 11, stiffness: 220});
  const plane = interpolate(frame, [f(42.9), f(43.5)], [0, 1], {...clamp, easing: Easing.in(Easing.cubic)});
  return (
    <Scene from={40.9} to={DURATION_S + 1}>
      <Col top={260}>
        <Line size={210}>
          <Word at={41.08}>COMMENT</Word>
        </Line>
        <div
          style={{
            marginTop: 50,
            width: 940,
            height: 140,
            borderRadius: 70,
            background: '#1A1A1F',
            border: `3px solid ${frame >= f(41.85) ? C.y : '#33333B'}`,
            display: 'flex',
            alignItems: 'center',
            padding: '0 26px',
            gap: 26,
            opacity: Math.min(1, bar * 2),
            transform: `translateY(${(1 - bar) * 200}px)`,
            fontFamily: INTER,
          }}
        >
          <div style={{width: 92, height: 92, borderRadius: 46, background: C.y, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: ANTON, fontSize: 54, color: '#111'}}>J</div>
          <div style={{flex: 1, textAlign: 'left', fontSize: 54, fontWeight: 800, color: n > 0 ? C.y : '#6E6E76'}}>
            {n > 0 ? word.slice(0, n) : 'Add a comment...'}
            {frame < f(41.85) && n > 0 && <span style={{display: 'inline-block', width: 4, height: 56, background: C.fg, marginLeft: 6, verticalAlign: 'middle'}} />}
          </div>
          <div style={{fontSize: 40, fontWeight: 800, color: C.y, transform: `scale(${1 + (frame >= f(41.85) && frame < f(41.85) + 6 ? 0.2 : 0)})`}}>Post</div>
        </div>
        <div style={{height: 130, marginTop: 30, transform: `scale(${posted})`, opacity: posted}}>
          <div style={{fontFamily: INTER, fontSize: 40, color: C.fg, background: '#ffffff12', borderRadius: 30, padding: '20px 34px', display: 'inline-block'}}>
            <b style={{color: C.y}}>you</b> · CLAUDE <span style={{color: C.pink}}>♥</span>
          </div>
        </div>
        <Line size={72} font={INTER} style={{fontWeight: 800, letterSpacing: 4, marginTop: 10}}>
          <Word at={41.86} font={INTER}>
            AND
          </Word>
          <Word at={42.34} font={INTER}>
            I&apos;LL
          </Word>
          <Word at={42.48} font={INTER}>
            SEND
          </Word>
          <Word at={42.62} font={INTER}>
            YOU
          </Word>
        </Line>
        <Line size={140} style={{marginTop: 20}}>
          <Word at={42.76}>THE</Word>
          <Word at={42.88} color={C.y} glow>
            INSTRUCTIONS
          </Word>
        </Line>
        <div style={{marginTop: 40, fontFamily: INTER, fontSize: 46, fontWeight: 700, color: C.dim, opacity: interpolate(frame, [f(43.4), f(43.8)], [0, 1], clamp)}}>@jako.frames</div>
      </Col>
      {plane > 0 && plane < 1 && (
        <div style={{position: 'absolute', left: interpolate(plane, [0, 1], [-150, 1200]), top: interpolate(plane, [0, 1], [1300, 500]), transform: 'rotate(-25deg)', filter: `drop-shadow(0 0 20px ${C.y})`}}>
          <svg width={140} height={140} viewBox="0 0 24 24">
            <path d="M2 21 L23 12 L2 3 L2 10 L17 12 L2 14 Z" fill={C.y} />
          </svg>
        </div>
      )}
    </Scene>
  );
};

export const Reel: React.FC = () => {
  const frame = useCurrentFrame();
  const s = shake(frame);
  return (
    <AbsoluteFill style={{background: C.bg, overflow: 'hidden'}}>
      <Background />
      <AbsoluteFill style={{transform: `translate(${s.x}px, ${s.y}px) rotate(${s.r}deg)`}}>
        <S1Heck />
        <S2Ready />
        <S3AfterEffects />
        <S4Higgsfield />
        <S5Claude />
        <S6Chat />
        <S7DidIt />
        <S8aEveryFrame />
        <S8bExpensive />
        <S9Code />
        <S10Every />
        <S11AllCode />
        <S12aMoney />
        <S12bTime />
        <S13Comment />
      </AbsoluteFill>
      <Comet />
    </AbsoluteFill>
  );
};
