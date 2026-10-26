# Reel "1000 followers" (cake) — status

Updated 2026-10-26. Nothing is published or scheduled.

## v3 FINAL DONE 2026-10-26 13:54 — `out/reel_1k.mp4` + `out/reel_1k_nosubs.mp4` (tablet faces only Claude, screen glow). The watcher died after the last frame; re-running the launch line muxed it. v1 kept as `*_v1.mp4`.

## (v1) FINAL VIDEO DONE 2026-10-26 06:26 — waiting for the user's review
- `out/reel_1k.mp4` (1080×1920, 24 fps, 39.67 s, h264 + AAC, subtitles burned in) and `out/reel_1k_nosubs.mp4`.
- Checked: duration, a 16-frame contact sheet (look, subtitles, cuts, ending wide all OK).
- To check with the user before posting: the recording says "No, not with you. Just me." (script had the reverse); the ending laugh is short (~0.5 s);
  the tablet clip shows a real person + TikTok watermark; the Apple logo is on the MacBook; there's no music (add a track in Instagram).

## Where things are
- Audio: `audio/mix_preview.wav` (48 kHz stereo, 39.67 s = 952 frames @ 24 fps), stems in `audio/stems/`, single
  lines in `audio/lines/`, timing in `audio/timeline.json` (lines, word times, per-frame mouth/hop envelopes), cuts in
  `audio/shots.json`. Rebuild: `~/.agent-reach-venv/Scripts/python.exe -I tools/build_audio.py` (all timing knobs are at the top).
  Transcripts: `audio/src/*_words.json` (faster-whisper small.en), cross-checked with large-v3-turbo (`*_large.srt`).
- Script / shot list / Claude actions: `script.md`.
- Blender (4.5.15, `C:\Users\acer\Blender\blender-4.5.15-windows-x64\blender.exe`):
  - Rebuild everything: `blender.exe -b -y --factory-startup --python blender\run_all.py` -> `blender\scene.blend` (~3 s).
    Order: `s1_set.py` (room, props, lights, render settings) -> `s2_characters.py` (Jako append + Claude) -> `s3_anim.py`
    (acting, tablet, cameras/cuts, sound strip, writes `subs/subs.json` + `audio/shots.json`).
  - Stills: `blender.exe -b -y blender\scene.blend --python blender\render_stills.py -- <frame>:<out.png> ... [--pct 100] [--samples 64]`
  - Animatic frames: `blender.exe -b -y blender\scene.blend --python blender\render_animatic.py` -> `previews/animatic_frames/`
    (540x960, 12 samples, no ray tracing; resumable).
