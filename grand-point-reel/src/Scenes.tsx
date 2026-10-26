import React from 'react';
import data from './data.json';
import {C, FONT, outBack, outExpo} from './theme';
import {Check, Glass, Headline, Kicker, p, useT} from './ui';

const Q = data.cues;
const L = data.lines;
const TOP = 1215;
const RED = '#E5484D';

const Bubble: React.FC<{at: number; side: 'l' | 'r'; children: React.ReactNode; struck?: number}> = ({at, side, children, struck = 0}) => {
  const t = useT();
  const k = outBack(p(t, at, 0.45));
  const mine = side === 'r';
  return (
    <div style={{display: 'flex', justifyContent: mine ? 'flex-end' : 'flex-start'}}>
      <div
        style={{
          position: 'relative',
          maxWidth: '82%',
          padding: '20px 28px',
          borderRadius: 30,
          borderBottomRightRadius: mine ? 8 : 30,
          borderBottomLeftRadius: mine ? 30 : 8,
          background: mine ? `linear-gradient(135deg, ${C.accent}, ${C.gold})` : 'rgba(10,11,18,0.06)',
          color: mine ? '#fff' : C.text,
          fontSize: 38,
          fontWeight: 700,
          opacity: Math.min(1, k * 1.5),
          transform: `scale(${0.6 + 0.4 * k})`,
          transformOrigin: mine ? 'right bottom' : 'left bottom',
        }}
      >
        {children}
        {/* myth strike */}
        <div
          style={{
            position: 'absolute',
            left: 18,
            top: '50%',
            height: 6,
            borderRadius: 3,
            width: `${struck * 90}%`,
            background: RED,
            transform: 'rotate(-4deg)',
          }}
        />
      </div>
    </div>
  );
};

const Typing: React.FC<{from: number; to: number}> = ({from, to}) => {
  const t = useT();
  if (t < from || t > to) return null;
  return (
    <div style={{display: 'flex', gap: 10, padding: '22px 28px', borderRadius: 30, background: 'rgba(10,11,18,0.06)', width: 'fit-content'}}>
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          style={{
            width: 14,
            height: 14,
            borderRadius: 7,
            background: C.muted,
            transform: `translateY(${Math.sin(t * 12 - i * 0.9) * 5}px)`,
          }}
        />
      ))}
    </div>
  );
};

const Hook: React.FC = () => {
  const t = useT();
  const strike = outExpo(p(t, Q.myth + 0.05, 0.3));
  return (
    <Glass top={TOP} from={Q.hook - 0.05} to={L[2].s - 0.02}>
      <Kicker at={Q.hook}>ЧАСТЫЙ ВОПРОС</Kicker>
      <div style={{height: 24}} />
      <div style={{display: 'flex', flexDirection: 'column', gap: 16}}>
        <Bubble at={Q.hook + 0.25} side="r">Кредитов раньше не было</Bubble>
        <Typing from={Q.credit + 0.1} to={Q.approve - 0.05} />
        <Bubble at={Q.approve - 0.05} side="r" struck={strike}>
          Значит, банк одобрит?
        </Bubble>
      </div>
    </Glass>
  );
};

// full-frame stamp on "Это миф."
export const MythStamp: React.FC = () => {
  const t = useT();
  const a = Q.myth;
  if (t < a - 0.05 || t > L[2].s) return null;
  const slam = outExpo(p(t, a, 0.22));
  const out = outExpo(p(t, L[2].s - 0.2, 0.2));
  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        top: 600,
        display: 'flex',
        justifyContent: 'center',
        opacity: Math.min(1, slam * 2) * (1 - out),
        transform: `scale(${2.4 - 1.4 * slam}) rotate(-9deg)`,
        fontFamily: FONT,
      }}
    >
      <div
        style={{
          padding: '18px 54px',
          border: `12px solid ${RED}`,
          borderRadius: 26,
          color: RED,
          fontSize: 190,
          fontWeight: 800,
          letterSpacing: 10,
          lineHeight: 1,
          background: 'rgba(255,255,255,0.9)',
          boxShadow: '0 30px 80px rgba(0,0,0,0.4)',
        }}
      >
        МИФ
      </div>
    </div>
  );
};

const Tile: React.FC<{at: number; icon: React.ReactNode; label: string}> = ({at, icon, label}) => {
  const t = useT();
  const k = outBack(p(t, at, 0.45));
  return (
    <div
      style={{
        flex: 1,
        padding: '24px 18px',
        borderRadius: 24,
        background: 'rgba(10,11,18,0.035)',
        border: `1.5px solid ${C.line}`,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 14,
        opacity: Math.min(1, k * 1.5),
        transform: `translateY(${(1 - k) * 40}px) scale(${0.8 + 0.2 * k})`,
      }}
    >
      <div
        style={{
          width: 76,
          height: 76,
          borderRadius: 22,
          background: `linear-gradient(135deg, ${C.accent}, ${C.gold})`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontSize: 40,
          fontWeight: 800,
        }}
      >
        {icon}
      </div>
      <div style={{fontSize: 27, fontWeight: 700, textAlign: 'center', lineHeight: 1.2}}>{label}</div>
    </div>
  );
};

const ListIcon = () => (
  <svg width={40} height={40} viewBox="0 0 40 40">
    {[10, 20, 30].map((y) => (
      <g key={y}>
        <circle cx={8} cy={y} r={3} fill="#fff" />
        <rect x={15} y={y - 2.5} width={20} height={5} rx={2.5} fill="#fff" />
      </g>
    ))}
  </svg>
);

