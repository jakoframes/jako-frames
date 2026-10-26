# s1_set.py - the room (warm wooden study, desk turned to face the camera, rainy evening window behind),
# props (desk, "1000" cake, MacBook-style laptop, Claude's phone, pendant lamp, bookshelf, plants, balloons),
# lights, world and render settings. Idempotent: rebuilds collections SET / PROPS / LIGHTS.
import sys, importlib
sys.path.insert(0, r'C:\Users\acer\Downloads\jako-frames\reel-1k-cake\blender')
import common; importlib.reload(common)
from common import *

for _n in ('Cube', 'Light', 'Camera'):            # factory-startup leftovers
    if _n in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[_n], do_unlink=True)
SET = reset_coll('SET')
PROPS = reset_coll('PROPS')
LIG = reset_coll('LIGHTS')
rnd = random.Random(3)
FONT_BLACK = r'C:\Windows\Fonts\seguibl.ttf'
FONT_BOLD = r'C:\Windows\Fonts\segoeuib.ttf'

# ---------------------------------------------------------------- materials
WOOD_WALL = wood_mat('MAT_wood_wall', '#4E433B', '#433932', grain='Z', rough=0.6, coat=0.0, planks=5.0)
WOOD_CEIL = wood_mat('MAT_wood_ceiling', '#3A322C', '#312A25', grain='Y', rough=0.6, coat=0.0, planks=5.0)
WOOD_DESK = wood_mat('MAT_wood_desk', '#5C4B40', '#4D3F35', grain='X', rough=0.45, coat=0.15)
WOOD_FLOOR = wood_mat('MAT_wood_floor', '#3A2F28', '#2F2620', grain='Y', rough=0.4, coat=0.2, planks=6.0)
WOOD_FRAME = wood_mat('MAT_wood_frame', '#3E3631', '#352E29', grain='Z', rough=0.4, coat=0.2)
CREAM = pbr('MAT_cream', '#EFE3CF', 0.6)
RUG = pbr('MAT_rug', '#4A423C', 0.95, sheen=0.4)
RUG_EDGE = pbr('MAT_rug_edge', '#3A332E', 0.95, sheen=0.4)
POT_W = pbr('MAT_pot_white', '#F1ECE4', 0.35, coat=0.3)
POT_T = pbr('MAT_pot_terracotta', '#C8714B', 0.7)
LEAF = pbr('MAT_leaf', '#3E7A44', 0.45, sss=0.15, coat=0.2)
LEAF2 = pbr('MAT_leaf2', '#5C9A4E', 0.45, sss=0.15, coat=0.2)
STEM = pbr('MAT_stem', '#4E7A3A', 0.6)
METAL = pbr('MAT_alu', '#C9CBD0', 0.28, metal=1.0)
METAL_D = pbr('MAT_alu_dark', '#5A5C62', 0.35, metal=1.0)
BLACK = pbr('MAT_black_gloss', '#0E0E12', 0.2, coat=0.6)
KEYS = pbr('MAT_keys', '#202126', 0.5)
WHITE_CER = pbr('MAT_ceramic', '#F6F3EE', 0.2, coat=0.5)

# ---------------------------------------------------------------- room shell
W0, W1 = ROOM_X0, ROOM_X1
FRONT_Y = -4.2
obj('floor', m_plane('floor', W1 - W0, WALL_Y - FRONT_Y, ((W0 + W1) / 2, (WALL_Y + FRONT_Y) / 2, 0)), SET, mats=[WOOD_FLOOR])
obj('ceiling', m_plane('ceiling', W1 - W0, WALL_Y - FRONT_Y), SET, loc=((W0 + W1) / 2, (WALL_Y + FRONT_Y) / 2, CEIL),
    rot=(math.pi, 0, 0), mats=[WOOD_CEIL])
for side, x in (('L', W0), ('R', W1)):
    o = obj('wall_' + side, m_box('wall_' + side, (0.12, WALL_Y - FRONT_Y, CEIL), (x + (-0.06 if side == 'L' else 0.06), (WALL_Y + FRONT_Y) / 2, CEIL / 2)), SET, mats=[WOOD_WALL])