- Subtitles (Remotion, separate entry so `reel-what-the-heck`'s own files stay untouched): `reel-what-the-heck\src\cake\`
  (`index.ts`, `CakeRoot.tsx`, `CakeSubs.tsx`). Transparent overlay:
  `npx remotion render src/cake/index.ts CakeSubs <out.mov> --codec=prores --prores-profile=4444 --image-format=png --pixel-format=yuva444p10le --browser-executable="C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" [--scale=0.5]`
  Style = user's refs: white bold sans in a rounded semi-transparent dark-grey box, top-centre, word-timed chunks.
- References: `ref/room_ref.jpg`, `ref/claude_ref.jpg` (voxel Claude, user's pick), `ref/macbook_ref.jpg`, `ref/style_ref_4..7.png` (look).

## Jako (real asset, appended)
`s2_characters.py` APPENDS collection `JAKO` from `jako-3d\jako.blend` (that file is only read, never written). The rig
`JAKO_rig` is parented to the empty `JAKO_SPOT` (seat position; object-level acting is keyed on JAKO_SPOT), and gets a
sitting pose plus scene-side skin override (`MAT_skin` base `#EDB994`, SSS 0.3) on the appended copy only.
**To pick up a newer Jako:** just rebuild (`run_all.py`): s2 deletes the old `JAKO` copy and appends the current
`jako-3d\jako.blend` again; `s3_anim.py` re-keys the rig props (`eyes`, `mouth`, `blush`) and bones (head, chest,
arms) by name. If bone names/rest axes change, adjust `REST_POSE` in s2 and the bone offsets in `jpose()` calls in s3.

## Done
- Audio cut + interleave (follows the recording: C02 is "No, not with you. Just me."), phone clip src 15.00 s with phone-speaker FX.
- Room v3 (low-key after the user's style refs), voxel Claude, MacBook lid + logo toward camera, student desk, "1000" cake.
- Acting for both characters keyed from word times; Claude syllable hops (33) from its envelope; Jako lip flaps from his envelope.
- 15 shots with slow pushes, cut list in `audio/shots.json`; CUs f/1.1-1.2, wides f/2.8.
- Location stills sent: previews/location_wip.png, _v2, _v3, closeup_jako_v3, closeup_claude_v3.

- Animatic DONE: `previews/animatic.mp4` (540x960, 39.67 s, audio + burned-in subs; assembled by `tools/make_animatic.ps1`).
- Hi-res key stills DONE: `stills/s01_wide_tablet.png`, `s02_jako_cu.png`, `s09_claude_cu.png`, `s15_wide_laugh.png`.
- After the animatic: S01 start reframed (Claude was cut), S04 "What?" less tight, S08 Jako centred (scene.blend rebuilt;
  the animatic above predates these three framing fixes).
- Subtitle overlays rendered: `subs/subs_540.mov` (animatic), `subs/subs_1080.mov` (final).

## v1 FINAL (kept)
- Rendered 05:01-06:26 on 2026-10-26: `out/reel_1k_v1.mp4` and `out/reel_1k_nosubs_v1.mp4`, frames in `renders_v1/`.
  The user liked it ("барлығы мощ") and asked for one change, which is v2.

## v2 attempt (stopped)
- The v2 tablet faced only Claude but sat off to its side. The coordinator stopped it after 17 frames; they were moved to `renders_v2_partial/`.

## v3 change: Claude watching the tablet
- The watching beat is rebuilt in `blender/s3_anim.py` (intro block + tablet section).
- Claude is turned 40 deg toward camera-left and leans forward. It holds a bigger tablet (36 x 24 cm) at lap level in both stubs.
- The screen is tilted up to Claude's face. Only Claude sees it; the camera sees the back.
- Claude's eye slits are lowered 2.8 cm (looking down at the screen) and come back up on "Claude.".
- `L_tablet` puts a soft cool glow on its front. It flickers with the clip's brightness, dims when paused, and goes off as the tablet goes down.
- On "Claude." the right stub taps pause. Claude then turns back toward Jako and the camera while laying the tablet SCREEN-DOWN on the desk.
- The tablet follows CLAUDE_torso through a per-frame bake, so it moves with hops and leans.
- Checked stills: `stills/v3_s01_opening_wide.png` (frame 20) and `stills/v3_s01_claude_watching.png` (frame 72). Frames 86 and 96 were checked at low res.

## v3 FINAL render RUNNING (launched 2026-10-26 12:18:57)
- Watcher: powershell PID 20992, started via WMI, so it survives the agent session. First Blender child PID 3536.
- It should take about 85 min, like v1.
- Output: `out/reel_1k.mp4` and `out/reel_1k_nosubs.mp4`. The v1 files stay as `*_v1.mp4`.
- Check progress:
  - Frames done (of 952): `(Get-ChildItem C:\Users\acer\Downloads\jako-frames\reel-1k-cake\renders -Filter *.png | ? Length -gt 0).Count`
  - Log: `Get-Content C:\Users\acer\Downloads\jako-frames\reel-1k-cake\renders\finish.log`. It writes "DONE: ..." at the end.
- Resume after a stop or reboot: run the launch line below again. Existing frames are skipped.

## How the FINAL render is started
- Launch detached (survives the session, keeps the PC awake, resumable):
  `Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine='powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\Users\acer\Downloads\jako-frames\reel-1k-cake\finish_render.ps1"'; CurrentDirectory='C:\Users\acer\Downloads\jako-frames\reel-1k-cake'}`
- Frames go to `renders/####.png`: 1080x1920, EEVEE 64 samples, ray tracing, set in `blender/render_final.py`.
- If the timing or subtitles change after `subs/subs_1080.mov` was made, delete that .mov so the watcher re-renders it.
- For a full re-render, first move `renders/` aside (for example to `renders_vN/`). Existing frames are never overwritten.
