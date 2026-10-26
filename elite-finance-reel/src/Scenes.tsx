import React from 'react';
import data from './data.json';
import {C, outBack, outExpo} from './theme';
import {Bar, Check, Count, Divider, Glass, Headline, HouseIcon, Kicker, Pin, Stat, p, useT} from './ui';

const Q = data.cues;
const TOP = 1215; // below the chin; captions sit between face and card
const row: React.CSSProperties = {display: 'flex', gap: 60, alignItems: 'flex-start'};
const money = (n: number) => Math.round(n).toLocaleString('ru-RU').replace(/ /g, ' ');

const Title: React.FC = () => (
  <Glass top={TOP} from={Q.title - 0.1} to={Q.p725 - 0.05}>
    <div style={{display: 'flex', alignItems: 'center', gap: 34}}>
      <HouseIcon at={Q.title} />
      <div>
        <Kicker at={Q.title + 0.1}>ҚАЗАҚСТАН · 2026</Kicker>
        <div style={{height: 14}} />
        <Headline text="Ипотекалық" at={Q.title + 0.1} size={70} />
        <Headline text="бағдарламалар" at={Q.title + 0.35} size={70} color={C.accent} />
      </div>
    </div>
  </Glass>
);

const P725: React.FC = () => {
  const t = useT();
  // stats give way to the requirements checklist
  const swap = outExpo(p(t, Q.limit - 0.2, 0.5));
  return (
    <Glass top={TOP} from={Q.p725 - 0.1} to={Q.nauryz - 0.05}>
      <Kicker at={Q.p725}>БАҒДАРЛАМА №1</Kicker>
      <div style={{height: 12}} />
      <Headline text="«7-20-25»" at={Q.p725} size={96} color={C.accent} />
      <Divider at={Q.p725 + 0.3} />
      <div style={{position: 'relative', height: 200}}>
        <div style={{...row, position: 'absolute', inset: 0, opacity: 1 - swap, transform: `translateX(${-swap * 80}px)`}}>
          <Stat at={Q.down20} value={<>≥<Count to={20} at={Q.down20} />%</>} label="Бастапқы жарна" />
          <Stat at={Q.years25} value={<><Count to={25} at={Q.years25} /> жыл</>} label="Мерзім · дейін" accent={C.text} />
        </div>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            gap: 26,
            opacity: swap,
            transform: `translateX(${(1 - swap) * 80}px)`,
          }}
        >
          <Check at={Q.limit}>Баспана құнына лимит</Check>
          <Check at={Q.income}>Расталған тұрақты табыс</Check>
          <Check at={Q.match}>Бағдарламаға сәйкестік</Check>
        </div>
      </div>
    </Glass>
  );
};

const Column: React.FC<{at: number; who: string; rate: number; rateAt: number; down: number; downAt: number}> = ({
  at,
  who,
  rate,
  rateAt,
  down,
  downAt,
}) => {
  const t = useT();
  const k = outExpo(p(t, at, 0.5));
  return (
    <div
      style={{
        flex: 1,
        padding: '26px 28px',
        borderRadius: 24,
        background: 'rgba(10,11,18,0.035)',
        border: `1.5px solid ${C.line}`,
        opacity: k,
        transform: `translateY(${(1 - k) * 40}px)`,
      }}
    >
      <div style={{fontSize: 25, fontWeight: 600, color: C.muted, height: 64, lineHeight: 1.25}}>{who}</div>
      <Stat at={rateAt} value={<><Count to={rate} at={rateAt} />%</>} label="жылдық" size={88} />
      <div style={{height: 26}} />
      <div style={{fontSize: 25, fontWeight: 600, color: C.muted, marginBottom: 12}}>
        Жарна <span style={{color: C.text, fontWeight: 800}}><Count to={down} at={downAt} />%</span>
      </div>
      <Bar at={downAt} frac={down / 100} height={12} />
    </div>
  );
};

const Nauryz: React.FC = () => (
  <Glass top={TOP - 40} from={Q.nauryz - 0.1} to={Q.deposit - 0.05}>
    <Kicker at={Q.nauryz}>БАҒДАРЛАМА №2</Kicker>
    <div style={{height: 12}} />
    <Headline text="«Наурыз»" at={Q.nauryz} size={88} color={C.accent} />
    <div style={{height: 26}} />
    <div style={{display: 'flex', gap: 22}}>
      <Column at={Q.nauryzVuln} who="Әлеуметтік осал топтар" rate={7} rateAt={Q.nauryz7} down={10} downAt={Q.nauryz10} />
      <Column at={Q.nauryzOther} who="Басқа қатысушылар" rate={9} rateAt={Q.nauryz9} down={20} downAt={Q.nauryz20} />
    </div>
  </Glass>
);

