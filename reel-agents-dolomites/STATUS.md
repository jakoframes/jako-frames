# Reel "Who are they?" (Dolomites, agents) — status

Updated 2026-10-23.

## Done
- Script + shot list: `script.md` (14 shots, vertical 1080×1920, 24 fps).
- Audio LOCKED (user approved): `audio/mix_preview.wav`, 49.57 s = 1190 frames. Claude voice = original ElevenLabs (no FX), J08 echo subtle. Timings: `audio/timeline.json`.
- Blender 4.5.15 LTS installed portable at `C:\Users\acer\Blender\blender-4.5.15-windows-x64\blender.exe`; MCP addon installed + auto-starts (port 9876).
  Launch with: blender.exe (addon auto-starts the server).
- Scene: `blender/run_all.py` rebuilds everything (~8 s) and saves `blender/reel.blend`. `blender/08_preview_stills.py` renders 540×960 stills to `previews/`.
- User said overall quality is good.

## SUBTITLED VERSION: out\reel_subs.mp4 — speech bubbles (JAKO/CLAUDE chip) anchored over the speaker. Source: reel-what-the-heck\src\DolomitesSubs.tsx + reel-agents-dolomites\subs.json (speaker positions from Blender). Re-render: in reel-what-the-heck, `npx remotion render src/index.ts DolomitesSubs <out> --browser-executable=<msedge.exe>` (bundled Chrome fails with EFTYPE).

## FINAL VIDEO DONE 2026-10-23 05:00: out\reel.mp4 (1080×1920, 24 fps, 49.57 s, Claude voice = Miguel take, timeline unchanged). Not published — waiting for user review.

## FULL RENDER STARTED 2026-10-23 (user approved Jako look = shot03_f0076_v8.png: first-variant head + center-part curtain bangs, no outline)
- Background Blender process renders reel.blend → renders/frame_0001..1190.png, log renders/render.log, ~30 s/frame (~10 h).
- Watcher `finish_render.ps1` runs detached: keeps PC awake, resumes render if it stops, then auto-builds out\reel.mp4. Progress: renders\finish.log ("DONE: ..." when finished). If the PC rebooted, run it again (no -RenderPid).
- If interrupted: re-run with `-x 1` (skips existing frames): blender.exe -b blender\reel.blend -x 1 -a
- Then mux: ffmpeg -framerate 24 -i renders\frame_%04d.png -i audio\mix_preview.wav -c:v libx264 -crf 16 -pix_fmt yuv420p -c:a aac -b:a 320k -shortest out\reel.mp4
  (ffmpeg at C:\Users\acer\ffmpeg\ffmpeg-9.0.2-full_build\bin)

## Jako hair fix DONE (2026-10-23) — stills previews/*_v2.png, waiting for user's verdict. Possible tweaks: longer lock points, ink outline.

## (old) In progress
- Fixing Jako to match the real character: `ref/sheet.png` (rendered from the Mini Me kit). Hair must be a center-parted curtain bob swept to both sides (no triangle bangs), strand highlights, back strands, sleepy eyes, clean maroon V collar, sunglasses on top of head. Edit `blender/03_jako.py`, re-run, re-render shots 01, 03, 09, 14 and compare to the sheet.

## Next
1. Finish the Jako fix, show stills to the user.
2. Optional quality items: Claude reads as a box from behind (eyes/laptop), Sassolungo walls look smeared, dark meadow, no mouth movement.
3. Check unchecked shots (02, 04b–e, 05, 07, 08, 10, 11a/b/d, 13) and motion (contact sheet).
4. Full render 1080×1920 EEVEE (~25–30 s/frame, ~8–10 h) → mux with mix_preview.wav. Never publish without the user's OK.
