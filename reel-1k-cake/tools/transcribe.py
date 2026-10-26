"""Transcribe an audio/video file with faster-whisper (small.en) -> JSON list of words {w, s, e}.
usage: python transcribe.py <in> <out.json> [start_s] [dur_s]
"""
import json, subprocess, sys
import numpy as np
from faster_whisper import WhisperModel

FF = r'C:\Users\acer\ffmpeg\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe'
src, out = sys.argv[1], sys.argv[2]
ss = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
dur = float(sys.argv[4]) if len(sys.argv) > 4 else None
cmd = [FF, '-v', 'error', '-ss', str(ss)] + (['-t', str(dur)] if dur else []) + ['-i', src, '-ac', '1', '-ar', '16000', '-f', 'f32le', '-']
x = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, dtype=np.float32)
model = WhisperModel('small.en', device='cpu', compute_type='int8')
res, _ = model.transcribe(x, word_timestamps=True, beam_size=5, vad_filter=False)
segs = []
for seg in res:
    segs.append({'s': round(seg.start + ss, 3), 'e': round(seg.end + ss, 3), 'text': seg.text.strip(),
                 'words': [{'w': w.word.strip(), 's': round(w.start + ss, 3), 'e': round(w.end + ss, 3)} for w in seg.words]})
    print('%7.2f-%7.2f  %s' % (seg.start + ss, seg.end + ss, seg.text.strip()), flush=True)
json.dump(segs, open(out, 'w', encoding='utf-8'), indent=1)
