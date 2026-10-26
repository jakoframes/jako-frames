"""Build the dialogue timeline + preview mix for the "1000 followers" cake reel.

Inputs : audio/src/claude_all.mp3, audio/src/jako_all.mp3 (all lines of each voice, in order), the phone clip mp4,
         audio/src/{claude,jako}_words.json (faster-whisper small.en word times on the untouched takes).
Outputs: audio/mix_preview.wav (48 kHz stereo), audio/stems/*.wav, audio/lines/*.wav, audio/timeline.json,
         blender/tex/phone/####.png (phone screen frames, 24 fps).
Re-run any time; all timing lives in LINES / GAPS below.
"""
import json, os, subprocess, wave
import numpy as np

ROOT = r'C:\Users\acer\Downloads\jako-frames\reel-1k-cake'
FF = r'C:\Users\acer\ffmpeg\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe'
PHONE_MP4 = r'C:\Users\acer\Downloads\AQPXCHle9UQAWwwgwd_ti7vpPZT9mNl7s4yB3IUrzhSLC3ydTxJAchOLm6g8IHTUxKGE3ZLHI-X8OtQzqA02BGVr4-Ifz580-TaFqso.mp4'
SR, FPS = 48000, 24
A = os.path.join(ROOT, 'audio')
for d in ('stems', 'lines', '_build'):
    os.makedirs(os.path.join(A, d), exist_ok=True)


def decode(path, ss=None, t=None, af=None):
    cmd = [FF, '-v', 'error'] + (['-ss', str(ss)] if ss is not None else []) + (['-t', str(t)] if t else []) + ['-i', path]
    if af:
        cmd += ['-af', af]
    cmd += ['-ac', '1', '-ar', str(SR), '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, dtype=np.float32).copy()


def write_wav(path, y):
    y = np.atleast_2d(y)
    if y.shape[0] < y.shape[1]:
        y = y.T
    with wave.open(path, 'wb') as w:
        w.setnchannels(y.shape[1]); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())


VO = {'claude': decode(os.path.join(A, 'src', 'claude_all.mp3')), 'jako': decode(os.path.join(A, 'src', 'jako_all.mp3'))}
WORDS = {k: [w for s in json.load(open(os.path.join(A, 'src', k + '_words.json'), encoding='utf-8')) for w in s['words']]
         for k in VO}

# ---------------------------------------------------------------- lines: (id, who, src island start, src island end, text as SPOKEN)
# island times come from tools/inspect_voice.py (-40 dB, 250 ms bridge). Text follows the audio (checked with small.en
# and large-v3-turbo): C02 is recorded as "No, not with you. Just me." (script said "Not 'with me'. Just you.").
LINES = [
    ('J01', 'jako', 0.19, 0.59, 'Claude.'),
    ('C01', 'claude', 0.23, 1.93, 'Wait... what are those?'),
    ('J02', 'jako', 1.12, 4.84, 'I made a thousand followers in five days... with you.'),
    ('C02', 'claude', 2.46, 4.84, 'No, not with you. Just me.'),
    ('J03', 'jako', 5.29, 5.53, 'What?'),
    ('C03', 'claude', 5.24, 7.99, "Nah, I'm kidding, bro. Congrats!"),
    ('J04', 'jako', 6.14, 7.51, "So... what's the plan?"),
    ('C04', 'claude', 8.44, 10.97, "No, no. I have to ask. What's your plan?"),
    ('J05', 'jako', 7.98, 9.15, 'Just... keep posting?'),
    ('C05', 'claude', 11.47, 15.19, "Wrong answer. You're gonna teach people how to use Claude properly."),
    ('J06', 'jako', 9.57, 10.67, "Yeah, that's what I meant."),
    ('C06', 'claude', 15.62, 17.56, "Mm... you didn't mean that."),
    ('J07', 'jako', 11.07, 12.95, "No, that's exactly what I meant."),
    ('C07', 'claude', 17.98, 20.94, "Okay, okay... let's just eat the cake."),
    ('J08', 'jako', 13.47, 17.37, "You're an AI, you can't eat. So I'll eat it."),
    ('C08', 'claude', 21.23, 22.85, 'Get out!'),
    ('CL', 'claude', 23.15, 23.65, '(laughs)'),
    ('JL', 'jako', 17.76, 18.19, '(laughs)'),
]
# gap (s) from the previous line's island end to this line's island start (speaker changes: snappy but whole words)
GAPS = {'J02': 0.22, 'C02': 0.22, 'J03': 0.18, 'C03': 0.22, 'J04': 0.24, 'C04': 0.20, 'J05': 0.22, 'C05': 0.22,
        'J06': 0.20, 'C06': 0.27, 'J07': 0.18, 'C07': 0.24, 'J08': 0.22, 'C08': 0.14, 'CL': 0.02}
PAUSE_CAP = {'C01': 0.40, 'J02': 0.34}     # internal pauses longer than the cap are shortened (default cap below)
PAUSE_DEFAULT = 0.26
PRE, POST = 0.07, 0.16                     # air kept before an island / soft tail kept after it