# back wall with a big window opening: x -1.25..0.95, z 0.80..2.62
WX0, WX1, WZ0, WZ1 = -1.25, 0.95, 0.80, 2.62
T = 0.14
def wall_piece(name, x0, x1, z0, z1):
    rbox(name, (x1 - x0, T, z1 - z0), ((x0 + x1) / 2, WALL_Y + T / 2, (z0 + z1) / 2), 0.004, 1, SET, [WOOD_WALL])
wall_piece('backwall_L', W0, WX0, 0, CEIL)
wall_piece('backwall_R', WX1, W1, 0, CEIL)
wall_piece('backwall_B', WX0, WX1, 0, WZ0)
wall_piece('backwall_T', WX0, WX1, WZ1, CEIL)
# chunky window frame + mullion + deep sill (like the ref)
FW = 0.09
for nm, sz, c in (('win_frame_B', (WX1 - WX0 + 2 * FW, 0.30, FW), ((WX0 + WX1) / 2, WALL_Y - 0.02, WZ0 - FW / 2 + 0.02)),
                  ('win_frame_T', (WX1 - WX0 + 2 * FW, 0.22, FW), ((WX0 + WX1) / 2, WALL_Y + 0.02, WZ1 + FW / 2)),
                  ('win_frame_L', (FW, 0.22, WZ1 - WZ0 + FW), (WX0 - FW / 2, WALL_Y + 0.02, (WZ0 + WZ1) / 2)),
                  ('win_frame_R', (FW, 0.22, WZ1 - WZ0 + FW), (WX1 + FW / 2, WALL_Y + 0.02, (WZ0 + WZ1) / 2)),
                  ('win_mullion', (0.05, 0.10, WZ1 - WZ0), (-0.42, WALL_Y + 0.06, (WZ0 + WZ1) / 2))):
    rbox(nm, sz, c, 0.012, 3, SET, [WOOD_FRAME])

# glass with rain drops + streaks (animated by frame drivers, no python needed)
gm, nt, out = new_mat('MAT_glass_rain')
tc = nt.nodes.new('ShaderNodeTexCoord')
def moving_mapping(scale, speed):
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = scale
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    d = mp.inputs['Location'].driver_add('default_value', 2).driver
    d.type = 'SCRIPTED'; d.expression = 'frame*%f' % speed
    return mp
mp1 = moving_mapping((26, 26, 26), 0.0)           # still drops
vo1 = nt.nodes.new('ShaderNodeTexVoronoi'); vo1.inputs['Scale'].default_value = 3.0
nt.links.new(mp1.outputs['Vector'], vo1.inputs['Vector'])
drop = math_node = nt.nodes.new('ShaderNodeMath'); drop.operation = 'LESS_THAN'; drop.inputs[1].default_value = 0.12
nt.links.new(vo1.outputs['Distance'], drop.inputs[0])
mp2 = moving_mapping((70, 70, 5), 0.06)            # streaks sliding down
vo2 = nt.nodes.new('ShaderNodeTexVoronoi'); vo2.inputs['Scale'].default_value = 1.0
nt.links.new(mp2.outputs['Vector'], vo2.inputs['Vector'])
streak = nt.nodes.new('ShaderNodeMath'); streak.operation = 'LESS_THAN'; streak.inputs[1].default_value = 0.08
nt.links.new(vo2.outputs['Distance'], streak.inputs[0])
wet = nt.nodes.new('ShaderNodeMath'); wet.operation = 'MAXIMUM'
nt.links.new(drop.outputs[0], wet.inputs[0]); nt.links.new(streak.outputs[0], wet.inputs[1])
fac = nt.nodes.new('ShaderNodeMath'); fac.operation = 'MULTIPLY_ADD'; fac.inputs[1].default_value = 0.10; fac.inputs[2].default_value = 0.01
nt.links.new(wet.outputs[0], fac.inputs[0])
tr = nt.nodes.new('ShaderNodeBsdfTransparent')
gl = nt.nodes.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = 0.2
mx = nt.nodes.new('ShaderNodeMixShader')
nt.links.new(fac.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(gl.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], out.inputs[0])
try:
    gm.surface_render_method = 'BLENDED'
