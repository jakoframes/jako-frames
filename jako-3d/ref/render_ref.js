// Builds reference HTML pages from the 2D Mini Me kit (look "medium").
// Run: node render_ref.js   then render_ref.ps1 screenshots them with headless Edge.
// All full-canvas pages are the 400x500 kit canvas at 2x = 800x1000 px, so pixel = 2 * svg unit.
const fs = require('fs');
const path = require('path');
const M = require('./character.js');
M.setLook('medium');

const out = path.join(__dirname, 'html');
fs.mkdirSync(out, { recursive: true });
const MAG = '#ff00ff', BG = '#efe9df';

function page(name, inner, vb, w, h, bg) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${vb.join(' ')}" width="${w}" height="${h}">${M.defs()}${inner}</svg>`;
  fs.writeFileSync(path.join(out, name + '.html'),
    `<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;padding:0;background:${bg};overflow:hidden}svg{display:block}</style></head><body>${svg}</body></html>`);
  return { name, w, h };
}
const FULL = [0, 0, 400, 500];
const ink = s => `<g filter="url(#ink)">${s}</g>`;
const headFront = (face = 'neutral') => ink(M.headBase('right') + M.FACES[face]() + M.hairFront());
// headBack() is not exported; character({view:'back'}) contains it. Crop the body away with a clip.
const headBackOnly = () => `<clipPath id="hb"><rect x="0" y="0" width="400" height="272"/></clipPath><g clip-path="url(#hb)">${M.character({ view: 'back' })}</g>`;

const pages = [
  page('kit_front', M.character({ view: 'front', glasses: true }), FULL, 800, 1000, BG),
  page('kit_front_noshades', M.character({ view: 'front', glasses: false }), FULL, 800, 1000, BG),
  page('kit_compare', M.character({ view: 'front', glasses: false }), FULL, 864, 1080, BG),
  page('kit_back',M.character({ view: 'back' }), FULL, 800, 1000, BG),
  page('mask_head_front', headFront(), FULL, 800, 1000, MAG),
  page('mask_head_back', headBackOnly(), FULL, 800, 1000, MAG),
  page('mask_body_front', M.character({ view: 'front', glasses: false }), FULL, 800, 1000, MAG),
  page('mask_body_back', M.character({ view: 'back' }), FULL, 800, 1000, MAG),
];
// segmentation masks (fills only, no ink): hair = red, skin (face + ears) = green, on black
const FACE = 'M112,165 C110,232 150,268 200,268 C250,268 290,232 288,165 C286,110 250,96 200,96 C150,96 114,110 112,165 Z';
const AHOGE = 'M197,48 Q193,34 182,31 M201,48 Q207,33 218,29';
const earsSeg = `<ellipse cx="111" cy="206" rx="10" ry="12" fill="#0f0"/><ellipse cx="289" cy="206" rx="10" ry="12" fill="#0f0"/>`;
const ahogeSeg = `<path d="${AHOGE}" fill="none" stroke="#f00" stroke-width="4" stroke-linecap="round"/>`;
pages.push(page('seg_front', earsSeg + `<path d="${FACE}" fill="#0f0"/>` + ahogeSeg + `<path d="${M.LOOKS.medium.hair}" fill="#f00"/>`, FULL, 800, 1000, '#000'));
pages.push(page('seg_back', earsSeg + ahogeSeg + `<path d="${M.LOOKS.medium.back}" fill="#f00"/>`, FULL, 800, 1000, '#000'));
// expression sheet: neutral, blink, happy, surprised heads side by side
const HV = M.HEAD_VB, faces = ['neutral', 'blink', 'happy', 'surprised'];
let sheet = '';
faces.forEach((f, i) => { sheet += `<g transform="translate(${i * HV[2]},0)"><g transform="translate(${-HV[0]},${-HV[1]})">${headFront(f)}</g></g>`; });
pages.push(page('kit_heads', sheet, [0, 0, HV[2] * 4, HV[3]], HV[2] * 4 * 2, HV[3] * 2, BG));

fs.writeFileSync(path.join(out, 'pages.json'), JSON.stringify(pages));
console.log(pages.map(p => `${p.name} ${p.w}x${p.h}`).join('\n'));
