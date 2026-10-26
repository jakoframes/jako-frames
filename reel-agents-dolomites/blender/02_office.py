# 02_office.py - Jako HQ campus ported from jako-hq.html: office pavilion (deck, frame, pergola slats, rug,
# planters, string lights, stepping stones), 5 desks with laptops/monitors and agent screens
# (calendar / chart / text / timeline / grid), sports courts (east), lounge (west), campfire by the cliff edge.
# Re-runnable: rebuilds collection OFFICE.
import sys, importlib
sys.path.insert(0, r'C:\Users\acer\Downloads\jako-frames\reel-agents-dolomites\blender')
import common; importlib.reload(common)
from common import *

C = reset_coll('OFFICE')
rng = random.Random(4)

# ------------------------------------------------------------ materials
def plank_mat(name, scale=1.0):
    m, nt, out = new_mat(name)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.inputs['Color1'].default_value = hexc('#c49a6e'); br.inputs['Color2'].default_value = hexc('#a97c52')
    br.inputs['Mortar'].default_value = hexc('#5a3a22')
    br.inputs['Scale'].default_value = 1.0 * scale
    br.inputs['Mortar Size'].default_value = 0.006
    br.inputs['Brick Width'].default_value = 2.4; br.inputs['Row Height'].default_value = 0.16
    br.offset = 0.37
    nt.links.new(tc.outputs['Object'], br.inputs['Vector'])
    gn = nt.nodes.new('ShaderNodeTexNoise'); gn.inputs['Scale'].default_value = 1.5
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1.0, 30.0, 1.0)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], gn.inputs['Vector'])
    f = math_node(nt, 'MULTIPLY_ADD', gn.outputs['Fac'], 0.35, 0.82)
    b = bsdf_node(nt, rough=0.75, spec=0.4)
    nt.links.new(scale_color(nt, br.outputs['Color'], f), b.inputs['Base Color'])
    nt.links.new(b.outputs[0], out.inputs[0])
    return m


DECKM = plank_mat('MAT_deck')
METAL = pbr('MAT_frame', '#e6e2da', 0.5, metal=0.1)
DARK = pbr('MAT_dark', '#2a2d33', 0.45, metal=0.5)
WHITE = pbr('MAT_white', '#f3f1ec', 0.55)
CONC = pbr('MAT_concrete', '#bdb8ae', 0.95)
WOOD = pbr('MAT_wood', '#8a6040', 0.8)
LEAF = pbr('MAT_leaf', '#3b6b31', 0.9)
STONE = pbr('MAT_stone', '#c9c4b8', 1.0)
RUG = pbr('MAT_rug', '#a88d6c', 1.0, sheen=0.5)
LAP = pbr('MAT_laptop', '#c9ccd3', 0.3, metal=0.8)
KEYS = pbr('MAT_keys', '#2a2d33', 0.6)


def box(name, size, center, mat, parent=None, bevel=0.0):
    o = obj(name, m_box(name, size, center), C, parent, mats=[mat])
    if bevel:
        mod_bevel(o, bevel, 2)
    return o


def cyl(name, r1, r2, h, center, mat, parent=None, seg=16):
    return obj(name, m_cyl(name, r1, r2, h, center, seg), C, parent, mats=[mat])


# ------------------------------------------------------------ pavilion
box('DECK', (16.4, 10.4, DECK), (0, 0.5, DECK / 2), DECKM, bevel=0.02)
box('DECK_step', (4.0, 0.7, 0.15), (0, -5.05, 0.075), DECKM, bevel=0.015)
for sx in (-8, 8):
    for sy in (5.5, -4.5):
        box('POST_%d_%d' % (sx, sy), (0.14, 0.14, 3.3), (sx, sy, DECK + 1.65), METAL, bevel=0.01)
for sy in (5.5, -4.5):
    box('BEAM_y%d' % sy, (16.2, 0.16, 0.16), (0, sy, DECK + 3.3), METAL)
for sx in (-8, 8):
    box('BEAM_x%d' % sx, (0.16, 10.2, 0.16), (sx, 0.5, DECK + 3.3), METAL)
