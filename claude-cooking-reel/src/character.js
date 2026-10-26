// Mini Me v2 — one source of truth for the character.
// Pure functions that return SVG markup; works in the browser (window.MiniMe) and in Node (module.exports).
(function (root) {
  'use strict';

  const W = 400, H = 500, SCALE = 4;

  const C = {
    line: '#2a1517',
    skin: '#f6e3d3', skinShade: '#eacab4',
    blush: '#f2a39b', blushHatch: '#d9776e', mouth: '#9c3b3b',
    hair: '#2a1a17', strand: '#efe6dc',
    jersey: '#f2ece0', maroon: '#8e1f35', navy: '#1f2c6b', gold: '#f0bf2e', red: '#c8102e',
    denimDark: '#1f1c1e', denimMid: '#5a5658', denimLine: '#8d8789',
    shoe: '#fbfaf7', mesh: '#c3c6cc',
    watch: '#c9ced6', lcd: '#a9ba8f',
    shades: '#141113', bud: '#ffffff',
  };
  const SW = 4.5;
  const line = (w = SW) => `stroke="${C.line}" stroke-width="${w}" stroke-linejoin="round" stroke-linecap="round"`;

  // Pivot points in canvas units (400x500). Exported PNGs are SCALE x bigger.
  const PIVOT = {
    head: [200, 262], arm_left: [146, 290], arm_right: [254, 290],
    leg_left: [174, 388], leg_right: [226, 388], torso: [200, 392],
  };

  // ---------- shapes ----------
  const TORSO = 'M146,290 Q148,277 168,275 L232,275 Q252,277 254,290 L262,384 Q262,393 252,394 Q200,400 148,394 Q138,393 138,384 Z';
  const FACE = 'M112,165 C110,232 150,268 200,268 C250,268 290,232 288,165 C286,110 250,96 200,96 C150,96 114,110 112,165 Z';
  // Two looks share everything except the head:
  //   medium — fringe to eye level, sides over the top of small ears
  //   long   — the first version: curtains fall past the cheeks, nape strands, bigger ears, earbud
  const HAIR_LONG = [
    'M106,192 C90,138 104,86 150,60 C178,44 222,42 250,56 C300,78 312,134 294,192',
    'Q292,212 278,216 Q270,204 266,184 Q264,196 254,200 Q250,182 244,168 Q242,178 232,180 Q228,146 202,120',
    'Q200,126 198,120 Q172,146 168,180 Q158,178 156,168 Q150,182 146,200 Q136,196 134,184 Q130,204 122,216',
    'Q108,212 106,192 Z',
  ].join(' ');
  const HAIR_BACK_LONG = 'M106,186 C92,138 104,86 150,60 C178,44 232,40 262,56 C302,78 310,132 294,186 C298,228 266,258 230,266 L221,256 L211,268 L200,257 L189,268 L179,256 L170,266 C134,258 102,228 106,186 Z';
  const NAPE_LONG = 'M112,186 Q104,226 116,252 L124,240 L128,258 L136,244 L144,256 L150,236 Z M288,186 Q296,226 284,252 L276,240 L272,258 L264,244 L256,256 L250,236 Z';
  const HAIR = [
    'M106,200 C90,140 104,86 150,60 C178,44 222,42 250,56 C300,78 310,140 294,200',
    'Q290,212 280,210 Q276,196 268,186 Q264,198 256,202 Q252,184 244,172 Q240,182 230,184 Q226,150 202,122',
    'Q200,128 198,122 Q174,150 170,184 Q160,182 156,172 Q148,184 144,202 Q136,198 132,186 Q124,196 120,210',
    'Q110,212 106,200 Z',
  ].join(' ');
  const HAIR_BACK = 'M106,196 C92,138 104,86 150,60 C178,44 232,40 262,56 C302,78 310,138 294,196 C294,226 266,248 232,252 L218,246 L208,254 L200,248 L192,254 L182,246 L168,252 C134,248 106,226 106,196 Z';
  const AHOGE = 'M197,48 Q193,34 182,31 M201,48 Q207,33 218,29';
  const SLEEVE = 'M-17,-6 Q-17,-19 0,-19 Q17,-19 17,-6 L19,30 L-19,30 Z';
  // very wide, stacked baggy leg
  const PANT = 'M-22,-14 L22,-14 L33,68 Q34,76 25,76 L-25,76 Q-34,76 -33,68 Z';
  const SHOE = 'M-30,80 Q-30,64 -12,64 L18,64 Q38,64 38,80 L38,86 Q38,97 28,97 L-22,97 Q-30,97 -30,89 Z';
  const SHADES = 'M126,197 Q128,189 140,189 L188,191 Q200,195 212,191 L260,189 Q272,189 274,197 L272,212 Q266,226 242,226 Q220,226 210,211 Q200,203 190,211 Q180,226 158,226 Q134,226 128,212 Z';

  function defs() {
    return `<defs>
  <filter id="ink" x="-5%" y="-5%" width="110%" height="110%">
    <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="2" seed="4" result="w"/>
    <feDisplacementMap in="SourceGraphic" in2="w" scale="1.8" xChannelSelector="R" yChannelSelector="G"/>
  </filter>
  <filter id="paper" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB">
    <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="5" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 -1.2 0.6" result="s"/>
    <feComposite in="s" in2="SourceGraphic" operator="in" result="si"/>
    <feMerge><feMergeNode in="SourceGraphic"/><feMergeNode in="si"/></feMerge>
  </filter>
  <filter id="soft" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="2.4"/></filter>
  <linearGradient id="denim" x1="0" x2="1" y1="0" y2="0">
    <stop offset="0" stop-color="${C.denimDark}"/><stop offset=".48" stop-color="${C.denimMid}"/><stop offset="1" stop-color="${C.denimDark}"/>
  </linearGradient>
  <linearGradient id="denimV" x1="0" x2="0" y1="0" y2="1">
    <stop offset="0" stop-color="#000" stop-opacity=".25"/><stop offset=".35" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".4"/>
  </linearGradient>
  <clipPath id="faceClip"><path d="${FACE}"/></clipPath>
  <clipPath id="torsoClip"><path d="${TORSO}"/></clipPath>
  <clipPath id="sleeveClip"><path d="${SLEEVE}"/></clipPath>
</defs>`;
  }

  // ---------- body parts ----------
  function legPart([px, py], angle = 0, mirror = false, lift = 0) {
    return `<g transform="translate(${px},${py + lift}) rotate(${angle})"><g transform="scale(${mirror ? -1 : 1},1)">
      <path d="${SHOE}" fill="${C.shoe}" ${line()}/>
      <path d="M20,76 L32,77 L35,86 L20,86 Z" fill="${C.mesh}" ${line(2)}/>
      <path d="M-6,86 Q5,75 16,86" fill="none" stroke="${C.navy}" stroke-width="4.5" stroke-linecap="round"/>
      <path d="M-30,88 L38,88 L38,89 Q38,97 28,97 L-22,97 Q-30,97 -30,90 Z" fill="${C.navy}"/>
      <path d="M-30,88 L38,88" fill="none" ${line(3)}/>
      <path d="${SHOE}" fill="none" ${line()}/>
      <path d="${PANT}" fill="url(#denim)"/>
      <path d="${PANT}" fill="url(#denimV)" ${line()}/>
      <path d="M-14,6 Q-6,10 3,5 M-12,16 Q-4,19 5,15 M-12,32 Q-2,36 9,30" fill="none" stroke="${C.denimLine}" stroke-opacity=".7" stroke-width="2" stroke-linecap="round"/>
      <path d="M-28,50 Q-14,45 0,50 Q14,55 30,49 M-31,61 Q-15,57 2,62 Q16,66 32,60" fill="none" stroke="${C.denimLine}" stroke-opacity=".6" stroke-width="2" stroke-linecap="round"/>
    </g></g>`;
  }

  function armPart([px, py], angle, watch = false) {
    return `<g transform="translate(${px},${py}) rotate(${angle})">
      <rect x="-8.5" y="18" width="17" height="46" rx="8" fill="${C.skin}" ${line()}/>
      <circle cx="0" cy="68" r="11.5" fill="${C.skin}" ${line()}/>
      ${watch ? `<rect x="-10.5" y="49" width="21" height="10" rx="2.5" fill="${C.watch}" ${line(2.5)}/>
      <rect x="-5.5" y="50.8" width="11" height="6.4" rx="1" fill="${C.lcd}" stroke="${C.line}" stroke-width="1.4"/>` : ''}
      <path d="${SLEEVE}" fill="${C.jersey}"/>
      <g clip-path="url(#sleeveClip)">
        <rect x="-22" y="21" width="44" height="5" fill="${C.maroon}"/>
        <rect x="-22" y="26" width="44" height="5" fill="${C.navy}"/>
      </g>
      <path d="${SLEEVE}" fill="none" ${line()}/>
    </g>`;
  }

  function crest() {
    return `<g transform="translate(225,318)">
      <path d="M-9,-11 L9,-11 L9,1 Q9,9 0,13 Q-9,9 -9,1 Z" fill="${C.navy}"/>
      <path d="M-9,-11 L0,-11 L0,-3 L-9,-3 Z" fill="#fff"/>
      <path d="M-5.5,-11 L-3.5,-11 L-3.5,-3 L-5.5,-3 Z M-9,-8 L0,-8 L0,-6 L-9,-6 Z" fill="${C.red}"/>
      <path d="M0,-11 L9,-11 L9,-3 L0,-3 Z" fill="${C.gold}"/>
      <path d="M2,-11 L3.6,-11 L3.6,-3 L2,-3 Z M5.4,-11 L7,-11 L7,-3 L5.4,-3 Z" fill="${C.red}"/>
      <path d="M-3,-3 L3,-3 L3,11.6 Q0,13 -3,11.6 Z" fill="${C.maroon}"/>
      <circle cx="0" cy="4" r="2.8" fill="${C.gold}" stroke="${C.line}" stroke-width="1"/>
      <path d="M-9,-3 L9,-3" stroke="${C.line}" stroke-width="1.2"/>
      <path d="M-9,-11 L9,-11 L9,1 Q9,9 0,13 Q-9,9 -9,1 Z" fill="none" ${line(2)}/>
    </g>`;
  }

  function torsoPart(view = 'front') {
    const front = view === 'front';
    const panels = `
      <path d="M139,280 L154,280 L146,402 L131,402 Z" fill="${C.navy}"/>
      <path d="M154,280 L163,280 L155,402 L146,402 Z" fill="${C.maroon}"/>
      <path d="M246,280 L261,280 L269,402 L254,402 Z" fill="${C.navy}"/>
      <path d="M237,280 L246,280 L254,402 L245,402 Z" fill="${C.maroon}"/>`;
    const neckLines = `<path d="M187,236 L187,268 Q187,273 179,276 M213,236 L213,268 Q213,273 221,276" fill="none" ${line()}/>`;
    const collar = front
      ? `<path d="M187,236 L187,268 Q187,274 178,276 L200,300 L222,276 Q213,274 213,268 L213,236 Z" fill="${C.skin}"/>
         <rect x="189.5" y="256" width="21" height="14" fill="${C.skinShade}"/>${neckLines}
         <path d="M170,275 L200,307 L230,275 L220,275 L200,296 L180,275 Z" fill="${C.maroon}" ${line(3.5)}/>`
      : `<path d="M187,236 L187,268 Q187,274 176,277 Q200,290 224,277 Q213,274 213,268 L213,236 Z" fill="${C.skin}"/>${neckLines}
         <path d="M174,275 Q200,290 226,275 L218,275 Q200,283 182,275 Z" fill="${C.maroon}" ${line(3.5)}/>`;
    const number = front ? crest()
      : `<text x="200" y="366" text-anchor="middle" font-family="Arial Black, Arial, Helvetica, sans-serif" font-weight="900" font-size="56" fill="${C.navy}" stroke="${C.maroon}" stroke-width="2" paint-order="stroke">10</text>`;
    return `<path d="${TORSO}" fill="${C.jersey}"/>
      <g clip-path="url(#torsoClip)">${panels}</g>
      ${number}
      <path d="${TORSO}" fill="none" ${line()}/>
      ${collar}`;
  }

  const LOOKS = {
    medium: {
      label: 'Medium hair', hair: HAIR, back: HAIR_BACK, nape: '', bud: false,
      strands: ['M194,116 Q176,134 170,160', 'M206,116 Q224,134 230,160', 'M184,96 Q158,118 148,156', 'M216,96 Q242,118 252,156'],
      backStrands: ['M200,64 Q196,120 200,240', 'M160,80 Q142,150 170,240 M240,80 Q258,150 230,240'],
      glassesArms: 'M127,197 L113,199 M273,197 L287,199',
      ears: () => `<ellipse cx="111" cy="206" rx="10" ry="12" fill="${C.skin}" ${line(4)}/>
        <path d="M110,201 Q105,206 110,212" fill="none" ${line(2.5)}/>
        <ellipse cx="289" cy="206" rx="10" ry="12" fill="${C.skin}" ${line(4)}/>
        <path d="M290,201 Q295,206 290,212" fill="none" ${line(2.5)}/>`,
    },
    long: {
      label: 'Long hair (first version)', hair: HAIR_LONG, back: HAIR_BACK_LONG, nape: NAPE_LONG, bud: true,
      strands: ['M194,116 Q172,136 162,164', 'M206,116 Q228,136 238,164', 'M184,96 Q156,118 142,160', 'M216,96 Q244,118 258,160'],
      backStrands: ['M200,64 Q196,120 200,250', 'M160,80 Q140,160 172,250 M240,80 Q260,160 228,250'],
      glassesArms: 'M127,197 L108,192 M273,197 L292,192',
      ears: () => `<circle cx="106" cy="198" r="16" fill="${C.skin}" ${line()}/>
        <path d="M104,191 Q98,199 105,206" fill="none" ${line(3)}/>
        <circle cx="294" cy="198" r="16" fill="${C.skin}" ${line()}/>
        <path d="M296,191 Q302,199 295,206" fill="none" ${line(3)}/>`,
    },
  };
  let look = LOOKS.medium, lookName = 'medium';
  function setLook(name) { if (LOOKS[name]) { look = LOOKS[name]; lookName = name; } }
  const getLook = () => lookName;

  function ears(side = 'front') {
    const earbud = (cx) => `<rect x="${cx - 2.5}" y="201" width="5" height="15" rx="2.5" fill="${C.bud}" ${line(2.2)}/>
      <ellipse cx="${cx}" cy="199" rx="6" ry="5.5" fill="${C.bud}" ${line(2.2)}/>`;
    return look.ears() + (look.bud ? earbud(side === 'front' ? 295 : 105) : '');
  }

  function headBase() {
    return `${look.nape ? `<path d="${look.nape}" fill="${C.hair}" ${line()}/>` : ''}${ears('front')}<path d="${FACE}" fill="${C.skin}" ${line()}/>`;
  }

  function hairFront() {
    const s = (d, o = 0.85) => `<path d="${d}" fill="none" stroke="${C.strand}" stroke-opacity="${o}" stroke-width="2" stroke-linecap="round"/>`;
    const [a, b, c, d] = look.strands;
    return `<path d="${AHOGE}" fill="none" ${line(4)}/>
      <path d="${look.hair}" fill="${C.hair}" ${line()}/>
      ${s(a)}${s(b)}${s(c, 0.6)}${s(d, 0.6)}`;
  }

  function headBack() {
    const [a, b] = look.backStrands;
    return `${ears('back')}<path d="${AHOGE}" fill="none" ${line(4)}/>
      <path d="${look.back}" fill="${C.hair}" ${line()}/>
      <path d="${a}" fill="none" stroke="${C.strand}" stroke-opacity=".5" stroke-width="2" stroke-linecap="round"/>
      <path d="${b}" fill="none" stroke="${C.strand}" stroke-opacity=".4" stroke-width="2" stroke-linecap="round"/>`;
  }

  function glassesPart() {
    return `<path d="${look.glassesArms}" fill="none" ${line(4)}/>
      <path d="${SHADES}" fill="${C.shades}" ${line(4)}/>
      <path d="M142,198 L160,197 M226,197 L250,198" fill="none" stroke="#fff" stroke-opacity=".38" stroke-width="3" stroke-linecap="round"/>
      <path d="M236,219 L246,205 M164,219 L172,208" fill="none" stroke="#fff" stroke-opacity=".22" stroke-width="3" stroke-linecap="round"/>`;
  }

  // ---------- faces (brows + eyes + mouth; brows tuck under the curtain) ----------
  const EYES = [161, 239];
  const brows = (dy = 0, dyR = dy) =>
    `<path d="M150,${183 + dy} Q162,${180 + dy} 173,${182 + dy} M227,${182 + dyR} Q238,${180 + dyR} 250,${183 + dyR}" fill="none" ${line(4)}/>`;
  const sleepyEyes = (lid = 203, dx = 0) => EYES.map(x0 => {
    const x = x0 + dx;
    return `<path d="M${x - 11},${lid} L${x + 11},${lid} C${x + 11},${lid + 13} ${x + 6},${lid + 20} ${x},${lid + 20} C${x - 6},${lid + 20} ${x - 11},${lid + 13} ${x - 11},${lid} Z" fill="${C.line}"/>
      <path d="M${x0 - 14},${lid - 1} Q${x0},${lid - 4} ${x0 + 14},${lid - 1}" fill="none" ${line(4)}/>`;
  }).join('');
  const blush = (s = 1, op = 0.7) =>
    `<g clip-path="url(#faceClip)"><g filter="url(#soft)" opacity="${op}"><ellipse cx="144" cy="234" rx="${18 * s}" ry="${10 * s}" fill="${C.blush}"/><ellipse cx="256" cy="234" rx="${18 * s}" ry="${10 * s}" fill="${C.blush}"/></g></g>`;
  const mouthFlat = `<path d="M196,246 L204,246" fill="none" ${line(3)}/>`;

  const FACES = {
    neutral: () => brows() + sleepyEyes() + mouthFlat,
    happy: () => blush(1, 0.85) + brows(-4) + EYES.map(x => `<path d="M${x - 11},213 Q${x},197 ${x + 11},213" fill="none" ${line(5)}/>`).join('')
      + `<path d="M191,240 Q200,242 209,240 Q207,253 200,253 Q193,253 191,240 Z" fill="${C.mouth}" ${line(3)}/>`,
    blink: () => brows() + EYES.map(x => `<path d="M${x - 11},211 Q${x},216 ${x + 11},211" fill="none" ${line(4.5)}/>`).join('') + mouthFlat,
    surprised: () => brows(-8) + EYES.map(x => `<ellipse cx="${x}" cy="210" rx="10" ry="13" fill="${C.line}"/><circle cx="${x + 3}" cy="205" r="2.6" fill="#fff"/>`).join('')
      + `<ellipse cx="200" cy="248" rx="5" ry="6.5" fill="${C.mouth}" ${line(3)}/>`,
    sideeye: () => brows(1, -2) + sleepyEyes(206, 5) + `<path d="M197,247 Q202,245 207,246" fill="none" ${line(3)}/>`,
    shy: () => blush(1.3, 1)
      + [144, 256].map(cx => [-8, 0, 8].map(d => `<path d="M${cx + d - 3},240 L${cx + d + 3},228" stroke="${C.blushHatch}" stroke-width="2.5" stroke-linecap="round"/>`).join('')).join('')
      + brows(-2) + `<path d="M154,200 L167,209 L154,218" fill="none" ${line(4.5)}/><path d="M246,200 L233,209 L246,218" fill="none" ${line(4.5)}/>`
      + `<path d="M191,246 Q195.5,241 200,246 Q204.5,251 209,246" fill="none" ${line(3)}/>`,
  };
  const FACE_LABELS = { neutral: 'Neutral', happy: 'Happy', blink: 'Blink', surprised: 'Surprised', sideeye: 'Side-eye', shy: 'Shy' };

  // ---------- full character ----------
  function character(o = {}) {
    const p = Object.assign({ armL: 14, armR: -14, legL: 0, legR: 0, legLy: 0, legRy: 0, head: 0, y: 0, face: 'neutral', faces: null, view: 'front', anim: false, glasses: true }, o);
    const A = (cls, inner) => (p.anim ? `<g class="${cls}">${inner}</g>` : inner);
    const front = p.view === 'front';
    const faceSvg = p.faces ? p.faces.map(f => `<g class="p-face-${f}">${FACES[f]()}</g>`).join('') : FACES[p.face]();
    const head = front ? headBase('right') + faceSvg + hairFront() + (p.glasses ? glassesPart() : '') : headBack();
    return `<g filter="url(#ink)" transform="translate(0,${p.y})">
      ${A('p-legL', legPart(PIVOT.leg_left, p.legL, true, p.legLy))}
      ${A('p-legR', legPart(PIVOT.leg_right, p.legR, false, p.legRy))}
      ${A('p-upper', `${torsoPart(p.view)}
        <g transform="rotate(${p.head} ${PIVOT.head.join(' ')})">${A('p-head', head)}</g>
        ${A('p-armL', armPart(PIVOT.arm_left, p.armL, !front))}
        ${A('p-armR', armPart(PIVOT.arm_right, p.armR, front))}`)}
    </g>`;
  }

  const POSES = {
    idle: { label: 'Idle' },
    wave: { label: 'Wave', armR: -138, head: -5, face: 'happy' },
    walk: { label: 'Walk', armL: 30, armR: -2, legL: 8, legR: -3, legRy: -7, y: -3 },
    cheer: { label: 'Cheer', armL: 150, armR: -150, legL: 12, legR: -12, y: -18, face: 'happy' },
    shrug: { label: 'Shrug', armL: 64, armR: -64, head: 6, face: 'sideeye' },
    oops: { label: 'Oops', armL: 38, armR: -38, y: -6, face: 'surprised' },
  };

  // ---------- avatar ----------
  const AVATAR_VB = [44, 12, 312, 312];
  const AVATAR_BGS = [['paper', 'paper'], ['blaugrana', 'stripes'], ['cream', '#efe9df'], ['transparent', 'transparent']];
  function avatarScene(bg, o = {}) {
    const [x, y, w, h] = AVATAR_VB;
    let back = '';
    if (bg === 'paper') back = `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="#8f8c8a" filter="url(#paper)"/>`;
    else if (bg === 'stripes') {
      back = `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${C.navy}"/>`;
      for (let sx = x + 26; sx < x + w; sx += 78) back += `<rect x="${sx}" y="${y}" width="39" height="${h}" fill="${C.maroon}"/>`;
    } else if (bg !== 'transparent') back = `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${bg}"/>`;
    return back + character(o);
  }

  // ---------- rig layers (bottom -> top) ----------
  const LAYERS = [
    { name: '01_leg_left', parent: 'torso', pivot: PIVOT.leg_left, svg: () => legPart(PIVOT.leg_left, 0, true), view: [130, 370, 80, 120] },
    { name: '02_leg_right', parent: 'torso', pivot: PIVOT.leg_right, svg: () => legPart(PIVOT.leg_right, 0, false), view: [190, 370, 80, 120] },
    { name: '03_torso', parent: null, pivot: PIVOT.torso, svg: () => torsoPart('front'), view: [126, 232, 148, 172] },
    { name: '04_head', parent: 'torso', pivot: PIVOT.head, svg: () => headBase('right'), view: [84, 90, 232, 180] },
    { name: '05_face', parent: 'head', pivot: PIVOT.head, svg: FACES.neutral, view: [134, 170, 132, 100] },
    { name: '06_hair', parent: 'head', pivot: PIVOT.head, svg: hairFront, view: [92, 20, 216, 204] },
    { name: '07_glasses', parent: 'head', pivot: PIVOT.head, svg: glassesPart, view: [100, 180, 200, 56] },
    { name: '08_arm_left', parent: 'torso', pivot: PIVOT.arm_left, svg: () => armPart(PIVOT.arm_left, 14, false), view: [104, 262, 70, 118] },
    { name: '09_arm_right', parent: 'torso', pivot: PIVOT.arm_right, svg: () => armPart(PIVOT.arm_right, -14, true), view: [226, 262, 70, 118] },
  ];

  const HEAD_VB = [72, 8, 256, 276];
  const POSE_VB = [0, -10, W, H + 10];

  const svg = (inner, vb = [0, 0, W, H], attrs = '') =>
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${vb.join(' ')}" ${attrs}>${inner}</svg>`;
  const standalone = (inner, vb, px) => svg(defs() + inner, vb, `width="${px[0]}" height="${px[1]}"`);

  // Everything in the downloadable kit: [{path, svg, w, h}]
  function exportList() {
    const PW = W * SCALE, PH = H * SCALE, out = [];
    const add = (path, inner, vb, w, h) => out.push({ path, svg: standalone(inner, vb, [w, h]), w, h });
    LAYERS.forEach(L => add(`layers/${L.name}.png`, `<g filter="url(#ink)">${L.svg()}</g>`, [0, 0, W, H], PW, PH));
    Object.keys(FACES).filter(f => f !== 'neutral').forEach(f =>
      add(`layers/face_swaps/05_face_${f}.png`, `<g filter="url(#ink)">${FACES[f]()}</g>`, [0, 0, W, H], PW, PH));
    for (const glasses of [true, false]) {
      const tag = glasses ? '' : '_no-shades';
      ['front', 'back'].forEach(v => add(`character_${v}${tag}.png`, character({ view: v, glasses }), [0, 0, W, H], PW, PH));
      Object.entries(POSES).forEach(([k, p]) => add(`poses/pose_${k}${tag}.png`, character({ ...p, glasses }), POSE_VB, PW, PH + 40));
      AVATAR_BGS.forEach(([k, bg]) => add(`avatar/avatar_${k}${tag}.png`, avatarScene(bg, { glasses }), AVATAR_VB, 1024, 1024));
    }
    Object.keys(FACES).forEach(f =>
      add(`expressions/head_${f}.png`, `<g filter="url(#ink)">${headBase('right')}${FACES[f]()}${hairFront()}</g>`, HEAD_VB, HEAD_VB[2] * 4, HEAD_VB[3] * 4));
    return out;
  }

  function rigJson() {
    return JSON.stringify({
      canvas: { width: W * SCALE, height: H * SCALE },
      note: 'All layers share the same canvas so they line up when stacked. Pivots are in pixels of that canvas. Layers are listed bottom to top.',
      layers: LAYERS.map(L => ({ file: `layers/${L.name}.png`, name: L.name.slice(3), parent: L.parent, pivot: { x: L.pivot[0] * SCALE, y: L.pivot[1] * SCALE } })),
      faceSwaps: Object.keys(FACES).filter(f => f !== 'neutral').map(f => `layers/face_swaps/05_face_${f}.png`),
    }, null, 2);
  }

  const api = {
    W, H, SCALE, C, PIVOT, FACES, LOOKS, setLook, getLook, FACE_LABELS, POSES, LAYERS, AVATAR_VB, AVATAR_BGS, HEAD_VB, POSE_VB,
    defs, svg, standalone, character, avatarScene, headBase, hairFront, glassesPart, exportList, rigJson,
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.MiniMe = api;
})(typeof window !== 'undefined' ? window : globalThis);
