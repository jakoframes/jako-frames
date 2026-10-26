import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from au import *

tl = json.load(open(os.path.join(ROOT, "timeline.json"), encoding="utf-8"))
stem = {k: decode(os.path.join(ROOT, "stems", k + ".wav"), ch=2) for k in ("dialogue", "sfx", "ambience")}
mix = decode(os.path.join(ROOT, "mix_preview.wav"), ch=2)
print("lengths", {k: len(v) / SR for k, v in stem.items()}, len(mix) / SR, "nan:", np.isnan(mix).any())
print("DC offset mix", mix.mean(axis=0))


def rms(x):
    return db(np.sqrt(np.mean(x ** 2)) if len(x) else 0)


print("\nper-shot RMS dB (final levels): dialogue(active) | sfx | ambience | mix")
for s in tl["shots"]:
    a, b = int(s["start_s"] * SR), int(s["end_s"] * SR)
    print(f'{s["shot"]:2d} {active_rms_db(stem["dialogue"][a:b], -45):7.1f} {rms(stem["sfx"][a:b]):7.1f} {rms(stem["ambience"][a:b]):7.1f} {rms(mix[a:b]):7.1f}')

bands = [63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]


def octave(x):
    x = x.mean(axis=1) if x.ndim > 1 else x
    X = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2
    f = np.fft.rfftfreq(len(x), 1 / SR)
    tot = X.sum()
    return [round(10 * np.log10(X[(f >= c / 1.414) & (f < c * 1.414)].sum() / tot + 1e-12), 1) for c in bands]


print("\noctave balance (dB rel total) ", bands)
for name in ["amb_wind_pines", "amb_birds_distant", "amb_cowbells_far", "amb_crickets_dusk", "amb_campfire", "keyboard_typing",
             "whoosh_01", "pop_01", "bloop_screen_01_calendar", "footsteps_grass_run"]:
    x = decode(os.path.join(ROOT, "sfx", name + ".wav"), ch=2)
    nz = x[np.abs(x).max(axis=1) > 1e-6]
    print(f"{name:28s} rms {rms(nz):6.1f} peak {db(np.abs(x).max()):6.1f}  {octave(nz)}")


def f0_est(x, fmin=70, fmax=600):
    x = x.mean(axis=1) if x.ndim > 1 else x
    out = []
    w = 2048
    for i in range(0, len(x) - w, 512):
        fr = x[i:i + w] * np.hanning(w)
        if np.sqrt(np.mean(fr ** 2)) < 10 ** (-35 / 20):
            continue
        ac = np.fft.irfft(np.abs(np.fft.rfft(fr, 4 * w)) ** 2)[:w]
        lo, hi = int(SR / fmax), int(SR / fmin)
        k = lo + np.argmax(ac[lo:hi])
        if ac[k] / ac[0] > 0.5:
            out.append(SR / k)
    return np.median(out) if out else float("nan")


print("\nmedian f0 raw -> processed (semitones)")
for lid in ["C01", "C02", "C03", "C06", "C08", "J01", "J04"]:
    r = f0_est(decode(os.path.join(ROOT, "lines_raw", lid + ".wav")))
    p = f0_est(decode(os.path.join(ROOT, "lines", lid + ".wav"), ch=2))
    print(lid, round(r, 1), "->", round(p, 1), round(12 * np.log2(p / r), 2))

# where in the timeline the mix is loudest (short-term)
f = frame_db(mix, hop=4800, win=14400)
print("\nshort-term (300ms) mix level max", round(f.max(), 1), "at", np.argmax(f) * 0.1, "s; min during speech-free tail", round(f[-25:].mean(), 1))
