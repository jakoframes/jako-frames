# 06_cameras_shots.py - one camera per shot (21 cameras for the 14 shots, shot 4 = 5 fast cuts with whip-pans,
# shot 11 = 4 cuts), timeline markers S01..S14 bound to the cameras, a per-shot face fill light, and the blocking
# animation for Jako and Claude (placement, turns, faces, hops on Claude's lines, shout pose, walk in shot 14).
# Needs 03_jako + 04_claude (+ 05_agents for focus targets). Re-runnable: rebuilds collection CAMERAS and
# clears/re-keys the Jako and Claude animation.
import sys, importlib
sys.path.insert(0, r'C:\Users\acer\Downloads\jako-frames\reel-agents-dolomites\blender')
import common; importlib.reload(common)
from common import *

scene = bpy.context.scene
CC = reset_coll('CAMERAS')
for m in list(scene.timeline_markers):
    scene.timeline_markers.remove(m)
OB = bpy.data.objects
for cname in ('JAKO', 'CLAUDE'):
    for o in bpy.data.collections[cname].all_objects:
        clear_anim(o)

J = {k: OB['JAKO' + ('' if k == 'root' else '_' + k)] for k in ('root', 'hips', 'torso', 'head', 'arm_R', 'arm_L', 'leg_R', 'leg_L')}
FACES = {k: OB['FACE_' + k] for k in ('neutral', 'blink', 'surprised', 'happy')}
CR, CB = OB['CLAUDE'], OB['CLAUDE_body']

gA = ground_h(*JAKO_A)
gC = ground_h(*CLAUDE_A)
JA = Vector((JAKO_A[0], JAKO_A[1], gA))
CA = Vector((CLAUDE_A[0], CLAUDE_A[1], gC))
DOOR_Z = 0.15
JD = Vector((DOOR[0] - 0.15, DOOR[1], DOOR_Z))
CD = Vector((DOOR[0] + 0.48, DOOR[1] + 0.12, DOOR_Z))
W0, W1 = Vector((-7.6, 25.6, 0)), Vector((-9.2, 29.9, 0))      # shot 14 walk (towards the campfire)
for v in (W0, W1):
    v.z = ground_h(v.x, v.y)

ARM_IDLE_R, ARM_IDLE_L = (0, 10, 0), (0, -10, 0)


def deg3(e):
    return tuple(math.degrees(a) for a in e)


def jako(f, loc=None, yaw=None, head=(0, 0, 0), armR=ARM_IDLE_R, armL=ARM_IDLE_L, hips=(0, 0, 0), legs=((0, 0, 0), (0, 0, 0)),
         hips_z=0.0, arm_scale=1.0):
    if loc is not None or yaw is not None:
        KO(J['root'], f, loc=tuple(loc) if loc is not None else None, rot=(0, 0, yaw) if yaw is not None else None)
    KO(J['hips'], f, loc=(0, 0, 0.298 + hips_z), rot=hips)
    KO(J['head'], f, rot=head)
    KO(J['arm_R'], f, rot=armR, scl=(1, 1, arm_scale)); KO(J['arm_L'], f, rot=armL, scl=(1, 1, arm_scale))
    KO(J['leg_R'], f, rot=legs[0]); KO(J['leg_L'], f, rot=legs[1])


def face(f, name, dur=None):
    for k, o in FACES.items():
        KH(o, f, k != name)
    if dur:
        for k, o in FACES.items():
            KH(o, f + dur, k != 'neutral')


def blink(f, base='neutral'):
    for k, o in FACES.items():
        KH(o, f, k != 'blink')
        KH(o, f + 3, k != base)


def claude(f, loc=None, yaw=None, tilt=0.0, body_z=0.0, squash=1.0):
    if loc is not None or yaw is not None:
        KO(CR, f, loc=tuple(loc) if loc is not None else None, rot=(0, 0, yaw) if yaw is not None else None)
    s = squash
    KO(CB, f, loc=(0, 0, body_z), rot=(tilt, 0, 0), scl=(1 / math.sqrt(s), 1 / math.sqrt(s), s))


def hop(f, tilt=0.0, h=0.09):
    claude(f, tilt=tilt); claude(f + 3, tilt=tilt, squash=0.86); claude(f + 7, tilt=tilt, body_z=h, squash=1.1)
    claude(f + 11, tilt=tilt, body_z=0.0, squash=0.88); claude(f + 15, tilt=tilt)


