"""Timeline + procedural SFX/ambience + mix for 'Who are they?' (Dolomites)."""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from au import *

FPS = 24
SFXD = os.path.join(ROOT, "sfx")
STEMS = os.path.join(ROOT, "stems")
split = json.load(open(os.path.join(HERE, "split_report.json")))
speech = {s["id"]: s["dur"] for k in ("dev", "mike") for s in split[k]["segments"]}
PAD = 0.06

TEXT = {
    "J01": "Who are they?", "J02": "Whaaat?", "J03": "What is this place?", "J04": "Why Dolomites?",
    "J05": "What are they doing?", "J06": "Why?", "J07": "Really?", "J08": "Come to the office!",
    "J09": "Ohhh, this one's planning, this one's analysing?", "J10": "So that's how my agents work.",
    "J11": "Thank you. Let's relax.",
    "C01": "Your agents.", "C02": "Yep. Planner, analyst, caption writer, video director... and trend scout.",
    "C03": "Italy. Dolomites.", "C04": "'Cause you love it here.", "C05": "Just chilling.",
    "C06": "No task yet. Ask them something, they'll come to the office.", "C07": "Yep. Call 'em.",
    "C08": "They're on your project now. You don't need to do anything.", "C09": "You're right.",
    "C10": "Everything is for you.",
}
# (line, silence before its speech onset)
ORDER = [("J01", 0.25), ("C01", 0.32), ("J02", 0.28), ("C02", 0.40), ("J03", 0.45), ("C03", 0.55),
         ("J04", 0.60), ("C04", 0.30), ("J05", 0.45), ("C05", 0.28), ("J06", 0.25), ("C06", 0.28),
         ("J07", 0.30), ("C07", 0.28), ("J08", 0.40), ("C08", 4.60), ("J09", 0.35), ("C09", 0.28),
         ("J10", 0.45), ("C10", 0.32), ("J11", 0.50)]
TAIL = 3.0

L = {}
t = 0.0
for lid, gap in ORDER:
    s = t + gap
    L[lid] = {"speech_start": s, "speech_end": s + speech[lid], "clip_start": s - PAD}
    t = s + speech[lid]
TOTAL = t + TAIL
N = int(round(TOTAL * SR))


def fr(x):
    return int(round(x * FPS))


def snap(x):
    return fr(x) / FPS


st = lambda k: L[k]["speech_start"]
en = lambda k: L[k]["speech_end"]
c02 = L["C02"]["clip_start"]
cuts = [0.0,
        st("C01") - 0.12,          # 1 -> 2
        st("J02") - 0.10,          # 2 -> 3
        st("C02") - 0.08,          # 3 -> 4 (fast cuts)
        st("J03") - 0.15,          # 4 -> 5
        en("J03") + 0.12,          # 5 -> 6 drone
        st("J04") - 0.12,          # 6 -> 7
        st("C04") - 0.10,          # 7 -> 8
        st("J05") - 0.15,          # 8 -> 9
        st("J08") - 0.15,          # 9 -> 10
        en("J08") + 0.30,          # 10 -> 11 gathering
        st("C08") - 0.45,          # 11 -> 12 inside office
        st("J10") - 0.15,          # 12 -> 13
        en("C10") + 0.15,          # 13 -> 14 walk + crane
        TOTAL]
cuts = [snap(c) for c in cuts[:-1]] + [TOTAL]
SHOT_NAMES = ["Meadow ridge, behind-the-shoulder", "Low angle on Claude", "Close-up Jako (surprise)",
              "Fast cuts: the 5 agents", "Medium two-shot, Jako looks around", "Drone orbit over meadow",
              "Two-shot, Jako turns to Claude", "Close on Claude, pan across peaks", "Two-shot Q&A, agents chilling",
              "Low hero angle, shout", "Agents gather: antennas, run, desks, screens", "Inside office dolly, typing",
              "Close-up Jako, smile", "Walk to campfire, crane up"]