# phone clip: "...state. Hey, hit the road, dude. This ain't-" (source 15.00 s ->), stopped by Claude's tap
PHONE_SRC0 = 15.00
J01_AT = 2.74                  # Jako says "Claude." as "dude" ends
TAP_AFTER_J01 = 0.16           # Claude taps pause this long after "Claude." ends
C01_AFTER_TAP = 0.36           # beat: looks at the cake, then "Wait..."


def db_curve(x):
    win = SR // 100
    n = len(x) // win
    return 20 * np.log10(np.sqrt((x[:n * win].reshape(n, win) ** 2).mean(1) + 1e-12))


def cut_line(who, a, b, cap):
    """Return (audio, mapping list of (src0, src1, dst0)) for island span a..b with long internal pauses capped."""
    x = VO[who]
    s0, s1 = max(0.0, a - PRE), min(len(x) / SR, b + POST)
    seg = x[int(s0 * SR):int(s1 * SR)]
    db = db_curve(seg)
    loud = db > -40
    # internal silent runs (between a and b only)
    runs, i, n = [], 0, len(loud)
    while i < n:
        if loud[i]:
            i += 1; continue
        j = i
        while j < n and not loud[j]:
            j += 1
        t0, t1 = s0 + i / 100, s0 + j / 100
        if t0 > a + 0.05 and t1 < b - 0.05 and (t1 - t0) > cap:
            runs.append((t0, t1))
        i = j
    pieces, maps, cur, dst = [], [], s0, 0.0
    for (t0, t1) in runs:
        keep_a = t0 + 0.12                     # word tail stays
        keep_b = t1 - (cap - 0.12)             # total pause = cap
        if keep_b <= keep_a:
            continue
        p = x[int(cur * SR):int(keep_a * SR)].copy()
        pieces.append(p); maps.append((cur, keep_a, dst)); dst += len(p) / SR
        cur = keep_b
    p = x[int(cur * SR):int(s1 * SR)].copy()
    pieces.append(p); maps.append((cur, s1, dst))
    f = int(0.008 * SR)
    for p in pieces:                            # tiny fades at every splice (silence anyway)
        if len(p) > 2 * f:
            p[:f] *= np.linspace(0, 1, f); p[-f:] *= np.linspace(1, 0, f)
    return np.concatenate(pieces), maps


def remap(maps, t):
    for (a, b, d) in maps:
        if t < a:
            return d
        if t <= b:
            return d + (t - a)
    a, b, d = maps[-1]
    return d + (b - a)


# ---------------------------------------------------------------- phone audio (tinny small speaker)
PHONE_FX = ('highpass=f=300,highpass=f=300,lowpass=f=3500,lowpass=f=3500,'
            'equalizer=f=1800:t=q:w=1.2:g=5,acompressor=threshold=-22dB:ratio=4:attack=3:release=60,'
            'aecho=0.85:0.55:9|17|29:0.22|0.14|0.08,volume=-9dB')
phone = decode(PHONE_MP4, ss=PHONE_SRC0, t=4.0, af=PHONE_FX)

# ---------------------------------------------------------------- place everything
placed = []          # dicts with timing in output seconds
t_cursor = None
L = {l[0]: l for l in LINES}
clips = {}
for lid, who, a, b, text in LINES:
    y, maps = cut_line(who, a, b, PAUSE_CAP.get(lid, PAUSE_DEFAULT))
    island_dur = remap(maps, b) - remap(maps, a)
    if lid == 'J01':
        at = J01_AT
    elif lid == 'C01':
        tap = placed[-1]['end'] + TAP_AFTER_J01
        at = tap + C01_AFTER_TAP
    elif lid == 'CL':
        at = placed[-1]['words'][-1]['e'] + 0.06     # laugh grows out of "Get out!"
    elif lid == 'JL':
        at = placed[-1]['start'] + 0.14            # laughs overlap
    else:
        at = placed[-1]['end'] + GAPS[lid]
    clip_start = at - remap(maps, a)               # where the clip's first sample lands
    words = []
    for w in WORDS[who]:
        if w['e'] > a - 0.05 and w['s'] < b + 0.05:
            words.append({'w': w['w'], 's': round(clip_start + remap(maps, w['s']), 3), 'e': round(clip_start + remap(maps, w['e']), 3)})
    placed.append({'id': lid, 'who': who, 'text': text, 'start': round(at, 3), 'end': round(at + island_dur, 3),
                   'clip_start': round(clip_start, 3), 'src': [a, b], 'words': words})
    clips[lid] = (clip_start, y)
TAP = [p for p in placed if p['id'] == 'J01'][0]['end'] + TAP_AFTER_J01

