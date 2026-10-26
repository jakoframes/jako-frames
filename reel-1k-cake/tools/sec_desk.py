# ---------------------------------------------------------------- desk: simple wooden student desk ("парта"): flat top on four legs
DX0, DX1 = -DESK_W / 2, DESK_W / 2
LEG = 0.05
rbox('desk_top', (DESK_W, DESK_D, 0.045), (0, DESK_D / 2, DESK_H - 0.0225), 0.01, 3, PROPS, [WOOD_DESK])
rbox('desk_apron_F', (DESK_W - 0.12, 0.022, 0.075), (0, 0.05, DESK_H - 0.045 - 0.0375), 0.004, 2, PROPS, [WOOD_DESK])
rbox('desk_apron_B', (DESK_W - 0.12, 0.022, 0.075), (0, DESK_D - 0.05, DESK_H - 0.045 - 0.0375), 0.004, 2, PROPS, [WOOD_DESK])
for sx in (-1, 1):
    rbox('desk_apron_S', (0.022, DESK_D - 0.12, 0.075), (sx * (DESK_W / 2 - 0.05), DESK_D / 2, DESK_H - 0.045 - 0.0375), 0.004, 2, PROPS, [WOOD_DESK])
    for y in (0.05, DESK_D - 0.05):
        lg = m_cyl('leg', LEG / 2, LEG / 2 * 0.72, DESK_H - 0.045, (0, 0, (DESK_H - 0.045) / 2), 4, smooth=False)
        o = obj('desk_leg', lg, PROPS, loc=(sx * (DESK_W / 2 - 0.05), y, 0), rot=(0, 0, math.pi / 4), mats=[WOOD_DESK])
        mod_bevel(o, 0.004, 2)
    rbox('desk_stretcher', (0.025, DESK_D - 0.12, 0.03), (sx * (DESK_W / 2 - 0.05), DESK_D / 2, 0.14), 0.004, 2, PROPS, [WOOD_DESK])
rbox('desk_footbar', (DESK_W - 0.12, 0.03, 0.03), (0, DESK_D - 0.05, 0.14), 0.004, 2, PROPS, [WOOD_DESK])
# Jako's chair (tall: he is a 1.38 m chibi); mostly hidden behind him
CH_Y, SEAT = JAKO_XY[1] + 0.06, 0.50
rbox('chair_seat', (0.46, 0.42, 0.04), (0, CH_Y, SEAT - 0.02), 0.012, 3, PROPS, [WOOD_FRAME])
for sx in (-1, 1):
    for sy in (-1, 1):
        rbox('chair_leg', (0.035, 0.035, SEAT - 0.04), (sx * 0.2, CH_Y + sy * 0.18, (SEAT - 0.04) / 2), 0.006, 2, PROPS, [WOOD_FRAME])
    rbox('chair_back_post', (0.035, 0.035, 0.5), (sx * 0.2, CH_Y + 0.2, SEAT + 0.25), 0.006, 2, PROPS, [WOOD_FRAME])
rbox('chair_back', (0.44, 0.03, 0.16), (0, CH_Y + 0.2, SEAT + 0.40), 0.01, 3, PROPS, [WOOD_FRAME])

TOP = DESK_H
# ---------------------------------------------------------------- the "1000" cake (big readable topper facing the camera)
CK = empty('CAKE', PROPS, loc=(CAKE_XY[0], CAKE_XY[1], TOP), size=0.15)
CR, CH = 0.19, 0.12
obj('cake_plate', m_cyl('plate', CR + 0.04, CR + 0.015, 0.018, (0, 0, 0.009), 64), PROPS, CK, mats=[WHITE_CER])
FROST = pbr('MAT_frosting', '#FBEDE4', 0.42, sss=0.25, coat=0.2)
CORAL_ICING = pbr('MAT_icing_coral', '#E8845C', 0.35, sss=0.2, coat=0.35)
ck = obj('cake_body', m_cyl('cake', CR, CR, CH, (0, 0, 0.018 + CH / 2), 64), PROPS, CK, mats=[FROST])
mod_bevel(ck, 0.018, 4)
ZT = 0.018 + CH
top_icing = obj('cake_top_icing', m_cyl('cti', CR - 0.007, CR - 0.007, 0.012, (0, 0, ZT), 64), PROPS, CK, mats=[CORAL_ICING])
mod_bevel(top_icing, 0.006, 3)
for i in range(26):                       # coral drips over the edge
    a = 2 * math.pi * i / 26 + rnd.uniform(-0.05, 0.05)
    L = rnd.uniform(0.025, 0.065)
    p0 = Vector((math.cos(a) * (CR - 0.002), math.sin(a) * (CR - 0.002), ZT + 0.007))
    p1 = Vector((math.cos(a) * (CR + 0.004), math.sin(a) * (CR + 0.004), ZT + 0.007 - L))
    obj('drip', m_tube('drip', [p0, (p0 + p1) / 2, p1], [0.012, 0.010, 0.011], 10, True), PROPS, CK, mats=[CORAL_ICING])