def yaw_to(src, dst):
    d = Vector(dst) - Vector(src)
    return math.degrees(math.atan2(d.x, -d.y))


def arm_point(side, target_local):
    """Rotation (deg) pointing an arm (rest = -Z) at a point in torso-pivot space."""
    sh = Vector((-0.166 if side == 'R' else 0.166, 0, 0.301))
    d = (Vector(target_local) - sh)
    q = Vector((0, 0, -1)).rotation_difference(d.normalized())
    return deg3(q.to_euler()), d.length / 0.212


# ================================================================ cameras
def make_cam(name, lens, fstop=2.8, focus=None, fdist=None):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens; cd.sensor_width = 36.0; cd.sensor_fit = 'AUTO'
    cd.clip_start = 0.05; cd.clip_end = 3000.0
    cd.dof.use_dof = True; cd.dof.aperture_fstop = fstop
    if focus is not None:
        cd.dof.focus_object = focus
    if fdist:
        cd.dof.focus_distance = fdist
    try:
        cd.dof.aperture_blades = 7
    except Exception:
        pass
    return obj(name, cd, CC)


def static_cam(name, loc, tgt, lens, fstop=2.8, focus=None, roll=0.0, push=None, f0=None, f1=None):
    c = make_cam(name, lens, fstop, focus, (Vector(tgt) - Vector(loc)).length)
    c.location = loc; c.rotation_euler = look_rot(loc, tgt, roll)
    if push and f0 is not None:
        d = (Vector(tgt) - Vector(loc)).normalized() * push
        KO(c, f0, loc=tuple(loc)); KO(c, f1, loc=tuple(Vector(loc) + d))
    return c


def tracked_cam(name, keys, lens, fstop=2.8, focus=None):
    """keys: list of (frame, cam_loc, target_loc)."""
    c = make_cam(name, lens, fstop, focus, (Vector(keys[0][2]) - Vector(keys[0][1])).length)
    t = empty(name + '_tgt', CC, size=0.3, kind='SPHERE')
    for f, l, tg in keys:
        KO(c, f, loc=tuple(l)); KO(t, f, loc=tuple(tg))
    con = c.constraints.new('TRACK_TO'); con.target = t; con.track_axis = 'TRACK_NEGATIVE_Z'; con.up_axis = 'UP_Y'
    if focus is None:
        c.data.dof.focus_object = t
    return c


def whip(c, f0, f1, ang_in=28.0, ang_out=-28.0):
    base = c.rotation_euler.copy()
    for f, dz in ((f0, ang_in), (f0 + 4, 0.0), (f1 - 4, 0.0), (f1, ang_out)):
        c.rotation_euler = (base.x, base.y, base.z + math.radians(dz)); c.keyframe_insert('rotation_euler', frame=f)
    c.rotation_euler = base


cams = {}
HEADT = J['head']
mid = (JA + CA) / 2
s0 = lambda sid: SHOT[sid][1]
s1 = lambda sid: SHOT[sid][2]

# 01 behind-shoulder, low, office + pink peaks behind
cams['01'] = static_cam('CAM_01', JA + Vector((-0.75, -2.1, 0.55)), JA + Vector((2.6, 14.0, 2.8)), 22, 4.0, HEADT,
                        push=0.3, f0=s0('01'), f1=s1('01'))
# 02 low on Claude, Jako towering
cams['02'] = static_cam('CAM_02', CA + Vector((0.6, 0.78, 0.24)), Vector((1.08, -18.35, gA + 0.66)), 18, 3.2, CB)
# 03 close-up Jako, push-in, whip out into shot 4 (whoosh_01)
cams['03'] = static_cam('CAM_03', JA + Vector((0.15, 1.75, 0.98)), JA + Vector((0, 0, 0.98)), 45, 2.0, HEADT, push=0.25, f0=s0('03'), f1=s1('03'))
whip(cams['03'], s0('03'), s1('03'), 0.0, -28.0)