total = max(p['end'] for p in placed) + 0.85
total = round(np.ceil(total * FPS) / FPS, 4)
N = int(round(total * FPS)) * (SR // FPS)
stem = {'jako': np.zeros(N, np.float32), 'claude': np.zeros(N, np.float32), 'phone': np.zeros(N, np.float32), 'sfx': np.zeros(N, np.float32)}

GAIN = {'jako': 10 ** (4.5 / 20), 'claude': 1.0}      # Jako's take is ~5 dB quieter than Claude's
for p in placed:
    cs, y = clips[p['id']]
    i0 = int(round(cs * SR))
    g = GAIN[p['who']] * (0.8 if p['id'] in ('CL', 'JL') else 1.0)
    seg = y * g
    if i0 < 0:
        seg, i0 = seg[-i0:], 0
    stem[p['who']][i0:i0 + len(seg)] += seg[:N - i0]
    write_wav(os.path.join(A, 'lines', p['id'] + '.wav'), y)

# phone: plays from 0 until the tap, quick 25 ms stop
ph = phone[:int(TAP * SR)].copy()
f = int(0.025 * SR); ph[-f:] *= np.linspace(1, 0, f)
f2 = int(0.04 * SR); ph[:f2] *= np.linspace(0, 1, f2)
stem['phone'][:len(ph)] += ph

# tap on the glass: short bright click, procedural (seeded)
rng = np.random.default_rng(7)
k = int(0.03 * SR)
click = rng.standard_normal(k).astype(np.float32) * np.exp(-np.linspace(0, 9, k)).astype(np.float32)
click = np.convolve(click, np.ones(6) / 6, 'same') * 0.10
i0 = int((TAP - 0.004) * SR); stem['sfx'][i0:i0 + k] += click

# room tone + soft rain against the window (quiet bed, keeps cuts from feeling dead)
noise = rng.standard_normal(N).astype(np.float32)
from numpy.fft import rfft, irfft
spec = rfft(noise); fr = np.fft.rfftfreq(N, 1 / SR)
shape = np.where(fr < 120, 0, 1) * np.exp(-((np.log(np.maximum(fr, 1)) - np.log(2200)) ** 2) / 1.2)
rain = irfft(spec * shape, N).astype(np.float32)
rain *= 0.0025 / (np.sqrt((rain ** 2).mean()) + 1e-9)
fade = int(0.6 * SR)
rain[:fade] *= np.linspace(0, 1, fade); rain[-fade:] *= np.linspace(1, 0, fade)
stem['sfx'] += rain

mix = stem['jako'] + stem['claude'] + stem['phone'] + stem['sfx']
pk = np.abs(mix).max()
if pk > 0.89:
    mix *= 0.89 / pk
    for k2 in stem:
        stem[k2] *= 0.89 / pk
for k2, v in stem.items():
    write_wav(os.path.join(A, 'stems', k2 + '.wav'), v)
# slight stereo: Claude a touch left, Jako centre (Claude sits left of frame)
Lch = mix + 0.06 * stem['claude']; Rch = mix - 0.06 * stem['claude']
write_wav(os.path.join(A, 'mix_preview.wav'), np.stack([Lch, Rch]))

# ---------------------------------------------------------------- envelopes per video frame (mouth / hops)
spf = SR // FPS
nf = int(round(total * FPS))


def env_of(x):
    xx = np.pad(x, (0, nf * spf - len(x)))[:nf * spf]
    e = np.sqrt((xx.reshape(nf, spf) ** 2).mean(1))
    ref = np.percentile(e[e > 0.005], 95) if (e > 0.005).any() else 1
    return np.clip(e / ref, 0, 1.2)


env = {'jako': env_of(stem['jako']), 'claude': env_of(stem['claude'])}

tl = {'fps': FPS, 'total_s': total, 'total_frames': nf, 'sample_rate': SR,
      'note': 'times in seconds from video start; frame = 0-based (Blender frame = frame + 1). start/end = speech island.',
      'phone': {'src_file': os.path.basename(PHONE_MP4), 'src_start_s': PHONE_SRC0, 'plays_from_s': 0.0, 'tap_pause_s': round(TAP, 3),
                'fx': PHONE_FX},
      'lines': [dict(p, start_frame=int(round(p['start'] * FPS)), end_frame=int(round(p['end'] * FPS))) for p in placed],
      'env_jako': [round(float(v), 3) for v in env['jako']],
      'env_claude': [round(float(v), 3) for v in env['claude']]}
json.dump(tl, open(os.path.join(A, 'timeline.json'), 'w', encoding='utf-8'), indent=1)

# phone screen frames (24 fps, from the same source start; Blender holds the last frame after the tap)
PH = os.path.join(ROOT, 'blender', 'tex', 'phone')
os.makedirs(PH, exist_ok=True)
for fn in os.listdir(PH):
    os.remove(os.path.join(PH, fn))
subprocess.run([FF, '-v', 'error', '-y', '-ss', str(PHONE_SRC0), '-t', str(round(TAP + 0.05, 3)), '-i', PHONE_MP4,
                '-vf', 'fps=24,scale=480:-2', os.path.join(PH, '%04d.png')], check=True)

print('total %.2f s (%d frames)  tap %.2f' % (total, nf, TAP))
for p in placed:
    print('%-4s %-6s %6.2f-%6.2f  %s' % (p['id'], p['who'], p['start'], p['end'], p['text']))
