# ---------------------------------------------------------------- floor dressing: gift boxes, floor balloons, confetti (fills the vertical wide)
GIFTS = [((-0.78, -0.30), (0.30, 0.28, 0.26), '#E8845C', '#FFF3E0', 12), ((-0.42, -0.42), (0.20, 0.20, 0.17), '#F1EDE5', '#E8845C', -20),
         ((0.70, -0.32), (0.34, 0.30, 0.22), '#3F5A7A', '#F7C548', 8), ((0.98, -0.12), (0.22, 0.22, 0.30), '#F7C548', '#E8845C', -10),
         ((0.74, -0.33), (0.18, 0.18, 0.15), '#E8845C', '#FFFFFF', 30)]
for i, ((x, y), (w, d, h), c, rc, rz) in enumerate(GIFTS):
    z0 = 0.012 + (0.22 if i == 4 else 0.0)
    gb = empty('gift_%d' % i, PROPS, loc=(x, y, z0), rot=(0, 0, math.radians(rz)), size=0.1)
    gm = pbr('MAT_gift_%d' % i, c, 0.45, coat=0.3)
    rm = pbr('MAT_ribbon_%d' % i, rc, 0.3, coat=0.5, sheen=0.4)
    rbox('gift_box', (w, d, h), (0, 0, h / 2), 0.006, 2, PROPS, [gm], parent=gb)
    rbox('gift_lid', (w + 0.012, d + 0.012, 0.035), (0, 0, h + 0.012), 0.006, 2, PROPS, [gm], parent=gb)
    rbox('gift_ribbon_x', (w + 0.016, 0.028, h + 0.05), (0, 0, (h + 0.03) / 2), 0.003, 1, PROPS, [rm], parent=gb)
    rbox('gift_ribbon_y', (0.028, d + 0.016, h + 0.05), (0, 0, (h + 0.03) / 2), 0.003, 1, PROPS, [rm], parent=gb)
    for s in (-1, 1):
        obj('gift_bow', m_sphere('bow', (0.045, 0.018, 0.03), (s * 0.04, 0, h + 0.055), 14, 8), PROPS, gb, rot=(0, math.radians(s * 25), 0), mats=[rm])
for i, (x, y, c) in enumerate(((-1.25, -0.1, '#E8845C'), (1.28, 0.25, '#F7C548'))):
    obj('floor_balloon', m_sphere('fbal', (0.15, 0.15, 0.17), (0, 0, 0.17), 32, 16), PROPS, loc=(x, y, 0.0),
        mats=[pbr('MAT_fballoon_%d' % i, c, 0.18, coat=0.8)])
CONF = [pbr('MAT_conf_%d' % i, c, 0.4) for i, c in enumerate(['#F7C548', '#E8845C', '#7FC8F8', '#FFFFFF', '#9B5CFF', '#2FBF66'])]
for i in range(260):
    x = rnd.uniform(-1.2, 1.2); y = rnd.uniform(-1.15, 0.05)
    obj('confetti', m_box('cf', (0.018, 0.012, 0.0015)), PROPS, loc=(x, y, 0.016), rot=(0, 0, rnd.random() * math.pi), mats=[rnd.choice(CONF)])