# Shot 4 sub-cuts on the agent names (onsets measured in C02's envelope, seconds from clip start)
NAME_ON = {"planner": 0.85, "analyst": 1.45, "caption-writer": 2.12, "video-director": 2.98, "trend-scout": 4.08}
sub_starts = [cuts[3]] + [snap(c02 + NAME_ON[k] - 0.05) for k in ["analyst", "caption-writer", "video-director", "trend-scout"]]
sub_ends = sub_starts[1:] + [cuts[4]]
subshots = [{"agent": a, "start_s": round(s, 3), "end_s": round(e, 3), "start_frame": fr(s), "end_frame": fr(e)}
            for a, s, e in zip(["planner", "analyst", "caption-writer", "video-director", "trend-scout"], sub_starts, sub_ends)]


def shot_of(x):
    for i in range(14):
        if cuts[i] <= x < cuts[i + 1]:
            return i + 1
    return 14


rng = np.random.default_rng(2026)
tt = np.arange(N) / SR

# ------------------------------------------------------------------ dialogue
dialogue = np.zeros((N, 2))
for lid in L:
    y = decode(os.path.join(ROOT, "lines", lid + ".wav"), ch=2)
    i = int(round(L[lid]["clip_start"] * SR))
    m = min(len(y), N - i)
    dialogue[i:i + m] += y[:m]
    L[lid]["clip_end"] = L[lid]["clip_start"] + len(y) / SR

# speech activity envelope for ambience ducking
act = np.zeros(N)
for lid in L:
    a, b = int(L[lid]["speech_start"] * SR), int(L[lid]["speech_end"] * SR)
    act[a:b] = 1.0
k = int(0.25 * SR)
act = np.convolve(act, np.ones(k) / k, mode="same")

# ------------------------------------------------------------------ helpers
events = []  # sfx placements for timeline.json


def place(buf, y, t0, p=None):
    if y.ndim == 1:
        y = pan(y, p or 0.0)
    i = int(round(t0 * SR))
    if i < 0:
        y, i = y[-i:], 0
    m = min(len(y), N - i)
    if m > 0:
        buf[i:i + m] += y[:m]


def save_sfx(name, y, t0, shot_note=None, kind="sfx"):
    if y.ndim == 1:
        y = np.stack([y, y], axis=1)
    write_wav(os.path.join(SFXD, name), y)
    events.append({"id": name[:-4], "file": f"sfx/{name}", "type": kind, "start_s": round(t0, 3),
                   "end_s": round(t0 + len(y) / SR, 3), "shot": shot_note or shot_of(t0 + 0.01)})


def norm_rms(x, target_db):
    r = np.sqrt(np.mean(x ** 2))
    return x * 10 ** (target_db / 20) / (r + 1e-12)


def norm_peak(x, target_db):
    return x * 10 ** (target_db / 20) / (np.abs(x).max() + 1e-12)


def gliss(f0, f1, dur, curve=1.0):
    n = int(dur * SR)
    u = np.linspace(0, 1, n) ** curve
    f = f0 + (f1 - f0) * u
    return 2 * np.pi * np.cumsum(f) / SR


def adsr(n, a, d_tau):
    t = np.arange(n) / SR
    e = np.exp(-np.maximum(t - a, 0) / d_tau)
    e[t < a] = (t[t < a] / a) if a > 0 else 1
    return e


def bp_center_gain(fc, bw):
    def g(f):
        f = np.maximum(f, 1.0)
        return 1 / np.sqrt(1 + ((f / fc - fc / f) / bw) ** 2)
    return g