for i in range(18):                       # cream rosettes on the top edge
    a = 2 * math.pi * i / 18
    obj('rosette', m_sphere('ros', (0.018, 0.018, 0.015), (math.cos(a) * (CR - 0.03), math.sin(a) * (CR - 0.03), ZT + 0.013), 12, 8), PROPS, CK, mats=[FROST])
SPR = [pbr('MAT_spr_%d' % i, c, 0.4) for i, c in enumerate(['#F7C548', '#7FC8F8', '#FFFFFF', '#9B5CFF', '#2FBF66'])]
for i in range(70):                       # sprinkles
    rr = math.sqrt(rnd.random()) * (CR - 0.06); a = rnd.random() * 2 * math.pi
    obj('sprinkle', m_cyl('spr', 0.0025, 0.0025, 0.011, (0, 0, 0), 6), PROPS, CK,
        loc=(math.cos(a) * rr, math.sin(a) * rr, ZT + 0.012), rot=(math.pi / 2, 0, rnd.random() * math.pi), mats=[rnd.choice(SPR)])
# "1000" topper: deep coral number candles with a white piped outline behind them, leaning back toward the camera
NUM = pbr('MAT_number', '#D9461A', 0.3, coat=0.6)
NUM_OUT = pbr('MAT_number_outline', '#FFFFFF', 0.35, coat=0.3)
FLAME = emit_mat('MAT_flame', '#FFB347', 14.0)
FLAME_CORE = emit_mat('MAT_flame_core', '#FFF4D6', 18.0)
WICK = pbr('MAT_wick', '#2A2420', 0.8)
TOPPER = empty('cake_topper', PROPS, CK, loc=(0, -0.03, ZT + 0.008), rot=(math.radians(76), 0, 0), size=0.05)
SZ = 0.135
num = text_obj('cake_1000', '1000', PROPS, FONT_BLACK, size=SZ, extrude=0.009, bevel=0.003, parent=TOPPER, mats=[NUM])
outl = text_obj('cake_1000_outline', '1000', PROPS, FONT_BLACK, size=SZ, extrude=0.004, bevel=0.0, parent=TOPPER, loc=(0, 0, -0.012), mats=[NUM_OUT])
outl.data.offset = 0.0065
bpy.context.view_layer.update()
bb = [Vector(c) for c in num.bound_box]
w_txt = max(c.x for c in bb) - min(c.x for c in bb); h_txt = max(c.y for c in bb)
FLAMES = []
for k in range(4):
    xo = -w_txt / 2 + w_txt * (k + 0.5) / 4
    # wicks/flames sit on top of each digit, in topper space (+Y = up the digit)
    obj('wick', m_cyl('wick', 0.0016, 0.0016, 0.012, (0, 0, 0), 6), PROPS, TOPPER, loc=(xo, h_txt + 0.006, 0.0), rot=(-math.pi / 2, 0, 0), mats=[WICK])
    fl = empty('flame_%d' % k, PROPS, TOPPER, loc=(xo, h_txt + 0.014, 0.0), rot=(-math.radians(76), 0, 0), size=0.01)
    obj('flame_outer', m_sphere('fo', (0.009, 0.009, 0.018), (0, 0, 0.012), 12, 8), PROPS, fl, mats=[FLAME]).visible_shadow = False
    obj('flame_core', m_sphere('fc', (0.0045, 0.0045, 0.0085), (0, 0, 0.008), 10, 6), PROPS, fl, mats=[FLAME_CORE]).visible_shadow = False
    FLAMES.append(fl)
# cake knife + 2 small plates (for "let's eat the cake")
obj('knife_blade', m_box('kb', (0.16, 0.022, 0.003), (0, 0, 0)), PROPS, loc=(0.24, 0.12, TOP + 0.004), rot=(0, 0, math.radians(-18)), mats=[METAL])
obj('knife_handle', m_box('kh', (0.07, 0.02, 0.012), (0, 0, 0)), PROPS, loc=(0.35, 0.085, TOP + 0.008), rot=(0, 0, math.radians(-18)), mats=[pbr('MAT_knife_handle', '#E8845C', 0.4)])
for i, (x, y) in enumerate(((-0.30, 0.13), (0.30, 0.66))):
    obj('small_plate', m_cyl('sp', 0.075, 0.065, 0.012, (0, 0, 0.006), 40), PROPS, loc=(x, y, TOP), mats=[WHITE_CER])

