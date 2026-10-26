import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {Crop} from './Crop';
import {inOutCubic, outBack, outExpo, prog} from './theme';

export const OUTRO_FRAMES = 120;

// Rebuilds outro-white.png (1080x1920) piece by piece so the last frame matches it exactly.
const piece = (x: number, y: number, w: number, h: number) => ({x, y, w, h});
const Z = piece(390, 200, 266, 240);
const PHONE = piece(235, 568, 560, 132);
const BRAND = piece(235, 890, 615, 145);
const ADDR = piece(235, 1182, 595, 155);
const STAR = piece(362, 1428, 342, 336);

export const Outro: React.FC = () => {
  const f = useCurrentFrame();

  const panel = inOutCubic(prog(f, 0, 14));
  const z = outBack(prog(f, 8, 18));
  const row = (start: number) => outExpo(prog(f, start, 18));
  const star = outBack(prog(f, 40, 22));
  const spin = -120 * (1 - outExpo(prog(f, 40, 30))) + Math.max(0, f - 40) * 0.35;

  const rowStyle = (p: number, r: typeof PHONE): React.CSSProperties => ({
    left: r.x,
    top: r.y,
    opacity: p,
    transform: `translateX(${(1 - p) * -60}px)`,
    clipPath: `inset(0 ${(1 - p) * 100}% 0 0)`,
  });

  return (
    <AbsoluteFill>
      {/* white panel slides up over the footage */}
      <AbsoluteFill style={{background: '#FFFFFF', transform: `translateY(${(1 - panel) * 100}%)`}} />

      <Crop
        src="outro-white.png"
        srcW={1080}
        {...Z}
        style={{left: Z.x, top: Z.y, opacity: prog(f, 8, 6), transform: `translateY(${(1 - z) * -80}px) scale(${0.7 + 0.3 * z})`}}
      />
      <Crop src="outro-white.png" srcW={1080} {...PHONE} style={rowStyle(row(18), PHONE)} />
      <Crop src="outro-white.png" srcW={1080} {...BRAND} style={rowStyle(row(26), BRAND)} />
      <Crop src="outro-white.png" srcW={1080} {...ADDR} style={rowStyle(row(34), ADDR)} />
      <Crop
        src="outro-white.png"
        srcW={1080}
        {...STAR}
        style={{left: STAR.x, top: STAR.y, opacity: prog(f, 40, 6), transform: `scale(${star}) rotate(${spin}deg)`}}
      />
    </AbsoluteFill>
  );
};