# 04 a-e fast cuts on the chilling agents (whip-pans between)
hx, hy = CHILL['planner']; hz = ground_h(hx, hy)
ax_, ay_ = CHILL['analyst']; az_ = ground_h(ax_, ay_)
bx, by = CHILL['caption-writer']; bz = ground_h(bx, by)
vx, vy = CHILL['video-director']; vz = ground_h(vx, vy)
sx_, sy_ = CHILL['trend-scout']; sz_ = ground_h(sx_, sy_) + 0.4
AGB = lambda aid: OB.get('AG_%s_body' % aid)
cams['04a'] = static_cam('CAM_04a', (hx + 1.45, hy - 0.9, hz + 1.75), (hx - 0.25, hy + 0.15, hz + 0.85), 32, 2.8, AGB('planner'))
cams['04b'] = static_cam('CAM_04b', (ax_ + 1.0, ay_ - 1.1, az_ + 2.0), (ax_, ay_, az_ + 0.35), 28, 2.8, AGB('analyst'))
cams['04c'] = static_cam('CAM_04c', (bx + 0.95, by + 1.7, bz + 1.05), (bx, by, bz + 0.85), 40, 2.8, AGB('caption-writer'))
cams['04d'] = static_cam('CAM_04d', (vx - 0.95, vy - 1.15, vz + 1.1), (vx + 1.0, vy + 30.0, vz + 6.0), 26, 4.0, AGB('video-director'))
cams['04e'] = static_cam('CAM_04e', (sx_ - 1.05, sy_ - 1.35, sz_ + 0.85), (sx_ + 0.6, sy_ + 4.0, sz_ + 1.4), 30, 4.0, AGB('trend-scout'))
for sid in ('04a', '04b', '04c', '04d', '04e'):
    _, f0, f1, _ = SHOT[sid]
    whip(cams[sid], f0, f1, 28.0, 0.0 if sid == '04e' else -28.0)