# ------------------------------------------------------------------ AMBIENCE: wind through pines
gust = smooth_random(N, 0.12, rng)
g01 = 1 / (1 + np.exp(-1.6 * gust))
shift = int(0.45 * SR)
g01R = np.concatenate([g01[shift:], g01[-shift:]])
wind = np.zeros((N, 2))
for ch, gg in ((0, g01), (1, g01R)):
    pink = colored_noise(N, 1.0, rng)
    air = stft_tv_filter(pink, lambda t_, f, gg=gg: bp_center_gain(350 + 900 * gg[min(N - 1, max(0, int(t_ * SR)))], 1.1)(f))
    air *= 0.35 + 0.65 * gg ** 1.5
    needles = fft_filter(colored_noise(N, 1.0, rng), bandpass_H(1800, 7000, 2)) * (gg ** 2) * 0.45
    rumble = fft_filter(colored_noise(N, 2.0, rng), bandpass_H(25, 140, 2)) * (0.5 + 0.5 * gg) * 0.3
    wind[:, ch] = air + needles + rumble
wind = norm_rms(fft_filter(wind, bandpass_H(55, None, 2)), -30.0)
# macro: swell on the drone shot and on the final crane-up
macro = env_curve(N, [(0, 1.0), (cuts[5], 1.0), (cuts[5] + 0.8, 1.35), (cuts[6], 1.25), (cuts[6] + 0.6, 1.0),
                      (cuts[13], 1.0), (cuts[13] + 2.0, 1.25), (TOTAL, 1.25)])
wind *= macro[:, None]

# ------------------------------------------------------------------ AMBIENCE: distant birds
birds = np.zeros((N, 2))
bird_rate = env_curve(N, [(0, 0.5), (16, 0.45), (24, 0.2), (30, 0.06), (33, 0.0), (TOTAL, 0.0)])
t_ev = 0.4
while t_ev < TOTAL:
    r = bird_rate[min(N - 1, int(t_ev * SR))]
    if r <= 0.001:
        break
    t_ev += rng.exponential(1 / max(r, 0.01))
    if t_ev > TOTAL - 1:
        break
    sp = rng.choice(["whistle", "trill", "feebee"], p=[0.45, 0.35, 0.2])
    gain = 10 ** (rng.uniform(-10, 0) / 20)
    p = rng.uniform(-0.85, 0.85)
    tt0 = t_ev
    if sp == "whistle":
        for _ in range(rng.integers(2, 6)):
            d = rng.uniform(0.07, 0.16)
            f0 = rng.uniform(2700, 3700)
            ph = gliss(f0, f0 + rng.uniform(-700, 700), d, rng.uniform(0.6, 1.8))
            n = len(ph)
            vib = 0.15 * np.sin(2 * np.pi * 28 * np.arange(n) / SR)
            y = (np.sin(ph + vib) + 0.08 * np.sin(2 * ph)) * np.sin(np.linspace(0, np.pi, n)) ** 1.5
            place(birds, y * gain, tt0, p)
            tt0 += d + rng.uniform(0.04, 0.10)
    elif sp == "trill":
        rate = rng.uniform(11, 16)
        f0 = rng.uniform(4000, 5400)
        for _ in range(rng.integers(4, 9)):
            d = rng.uniform(0.025, 0.04)
            ph = gliss(f0, f0 - rng.uniform(900, 1600), d, 0.7)
            n = len(ph)
            y = np.sin(ph) * np.sin(np.linspace(0, np.pi, n)) ** 2
            place(birds, y * gain * 0.8, tt0, p)
            tt0 += 1 / rate
    else:
        f0 = rng.uniform(3600, 4100)
        for f, d in ((f0, 0.24), (f0 * 0.84, 0.30)):
            ph = gliss(f, f * 0.98, d)
            n = len(ph)
            y = np.sin(ph) * np.sin(np.linspace(0, np.pi, n)) ** 1.2
            place(birds, y * gain * 0.7, tt0, p)
            tt0 += d + 0.05
