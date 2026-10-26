# "Claude is cooking" reel — status

Promo reel, 1080×1920, 30 fps, 27.5 s. Jako (Mini Me kit, medium hair) hosts in a bright white 3D studio.
Built on the `reel-find-skills` engine (CSS 3D world, camera rig, kit character), re-skinned light and a little maximalist.

## Story (absolute seconds)
- 0–1.66: hook montage of the reference's most dynamic moments (`CLIPS` in `src/timing.ts`: 3D phone, chest → sun,
  streak 0 → 1, Repeat → Animate, the owl's eyes turn red), speed-ramped, with punch-in / shake / whip blur / RGB split
  (`refFx` in `src/Scenes.tsx`), white flashes, a light leak, a noise riser and hits in the mix.
- 1.66–2.46: camera pulls back; the video keeps playing in a floating screen in the studio, Jako drops in. Voice starts at 2.36.
- hook "Claude Opus 5.5 is cooking" → made (selection box, Claude card, 20:00 timer) → meta (whole reel shrinks into an editor
  window, MADE BY CLAUDE stamp) → no designer (struck words) → three boards (drop IG reference → assets → paste prompt)
  → BOOM (reference flies back as the result) → CTA (comment "SaaS", DM with prompt.md + instructions.pdf, arrow to comments).

## Files
- `public/vo-raw.mp3`: ElevenLabs voice as delivered. `public/vo.wav`: pauses and breaths removed, words untouched (23.4 s).
  v1 cut at -38 dB with 20 ms gaps and swallowed word edges ("One drop", "asset", "instruction"); the user flagged it.
  `tools/prep_audio.py` now follows each word's soft tail/onset down to -50 dB, keeps 40 ms between phrases,
  90 ms at sentence ends, 100 ms before each step / "boom" and 160 ms after "One/Two/Three".
- `src/vo.json`: word timings from the untouched take (faster-whisper small.en), mapped onto the cut, + loudness per frame.
- `src/timing.ts`: VO_START offset, word keys (a few nudged onto phrase cuts), scenes.
- `src/Reel.tsx`: camera rig, white stage, décor, intro blur fill, meta window. `src/Scenes.tsx`: all scene art. `src/Jako.tsx`: character.
- `public/ref.mp4` (reference, 30 fps), `ref-small.mp4` (blur fill), `ig-a/b.png` (IG screenshots, cropped), `still-a/b/c.jpg` (BOOM fan).
- `mix.mjs`: voice + SFX + the reference's own sound under the opening. `tools/stills.mjs`: stills + contact sheet from one bundle.

## Commands
- Check stills: `node tools/stills.mjs cache/s1 0.3 30 140 255 ...`
- Final: `npm run render` (add `--crf=16 --jpeg-quality=95`), then `node mix.mjs out/silent.mp4 out/claude-cooking-reel.mp4`
- Python for `tools/prep_audio.py`: `C:\Users\acer\.agent-reach-venv\Scripts\python.exe -I tools/prep_audio.py public/vo-raw.mp3 public/vo.wav src/vo.json`

## Output
- v1 (2026-10-25): `out/claude-cooking-reel.mp4` (from `out/silent2.mp4`). User: intro too long, no hook; words eaten at 1-2-3.
- v2 (2026-10-25): `out/claude-cooking-reel-v2.mp4` (from `out/silent3.mp4`): hook montage + clean voice cut.
- v3 (2026-10-25): `out/claude-cooking-reel-v3.mp4` (from `out/silent4.mp4`): + steady subtitles (`src/Subtitles.tsx`:
  phrase ranges index the 79 words in vo.json; regroup them if the voice is regenerated).

## Notes
- No music. Add a trending sound in Instagram, low under the voice.
