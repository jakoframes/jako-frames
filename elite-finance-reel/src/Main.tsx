import React from 'react';
import {AbsoluteFill, Audio, OffthreadVideo, Sequence, staticFile, useCurrentFrame} from 'remotion';
import data from './data.json';
import {Intro, INTRO_FRAMES} from './Intro';
import {Outro, OUTRO_FRAMES} from './Outro';
import {Scenes} from './Scenes';
import {C, FONT, FPS, fontCss, outExpo, prog} from './theme';
import {p, useT} from './ui';

const VSTART = INTRO_FRAMES - 8; // footage fades in under the intro's exit
const CUT_FRAMES = Math.round(data.cutDur * FPS);
const OUTRO_START = VSTART + CUT_FRAMES - 12;
export const MAIN_FRAMES = OUTRO_START + OUTRO_FRAMES;
const Q = data.cues;

// alternate framing per edit segment hides jump cuts; slow push inside each segment
const Footage: React.FC = () => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const i = Math.max(0, data.segs.findIndex((s) => t >= s.start && t < s.start + s.dur));
  const seg = data.segs[i] ?? data.segs[0];
  const base = i % 2 === 0 ? 1.0 : 1.12;
  const push = 0.035 * ((t - seg.start) / seg.dur);
  const fadeIn = outExpo(prog(f, 0, 12));
  // blur transition: ramps up into each cut and resolves out of it (±BLUR_WIN frames)
  const BLUR_WIN = 6;
  const cutDist = Math.min(...data.segs.slice(1).map((s) => Math.abs(f - s.start * FPS)));
  const b = Math.max(0, 1 - cutDist / BLUR_WIN);
  const blur = b * b * 26;
  return (
    <AbsoluteFill style={{opacity: fadeIn}}>
      <AbsoluteFill
        style={{
          transform: `scale(${(base + push) * (1 + 0.08 * (1 - fadeIn)) * (1 + 0.07 * b)})`,
          transformOrigin: '540px 640px',
          filter: `contrast(1.06) saturate(1.04) brightness(${0.98 + 0.1 * b}) blur(${blur}px)`,
        }}
      >
        <OffthreadVideo src={staticFile('cut.mp4')} />
      </AbsoluteFill>
      {/* readability vignettes */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(4,5,11,0.55) 0%, rgba(4,5,11,0) 16%, rgba(4,5,11,0) 44%, rgba(4,5,11,0.5) 60%, rgba(4,5,11,0.7) 100%)',
        }}
      />
    </AbsoluteFill>
  );
};

const TABS: [string, number, number][] = [
  ['7-20-25', Q.p725, Q.nauryz],
  ['НАУРЫЗ', Q.nauryz, Q.otau],
  ['ОТАУ', Q.otau, Q.cta],
];

const TopBar: React.FC = () => {
  const t = useT();
  const k = outExpo(p(t, Q.title + 0.4, 0.6));
  const out = outExpo(p(t, Q.cta - 0.2, 0.4));
  const active = TABS.findIndex(([, a, b]) => t >= a && t < b);
  return (
    <div
      style={{
        position: 'absolute',
        top: 110,
        left: 0,
        right: 0,
        display: 'flex',
        justifyContent: 'center',
        opacity: k * (1 - out),
        transform: `translateY(${(1 - k) * -30}px)`,
        fontFamily: FONT,
      }}
    >
      <div
        style={{
          display: 'flex',
          gap: 6,
          padding: 8,
          borderRadius: 40,
          background: 'rgba(8,10,20,0.62)',
          border: '1.5px solid rgba(255,255,255,0.12)',
          backdropFilter: 'blur(16px)',
        }}
      >
        {TABS.map(([name, a], idx) => {
          const on = outExpo(p(t, a, 0.4)) * (idx === active ? 1 : 0);
          return (
            <div
              key={name}
              style={{
                padding: '14px 30px',
                borderRadius: 32,
                fontSize: 26,
                fontWeight: 800,
                letterSpacing: 1.5,
                color: on > 0.5 ? C.ink : 'rgba(255,255,255,0.7)',
                background: `rgba(242,169,59,${on})`,
                boxShadow: on > 0.5 ? '0 6px 24px rgba(242,169,59,0.45)' : 'none',
              }}
            >
              {name}
            </div>
          );
        })}
      </div>
    </div>
  );
};