const Deposit: React.FC = () => {
  const t = useT();
  const yearsK = outExpo(p(t, Q.years19, 0.5));
  return (
    <Glass top={TOP} from={Q.deposit - 0.1} to={Q.cities - 0.05}>
      <Kicker at={Q.deposit}>«НАУРЫЗ» · ШАРТТАРЫ</Kicker>
      <div style={{height: 22}} />
      <div style={{fontSize: 28, fontWeight: 600, color: C.muted}}>Депозит шотында міндетті түрде</div>
      <div style={{fontSize: 96, fontWeight: 800, color: C.accent, letterSpacing: -2, lineHeight: 1.1}}>
        <Count to={2000000} at={Q.deposit2m} dur={1.1} fmt={money} /> ₸
      </div>
      <Divider at={Q.years19 - 0.1} />
      <div style={{opacity: yearsK, transform: `translateY(${(1 - yearsK) * 30}px)`}}>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 16}}>
          <span style={{fontSize: 30, fontWeight: 600, color: C.muted}}>Мерзімі</span>
          <span style={{fontSize: 56, fontWeight: 800}}>
            <Count to={19} at={Q.years19} /> жыл
          </span>
        </div>
        <Bar at={Q.years19} frac={1} height={12} />
      </div>
    </Glass>
  );
};

const Cities: React.FC = () => {
  const City: React.FC<{at: number; name: string; amount: number; amountAt: number}> = ({at, name, amount, amountAt}) => {
    const t = useT();
    const k = outExpo(p(t, at, 0.5));
    const pin = outBack(p(t, at, 0.5));
    return (
      <div style={{opacity: k, transform: `translateX(${(1 - k) * 40}px)`}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16}}>
          <div style={{transform: `translateY(${(1 - pin) * -30}px)`}}>
            <Pin size={44} />
          </div>
          <span style={{fontSize: 36, fontWeight: 700, flex: 1}}>{name}</span>
          <span style={{fontSize: 46, fontWeight: 800, color: C.accent}}>
            <Count to={amount} at={amountAt} /> млн ₸
          </span>
        </div>
        <Bar at={amountAt} frac={amount / 36} height={14} />
      </div>
    );
  };
  return (
    <Glass top={TOP} from={Q.cities - 0.1} to={Q.otau - 0.05}>
      <Kicker at={Q.cities}>БАСПАНА ҚҰНЫ · ДЕЙІН</Kicker>
      <div style={{height: 34}} />
      <City at={Q.cities} name="Астана · Алматы" amount={36} amountAt={Q.city36} />
      <div style={{height: 40}} />
      <City at={Q.city30 - 0.9} name="Басқа қалалар" amount={30} amountAt={Q.city30} />
    </Glass>
  );
};

const Otau: React.FC = () => {
  const t = useT();
  const same = outBack(p(t, Q.otau + 1.2, 0.5));
  return (
    <Glass top={TOP - 20} from={Q.otau - 0.1} to={Q.savings - 0.05}>
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
        <Kicker at={Q.otau}>БАҒДАРЛАМА №3</Kicker>
        <div
          style={{
            fontSize: 24,
            fontWeight: 700,
            padding: '10px 20px',
            borderRadius: 40,
            border: `1.5px solid ${C.accent}`,
            color: C.accent,
            opacity: Math.min(1, same),
            transform: `scale(${same})`,
          }}
        >
          ≈ «Наурыз» секілді
        </div>
      </div>
      <div style={{height: 12}} />
      <Headline text="«Отау»" at={Q.otau} size={88} color={C.accent} />
      <Divider at={Q.otau + 0.4} />
      <div style={row}>
        <Stat at={Q.otauRates} value={<><Count to={7} at={Q.otauRates} />%</>} label="Осал топтар" size={84} />
        <Stat at={Q.otau9} value={<><Count to={9} at={Q.otau9} />%</>} label="Басқалар" size={84} accent={C.text} />
        <Stat at={Q.otau20} value={<><Count to={20} at={Q.otau20} />%</>} label="Жарна · бәріне" size={84} />
      </div>
    </Glass>
  );
};