birds = fft_filter(birds, bandpass_H(1500, 7000, 1))
forest = noise_ir(1.3, 0.9, rng, lp=5000, predelay=0.015)
birds = 0.75 * birds + 0.45 * convolve(birds, forest)[:N] * 0.6
birds = norm_peak(birds, -27.0)

# ------------------------------------------------------------------ AMBIENCE: far cow bells (valley)
cows = np.zeros((N, 2))
ratios = np.array([1.0, 2.02, 2.66, 3.41, 4.31, 5.23])
amps = np.array([1.0, 0.55, 0.45, 0.3, 0.2, 0.12])
t_ev = 1.0
while t_ev < 26:
    f0 = rng.uniform(480, 640)
    p = rng.uniform(-0.75, -0.25)
    tc = t_ev
    for _ in range(rng.integers(2, 5)):
        dur = 0.9
        n = int(dur * SR)
        tn = np.arange(n) / SR
        y = np.zeros(n)
        for r_, a_ in zip(ratios, amps):
            y += a_ * np.sin(2 * np.pi * f0 * r_ * tn + rng.uniform(0, 6.28)) * np.exp(-tn / (0.5 / r_ ** 0.6))
        y[:int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))
        place(cows, y * rng.uniform(0.5, 1.0), tc, p)
        tc += rng.uniform(0.12, 0.35)
    t_ev += rng.uniform(3.5, 7.0)
cows = fft_filter(cows, bandpass_H(300, 2400, 2))
valley = noise_ir(2.2, 1.7, rng, lp=2200, predelay=0.06)
cows = 0.35 * cows + convolve(cows, valley)[:N] * 0.5
cows *= env_curve(N, [(0, 1), (20, 1), (27, 0), (TOTAL, 0)])[:, None]
cows = norm_peak(cows, -37.0)

# ------------------------------------------------------------------ AMBIENCE: crickets at dusk
crk = np.zeros((N, 2))
for f0, prate, chirp_n, period, p in [(4400, 30, 3, 0.48, -0.6), (4800, 34, 4, 0.62, 0.55), (4100, 27, 3, 0.41, 0.1),
                                       (5150, 40, 0, 0, -0.2)]:
    tn = tt
    car = np.sin(2 * np.pi * f0 * tn + 0.6 * np.sin(2 * np.pi * 3 * tn))
    pulse = np.clip(np.sin(2 * np.pi * prate * tn), 0, None) ** 3
    if chirp_n:
        ph = (tn + rng.uniform(0, period)) % period
        gate = (ph < chirp_n / prate).astype(float)
        gate = np.convolve(gate, np.ones(96) / 96, mode="same")
        amp_mod = gate * (0.8 + 0.2 * smooth_random(N, 0.3, rng))
    else:  # a far triller with slow swell
        amp_mod = 0.45 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * tn + 1.0))
    crk += pan(car * pulse * amp_mod, p)
crk = fft_filter(crk, bandpass_H(2500, 8000, 1))
crk = 0.8 * crk + convolve(crk, noise_ir(0.8, 0.6, rng, lp=7000))[:N] * 0.35
crk = norm_peak(crk, -27.0)
crk *= env_curve(N, [(0, 0), (19.5, 0), (27.0, 1.0), (cuts[13], 1.15), (TOTAL, 1.3)])[:, None]