for i in range(29):                       # pergola slats -> striped evening light on the desks
    x = -7.7 + i * (15.4 / 28)
    box('SLAT_%02d' % i, (0.07, 10.0, 0.16), (x, 0.5, DECK + 3.46), WOOD)
obj('RUG', m_cyl('rug', 6.4, 6.4, 0.012, (0, 1.4, DECK + 0.006), seg=64), C, mats=[RUG])
for (px, py) in [(-7, -3.6), (7, -3.6), (-7, 4.6), (7, 4.6)]:
    box('PLANTER_%d_%d' % (px, py), (1.2, 1.2, 0.6), (px, py, DECK + 0.3), CONC, bevel=0.03)
    for j in range(7):
        rr = 0.3 + rng.random() * 0.17
        obj('BUSH', m_rock('bush', rr, (px + (rng.random() - .5) * 0.6, py + (rng.random() - .5) * 0.6, DECK + 0.78 + rng.random() * 0.3),
                           seed=j + int(px * 3), squash=0.9, rough=0.15), C, mats=[LEAF])
for i in range(9):
    y = -(6.1 + i * 1.15); x = math.sin(i * 1.7) * 0.35
    o = obj('STEPSTONE_%d' % i, m_cyl('ss', 0.42, 0.45, 0.1, (0, 0, 0), seg=9), C, loc=(x, y, ground_h(x, y) + 0.04), rot=(0, 0, i), mats=[STONE])

