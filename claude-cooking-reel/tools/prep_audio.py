"""Shorten the pauses in the VO without touching the words.

Transcribe the untouched take with word timestamps, find the silences, keep a little air on both sides
of every word (soft tails like s / t / th stay whole), drop the rest of each long pause, then map the
word times onto the cut and build a per-frame loudness envelope (drives the mouth).
"""
import json, subprocess, sys, wave
import numpy as np
from faster_whisper import WhisperModel

raw, out_wav, out_json = sys.argv[1], sys.argv[2], sys.argv[3]
SR, FPS = 48000, 30


def decode(path, sr, fmt, dtype):
    out = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(sr), '-f', fmt, '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=dtype)


x = decode(raw, SR, 's16le', np.int16).astype(np.float32) / 32768

# 1) words, on the untouched take
model = WhisperModel('small.en', device='cpu', compute_type='int8')
res, _ = model.transcribe(decode(raw, 16000, 'f32le', np.float32), word_timestamps=True, beam_size=5,
                          initial_prompt='Claude Opus 5.5 is cooking. One, drop a reference. Two, send your extra assets. '
                                         'A professional SaaS animation. Comment "SaaS".')
words = [{'w': wd.word.strip(), 's': float(wd.start), 'e': float(wd.end)} for seg in res for wd in seg.words]
# whisper likes to append "Thanks for watching!" at the end of a file
if [w['w'].lower().strip('!.,') for w in words[-3:]] == ['thanks', 'for', 'watching']:
    words = words[:-3]

# 2) pauses: on 10 ms windows, a pause is a long run below -38 dBFS (breaths sit in there too);
#    from both ends of it, the word's soft tail / onset is followed down to -50 dBFS and kept whole
win = SR // 100
n = len(x) // win
db = 20 * np.log10(np.sqrt((x[:n * win].reshape(n, win) ** 2).mean(1) + 1e-12))
loud = db > -38
air = db > -50
idx = np.flatnonzero(air)
first, last = int(idx[0]), int(idx[-1]) + 1

NUM = {'1', '2', '3', 'one', 'two', 'three'}
key = lambda w: w['w'].lower().strip('.,!?—–-"“”') if w else ''
before = lambda t: ([w for w in words if w['s'] < t] or [None])[-1]
after = lambda t: ([w for w in words if w['s'] >= t - 0.05] or [None])[0]

keep, cur, i = [], max(0, first - 4), first  # 40 ms lead-in
while i < last:
    if loud[i]:
        i += 1
        continue
    j = i
    while j < last and not loud[j]:
        j += 1
    if j - i < 20:                                   # under 200 ms: a stop inside a word or a quick comma, leave it
        i = j
        continue
    tail = i
    while tail < j and air[tail] and tail - i < 22:  # the word's decay (s, t, th) belongs to the word
        tail += 1
    onset = j
    while onset > tail and air[onset - 1] and j - onset < 15:
        onset -= 1
    prev, nxt = before(i / 100), after(j / 100)
    gap = 4                                          # 40 ms of clean silence between ordinary phrases
    if prev and prev['w'][-1:] in '.?!':
        gap = 9                                      # sentence end
    if key(nxt) in NUM or key(nxt) == 'boom':
        gap = max(gap, 10)                           # a breath before each step and before "boom"
    if key(prev) in NUM:
        gap = 16                                     # "One…" lands on its own before the step
    if onset - tail > gap + 2:
        keep.append([cur, tail + gap // 2])
        cur = onset - (gap - gap // 2)
    i = j
keep.append([cur, min(n, last + 15)])                # 150 ms tail

parts, segs, t = [], [], 0.0
f = int(0.01 * SR)
for a, b in keep:
    chunk = x[a * win:b * win].copy()
    chunk[:f] *= np.linspace(0, 1, f)
    chunk[-f:] *= np.linspace(1, 0, f)
    segs.append({'src': [a / 100, b / 100], 'dst': [round(t, 3), round(t + len(chunk) / SR, 3)]})
    parts.append(chunk)
    t += len(chunk) / SR
y = np.concatenate(parts)
with wave.open(out_wav, 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())


def remap(s):
    for g in segs:
        a, b = g['src']
        if s < a:
            return g['dst'][0]                       # inside a removed pause: snap to the next kept audio
        if s <= b:
            return g['dst'][0] + (s - a)
    return segs[-1]['dst'][1]


mapped = [{'w': w['w'], 's': round(remap(w['s']), 3), 'e': round(remap(w['e']), 3)} for w in words]

# loudness envelope per video frame
spf = SR // FPS
nf = int(np.ceil(len(y) / spf))
yy = np.pad(y, (0, nf * spf - len(y)))
env = np.sqrt((yy.reshape(nf, spf) ** 2).mean(1))
env = np.clip(env / np.percentile(env[env > 0.01], 95), 0, 1.2)

json.dump({'duration': len(y) / SR, 'fps': FPS, 'cuts': segs, 'words': mapped,
           'env': [round(float(v), 3) for v in env]}, open(out_json, 'w'), indent=1)
print('source', round(len(x) / SR, 2), '-> cut', round(len(y) / SR, 2), 'segments', len(segs))
print(' '.join(f"{w['w']}@{w['s']}" for w in mapped))