except Exception:
    pass
gm.use_backface_culling = False
glass = obj('window_glass', m_plane('glass', WX1 - WX0, WZ1 - WZ0, ((WX0 + WX1) / 2, WALL_Y + 0.08, (WZ0 + WZ1) / 2), axis='Y'), SET, mats=[gm])
glass.visible_shadow = False

# outside: dusk sky gradient (soft pink at the horizon -> pale blue up top), dark building silhouettes with a few
# warm lit windows (they become bokeh through the shallow DOF). Kept calm; the rain on the glass is subtle.
om, nt, out = new_mat('MAT_outside')
tc = nt.nodes.new('ShaderNodeTexCoord')
sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sep.inputs[0])
sky = nt.nodes.new('ShaderNodeValToRGB')
cr = sky.color_ramp
cr.elements[0].position = 0.0; cr.elements[0].color = hexc('#D9A398')
cr.elements[1].position = 1.0; cr.elements[1].color = hexc('#6F86B0')
e = cr.elements.new(0.30); e.color = hexc('#E3B1A4')
e = cr.elements.new(0.52); e.color = hexc('#B7A6BE')
e = cr.elements.new(0.75); e.color = hexc('#8FA4C8')
nt.links.new(sep.outputs['Z'], sky.inputs[0])
em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = 0.9
nt.links.new(sky.outputs[0], em.inputs['Color']); nt.links.new(em.outputs[0], out.inputs[0])
obj('outside', m_plane('outside', 16, 8, (0, WALL_Y + 6.0, 2.4), axis='Y'), SET, mats=[om]).visible_shadow = False
BLD = pbr('MAT_building', '#14161D', 0.8)
WIN = emit_mat('MAT_city_window', '#FFC98A', 4.0)
rb = random.Random(21)
x = -5.0
while x < 5.0:
    w = rb.uniform(0.6, 1.4); h = rb.uniform(0.9, 2.6) if abs(x) > 0.4 else rb.uniform(0.6, 1.4)
    y = WALL_Y + rb.uniform(2.6, 4.6)
    obj('building', m_box('bld', (w, 0.4, h), (x + w / 2, y, h / 2 - 0.2)), SET, mats=[BLD]).visible_shadow = False
    for _ in range(rb.randrange(0, 3)):                  # a few lit windows only
        wx = x + rb.uniform(0.15, w - 0.15); wz = rb.uniform(0.1, h - 0.4)
        obj('city_window', m_plane('cw', 0.14, 0.12, (wx, y - 0.21, wz), axis='Y'), SET, mats=[WIN]).visible_shadow = False
    x += w + rb.uniform(0.05, 0.4)
# falling rain sheet between glass and backdrop
rm, nt, out = new_mat('MAT_rain_sheet')
tc = nt.nodes.new('ShaderNodeTexCoord')
mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (90, 1, 2.5)
nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
d = mp.inputs['Location'].driver_add('default_value', 2).driver; d.type = 'SCRIPTED'; d.expression = 'frame*0.35'
nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.0; nz.inputs['Detail'].default_value = 1
nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.62; mr.inputs['From Max'].default_value = 0.75
nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 0.07
nt.links.new(mr.outputs['Result'], mul.inputs[0])
tr = nt.nodes.new('ShaderNodeBsdfTransparent'); emr = nt.nodes.new('ShaderNodeEmission')
emr.inputs['Color'].default_value = hexc('#C9D6F0'); emr.inputs['Strength'].default_value = 1.2
mx = nt.nodes.new('ShaderNodeMixShader')
nt.links.new(mul.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(emr.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], out.inputs[0])
try:
    rm.surface_render_method = 'BLENDED'
except Exception:
    pass
