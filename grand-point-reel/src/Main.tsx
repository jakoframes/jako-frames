import React from 'react';
import {AbsoluteFill, Audio, OffthreadVideo, Sequence, staticFile, useCurrentFrame} from 'remotion';
import data from './data.json';
import {Outro, OUTRO_FRAMES} from './Outro';
import {MythStamp, Scenes} from './Scenes';
import {C, FONT, FPS, fontCss, outExpo} from './theme';
import {p, useT} from './ui';

const VSTART = 0; // no logo intro: open straight on the hook
const CUT_FRAMES = Math.round(data.cutDur * FPS);
const OUTRO_START = VSTART + CUT_FRAMES - 10;
export const MAIN_FRAMES = OUTRO_START + OUTRO_FRAMES;
const Q = data.cues;
const L = data.lines;

// one framing per spoken line: wide / slam / medium / close ...
const SHOT_ZOOM = [1.0, 1.55, 1.14, 1.34, 1.02, 1.24, 1.1];
const ORIGIN = '600px 560px'; // face
const shotStarts = L.map((l, i) => (i === 0 ? 0 : l.s - 0.06));

const Footage: React.FC = () => {
  const f = useCurrentFrame();
  const t = f / FPS;
  let i = 0;
  shotStarts.forEach((s, k) => {
    if (t >= s) i = k;
  });
  const shotStart = shotStarts[i];
  const shotEnd = shotStarts[i + 1] ?? data.cutDur;
  const push = 0.05 * ((t - shotStart) / (shotEnd - shotStart));
  const fadeIn = 1;

  // zoom blur: overshoot + blur out of every shot change, short ramp into it
  const sinceCut = t - shotStart;
  const toNext = shotEnd - t;
  const inK = i === 0 ? 0 : Math.max(0, 1 - sinceCut / 0.28);
  const outK = i === shotStarts.length - 1 ? 0 : Math.max(0, 1 - toNext / 0.12);
  const zb = Math.max(inK * inK, outK * outK);
  const zoom = (SHOT_ZOOM[i] + push) * (1 + 0.16 * inK * inK + 0.08 * outK * outK) * (1 + 0.1 * (1 - fadeIn));

  // impact shake on "миф"
  const sh = Math.max(0, 1 - (t - Q.myth) / 0.35) * (t >= Q.myth ? 1 : 0);
  const sx = Math.sin(t * 90) * 16 * sh;
  const sy = Math.cos(t * 77) * 12 * sh;

  return (
    <AbsoluteFill style={{opacity: fadeIn}}>
      <AbsoluteFill
        style={{
          transform: `translate(${sx}px, ${sy}px) scale(${zoom})`,
          transformOrigin: ORIGIN,
          filter: `contrast(1.04) saturate(1.1) brightness(${1.04 + 0.12 * zb}) blur(${zb * 22}px)`,
        }}
      >
        <OffthreadVideo src={staticFile('cut.mp4')} />
      </AbsoluteFill>
      {/* warm cinematic vignette + readability bands */}
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(ellipse at 55% 32%, rgba(0,0,0,0) 50%, rgba(4,5,11,0.22) 100%), linear-gradient(180deg, rgba(4,5,11,0.3) 0%, rgba(4,5,11,0) 12%, rgba(4,5,11,0) 50%, rgba(4,5,11,0.3) 62%, rgba(4,5,11,0.45) 100%)',
        }}
      />
      {/* red flash on the myth hit */}
      <AbsoluteFill style={{background: '#E5484D', opacity: 0.22 * sh, mixBlendMode: 'multiply'}} />
    </AbsoluteFill>
  );
};

const TABS: [string, number, number][] = [
  ['МИФ', L[0].s, L[2].s],
  ['ФАКТЫ', L[2].s, L[4].s],
  ['РЕШЕНИЕ', L[4].s, data.cutDur + 1],
];

const TopBar: React.FC = () => {
  const t = useT();
  const k = outExpo(p(t, 0.3, 0.5));
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
        opacity: k,
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
          background: 'rgba(255,255,255,0.92)',
          boxShadow: '0 10px 30px rgba(0,0,0,0.25)',
        }}
      >
        {TABS.map(([name, a], idx) => {
          const on = outExpo(p(t, a, 0.3)) * (idx === active ? 1 : 0);
          return (
            <div
              key={name}
              style={{
                padding: '14px 30px',
                borderRadius: 32,
                fontSize: 26,
                fontWeight: 800,
                letterSpacing: 1.5,
                color: on > 0.5 ? '#fff' : C.muted,
                background: `rgba(10,11,18,${on})`,
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

// fixed captions between face and card; spoken word turns gold with a small pop
const Subtitles: React.FC = () => {
  const t = useT();
  const ch = data.chunks.find((c) => t >= c.s && t < c.e);
  if (!ch) return null;
  const k = outExpo(p(t, ch.s, 0.1));
  return (
    <div
      style={{
        position: 'absolute',
        left: 50,
        right: 50,
        top: 1050,
        height: 150,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        fontFamily: FONT,
        fontWeight: 800,
        fontSize: 68,
        lineHeight: 1.1,
        letterSpacing: -0.5,
        opacity: k,
        transform: `scale(${0.92 + 0.08 * k})`,
      }}
    >
      <div>
        {ch.ids.map((id, n) => {
          const w = data.words[id];
          const on = t >= w.s - 0.04;
          const now = on && t < w.e + 0.05;
          return (
            <span
              key={id}
              style={{
                display: 'inline-block',
                margin: '0 0.18em',
                color: now ? C.gold : on ? C.white : 'rgba(255,255,255,0.55)',
                transform: `scale(${now ? 1.06 : 1})`,
                textShadow: '0 3px 0 rgba(0,0,0,0.35), 0 6px 22px rgba(0,0,0,0.65)',
              }}
            >
              {w.w}
            </span>
          );
        })}
      </div>
    </div>
  );
};

const SFX: React.FC = () => {
  const at = (s: number) => VSTART + Math.max(0, Math.round(s * FPS));
  const whooshes = shotStarts.slice(1).map((s) => s - 0.12);
  const ticks = [Q.credit, Q.approve, Q.income, Q.oblig, Q.factors, Q.noKi + 0.3, Q.guarantee, Q.form, Q.tactic];
  return (
    <>
      {whooshes.map((s, i) => (
        <Sequence key={'w' + i} from={at(s)}>
          <Audio src={staticFile('sfx/whoosh.wav')} volume={0.18} />
        </Sequence>
      ))}
      {ticks.map((s, i) => (
        <Sequence key={'t' + i} from={at(s)}>
          <Audio src={staticFile('sfx/tick.wav')} volume={0.16} />
        </Sequence>
      ))}
      <Sequence from={at(Q.myth)}>
        <Audio src={staticFile('sfx/hit.wav')} volume={0.75} />
      </Sequence>
      <Sequence from={at(Q.brand)}>
        <Audio src={staticFile('sfx/pop.wav')} volume={0.22} />
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

export const Main: React.FC = () => (
  <AbsoluteFill style={{background: C.bg}}>
    <style>{fontCss}</style>
    <Sequence from={VSTART} durationInFrames={CUT_FRAMES}>
      <Footage />
      <Scenes />
      <TopBar />
      <Subtitles />
      <MythStamp />
    </Sequence>
    <Sequence from={OUTRO_START} durationInFrames={OUTRO_FRAMES}>
      <Outro />
    </Sequence>
    <SFX />
  </AbsoluteFill>
);
