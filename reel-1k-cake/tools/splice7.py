"""Framing fixes after the animatic: S01 start keeps Claude in frame, S04 'What?' less tight, S08 Jako centred."""
import io
B = r'C:\Users\acer\Downloads\jako-frames\reel-1k-cake\blender'
P = B + r'\s3_anim.py'
s = io.open(P, encoding='utf-8').read()
reps = [
    ("[(V(-0.06, -2.55, 1.30), V(-0.06, 0.55, 1.20)), (V(-0.12, -2.0, 1.26), V(-0.12, 0.55, 1.15))], 40, 2.8, MID, None))",
     "[(V(-0.10, -2.75, 1.30), V(-0.10, 0.55, 1.20)), (V(-0.14, -2.05, 1.26), V(-0.14, 0.55, 1.15))], 38, 2.8, MID, None))"),
    ("        jcu(sid, lid, t0, t1, side=-0.6, lens=70, d0=1.5, d1=1.25)               # punch-in",
     "        jcu(sid, lid, t0, t1, side=-0.6, lens=55, d0=1.55, d1=1.32)              # punch-in"),
    ("        jcu(sid, lid, t0, t1, side=-1, lens=60, d0=1.55, d1=1.35)",
     "        jcu(sid, lid, t0, t1, side=-0.5, lens=50, d0=1.6, d1=1.4)"),
]
for x, y in reps:
    if x not in s:
        print('MISSING', x[:80])
    s = s.replace(x, y)
io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('done')
