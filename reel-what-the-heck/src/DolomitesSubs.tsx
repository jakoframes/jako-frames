import React from 'react';
import {AbsoluteFill, OffthreadVideo, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {loadFont as loadInter} from '@remotion/google-fonts/Inter';
import subs from '../../reel-agents-dolomites/subs.json';

// Plain subtitles over the Blender render of "Who are they?" (Dolomites).
// One fixed spot, no speaker names; long lines are split into short chunks shown one after another.
const INTER = loadInter('normal', {weights: ['700'], subsets: ['latin']}).fontFamily;

export const SUBS_FRAMES = 1190;
const SUB_Y = 1400;        // fixed baseline: lower third, above Instagram's caption area
const MAX_WORDS = 4;

type Line = {id: string; text: string; from: number; to: number};
type Chunk = {text: string; from: number; to: number};

// split at punctuation first, then into pieces of at most MAX_WORDS words; time each piece by its length
function chunks(l: Line): Chunk[] {
  const parts: string[] = [];
  for (const p of l.text.split(/(?<=[.,?!…])\s+/)) {
    const w = p.split(/\s+/);
    for (let i = 0; i < w.length; i += MAX_WORDS) parts.push(w.slice(i, i + MAX_WORDS).join(' '));
  }
  // C02 names the agents over the fast cuts: lock each name to its cut (frames from timeline.json subshots)
  if (l.id === 'C02' && parts.length === 6) {
    const at = [l.from, 112, 126, 142, 163, 189, l.to];
    return parts.map((p, i) => ({text: p, from: at[i], to: at[i + 1]}));
  }
  const total = parts.reduce((s, p) => s + p.length, 0);
  const span = l.to - l.from;
  let t = l.from;
  return parts.map((p, i) => {
    const d = i === parts.length - 1 ? l.to - t : Math.round((span * p.length) / total);
    const c = {text: p, from: t, to: t + d};
    t += d;
    return c;
  });
}

const ALL: Chunk[] = (subs as Line[]).flatMap((l) => {
  const c = chunks(l);
  c[0].from -= 2;              // appear just before the voice
  c[c.length - 1].to += 6;     // linger a moment after it
  return c;
});

export const DolomitesSubs: React.FC = () => {
  const frame = useCurrentFrame();
  const cur = ALL.find((c) => frame >= c.from && frame < c.to);
  // fade only where a line starts/ends; chunks inside a line just swap
  const line = cur && (subs as Line[]).find((l) => cur.from >= l.from - 2 && cur.to <= l.to + 6);
  const a = line ? line.from - 2 : 0;
  const b = line ? line.to + 6 : 1;
  const op = cur ? interpolate(frame, [a, a + 3, b - 3, b], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}) : 0;
  return (
    <AbsoluteFill>
      <OffthreadVideo src={staticFile('dolomites.mp4')} />
      {cur && (
        <div style={{position: 'absolute', left: 0, right: 0, top: SUB_Y, display: 'flex', justifyContent: 'center', opacity: op}}>
          <div
            style={{
              background: 'rgba(15,10,20,0.45)',
              borderRadius: 14,
              padding: '10px 22px',
              fontFamily: INTER,
              fontWeight: 700,
              fontSize: 44,
              color: 'white',
              whiteSpace: 'nowrap',
            }}
          >
            {cur.text}
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
