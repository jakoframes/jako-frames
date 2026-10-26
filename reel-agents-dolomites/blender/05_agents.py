# 05_agents.py - the 5 Jako HQ agents (cute vinyl aliens with glowing antennas, from jako-hq.html) + their chill
# props, and their whole timeline:
#   1..T_CHILL_END  chilling: planner swings in a hammock with a paper calendar, analyst lies in the grass counting
#                   stars, caption-writer scribbles on a bench, video-director films the pink peaks, trend-scout
#                   looks through binoculars
#   PERK frames     antennas perk up one by one on the 5 pops in the mix   [shots 11a/11b]
#   T_RUN0..        run in from the sides, hop onto the deck, sit at their desks [shot 11c]
#   SCREEN_ON       screens + desk glow switch on, on the 5 bloops; typing until the end [11d, 12, 13, 14]
# All frames come from audio/timeline.json via common.py.
# Needs 02_office.py (stations, screen materials, desk lights). Re-runnable: rebuilds collection AGENTS.
import sys, importlib
sys.path.insert(0, r'C:\Users\acer\Downloads\jako-frames\reel-agents-dolomites\blender')
import common; importlib.reload(common)
from common import *

C = reset_coll('AGENTS')
for ag in AGENTS:     # clear old screen/desk-light keys from a previous run
    m = bpy.data.materials.get('MAT_screen_' + ag['id'])
    if m and m.node_tree.animation_data:
        m.node_tree.animation_data_clear()
    ld = bpy.data.lights.get('DESKLIGHT_' + ag['id'])
    if ld and ld.animation_data:
        ld.animation_data_clear()

BLACK = pbr('MAT_agent_eye', '#121319', 0.1, coat=1.0, coat_rough=0.05)
SHINE = emit_mat('MAT_agent_shine', '#ffffff', 3.0)
m, nt, out = new_mat('MAT_agent_blush')
b = bsdf_node(nt, hexc('#ff7b9c'), 0.6, alpha=0.5); nt.links.new(b.outputs[0], out.inputs[0]); set_alpha_mode(m, True)
BLUSH = m
WOODM = pbr('MAT_wood', '#8a6040', 0.8)
DARKM = pbr('MAT_dark', '#2a2d33', 0.45, metal=0.5)

SEAT_LOCAL = Vector((0, 0.8, 0))


def vinyl(name, hexcol, mult=1.0):
    c = hexc(hexcol); c = (c[0] * mult, c[1] * mult, c[2] * mult, 1)
    return pbr(name, c, 0.38 if mult == 1.0 else 0.45, coat=0.7 if mult == 1.0 else 0.4, coat_rough=0.25)


def build_agent(ag):
    aid = ag['id']
    bodyM = vinyl('MAT_ag_body_' + aid, ag['color'])
    limbM = vinyl('MAT_ag_limb_' + aid, ag['color'], 0.75)
    ballM = emit_mat('MAT_ag_ball_' + aid, ag['color'], 4.0)
    carrier = empty('AG_%s_carrier' % aid, C, size=0.3)
    root = empty('AG_' + aid, C, carrier, size=0.4, kind='ARROWS')
    body = empty('AG_%s_body' % aid, C, root, loc=(0, 0, 0.53), size=0.3)
    obj('AG_%s_torso' % aid, m_sphere('agb', (0.42, 0.40, 0.43), (0, 0, 0), 48, 24), C, body, mats=[bodyM])
    for sx in (-1, 1):
        e = obj('AG_%s_eye' % aid, m_sphere('age', (0.075, 0.045, 0.095), (sx * 0.135, -0.35, 0.07), 24, 12), C, body, mats=[BLACK])
        obj('AG_%s_shine' % aid, m_sphere('ags', (0.022, 0.013, 0.022), (sx * 0.135 + 0.0225, -0.386, 0.106), 12, 6), C, body, mats=[SHINE])
        obj('AG_%s_blush' % aid, m_sphere('agbl', (0.06, 0.02, 0.035), (sx * 0.245, -0.315, -0.05), 16, 8), C, body, mats=[BLUSH])
    sm = obj('AG_%s_smile' % aid, m_torus('smile', 0.04, 0.011, arc=math.pi, seg=16, rseg=8, start=math.pi), C, body,
             loc=(0, -0.392, -0.045), rot=(math.pi / 2, 0, 0), mats=[BLACK])
    ant = empty('AG_%s_ant' % aid, C, body, loc=(0, 0, 0.4), size=0.1)
    obj('AG_%s_stalk' % aid, m_cyl('stalk', 0.02, 0.014, 0.28, (0, 0, 0.14), 10), C, ant, mats=[limbM])
    obj('AG_%s_ball' % aid, m_sphere('ball', 0.065, (0, 0, 0.31), 20, 10), C, ant, mats=[ballM])
    arms = []
    for sx, nm in ((-1, 'R'), (1, 'L')):
        piv = empty('AG_%s_arm_%s' % (aid, nm), C, body, loc=(sx * 0.36, -0.08, -0.02), size=0.06)
        obj('AG_%s_armmesh_%s' % (aid, nm), m_sphere('arm', (0.07, 0.07, 0.2), (0, 0, -0.2), 16, 10), C, piv, mats=[limbM])
        arms.append(piv)
    feet = []
    for sx, nm in ((-1, 'R'), (1, 'L')):
        f = empty('AG_%s_foot_%s' % (aid, nm), C, root, loc=(sx * 0.14, -0.03, 0.055), size=0.05)
        obj('AG_%s_footmesh_%s' % (aid, nm), m_sphere('foot', (0.08, 0.1, 0.055), (0, 0, 0), 16, 8), C, f, mats=[limbM])
        feet.append(f)
    return dict(id=aid, carrier=carrier, root=root, body=body, ant=ant, arms=arms, feet=feet, ball=ballM)


