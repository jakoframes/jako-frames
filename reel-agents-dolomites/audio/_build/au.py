"""Shared audio helpers (numpy + ffmpeg). No scipy available."""
import subprocess, json, re, wave, struct
import numpy as np

FF = r"C:\Users\acer\ffmpeg\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
SR = 48000
ROOT = r"C:\Users\acer\Downloads\jako-frames\reel-agents-dolomites\audio"
SRC_DEV = r"C:\Users\acer\Downloads\ElevenLabs_2026-10-22T19_31_51_Dev - English Speaking Korean Male Streamer_pvc_sp100_s50_sb75_v4.mp3"
SRC_MIKE = r"C:\Users\acer\Downloads\ElevenLabs_2026-10-22T19_33_36_Mike - Animation, Explainers & Gaming_pvc_sp100_s50_sb75_v4.mp3"


def decode(path, ch=1, af=None):
    """Decode any file to float32 numpy at 48k. Returns (n,) for mono or (n,ch)."""
    filt = "aresample=48000:resampler=soxr:precision=28"
    if af:
        filt = af + "," + filt
    cmd = [FF, "-v", "error", "-i", path, "-af", filt, "-ac", str(ch), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
    return x if ch == 1 else x.reshape(-1, ch)


def ffilter(x, af, ch_out=None):
    """Run a numpy signal through an ffmpeg filter chain (48k)."""
    x = np.asarray(x, dtype=np.float32)
    ch = 1 if x.ndim == 1 else x.shape[1]
    ch_out = ch_out or ch
    cmd = [FF, "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", str(ch), "-i", "-",
           "-af", af, "-ar", str(SR), "-ac", str(ch_out), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, input=x.tobytes(), capture_output=True, check=True).stdout
    y = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
    return y if ch_out == 1 else y.reshape(-1, ch_out)


def write_wav(path, x, bits=24):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    n, ch = x.shape
    x = np.clip(x, -1.0, 1.0 - 1e-9)
    if bits == 24:
        q = np.round(x * 8388607).astype(np.int32).reshape(-1)
        b = np.empty((q.size, 3), dtype=np.uint8)
        b[:, 0] = q & 0xFF
        b[:, 1] = (q >> 8) & 0xFF
        b[:, 2] = (q >> 16) & 0xFF
        data = b.tobytes()
        sw = 3
    else:
        data = np.round(x * 32767).astype("<i2").tobytes()
        sw = 2
    with wave.open(path, "wb") as w:
        w.setnchannels(ch)
        w.setsampwidth(sw)
        w.setframerate(SR)
        w.writeframes(data)


def read_wav(path):
    return decode(path, ch=2) if wave_channels(path) == 2 else decode(path)


def wave_channels(path):
    with wave.open(path, "rb") as w:
        return w.getnchannels()


def db(v):
    return 20 * np.log10(max(float(v), 1e-12))


def frame_db(x, hop=480, win=960):
    """Short-term RMS level in dB, 10 ms hop."""
    if x.ndim > 1:
        x = x.mean(axis=1)
    n = 1 + max(0, (len(x) - win) // hop)
    idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
    fr = x[idx]
    return 20 * np.log10(np.sqrt((fr ** 2).mean(axis=1)) + 1e-12)


def active_rms_db(x, gate=-50):
    """RMS over frames above gate (speech-active RMS)."""
    f = frame_db(x)
    act = f[f > gate]
    if len(act) == 0:
        return -120.0
    return 10 * np.log10(np.mean(10 ** (act / 10)))


def ebur128(path_or_x):
    """Integrated LUFS + true peak via ffmpeg ebur128."""
    if isinstance(path_or_x, str):
        cmd = [FF, "-hide_banner", "-nostats", "-i", path_or_x, "-af", "ebur128=peak=true", "-f", "null", "-"]
        out = subprocess.run(cmd, capture_output=True, text=True).stderr
    else:
        x = np.asarray(path_or_x, dtype=np.float32)
        ch = 1 if x.ndim == 1 else x.shape[1]
        cmd = [FF, "-hide_banner", "-nostats", "-f", "f32le", "-ar", str(SR), "-ac", str(ch), "-i", "-",
               "-af", "ebur128=peak=true", "-f", "null", "-"]
        out = subprocess.run(cmd, input=x.tobytes(), capture_output=True).stderr.decode("utf-8", "replace")
    summ = out[out.rfind("Summary:"):]
    I = float(re.search(r"I:\s+(-?[\d.]+|-inf) LUFS", summ).group(1).replace("-inf", "-120"))
    LRA = float(re.search(r"LRA:\s+(-?[\d.]+)", summ).group(1))
    tp = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", summ)
    TP = float(tp.group(1).replace("-inf", "-120")) if tp else None
    return {"I": I, "LRA": LRA, "TP": TP}


# ---------- DSP helpers (FFT based, no scipy) ----------
def fft_filter(x, H_func):
    """Zero-phase filter: multiply spectrum by H_func(freqs). Works on mono or (n,ch)."""
    n = x.shape[0]
    nfft = 1 << int(np.ceil(np.log2(n + 1)))
    f = np.fft.rfftfreq(nfft, 1 / SR)
    H = H_func(f)
    X = np.fft.rfft(x, n=nfft, axis=0)
    if x.ndim > 1:
        H = H[:, None]
    return np.fft.irfft(X * H, n=nfft, axis=0)[:n]


def bandpass_H(lo, hi, order=2):
    def H(f):
        f = np.maximum(f, 1e-3)
        h = np.ones_like(f)
        if lo:
            h *= 1 / np.sqrt(1 + (lo / f) ** (2 * order))
        if hi:
            h *= 1 / np.sqrt(1 + (f / hi) ** (2 * order))
        return h
    return H


def colored_noise(n, alpha, rng, ch=1):
    """1/f^alpha noise (alpha=1 pink, 2 brown), unit RMS."""
    w = rng.standard_normal((n, ch))
    def H(f):
        f = np.maximum(f, 15.0)
        return f ** (-alpha / 2)
    y = fft_filter(w, H)
    y /= y.std(axis=0, keepdims=True) + 1e-12
    return y if ch > 1 else y[:, 0]


def smooth_random(n, rate_hz, rng, ch=1):
    """Slow random modulation curve ~N(0,1) with given bandwidth."""
    y = colored_noise(n, 0, rng, ch)
    y = fft_filter(y, bandpass_H(None, rate_hz, order=4))
    y /= y.std(axis=0) + 1e-12
    return y


def stft_tv_filter(x, gain_fn, nfft=2048, hop=512):
    """Time-varying spectral filter. gain_fn(t_seconds, freqs)->gain array. Mono in/out."""
    win = np.hanning(nfft)
    n = len(x)
    pad = np.concatenate([np.zeros(nfft), x, np.zeros(nfft)])
    out = np.zeros_like(pad)
    norm = np.zeros_like(pad)
    freqs = np.fft.rfftfreq(nfft, 1 / SR)
    for s in range(0, len(pad) - nfft, hop):
        t = (s - nfft + nfft / 2) / SR
        X = np.fft.rfft(pad[s:s + nfft] * win)
        y = np.fft.irfft(X * gain_fn(t, freqs), n=nfft) * win
        out[s:s + nfft] += y
        norm[s:s + nfft] += win ** 2
    out = out / np.maximum(norm, 1e-3)
    return out[nfft:nfft + n]


def pan(x, p):
    """Equal-power pan, p in [-1,1]. Returns (n,2)."""
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1)


def fade(x, fin, fout):
    x = x.copy()
    a, b = int(fin * SR), int(fout * SR)
    if a > 0:
        r = np.sin(np.linspace(0, np.pi / 2, a)) ** 2
        x[:a] *= r if x.ndim == 1 else r[:, None]
    if b > 0:
        r = np.cos(np.linspace(0, np.pi / 2, b)) ** 2
        x[-b:] *= r if x.ndim == 1 else r[:, None]
    return x


def env_curve(n, points):
    """Piecewise-linear envelope from [(t, value), ...]."""
    t = np.arange(n) / SR
    ts, vs = zip(*points)
    return np.interp(t, ts, vs)


def noise_ir(dur, rt60, rng, lp=6000, ch=2, predelay=0.0):
    """Simple decaying-noise reverb IR."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    e = np.exp(-6.91 * t / rt60)
    ir = rng.standard_normal((n, ch)) * e[:, None]
    ir = fft_filter(ir, bandpass_H(150, lp, 1))
    ir /= np.sqrt((ir ** 2).sum(axis=0, keepdims=True)) + 1e-12
    if predelay:
        ir = np.concatenate([np.zeros((int(predelay * SR), ch)), ir])
    return ir


def convolve(x, ir):
    """FFT convolution. x mono or (n,ch); ir (m,ch). Returns (n+m-1, ch)."""
    if x.ndim == 1:
        x = np.repeat(x[:, None], ir.shape[1], axis=1)
    n = x.shape[0] + ir.shape[0] - 1
    nfft = 1 << int(np.ceil(np.log2(n)))
    Y = np.fft.rfft(x, nfft, axis=0) * np.fft.rfft(ir, nfft, axis=0)
    return np.fft.irfft(Y, nfft, axis=0)[:n]
