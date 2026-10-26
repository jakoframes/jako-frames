import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from au import *

THR = -45.0
PAD = 0.060


def segments(x, thr, min_sil, min_seg=0.12):
    m = len(x) // 480
    f = 20 * np.log10(np.abs(x[:m * 480]).reshape(m, 480).max(axis=1) + 1e-12)  # 10 ms frame sample-peak
    loud = f > thr
    hop = 0.01
    segs = []
    i = 0
    n = len(loud)
    # find runs of loud frames, merge if gap < min_sil
    runs = []
    while i < n:
        if loud[i]:
            j = i
            while j < n and loud[j]:
                j += 1
            runs.append([i, j])
            i = j
        else:
            i += 1
    merged = []
    for r in runs:
        if merged and (r[0] - merged[-1][1]) * hop < min_sil:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    merged = [r for r in merged if (r[1] - r[0]) * hop >= min_seg]
    return [(a * hop, b * hop) for a, b in merged]


report = {}
for tag, src, prefix, min_sil in [("dev", SRC_DEV, "J", 0.85), ("mike", SRC_MIKE, "C", 0.45)]:
    x = decode(src)
    dur = len(x) / SR
    info = {"file": src, "duration_s": round(dur, 3)}
    for ms in (0.2, 0.3, 0.45, 0.6, 0.7, 0.9):
        info[f"count_minsil_{ms}"] = len(segments(x, THR, ms))
    segs = segments(x, THR, min_sil)
    info["min_sil_used"] = min_sil
    info["segments"] = []
    for k, (a, b) in enumerate(segs):
        seg_id = f"{prefix}{k+1:02d}"
        s0 = max(0, int((a - PAD) * SR))
        s1 = min(len(x), int((b + PAD) * SR))
        y = fade(x[s0:s1], 0.012, 0.035)
        peak = db(np.abs(y).max())
        # internal pauses (word gaps) at a stricter level
        sub = segments(x[int(a * SR):int(b * SR)], -40, 0.06, 0.03)
        info["segments"].append({"id": seg_id, "src_start": round(a, 3), "src_end": round(b, 3),
                                 "dur": round(b - a, 3), "padded_dur": round((s1 - s0) / SR, 3),
                                 "peak_db": round(peak, 1), "active_rms_db": round(active_rms_db(y), 1),
                                 "sub_runs": [(round(p, 2), round(q, 2)) for p, q in sub]})
        write_wav(os.path.join(ROOT, "lines_raw", f"{seg_id}.wav"), y)
    report[tag] = info

json.dump(report, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "split_report.json"), "w"), indent=1)
for tag, info in report.items():
    print("==", tag, info["duration_s"], "s; counts by min-silence:",
          {k: v for k, v in info.items() if k.startswith("count")})
    for s in info["segments"]:
        print(f'  {s["id"]} {s["src_start"]:6.2f}-{s["src_end"]:6.2f} dur {s["dur"]:.2f} peak {s["peak_db"]} rms {s["active_rms_db"]} words~{len(s["sub_runs"])} {s["sub_runs"]}')


