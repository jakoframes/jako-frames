# How I Made This Motion Graphic With Claude (No After Effects)

A step-by-step guide to recreating a premium motion-design video from a reference, using only Claude, your voiceover and your music.

Made by **@jako.frames**

---

## What you need

| Item | Notes |
|---|---|
| **Claude** | Use the **Claude desktop app → Code tab** (or Claude Code). It can write the animation code *and* render a real MP4. A normal chat can design the animation, but it can't export a video file for you. |
| **A reference video** | Any motion-design video you love (Instagram, Behance, Dribbble, YouTube). |
| **Voiceover (MP3)** | Record yourself or generate it, e.g. with ElevenLabs. |
| **Music (MP3)** | A background track you have the rights to use. |
| **SFX (optional)** | Whooshes, clicks, impacts, pops. Free packs are on Pixabay and Freesound. |

---

## Step 1: Find a reference you love

Pick one video whose **style** you want: colors, fonts, transitions, pace.

The reference I used:
👉 https://www.instagram.com/reel/Del86T5zm-n/

Why it works as a reference:
- Bold heavy fonts paired with an elegant italic serif
- A strong palette: orange, lime, violet, cream on black
- Lots of elements: dot grids, particles, glass blobs, UI cards, 3D camera moves
- Fast, rhythmic cuts

> 💡 You are copying the **techniques and style**, not the artwork itself. Don't reuse someone's exact logo, characters or music.

## Step 2: Save the reference video

Download or screen-record the reference so you have it as a video file (MP4).

## Step 3: Prepare your voiceover

1. Write your script. Keep sentences short and punchy.
2. Use CAPITAL LETTERS on the words you want stressed, and "..." for pauses.
3. Generate it in ElevenLabs (the **Eleven v3** model gives the most emotion) or record yourself.
4. Export as MP3.

Example script line:
```
WHAT THE HEEECK?! The world was NOT ready for this...
```

## Step 4: Pick your music and SFX

- Choose a background track (MP3) and note where you want it to start (for example, "start from 0:32").
- Collect a few SFX: whoosh, click, impact, pop, sparkle.

## Step 5: Give everything to Claude

Open Claude (Code tab), create a project folder and attach or point Claude to:
- the reference video
- your voiceover MP3
- your music MP3
- your SFX files

## Step 6: Paste the prompt

Use the template below. Replace everything in **[brackets]**.

```
Using these assets, recreate a motion-design video in the style of the attached reference.

ASSETS
- Reference video: [file name or link]
- Voiceover: [file name]. Sync every word on screen to the exact moment it is spoken.
- Music: [file name]. Start it from [0:32]. Keep it quiet under the voice.
- SFX: [file names]. Put a sound on every important animation, but keep them quieter than the voice.

FORMAT
- Size: [1920x1080 (16:9, YouTube/landscape) OR 1080x1920 (9:16, Reels/TikTok)]
- Quality: 30 fps, high quality MP4 (H.264), loudness around -14 to -16 LUFS
- Length: match the voiceover length

STYLE
- Style: [maximalism / minimalism / brutalism / Swiss / retro / glassmorphism]
- Colors: [orange #FF5B1F, lime #D9F53B, violet #6C5CF5, cream #F1ECE4 on black]
- Fonts: [heavy grotesk for keywords + italic serif for soft words + small mono for UI labels]
- Pace: fast, dynamic, a new visual every 0.5–2 seconds

ANIMATIONS TO USE
- Kinetic typography: words slam in, stretch, mask-reveal, letters tumble in 3D
- Smooth 3D camera movements: orbit, push-in, dolly, a fast swing on key words
- Shape morphing: circle → square → triangle, blobs merging
- UI/UX design: floating cards, toggles, charts, a cursor clicking buttons
- Particles: a sphere of particles that morphs into a word
- Glow and depth: glass/iridescent spheres, light bloom, text behind objects
- Transitions: hard color cuts on the beat, whip pans, zoom-throughs
- A HUD frame: corner brackets, timecode, progress ruler, section labels

Make each spoken word trigger its own visual (for example "money" → falling bills, "time" → a spinning clock).
Before the final render, show me preview frames so I can check them.
```

## Step 7: Review and fix

Claude shows you preview frames first. Check them and ask for fixes in plain words, for example:
- "The word CODE is cut off on the right, make it smaller."
- "The music is too loud, I want to hear the voice."
- "Make the Claude chat scene 3D with elements orbiting around the camera."

## Step 8: Export and post

Claude renders the final MP4. Watch it once with sound, then post it. 🚀

---

## My example (what I actually did)

1. **Reference:** the Instagram reel above.
2. **Voiceover:** my own script, generated in ElevenLabs with the Eleven v3 model.
3. **Music:** started from second 32, kept quiet and ducked under the voice.
4. **Prompt:** the template above, with 1920×1080, maximalism, and the orange/lime/violet palette.
5. **What Claude built:**
   - A HUD frame with a live timecode
   - Kinetic type: "WHAT THE HEEECK?!", "NOT", "READY."
   - A particle sphere that morphs into the word "CLAUDE"
   - A 3D Claude chat window with UI cards orbiting around it while the prompt types itself
   - Glass blobs, a swirling dot grid, a UI dashboard, a code editor, falling money, a dot clock
   - SFX on every hit, with the music ducked under the voice
6. **Result:** a 47-second, 1920×1080 video, made with **zero** After Effects.

---

## Tips

- **One clear reference beats five mixed ones.**
- **The voiceover is the timeline.** Give Claude the final voice before it starts animating.
- **Be specific.** "Make it pop" is vague; "slam the word in with a scale bounce and a camera shake" is clear.
- **Iterate.** The first version is a draft. Two or three rounds of feedback make it premium.
- **Respect rights.** Use music, SFX and fonts you're allowed to use.

---

*Follow **@jako.frames** for more Claude × motion design.*