# ------------------------------------------------------------------ AMBIENCE: campfire (shot 14)
def campfire(n, rng):
    tn = np.arange(n) / SR
    mod = 0.6 + 0.4 * (1 / (1 + np.exp(-1.5 * smooth_random(n, 0.8, rng))))
    roar = fft_filter(colored_noise(n, 2.0, rng, ch=2), bandpass_H(70, 260, 2)) * mod[:, None]
    breath = fft_filter(colored_noise(n, 1.0, rng, ch=2), bandpass_H(250, 900, 2)) * (mod[:, None] ** 2) * 0.35
    hiss = fft_filter(colored_noise(n, 1.0, rng, ch=2), bandpass_H(2500, 7000, 2)) * 0.06
    bed = norm_rms(roar + breath + hiss, -34)
    cr = np.zeros((n, 2))
    rate_c = 7 + 6 * (1 / (1 + np.exp(-2 * smooth_random(n, 1.5, rng))))
    t_c = 0.05
    while t_c < n / SR - 0.05:
        t_c += rng.exponential(1 / rate_c[int(t_c * SR)])
        if rng.random() < 0.12:  # sap pop, longer + lower
            Lc, tau, fc = int(0.04 * SR), rng.uniform(0.006, 0.014), rng.uniform(900, 2200)
            amp = rng.uniform(0.5, 1.0)
        else:
            Lc, tau, fc = int(0.012 * SR), rng.uniform(0.0004, 0.002), rng.uniform(1800, 7000)
            amp = min(1.0, 0.12 * rng.pareto(2.2) + 0.08)
        b = rng.standard_normal(Lc) * np.exp(-np.arange(Lc) / SR / tau)
        b = fft_filter(b, bandpass_H(fc / 1.7, fc * 1.7, 2))
        b = b / (np.abs(b).max() + 1e-9) * amp
        i = int(t_c * SR)
        m = min(Lc, n - i)
        cr[i:i + m] += pan(b[:m], rng.uniform(-0.3, 0.3))
    cr = norm_peak(cr, -16)
    return bed + cr


fire_start = cuts[13] - 0.6
fire = np.zeros((N, 2))
fire_len = N - int(fire_start * SR)
fire_clip = campfire(fire_len, rng)
fire_env = env_curve(fire_len, [(0, 0), (1.4, 0.55), (en("J11") - fire_start, 0.65),
                                (en("J11") - fire_start + 0.8, 1.0), (TOTAL - fire_start, 1.0)])
fire_clip *= fire_env[:, None]
place(fire, fire_clip, fire_start)

# ------------------------------------------------------------------ office muffling + ducking of the outdoor bed
outdoor = wind + birds + cows + crk
muffled = fft_filter(outdoor, bandpass_H(None, 1100, 2)) * 0.55
w_in = env_curve(N, [(0, 0), (cuts[11] - 0.15, 0), (cuts[11] + 0.25, 0.8), (cuts[12] - 0.2, 0.8), (cuts[12] + 0.4, 0.25),
                     (cuts[13] - 0.2, 0.25), (cuts[13] + 0.5, 0), (TOTAL, 0)])
outdoor = outdoor * (1 - w_in)[:, None] + muffled * w_in[:, None]
duck = 1 - 0.25 * act
ambience = (outdoor + fire) * duck[:, None]
# final fade of everything outdoor at the very end
end_fade = env_curve(N, [(0, 1), (TOTAL - 2.2, 1), (TOTAL, 0)])
ambience *= end_fade[:, None]

# ------------------------------------------------------------------ SFX
sfx = np.zeros((N, 2))


def whoosh(dur, direction, rng):
    n = int(dur * SR)
    x = colored_noise(n, 0.6, rng)
    pk = 0.62
    def g(t_, f):
        u = np.clip(t_ / dur, 0, 1)
        fc = 350 * (3200 / 350) ** (u / pk) if u < pk else 3200 * (900 / 3200) ** ((u - pk) / (1 - pk))
        return bp_center_gain(fc, 0.9)(f)
    y = stft_tv_filter(x, g, nfft=1024, hop=256)
    u = np.linspace(0, 1, n)
    env = np.where(u < pk, (u / pk) ** 2.2, np.exp(-(u - pk) / 0.12))
    y *= env
    ps = np.linspace(-0.7, 0.7, n) * direction
    a = (ps + 1) * np.pi / 4
    st2 = np.stack([y * np.cos(a), y * np.sin(a)], axis=1)
    return norm_peak(st2, -17.0), pk * dur


