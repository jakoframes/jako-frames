// Separate Remotion entry for the reel-1k-cake subtitles (keeps the existing src/index.ts / Root.tsx untouched).
//   npx remotion render src/cake/index.ts CakeSubs <out.mov> --codec=prores --prores-profile=4444 --image-format=png
//     --pixel-format=yuva444p10le --browser-executable="C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" [--scale=0.5]
import {registerRoot} from 'remotion';
import {CakeRoot} from './CakeRoot';

registerRoot(CakeRoot);