rs = obj('rain_sheet', m_plane('rain_sheet', 6, 4, (0, WALL_Y + 1.2, 1.8), axis='Y'), SET, mats=[rm])
rs.visible_shadow = False

# rug
obj('rug', m_box('rug', (2.2, 1.3, 0.012), (0, -0.55, 0.006)), SET, mats=[RUG])
obj('rug_edge', m_box('rug_edge', (2.28, 1.38, 0.008), (0, -0.55, 0.004)), SET, mats=[RUG_EDGE])

# ---------------------------------------------------------------- bookshelf (back wall, right of the window)
BS_X0, BS_X1, BS_Y = 1.12, 2.28, WALL_Y - 0.17
BOOKCOLS = ['#6B645C', '#5A524B', '#4A4540', '#7A7066', '#3F3B37', '#857B70', '#544B44', '#383532']
for k, z in enumerate((0.0, 0.42, 0.84, 1.26, 1.68, 2.10)):
    rbox('shelf_%d' % k, (BS_X1 - BS_X0, 0.32, 0.035), ((BS_X0 + BS_X1) / 2, BS_Y, z + 0.4), 0.006, 2, SET, [WOOD_FRAME])
    if z < 2.0:
        x = BS_X0 + 0.04
        while x < BS_X1 - 0.08:
            if rnd.random() < 0.12:
                x += rnd.uniform(0.05, 0.15)
                continue
            w = rnd.uniform(0.025, 0.055); h = rnd.uniform(0.22, 0.34)
            tilt = rnd.uniform(-0.06, 0.06) if rnd.random() < 0.2 else 0.0
            rbox('book', (w, rnd.uniform(0.18, 0.24), h), (0, 0, h / 2), 0.003, 1, SET,
                 [pbr('MAT_book_%d' % rnd.randrange(len(BOOKCOLS)), BOOKCOLS[rnd.randrange(len(BOOKCOLS))], 0.6)],
                 loc=(x + w / 2, BS_Y + 0.02, z + 0.42), rot=(0, tilt, 0))
            x += w + 0.004
rbox('shelf_side_L', (0.035, 0.32, 2.15), (BS_X0, BS_Y, 1.47), 0.006, 2, SET, [WOOD_FRAME])

# ---------------------------------------------------------------- plants
def plant(name, base, pot_r, pot_h, pot_mat, n_leaves, leaf_len, height, seed, leaf_mat=LEAF):
    r = random.Random(seed)
    root = empty(name, PROPS, loc=base)
    obj(name + '_pot', m_cyl(name + '_pot', pot_r, pot_r * 0.82, pot_h, (0, 0, pot_h / 2), 40), PROPS, root, mats=[pot_mat])
    obj(name + '_soil', m_cyl(name + '_soil', pot_r * 0.92, pot_r * 0.92, 0.01, (0, 0, pot_h - 0.015), 32), PROPS, root,
        mats=[pbr('MAT_soil', '#3B2A20', 0.9)])
    for i in range(n_leaves):
        a = 2 * math.pi * i / n_leaves + r.uniform(-0.3, 0.3)
        h = height * r.uniform(0.55, 1.0)
        out_r = r.uniform(0.25, 0.6) * height * 0.6
        tip = Vector((math.cos(a) * out_r, math.sin(a) * out_r, pot_h + h))
        mid = Vector((math.cos(a) * out_r * 0.35, math.sin(a) * out_r * 0.35, pot_h + h * 0.75))
        obj(name + '_stem', m_tube('stem', [(0, 0, pot_h), mid, tip], [0.006, 0.005, 0.004], 6, False), PROPS, root, mats=[STEM])
        L = leaf_len * r.uniform(0.75, 1.15)
        lm = m_sphere('leaf', (L * 0.42, L * 0.5, 0.008), (0, L * 0.45, 0), 16, 8)
        lo = obj(name + '_leaf', lm, PROPS, root, loc=tip, rot=(r.uniform(-0.6, -0.1), r.uniform(-0.3, 0.3), a - math.pi / 2),
                 mats=[leaf_mat if r.random() < 0.6 else LEAF2])
    return root

