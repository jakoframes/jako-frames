import io
B = r'C:\Users\acer\Downloads\jako-frames\reel-1k-cake\blender'


def edit(path, reps):
    s = io.open(path, encoding='utf-8').read()
    for x, y in reps:
        if x not in s:
            print('MISSING in', path, ':', x[:70])
        s = s.replace(x, y)
    io.open(path, 'w', encoding='utf-8', newline='\n').write(s)


edit(B + r'\s3_anim.py', [
    ("def ccu(i, lid, t0, t1, lens=50, d0=1.25, d1=1.0, side=1, zoff=0.0):", "def ccu(i, lid, t0, t1, lens=40, d0=1.75, d1=1.45, side=1, zoff=0.10):"),
    ("        ccu(sid, lid, t0, t1, lens=48, d0=1.3, d1=1.05)", "        ccu(sid, lid, t0, t1, lens=40, d0=1.75, d1=1.45)"),
    ("        ccu(sid, lid, t0, t1, lens=42, d0=1.25, d1=1.05, zoff=0.04)              # room for arms-up",
     "        ccu(sid, lid, t0, t1, lens=35, d0=1.7, d1=1.45, zoff=0.12)               # room for arms-up"),
    ("        ccu(sid, lid, t0, t1, lens=50, d0=1.25, d1=1.02, side=0.7)", "        ccu(sid, lid, t0, t1, lens=40, d0=1.7, d1=1.4, side=0.7)"),
    ("        ccu(sid, lid, t0, t1, lens=50, d0=1.35, d1=0.92)                          # faster push",
     "        ccu(sid, lid, t0, t1, lens=40, d0=1.85, d1=1.3)                           # faster push"),
    ("        ccu(sid, lid, t0, t1, lens=60, d0=1.15, d1=0.85, side=0.8)                # creeping to ECU",
     "        ccu(sid, lid, t0, t1, lens=45, d0=1.55, d1=1.15, side=0.8)                # creeping in on the squint"),
    ("[(V(-0.42, -0.95, 1.05), V(-0.42, 0.36, 0.88)), (V(-0.26, -0.78, 1.03), V(-0.30, 0.36, 0.87))], 38, 3.2, C_HEAD, 'claude'))",
     "[(V(-0.55, -1.05, 1.10), V(-0.50, 0.36, 0.88)), (V(-0.38, -0.88, 1.08), V(-0.38, 0.36, 0.87))], 36, 3.2, C_HEAD, 'claude'))"),
    # phone chip: anchored on the tablet in S01, word-timed from the phone transcript
    ("with open(os.path.join(ROOT, 'subs', 'subs.json'), 'w', encoding='utf-8') as f:\n    json.dump({'fps': FPS, 'frames': FRAME_END, 'width': 1080, 'height': 1920, 'phone_chip': {'from': 0, 'to': F(tap) - 1, 'text': '...hit the road, dude'},",
     "sc.frame_set(F(1.2))\nco = world_to_camera_view(sc, O['CAM_S01'], PHONE.matrix_world.translation + V(0, 0, 0.10))\n"
     "src0 = TL['phone']['src_start_s']\n"
     "pw = [w for s_ in json.load(open(os.path.join(ROOT, 'audio', 'src', 'phone_words.json'), encoding='utf-8')) for w in s_['words']]\n"
     "pw = [{'w': w['w'], 'from': F(w['s'] - src0) - 1, 'to': F(w['e'] - src0) - 1} for w in pw if src0 - 0.05 <= w['s'] < src0 + tap]\n"
     "sc.frame_set(1)\n"
     "with open(os.path.join(ROOT, 'subs', 'subs.json'), 'w', encoding='utf-8') as f:\n"
     "    json.dump({'fps': FPS, 'frames': FRAME_END, 'width': 1080, 'height': 1920,\n"
     "               'phone_chip': {'from': 0, 'to': F(tap) - 1, 'x': round(co.x * 1080), 'y': round((1 - co.y) * 1920), 'words': pw},"),
])
print('done')