whoosh_times = [cuts[3]] + sub_starts[1:]
for k, tc in enumerate(whoosh_times):
    y, pk_t = whoosh(0.42, 1 if k % 2 == 0 else -1, rng)
    t0 = tc - pk_t
    place(sfx, y, t0)
    save_sfx(f"whoosh_{k+1:02d}.wav", y, t0)

T11 = cuts[10]
T12 = cuts[11]
agents_pan = [-0.55, -0.25, 0.0, 0.25, 0.55]
# antenna pops: cute upward "bwip"
pop_notes = [784, 880, 988, 1175, 1319]
for k, f in enumerate(pop_notes):
    d = 0.11
    ph = gliss(f * 0.55, f, d, 0.35)
    n = len(ph)
    env = adsr(n, 0.003, 0.035)
    y = (np.sin(ph) + 0.25 * np.sin(2 * ph)) * env
    click = rng.standard_normal(n) * np.exp(-np.arange(n) / SR / 0.0015) * 0.15
    y = norm_peak(fft_filter(y + click, bandpass_H(200, 9000, 1)), -12.0)
    y = pan(y, agents_pan[k])
    t0 = T11 + 0.20 + 0.19 * k
    place(sfx, y, t0)
    save_sfx(f"pop_{k+1:02d}.wav", y, t0)

# footsteps on grass, 5 small agents running in
steps = np.zeros((int(2.2 * SR), 2))
for k in range(5):
    t_s = 0.05 + 0.12 * k + rng.uniform(0, 0.06)
    p0, p1 = agents_pan[k] * 1.6, agents_pan[k] * 0.3
    nsteps = rng.integers(8, 11)
    for s_i in range(nsteps):
        n = int(0.09 * SR)
        e = adsr(n, 0.004, 0.022)
        swish = fft_filter(rng.standard_normal(n), bandpass_H(900, 5500, 2)) * e
        thump = np.sin(2 * np.pi * rng.uniform(85, 120) * np.arange(n) / SR) * adsr(n, 0.002, 0.018) * 0.5
        y = (swish / (np.abs(swish).max() + 1e-9) + thump) * rng.uniform(0.6, 1.0) * (0.6 + 0.4 * s_i / nsteps)
        u = s_i / max(1, nsteps - 1)
        y = pan(y, float(np.clip(p0 + (p1 - p0) * u, -1, 1)))
        i = int(t_s * SR)
        m = min(n, len(steps) - i)
        if m > 0:
            steps[i:i + m] += y[:m]
        t_s += rng.uniform(0.135, 0.165)
steps = norm_peak(steps, -19.0)
t_steps = T11 + 1.05
place(sfx, steps, t_steps)
save_sfx("footsteps_grass_run.wav", steps, t_steps)

# little chair/seat thumps
chairs = np.zeros((int(0.9 * SR), 2))
for k in range(5):
    n = int(0.12 * SR)
    tn = np.arange(n) / SR
    y = np.sin(2 * np.pi * (150 - 50 * tn / 0.12) * tn) * adsr(n, 0.003, 0.03)
    y += fft_filter(rng.standard_normal(n), bandpass_H(400, 2500, 2)) * adsr(n, 0.002, 0.01) * 0.08
    i = int((0.03 + 0.16 * k + rng.uniform(0, 0.04)) * SR)
    chairs[i:i + n] += pan(y, agents_pan[k] * 0.5)[:len(chairs) - i]
chairs = norm_peak(chairs, -21.0)
t_ch = T11 + 2.45
place(sfx, chairs, t_ch)
save_sfx("chairs_sit.wav", chairs, t_ch)