plant('plant_sill_R', (0.62, WALL_Y - 0.08, WZ0 + 0.02), 0.065, 0.11, POT_T, 6, 0.13, 0.3, 14, LEAF2)

# ---------------------------------------------------------------- pendant dome lamp
LAMP = (0.30, 0.92, 2.12)
obj('lamp_cord', m_cyl('cord', 0.006, 0.006, CEIL - LAMP[2], (LAMP[0], LAMP[1], (CEIL + LAMP[2]) / 2), 8), PROPS, mats=[BLACK])
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=0.30)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.001], context='VERTS')
for v in bm.verts:
    v.co.z *= 0.62
dome_me = bm_to_mesh(bm, 'dome')
dome = obj('lamp_dome', dome_me, PROPS, loc=LAMP, mats=[pbr('MAT_dome', '#3A3A3E', 0.5, sheen=0.2)])
s = dome.modifiers.new('Solidify', 'SOLIDIFY'); s.thickness = 0.008
mod_subsurf(dome, 1)
glow = emit_mat('MAT_dome_glow', '#FFD9A0', 2.5)
lg_ = obj('lamp_glow', m_cyl('lglow', 0.27, 0.27, 0.004, (0, 0, 0.012), 40), PROPS, dome, mats=[glow])
lg_.visible_glossy = False      # its mirror image made a pale ellipse on Jako's forehead / Claude's top
lg_.visible_shadow = False

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
CR, CH = 0.155, 0.10
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
SPR = [pbr('MAT_spr_%d' % i, c, 0.4) for i, c in enumerate(['#F3E2C0', '#FFFFFF', '#E8845C'])]
for i in range(40):                       # sprinkles
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
SZ = 0.115
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
for i, (x, y) in enumerate(((0.30, 0.66),)):
    obj('small_plate', m_cyl('sp', 0.075, 0.065, 0.012, (0, 0, 0.006), 40), PROPS, loc=(x, y, TOP), mats=[WHITE_CER])

# ---------------------------------------------------------------- MacBook (screen faces Jako, the camera sees the lid back + black logo)
MAC = empty('LAPTOP', PROPS, loc=(MAC_XY[0], MAC_XY[1], TOP), rot=(0, 0, math.radians(-160)), size=0.1)
LW, LD = 0.42, 0.29
ALU = pbr('MAT_macbook_alu', '#E4E6EA', 0.34, metal=0.65, coat=0.2)
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
obj('mug', m_cyl('mug', 0.042, 0.042, 0.095, (0, 0, 0.0475), 32), PROPS, loc=(0.36, 0.66, TOP), mats=[WHITE_CER])
obj('mug_handle', m_tube('mh', [(0.04, 0, 0.075), (0.07, 0, 0.065), (0.07, 0, 0.03), (0.04, 0, 0.022)], 0.008, 8, False), PROPS, loc=(0.36, 0.66, TOP),
    mats=[WHITE_CER])
for i in range(0):
    a = i * 1.3
    obj('pencil', m_cyl('pen', 0.004, 0.004, 0.17, (0, 0, 0.085), 6), PROPS, loc=(-0.9 + math.cos(a) * 0.012, 0.62 + math.sin(a) * 0.012, TOP + 0.02),
        rot=(rnd.uniform(-0.2, 0.2), rnd.uniform(-0.2, 0.2), 0), mats=[pbr('MAT_pencil_%d' % i, ['#F7C548', '#E8845C', '#3F5A7A', '#2FBF66', '#F1EDE5'][i], 0.5)])
# book stack Claude sits on
for i, (h, c, rz) in enumerate(((0.04, '#3F5A7A', 4), (0.035, '#E6C9A8', -6))):
    zb = TOP + (0.04 if i else 0.0)
    rbox('claude_book_%d' % i, (0.40, 0.28, h), (0, 0, h / 2), 0.004, 2, PROPS, [pbr('MAT_cbook_%d' % i, ('#2F3540', '#8C8378')[i], 0.6)],
         loc=(CLAUDE_XY[0], CLAUDE_XY[1] + 0.02, zb), rot=(0, 0, math.radians(rz)))
