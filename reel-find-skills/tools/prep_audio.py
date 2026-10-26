"""Cut pauses from the VO, then transcribe with word timestamps and build a per-frame loudness envelope."""
import json, subprocess, sys, wave
import numpy as np

raw, out_wav, out_json = sys.argv[1], sys.argv[2], sys.argv[3]
SR, FPS = 48000, 30
pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', raw, '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'],
                     capture_output=True, check=True).stdout
x = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768

# speech detection on 10 ms windows
win = SR // 100
n = len(x) // win
rms = np.sqrt((x[:n * win].reshape(n, win) ** 2).mean(1) + 1e-12)
db = 20 * np.log10(rms)
speech = db > -38
# close tiny gaps (< 120 ms) and drop blips (< 50 ms)
segs, i = [], 0
while i < n:
    if speech[i]:
        j = i
        while j < n and speech[j]: j += 1
        segs.append([i, j]); i = j
    else: i += 1
merged = []
for s in segs:
    if merged and s[0] - merged[-1][1] < 12: merged[-1][1] = s[1]
    else: merged.append(s)
merged = [s for s in merged if s[1] - s[0] >= 5]

PAD, GAP = 4, 7  # 40 ms padding each side, 70 ms gap between phrases
gap = np.zeros(GAP * win, dtype=np.float32)
parts, cuts, t = [], [], 0.0
for a, b in merged:
    a2, b2 = max(0, a - PAD), min(n, b + PAD)
    chunk = x[a2 * win:b2 * win].copy()
    f = min(len(chunk) // 4, int(0.008 * SR))  # 8 ms fades, no clicks
    chunk[:f] *= np.linspace(0, 1, f); chunk[-f:] *= np.linspace(1, 0, f)
    cuts.append({'src': [a2 / 100, b2 / 100], 'dst': [t, t + len(chunk) / SR]})
    parts += [chunk, gap]; t += (len(chunk) + len(gap)) / SR
y = np.concatenate(parts[:-1])
with wave.open(out_wav, 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())

# loudness envelope per video frame (drives the mouth)
spf = SR // FPS
nf = int(np.ceil(len(y) / spf))
yy = np.pad(y, (0, nf * spf - len(y)))
env = np.sqrt((yy.reshape(nf, spf) ** 2).mean(1))
env = np.clip(env / np.percentile(env[env > 0.01], 95), 0, 1.2)

from faster_whisper import WhisperModel
model = WhisperModel('small.en', device='cpu', compute_type='int8')
a16 = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', out_wav, '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'],
                                   capture_output=True, check=True).stdout, dtype=np.float32)
res, _ = model.transcribe(a16, word_timestamps=True, beam_size=5,
                          initial_prompt='Claude skills. Find Skills. Comment FIND.')
words = [{'w': wd.word.strip(), 's': round(wd.start, 3), 'e': round(wd.end, 3)} for seg in res for wd in seg.words]
json.dump({'duration': len(y) / SR, 'fps': FPS, 'cuts': cuts, 'words': words,
           'env': [round(float(v), 3) for v in env]}, open(out_json, 'w'), indent=1)
print('duration', round(len(y) / SR, 2), 'segments', len(merged))
print(' '.join(f"{w['w']}@{w['s']}" for w in words))
