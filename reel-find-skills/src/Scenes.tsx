// World-space scene art. Units are px; y grows down; the floor is at FLOOR (380).
// Graphics live in a band around y = -740 (top of the frame at the default camera).
import React from 'react';
import {Img, staticFile} from 'remotion';
import M from './character.js';
import {SC, T, VO_END} from './timing';
import {jakoPos, FLOOR} from './Jako';
import {Big, C, Check, Cursor, FONT, Mono, O, Panel, ZipIcon, clamp, inCubic, inOutCubic, life, lerp, outCubic, outExpo, pop, prog, rnd} from './ui';

type R = {t: number};
// visible window of a scene, plus k = exit envelope (1 → 0) for every object in it
const win = (t: number, id: string, exit = 0.3) => {
  const sc = SC[id];
  if (t < sc.s - 0.05 || t > sc.e + exit) return null;
  return {s: sc.s, e: sc.e, k: 1 - inCubic(clamp((t - sc.e) / exit))};
};
// enter from depth: returns z offset / tilt / opacity for an element that appears at `a`
const enter = (t: number, a: number, d = 0.5) => {
  const p = outExpo(prog(t, a, d));
  return {p, dz: -520 * (1 - p), rx: 24 * (1 - p), o: clamp(p * 1.6)};
};

// ---------------------------------------------------------------- 1. hook: a wall of skills
const NAMES = ['pdf', 'excel', 'seo', 'figma', 'react', 'motion', 'copywriting', 'legal', '3d', 'music', 'pptx', 'docx', 'ui-ux', 'email', 'sql', 'tiktok', 'notion', 'python', 'resume', 'branding', 'blender', 'video', 'ads', 'research', 'translate', 'finance', 'threejs', 'data-viz', 'youtube', 'logo', 'fitness', 'sales', 'podcast', 'shorts', 'api', 'game-dev', 'memes', 'docs', 'charts', 'mcp', 'security', 'pitch-deck', 'invoices', 'recipes', 'travel', 'crm', 'webflow', 'shopify', 'unity', 'audio', 'seo-audit', 'brand-voice', 'scraper', 'calendar'];
const Tile: React.FC<{label: string; hot?: boolean}> = ({label, hot}) => (
  <div style={{width: 250, height: 88, borderRadius: 18, background: hot ? 'rgba(240,122,72,.16)' : 'rgba(30,27,36,.92)', border: `2px solid ${hot ? C.orange : C.line}`, display: 'flex', alignItems: 'center', gap: 14, padding: '0 22px', boxSizing: 'border-box', boxShadow: '0 20px 40px rgba(0,0,0,.45)'}}>
    <span style={{width: 14, height: 14, borderRadius: 4, background: hot ? C.orange : '#4A4354', flex: 'none'}} />
    <Mono size={27} color={hot ? C.orangeHi : C.cream} w={700}>{label}</Mono>
  </div>
);
const Hook: React.FC<R> = ({t}) => {
  const w = win(t, 'hook', 0.6);
  if (!w) return null;
  const n = Math.round(1000 * outExpo(prog(t, -0.45, 1.5)));
  const counterO = 1 - prog(t, T.one - 0.16, 0.12);
  return (
    <>
      {Array.from({length: 54}, (_, i) => {
        const c = i % 9, r = Math.floor(i / 9);
        const drop = inCubic(prog(t, T.but0 + rnd(`dd${i}`) * 0.3, 0.55));
        return <O key={i} x={(c - 4) * 276} y={-720 + (r - 2.5) * 112 + drop * 1300} z={-560} rx={drop * 70} o={1 - drop}><Tile label={NAMES[i]} hot={i % 7 === 3} /></O>;
      })}
      {Array.from({length: 22}, (_, i) => {
        const drift = Math.sin(t * 0.9 + i) * 30;
        const drop = inCubic(prog(t, T.but0 + rnd(`fd${i}`) * 0.25, 0.5));
        let fy = -1250 + rnd(`fy${i}`) * 1500;
        if (fy > -600 && fy < -150) fy += 520; // keep the caption band clear
        return (
          <O key={`f${i}`} x={(rnd(`fx${i}`) - 0.5) * 2200} y={fy + drift + drop * 1400} z={-250 + rnd(`fz${i}`) * 900}
            ry={(rnd(`fr${i}`) - 0.5) * 50} rz={(rnd(`fq${i}`) - 0.5) * 20} o={1 - drop}>
            <Tile label={NAMES[(i * 7 + 5) % NAMES.length]} hot={i % 5 === 0} />
          </O>
        );
      })}
      {/* dark backdrop so the counter separates from the tile wall */}
      <O x={0} y={-740} z={-200} o={counterO}>
        <div style={{width: 1300, height: 760, borderRadius: '50%', background: 'radial-gradient(closest-side, rgba(9,8,12,.92), rgba(9,8,12,.6) 55%, rgba(9,8,12,0))'}} />
      </O>
      <O x={0} y={-740} z={-120} o={counterO * (0.55 + 0.45 * Math.sin(t * 5) ** 2)}>
        <div style={{width: 900, height: 420, borderRadius: '50%', background: `radial-gradient(closest-side, rgba(255,210,63,.42), rgba(255,170,40,.12) 60%, rgba(255,170,40,0))`}} />
      </O>
      <O x={0} y={-770} z={40} s={1 + 0.14 * Math.exp(-Math.max(0, t - 1.05) * 7) * (t > 1.05 ? 1 : 0)} o={counterO}>
        <div style={{display: 'grid', justifyItems: 'center', gap: 20}}>
          <Big size={215} color={C.yellow} depth={12} glow="rgba(255,200,40,.95)"
            style={{filter: 'drop-shadow(0 0 30px rgba(255,200,40,.55)) drop-shadow(0 0 80px rgba(255,150,30,.35))'}}>
            {n >= 1000 ? '1,000s' : n.toLocaleString('en-US')}
          </Big>
          <Mono size={32} color={C.yellow} w={700} style={{letterSpacing: '.32em', textShadow: '0 0 18px rgba(255,200,40,.8)'}}>CLAUDE SKILLS</Mono>
        </div>
      </O>
    </>
  );
};