# ---------------------------------------------------------------- MacBook (screen faces Jako, the camera sees the lid back + black logo)
MAC = empty('LAPTOP', PROPS, loc=(MAC_XY[0], MAC_XY[1], TOP), rot=(0, 0, math.radians(-160)), size=0.1)
LW, LD = 0.42, 0.29
ALU = pbr('MAT_macbook_alu', '#D5D7DB', 0.3, metal=1.0, coat=0.2)
rbox('mac_base', (LW, LD, 0.016), (0, 0, 0.008), 0.007, 3, PROPS, [ALU], parent=MAC)
obj('mac_keys', m_box('mk', (LW * 0.82, LD * 0.42, 0.002), (0, 0.035, 0.0165)), PROPS, MAC, mats=[KEYS])
obj('mac_pad', m_box('mp', (LW * 0.36, LD * 0.3, 0.001), (0, -0.09, 0.0162)), PROPS, MAC, mats=[pbr('MAT_mac_pad', '#C2C4C8', 0.25, metal=1.0)])
hinge = empty('mac_hinge', PROPS, MAC, loc=(0, LD / 2 - 0.005, 0.014), rot=(math.radians(-18), 0, 0), size=0.03)
rbox('mac_lid', (LW, 0.008, LD - 0.01), (0, 0.004, (LD - 0.01) / 2), 0.004, 3, PROPS, [ALU], parent=hinge)
obj('mac_bezel', m_box('mbz', (LW - 0.008, 0.001, LD - 0.018), (0, -0.0003, (LD - 0.01) / 2)), PROPS, hinge, mats=[BLACK])
SCR = emit_mat('MAT_laptop_screen', '#DCE6FF', 1.4)
obj('mac_screen', m_plane('mscr', LW - 0.03, LD - 0.04, (0, -0.0012, (LD - 0.01) / 2 + 0.004), axis='Y'), PROPS, hinge, mats=[SCR])


def apple_outline(n=120):
    pts = []
    bite_c, bite_r = Vector((1.02, 0.18)), 0.34
    for i in range(n):
        th = 2 * math.pi * i / n
        r = 1.0 - 0.20 * math.exp(-((th - math.pi / 2) / 0.33) ** 2) - 0.09 * math.exp(-((th - 3 * math.pi / 2) / 0.28) ** 2)
        x, y = math.cos(th) * r * 0.93, math.sin(th) * r
        if y < 0:
            x *= 1 - 0.14 * (-y)
        p = Vector((x, y))
        if (p - bite_c).length < bite_r:
            p = bite_c + (p - bite_c).normalized() * bite_r
        pts.append(p)
    return pts


def poly_mesh(name, pts, z=0.0):
    bm = bmesh.new()
    vs = [bm.verts.new((p.x, p.y, z)) for p in pts]
    bm.faces.new(vs)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    return bm_to_mesh(bm, name, smooth=False)


LOGO = pbr('MAT_logo', '#0A0A0C', 0.35, coat=0.4)
LS = 0.030                                     # logo half-height (m)
logo = empty('mac_logo', PROPS, hinge, loc=(0, 0.0085, (LD - 0.01) * 0.54), rot=(math.pi / 2, 0, math.pi), size=0.02)
obj('mac_logo_body', poly_mesh('logo_body', [p * LS for p in apple_outline()]), PROPS, logo, mats=[LOGO])
leaf = [Vector((math.cos(a) * 0.30, math.sin(a) * 0.13)) for a in np.linspace(0, 2 * math.pi, 30, endpoint=False)]
rot45 = Matrix.Rotation(math.radians(50), 2)
obj('mac_logo_leaf', poly_mesh('logo_leaf', [(rot45 @ p + Vector((0.16, 1.17))) * LS for p in leaf]), PROPS, logo, mats=[LOGO])

# ---------------------------------------------------------------- small desk props
obj('mug', m_cyl('mug', 0.042, 0.042, 0.095, (0, 0, 0.0475), 32), PROPS, loc=(0.36, 0.66, TOP), mats=[pbr('MAT_mug', '#3F5A7A', 0.3, coat=0.5)])
obj('mug_handle', m_tube('mh', [(0.04, 0, 0.075), (0.07, 0, 0.065), (0.07, 0, 0.03), (0.04, 0, 0.022)], 0.008, 8, False), PROPS, loc=(0.36, 0.66, TOP),
    mats=[pbr('MAT_mug', '#3F5A7A', 0.3, coat=0.5)])
