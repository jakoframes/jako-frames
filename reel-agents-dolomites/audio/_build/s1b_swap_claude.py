"""Swap Claude's voice for a new ElevenLabs take without moving the timeline.
Splits the new file into C01..C10, then time-stretches each line (rubberband, pitch kept) to the old
speech duration from split_report.json, so s3_mix.py keeps every cue and the rendered video stays in sync."""
import sys, os, json, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from au import *
from s1_split import segments, THR, PAD

NEW = r"C:\Users\acer\Downloads\ElevenLabs_2026-10-22T22_03_38_Miguel - American English - Clear and Youthful_pvc_sp100_s35_sb35_v4.mp3"
FFMPEG = r"C:\Users\acer\ffmpeg\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
old = {s["id"]: s["dur"] for s in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "split_report.json")))["mike"]["segments"]}

x = decode(NEW)
segs = None
for ms in (0.45, 0.4, 0.5, 0.35, 0.55, 0.6, 0.3):
    s = segments(x, THR, ms)
    print("min_sil", ms, "->", len(s))
    if len(s) == 10:
        segs = s
        break
if segs is None:
    sys.exit("could not split the new take into 10 lines")

tmp = os.path.join(ROOT, "_tmp_c.wav")
for k, (a, b) in enumerate(segs):
    lid = f"C{k + 1:02d}"
    y = x[int(a * SR):int(b * SR)]
    ratio = (b - a) / old[lid]                       # >1 = new line is longer -> speed up
    print(f"{lid} new {b - a:.2f}s old {old[lid]:.2f}s tempo x{ratio:.3f}")
    write_wav(tmp, y)
    out = os.path.join(ROOT, "_tmp_c_st.wav")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", tmp, "-af",
                    f"rubberband=tempo={ratio:.5f}:pitch=1:transients=mixed", "-ar", str(SR), out], check=True)
    z = decode(out)
    n = int(round(old[lid] * SR))
    z = z[:n] if len(z) >= n else np.concatenate([z, np.zeros(n - len(z))])
    p = np.zeros(int(PAD * SR))
    write_wav(os.path.join(ROOT, "lines_raw", lid + ".wav"), fade(np.concatenate([p, z, p]), 0.012, 0.035))
for f in (tmp, out):
    os.remove(f)
print("ok")