# 05 medium two-shot, Jako looks around
cams['05'] = static_cam('CAM_05', JA + Vector((1.95, 2.45, 1.0)), mid + Vector((0, 0, 0.62)), 32, 2.8, HEADT)
# 06 drone (2.7 s): rise + orbit over the meadow, fog in the valley, Sassolungo pink
f6a, f6b = s0('06'), s1('06')
cams['06'] = tracked_cam('CAM_06', [(f6a, (8.0, -22.0, 8.0), (0.0, 10.0, 2.0)), ((f6a + f6b) // 2, (0.0, 2.0, 24.0), (8.0, 90.0, -25.0)),
                                    (f6b, (-6.0, 18.0, 40.0), (25.0, 260.0, -10.0))], 24, 8.0)
# 07 two-shot side, Jako turns to Claude
cams['07'] = static_cam('CAM_07', CA + Vector((2.3, 0.75, 0.8)), mid + Vector((0, 0, 0.6)), 35, 2.8, HEADT)
# 08 close on Claude, then slow pan across the peaks
f8a, f8b = s0('08'), s1('08')
cams['08'] = tracked_cam('CAM_08', [(f8a, CA + Vector((0.36, 0.78, 0.3)), CA + Vector((0, 0, 0.2))),
                                    (f8a + 22, CA + Vector((0.36, 0.78, 0.3)), CA + Vector((0, 0, 0.2))),
                                    (f8b, CA + Vector((0.36, 0.78, 0.36)), CA + Vector((9.0, 60.0, 14.0)))], 40, 2.8)
# 09 medium two-shot looking south, agents chilling behind (out of focus)
cams['09'] = static_cam('CAM_09', JA + Vector((0.95, 2.25, 0.85)), mid + Vector((0.12, 0, 0.58)), 38, 2.2, HEADT)
# 10 low hero angle, hands cupped around the mouth
cams['10'] = static_cam('CAM_10', JA + Vector((-0.8, 1.2, 0.28)), JA + Vector((0, 0, 1.02)), 20, 3.2, HEADT)
# 11 a-d: antennas perk (south group, north pair), wide office run-in, screens light up
cams['11a'] = static_cam('CAM_11a', (-3.2, -26.2, ground_h(-3.2, -26.2) + 1.5), (-3.4, -32.5, ground_h(-3.4, -32.5) + 0.7), 28, 4.0, AGB('caption-writer'))
cams['11b'] = static_cam('CAM_11b', (8.0, 26.0, ground_h(8.0, 26.0) + 1.9), (8.0, 34.0, ground_h(8.0, 34.0) + 1.0), 24, 5.6, AGB('video-director'))
cams['11c'] = static_cam('CAM_11c', (-4.8, -9.6, 3.4), (0.4, 2.2, 0.6), 26, 8.0, AGB('planner'))
cams['11d'] = static_cam('CAM_11d', (-1.25, 3.7, 1.5), (0.35, 1.6, 0.98), 30, 2.8, OB.get('SCREEN_planner'))
# 12 inside the office: slow dolly along the desks, Jako + Claude watching from the doorway (foreground)
cams['12'] = tracked_cam('CAM_12', [(s0('12'), (0.9, -7.7, 1.6), (1.4, 1.4, 0.95)), (s1('12'), (-0.9, -7.6, 1.6), (-1.4, 1.4, 0.95))], 32, 2.8,
                         OB.get('AG_planner_body'))
# 13 close-up Jako in warm light (camera inside the office looking out)
cams['13'] = static_cam('CAM_13', JD + Vector((0.3, 2.1, 1.05)), JD + Vector((0, 0, 0.98)), 55, 2.0, HEADT, push=0.1, f0=s0('13'), f1=s1('13'))
# 14 behind them walking to the campfire, then crane up to the first stars
F14A, F14B = s0('14'), s1('14')
F14W = F14A + 80                       # walk ends, crane continues to the stars
cams['14'] = tracked_cam('CAM_14', [(F14A, W0 + Vector((1.7, -2.8, 1.15)), W0 + Vector((-3.2, 7.5, 0.9))),
                                    (F14A + 50, W0 + Vector((1.2, -1.0, 1.55)), W1 + Vector((-2.4, 5.0, 1.2))),
                                    (F14B, W1 + Vector((0.3, -2.6, 8.5)), W1 + Vector((-3.0, 40.0, 34.0)))], 26, 4.0, HEADT)

for sid, f0, f1, cname in SHOTS:
    mk = scene.timeline_markers.new('S' + sid, frame=f0)
    mk.camera = OB[cname]
scene.camera = OB['CAM_01']

# ================================================================ face fill light (moves with the shots)
fd = bpy.data.lights.new('FACE_FILL', 'AREA'); fd.shape = 'DISK'; fd.size = 1.4; fd.color = hex3('#efe2ff')
fill = obj('FACE_FILL', fd, CC)
try:
    fd.use_shadow = False
except Exception:
    pass
kd = bpy.data.lights.new('WARM_KEY', 'AREA'); kd.shape = 'DISK'; kd.size = 1.0; kd.color = hex3('#ffb070')
warm = obj('WARM_KEY', kd, CC)
FILLS = {  # shot: (subject point, energy, warm energy)
    '01': (JA + Vector((0, 0, 1.0)), 6, 0), '02': (CA + Vector((0, 0, 0.3)), 8, 0), '03': (JA + Vector((0, 0, 0.95)), 14, 0),
    '04a': (Vector((hx, hy, hz + 0.8)), 10, 0), '04b': (Vector((ax_, ay_, az_ + 0.4)), 10, 0), '04c': (Vector((bx, by, bz + 0.9)), 10, 0),
    '04d': (Vector((vx, vy, vz + 1.0)), 6, 0), '04e': (Vector((sx_, sy_, sz_ + 1.0)), 6, 0), '05': (mid + Vector((0, 0, 0.8)), 12, 0),
    '06': (JA, 0, 0), '07': (mid + Vector((0, 0, 0.8)), 12, 0), '08': (CA + Vector((0, 0, 0.25)), 10, 0),
    '09': (mid + Vector((0, 0, 0.8)), 32, 0), '10': (JA + Vector((0, 0, 1.0)), 12, 0),
    '11a': (Vector((-3.4, -32.5, 1.0)), 0, 0), '11b': (Vector((8, 34, 1)), 0, 0), '11c': (Vector((0, 2, 1)), 0, 0),
    '11d': (Vector((0, 2.4, 1.1)), 0, 0), '12': (JD + Vector((0, 0, 1.0)), 0, 12), '13': (JD + Vector((0, 0, 0.95)), 10, 22),
    '14': (W0 + Vector((0, 0, 1)), 0, 0)}
for sid, f0, f1, cname in SHOTS:
    subj, e, we = FILLS[sid]
    cam = OB[cname]
    camloc = cam.location.copy()
    if cam.animation_data and fcurves_of(cam):
        scene.frame_set(f0); camloc = cam.matrix_world.translation.copy()
    off = (camloc - subj); off.z = 0
    side = Vector((off.y, -off.x, 0)).normalized() if off.length > 1e-3 else Vector((1, 0, 0))
    pos = subj + off.normalized() * 1.6 + side * 0.9 + Vector((0, 0, 0.7)) if off.length > 1e-3 else subj + Vector((0, 0, 2))
    fill.location = pos; fill.rotation_euler = look_rot(pos, subj)
    fill.keyframe_insert('location', frame=f0); fill.keyframe_insert('rotation_euler', frame=f0)
    fd.energy = e; fd.keyframe_insert('energy', frame=f0)
    wpos = subj + Vector((0.0, 1.8, 0.6)) if sid in ('12', '13') else subj + Vector((0, 0, 3))
    warm.location = wpos; warm.rotation_euler = look_rot(wpos, subj)
    warm.keyframe_insert('location', frame=f0); warm.keyframe_insert('rotation_euler', frame=f0)
    kd.energy = we; kd.keyframe_insert('energy', frame=f0)
set_interp(fill, 'CONSTANT'); set_interp(fd, 'CONSTANT'); set_interp(warm, 'CONSTANT'); set_interp(kd, 'CONSTANT')

# ================================================================ Jako + Claude blocking
N_, YAW_C = 180.0, 180.0
yaw_cj = yaw_to(CA, JA)                     # Claude facing Jako
# --- shot 1: standing at the meadow spot, looking at the office (J01)
a, b = s0('01'), s1('01')
face(a, 'neutral')
jako(a, JA, N_); jako(CUES['J01'] + 4, head=(-3, 0, -6)); jako(b, JA, N_, head=(0, 0, 4))
claude(a, CA, YAW_C); claude(b, CA, YAW_C)
# --- shot 2: Claude hops on C01 and looks up; Jako looks down at it
a, b = s0('02'), s1('02')
cy2 = yaw_to(CA, cams['02'].location)
jako(a, JA, N_, head=(14, 0, -18)); jako(b, JA, N_, head=(16, 0, -22))
claude(a, CA, cy2); hop(CUES['C01'])
claude(CUES['C01'] + 18, CA, cy2, tilt=-16); claude(b, CA, cy2, tilt=-18)
# --- shot 3: surprised (J02), whip out
a, b = s0('03'), s1('03')
face(a, 'surprised')
jako(a, JA, N_, head=(-4, 0, 0)); jako(CUES['J02'] + 3, head=(-9, 0, 0), hips_z=0.02); jako(b, JA, N_, head=(-8, 0, 0))
# --- shot 5: looks around (J03)
a, b = s0('05'), s1('05')
face(a, 'neutral')
jako(a, JA, N_, head=(0, 0, 0)); jako(a + 10, head=(-3, 0, 38)); jako(a + 22, head=(-3, 0, -38)); jako(b, JA, N_, head=(0, 0, -10))
claude(a, CA, 165); claude(b, CA, 165)
# --- shot 6: drone (characters tiny)
a, b = s0('06'), s1('06')
jako(a, JA, N_); jako(b, JA, N_)
claude(a, CA, 165); claude(b, CA, 165)
# --- shot 7: Jako turns to Claude (J04)
a, b = s0('07'), s1('07')
yaw_jc = yaw_to(JA, CA)
turn = (N_ + yaw_jc) / 2 + 18
jako(a, JA, N_); jako(a + 12, JA, turn, head=(4, 0, 12)); jako(b, JA, turn, head=(4, 0, 14))
ycj = yaw_cj + 360 if yaw_cj < 0 else yaw_cj
claude(a, CA, ycj); claude(b, CA, ycj)
blink(a + 30)
# --- shot 8: close on Claude, hop + happy wiggle on C04, then pan to the peaks
a, b = s0('08'), s1('08')
cy8 = yaw_to(CA, cams['08'].location)
claude(a, CA, cy8); hop(CUES['C04'], h=0.05)
for k, f in enumerate(range(CUES['C04'] + 16, CUES['C04'] + 40, 4)):
    KO(CR, f, rot=(0, 0, cy8 + (12 if k % 2 == 0 else -12)))
claude(CUES['C04'] + 42, CA, cy8); claude(b, CA, cy8)
jako(a, JA, 150, head=(6, 0, 0)); jako(b, JA, 150, head=(6, 0, 0))
# --- shot 9: Q&A, agents chilling behind out of focus
a, b = s0('09'), s1('09')
face(a, 'neutral')
jako(a, JA, 152, head=(-4, 0, -10)); jako(CUES['J05'] + 4, head=(-5, 4, -12))
jako(CUES['J06'], head=(-4, 9, -10)); jako(CUES['C06'] + 6, head=(-2, 0, -14))
jako(CUES['J07'], head=(-5, -10, -10)); jako(CUES['C07'] + 6, head=(-3, 0, -12)); jako(b, JA, 152, head=(-3, 0, -12))
claude(a, CA, 186)
for cue in ('C05', 'C06', 'C07'):
    hop(CUES[cue], h=0.07)
hop((CUES['C06'] + CUE_END['C06']) // 2, h=0.04)
claude(b, CA, 186)
for f in (a + 20, CUES['C05'] + 25, CUES['C06'] + 30, CUES['J07'] - 6, b - 8):
    blink(f)
# --- shot 10: hands cupped around the mouth, shout towards the office (J08)
a, b = s0('10'), s1('10')
armR_rot, sR = arm_point('R', (-0.075, -0.25, 0.43))
armL_rot, sL = arm_point('L', (0.075, -0.25, 0.43))
asc = min(1.25, max(sR, sL))
face(a, 'surprised')
jako(a, JA, N_, head=(0, 0, 0), hips=(0, 0, 0))
jako(CUES['J08'] - 1, JA, N_, head=(-6, 0, 0), hips=(6, 0, 0), armR=armR_rot, armL=armL_rot, arm_scale=asc)
jako(b, JA, N_, head=(-8, 0, 0), hips=(8, 0, 0), armR=armR_rot, armL=armL_rot, arm_scale=asc)
claude(a, CA, YAW_C); claude(b, CA, YAW_C)
# --- shot 11: Jako off screen
jako(s0('11a') + 10, JA, N_)
# --- shot 12: doorway, watching the agents work (C08, J09, C09)
a, b = s0('12'), s1('12')
face(a, 'neutral')
jako(a, JD, N_, head=(6, 0, 0)); jako(CUES['J09'] + 10, head=(4, 0, 18)); jako(CUES['J09'] + 50, head=(4, 0, -16)); jako(b, JD, N_, head=(4, 0, 0))
claude(a, CD, YAW_C); hop(CUES['C08'], h=0.06); hop(CUES['C09'], h=0.08); claude(b, CD, YAW_C)
# --- shot 13: close-up, happy (J10, C10)
a, b = s0('13'), s1('13')
face(a, 'happy')
jako(a, JD, N_, head=(-4, 0, 0)); jako(CUES['C10'], head=(-6, 6, 0)); jako(b, JD, N_, head=(-4, 4, 0))
claude(a, CD, YAW_C); hop(CUES['C10'], h=0.05); claude(b, CD, YAW_C)
# --- shot 14: walk towards the campfire (J11), camera cranes up to the stars
a = F14A
face(a, 'happy')
walk_yaw = yaw_to(W0, W1)
steps = 14
for s in range(steps + 1):
    t = s / steps
    f = a + round(t * (F14W - a))
    p = W0.lerp(W1, t); p.z = ground_h(p.x, p.y)
    ph = 1 if s % 2 else -1
    last = s == steps
    jako(f, p, walk_yaw, head=(0, 0, 0), armR=(0 if last else 18 * ph, 10, 0), armL=(0 if last else -18 * ph, -10, 0),
         legs=((0 if last else -22 * ph, 0, 0), (0 if last else 22 * ph, 0, 0)), hips_z=0.012 if (s % 2 and not last) else 0.0)
    cp = p + Vector((0.55, 0.15, 0)); cp.z = ground_h(cp.x, cp.y)
    claude(f, cp, walk_yaw, body_z=0.035 if (s % 2 and not last) else 0.0, squash=1.0 if last else (1.04 if s % 2 else 0.95))
jako(F14B, p, walk_yaw); claude(F14B, cp, walk_yaw)

# idle life: breathing + tiny head drift
KO(J['torso'], 1, scl=1.0)
add_noise(J['torso'], 'scale', 2, 0.006, 22.0)
add_noise(J['head'], 'rotation_euler', 2, 0.02, 40.0)
for o in FACES.values():
    set_interp(o, 'CONSTANT')

scene.frame_start, scene.frame_end = FRAME_START, FRAME_END
print('cameras', len(cams), 'markers', len(scene.timeline_markers))
print('06_cameras_shots done')