// ---------------------------------------------------------------- 2. only one → masterpiece
const One: React.FC<R> = ({t}) => {
  const w = win(t, 'one');
  if (!w) return null;
  const p = outExpo(prog(t, T.one - 0.05, 0.45));
  const jx = jakoPos(t).x;
  const frame = outCubic(prog(t, T.master - 0.06, 0.6));
  return (
    <>
      <O x={0} y={-770} z={-80 - 400 * (1 - p)} s={1.25 - 0.25 * p} o={p * w.k}><Big size={470} color={C.orange} glow="rgba(240,122,72,.55)" depth={14}>1</Big></O>
      <O x={0} y={-500} z={-60} o={pop(t, T.one + 0.1) * w.k}><Mono size={30} color={C.cream} w={700} style={{letterSpacing: '.3em'}}>ONLY ONE</Mono></O>
      {frame > 0 && (
        <>
          <O x={jx} y={FLOOR - 360} z={-50} o={w.k}>
            <svg width={600} height={820} viewBox="0 0 600 820" style={{display: 'block', overflow: 'visible'}}>
              <rect x={10} y={10} width={580} height={800} rx={6} fill="none" stroke={C.orange} strokeWidth={4} strokeDasharray={2800} strokeDashoffset={2800 * (1 - frame)} />
              {[[10, 10, 1, 1], [590, 10, -1, 1], [10, 810, 1, -1], [590, 810, -1, -1]].map(([x, y, dx, dy], i) => (
                <path key={i} d={`M${x},${y + dy * 60} L${x},${y} L${x + dx * 60},${y}`} fill="none" stroke={C.cream} strokeWidth={8} opacity={frame} />
              ))}
            </svg>
          </O>
          <O x={jx + 340} y={-60} z={20} o={pop(t, T.master + 0.2) * w.k} ry={-8}>
            <Panel w={300} h={124} radius={10}>
              <div style={{padding: '18px 22px', display: 'grid', gap: 6}}>
                <div style={{fontFamily: FONT.serif, fontStyle: 'italic', fontSize: 44, color: C.cream, lineHeight: 1}}>Masterpiece</div>
                <Mono size={20}>JAKO · 2026 · CLAUDE</Mono>
              </div>
            </Panel>
          </O>
        </>
      )}
    </>
  );
};

// ---------------------------------------------------------------- 3. totally free
const Free: React.FC<R> = ({t}) => {
  const w = win(t, 'free');
  if (!w) return null;
  const e = enter(t, w.s + 0.04, 0.5);
  const under = outCubic(prog(t, T.free - 0.04, 0.35));
  return (
    <>
      {[3, 2, 1].map((i) => (
        <O key={i} x={130} y={-760} z={-80 - i * 230 + e.dz} o={e.o * w.k * (0.42 - i * 0.11)}><Big size={400} color={C.orange} depth={0}>$0</Big></O>
      ))}
      <O x={130} y={-760} z={-80 + e.dz} rx={e.rx} o={e.o * w.k}><Big size={400} depth={14}>$0</Big></O>
      <O x={130} y={-545} z={-80} o={w.k}><div style={{width: 430 * under, height: 14, borderRadius: 7, background: C.orange, boxShadow: `0 0 30px ${C.orange}`}} /></O>
      <O x={-230} y={-920} z={40} rz={-6} o={pop(t, T.free - 0.02) * w.k}>
        <div style={{border: `3px solid ${C.orange}`, borderRadius: 999, padding: '10px 30px'}}><Mono size={38} color={C.orange} w={700} style={{letterSpacing: '.25em'}}>FREE</Mono></div>
      </O>
    </>
  );
};