A = {ag['id']: build_agent(ag) for ag in AGENTS}
ALL_PARTS = lambda a: [a['carrier'], a['root'], a['body'], a['ant']] + a['arms'] + a['feet']


def pose(a, f, root_loc=None, root_rot=0.0, body=(0, 0, 0.53), body_rot=(0, 0, 0), armR=(0, 10, 0), armL=(0, -10, 0),
         footR=(-0.14, -0.03, 0.055), footL=(0.14, -0.03, 0.055), carrier=None, carrier_rot=(0, 0, 0)):
    """Key a full pose at frame f. Rotations in degrees. root_loc in world (or carrier) space."""
    if carrier is not None:
        KO(a['carrier'], f, loc=carrier, rot=carrier_rot)
    else:
        KO(a['carrier'], f, loc=(0, 0, 0), rot=(0, 0, 0))
    KO(a['root'], f, loc=root_loc, rot=(0, 0, root_rot))
    KO(a['body'], f, loc=body, rot=body_rot)
    KO(a['arms'][0], f, rot=armR); KO(a['arms'][1], f, rot=armL)
    KO(a['feet'][0], f, loc=footR); KO(a['feet'][1], f, loc=footL)
    KO(a['ant'], f, scl=1.0)


def hold(a, f):
    """Make the keys at frame f step (constant) for every part of agent a."""
    for o in ALL_PARTS(a):
        for fc in fcurves_of(o):
            for kp in fc.keyframe_points:
                if abs(kp.co[0] - f) < 0.5:
                    kp.interpolation = 'CONSTANT'


def gz(x, y):
    return ground_h(x, y)


# ============================================================ chill props + poses (f1..880)
PROPS = {}
# --- planner: hammock between two posts, swinging; paper calendar
hx, hy = CHILL['planner']
hz = gz(hx, hy)
ham = empty('HAMMOCK', C, loc=(hx, hy, hz), size=0.4)
for sx in (-1, 1):
    for dy in (-0.35, 0.35):
        p = obj('HAMMOCK_post', m_cyl('hp', 0.05, 0.06, 1.75, (0, 0, 0), 10), C, ham, loc=(sx * 1.45, dy * 0.6, 0.85),
                rot=(math.radians(-dy * 28), 0, 0), mats=[WOODM])
swing = empty('HAMMOCK_swing', C, ham, loc=(0, 0, 1.55), size=0.3)
L_, W_ = 2.2, 0.9
vv, ff = [], []
NX_, NY_ = 22, 8
for i in range(NX_ + 1):
    for j in range(NY_ + 1):
        x = -L_ / 2 + L_ * i / NX_; y = -W_ / 2 + W_ * j / NY_
        z = -1.0 + 0.42 * (2 * x / L_) ** 2 + 0.16 * (2 * y / W_) ** 2
        y *= 1 - 0.55 * (2 * x / L_) ** 4
        vv.append((x, y, z))
