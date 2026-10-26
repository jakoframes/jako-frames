import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {loadFont as loadInter} from '@remotion/google-fonts/Inter';
import subs from '../../../reel-1k-cake/subs/subs.json';

// Subtitles for the "1000 followers" cake reel (reel-1k-cake), transparent overlay composited by ffmpeg.
// Look follows the user's style refs (reel-1k-cake/ref/style_ref_4..7.png): white bold sans-serif in a rounded
// semi-transparent dark-grey box, top-centre. Chunking/fading approach from DolomitesSubs.tsx; chunk timing is
// word-accurate (whisper word times in subs.json, exported by blender/s3_anim.py).
const INTER = loadInter('normal', {weights: ['700'], subsets: ['latin']}).fontFamily;

export const CAKE_FRAMES: number = (subs as any).frames;
const TOP = 250;            // below the IG top bar
const MAX_W = 700;
const MAX_WORDS = 5;

type Word = {w: string; from: number; to: number};
type Line = {id: string; who: string; text: string; from: number; to: number; words: Word[]};
type Chunk = {words: Word[]; from: number; to: number; a: number; b: number; italic?: boolean};

function tokens(l: Line): Word[] {
  const t = l.text.split(/\s+/);
  return t.length === l.words.length ? l.words.map((w, i) => ({...w, w: t[i]})) : l.words;
}

// split a line into short chunks (sentence ends, commas after 4+ words, max 5 words); time each chunk by its words
function chunks(ws: Word[], lineFrom: number, lineTo: number, italic = false): Chunk[] {
  const out: Chunk[] = [];
  let cur: Word[] = [];
  ws.forEach((w, i) => {
    cur.push(w);
    if (/[.?!…—]$/.test(w.w) || cur.length >= MAX_WORDS || (/,$/.test(w.w) && cur.length >= 4) || i === ws.length - 1) {
      out.push({words: cur, from: 0, to: 0, a: lineFrom - 2, b: lineTo + 8, italic});
      cur = [];
    }
  });
  out.forEach((c, i) => {
    c.from = i === 0 ? lineFrom - 2 : c.words[0].from - 1;
    c.to = i < out.length - 1 ? out[i + 1].words[0].from - 1 : lineTo + 8;
  });
  return out;
}

const LINES = (subs as any).lines as Line[];
const phone = (subs as any).phone_chip;
const PHONE_TOKENS = ['"...state.', 'Hey,', 'hit', 'the', 'road,', 'dude."'];
const firstLine = Math.min(...LINES.map((l) => l.from));
const phoneWords: Word[] = phone.words.slice(0, PHONE_TOKENS.length).map((w: Word, i: number) => ({...w, w: PHONE_TOKENS[i]}));
const ALL: Chunk[] = [
  ...chunks(phoneWords, Math.max(0, phone.from + 2), Math.min(phone.to, firstLine - 10), true).map((c) => ({...c, from: Math.max(0, c.from), to: Math.min(c.to, firstLine - 3), b: firstLine - 3})),
  ...LINES.flatMap((l) => chunks(tokens(l), l.from, l.to)),
];

export const CakeSubs: React.FC = () => {
  const frame = useCurrentFrame();
  const c = [...ALL].reverse().find((k) => frame >= k.from && frame < k.to);   // later line wins on overlap
  if (!c) return <AbsoluteFill style={{backgroundColor: 'transparent'}} />;
  const op = interpolate(frame, [c.a, c.a + 3, c.b - 3, c.b], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{backgroundColor: 'transparent'}}>
      <div style={{position: 'absolute', top: TOP, left: 0, right: 0, display: 'flex', justifyContent: 'center', opacity: op}}>
        <div style={{maxWidth: MAX_W, background: 'rgba(58,58,62,0.62)', borderRadius: 26, padding: '16px 30px 18px', textAlign: 'center',
          fontFamily: INTER, fontWeight: 700, fontSize: 54, lineHeight: 1.22, color: '#FFFFFF', fontStyle: c.italic ? 'italic' : 'normal'}}>
          {c.words.map((w) => w.w).join(' ')}
        </div>
      </div>
    </AbsoluteFill>
  );
};