// ---------------------------------------------------------------- 4. here's the thing
const Thing: React.FC<R> = ({t}) => {
  const w = win(t, 'thing', 0.2);
  if (!w) return null;
  const {x, z} = jakoPos(t);
  return (
    <O x={x + 250} y={-250} z={z + 40} o={pop(t, T.thing) * w.k}>
      <Mono size={30} color={C.orange} w={700}>// here's the thing</Mono>
    </O>
  );
};

// ---------------------------------------------------------------- 5. every field needs its own skill
const Icon: React.FC<{k: string}> = ({k}) => {
  const s = {fill: 'none', stroke: C.orange, strokeWidth: 4, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const};
  return (
    <svg width={64} height={64} viewBox="0 0 64 64" style={{display: 'block'}}>
      {k === 'design' && <><path d="M8,54 C18,14 46,58 56,12" {...s} /><rect x={4} y={50} width={9} height={9} {...s} /><rect x={51} y={7} width={9} height={9} {...s} /></>}
      {k === 'video' && <><rect x={6} y={14} width={52} height={38} rx={8} {...s} /><path d="M27,24 L40,33 L27,42 Z" {...s} /></>}
      {k === 'code' && <><path d="M22,18 L8,32 L22,46 M42,18 L56,32 L42,46 M36,12 L28,52" {...s} /></>}
      {k === 'marketing' && <><path d="M8,26 L36,14 L36,50 L8,38 Z" {...s} /><path d="M14,38 L18,54 L26,54 L24,42 M44,24 Q52,32 44,40 M50,18 Q62,32 50,46" {...s} /></>}
    </svg>
  );
};
const FIELDS = [
  {k: 'design', n: '01', x: -285, y: -880, z: -80, ry: 16},
  {k: 'video', n: '02', x: 285, y: -880, z: -80, ry: -16},
  {k: 'code', n: '03', x: -285, y: -610, z: 30, ry: 18},
  {k: 'marketing', n: '04', x: 285, y: -610, z: 30, ry: -18},
];
const Fields: React.FC<R> = ({t}) => {
  const w = win(t, 'fields');
  if (!w) return null;
  return (
    <>
      {FIELDS.map((f, i) => {
        const tc = (T as any)[f.k] as number;
        const e = enter(t, tc - 0.06, 0.5);
        const own = pop(t, T.own + i * 0.07);
        const slot = pop(t, w.s + i * 0.05) * (1 - e.o) * w.k;
        return (
          <React.Fragment key={f.k}>
            <O x={f.x} y={f.y} z={f.z} ry={f.ry} o={slot}><div style={{width: 400, height: 230, borderRadius: 26, border: '2px dashed rgba(255,255,255,.22)'}} /></O>
            <O x={f.x} y={f.y + Math.sin(t * 1.6 + i) * 8} z={f.z + e.dz} ry={f.ry} rx={e.rx} o={e.o * w.k}>
              <Panel w={400} h={230} accent={own}>
                <div style={{padding: '22px 26px', display: 'grid', gap: 12}}>
                  <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                    <Icon k={f.k} />
                    {own > 0.05 && <div style={{display: 'flex', alignItems: 'center', gap: 10, opacity: own, transform: `translateX(${(1 - own) * 30}px)`}}><Check size={34} /><Mono size={22} color={C.green} w={700}>SKILL.md</Mono></div>}
                  </div>
                  <div style={{fontFamily: FONT.display, fontWeight: 800, fontSize: 56, color: C.cream, letterSpacing: '-0.03em', lineHeight: 1}}>{f.k[0].toUpperCase() + f.k.slice(1)}</div>
                  <Mono size={22}>{f.n} — {f.k}.skill</Mono>
                </div>
              </Panel>
            </O>
          </React.Fragment>
        );
      })}
    </>
  );
};