// fixed-position captions: same baseline, no bounce; spoken word turns gold
const Subtitles: React.FC = () => {
  const t = useT();
  const ch = data.chunks.find((c) => t >= c.s && t < c.e);
  if (!ch) return null;
  const k = outExpo(p(t, ch.s, 0.12));
  return (
    <div
      style={{
        position: 'absolute',
        left: 60,
        right: 60,
        top: 1050,
        height: 150,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        fontFamily: FONT,
        fontWeight: 800,
        fontSize: 64,
        lineHeight: 1.12,
        letterSpacing: -0.5,
        opacity: k,
        transform: `translateY(${(1 - k) * 8}px)`,
      }}
    >
      <div>
        {ch.ids.map((id, n) => {
          const w = data.words[id];
          const on = t >= w.s - 0.04;
          return (
            <span
              key={id}
              style={{
                color: on ? (t < w.e + 0.05 ? C.gold : C.white) : 'rgba(255,255,255,0.55)',
                textShadow: '0 3px 0 rgba(0,0,0,0.35), 0 6px 22px rgba(0,0,0,0.65)',
              }}
            >
              {w.w}
              {n < ch.ids.length - 1 ? ' ' : ''}
            </span>
          );
        })}
      </div>
    </div>
  );
};

// cue-driven sound design, kept quiet under the voice
const SFX: React.FC = () => {
  const at = (s: number) => VSTART + Math.round(s * FPS);
  const cards = [Q.title, Q.p725, Q.nauryz, Q.deposit, Q.cities, Q.otau, Q.savings, Q.cta];
  const ticks = [Q.down20, Q.years25, Q.limit, Q.income, Q.match, Q.nauryz7, Q.nauryz10, Q.nauryz9, Q.nauryz20, Q.deposit2m, Q.years19, Q.city36, Q.city30, Q.otauRates, Q.otau9, Q.otau20, Q.savingsDown];
  return (
    <>
      <Sequence from={0}>
        <Audio src={staticFile('sfx/whoosh.wav')} volume={0.35} />
      </Sequence>
      <Sequence from={14}>
        <Audio src={staticFile('sfx/hit.wav')} volume={0.55} />
      </Sequence>
      {cards.map((s, i) => (
        <Sequence key={'w' + i} from={at(s) - 6}>
          <Audio src={staticFile('sfx/whoosh.wav')} volume={0.12} />
        </Sequence>
      ))}
      {ticks.map((s, i) => (
        <Sequence key={'t' + i} from={at(s)}>
          <Audio src={staticFile('sfx/tick.wav')} volume={0.14} />
        </Sequence>
      ))}
      <Sequence from={at(Q.ctaBrand + 1.0)}>
        <Audio src={staticFile('sfx/pop.wav')} volume={0.2} />
      </Sequence>
      <Sequence from={OUTRO_START}>
        <Audio src={staticFile('sfx/whoosh.wav')} volume={0.3} />
      </Sequence>
      <Sequence from={OUTRO_START + 40}>
        <Audio src={staticFile('sfx/hit.wav')} volume={0.35} />
      </Sequence>
    </>
  );
};

export const Main: React.FC = () => {
  return (
    <AbsoluteFill style={{background: C.bg}}>
      <style>{fontCss}</style>
      <Sequence from={VSTART} durationInFrames={CUT_FRAMES}>
        <Footage />
        <Scenes />
        <TopBar />
        <Subtitles />
      </Sequence>
      <Sequence durationInFrames={INTRO_FRAMES}>
        <Intro />
      </Sequence>
      <Sequence from={OUTRO_START} durationInFrames={OUTRO_FRAMES}>
        <Outro />
      </Sequence>
      <SFX />
    </AbsoluteFill>
  );
};