# string lights (emission keyed brighter as the light drops)
BULB = emit_mat('MAT_bulb', '#ffd28a', 2.0)
em = next(n for n in BULB.node_tree.nodes if n.type == 'EMISSION')
for f, v in ((1, 1.5), (FRAME_END // 2, 3.0), (FRAME_END, 7.0)):
    em.inputs['Strength'].default_value = v; em.inputs['Strength'].keyframe_insert('default_value', frame=f)
bulb_me = m_sphere('bulb', 0.055, (0, 0, 0), 10, 6)
bulb_me.materials.append(BULB)
for sy in (5.5, -4.5):
    for i in range(25):
        x = -8 + i * (16 / 24); sag = math.sin((i % 6) / 6 * math.pi) * 0.22
        o = obj('BULB', bulb_me, C, loc=(x, sy + (-0.12 if sy > 0 else 0.12), DECK + 3.1 - sag))
for i, x in enumerate((-5.5, 0.0, 5.5)):
    for sy in (5.2, -4.2):
        ld = bpy.data.lights.new('STRING_LIGHT', 'POINT'); ld.color = hex3('#ffc27a'); ld.shadow_soft_size = 0.4
        lo = obj('STRING_LIGHT_%d_%d' % (i, sy), ld, C, loc=(x, sy, DECK + 2.9))
        for f, v in ((1, 6.0), (FRAME_END // 2, 15.0), (FRAME_END, 35.0)):
            ld.energy = v; ld.keyframe_insert('energy', frame=f)

# ------------------------------------------------------------ agent screens (textures, 2x the jako-hq canvas)
def screen_image(kind, color):
    W, H = 512, 320
    a = canvas(W, H, '#10141f')
    rect(a, 0, 0, W, 32, '#1c2233')
    for i, cc in enumerate(('#ff5f57', '#febc2e', '#28c840')):
        disc(a, 20 + i * 22, 16, 6.4, cc)
    if kind == 'text':
        for i in range(9):
            w = 120 + ((i * 7919) % 100) / 100 * 300
            rect(a, 28, 52 + i * 28, w, 12, color if i % 3 == 0 else '#c9d1e3')
        rect(a, 28 + 120, 52 + 9 * 28, 12, 18, '#ffffff')
    elif kind == 'grid':
        cols = ['#ff8a3d', '#3d8bff', '#9b5cff', '#2fbf66', '#f2b90f', '#ff5fa2']
        for i in range(6):
            cx, cy = 28 + (i % 3) * 156, 52 + (i // 3) * 128
            c0 = np.array(rgb255(cols[i])[:3]); c1 = np.array(rgb255('#1c2233')[:3])
            for k in range(0, 112, 4):
                t = k / 112
                rect(a, cx, cy + k, 140, 4, list(c0 * (1 - t) + c1 * t) + [1])
            if i == 2:
                for (x, y, w, h) in ((cx - 4, cy - 4, 148, 4), (cx - 4, cy + 112, 148, 4), (cx - 4, cy - 4, 4, 120), (cx + 140, cy - 4, 4, 120)):
                    rect(a, x, y, w, h, color)
    elif kind == 'chart':
        for i in range(9):
            h = 60 + (math.sin(i * 0.8) * 0.5 + 0.5) * 140 + i * 8
            rect(a, 32 + i * 50, H - 28 - h, 32, h, color if i == 8 else '#3a4560')
        pts = [(48 + i * 50, H - 100 - i * 18 - math.sin(i) * 12) for i in range(9)]
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            for t in np.linspace(0, 1, 30):
                disc(a, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 2.5, '#ffffff')
    elif kind == 'timeline':
        rect(a, 24, 48, 464, 116, '#1b2030')
        disc(a, 256, 106, 32, color)
        for r, cc in enumerate(('#ff8a3d', color, '#2fbf66', '#3d8bff')):
            for j in range(4):
                rect(a, 28 + j * 116 + ((r * 3 + j * 5) % 7) * 4, 184 + r * 30, 60 + ((j * 3 + r) % 5) * 9, 20, cc, 0.85)
        rect(a, 300, 176, 4, 132, '#ffffff')
    elif kind == 'calendar':
        today = 12
        for i in range(28):
            cx, cy = 28 + (i % 7) * 66, 48 + (i // 7) * 66
            if i < today:
                rect(a, cx, cy, 56, 56, color, 0.75)
            elif i == today:
                rect(a, cx, cy, 56, 56, '#ffffff')
            else:
                rect(a, cx, cy, 56, 56, '#262d40')
    return save_image('screen_' + kind, a)


for i, ag in enumerate(AGENTS):
    img = screen_image(ag['screen'], ag['color'])
    m = image_mat('MAT_screen_' + ag['id'], img, rough=0.25, emission=0.12, base_dark=True)
    next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').name = 'SCREEN_BSDF'

# ------------------------------------------------------------ desks (jako-hq buildAgent stations)
for i, ag in enumerate(AGENTS):
    x, y, rz = station(i)
    st = empty('STATION_' + ag['id'], C, loc=(x, y, DECK), rot=(0, 0, rz), size=0.4)
    acol = hexc(ag['color'])
    seat_col = lerpc(acol, (1, 1, 1, 1), 0.55)
    box('DESK_top_' + ag['id'], (1.6, 0.75, 0.05), (0, 0, 0.6), WHITE, st, bevel=0.01)
    for lx in (-0.74, 0.74):
        for ly in (-0.32, 0.32):
            cyl('DESK_leg', 0.02, 0.02, 0.6, (lx, ly, 0.3), DARK, st, 8)
    seat = pbr('MAT_seat_' + ag['id'], seat_col, 0.7)
    cyl('STOOL_seat_' + ag['id'], 0.26, 0.26, 0.06, (0, 0.8, 0.5), seat, st, 24)
    cyl('STOOL_stem', 0.03, 0.03, 0.47, (0, 0.8, 0.235), DARK, st, 10)
    cyl('STOOL_base', 0.2, 0.2, 0.03, (0, 0.8, 0.015), DARK, st, 20)
    cyl('MUG_' + ag['id'], 0.05, 0.045, 0.1, (-0.58, 0.12, 0.675), pbr('MAT_mug_' + ag['id'], acol, 0.35), st, 16)
    box('LAPTOP_base_' + ag['id'], (0.56, 0.38, 0.025), (0, 0.08, 0.6375), LAP, st, bevel=0.006)
    obj('LAPTOP_keys_' + ag['id'], m_plane('kb', 0.48, 0.16, (0, 0.04, 0.6515)), C, st, mats=[KEYS])
    lid = empty('LAPTOP_lid_' + ag['id'], C, st, loc=(0, -0.11, 0.65), rot=(0.25, 0, 0), size=0.1)
    box('LAPTOP_lidbody_' + ag['id'], (0.56, 0.018, 0.3), (0, 0, 0.15), LAP, lid, bevel=0.005)
    scr = obj('SCREEN_' + ag['id'], m_plane('scr', 0.52, 0.27, (0, 0, 0), 'Y'), C, lid, loc=(0, 0.0095, 0.15), rot=(0, 0, math.pi),
              mats=[bpy.data.materials['MAT_screen_' + ag['id']]])
    logo = emit_mat('MAT_logo_' + ag['id'], ag['color'], 3.0)
    obj('LAPTOP_logo_' + ag['id'], m_cyl('logo', 0.035, 0.035, 0.002, (0, 0, 0), 24), C, lid, loc=(0, -0.0105, 0.17), rot=(math.pi / 2, 0, 0), mats=[logo])
    if ag['monitor']:
        mon = empty('MONITOR_' + ag['id'], C, st, loc=(0.5, -0.12, 0.625), rot=(0, 0, 0.5), size=0.1)
        box('MON_foot', (0.16, 0.12, 0.012), (0, 0, 0.006), DARK, mon)
        cyl('MON_neck', 0.015, 0.015, 0.16, (0, -0.02, 0.09), DARK, mon, 8)
        box('MON_body_' + ag['id'], (0.46, 0.022, 0.29), (0, -0.02, 0.31), DARK, mon, bevel=0.004)
        obj('MON_screen_' + ag['id'], m_plane('ms', 0.43, 0.26, (0, 0, 0), 'Y'), C, mon, loc=(0, -0.0075, 0.31), rot=(0, 0, math.pi),
            mats=[bpy.data.materials['MAT_screen_' + ag['id']]])
    # screen glow on the agent's face (keyed on in 05_agents)
    ld = bpy.data.lights.new('DESKLIGHT_' + ag['id'], 'AREA'); ld.shape = 'RECTANGLE'; ld.size = 0.5; ld.size_y = 0.3
    ld.color = lerpc(acol[:3], (1, 1, 1), 0.5); ld.energy = 0.0
    try:
        ld.use_shadow = False
    except Exception:
        pass
    obj('DESKLIGHT_' + ag['id'], ld, C, st, loc=(0, 0.0, 0.95), rot=(math.radians(90), 0, 0))   # shines +Y onto the agent's face

# ------------------------------------------------------------ sports courts (east)
def court_img(name, W, H, draw):
    a = canvas(W, H, '#000000'); draw(a, W, H); return save_image(name, a)


def lines_box(a, x, y, w, h, t, col):
    rect(a, x, y, w, t, col); rect(a, x, y + h - t, w, t, col); rect(a, x, y, t, h, col); rect(a, x + w - t, y, t, h, col)


def ring(a, cx, cy, r, t, col, inner):
    disc(a, cx, cy, r, col); disc(a, cx, cy, r - t, inner)


def bb(a, W, H):
    rect(a, 0, 0, W, H, '#b4553b'); rect(a, 150, 0, 200, 240, '#2f5d8a')
    ring(a, 250, 240, 75, 5, '#ffffff', '#b4553b'); rect(a, 150, 0, 200, 240, '#2f5d8a')
    lines_box(a, 4, 4, W - 8, H - 8, 5, '#ffffff'); lines_box(a, 150, 0, 200, 240, 5, '#ffffff')


def tn(a, W, H):
    rect(a, 0, 0, W, H, '#2e6b5a'); rect(a, 48, 24, 544, 252, '#3567a8')
    lines_box(a, 48, 24, 544, 252, 4, '#ffffff'); lines_box(a, 48, 52, 544, 196, 4, '#ffffff')
    rect(a, 176, 52, 4, 196, '#ffffff'); rect(a, 464, 52, 4, 196, '#ffffff'); rect(a, 176, 148, 292, 4, '#ffffff')


def sd(a, W, H):
    rect(a, 0, 0, W, H, '#e2cf9e')
    noise = np.random.default_rng(1).random((H, W))
    a[..., :3] *= (0.9 + 0.2 * noise)[..., None]
    lines_box(a, 14, 14, W - 28, H - 28, 3, '#2f7fd1')


def court(name, img, w, h, center, rot=0.0):
    me = m_plane(name, w, h, center)
    return obj(name, me, C, rot=(0, 0, rot), mats=[image_mat('MAT_' + name, img, 0.85)])


court('COURT_basket', court_img('court_basket', 500, 450, bb), 10, 9, (20, 11.5, 0.02))
court('COURT_tennis', court_img('court_tennis', 640, 300, tn), 16, 7.5, (30, -6.25, 0.02))
court('COURT_volley', court_img('court_volley', 256, 150, sd), 13.2, 7.6, (34, 11, 0.03))
cyl('HOOP_pole', 0.08, 0.1, 3.0, (20, 16.4, 1.5), DARK)
box('HOOP_board', (1.5, 0.05, 0.95), (20, 15.28, 2.78), WHITE)
obj('HOOP_rim', m_torus('rim', 0.23, 0.018, seg=28, rseg=8), C, loc=(20, 14.9, 2.4), mats=[pbr('MAT_rim', '#e2572b', 0.35, metal=0.6)])
netimg = canvas(256, 32, '#ffffff'); netimg[..., 3] = 0.0
for i in range(0, 256, 8):
    netimg[:, i:i + 2, 3] = 1.0
for j in range(0, 32, 8):
    netimg[j:j + 2, :, 3] = 1.0
netimg = save_image('net', netimg)
nm, nt, out = new_mat('MAT_net')
t = nt.nodes.new('ShaderNodeTexImage'); t.image = netimg
b = bsdf_node(nt, (0.95, 0.95, 0.95, 1), 0.8)
nt.links.new(t.outputs['Alpha'], b.inputs['Alpha']); nt.links.new(b.outputs[0], out.inputs[0])
set_alpha_mode(nm)
for (cx, cy, w, h, z) in ((34, 11, 7.6, 0.9, 1.8), (30, -6.25, 7.0, 0.7, 0.37)):
    obj('NET', m_plane('net', w, h, (0, 0, 0), 'Y'), C, loc=(cx, cy, z), rot=(0, 0, math.pi / 2), mats=[nm])
    for yy in (cy - w / 2, cy + w / 2):
        cyl('NETPOST', 0.05, 0.05, z + h / 2, (cx, yy, (z + h / 2) / 2), METAL, seg=8)
box('PINGPONG_top', (2.2, 1.2, 0.05), (15.5, -6.5, 0.62), pbr('MAT_pingpong', '#1f4e8c', 0.5))
for lx in (-0.9, 0.9):
    for ly in (-0.45, 0.45):
        cyl('PP_leg', 0.025, 0.025, 0.6, (15.5 + lx, -6.5 + ly, 0.3), DARK, seg=8)
box('PP_net', (0.02, 1.32, 0.1), (15.5, -6.5, 0.695), DARK)
box('COURT_bench', (2.2, 0.45, 0.08), (20, -1.2, 0.42), WOOD)

# ------------------------------------------------------------ lounge (west)
box('SPA_DECK', (17, 16, SPA), (-20.5, 1, SPA / 2), plank_mat('MAT_spa_deck', 1.0), bevel=0.02)
for (px, py) in [(-18.6, 8.6), (-12.6, 8.6), (-18.6, 3.4), (-12.6, 3.4)]:
    box('SAIL_post', (0.1, 0.1, 2.6), (px, py, SPA + 1.3), METAL)
box('SAIL', (6.3, 5.4, 0.05), (-15.6, 6, SPA + 2.62), pbr('MAT_sail', '#f4efe6', 0.9))
for tx in (-14.4, -16.9):
    box('MASSAGE_table', (0.85, 2.0, 0.1), (tx, 6, SPA + 0.65), pbr('MAT_massage', '#d8c7ad', 0.7), bevel=0.02)
for i, by in enumerate((7, 4.2, 1.4)):
    box('BED_frame', (2.3, 1.3, 0.3), (-25.6, by, SPA + 0.15), WOOD, bevel=0.02)
    box('BED_mattress', (2.2, 1.2, 0.18), (-25.6, by, SPA + 0.39), WHITE, bevel=0.05)
    box('BED_blanket', (1.15, 1.24, 0.07), (-24.95, by, SPA + 0.51), pbr('MAT_blanket_%d' % i, ['#b5c7d9', '#e3c6a8', '#c9d6b4'][i], 1.0), bevel=0.03)
obj('TUB_wall', m_cyl('tub', 1.8, 1.75, 0.85, (-16.5, -3.2, SPA + 0.425), seg=40), C, mats=[WOOD])
obj('TUB_water', m_cyl('water', 1.62, 1.62, 0.02, (-16.5, -3.2, SPA + 0.72), seg=40), C,
    mats=[pbr('MAT_water', '#4cb9cf', 0.05, metal=0.1)])

# ------------------------------------------------------------ campfire by the cliff edge
fx, fy = FIRE
fz = ground_h(fx, fy)
fire = empty('CAMPFIRE', C, loc=(fx, fy, fz), size=0.5)
stoneM = pbr('MAT_firestone', '#8d877c', 1.0)
for i in range(11):
    a = i / 11 * math.tau
    obj('FIRE_stone', m_rock('fs', 0.2, (math.sin(a) * 0.75, math.cos(a) * 0.75, 0.1), seed=50 + i, squash=0.7), C, fire, mats=[stoneM])
charm = pbr('MAT_log', '#4a3322', 0.9)
for i in range(3):
    o = obj('FIRE_log', m_cyl('log', 0.07, 0.07, 1.0, (0, 0, 0), 10), C, fire, loc=(0, 0, 0.14), rot=(math.pi / 2 - 0.3, 0, i * 1.05), mats=[charm])
m, nt, out = new_mat('MAT_flame')
tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
nt.links.new(tc.outputs['Generated'], sep.inputs[0])
fc = ramp(nt, sep.outputs['Z'], [(0.0, hexc('#fff1a8')), (0.35, hexc('#ffb02e')), (0.75, hexc('#ff5a1a')), (1.0, hexc('#c4200f'))])
e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Strength'].default_value = 14.0
nt.links.new(fc, e.inputs['Color'])
tr = nt.nodes.new('ShaderNodeBsdfTransparent')
ms = nt.nodes.new('ShaderNodeMixShader')
fade = math_node(nt, 'POWER', sep.outputs['Z'], 2.0)
nt.links.new(fade, ms.inputs[0]); nt.links.new(e.outputs[0], ms.inputs[1]); nt.links.new(tr.outputs[0], ms.inputs[2])
nt.links.new(ms.outputs[0], out.inputs[0])
set_alpha_mode(m, blended=True)
FLAME = m
for k in range(4):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=1.0)
    for v in bm.verts:
        z = (v.co.z + 1) / 2
        pinch = (1 - z) ** 0.8 * (1 + 0.4 * z)
        v.co = Vector((v.co.x * 0.16 * pinch, v.co.y * 0.16 * pinch, z * (0.75 - 0.12 * k)))
    me = bpy.data.meshes.new('flame'); bm.to_mesh(me); bm.free()
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    a = k * 1.7
    fo = obj('FLAME_%d' % k, me, C, fire, loc=(math.sin(a) * 0.1, math.cos(a) * 0.1, 0.12), mats=[FLAME])
    fo.keyframe_insert('scale', frame=1); fo.keyframe_insert('rotation_euler', frame=1)
    for idx in range(3):
        add_noise(fo, 'scale', idx, strength=0.25 if idx == 2 else 0.12, scale=3.0 + k)
    add_noise(fo, 'rotation_euler', 0, 0.12, 4.0); add_noise(fo, 'rotation_euler', 1, 0.12, 4.5)
ld = bpy.data.lights.new('FIRE_LIGHT', 'POINT'); ld.color = hex3('#ff8a3a'); ld.energy = 160.0; ld.shadow_soft_size = 0.25
fl = obj('FIRE_LIGHT', ld, C, fire, loc=(0, 0, 0.55))
ld.keyframe_insert('energy', frame=1)
add_noise(ld, 'energy', 0, strength=55.0, scale=2.5)
for i, (cc, a) in enumerate((('#c96d4a', -1.0), ('#5a7fa6', 0.15), ('#d9b04a', 1.2))):
    obj('BEANBAG_%d' % i, m_sphere('bag', (0.55, 0.55, 0.3), (0, 0, 0), 32, 16), C, fire,
        loc=(math.sin(a) * 2.0, math.cos(a) * 2.0, 0.24), mats=[pbr('MAT_bag_%d' % i, cc, 0.95, sheen=0.4)])

print('02_office done')