// ---------------------------------------------------------------- 6. waste hours searching
const QUERY = 'best claude skill for video editing';
const clock = (sec: number) => [3600, 60, 1].map((d) => String(Math.floor(sec / d) % (d === 3600 ? 100 : 60)).padStart(2, '0')).join(':');
const Waste: React.FC<R> = ({t}) => {
  const w = win(t, 'waste');
  if (!w) return null;
  const typed = QUERY.slice(0, Math.max(0, Math.floor((t - w.s - 0.05) / 0.035)));
  const e = enter(t, w.s, 0.4);
  const secs = 3.2 * 3600 * Math.pow(prog(t, T.waste, 2.0), 1.6);
  return (
    <>
      <O x={0} y={-950} z={-40 + e.dz} rx={e.rx} o={e.o * w.k}>
        <Panel w={880} h={104} radius={52}>
          <div style={{display: 'flex', alignItems: 'center', gap: 20, height: '100%', padding: '0 34px'}}>
            <svg width={40} height={40} viewBox="0 0 56 56"><circle cx={23} cy={23} r={16} fill="none" stroke={C.muted} strokeWidth={6} /><path d="M35,35 L50,50" stroke={C.muted} strokeWidth={7} strokeLinecap="round" /></svg>
            <Mono size={34} color={C.cream}>{typed}<span style={{opacity: Math.floor(t * 4) % 2 ? 0 : 1, color: C.orange}}>|</span></Mono>
          </div>
        </Panel>
      </O>
      {Array.from({length: 16}, (_, i) => {
        const te = enter(t, T.waste - 0.05 + i * 0.1, 0.4);
        const bad = i % 3 === 1;
        return (
          <O key={i} x={(rnd(`wx${i}`) - 0.5) * 1000} y={-830 + rnd(`wy${i}`) * 420 + Math.sin(t * 1.3 + i) * 10} z={-560 + rnd(`wz${i}`) * 640 + te.dz}
            ry={(rnd(`wr${i}`) - 0.5) * 50} rz={(rnd(`wq${i}`) - 0.5) * 16} rx={te.rx} o={te.o * w.k}>
            <Panel w={270} h={170} radius={16}>
              <div style={{height: 34, borderBottom: `2px solid ${C.line}`, display: 'flex', gap: 8, alignItems: 'center', padding: '0 14px'}}>
                {[0, 1, 2].map((d) => <span key={d} style={{width: 10, height: 10, borderRadius: '50%', background: '#4A4354'}} />)}
              </div>
              <div style={{padding: 18, display: 'grid', gap: 12}}>
                {bad ? <Mono size={30} color={C.red} w={700}>404</Mono> : <Mono size={22} color={C.muted}>no results</Mono>}
                <div style={{height: 10, width: '80%', borderRadius: 5, background: 'rgba(255,255,255,.09)'}} />
                <div style={{height: 10, width: '55%', borderRadius: 5, background: 'rgba(255,255,255,.06)'}} />
              </div>
            </Panel>
          </O>
        );
      })}
      <O x={300} y={-560} z={170} ry={-12} o={pop(t, T.hours - 0.08) * w.k}>
        <Panel w={360} h={150} accent={0.8} glow={C.red}>
          <div style={{padding: '20px 26px', display: 'grid', gap: 8}}>
            <Mono size={22} color={C.muted} w={700} style={{letterSpacing: '.2em'}}>TIME SPENT</Mono>
            <div style={{fontFamily: FONT.mono, fontWeight: 700, fontSize: 62, color: C.red, lineHeight: 1}}>{clock(secs)}</div>
          </div>
        </Panel>
      </O>
    </>
  );
};