for i in range(NX_):
    for j in range(NY_):
        a0 = i * (NY_ + 1) + j
        ff.append((a0, a0 + NY_ + 1, a0 + NY_ + 2, a0 + 1))
m, nt, out = new_mat('MAT_hammock')
tc = nt.nodes.new('ShaderNodeTexCoord')
wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.inputs['Scale'].default_value = 3.0
try:
    wv.bands_direction = 'Y'
except Exception:
    pass
nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
hc = ramp(nt, wv.outputs['Fac'], [(0.0, hexc('#f4ead8')), (0.5, hexc('#f4ead8')), (0.52, hexc('#e8845c')), (0.7, hexc('#e8845c')), (0.72, hexc('#2f8f8a'))], 'CONSTANT')
b = bsdf_node(nt, rough=0.9, sheen=0.6); nt.links.new(hc, b.inputs['Base Color']); nt.links.new(b.outputs[0], out.inputs[0])
cloth = obj('HAMMOCK_cloth', mesh_from('hammock', vv, ff), C, swing, mats=[m])
mod_solidify(cloth, 0.012, 0.0); mod_subsurf(cloth, 1, 1)
rope = pbr('MAT_rope', '#d8c8a8', 0.9)
for sx in (-1, 1):
    obj('HAMMOCK_rope', m_tube('rope', [(sx * 1.42, 0, 0.12), (sx * 1.25, 0, -0.32), (sx * 1.1, 0, -0.58)], 0.012, 6), C, swing, mats=[rope])