# screen "bloops" (calendar, chart, text, timeline, grid)
bloop_notes = [523.25, 587.33, 659.26, 783.99, 880.0]
screens = ["calendar", "chart", "text", "timeline", "grid"]
for k, f in enumerate(bloop_notes):
    d = 0.32
    n = int(d * SR)
    ph = gliss(f * 0.5, f, 0.07, 0.5)
    ph = np.concatenate([ph, ph[-1] + 2 * np.pi * f * np.arange(1, n - len(ph) + 1) / SR])
    env = adsr(n, 0.006, 0.09)
    y = (np.sin(ph) + 0.18 * np.sin(3 * ph) + 0.1 * np.sin(2 * ph)) * env
    y = fft_filter(y, bandpass_H(180, 5000, 2))
    y = norm_peak(y, -15.5)
    y = pan(y, agents_pan[k] * 0.8)
    t0 = T11 + 2.75 + 0.22 * k
    place(sfx, y, t0)
    save_sfx(f"bloop_screen_{k+1:02d}_{screens[k]}.wav", y, t0)

# soft keyboard typing (shot 12)
t_ty0, t_ty1 = T12 - 0.1, cuts[12] + 0.3
typ = np.zeros((int((t_ty1 - t_ty0) * SR), 2))
for p in (-0.6, -0.2, 0.25, 0.6):
    tk = rng.uniform(0, 0.8)
    while tk < (t_ty1 - t_ty0) - 0.2:
        burst = rng.integers(4, 16)
        for _ in range(burst):
            for rel, amp in ((0.0, 1.0), (rng.uniform(0.06, 0.09), 0.45)):
                n = int(0.03 * SR)
                c = fft_filter(rng.standard_normal(n), bandpass_H(1800, 7000, 2)) * adsr(n, 0.0005, 0.0018)
                th = np.sin(2 * np.pi * rng.uniform(170, 240) * np.arange(n) / SR) * adsr(n, 0.001, 0.010) * 0.35
                y = (c / (np.abs(c).max() + 1e-9) + th) * amp * rng.uniform(0.5, 1.0)
                i = int((tk + rel) * SR)
                m = min(n, len(typ) - i)
                if m > 0:
                    typ[i:i + m] += pan(y[:m], p + rng.uniform(-0.05, 0.05))
            tk += rng.gamma(4, 0.028)
        tk += rng.uniform(0.35, 1.1)
office = noise_ir(0.6, 0.35, rng, lp=7000, predelay=0.004)
typ = 0.8 * typ + convolve(typ, office)[:len(typ)] * 0.35
typ = norm_peak(typ, -23.0)
typ = fade(typ, 0.4, 0.5)
place(sfx, typ, t_ty0)
save_sfx("keyboard_typing.wav", typ, t_ty0)

# ------------------------------------------------------------------ write ambience beds (timeline-aligned, start 0)
for name, bed in (("amb_wind_pines.wav", wind), ("amb_birds_distant.wav", birds), ("amb_cowbells_far.wav", cows),
                  ("amb_crickets_dusk.wav", crk), ("amb_campfire.wav", fire)):
    write_wav(os.path.join(SFXD, name), bed)
    events.append({"id": name[:-4], "file": f"sfx/{name}", "type": "ambience_bed (raw, before duck/muffle/fade)",
                   "start_s": 0.0, "end_s": round(TOTAL, 3), "shot": "all"})

# ------------------------------------------------------------------ levels, loudness, limiter
def rms_db(x):
    return db(np.sqrt(np.mean(x ** 2)))


pre = {"dialogue_active_rms_db": round(active_rms_db(dialogue, -45), 2),
       "dialogue_peak_db": round(db(np.abs(dialogue).max()), 2),
       "ambience_rms_db": round(rms_db(ambience), 2),
       "ambience_rms_db_0_30s": round(rms_db(ambience[:30 * SR]), 2),
       "sfx_peak_db": round(db(np.abs(sfx).max()), 2)}