// ---------------------------------------------------------------- 7. it scans the internet and finds skills
const LINES: [number, string, string][] = [
  [T.this - 0.02, '> find a skill for editing reels', C.cream],
  [T.search1 - 0.05, '  searching the internet...', C.muted],
  [T.scans - 0.05, '  scanning 1,000s of skills', C.muted],
  [T.internet + 0.25, '  matching your task...', C.muted],
  [T.finds - 0.04, '✓ 3 skills found', C.green],
];
const FOUND = ['motion-video-director', 'impeccable', 'ui-ux-pro-max'];
const Globe: React.FC<{t: number}> = ({t}) => {
  const R = 150;
  return (
    <svg width={2 * R + 40} height={2 * R + 40} viewBox={`${-R - 20} ${-R - 20} ${2 * R + 40} ${2 * R + 40}`} style={{display: 'block', overflow: 'visible'}}>
      <circle r={R} fill="rgba(240,122,72,.06)" stroke={C.cream} strokeOpacity={0.6} strokeWidth={2.5} />
      {Array.from({length: 6}, (_, i) => <ellipse key={i} rx={R * Math.abs(Math.cos(t * 0.9 + (i * Math.PI) / 6))} ry={R} fill="none" stroke={C.cream} strokeOpacity={0.35} strokeWidth={2} />)}
      {[-0.6, -0.3, 0, 0.3, 0.6].map((k) => <ellipse key={k} cy={k * R} rx={R * Math.sqrt(1 - k * k)} ry={R * 0.12 * Math.sqrt(1 - k * k)} fill="none" stroke={C.cream} strokeOpacity={0.3} strokeWidth={2} />)}
      {[0, 0.5].map((o) => {
        const p = ((t * 0.9 + o) % 1);
        return <circle key={o} r={R * (0.3 + p * 0.9)} fill="none" stroke={C.orange} strokeWidth={3} opacity={1 - p} />;
      })}
    </svg>
  );
};
const Scan: React.FC<R> = ({t}) => {
  const w = win(t, 'scan');
  if (!w) return null;
  const e = enter(t, w.s, 0.5);
  const back = inOutCubic(prog(t, T.exactly - 0.08, 0.4));
  const ge = enter(t, T.scans - 0.12, 0.5);
  return (
    <>
      <O x={210} y={-740} z={-40 + e.dz - back * 300} ry={-14} rx={e.rx} o={e.o * w.k * (1 - back * 0.6)}>
        <Panel w={650} h={470} accent={t > T.finds ? 0.6 : 0}>
          <div style={{height: 54, borderBottom: `2px solid ${C.line}`, display: 'flex', alignItems: 'center', gap: 10, padding: '0 20px'}}>
            {['#F05252', '#F5B83D', '#4ADE80'].map((c) => <span key={c} style={{width: 14, height: 14, borderRadius: '50%', background: c}} />)}
            <Mono size={22} style={{marginLeft: 12}}>find-skills</Mono>
          </div>
          <div style={{padding: '26px 28px', display: 'grid', gap: 18}}>
            {LINES.map(([a, text, color], i) => {
              const n = Math.floor((t - a) / 0.022);
              if (n <= 0) return null;
              return <Mono key={i} size={29} color={color} w={i === 0 || i === 4 ? 700 : 500}>{text.slice(0, n)}</Mono>;
            })}
          </div>
        </Panel>
      </O>
      <O x={-300} y={-880} z={-260 + ge.dz} o={ge.o * w.k}><Globe t={t} /></O>
      {FOUND.map((n, i) => {
        const fe = enter(t, T.exactly + 0.08 + i * 0.3, 0.45);
        return (
          <O key={n} x={200} y={-900 + i * 122} z={150 + fe.dz} ry={-10} rx={fe.rx} o={fe.o * w.k}>
            <Panel w={620} h={98} accent={0.5}>
              <div style={{display: 'flex', alignItems: 'center', gap: 20, height: '100%', padding: '0 24px'}}>
                <Check size={44} />
                <Mono size={32} color={C.cream} w={700}>{n}</Mono>
              </div>
            </Panel>
          </O>
        );
      })}
    </>
  );
};

// ---------------------------------------------------------------- 8. it's called… Find Skills
const Reveal: React.FC<R> = ({t}) => {
  const w = win(t, 'reveal');
  if (!w) return null;
  const a = enter(t, T.find0 - 0.04, 0.5);
  const b = enter(t, T.skillName - 0.04, 0.5);
  return (
    <>
      <O x={0} y={-1150} z={-60} anchor="translate(-50%,0)" o={w.k * (0.5 + 0.5 * pop(t, w.s))}>
        <div style={{width: 760, height: 1560, background: 'linear-gradient(180deg, rgba(255,214,190,.30), rgba(255,214,190,0) 85%)', clipPath: 'polygon(42% 0, 58% 0, 100% 100%, 0 100%)'}} />
      </O>
      {t < T.find0 && (
        <O x={0} y={-760} z={0} o={pop(t, w.s + 0.05)}>
          <div style={{display: 'flex', gap: 34}}>
            {[0, 1, 2].map((i) => <div key={i} style={{width: 30, height: 30, borderRadius: '50%', background: C.orange, transform: `translateY(${Math.sin(t * 13 - i * 0.9) * 22}px)`}} />)}
          </div>
        </O>
      )}
      <O x={-70} y={-890} z={-120 + a.dz} rx={a.rx} s={1 + 0.3 * (1 - a.p)} o={a.o * w.k}><Big size={300} depth={16}>Find</Big></O>
      <O x={90} y={-650} z={-40 + b.dz} rx={b.rx} s={1 + 0.3 * (1 - b.p)} o={b.o * w.k}><Big size={330} serif color={C.orange} glow="rgba(240,122,72,.6)" depth={0}>Skills</Big></O>
    </>
  );
};