const Bank: React.FC = () => (
  <Glass top={TOP} from={Q.bank - 0.05} to={L[3].s - 0.02}>
    <Kicker at={Q.bank}>ФАКТ №1</Kicker>
    <div style={{height: 10}} />
    <Headline text="Банк оценивает" at={Q.bank} size={64} />
    <div style={{height: 26}} />
    <div style={{display: 'flex', gap: 18}}>
      <Tile at={Q.income} icon="₸" label="Доход" />
      <Tile at={Q.oblig} icon={<ListIcon />} label="Обязательства" />
      <Tile at={Q.factors} icon="•••" label="Другие факторы" />
    </div>
  </Glass>
);

const Toggle: React.FC<{off: number}> = ({off}) => (
  <div style={{width: 96, height: 54, borderRadius: 27, background: off > 0.5 ? 'rgba(10,11,18,0.15)' : C.accent, position: 'relative', flex: 'none'}}>
    <div
      style={{
        position: 'absolute',
        top: 5,
        left: 5 + 42 * (1 - off),
        width: 44,
        height: 44,
        borderRadius: 22,
        background: '#fff',
        boxShadow: '0 3px 8px rgba(0,0,0,0.2)',
      }}
    />
  </div>
);

const NoHistory: React.FC = () => {
  const t = useT();
  const off = outExpo(p(t, Q.noKi + 0.3, 0.35));
  const badge = outBack(p(t, Q.guarantee, 0.45));
  const rowStyle: React.CSSProperties = {display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 20};
  return (
    <Glass top={TOP} from={L[3].s - 0.05} to={L[4].s - 0.02}>
      <Kicker at={L[3].s}>ФАКТ №2</Kicker>
      <div style={{height: 26}} />
      <div style={rowStyle}>
        <span style={{fontSize: 38, fontWeight: 700}}>Кредитная история</span>
        <Toggle off={off} />
      </div>
      <div style={{height: 1.5, background: C.line, margin: '26px 0'}} />
      <div style={rowStyle}>
        <span style={{fontSize: 38, fontWeight: 700}}>Одобрение</span>
        <span
          style={{
            padding: '12px 22px',
            borderRadius: 16,
            background: 'rgba(229,72,77,0.12)',
            color: RED,
            fontSize: 30,
            fontWeight: 800,
            opacity: Math.min(1, badge * 1.5),
            transform: `scale(${0.6 + 0.4 * badge})`,
            transformOrigin: 'right center',
          }}
        >
          Не гарантировано
        </span>
      </div>
    </Glass>
  );
};

const Help: React.FC = () => {
  const t = useT();
  const q = outBack(p(t, Q.help + 0.2, 0.5));
  return (
    <Glass top={TOP} from={Q.help - 0.05} to={L[6].s - 0.02}>
      <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
        <Kicker at={Q.help}>РЕШЕНИЕ</Kicker>
        <div
          style={{
            width: 64,
            height: 64,
            borderRadius: 32,
            background: C.text,
            color: '#fff',
            fontSize: 40,
            fontWeight: 800,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transform: `scale(${q}) rotate(${(1 - q) * -90}deg)`,
          }}
        >
          ?
        </div>
      </div>
      <div style={{height: 22}} />
      <div style={{display: 'flex', flexDirection: 'column', gap: 22}}>
        <Check at={Q.form}>
          <span>
            <span style={{color: C.accent}}>01</span> Грамотная анкета
          </span>
        </Check>
        <Check at={Q.tactic}>
          <span>
            <span style={{color: C.accent}}>02</span> Продуманная тактика
          </span>
        </Check>
      </div>
    </Glass>
  );
};

const Cta: React.FC = () => {
  const t = useT();
  const k = outBack(p(t, Q.us + 0.35, 0.45));
  const press = Q.brand;
  const tap = t > press && t < press + 0.2 ? 0.95 : 1;
  const ripple = p(t, press, 0.6);
  return (
    <Glass top={TOP} from={L[6].s - 0.05} to={data.cutDur + 1}>
      <Kicker at={L[6].s}>ПОМОЖЕМ МЫ</Kicker>
      <div style={{height: 14}} />
      <Headline text="С анкетой и тактикой" at={L[6].s} size={48} />
      <div style={{height: 26}} />
      <div
        style={{
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '26px 34px',
          borderRadius: 26,
          background: C.text,
          color: '#fff',
          fontSize: 42,
          fontWeight: 800,
          opacity: Math.min(1, k),
          transform: `scale(${(0.85 + 0.15 * k) * tap})`,
          boxShadow: '0 20px 50px rgba(0,0,0,0.3)',
          overflow: 'hidden',
        }}
      >
        <span>
          Elite <span style={{color: C.gold}}>Finance</span>
        </span>
        <span style={{color: C.gold, fontSize: 46}}>→</span>
        <div
          style={{
            position: 'absolute',
            left: '80%',
            top: '50%',
            width: 600 * ripple,
            height: 600 * ripple,
            marginLeft: -300 * ripple,
            marginTop: -300 * ripple,
            borderRadius: '50%',
            background: 'rgba(242,169,59,0.35)',
            opacity: 1 - ripple,
          }}
        />
      </div>
    </Glass>
  );
};

export const Scenes: React.FC = () => (
  <>
    <Hook />
    <Bank />
    <NoHistory />
    <Help />
    <Cta />
  </>
);
