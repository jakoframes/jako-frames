import React from 'react';
import {AbsoluteFill} from 'remotion';
import {loadFont as loadHeavy} from '@remotion/google-fonts/InterTight';
import {loadFont as loadSerif} from '@remotion/google-fonts/InstrumentSerif';
import {loadFont as loadMono} from '@remotion/google-fonts/IBMPlexMono';

const HEAVY = loadHeavy('normal', {weights: ['900'], subsets: ['latin']}).fontFamily;
const SERIF = loadSerif('italic', {weights: ['400'], subsets: ['latin']}).fontFamily;
const MONO = loadMono('normal', {weights: ['500'], subsets: ['latin']}).fontFamily;

const P = {
  cream: '#F1ECE4',
  orange: '#FF5B1F',
  lime: '#D9F53B',
  violet: '#6C5CF5',
  deep: '#15122E',
};

// Instagram cover, 1080x1920. Key content stays inside the 3:4 grid crop (y 285..1635).
const Glass: React.FC<{x: number; y: number; r: number; sx?: number; rot?: number}> = ({x, y, r, sx = 1, rot = 0}) => (
  <div
    style={{
      position: 'absolute',
      left: x - r,
      top: y - r,
      width: 2 * r,
      height: 2 * r,
      borderRadius: '50%',
      transform: `rotate(${rot}deg) scaleX(${sx})`,
      background: [
        'radial-gradient(circle at 32% 26%, rgba(255,255,255,0.95) 0 3%, rgba(255,255,255,0.35) 9%, transparent 22%)',
        'radial-gradient(circle at 72% 76%, rgba(255,110,90,0.9), transparent 42%)',
        'radial-gradient(circle at 22% 72%, rgba(80,220,255,0.75), transparent 45%)',
        'radial-gradient(circle at 80% 30%, rgba(217,245,59,0.45), transparent 35%)',
        'radial-gradient(circle at 50% 50%, #3a2f8f 0%, #1a1440 70%, #0d0a24 100%)',
      ].join(','),
      boxShadow: `inset -${r * 0.15}px -${r * 0.2}px ${r * 0.4}px rgba(0,0,0,0.5), inset ${r * 0.08}px ${r * 0.08}px ${r * 0.25}px rgba(255,255,255,0.3), 0 ${r * 0.35}px ${r * 0.7}px rgba(0,0,0,0.5)`,
    }}
  />
);

const hud: React.CSSProperties = {position: 'absolute', fontFamily: MONO, fontWeight: 500, fontSize: 22, letterSpacing: '0.22em', color: '#ffffff66'};

export const Cover: React.FC = () => (
  <AbsoluteFill style={{background: `radial-gradient(circle at 50% 46%, #2C2566 0%, ${P.deep} 48%, #08080D 100%)`, overflow: 'hidden'}}>
    <AbsoluteFill style={{backgroundImage: 'radial-gradient(#ffffff14 2px, transparent 2.5px)', backgroundSize: '36px 36px'}} />

    <Glass x={170} y={520} r={95} />
    <Glass x={930} y={430} r={58} />
    <Glass x={880} y={1440} r={150} sx={0.72} rot={-30} />
    <Glass x={200} y={1390} r={46} />

    <div style={{...hud, left: 60, top: 70}}>JAKO.FRAMES / MOTION REEL 2026</div>
    <div style={{...hud, right: 60, top: 70}}>TC 00:00:00:00</div>
    <div style={{...hud, left: 60, bottom: 70}}>1080 × 1920</div>
    <div style={{...hud, right: 60, bottom: 70}}>30 FPS</div>

    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', textAlign: 'center'}}>
      <div style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 78, color: '#ffffffcc', marginBottom: 34}}>me, after one prompt:</div>
      <div style={{fontFamily: HEAVY, fontWeight: 900, letterSpacing: '-0.045em', lineHeight: 0.86, color: P.cream, fontSize: 184}}>WHAT THE</div>
      <div style={{fontFamily: HEAVY, fontWeight: 900, letterSpacing: '-0.045em', lineHeight: 0.86, color: P.cream, fontSize: 212, marginTop: 6}}>
        HEEECK<span style={{fontFamily: SERIF, fontStyle: 'italic', fontWeight: 400, letterSpacing: 0, color: P.orange}}>?!</span>
      </div>
      <div
        style={{
          marginTop: 70,
          padding: '18px 40px',
          borderRadius: 60,
          background: P.lime,
          fontFamily: MONO,
          fontWeight: 500,
          fontSize: 30,
          letterSpacing: '0.2em',
          color: '#0C0C0E',
        }}
      >
        MADE WITH ONLY CLAUDE
      </div>
    </AbsoluteFill>
  </AbsoluteFill>
);