// ---------------------------------------------------------------- 9. grab it online / a ready file
const ZipCard: React.FC<{t: number; status: 'prep' | 'ready' | number}> = ({t, status}) => (
  <Panel w={580} h={210} accent={status === 'ready' ? 1 : 0.15} glow={status === 'ready' ? C.green : C.orange}>
    <div style={{display: 'flex', alignItems: 'center', gap: 28, height: '100%', padding: '0 34px'}}>
      <ZipIcon size={104} />
      <div style={{display: 'grid', gap: 14}}>
        <div style={{fontFamily: FONT.display, fontWeight: 800, fontSize: 52, color: C.cream, letterSpacing: '-0.03em', lineHeight: 1}}>find-skills.zip</div>
        {status === 'prep' && <Mono size={26}>preparing{'.'.repeat(1 + (Math.floor(t * 6) % 3))}</Mono>}
        {status === 'ready' && <div style={{display: 'flex', alignItems: 'center', gap: 12}}><Check size={34} /><Mono size={26} color={C.green} w={700}>ready</Mono></div>}
        {typeof status === 'number' && (
          <div style={{display: 'grid', gap: 10}}>
            <div style={{width: 340, height: 10, borderRadius: 5, background: 'rgba(255,255,255,.1)', overflow: 'hidden'}}><div style={{width: `${status * 100}%`, height: '100%', background: status < 1 ? C.orange : C.green}} /></div>
            <Mono size={24} color={status < 1 ? C.muted : C.green} w={700}>{status < 1 ? `downloading ${Math.round(status * 100)}%` : 'downloaded ✓'}</Mono>
          </div>
        )}
      </div>
    </div>
  </Panel>
);
const FileScene: React.FC<R> = ({t}) => {
  const w = win(t, 'file', 0.05);
  if (!w) return null;
  const e = enter(t, w.s, 0.5);
  const gone = inCubic(prog(t, T.but2 - 0.02, 0.35));
  const z = enter(t, T.but2 + 0.06, 0.5);
  return (
    <>
      <O x={200 + gone * 600} y={-740} z={-60 + e.dz} ry={-16 - gone * 60} rx={e.rx} o={e.o * (1 - gone)}>
        <Panel w={640} h={430}>
          <div style={{height: 70, borderBottom: `2px solid ${C.line}`, display: 'flex', alignItems: 'center', gap: 14, padding: '0 20px'}}>
            {[0, 1, 2].map((d) => <span key={d} style={{width: 14, height: 14, borderRadius: '50%', background: '#4A4354'}} />)}
            <div style={{flex: 1, marginLeft: 10, height: 42, borderRadius: 21, background: 'rgba(255,255,255,.06)', display: 'flex', alignItems: 'center', padding: '0 18px'}}><Mono size={22} color={C.cream}>claude skills — search</Mono></div>
          </div>
          <div style={{padding: 26, display: 'grid', gap: 18}}>
            {[0, 1, 2, 3].map((i) => (
              <div key={i} style={{display: 'flex', alignItems: 'center', gap: 18, padding: '8px 12px', borderRadius: 14, border: `2px solid ${i === 1 ? C.orange : 'transparent'}`, background: i === 1 ? 'rgba(240,122,72,.1)' : 'transparent'}}>
                <span style={{width: 44, height: 44, borderRadius: 10, background: i === 1 ? C.orange : '#3A3442', flex: 'none'}} />
                <div style={{flex: 1, display: 'grid', gap: 10}}>
                  <div style={{height: 14, width: `${72 - i * 8}%`, borderRadius: 7, background: 'rgba(244,238,230,.7)'}} />
                  <div style={{height: 10, width: `${48 + i * 9}%`, borderRadius: 5, background: 'rgba(255,255,255,.12)'}} />
                </div>
              </div>
            ))}
          </div>
        </Panel>
      </O>
      <O x={190} y={-760} z={40 + z.dz} ry={30 * (1 - z.p)} o={z.o}><ZipCard t={t} status={t >= T.ready - 0.04 ? 'ready' : 'prep'} /></O>
    </>
  );
};