const Savings: React.FC = () => {
  const t = useT();
  const fill = outExpo(p(t, Q.savings50 - 0.2, 1.2)) * 0.62;
  const down = outBack(p(t, Q.savingsDown, 0.5));
  const R = 92;
  const L = 2 * Math.PI * R;
  return (
    <Glass top={TOP} from={Q.savings - 0.1} to={Q.cta - 0.05}>
      <Kicker at={Q.savings}>«ОТАУ» · ЖЕҢІЛДІК</Kicker>
      <div style={{height: 26}} />
      <div style={{display: 'flex', alignItems: 'center', gap: 44}}>
        <svg width={220} height={220} viewBox="0 0 220 220" style={{flex: 'none'}}>
          <circle cx={110} cy={110} r={R} fill="none" stroke={C.line} strokeWidth={16} />
          <circle
            cx={110}
            cy={110}
            r={R}
            fill="none"
            stroke={C.accent}
            strokeWidth={16}
            strokeLinecap="round"
            strokeDasharray={L}
            strokeDashoffset={L * (1 - fill)}
            transform="rotate(-90 110 110)"
          />
          {/* 50% mark */}
          <line x1={110} y1={110 + R - 14} x2={110} y2={110 + R + 14} stroke={C.text} strokeWidth={3} />
          <text x={110} y={124} textAnchor="middle" fontFamily="MontserratLocal" fontWeight={800} fontSize={46} fill={C.text}>
            {fill >= 0.5 ? '50%+' : `${Math.round(fill * 100)}%`}
          </text>
        </svg>
        <div>
          <div style={{fontSize: 30, fontWeight: 600, color: C.muted, lineHeight: 1.3}}>Жинақ үлесі</div>
          <div style={{fontSize: 52, fontWeight: 800, lineHeight: 1.1}}>
            50%-дан <span style={{color: C.accent}}>асса</span>
          </div>
          <div
            style={{
              marginTop: 22,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 14,
              padding: '14px 24px',
              borderRadius: 18,
              background: 'rgba(242,169,59,0.14)',
              border: `1.5px solid ${C.accent}`,
              fontSize: 30,
              fontWeight: 800,
              color: C.accent,
              opacity: Math.min(1, down),
              transform: `scale(${0.8 + 0.2 * down})`,
              transformOrigin: 'left center',
            }}
          >
            <span style={{display: 'inline-block', transform: `translateY(${Math.sin(t * 6) * 3}px)`}}>↓</span> Мөлшерлеме төмендейді
          </div>
        </div>
      </div>
    </Glass>
  );
};

const Cta: React.FC = () => {
  const t = useT();
  const k = outBack(p(t, Q.ctaBrand - 0.2, 0.55));
  const press = Q.ctaBrand + 1.0;
  const tap = t > press && t < press + 0.25 ? 0.95 : 1;
  const ripple = p(t, press, 0.6);
  return (
    <>
      <Glass top={TOP} from={Q.cta - 0.1} to={data.cutDur + 1}>
        <Kicker at={Q.cta}>КӨПТЕГЕН БАСҚА БАҒДАРЛАМАЛАР</Kicker>
        <div style={{height: 18}} />
        <div style={{fontSize: 50, fontWeight: 800, lineHeight: 1.15}}>
          Бас қатырғыңыз <span style={{color: C.accent}}>келмесе?</span>
        </div>
        <div style={{height: 30}} />
        <div
          style={{
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '26px 34px',
            borderRadius: 26,
            background: `linear-gradient(90deg, ${C.accent}, ${C.accentHi})`,
            color: C.ink,
            fontSize: 40,
            fontWeight: 800,
            opacity: Math.min(1, k),
            transform: `scale(${(0.85 + 0.15 * k) * tap})`,
            boxShadow: '0 20px 50px rgba(242,169,59,0.35)',
            overflow: 'hidden',
          }}
        >
          <span>Elite Finance-ке келіңіз</span>
          <span style={{fontSize: 46}}>→</span>
          <div
            style={{
              position: 'absolute',
              left: '72%',
              top: '50%',
              width: 600 * ripple,
              height: 600 * ripple,
              marginLeft: -300 * ripple,
              marginTop: -300 * ripple,
              borderRadius: '50%',
              background: 'rgba(255,255,255,0.35)',
              opacity: 1 - ripple,
            }}
          />
        </div>
      </Glass>
    </>
  );
};

export const Scenes: React.FC = () => (
  <>
    <Title />
    <P725 />
    <Nauryz />
    <Deposit />
    <Cities />
    <Otau />
    <Savings />
    <Cta />
  </>
);
