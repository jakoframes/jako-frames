"""Voice treatment: lines_raw/*.wav -> lines/*.wav (48k stereo 24-bit)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from au import *

RAW = os.path.join(ROOT, "lines_raw")
OUT = os.path.join(ROOT, "lines")
rng = np.random.default_rng(7)

PITCH_ST = 4.5
PITCH = 2 ** (PITCH_ST / 12)

JAKO_AF = ("highpass=f=80:poles=2,"
           "equalizer=f=220:t=q:w=1.2:g=-1.5,"
           "equalizer=f=3200:t=q:w=1.0:g=2.5,"
           "treble=g=1.0:f=9000,"
           "acompressor=threshold=-24dB:ratio=2.5:attack=8:release=160:makeup=1:knee=4")
CLAUDE_AF = (f"rubberband=pitch={PITCH:.5f}:transients=mixed:formant=shifted:window=standard,"
             "highpass=f=140:poles=2,"
             "equalizer=f=300:t=q:w=1.0:g=-1.5,"
             "equalizer=f=4800:t=q:w=1.4:g=2.0,"
             "treble=g=1.5:f=9500,"
             "acompressor=threshold=-24dB:ratio=2.5:attack=6:release=140:makeup=1:knee=4,"
             "chorus=0.9:0.92:19|27:0.11|0.08:0.33|0.47:1.3|1.7")


def set_rms(x, target):
    return x * 10 ** ((target - active_rms_db(x, gate=-45)) / 20)


def limiter(x, thr_db=-3.0, look=0.004):
    """Lookahead peak limiter on (n,ch)."""
    thr = 10 ** (thr_db / 20)
    a = np.abs(x).max(axis=1) if x.ndim > 1 else np.abs(x)
    g = np.minimum(1.0, thr / np.maximum(a, 1e-9))
    w = max(2, int(look * SR))
    gp = np.concatenate([g, np.ones(w - 1)])
    gmin = sliding_window_view(gp, w).min(axis=1)
    k = np.ones(w) / w
    gs = np.convolve(np.concatenate([np.ones(w - 1) * gmin[0], gmin]), k, mode="valid")
    gs = np.minimum(gs, 1.0)
    return x * (gs[:, None] if x.ndim > 1 else gs)


def taps_ir(taps, lp, n_ms=400):
    """Sparse early-reflection IR (n,2) from [(ms, dB, pan)]. Direct path included."""
    n = int(n_ms / 1000 * SR)
    ir = np.zeros((n, 2))
    ir[0, :] = 1.0
    refl = np.zeros((n, 2))
    for ms, g, p in taps:
        i = int(ms / 1000 * SR)
        a = (p + 1) * np.pi / 4
        refl[i, 0] += 10 ** (g / 20) * np.cos(a) * np.sqrt(2)
        refl[i, 1] += 10 ** (g / 20) * np.sin(a) * np.sqrt(2)
    refl = fft_filter(refl, bandpass_H(200, lp, 1))
    return ir + refl


# Open-air: a few low-level reflections (ground/rocks/trees), one faint far slap. No diffuse hall.
OUTDOOR = taps_ir([(13, -17, -0.6), (17, -18, 0.6), (31, -22, -0.3), (37, -23, 0.4),
                   (57, -27, -0.8), (71, -28, 0.8), (185, -33, 0.3)], lp=5000)
OUTDOOR_CLAUDE = taps_ir([(11, -19, -0.6), (15, -20, 0.6), (29, -24, -0.3), (41, -25, 0.4),
                          (63, -29, -0.8), (185, -35, 0.3)], lp=5500)


def valley_echo(dry_st):
    """2-3 decaying, darker, smeared repeats from the far side of the valley."""
    out = dry_st.copy()
    tail = int(1.8 * SR)
    out = np.concatenate([out, np.zeros((tail, 2))])
    mono = dry_st.mean(axis=1)
    # v2 (user feedback): only a slight hint -- 2 repeats, -18 / -26 dB, darker
    for k, (d, g, lp, p) in enumerate([(0.62, -18.0, 2400, 0.4), (1.26, -26.0, 1500, -0.4)]):
        e = fft_filter(mono, bandpass_H(250, lp, 2)) * 10 ** (g / 20)
        smear = noise_ir(0.12 + 0.05 * k, 0.08 + 0.05 * k, rng, lp=lp, ch=1)[:, 0]
        e = np.convolve(e, smear)[:len(e) + 2000] * 0.9 + np.concatenate([e, np.zeros(2000)]) * 0.35
        e = pan(e, p)
        i = int(d * SR)
        out[i:i + len(e)] += e[:len(out) - i]
    return out


report = {}
for name in sorted(os.listdir(RAW)):
    if not name.endswith(".wav"):
        continue
    lid = name[:-4]
    x = decode(os.path.join(RAW, name))
    if lid.startswith("C"):
        # v2 (user feedback): Claude untouched -- original voice, only trim/fades (from split) + level match
        y = set_rms(x, -18.5)
        y = np.stack([y, y], axis=1)
        pre_peak = db(np.abs(y).max())
        y = limiter(y, -3.0)
        write_wav(os.path.join(OUT, name), y)
        r = {"dur": round(len(y) / SR, 3), "peak_db": round(db(np.abs(y).max()), 2),
             "active_rms_db": round(active_rms_db(y, -45), 2), "limiter_gr_db": round(max(0.0, pre_peak + 3.0), 2)}
        report[lid] = r
        print(lid, r)
        continue
    x = set_rms(x, -20.0)
    x = np.concatenate([x, np.zeros(int(0.05 * SR))])
    if lid.startswith("J"):
        y = ffilter(x, JAKO_AF)
        y = set_rms(y, -16.5 if lid == "J08" else -18.0)
        y = convolve(y, OUTDOOR)
        if lid == "J08":
            y = valley_echo(y)
    else:
        y = ffilter(x, CLAUDE_AF)
        y = set_rms(y, -18.5)
        y = convolve(y, OUTDOOR_CLAUDE)
    # trim trailing near-silence of the IR, keep a short tail
    lvl = np.abs(y).max(axis=1)
    last = np.nonzero(lvl > 10 ** (-70 / 20))[0][-1]
    y = y[:last + int(0.02 * SR)]
    pre_peak = db(np.abs(y).max())
    y = limiter(y, -3.0)
    y = fade(y, 0.004, 0.03)
    write_wav(os.path.join(OUT, name), y)
    r = {"dur": round(len(y) / SR, 3), "peak_db": round(db(np.abs(y).max()), 2),
         "active_rms_db": round(active_rms_db(y, -45), 2), "limiter_gr_db": round(max(0.0, pre_peak + 3.0), 2)}
    report[lid] = r
    print(lid, r)
json.dump(report, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice_report.json"), "w"), indent=1)