// ---------------------------------------------------------------- 10. download → upload → done (real screenshots)
const UP = {w: 840, iw: 1288, ih: 741};
const SK = {w: 840, iw: 1273, ih: 570};
const Install: React.FC<R> = ({t}) => {
  const w = win(t, 'install');
  if (!w) return null;
  const ph2 = T.upload - 0.06;
  const pct = clamp((t - T.download) / 0.6);
  const zipGo = inCubic(prog(t, ph2 - 0.05, 0.3));
  const k = UP.w / UP.iw, ks = SK.w / SK.iw;
  const upH = UP.ih * k, skH = SK.ih * ks;
  const card = enter(t, ph2, 0.5);
  const flip = 180 * inOutCubic(prog(t, T.skillsYour - 0.12, 0.45));
  const CX = 60, CY = -680, CZ = -40;
  // front face: drop the file in, click Upload
  const drop = {x: CX + (742 - UP.iw / 2) * k, y: CY + (268 - UP.ih / 2) * k};
  const btn = {x: CX + (297 - UP.iw / 2) * k, y: CY + (493 - UP.ih / 2) * k};
  const fp = outCubic(prog(t, T.upload + 0.02, 0.26));
  const land = prog(t, T.upload + 0.28, 0.1);
  const cp = outCubic(prog(t, T.upload + 0.16, 0.24));
  const click = T.upload + 0.42;
  const front = flip < 90;
  const hl = pop(t, T.skillsYour + 0.12);
  const done = enter(t, T.done - 0.05, 0.45);
  const row = {x: (741 - SK.iw / 2) * ks, y: (218 - SK.ih / 2) * ks, w: 870 * ks, h: 72 * ks};
  return (
    <>
      <O x={190} y={-760 - zipGo * 300} z={40 - zipGo * 300} o={(1 - zipGo) * pop(t, w.s - 0.05)}><ZipCard t={t} status={pct} /></O>
      <O x={CX} y={CY} z={CZ + card.dz} rx={card.rx} ry={20 * (1 - card.p) + flip} o={card.o * w.k}>
        <div style={{position: 'relative', width: UP.w, height: upH, transformStyle: 'preserve-3d'}}>
          <div style={{position: 'absolute', inset: 0, backfaceVisibility: 'hidden', borderRadius: 22, overflow: 'hidden', border: `2px solid ${C.line}`, boxShadow: '0 50px 100px rgba(0,0,0,.65)'}}>
            <Img src={staticFile('shot-upload.png')} style={{width: '100%', height: '100%', display: 'block'}} />
            <div style={{position: 'absolute', left: 262 * k, top: 209 * k, width: 960 * k, height: 118 * k, borderRadius: 12, border: `3px solid ${C.orange}`, background: 'rgba(240,122,72,.14)', opacity: land, boxShadow: `0 0 40px ${C.orange}`}} />
          </div>
          <div style={{position: 'absolute', left: 0, top: (upH - skH) / 2, width: SK.w, height: skH, backfaceVisibility: 'hidden', transform: 'rotateY(180deg)', borderRadius: 22, overflow: 'hidden', border: `2px solid ${C.line}`, boxShadow: '0 50px 100px rgba(0,0,0,.65)'}}>
            <Img src={staticFile('shot-skills.png')} style={{width: '100%', height: '100%', display: 'block'}} />
            <div style={{position: 'absolute', left: SK.w / 2 + row.x - row.w / 2, top: skH / 2 + row.y - row.h / 2, width: row.w, height: row.h, borderRadius: 12, border: `3px solid ${C.green}`, background: 'rgba(74,222,128,.12)', boxShadow: '0 0 34px rgba(74,222,128,.7)', opacity: clamp(hl * 2), transform: `scale(${0.85 + 0.15 * hl})`}} />
          </div>
        </div>
      </O>
      {front && t > ph2 && land < 1 && (
        <O x={lerp(460, drop.x, fp)} y={lerp(-1150, drop.y, fp)} z={lerp(260, CZ + 20, fp)} s={(0.9 - 0.4 * fp) * (1 - land)} rz={lerp(-18, 0, fp)}><ZipIcon size={110} /></O>
      )}
      {front && t > T.upload + 0.16 && (
        <O x={lerp(520, btn.x + 26, cp)} y={lerp(-420, btn.y + 26, cp)} z={CZ + 30} s={t > click && t < click + 0.1 ? 0.85 : 1} o={1 - prog(t, T.skillsYour - 0.16, 0.06)}><Cursor /></O>
      )}
      {front && t > click && t < click + 0.4 && (
        <O x={btn.x} y={btn.y} z={CZ + 25} s={1 + prog(t, click, 0.4) * 3} o={1 - prog(t, click, 0.4)}><div style={{width: 40, height: 40, borderRadius: '50%', border: `4px solid ${C.orange}`}} /></O>
      )}
      <O x={250} y={-470} z={200 + done.dz} rx={done.rx} o={done.o * w.k}>
        <div style={{display: 'flex', alignItems: 'center', gap: 22}}>
          <Check size={110} />
          <Big size={110} depth={8}>Done.</Big>
        </div>
      </O>
    </>
  );
};

