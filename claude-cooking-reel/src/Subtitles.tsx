// Steady subtitles: one short phrase at a time in one fixed spot, just above Instagram's caption area.
// Nothing bounces: a phrase gives way the instant the next one fades in, and the word being spoken turns orange.
import React from 'react';
import {VO_END, WORDS} from './timing';
import {FONT, clamp} from './ui';

// phrases as word-index ranges into vo.json (inclusive), cut where a viewer would breathe
const RANGES: [number, number][] = [
  [0, 5], [6, 10], [11, 16], [17, 20], [21, 24], [25, 31], [32, 37], [38, 40], [41, 44], [45, 48],
  [49, 53], [54, 57], [58, 60], [61, 62], [63, 66], [67, 68], [69, 74], [75, 78],
];
if (WORDS.length !== 79) throw new Error(`RANGES expect 79 words, vo.json has ${WORDS.length}: regroup them`);
const show = (w: string) => w.replace(/\.$/, '');
type Phrase = {words: {text: string; s: number}[]; s: number; e: number};
const PHRASES: Phrase[] = RANGES.map(([a, b]) => {
  const words: {text: string; s: number}[] = [];
  for (let i = a; i <= b; i++) {
    const w = WORDS[i];
    // whisper splits "5.5" into "5" + ".5"
    if (/^\.\d/.test(w.w) && words.length) words[words.length - 1].text += w.w;
    else words.push({text: i === 68 ? '“SaaS”' : show(w.w), s: w.s});
  }
  return {words, s: WORDS[a].s - 0.08, e: 0};
});
PHRASES.forEach((p, i) => (p.e = i + 1 < PHRASES.length ? PHRASES[i + 1].s : VO_END + 0.25));

const Y = 1430; // phrase centre: clear of the IG caption (bottom ~420 px) and of the headline band at the top
export const Subtitles: React.FC<{t: number}> = ({t}) => (
  <>
    {PHRASES.map((p, i) => {
      const last = i === PHRASES.length - 1;
      if (t < p.s || t >= p.e + (last ? 0.15 : 0)) return null;
      const pin = clamp((t - p.s) / 0.1);
      const o = pin * (last ? 1 - clamp((t - p.e) / 0.15) : 1);
      return (
        <div key={i} style={{position: 'absolute', left: 60, right: 60, top: Y, display: 'flex', justifyContent: 'center', opacity: o, transform: `translateY(calc(-50% + ${(1 - pin) * 8}px))`}}>
          <div style={{display: 'flex', flexWrap: 'wrap', justifyContent: 'center', columnGap: 13, padding: '14px 30px 16px', borderRadius: 24, maxWidth: 900,
            background: 'rgba(20,18,23,.88)', boxShadow: '0 14px 30px -8px rgba(20,18,23,.35)'}}>
            {p.words.map((w, j) => {
              const next = p.words[j + 1]?.s ?? p.e;
              const on = t >= w.s - 0.03 && t < next - 0.03;
              return <span key={j} style={{fontFamily: FONT.display, fontWeight: 700, fontSize: 50, lineHeight: 1.12, letterSpacing: '-0.01em', color: on ? '#FF9466' : '#FFFFFF', whiteSpace: 'nowrap'}}>{w.text}</span>;
            })}
          </div>
        </div>
      );
    })}
  </>
);