mix = dialogue + sfx + ambience
m0 = ebur128(mix)
gain_db = -14.0 - m0["I"]
g = 10 ** (gain_db / 20)
stems = {"dialogue": dialogue * g, "sfx": sfx * g, "ambience": ambience * g}
mixg = mix * g
limit_db = -1.4
for _ in range(6):
    lim = ffilter(mixg, f"aresample=192000,alimiter=limit={10 ** (limit_db / 20):.4f}:attack=1.5:release=60:level=0:asc=1,aresample=48000")
    if len(lim) < N:
        lim = np.concatenate([lim, np.zeros((N - len(lim), 2))])
    lim = lim[:N]
    lim = fade(lim, 0.0, 0.05)
    m1 = ebur128(lim)
    if m1["TP"] <= -1.0:
        break
    limit_db -= 0.3
write_wav(os.path.join(ROOT, "mix_preview.wav"), lim)
for k_, v in stems.items():
    write_wav(os.path.join(STEMS, f"{k_}.wav"), v)
post = {"mix_pre_gain": m0, "gain_applied_db": round(gain_db, 2), "limiter_ceiling_db": limit_db, "mix_final": m1,
        "dialogue_active_rms_db_final": round(active_rms_db(stems["dialogue"], -45), 2),
        "dialogue_peak_db_final": round(db(np.abs(stems["dialogue"]).max()), 2),
        "ambience_rms_db_final": round(rms_db(stems["ambience"]), 2),
        "sfx_peak_db_final": round(db(np.abs(stems["sfx"]).max()), 2)}

# ------------------------------------------------------------------ timeline.json
lines_out = []
for lid, _ in ORDER:
    d = L[lid]
    lines_out.append({"id": lid, "character": "Jako" if lid[0] == "J" else "Claude", "text": TEXT[lid],
                      "file": f"lines/{lid}.wav", "start_s": round(d["clip_start"], 3), "end_s": round(d["clip_end"], 3),
                      "speech_start_s": round(d["speech_start"], 3), "speech_end_s": round(d["speech_end"], 3),
                      "speech_start_frame": fr(d["speech_start"]), "speech_end_frame": fr(d["speech_end"]),
                      "shot": shot_of(d["speech_start"])})
shots = []
for i in range(14):
    s, e = cuts[i], cuts[i + 1]
    shots.append({"shot": i + 1, "name": SHOT_NAMES[i], "start_s": round(s, 3), "end_s": round(e, 3),
                  "duration_s": round(e - s, 3), "start_frame": fr(s), "end_frame": fr(e),
                  "lines": [l["id"] for l in lines_out if l["shot"] == i + 1]})
shots[3]["subshots"] = subshots
timeline = {"reel": "Who are they? (Dolomites, agents)", "fps": FPS, "sample_rate": SR,
            "total_duration_s": round(TOTAL, 3), "total_frames": fr(TOTAL),
            "notes": "Times in seconds from 0. Line start_s/end_s = clip file placement (file has 60 ms pre-roll + reverb/echo tail); "
                     "speech_start_s/speech_end_s = audible speech (use for lip-sync/acting). Shot cuts snapped to 24 fps frames. "
                     "Shot 4 subshot cuts sit on the agent-name onsets in C02 (estimated from the envelope, +-2 frames).",
            "shots": shots, "lines": lines_out, "sfx": sorted(events, key=lambda e: (e["start_s"], e["id"])),
            "mix": {"file": "mix_preview.wav", "stems": ["stems/dialogue.wav", "stems/sfx.wav", "stems/ambience.wav"],
                    "levels_nominal_before_final_gain": pre, **post}}
json.dump(timeline, open(os.path.join(ROOT, "timeline.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)

print("TOTAL", round(TOTAL, 3))
for s in shots:
    print(f'{s["shot"]:2d} {s["start_s"]:6.2f}-{s["end_s"]:6.2f} ({s["duration_s"]:.2f}s) f{s["start_frame"]}-{s["end_frame"]} {s["lines"]} {s["name"]}')
for s in subshots:
    print("   4.", s)
print(json.dumps(pre, indent=0))
print(json.dumps(post, indent=0))