// ---------------------------------------------------------------- 11. comment FIND → DM
const Avatar: React.FC<{size: number}> = ({size}) => (
  <div style={{width: size, height: size, borderRadius: '50%', overflow: 'hidden', border: `2px solid ${C.orange}`, flex: 'none', background: '#241F2B'}}
    dangerouslySetInnerHTML={{__html: M.svg(M.defs() + M.avatarScene('#241F2B', {glasses: true}), M.AVATAR_VB, `width="${size - 4}" height="${size - 4}"`)}} />
);
const Plane: React.FC<{size: number; color?: string}> = ({size, color = '#0B0A0F'}) => (
  <svg width={size} height={size} viewBox="0 0 60 60" style={{display: 'block'}}><path d="M6,28 L54,8 L40,52 L28,36 Z M28,36 L54,8" fill="none" stroke={color} strokeWidth={5} strokeLinejoin="round" strokeLinecap="round" /></svg>
);
const Cta: React.FC<R> = ({t}) => {
  const w = win(t, 'cta');
  if (!w) return null;
  const end = VO_END + 0.02;
  const out = inCubic(prog(t, end, 0.3));
  const typed = 'FIND'.slice(0, Math.max(0, Math.floor((t - T.comment - 0.02) / 0.06)));
  const sendAt = T.find1 + 0.32;
  const e = enter(t, w.s + 0.02, 0.45);
  const dm = enter(t, T.send - 0.08, 0.45);
  const sp = prog(t, sendAt, 0.55);
  const a = enter(t, end + 0.05, 0.5);
  const b = enter(t, end + 0.2, 0.5);
  return (
    <>
      <O x={0} y={-900 - out * 500} z={0 + e.dz} rx={e.rx} o={e.o * (1 - out)}>
        <Panel w={900} h={130} radius={65} accent={0.3}>
          <div style={{display: 'flex', alignItems: 'center', gap: 20, height: '100%', padding: '0 22px'}}>
            <Avatar size={88} />
            <div style={{flex: 1, height: 84, borderRadius: 42, background: 'rgba(255,255,255,.06)', display: 'flex', alignItems: 'center', padding: '0 28px', fontFamily: FONT.display, fontWeight: 800, fontSize: 50, color: C.cream}}>
              {t < sendAt ? typed : ''}<span style={{fontFamily: FONT.mono, fontWeight: 500, color: C.orange, opacity: Math.floor(t * 4) % 2 ? 0 : 1}}>|</span>
              {t < sendAt && !typed && <span style={{fontFamily: FONT.display, fontWeight: 500, fontSize: 34, color: C.muted}}>Add a comment…</span>}
            </div>
            <div style={{width: 84, height: 84, borderRadius: '50%', background: C.orange, display: 'grid', placeItems: 'center', flex: 'none', transform: `scale(${t > sendAt && t < sendAt + 0.12 ? 0.85 : 1})`}}><Plane size={44} /></div>
          </div>
        </Panel>
      </O>
      {sp > 0 && sp < 1 && (
        <O x={lerp(400, -60, sp)} y={-900 + 240 * sp - Math.sin(sp * Math.PI) * 200} z={120} rz={-20 + 60 * sp} o={1 - prog(t, sendAt + 0.4, 0.15)}><Plane size={70} color={C.orange} /></O>
      )}
      <O x={0} y={-690 - out * 500} z={80 + dm.dz} rx={dm.rx} o={dm.o * (1 - out)}>
        <Panel w={860} h={140} accent={0.7} glow={C.green}>
          <div style={{display: 'flex', alignItems: 'center', gap: 24, height: '100%', padding: '0 28px'}}>
            <ZipIcon size={62} />
            <div style={{flex: 1, display: 'grid', gap: 8}}>
              <Mono size={24}>@jako.frames sent you</Mono>
              <div style={{fontFamily: FONT.display, fontWeight: 800, fontSize: 46, color: C.cream, letterSpacing: '-0.03em', lineHeight: 1}}>find-skills.zip</div>
            </div>
            <Check size={54} />
          </div>
        </Panel>
      </O>
      <O x={0} y={-930} z={-60 + a.dz} rx={a.rx} o={a.o}><Big size={170} depth={12}>Comment</Big></O>
      <O x={0} y={-690} z={20 + b.dz} rx={b.rx} s={1 + 0.2 * (1 - b.p)} o={b.o}><Big size={300} serif color={C.orange} glow="rgba(240,122,72,.6)" depth={0}>“FIND”</Big></O>
      <O x={360} y={-330 + Math.abs(Math.sin(t * 6)) * 30} z={120} rz={-35} o={pop(t, end + 0.4)}>
        <svg width={90} height={130} viewBox="0 0 90 130"><path d="M45,8 L45,112 M12,80 L45,116 L78,80" fill="none" stroke={C.orange} strokeWidth={9} strokeLinecap="round" strokeLinejoin="round" /></svg>
      </O>
    </>
  );
};

export const WorldScenes: React.FC<R> = ({t}) => (
  <>
    <Hook t={t} /><One t={t} /><Free t={t} /><Thing t={t} /><Fields t={t} /><Waste t={t} />
    <Scan t={t} /><Reveal t={t} /><FileScene t={t} /><Install t={t} /><Cta t={t} />
  </>
);