obj('pencil_cup', m_cyl('pc', 0.035, 0.035, 0.1, (0, 0, 0.05), 24), PROPS, loc=(-0.9, 0.62, TOP), mats=[WHITE_CER])
for i in range(5):
    a = i * 1.3
    obj('pencil', m_cyl('pen', 0.004, 0.004, 0.17, (0, 0, 0.085), 6), PROPS, loc=(-0.9 + math.cos(a) * 0.012, 0.62 + math.sin(a) * 0.012, TOP + 0.02),
        rot=(rnd.uniform(-0.2, 0.2), rnd.uniform(-0.2, 0.2), 0), mats=[pbr('MAT_pencil_%d' % i, ['#F7C548', '#E8845C', '#3F5A7A', '#2FBF66', '#F1EDE5'][i], 0.5)])
# book stack Claude sits on
for i, (h, c, rz) in enumerate(((0.04, '#3F5A7A', 4), (0.035, '#E6C9A8', -6))):
    zb = TOP + (0.04 if i else 0.0)
    rbox('claude_book_%d' % i, (0.40, 0.28, h), (0, 0, h / 2), 0.004, 2, PROPS, [pbr('MAT_cbook_%d' % i, c, 0.6)],
         loc=(CLAUDE_XY[0], CLAUDE_XY[1] + 0.02, zb), rot=(0, 0, math.radians(rz)))
CLAUDE_SEAT_Z = TOP + 0.075
bpy.context.scene['claude_seat_z'] = CLAUDE_SEAT_Z

# balloons (celebration, upper corners of the wide)
for i, (x, y, z, c) in enumerate(((-1.45, 1.15, 1.85, '#E8845C'), (-1.22, 1.35, 2.05, '#F7C548'), (1.42, 1.0, 1.95, '#F1EDE5'))):
    bal = obj('balloon_%d' % i, m_sphere('bal', (0.14, 0.14, 0.17), (0, 0, 0), 32, 16), PROPS, loc=(x, y, z),
              mats=[pbr('MAT_balloon_%d' % i, c, 0.18, coat=0.8, sss=0.15)])
    obj('balloon_knot', m_cyl('bk', 0.012, 0.004, 0.02, (0, 0, -0.18), 8), PROPS, bal, mats=[pbr('MAT_balloon_%d' % i, c, 0.18, coat=0.8)])
    tx = -0.85 if x < 0 else 0.98
    obj('balloon_string', m_tube('bs', [(x, y, z - 0.19), (x * 0.8 + tx * 0.2, y - 0.2, z - 0.7), (tx, 0.62, TOP)], 0.0018, 4, False), PROPS,
        mats=[pbr('MAT_string', '#F1EDE5', 0.7)])

# ---------------------------------------------------------------- Claude's tablet (screen = the clip, 24 fps image sequence)
PHONE_DIR = os.path.join(TEX, 'phone')
nfr = len([f for f in os.listdir(PHONE_DIR) if f.endswith('.png')])
pimg = bpy.data.images.get('phone_seq')
if pimg:
    bpy.data.images.remove(pimg)
pimg = bpy.data.images.load(os.path.join(PHONE_DIR, '0001.png'))
pimg.name = 'phone_seq'; pimg.source = 'SEQUENCE'
pm, nt, out = new_mat('MAT_phone_screen')
t = nt.nodes.new('ShaderNodeTexImage'); t.image = pimg
t.image_user.frame_duration = nfr; t.image_user.frame_start = 1; t.image_user.frame_offset = 0
t.image_user.use_auto_refresh = True; t.image_user.use_cyclic = False
em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = 1.6
nt.links.new(t.outputs['Color'], em.inputs['Color']); nt.links.new(em.outputs[0], out.inputs[0])
bpy.context.scene['phone_frames'] = nfr
PH = empty('PHONE', PROPS, size=0.05)           # the tablet; animated in s3 (held by Claude, then laid on the desk)
TW, THh = 0.25, 0.17
rbox('phone_body', (TW, 0.010, THh), (0, 0, 0), 0.008, 3, PROPS, [pbr('MAT_phone_body', '#2B2D33', 0.3, coat=0.6)], parent=PH)
obj('phone_screen', m_plane('pscr', TW - 0.022, (TW - 0.022) * 574 / 1020, (0, -0.0052, 0), axis='Y'), PROPS, PH, mats=[pm])
# pause icon (shown after the tap)
PAUSE = emit_mat('MAT_pause', '#FFFFFF', 2.5)
pz = empty('phone_pause', PROPS, PH, loc=(0, -0.0062, 0), size=0.01)
obj('pause_disc', m_cyl('pd', 0.024, 0.024, 0.0006, (0, 0, 0), 24), PROPS, pz, rot=(math.pi / 2, 0, 0), mats=[pbr('MAT_pause_bg', '#000000', 0.5, alpha=0.6)])
for sx in (-1, 1):
    obj('pause_bar', m_box('pb', (0.006, 0.0008, 0.024), (sx * 0.0068, -0.0005, 0)), PROPS, pz, mats=[PAUSE])