CLAUDE_SEAT_Z = TOP + 0.075
bpy.context.scene['claude_seat_z'] = CLAUDE_SEAT_Z

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
TW, THh = 0.36, 0.24
rbox('phone_body', (TW, 0.010, THh), (0, 0, 0), 0.008, 3, PROPS, [pbr('MAT_phone_body', '#2B2D33', 0.3, coat=0.6)], parent=PH)
obj('phone_screen', m_plane('pscr', TW - 0.022, (TW - 0.022) * 574 / 1020, (0, -0.0052, 0), axis='Y'), PROPS, PH, mats=[pm])
# pause icon (shown after the tap)
PAUSE = emit_mat('MAT_pause', '#FFFFFF', 2.5)
pz = empty('phone_pause', PROPS, PH, loc=(0, -0.0062, 0), size=0.01)
obj('pause_disc', m_cyl('pd', 0.024, 0.024, 0.0006, (0, 0, 0), 24), PROPS, pz, rot=(math.pi / 2, 0, 0), mats=[pbr('MAT_pause_bg', '#000000', 0.5, alpha=0.6)])
for sx in (-1, 1):
    obj('pause_bar', m_box('pb', (0.006, 0.0008, 0.024), (sx * 0.0068, -0.0005, 0)), PROPS, pz, mats=[PAUSE])

# ---------------------------------------------------------------- lights: warm pool on the desk + characters, room falls off softly
def area(name, loc, target, energy, size, color, shape='DISK', size_y=None, shadow=True, spread=None):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.color = hexc(color)[:3]; ld.shape = shape; ld.size = size
    if size_y:
        ld.size_y = size_y
    if spread:
        ld.spread = math.radians(spread)
    try:
        ld.use_shadow = shadow
    except Exception:
        pass
    o = obj(name, ld, LIG, loc=loc)
    o.rotation_euler = look_rot(loc, target)
    return o

def spot(name, loc, target, energy, cone, blend, radius, color, shadow=True):
    ld = bpy.data.lights.new(name, 'SPOT'); ld.energy = energy; ld.color = hexc(color)[:3]
    ld.spot_size = math.radians(cone); ld.spot_blend = blend; ld.shadow_soft_size = radius
    try:
        ld.use_shadow = shadow
    except Exception:
        pass
    o = obj(name, ld, LIG, loc=loc)
    o.rotation_euler = look_rot(loc, target)
    return o

def point(name, loc, energy, radius, color, shadow=True):
    ld = bpy.data.lights.new(name, 'POINT'); ld.energy = energy; ld.color = hexc(color)[:3]; ld.shadow_soft_size = radius
    try:
        ld.use_shadow = shadow
    except Exception:
        pass
    return obj(name, ld, LIG, loc=loc)

