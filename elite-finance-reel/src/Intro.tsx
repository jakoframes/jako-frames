import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {Crop} from './Crop';
import {C, inOutCubic, outBack, outExpo, prog} from './theme';

export const INTRO_FRAMES = 78;

// Logo source (logo-dark.png, 2000x1281) mapped to screen: source (440,640) -> (OX,OY)
const S = 0.78;
const OX = 103;
const OY = 880;
const at = (x: number, y: number) => ({left: OX + (x - 440) * S, top: OY + (y - 640) * S});

const hexPoints = (cx: number, cy: number, r: number) =>
  Array.from({length: 6}, (_, i) => {
    const a = (Math.PI / 3) * i - Math.PI / 2;
    return `${cx + r * Math.cos(a)},${cy + r * Math.sin(a)}`;
  }).join(' ');

export const Intro: React.FC = () => {
  const f = useCurrentFrame();

  const bgIn = outExpo(prog(f, 0, 14));
  const line = outExpo(prog(f, 2, 20));
  const hexDraw = inOutCubic(prog(f, 4, 22));
  const hexFade = 1 - prog(f, 30, 12);
  const mark = outBack(prog(f, 14, 18));
  const markBlur = (1 - outExpo(prog(f, 14, 16))) * 14;
  const text = outExpo(prog(f, 26, 20));
  const sweep = inOutCubic(prog(f, 40, 18));
  const rule = outExpo(prog(f, 44, 16));
  const exit = inOutCubic(prog(f, 62, 16));

  const markC = at(555, 640);
  const hexR = 128;
  const perim = hexR * 6;

  return (
    <AbsoluteFill style={{background: C.bg, opacity: bgIn}}>
      {/* soft gold glow + faint grid */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at 50% 46%, rgba(242,169,59,${0.16 * bgIn}) 0%, rgba(242,169,59,0) 55%)`,
        }}
      />
      <AbsoluteFill
        style={{
          opacity: 0.07 * bgIn * (1 - exit),
          backgroundImage:
            'linear-gradient(rgba(255,255,255,1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,1) 1px, transparent 1px)',
          backgroundSize: '90px 90px',
          maskImage: 'radial-gradient(circle at 50% 46%, black 0%, transparent 60%)',
          WebkitMaskImage: 'radial-gradient(circle at 50% 46%, black 0%, transparent 60%)',
        }}
      />

      <AbsoluteFill
        style={{
          transform: `scale(${1 + 0.1 * exit})`,
          opacity: 1 - exit,
          filter: `blur(${exit * 10}px)`,
        }}
      >
        {/* horizontal scan line */}
        <div
          style={{
            position: 'absolute',
            top: OY + 150,
            left: 540 - 420 * line,
            width: 840 * line,
            height: 2,
            background: `linear-gradient(90deg, transparent, ${C.gold}, transparent)`,
            opacity: 0.8 * (1 - prog(f, 34, 14)),
          }}
        />

        {/* hexagon that draws itself, then hands over to the real mark */}
        <svg width={1080} height={1920} style={{position: 'absolute', inset: 0, opacity: hexFade}}>
          <polygon
            points={hexPoints(markC.left, markC.top, hexR)}
            fill="none"
            stroke={C.gold}
            strokeWidth={3}
            strokeDasharray={perim}
            strokeDashoffset={perim * (1 - hexDraw)}
            strokeLinejoin="round"
          />
        </svg>

        {/* mark */}
        <Crop
          src="logo-alpha.png"
          srcW={2000}
          x={440}
          y={515}
          w={232}
          h={250}
          s={S}
          style={{
            ...at(440, 515),
            transform: `scale(${0.55 + 0.45 * mark})`,
            opacity: prog(f, 14, 6),
            filter: `blur(${markBlur}px)`,
          }}
        />

        {/* wordmark wipe */}
        <div
          style={{
            position: 'absolute',
            ...at(712, 585),
            width: 852 * S,
            height: 102 * S,
            clipPath: `inset(0 ${(1 - text) * 100}% 0 0)`,
            transform: `translateX(${(1 - text) * -24}px)`,
          }}
        >
          <Crop src="logo-alpha.png" srcW={2000} x={712} y={585} w={852} h={102} s={S} style={{left: 0, top: 0}} />
          {/* light sweep */}
          <div
            style={{
              position: 'absolute',
              top: -20,
              bottom: -20,
              width: 120,
              left: -160 + sweep * (852 * S + 320),
              background: 'linear-gradient(90deg, transparent, rgba(255,240,210,0.55), transparent)',
              transform: 'skewX(-20deg)',
              mixBlendMode: 'overlay',
              opacity: sweep > 0 && sweep < 1 ? 1 : 0,
            }}
          />
        </div>

        {/* gold rule under wordmark */}
        <div
          style={{
            position: 'absolute',
            ...at(716, 720),
            width: 845 * S * rule,
            height: 3,
            background: `linear-gradient(90deg, ${C.gold}, rgba(242,169,59,0))`,
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