for k in range(0, FRAME_END + 36, 36):               # gentle swing
    KO(swing, 1 + k, rot=(7 if (k // 36) % 2 == 0 else -7, 0, 0))
set_interp(swing, 'BEZIER')

# calendar paper (double sided image)
cal = canvas(256, 300, '#fbf8f1')
rect(cal, 0, 0, 256, 54, '#e8845c')
for i in range(30):
    cx, cy = 14 + (i % 6) * 39, 66 + (i // 6) * 44
    rect(cal, cx, cy, 33, 36, '#f2b90f' if i < 12 else '#e7e1d4', 0.9)
rect(cal, 14 + 0 * 39, 66 + 2 * 44, 33, 36, '#1f2c6b')
cal_img = save_image('paper_calendar', cal)
CALM = image_mat('MAT_paper_calendar', cal_img, rough=0.8)

# --- caption-writer bench + notebook + pencil
bx, by = CHILL['caption-writer']
bench = empty('BENCH', C, loc=(bx, by, gz(bx, by)), rot=(0, 0, math.pi), size=0.4)
for name, size, c in (('seat', (1.5, 0.45, 0.07), (0, 0, 0.44)), ('back', (1.5, 0.06, 0.38), (0, 0.24, 0.7))):
    o = obj('BENCH_' + name, m_box('b', size, c), C, bench, mats=[WOODM]); mod_bevel(o, 0.01, 2)
for sx in (-0.65, 0.65):
    obj('BENCH_leg', m_box('bl', (0.07, 0.42, 0.42), (sx, 0.02, 0.21)), C, bench, mats=[DARKM])

# --- video-director tripod + tiny camera (facing the peaks)
vx, vy = CHILL['video-director']
tri = empty('TRIPOD', C, loc=(vx, vy + 0.55, gz(vx, vy + 0.55)), size=0.3)
for k in range(3):
    a = k * 2.094
    p0 = Vector((0, 0, 0.72)); p1 = Vector((math.sin(a) * 0.28, math.cos(a) * 0.28, 0.0))
    obj('TRIPOD_leg', m_tube('tl', [p0, p1], 0.012, 6), C, tri, mats=[DARKM])
cam_body = pbr('MAT_tinycam', '#2b2b30', 0.4)
obj('TINYCAM_body', m_box('tc', (0.16, 0.11, 0.1), (0, 0, 0.79)), C, tri, mats=[cam_body])
lens_me = m_cyl('tl', 0.04, 0.035, 0.09, (0, 0, 0), 16)
lens_me.transform(Matrix.Translation((0, 0.1, 0.79)) @ Matrix.Rotation(-math.pi / 2, 4, 'X'))
obj('TINYCAM_lens', lens_me, C, tri, mats=[cam_body])
obj('TINYCAM_rec', m_sphere('rec', 0.012, (0.06, -0.056, 0.83), 10, 6), C, tri, mats=[emit_mat('MAT_rec', '#ff2a2a', 8.0)])

# --- trend-scout rock at the cliff edge
sxp, syp = CHILL['trend-scout']
rockm = bpy.data.materials.get('MAT_rock') or pbr('MAT_rock', '#a59f93', 0.85)
rk = obj('SCOUT_rock', m_rock('srock', 0.75, (0, 0, 0), seed=77, squash=0.55), C, loc=(sxp, syp, gz(sxp, syp)), mats=[rockm])
ROCK_TOP = gz(sxp, syp) + 0.75 * 0.55 * 0.9

# ------------------------------------------------------------ handheld props (parented, hidden after the run)
def handheld(a):
    aid = a['id']
    items = []
    if aid == 'planner':
        o = obj('PROP_calendar', m_plane('cal', 0.5, 0.58, (0, 0, 0), 'Y'), C, a['body'], loc=(0, -0.5, -0.36), rot=(math.radians(35), 0, math.pi), mats=[CALM])
        items.append(o)
    if aid == 'caption-writer':
        nb = obj('PROP_notebook', m_box('nb', (0.3, 0.22, 0.03), (0, 0, 0)), C, a['body'], loc=(0, -0.46, -0.22), rot=(math.radians(-25), 0, 0),
                 mats=[pbr('MAT_notebook', '#ff8a3d', 0.6)])
        obj('PROP_notebook_page', m_box('pg', (0.27, 0.2, 0.004), (0, 0, 0.017)), C, nb, mats=[pbr('MAT_paper', '#fbf8f1', 0.8)])
        items.append(nb)
        pen = obj('PROP_pencil', m_cyl('pen', 0.008, 0.006, 0.16, (0, 0, -0.06), 6), C, a['arms'][0], loc=(0, 0, -0.38), rot=(0.4, 0, 0),
                  mats=[pbr('MAT_pencil', '#f2b90f', 0.5)])
        items.append(pen)
    if aid == 'trend-scout':
        bi = empty('PROP_binoculars', C, a['body'], loc=(0, -0.43, 0.08), size=0.05)
        bm_ = pbr('MAT_binoculars', '#24262c', 0.35)
        for sx in (-1, 1):
            o = obj('PROP_binocular_tube', m_cyl('bt', 0.045, 0.05, 0.14, (0, 0, 0), 16), C, bi, loc=(sx * 0.07, -0.06, 0), rot=(math.pi / 2, 0, 0), mats=[bm_])
            items.append(o)
            obj('PROP_binocular_lens', m_cyl('bl', 0.04, 0.04, 0.004, (0, 0, -0.072), 16), C, o, mats=[pbr('MAT_lens', '#6a8fb5', 0.05, metal=0.6)])
        items.append(obj('PROP_binocular_bridge', m_box('bb', (0.1, 0.04, 0.03), (0, -0.05, 0)), C, bi, mats=[bm_]))
    if aid == 'video-director':
        pass
    return items


for aid, a in A.items():
    a['props'] = handheld(a)

# ------------------------------------------------------------ chill poses (key at f1 and f880, + loops)
def chill(a, f):
    aid = a['id']
    x, y = CHILL[aid]
    if aid == 'planner':
        # lies back in the hammock; carrier = the swing pivot (world), root is relative to it
        sw_world = Vector((hx, hy, hz + 1.55))
        pose(a, f, root_loc=(0.05, 0, -0.97), root_rot=90, body=(0, 0, 0.34), body_rot=(-72, 0, 0),
             armR=(-58, 18, 0), armL=(-58, -18, 0), footR=(-0.14, -0.5, 0.3), footL=(0.14, -0.5, 0.3),
             carrier=tuple(sw_world))
    elif aid == 'analyst':
        pose(a, f, root_loc=(x, y, gz(x, y) - 0.12), root_rot=200, body=(0, 0, 0.47), body_rot=(-88, 0, 0),
             armR=(-95, 12, 0), armL=(-20, -40, 0), footR=(-0.16, -0.62, 0.3), footL=(0.16, -0.58, 0.2))
    elif aid == 'caption-writer':
        pose(a, f, root_loc=(x, y + 0.03, gz(x, y) + 0.34), root_rot=180, body=(0, 0, 0.53), body_rot=(10, 0, 0),
             armR=(-55, 10, 15), armL=(-48, -25, 0), footR=(-0.14, -0.32, 0.02), footL=(0.14, -0.3, 0.02))
    elif aid == 'video-director':
        pose(a, f, root_loc=(x, y, gz(x, y)), root_rot=180, body=(0, 0, 0.53), body_rot=(9, 0, 0),
             armR=(-62, -8, 0), armL=(-62, 8, 0))
    elif aid == 'trend-scout':
        pose(a, f, root_loc=(x, y, ROCK_TOP), root_rot=180, body=(0, 0, 0.53), body_rot=(-6, 0, 0),
             armR=(-128, 32, 0), armL=(-128, -32, 0))


for aid, a in A.items():
    chill(a, 1)
    chill(a, T_CHILL_END)
    KO(a['ant'], 1, rot=(0, 0, 0))
    a['body_chill'] = Vector(a['body'].location)
# the planner's carrier follows the hammock swing
pc = A['planner']['carrier']
for k in range(0, T_CHILL_END, 36):
    KO(pc, 1 + k, rot=(7 if (k // 36) % 2 == 0 else -7, 0, 0))
KO(pc, T_CHILL_END, rot=(tuple(math.degrees(r) for r in pc.rotation_euler)))

# little chill loops (noise restricted to the chill time)
def noise_range(idb, path, index, strength, scale, f0, f1):
    m = add_noise(idb, path, index, strength, scale)
    if m:
        m.use_restricted_range = True; m.frame_start = f0; m.frame_end = f1; m.blend_in = 4; m.blend_out = 4
    return m


noise_range(A['caption-writer']['arms'][0], 'rotation_euler', 0, 0.12, 2.0, 1, T_CHILL_END)     # scribble
noise_range(A['caption-writer']['arms'][0], 'rotation_euler', 2, 0.15, 1.5, 1, T_CHILL_END)
noise_range(A['analyst']['arms'][0], 'rotation_euler', 1, 0.25, 9.0, 1, T_CHILL_END)             # pointing at stars
noise_range(A['trend-scout']['body'], 'rotation_euler', 2, 0.18, 30.0, 1, T_CHILL_END)           # slow scan
noise_range(A['video-director']['body'], 'rotation_euler', 0, 0.04, 20.0, 1, T_CHILL_END)
for a in A.values():                                                                            # antennas sway
    noise_range(a['ant'], 'rotation_euler', 0, 0.12, 12.0, 1, FRAME_END)
    noise_range(a['ant'], 'rotation_euler', 1, 0.12, 14.0, 1, FRAME_END)

# ------------------------------------------------------------ antenna perk-up on the pops (shots 11a / 11b)
for aid, f in PERK.items():
    a = A[aid]
    KO(a['ant'], f - 1, scl=1.0); KO(a['ant'], f + 2, scl=(1.25, 1.25, 1.6)); KO(a['ant'], f + 6, scl=(0.95, 0.95, 0.9))
    KO(a['ant'], min(f + 9, T_CHILL_END), scl=1.0)
    em = next(n for n in a['ball'].node_tree.nodes if n.type == 'EMISSION')
    for ff_, v in ((1, 4.0), (f - 1, 4.0), (f + 2, 30.0), (f + 12, 8.0)):
        em.inputs['Strength'].default_value = v; em.inputs['Strength'].keyframe_insert('default_value', frame=ff_)
    b0 = a['body_chill']                         # small startled bounce
    KO(a['body'], f - 1, loc=tuple(b0)); KO(a['body'], f + 2, loc=tuple(b0 + Vector((0, 0, 0.09))))
    KO(a['body'], min(f + 6, T_CHILL_END), loc=tuple(b0))

# ------------------------------------------------------------ run in + sit (shot 11c), screens on the bloops (11d)
RUN = {  # start point (blender xy) just outside the wide frame, start delay, waypoint behind the desks
    'analyst': ((-10.5, 2.8), 0, (-6.2, 2.3)),
    'caption-writer': ((-9.5, 5.0), 2, (-3.0, 3.7)),
    'planner': ((0.4, 8.6), 0, (0.0, 4.2)),
    'video-director': ((9.5, 5.0), 1, (3.0, 3.7)),
    'trend-scout': ((10.5, 2.8), 3, (6.2, 2.3)),
}
ARRIVE = {}


def h_at(p):
    on_deck = -8.2 < p.x < 8.2 and -4.7 < p.y < 5.7
    return DECK if on_deck else gz(p.x, p.y)


for i, ag in enumerate(AGENTS):
    aid = ag['id']; a = A[aid]
    stx, sty, srz = station(i)
    seat = Vector((stx, sty, 0)) + Matrix.Rotation(srz, 4, 'Z') @ SEAT_LOCAL
    (sx_, sy_), delay, (wx, wy) = RUN[aid]
    pts = [Vector((sx_, sy_)), Vector((wx, wy)), Vector((seat.x, seat.y))]
    f0 = T_RUN0 + delay
    run_end = SCREEN_ON[aid] - 14
    for p in a['props']:
        KH(p, T_CHILL_END, False); KH(p, T_RUN0, True)
    seglens = [(pts[k + 1] - pts[k]).length for k in range(len(pts) - 1)]
    total = sum(seglens)
    frames = max(10, run_end - f0)
    nsteps = max(4, frames // 3)
    for s in range(nsteps + 1):
        d = total * s / nsteps
        k = 0
        while k < len(seglens) - 1 and d > seglens[k]:
            d -= seglens[k]; k += 1
        p = pts[k] + (pts[k + 1] - pts[k]) * min(1.0, d / max(1e-6, seglens[k]))
        direc = (pts[k + 1] - pts[k]).normalized()
        yaw = math.degrees(math.atan2(direc.x, -direc.y))
        fr = f0 + round(frames * s / nsteps)
        ph = s % 2
        pose(a, fr, root_loc=(p.x, p.y, h_at(p)), root_rot=yaw, body=(0, 0, 0.53 + (0.07 if ph else 0.0)), body_rot=(14, 0, 0),
             armR=(40 if ph else -40, 10, 0), armL=(-40 if ph else 40, -10, 0),
             footR=(-0.14, -0.15 if ph else 0.1, 0.055 + (0.0 if ph else 0.07)), footL=(0.14, 0.1 if ph else -0.15, 0.055 + (0.07 if ph else 0.0)))
        last = fr
    yaw_desk = math.degrees(srz)
    sit_z = DECK + 0.30
    pose(a, last + 4, root_loc=(seat.x, seat.y, sit_z + 0.12), root_rot=yaw_desk, body=(0, 0, 0.6), body_rot=(0, 0, 0),
         armR=(-20, 30, 0), armL=(-20, -30, 0), footR=(-0.14, -0.2, 0.0), footL=(0.14, -0.2, 0.0))
    pose(a, last + 8, root_loc=(seat.x, seat.y, sit_z), root_rot=yaw_desk, body=(0, 0, 0.5), body_rot=(-4, 0, 0),
         armR=(-62, 8, 0), armL=(-62, -8, 0), footR=(-0.14, -0.3, -0.02), footL=(0.14, -0.3, -0.02))
    sitpose = dict(root_loc=(seat.x, seat.y, sit_z), root_rot=yaw_desk, body=(0, 0, 0.53), body_rot=(0, 0, 0),
                   armR=(-68, 8, 0), armL=(-68, -8, 0), footR=(-0.14, -0.3, -0.02), footL=(0.14, -0.3, -0.02))
    pose(a, last + 12, **sitpose)
    pose(a, FRAME_END, **sitpose)
    ARRIVE[aid] = last + 12
    for arm in a['arms']:                                   # typing jiggle
        noise_range(arm, 'rotation_euler', 0, 0.09, 1.6, last + 14, FRAME_END)
    noise_range(a['body'], 'rotation_euler', 2, 0.03, 25.0, last + 14, FRAME_END)
    if f0 > T_RUN0:
        pose(a, T_RUN0, root_loc=(sx_, sy_, h_at(pts[0])), root_rot=math.degrees(math.atan2((pts[1] - pts[0]).x, -(pts[1] - pts[0]).y)), body_rot=(14, 0, 0))
    hold(a, T_CHILL_END)
    # screen + desk glow on the bloop
    fon = SCREEN_ON[aid]
    es = bpy.data.materials['MAT_screen_' + aid].node_tree.nodes['SCREEN_BSDF'].inputs['Emission Strength']
    for ff_, v in ((1, 0.12), (fon - 1, 0.12), (fon + 2, 4.0), (fon + 6, 2.6)):
        es.default_value = v; es.keyframe_insert('default_value', frame=ff_)
    ld = bpy.data.lights['DESKLIGHT_' + aid]
    for ff_, v in ((1, 0.0), (fon - 1, 0.0), (fon + 3, 9.0), (fon + 6, 6.0)):
        ld.energy = v; ld.keyframe_insert('energy', frame=ff_)

print('perks', PERK, 'arrivals', ARRIVE, 'screens', SCREEN_ON)
print('05_agents done')

