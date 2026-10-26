# Find Skills reel — status

Educational reel, 1080×1920, 30 fps, 30 s. Jako (Mini Me kit, medium hair) as host.

- v1 (`out/find-skills-reel.mp4`): bright sticker style. The user found it too childish.
- v2 (`out/find-skills-reel-v2.mp4`): dark premium look (Bricolage Grotesque + Instrument Serif + JetBrains Mono, Claude-orange accent).
  It runs in a CSS 3D world: floor grid, back wall word, dust. The camera rig in `src/Reel.tsx` (CAM keys) orbits, dollies,
  whip-pans and pushes in. Jako walks and jumps around the stage (`JX`/`JZ` in `src/Jako.tsx`).

## Files
- `public/vo-raw.mp3`: the ElevenLabs voice as delivered. `public/vo.wav`: the same voice with pauses cut (28.8 s).
- `src/vo.json`: word timings (faster-whisper small.en) + per-frame loudness that drives the mouth.
- `src/timing.ts`: scenes, caption groups and keywords, all keyed to words.
- `src/Jako.tsx`: kit character, kit faces for emotion, loudness mouth, shades off at "thing" and back on after "FIND".
- `src/Scenes.tsx`: 11 scenes (hook → one → free → thing → fields → waste → scan → reveal → file → install → cta).
- `public/shot-*.png`: the user's Claude Skills screenshots (upload dialog, skills list).
- `mix.mjs`: voice + SFX, cues from the same word times.

## Commands
- Preview: `npx remotion render src/index.ts Reel out/preview.mp4 --scale=0.4 --muted --browser-executable=.browser/chrome-headless-shell-win64/chrome-headless-shell.exe`
- Final: `npm run render`, then `node mix.mjs out/silent.mp4 out/find-skills-reel.mp4`

## Notes
- The Chrome copy in `../reel-what-the-heck/node_modules/.remotion` is truncated and will not start; use `.browser/`.
- No music in the mix. Add a trending sound in Instagram, kept low under the voice.
- To redo timings after a new voice: `python tools/prep_audio.py public/vo-raw.mp3 public/vo.wav src/vo.json` (needs `pip install faster-whisper`), then re-render.
