"""Print sound islands (split by silence) of a voice file together with whisper words.
usage: python inspect_voice.py <audio> <words.json>"""
import json, subprocess, sys
import numpy as np
FF = r'C:\Users\acer\ffmpeg\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe'
SR = 48000
x = np.frombuffer(subprocess.run([FF, '-v', 'error', '-i', sys.argv[1], '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                                 capture_output=True, check=True).stdout, dtype=np.float32)
segs = json.load(open(sys.argv[2], encoding='utf-8'))
words = [w for s in segs for w in s['words']]
win = SR // 100
n = len(x) // win
db = 20 * np.log10(np.sqrt((x[:n * win].reshape(n, win) ** 2).mean(1) + 1e-12))
loud = db > -40
isl, i = [], 0
while i < n:
    if not loud[i]:
        i += 1; continue
    j = i
    while j < n and (loud[j] or (j + 25 < n and loud[j:j + 25].any())):   # bridge gaps < 250 ms
        j += 1
    isl.append((i / 100, j / 100, float(db[i:j].max())))
    i = j
print('duration %.2f' % (len(x) / SR))
for a, b, pk in isl:
    ws = ' '.join(w['w'] for w in words if w['s'] < b and w['e'] > a)
    print('%6.2f - %6.2f  (%.2fs, peak %.0f dB)  %s' % (a, b, b - a, pk, ws))