AIM = (-0.15, 0.55, 0.95)
spot('L_key', (-1.1, -1.35, 1.85), AIM, 300, 36, 1.0, 0.6, '#FFD9B0')              # soft warm key pool on both faces, floor stays dark
spot('L_fill', (1.5, -1.6, 1.25), AIM, 60, 40, 1.0, 0.9, '#E8D8D0', shadow=False)         # faint fill, keeps shadows soft
spot('L_rim_L', (-0.35, 1.85, 2.15), (-0.66, 0.36, 0.9), 140, 22, 0.8, 0.25, '#E9C2C8')     # cool window rims (narrow spots,
spot('L_rim_R', (0.45, 1.85, 2.2), (0.0, 0.93, 1.2), 160, 24, 0.8, 0.25, '#C9D2F0')        # so the window frame stays calm)
area('L_lamp_pool', (LAMP[0], LAMP[1], LAMP[2] - 0.03), (LAMP[0] - 0.1, LAMP[1] - 0.5, 0), 45, 0.5, '#FFB870', spread=60)
point('L_lamp_bulb', (LAMP[0], LAMP[1], LAMP[2] + 0.06), 8, 0.08, '#FFC27F')
area('L_laptop', (MAC_XY[0] - 0.12, MAC_XY[1] + 0.14, TOP + 0.16), (0.0, 0.93, 1.12), 6, 0.3, '#DCE6FF', 'RECTANGLE', 0.2, shadow=False)
area('L_window_glow', (-0.15, WALL_Y - 0.15, 1.7), (-0.15, 0.4, 0.9), 60, 2.0, '#D8B4C0', 'RECTANGLE', 1.6, shadow=False)  # window spill on desk/backs
for _ln in ('L_key', 'L_fill', 'L_lamp_pool', 'L_lamp_bulb', 'L_laptop', 'L_window_glow'):
    _ld = bpy.data.objects[_ln].data
    for _k, _v in (('specular_factor', 0.12), ('diffuse_factor', 1.0)):
        try:
            setattr(_ld, _k, _v)
        except Exception:
            pass
cl = point('L_candles', (CAKE_XY[0], CAKE_XY[1] - 0.05, TOP + 0.3), 5.0, 0.03, '#FFB04A')
cl.data.keyframe_insert('energy', frame=1)
fc = [f for f in fcurves_of(cl.data) if f.data_path == 'energy']
if fc:
    m = fc[0].modifiers.new('NOISE'); m.strength = 2.0; m.scale = 2.0
for i, fl in enumerate(FLAMES):              # flame flicker
    fl.keyframe_insert('scale', frame=1)
    for idx in range(3):
        add_noise(fl, 'scale', idx, 0.25 if idx == 2 else 0.12, 1.5 + i * 0.3, phase=i * 7.0 + idx)

# world: warm soft ambient so nothing goes black
wd = bpy.data.worlds.get('WORLD_room') or bpy.data.worlds.new('WORLD_room')
wd.use_nodes = True
bg = next(n for n in wd.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = hexc('#4A4550'); bg.inputs['Strength'].default_value = 0.04
bpy.context.scene.world = wd

# ---------------------------------------------------------------- render settings
sc = bpy.context.scene
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.resolution_percentage = 100
sc.render.fps = FPS
sc.frame_start, sc.frame_end = FRAME_START, FRAME_END
ee = sc.eevee
for k, v in (('taa_render_samples', 48), ('taa_samples', 8), ('use_shadows', True), ('use_raytracing', True),
             ('shadow_ray_count', 2), ('shadow_step_count', 8), ('use_gtao', True), ('fast_gi_method', 'GLOBAL_ILLUMINATION')):
    try:
        setattr(ee, k, v)
    except Exception as ex:
        print('eevee setting skipped', k, ex)
try:
    ee.ray_tracing_options.resolution_scale = '2'
except Exception:
    pass
sc.view_settings.view_transform = 'Filmic'
try:
    sc.view_settings.look = 'Medium High Contrast'
except Exception:
    pass
sc.view_settings.exposure = 0.0
sc.render.film_transparent = False
# compositor: gentle glow on candles / lamp
sc.use_nodes = True
cnt = sc.node_tree
cnt.nodes.clear()
rl = cnt.nodes.new('CompositorNodeRLayers')
gla = cnt.nodes.new('CompositorNodeGlare'); gla.glare_type = 'FOG_GLOW'
try:
    gla.quality = 'MEDIUM'; gla.threshold = 1.6; gla.size = 7; gla.mix = -0.75
except Exception:
    pass
comp = cnt.nodes.new('CompositorNodeComposite')
cnt.links.new(rl.outputs['Image'], gla.inputs['Image'])
# (the vignette is added at assembly with ffmpeg's `vignette` filter: a compositor EllipseMask version came out
#  tiny and printed a pale oval on every frame, which looked like a highlight on Jako's forehead / Claude's body)
cnt.links.new(gla.outputs['Image'], comp.inputs['Image'])
print('s1_set done')
