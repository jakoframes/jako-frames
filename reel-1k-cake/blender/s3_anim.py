# s3_anim.py - all acting, the phone, the cake slide, cameras + cuts, sound strip, and the subtitle anchors.
# Everything is keyed from audio/timeline.json (word times), so re-running after an audio change re-times the film.
# Idempotent: clears the animation it owns and rebuilds collection CAMERAS.
import sys, importlib
sys.path.insert(0, r'C:\Users\acer\Downloads\jako-frames\reel-1k-cake\blender')
import common; importlib.reload(common)
from common import *
from bpy_extras.object_utils import world_to_camera_view

sc = bpy.context.scene
O = bpy.data.objects
rig = O['JAKO_rig']; SPOT = O['JAKO_SPOT']
CL = O['CLAUDE']; BODY = O['CLAUDE_body']; TORSO = O['CLAUDE_torso']; CMESH = O['CLAUDE_mesh']
ARM = {'L': O['CLAUDE_arm_L'], 'R': O['CLAUDE_arm_R']}
EYEP = [O['CLAUDE_eye_L'], O['CLAUDE_eye_R']]
EYEH = [O['CLAUDE_eyehappy_L'], O['CLAUDE_eyehappy_R']]
CAKE = O['CAKE']; PHONE = O['PHONE']
TOP = DESK_H
REST = json.loads(sc['jako_rest_pose'])

for o in [rig, SPOT, CL, BODY, TORSO, CMESH, CAKE, PHONE] + list(ARM.values()) + EYEP + EYEH:
    clear_anim(o)
for o in EYEH + EYEP:
    for ch in o.children:
        clear_anim(ch)
for pb in rig.pose.bones:
    pb.rotation_mode = 'XYZ'
    r = REST.get(pb.name, (0, 0, 0))
    pb.rotation_euler = tuple(math.radians(a) for a in r)
    pb.location = (0, 0, 0)


def W(lid, word, k=0, end=False):
    """time (s) of the k-th word in line lid that starts with `word` (case-insensitive)."""
    ws = [w for w in LINE[lid]['words'] if w['w'].lower().strip('.,!?').startswith(word.lower())]
    w = ws[min(k, len(ws) - 1)]
    return w['e'] if end else w['s']


def S(lid):
    return LINE[lid]['start']


def E(lid):
    return LINE[lid]['end']


def ease_all(idb):
    for fc in fcurves_of(idb):
        for kp in fc.keyframe_points:
            if kp.interpolation != 'CONSTANT':
                kp.interpolation = 'BEZIER'
                kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'


# ================================================================= generic pose keying
def key_obj(o, t, loc=None, rot=None, scl=None):
    f = F(t)
    if loc is not None:
        o.location = loc; o.keyframe_insert('location', frame=f)
    if rot is not None:
        o.rotation_euler = tuple(math.radians(a) for a in rot); o.keyframe_insert('rotation_euler', frame=f)
    if scl is not None:
        o.scale = scl if isinstance(scl, (tuple, list)) else (scl, scl, scl); o.keyframe_insert('scale', frame=f)


def key_bone(name, t, rot):
    """rot = offset (deg) added to the rest pose."""
    pb = rig.pose.bones[name]
    r0 = REST.get(name, (0, 0, 0))
    pb.rotation_euler = tuple(math.radians(a + b) for a, b in zip(r0, rot))
    pb.keyframe_insert('rotation_euler', frame=F(t))


def key_prop(t, **kw):
    for k, v in kw.items():
        rig[k] = v
        rig.keyframe_insert('["%s"]' % k, frame=F(t))


# ================================================================= JAKO
# ---- mouth: talk toggles 0/1 from the Jako envelope; happy (2) / surprised (3) as base states between words
env = TL['env_jako']
nf = len(env)
base = [0] * nf                         # mouth when not talking


def setbase(t0, t1, v):
    for i in range(max(0, int(t0 * FPS)), min(nf, int(t1 * FPS))):
        base[i] = v


setbase(W('J02', 'thousand'), S('C02'), 2)        # proud smile after "thousand followers"
setbase(E('C03') - 0.6, S('J04'), 2)              # "Congrats!" -> smile
setbase(W('J08', 'so'), E('J08') + 0.3, 2)        # "So I'll eat it" smug grin
setbase(S('C08'), nf / FPS, 2)                    # laugh ending
setbase(S('J03'), E('J03') + 0.35, 3)             # "What?" surprised
talk = [False] * nf
for l in TL['lines']:
    if l['who'] != 'jako' or l['id'] == 'JL':
        continue
    for i in range(int(l['start'] * FPS) - 1, min(nf, int(l['end'] * FPS) + 2)):
        talk[i] = True
state, prev, hold = [], None, 0
for i in range(nf):
    if talk[i]:
        o = env[i] > (0.20 if prev == 1 else 0.30)          # hysteresis
        v = 1 if o else (base[i] if base[i] == 3 else 0)
        if prev is not None and v != prev and hold < 2:      # hold every mouth shape >= 2 frames
            v = prev
    else:
        v = base[i]
    hold = hold + 1 if v == prev else 0
    state.append(v); prev = v
# laugh: mouth flaps happy<->talk
for t in np.arange(LINE['JL']['start'], LINE['JL']['end'] + 0.5, 0.12):
    i = int(t * FPS)
    if i < nf:
        state[i] = 1 if int((t - LINE['JL']['start']) / 0.12) % 2 == 0 else 2
last = None
for i, v in enumerate(state):
    if v != last:
        key_prop(i / FPS, mouth=v)
        last = v

# ---- eyes: neutral 0 / blink 1 / happy 2 / surprised 3
EYE_EVENTS = [(0.0, 0), (W('J02', 'thousand'), 2), (W('J02', 'with') - 0.1, 0), (S('J03') - 0.05, 3), (E('J03') + 0.5, 0),
              (W('C03', 'congrats'), 2), (S('J04') - 0.1, 0), (W('J07', 'exactly'), 1), (W('J07', 'meant', end=True) + 0.1, 0),
              (W('J08', 'so'), 2), (S('C08') + 0.05, 3), (W('C08', 'out', end=True) + 0.05, 2)]
EYE_EVENTS.sort()
spans = [(EYE_EVENTS[i][0], EYE_EVENTS[i + 1][0] if i + 1 < len(EYE_EVENTS) else 99, EYE_EVENTS[i][1]) for i in range(len(EYE_EVENTS))]
rng = random.Random(4)
t, blinks = 1.4, []
while t < TL['total_s'] - 1.0:
    st = [s for s in spans if s[0] <= t < s[1]][0]
    if st[2] == 0 and t + 0.2 < st[1] and t - 0.25 > st[0]:
        blinks.append(t)
    t += rng.uniform(2.4, 3.8)
ev = list(EYE_EVENTS)
for b in blinks:
    ev += [(b, 1), (b + 0.13, 0)]
ev.sort()
for t, v in ev:
    key_prop(t, eyes=v)
key_prop(0.0, shades=0, blush=0.0)
key_prop(W('J02', 'thousand'), blush=0.0); key_prop(W('J02', 'followers'), blush=0.6); key_prop(S('C02'), blush=0.2)
key_prop(S('C08'), blush=0.2); key_prop(S('CL') + 0.3, blush=0.8)
set_interp(rig, 'CONSTANT', path='["')
for fc in fcurves_of(rig):                       # blush may glide
    if fc.data_path == '["blush"]':
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'

# ---- body & head (offsets from rest, degrees). Head bone: X = nod (+ down), Y = turn (+ toward screen right), Z = tilt
SP0 = Vector((JAKO_XY[0], JAKO_XY[1], JAKO_Z))
LOOK_C = -16          # head turn toward Claude (screen-left)


def jpose(t, head=(0, 0, 0), chest=(0, 0, 0), spot=(0, 0, 0), spot_rot=(0, 0, 0), armL=(0, 0, 0), armR=(0, 0, 0), foreL=(0, 0, 0), foreR=(0, 0, 0)):
    key_bone('head', t, head)
    key_bone('chest', t, chest)
    key_bone('upper_arm.L', t, armL); key_bone('upper_arm.R', t, armR)
    key_bone('forearm.L', t, foreL); key_bone('forearm.R', t, foreR)
    key_obj(SPOT, t, loc=tuple(SP0 + Vector(spot)), rot=spot_rot)


jpose(0.0, head=(4, LOOK_C, 0))                                          # watches Claude's phone
jpose(S('J01') - 0.15, head=(4, LOOK_C, 0))
jpose(S('J01') + 0.1, head=(0, LOOK_C + 4, 3))                            # "Claude."
jpose(E('C01') - 0.3, head=(2, -6, 0))                                    # looks between Claude and the cake
jpose(S('J02'), head=(0, -4, 0), chest=(-3, 0, 0))
jpose(W('J02', 'thousand'), head=(-6, 0, 4), chest=(-6, 0, 0), spot=(0, 0, 0.015))     # proud
jpose(W('J02', 'five'), head=(-3, 2, -2), chest=(-4, 0, 0))
jpose(W('J02', 'with'), head=(3, LOOK_C, 3), chest=(2, -6, 0))           # "...with you" toward Claude
jpose(E('J02'), head=(2, LOOK_C, 2), chest=(1, -5, 0))
jpose(S('C02') + 0.6, head=(1, LOOK_C, 0))
jpose(S('J03') - 0.08, head=(1, LOOK_C, 0), spot=(0, 0, 0))
jpose(S('J03') + 0.06, head=(-9, LOOK_C - 4, -5), chest=(-5, 0, 0), spot=(0, 0.02, 0.02))  # "What?" jerk back
jpose(E('J03') + 0.4, head=(-5, LOOK_C, -3), chest=(-3, 0, 0))
jpose(W('C03', 'congrats'), head=(-3, LOOK_C, 4), spot=(0, 0, 0.012))
jpose(S('J04'), head=(0, LOOK_C, 0))
jpose(W('J04', 'what'), head=(2, LOOK_C + 2, 9))                          # head tilt "what's the plan?"
jpose(E('J04') + 0.3, head=(2, LOOK_C, 6))
jpose(S('J05'), head=(3, -4, 0), armL=(0, 0, 0), armR=(0, 0, 0))
jpose(W('J05', 'keep'), head=(4, -2, -7), chest=(0, 0, 0), spot=(0, 0, 0.02), armL=(0, 0, -14), armR=(0, 0, 14))   # shrug
jpose(E('J05') + 0.25, head=(3, LOOK_C, -4), spot=(0, 0, 0))
jpose(W('C05', 'wrong'), head=(4, LOOK_C, 0), spot=(0, 0.01, 0))
# J06 fast nods
t0 = W('J06', 'yeah')
for k in range(3):
    jpose(t0 + k * 0.28, head=(9, LOOK_C + 4, 0), spot=(0, 0, 0))
    jpose(t0 + k * 0.28 + 0.14, head=(-2, LOOK_C + 4, 0))
jpose(E('J06') + 0.2, head=(2, LOOK_C, 0))
jpose(W('C06', 'you'), head=(3, LOOK_C, -3))
# J07 head shake on "No", firm nod on "meant"
t0 = W('J07', 'no')
for k in range(2):
    jpose(t0 + k * 0.18, head=(1, LOOK_C - 10, 0)); jpose(t0 + k * 0.18 + 0.09, head=(1, LOOK_C + 10, 0))
jpose(W('J07', 'exactly'), head=(-5, -2, 4), chest=(-4, 0, 0))
jpose(W('J07', 'meant'), head=(8, -2, 0), chest=(0, 0, 0))
jpose(E('J07') + 0.25, head=(2, LOOK_C, 0))
jpose(W('C07', 'let'), head=(4, LOOK_C, 0))
# J08 points at Claude (right arm = screen-left), then pulls the cake in with both arms
jpose(S('J08'), head=(4, LOOK_C, 0), armR=(0, 0, 0))
jpose(W('J08', 'ai'), head=(3, LOOK_C - 4, 5), armR=(-55, 0, -25), foreR=(20, 0, 0))
jpose(W('J08', 'eat'), head=(3, LOOK_C - 2, 4), armR=(-50, 0, -22), foreR=(20, 0, 0))
jpose(W('J08', 'so'), head=(4, -2, 0), armR=(-25, 0, 0), foreR=(0, 0, 0), armL=(0, 0, 0), foreL=(0, 0, 0))
jpose(W('J08', 'eat', 1) - 0.25, head=(8, 0, 0), armR=(-40, 0, 6), armL=(-40, 0, -6), foreR=(-20, 0, 0), foreL=(-20, 0, 0), spot=(0, -0.03, 0))
jpose(E('J08') + 0.1, head=(10, 0, 3), armR=(-18, 0, 4), armL=(-18, 0, -4), foreR=(-10, 0, 0), foreL=(-10, 0, 0), spot=(0, -0.01, 0))
# C08 "Get out!" -> laughs
jpose(S('C08') + 0.1, head=(-4, LOOK_C, 0), armR=(0, 0, 0), armL=(0, 0, 0), foreR=(0, 0, 0), foreL=(0, 0, 0), spot=(0, 0.01, 0.0))
lt = LINE['JL']['start']
for k in range(6):
    jpose(lt + k * 0.17, head=(-8 - (k % 2) * 4, LOOK_C + 4, 4), chest=(-5 - (k % 2) * 3, 0, 0), spot=(0, 0, 0.012 * (k % 2)))
jpose(TL['total_s'], head=(-6, LOOK_C + 4, 4), chest=(-4, 0, 0), spot=(0, 0, 0))
ease_all(rig); ease_all(SPOT)
# subtle breathing on the chest
for fc in fcurves_of(rig):
    if fc.data_path == 'pose.bones["chest"].rotation_euler' and fc.array_index == 0:
        m = fc.modifiers.new('NOISE'); m.strength = 0.03; m.scale = 30.0; m.phase = 3.0
    if fc.data_path == 'pose.bones["head"].rotation_euler' and fc.array_index == 2:
        m = fc.modifiers.new('NOISE'); m.strength = 0.025; m.scale = 40.0; m.phase = 9.0

# ================================================================= CLAUDE
C0 = Vector((CLAUDE_XY[0], CLAUDE_XY[1], sc['claude_seat_z']))
TURN_PHONE, TURN_JAKO, TURN_CAKE = -40, 28, 48


def N(*rot):
    """native arm rotation (deg) relative to the horizontal stub rest pose."""
    return ('N',) + tuple(rot)


def arm_conv(side, rot):
    """Gestures below are authored for a HANGING arm (rest = pointing down, as in the first Claude draft).
    The voxel Claude's stub rests horizontally, so a gesture R becomes R @ Ry(+-90) (down -> gesture);
    the rest pose (0, 0, 0) stays horizontal; N(...) passes a native rotation through."""
    if rot and rot[0] == 'N':
        return rot[1:]
    if tuple(rot) == (0, 0, 0):
        return (0, 0, 0)
    R = Euler(tuple(math.radians(a) for a in rot), 'XYZ').to_matrix()
    D = Matrix.Rotation(math.radians(90 if side == 'R' else -90), 3, 'Y')
    e = (R @ D).to_euler('XYZ')
    return tuple(math.degrees(a) for a in e)


def cpose(t, turn=None, slide=None, lean=None, armL=None, armR=None, hop=None, puff=None):
    """turn: body yaw (deg); slide: (dx, dy) body offset; lean: torso (x fwd+, y tilt, z); arms: shoulder rot (deg)."""
    if turn is not None or slide is not None or hop is not None:
        cur_turn = turn if turn is not None else cpose.turn
        cur_slide = slide if slide is not None else cpose.slide
        h = hop or 0.0
        key_obj(BODY, t, loc=(cur_slide[0], cur_slide[1], h), rot=(0, 0, cur_turn))
        cpose.turn, cpose.slide = cur_turn, cur_slide
    if lean is not None:
        key_obj(TORSO, t, rot=lean)
    if armL is not None:
        key_obj(ARM['L'], t, rot=arm_conv('L', armL))
    if armR is not None:
        key_obj(ARM['R'], t, rot=arm_conv('R', armR))
    if puff is not None:
        key_obj(CMESH, t, scl=puff)


cpose.turn, cpose.slide = TURN_PHONE, (0, 0)
A0 = (0, 0, 0)


def ceyes(t, open_=1.0, happy=False):
    f = F(t)
    for p in EYEP:
        p.scale = (1.0, 1.0, open_); p.keyframe_insert('scale', frame=f)
        for ch in p.children:
            ch.hide_render = happy; ch.keyframe_insert('hide_render', frame=f)
            ch.hide_viewport = happy; ch.keyframe_insert('hide_viewport', frame=f)
    for h in EYEH:
        for ch in h.children:
            ch.hide_render = not happy; ch.keyframe_insert('hide_render', frame=f)
            ch.hide_viewport = not happy; ch.keyframe_insert('hide_viewport', frame=f)
    for h in EYEH:
        h.hide_render = False; h.hide_viewport = False


# --- intro: turned ~40 deg away (camera-left), tablet held at lap level in BOTH stubs, screen tilted up to its face;
#     eyes lowered to the screen, little chuckle bobs on "dude"
HOLD_L, HOLD_R = N(0, 0, 105), N(0, 0, -105)        # both stubs swung forward/inward, pinching the tablet's side edges
DOWN_L, DOWN_R = N(0, -35, 80), N(0, 35, -80)       # lowered with the tablet (laying it on the desk)
EYE_DOWN = -0.028                                   # eye slits shifted down = looking at the screen
cpose(0.0, turn=TURN_PHONE, slide=(0, 0), lean=(12, 0, 0), armL=HOLD_L, armR=HOLD_R, puff=1.0)
ceyes(0.0, 1.0)
cpose(2.30, lean=(12, 0, 0))
cpose(2.45, lean=(7, -3, 0)); cpose(2.58, lean=(12, 0, 0)); cpose(2.70, lean=(8, 3, 0))
# J01 "Claude." -> freeze, eyes up, tap pause (right stub jabs), turns back toward Jako/camera while laying the tablet down
cpose(2.86, lean=(9, 0, 0), armL=HOLD_L, armR=HOLD_R)
ceyes(2.86, 1.0); ceyes(2.95, 1.15)
tap = TL['phone']['tap_pause_s']
cpose(tap - 0.10, armR=HOLD_R)
cpose(tap, armR=N(0, -12, -112), lean=(12, 0, 0))                    # tap: the right stub jabs the screen
cpose(tap + 0.08, armR=HOLD_R)
PUT_DOWN = (tap + 0.10, tap + 0.38)
cpose(PUT_DOWN[0], turn=TURN_PHONE, armL=HOLD_L, armR=HOLD_R)
cpose(PUT_DOWN[1], armL=DOWN_L, armR=DOWN_R, lean=(14, 0, 0), turn=TURN_JAKO - 25)
cpose(PUT_DOWN[1] + 0.14, armL=A0, armR=A0)
cpose(S('C01') + 0.30, turn=TURN_CAKE - 10, lean=(-4, 0, 0))          # turned to the cake
for p_ in EYEP + EYEH:                                                # gaze: down at the screen, back up on "Claude."
    z0_ = p_.location.z
    for t_, dz_ in ((0.0, EYE_DOWN), (2.80, EYE_DOWN), (2.92, 0.0)):
        p_.location.z = z0_ + dz_; p_.keyframe_insert('location', index=2, frame=F(t_))
    p_.location.z = z0_
# C01 "Wait..." eyes wide + pull back; "what are those?" lean + point at the cake
ceyes(W('C01', 'wait'), 1.35)
cpose(W('C01', 'wait') + 0.12, lean=(-9, 0, 0), armR=A0)
cpose(W('C01', 'what') - 0.12, lean=(-6, 0, 0))
cpose(W('C01', 'what') + 0.12, lean=(14, 4, 0), armR=N(0, -15, -25))      # point
cpose(W('C01', 'those', end=True), lean=(15, 4, 0), armR=N(0, -18, -28))
cpose(E('C01') + 0.35, lean=(6, 0, 0), armR=N(0, 15, -10))
ceyes(E('C01') + 0.4, 1.1)
cpose(S('J02') + 0.3, turn=TURN_JAKO, lean=(2, 0, 0), armR=A0)           # listens to Jako
ceyes(S('J02') + 0.3, 1.0)
cpose(W('J02', 'with'), lean=(4, -6, 0))                                  # "with you" - head tilt
cpose(E('J02') + 0.1, lean=(2, 0, 0))
# C02 "No," stop-hand toward Jako; "not with you." shake; "Just me." puff up, arms to chest, hop
tn = W('C02', 'no')
cpose(tn - 0.22, armR=A0, lean=(2, 0, 0))
cpose(tn + 0.05, armR=N(0, -55, -40), lean=(-6, 4, 0))
cpose(tn + 0.45, armR=N(0, -50, -35), lean=(-4, 2, 0))
cpose(W('C02', 'not') - 0.05, turn=TURN_JAKO, lean=(2, 0, 0), armR=A0)
t0 = W('C02', 'not')
for k in range(3):
    cpose(t0 + 0.06 + k * 0.17, turn=TURN_JAKO + (12 if k % 2 == 0 else -12))
cpose(t0 + 0.06 + 3 * 0.17, turn=TURN_JAKO)
tj = W('C02', 'just')
cpose(tj - 0.05, puff=1.0, armL=A0, armR=A0, lean=(0, 0, 0))
cpose(tj + 0.15, puff=(1.07, 1.07, 1.09), armL=N(0, 0, 80), armR=N(0, 0, -80), lean=(-8, 0, 0))
cpose(W('C02', 'me'), armL=N(0, 0, 60), armR=N(0, 0, -60), hop=0.04)
cpose(W('C02', 'me') + 0.12, armL=N(0, 0, 82), armR=N(0, 0, -82), hop=0.0)
ceyes(W('C02', 'me'), 1.0, happy=True)
cpose(E('C02') + 0.35, puff=1.0, armL=A0, armR=A0, lean=(-3, 0, 0))
ceyes(E('C02') + 0.3, 1.0, happy=False)
# J03 "What?" -> Claude gives a smug little tilt
cpose(S('J03') + 0.1, lean=(-2, 8, 0))
# C03 "Nah," wave; "kidding, bro" nudge toward Jako; "Congrats!" arms up + big hop
tn = W('C03', 'nah')
cpose(S('C03'), lean=(0, 6, 0), armR=A0)
ceyes(S('C03'), 1.0, happy=True)
for k in range(4):
    cpose(tn - 0.15 + k * 0.13, armR=N(0, (-45 if k % 2 else -75), 0))
cpose(W('C03', 'kidding'), armR=N(0, 10, -15), lean=(10, 12, 0), slide=(0.03, 0))
ceyes(W('C03', 'kidding'), 1.0, happy=False)
cpose(W('C03', 'bro'), armR=N(0, -5, -55), lean=(14, 14, 0), slide=(0.045, 0))    # nudge
cpose(W('C03', 'bro', end=True) + 0.15, armR=N(0, 10, -10), lean=(4, 6, 0), slide=(0.03, 0))
tc = W('C03', 'congrats')
cpose(tc - 0.18, armL=(0, 0, 0), armR=(0, 0, 0), hop=0.0, lean=(6, 0, 0))
cpose(tc + 0.08, armL=N(0, 65, 0), armR=N(0, -65, 0), hop=0.07, lean=(-8, 0, 0))
cpose(tc + 0.30, armL=N(0, 75, 0), armR=N(0, -75, 0), hop=0.0)
ceyes(tc, 1.0, happy=True)
cpose(E('C03') + 0.35, armL=N(0, 25, 0), armR=N(0, -25, 0), lean=(0, 0, 0))
cpose(E('C03') + 0.7, armL=A0, armR=A0, slide=(0.0, 0))
ceyes(E('C03') + 0.6, 1.0, happy=False)
# C04 "No, no." wiggle; "I have to ask." finger up; "What's your plan?" lean + point at Jako
t0 = W('C04', 'no')
for k in range(4):
    cpose(t0 + k * 0.12, turn=TURN_JAKO + (15 if k % 2 == 0 else -15))
cpose(t0 + 4 * 0.12, turn=TURN_JAKO)
cpose(W('C04', 'i') - 0.1, armR=A0)
cpose(W('C04', 'have'), armR=N(0, -80, 0), lean=(-4, -4, 0))
cpose(W('C04', 'ask', end=True), armR=N(0, -85, 0))
cpose(W('C04', 'what') - 0.05, armR=N(0, -10, 15), lean=(8, 6, 0))
cpose(W('C04', 'plan'), armR=N(0, -15, 20), lean=(16, 10, 0), slide=(0.03, 0))
cpose(E('C04') + 0.4, armR=N(0, 15, 0), lean=(6, 4, 0))
cpose(S('J05') + 0.4, armR=A0, lean=(2, 0, 0), slide=(0.0, 0))
# C05 "Wrong answer." body shake + squint; "teach people" lean in, arms wide; "Claude" taps chest; "properly." nod
t0 = W('C05', 'wrong')
ceyes(t0, 0.4)
for k in range(4):
    cpose(t0 + 0.05 + k * 0.14, turn=TURN_JAKO + (18 if k % 2 == 0 else -18))
cpose(t0 + 0.05 + 4 * 0.14, turn=TURN_JAKO)
cpose(W('C05', 'you') - 0.1, lean=(0, 0, 0), armL=A0, armR=A0)
ceyes(W('C05', 'you') - 0.1, 1.05)
cpose(W('C05', 'teach'), lean=(15, 0, 0), armL=N(0, 25, -15), armR=N(0, -25, 15), slide=(0.02, -0.03))
cpose(W('C05', 'people', end=True), lean=(18, 0, 0), armL=N(0, 30, -20), armR=N(0, -30, 20))
cpose(W('C05', 'claude') - 0.08, armL=N(0, 0, 82), armR=N(0, 0, -82), lean=(8, 0, 0))
cpose(W('C05', 'claude') + 0.1, armL=N(0, 0, 60), armR=N(0, 0, -60))
cpose(W('C05', 'claude') + 0.25, armL=N(0, 0, 82), armR=N(0, 0, -82))
tp = W('C05', 'properly')
cpose(tp, lean=(2, 0, 0), armL=N(0, -10, 20), armR=N(0, 10, -20))
cpose(tp + 0.15, lean=(16, 0, 0))
cpose(tp + 0.35, lean=(4, 0, 0), armL=A0, armR=A0, slide=(0.0, 0))
# C06 "Mm..." squint + lean back; "you didn't mean that." arms cross, tilt
tm = W('C06', 'mmm')
cpose(S('C06') - 0.1, lean=(2, 0, 0))
ceyes(S('C06') - 0.1, 1.0)
ceyes(tm + 0.1, 0.22)
cpose(tm + 0.4, lean=(-10, -4, 0))
cpose(W('C06', 'you') - 0.1, armL=A0, armR=A0)
cpose(W('C06', 'didn'), armL=N(0, -8, 100), armR=N(0, 8, -100), lean=(-11, -8, 0))
cpose(E('C06') + 0.3, lean=(-10, -9, 0))
ceyes(E('C06') + 0.45, 0.3)
ceyes(S('J07') + 0.4, 1.0)
cpose(S('J07') + 0.5, armL=A0, armR=A0, lean=(-2, 0, 0))
# C07 "Okay, okay..." palms up + two hops; "let's just eat the cake." turn, slide, reach
for wk in (0, 1):
    to = W('C07', 'okay', wk)
    cpose(to - 0.1, armL=N(0, 20, 50), armR=N(0, -20, -50), hop=0.0, lean=(4, 0, 0))
    cpose(to + 0.08, hop=0.03, lean=(-2, 0, 0))
    cpose(to + 0.24, hop=0.0, lean=(4, 0, 0))
ceyes(W('C07', 'okay'), 1.0, happy=True)
ceyes(W('C07', 'let') - 0.2, 1.1, happy=False)
cpose(W('C07', 'let') - 0.1, turn=TURN_JAKO, armL=A0, armR=A0)
cpose(W('C07', 'eat'), turn=TURN_CAKE, slide=(0.09, 0.0), lean=(14, 0, 0), armR=N(0, 5, -40))
cpose(W('C07', 'cake', end=True), turn=TURN_CAKE, slide=(0.11, 0.0), lean=(18, 0, 0), armR=N(0, 8, -45))
# J08: freezes mid-reach, eyes widen as Jako pulls the cake away
cpose(W('J08', 'ai'), lean=(16, 0, 0), armR=N(0, 8, -45))
ceyes(W('J08', 'ai'), 1.25)
cpose(W('J08', 'so'), turn=TURN_CAKE - 10, lean=(6, 0, 0), armR=N(0, 20, -30))
ceyes(W('J08', 'eat', 1), 1.4)
cpose(E('J08'), turn=TURN_JAKO, armR=N(0, 20, -10), lean=(-2, 0, 0))
# C08 "Get out!" jumps back offended
tg = W('C08', 'get')
cpose(tg - 0.15, hop=0.0, slide=(0.11, 0.0), lean=(4, 0, 0), armL=A0, armR=N(0, 15, -5))
cpose(tg + 0.08, hop=0.085, slide=(0.02, 0.05), lean=(-20, -6, 0), armL=N(0, 60, 0), armR=N(0, -60, 0))
cpose(tg + 0.32, hop=0.0, slide=(-0.02, 0.06), lean=(-14, -4, 0))
ceyes(tg, 1.4)
# laugh (overlapping Jako's)
tl = LINE['CL']['start']
ceyes(tl, 1.0, happy=True)
for k in range(7):
    cpose(tl + k * 0.15, hop=0.022 * (k % 2), lean=(-12 + 6 * (k % 2), 6, 0), armL=N(0, -25, 35), armR=N(0, 25, -35))
cpose(TL['total_s'], hop=0.0, lean=(-6, 6, 0), armL=N(0, -20, 25), armR=N(0, 20, -25))
for o in (BODY, TORSO, CMESH) + tuple(ARM.values()):
    ease_all(o)
for p in EYEP:
    ease_all(p)

# ---- syllable mini-hops on CLAUDE_torso loc/scale from the Claude envelope (only inside Claude's lines)
envc = np.array(TL['env_claude'])
speaking = np.zeros(len(envc), bool)
for l in TL['lines']:
    if l['who'] == 'claude' and l['id'] != 'CL':
        speaking[int(l['start'] * FPS):int(l['end'] * FPS) + 1] = True
sm = np.convolve(envc, np.ones(3) / 3, 'same')
peaks, lastp = [], -99
for i in range(2, len(sm) - 2):
    if speaking[i] and sm[i] > 0.38 and sm[i] >= sm[i - 1] and sm[i] >= sm[i + 1] and i - lastp >= 6:
        peaks.append(i); lastp = i
TORSO.location = (0, 0, 0.06); TORSO.keyframe_insert('location', frame=1)
TORSO.scale = (1, 1, 1); TORSO.keyframe_insert('scale', frame=1)
for i in peaks:
    a = float(min(1.2, sm[i]))
    h = 0.006 + 0.012 * a
    for df, z, s in ((-3, 0.0, (1.03, 1.03, 0.95)), (0, h, (0.97, 0.97, 1.05)), (3, 0.0, (1.02, 1.02, 0.97))):
        f = i + 1 + df
        TORSO.location = (0, 0, 0.06 + z); TORSO.keyframe_insert('location', frame=f)
        TORSO.scale = s; TORSO.keyframe_insert('scale', frame=f)
sc['claude_hops'] = len(peaks)

# ================================================================= the tablet: held at lap level in both stubs (baked follow
# of CLAUDE_torso, every frame), screen tilted up to Claude's face so ONLY Claude sees it (camera sees the back);
# on the tap it pauses, then it is laid SCREEN-DOWN on the desk (before "Wait... what are those?")
for st_ in [o for o in O if o.name.startswith('phone_stand')]:
    O.remove(st_, do_unlink=True)
DIMS = json.loads(sc['claude_dims'])
d_loc = Vector((0.0, -DIMS['BD'] / 2 - 0.06, DIMS['ARM_Z'] - 0.06 + 0.02))   # torso space: in front of the lap
n_loc = Vector((0.0, 0.62, 0.78)).normalized()                                  # screen normal: back + up to the eyes
q_loc = n_loc.to_track_quat('-Y', 'Z')
M_loc = Matrix.Translation(d_loc) @ q_loc.to_matrix().to_4x4()
PHONE.rotation_mode = 'XYZ'
PHONE.parent = None
for f in range(1, F(PUT_DOWN[0]) + 1):
    sc.frame_set(f)
    mw = TORSO.matrix_world @ M_loc
    PHONE.matrix_world = mw
    PHONE.keyframe_insert('location', frame=f); PHONE.keyframe_insert('rotation_euler', frame=f)
e_last = PHONE.rotation_euler.copy()
flat = Euler((math.radians(90), 0, e_last.z), 'XYZ')          # laid SCREEN-DOWN on the desk
key_obj(PHONE, PUT_DOWN[1] + 0.05, loc=(-0.50, 0.12, TOP + 0.006), rot=tuple(math.degrees(a) for a in flat))
key_obj(PHONE, PUT_DOWN[1] + 0.14, loc=(-0.50, 0.12, TOP + 0.006), rot=tuple(math.degrees(a) for a in flat))
for fc in fcurves_of(PHONE):                                   # unwrap euler jumps between the baked keys
    prev = None
    for kp in fc.keyframe_points:
        if fc.data_path == 'rotation_euler' and prev is not None:
            while kp.co[1] - prev > math.pi:
                kp.co[1] -= 2 * math.pi
            while kp.co[1] - prev < -math.pi:
                kp.co[1] += 2 * math.pi
        prev = kp.co[1]
        kp.interpolation = 'LINEAR'
for fc in fcurves_of(PHONE):
    for kp in fc.keyframe_points:
        if kp.co[0] > F(PUT_DOWN[0]):
            kp.interpolation = 'BEZIER'
sc.frame_set(1)

# screen glow on Claude: soft cool-white area light on the screen, facing Claude, flickering with the clip's brightness;
# steady (dimmer) once paused, fades out fast as the tablet goes down
for o in [o for o in O if o.name.startswith('L_tablet')]:
    O.remove(o, do_unlink=True)
for d in [d for d in bpy.data.lights if d.name.startswith('L_tablet') and d.users == 0]:
    bpy.data.lights.remove(d)
gl = bpy.data.lights.new('L_tablet', 'AREA')
gl.shape = 'RECTANGLE'; gl.size = 0.32; gl.size_y = 0.18; gl.color = hexc('#CFE0FF')[:3]
for k_, v_ in (('specular_factor', 0.0), ('use_shadow', True)):
    try:
        setattr(gl, k_, v_)
    except Exception:
        pass
glo = obj('L_tablet', gl, bpy.data.collections['LIGHTS'], PHONE, loc=(0, -0.012, 0), rot=(math.radians(-90), 0, 0))
nfr = int(sc.get('phone_frames', 80))
img = bpy.data.images['phone_seq']
src_dir = os.path.dirname(bpy.path.abspath(img.filepath))
lum = []
for i in range(1, nfr + 1):
    im = bpy.data.images.load(os.path.join(src_dir, '%04d.png' % i), check_existing=False)
    px = np.array(im.pixels[:], dtype=np.float32).reshape(-1, 4)[::7]
    lum.append(float((px[:, 0] * 0.2126 + px[:, 1] * 0.7152 + px[:, 2] * 0.0722).mean()))
    bpy.data.images.remove(im)
lum = np.array(lum); lum = (lum - lum.min()) / max(1e-6, lum.max() - lum.min())
f_tap, f_off0, f_off1 = F(tap), F(PUT_DOWN[0]) + 1, F(PUT_DOWN[0]) + 4
for f in range(1, f_off0 + 1):
    li = min(f, nfr) - 1 if f < f_tap else min(f_tap, nfr) - 1
    e = (1.8 + 2.4 * lum[li]) * (0.7 if f >= f_tap else 1.0)
    gl.energy = e; gl.keyframe_insert('energy', frame=f)
gl.energy = 0.0; gl.keyframe_insert('energy', frame=f_off1)
for fc in fcurves_of(gl):
    for kp in fc.keyframe_points:
        kp.interpolation = 'LINEAR'
for ch in O['phone_pause'].children:
    clear_anim(ch)
    for f, hid in ((1, True), (F(tap), False)):
        ch.hide_render = hid; ch.keyframe_insert('hide_render', frame=f)
    set_interp(ch, 'CONSTANT')

# ================================================================= cake slides toward Jako on "So I'll eat it"
CK0 = Vector((CAKE_XY[0], CAKE_XY[1], TOP))
key_obj(CAKE, 0.0, loc=tuple(CK0))
key_obj(CAKE, W('J08', 'eat', 1) - 0.25, loc=tuple(CK0))
key_obj(CAKE, E('J08') + 0.1, loc=tuple(CK0 + Vector((0.0, 0.13, 0))))
ease_all(CAKE)

# ================================================================= cameras
CAMS = reset_coll('CAMERAS')
sc.timeline_markers.clear()
J_HEAD = Vector((0.0, JAKO_XY[1] - 0.02, 1.17))
C_HEAD = C0 + Vector((0.0, -0.02, 0.22))
CAKE_TOP = CK0 + Vector((0, 0, 0.2))
MID = (J_HEAD + C_HEAD) / 2


def V(*a):
    return Vector(a)


def cut_before(lid, pad=0.10):
    return S(lid) - pad


# (id, t0, t1, [ (pos, aim) at t0, (pos, aim) at t1 ], lens, fstop, focus point, speaker)
SH = []
SH.append(('S01', 0.0, cut_before('J02'), [(V(-0.10, -2.75, 1.30), V(-0.10, 0.55, 1.20)), (V(-0.14, -2.05, 1.26), V(-0.14, 0.55, 1.15))], 38, 2.8, MID, None))
def jcu(i, lid, t0, t1, side=-1, lens=50, d0=1.65, d1=1.35, punch=False):
    base = J_HEAD + V(0, 0, 0.06)
    dirv = V(0.22 * side, -1.0, 0.0).normalized()
    p0 = J_HEAD + dirv * d0 + V(0, 0, -0.03)
    p1 = J_HEAD + dirv * d1 + V(0, 0, -0.04)
    SH.append((i, t0, t1, [(p0, base), (p1, base + V(0, 0, -0.01))], lens, 1.2, J_HEAD, 'jako'))
def ccu(i, lid, t0, t1, lens=40, d0=1.75, d1=1.45, side=1, zoff=0.10):
    base = C_HEAD + V(0, 0, 0.03)
    dirv = V(0.42 * side, -1.0, 0.0).normalized()
    p0 = C_HEAD + dirv * d0 + V(0, 0, 0.05 + zoff)
    p1 = C_HEAD + dirv * d1 + V(0, 0, 0.04 + zoff)
    SH.append((i, t0, t1, [(p0, base), (p1, base)], lens, 1.1, C_HEAD, 'claude'))
order = ['J02', 'C02', 'J03', 'C03', 'J04', 'C04', 'J05', 'C05', 'J06', 'C06', 'J07', 'C07', 'J08']
bounds = [cut_before(l) for l in order] + [cut_before('C08')]
k = 2
for lid, t0, t1 in zip(order, bounds[:-1], bounds[1:]):
    sid = 'S%02d' % k; k += 1
    if lid == 'J02':
        jcu(sid, lid, t0, t1, side=-1, lens=45, d0=1.75, d1=1.45)
    elif lid == 'J03':
        jcu(sid, lid, t0, t1, side=-0.6, lens=55, d0=1.55, d1=1.32)              # punch-in
    elif lid in ('J04', 'J10'):
        jcu(sid, lid, t0, t1, side=0.8, lens=50)
    elif lid == 'J05':
        jcu(sid, lid, t0, t1, side=-0.5, lens=50, d0=1.6, d1=1.4)
    elif lid == 'J06':
        jcu(sid, lid, t0, t1, side=0.6, lens=50)
    elif lid == 'J07':
        jcu(sid, lid, t0, t1, side=-1, lens=55, d0=1.6, d1=1.35)
    elif lid == 'J08':          # Jako + cake medium
        SH.append((sid, t0, t1, [(V(0.18, -1.05, 1.12), V(0.0, 0.62, 0.98)), (V(0.14, -0.80, 1.10), V(0.0, 0.66, 0.99))], 40, 1.6, J_HEAD, 'jako'))
    elif lid == 'C02':
        ccu(sid, lid, t0, t1, lens=40, d0=1.75, d1=1.45)
    elif lid == 'C03':
        ccu(sid, lid, t0, t1, lens=35, d0=1.7, d1=1.45, zoff=0.12)               # room for arms-up
    elif lid == 'C04':
        ccu(sid, lid, t0, t1, lens=40, d0=1.7, d1=1.4, side=0.7)
    elif lid == 'C05':
        ccu(sid, lid, t0, t1, lens=40, d0=1.85, d1=1.3)                           # faster push
    elif lid == 'C06':
        ccu(sid, lid, t0, t1, lens=45, d0=1.55, d1=1.15, side=0.8)                # creeping in on the squint
    elif lid == 'C07':          # Claude + cake medium, trucking right toward the cake
        SH.append((sid, t0, t1, [(V(-0.55, -1.05, 1.10), V(-0.50, 0.36, 0.88)), (V(-0.38, -0.88, 1.08), V(-0.38, 0.36, 0.87))], 36, 1.6, C_HEAD, 'claude'))
SH.append(('S%02d' % k, cut_before('C08'), TL['total_s'], [(V(-0.10, -2.0, 1.26), V(-0.10, 0.55, 1.16)), (V(-0.04, -2.7, 1.34), V(-0.04, 0.55, 1.22))], 40, 2.8, MID, None))

FOC = {}
for nm, par, loc in (('FOCUS_claude', TORSO, (0, -0.12, 0.16)), ('FOCUS_mid', None, tuple(MID))):
    FOC[nm] = empty(nm, CAMS, par, loc=loc, size=0.03)
fj = empty('FOCUS_jako', CAMS, size=0.03)
fj.parent = rig; fj.parent_type = 'BONE'; fj.parent_bone = 'head'
bpy.context.view_layer.update()
hb = rig.pose.bones['head']
fj.matrix_world = Matrix.Translation(J_HEAD + V(0, -0.2, 0))
FOC['FOCUS_jako'] = fj

shots_out = []
for sid, t0, t1, keys, lens, fstop, focus, who in SH:
    cd = bpy.data.cameras.new('CAM_' + sid)
    cd.lens = lens; cd.sensor_fit = 'AUTO'; cd.clip_start = 0.05; cd.clip_end = 60
    cd.dof.use_dof = True; cd.dof.aperture_fstop = fstop
    cd.dof.focus_object = FOC['FOCUS_jako'] if who == 'jako' else (FOC['FOCUS_claude'] if who == 'claude' else FOC['FOCUS_mid'])
    cam = obj('CAM_' + sid, cd, CAMS)
    (p0, a0), (p1, a1) = keys
    f0, f1 = F(t0), F(t1)
    for f, p, a in ((f0 - 1, p0, a0), (f1 + 1, p1, a1)):
        cam.location = p; cam.rotation_euler = look_rot(p, a)
        cam.keyframe_insert('location', frame=f); cam.keyframe_insert('rotation_euler', frame=f)
    for fc in fcurves_of(cam):               # slow, eased push (never static)
        for kp in fc.keyframe_points:
            kp.interpolation = 'SINE'; kp.easing = 'EASE_IN_OUT'
    if sid in ('S01', 'S%02d' % k):           # wides: tiny handheld float
        for idx in range(3):
            add_noise(cam, 'rotation_euler', idx, 0.002, 60.0, phase=idx * 13.0)
    m = sc.timeline_markers.new(sid, frame=f0)
    m.camera = cam
    shots_out.append({'id': sid, 'start_s': round(t0, 3), 'end_s': round(t1, 3), 'start_frame': f0, 'end_frame': min(F(t1) - 1, FRAME_END),
                      'camera': cam.name, 'lens': lens, 'speaker': who})
sc.camera = O['CAM_S01']

# ================================================================= sound strip (so the .blend plays with audio)
if not sc.sequence_editor:
    sc.sequence_editor_create()
se = sc.sequence_editor
for s in list(se.sequences_all if hasattr(se, 'sequences_all') else se.strips_all):
    try:
        se.sequences.remove(s)
    except Exception:
        se.strips.remove(s)
try:
    se.sequences.new_sound('mix', MIX_WAV, 1, 1)
except Exception:
    se.strips.new_sound('mix', MIX_WAV, 1, 1)

# ================================================================= subtitle anchors (speaker head-top in pixels, per line)
RES = (1080, 1920)
subs = []
for l in TL['lines']:
    if l['id'] in ('CL', 'JL'):
        continue
    fm = F((l['start'] + l['end']) / 2)
    shot = [s for s in shots_out if s['start_frame'] <= fm <= s['end_frame'] + 1][0]
    sc.frame_set(fm)
    cam = O[shot['camera']]
    if l['who'] == 'jako':
        p = rig.matrix_world @ rig.pose.bones['head'].tail + V(0, 0, 0.12)
    else:
        p = TORSO.matrix_world @ V(0, 0, 0.30)
    co = world_to_camera_view(sc, cam, p)
    x, y = co.x * RES[0], (1 - co.y) * RES[1]
    subs.append({'id': l['id'], 'who': l['who'], 'text': l['text'], 'from': F(l['start']) - 1, 'to': F(l['end']) - 1,
                 'words': [{'w': w['w'], 'from': F(w['s']) - 1, 'to': F(w['e']) - 1} for w in l['words']],
                 'x': round(x), 'y': round(y), 'visible': bool(0 <= co.x <= 1 and 0 <= co.y <= 1 and co.z > 0), 'shot': shot['id']})
sc.frame_set(1)
sc.frame_set(F(1.2))
co = world_to_camera_view(sc, O['CAM_S01'], PHONE.matrix_world.translation + V(0, 0, 0.10))
src0 = TL['phone']['src_start_s']
pw = [w for s_ in json.load(open(os.path.join(ROOT, 'audio', 'src', 'phone_words.json'), encoding='utf-8')) for w in s_['words']]
pw = [{'w': w['w'], 'from': F(w['s'] - src0) - 1, 'to': F(w['e'] - src0) - 1} for w in pw if src0 - 0.05 <= w['s'] < src0 + tap]
sc.frame_set(1)
with open(os.path.join(ROOT, 'subs', 'subs.json'), 'w', encoding='utf-8') as f:
    json.dump({'fps': FPS, 'frames': FRAME_END, 'width': 1080, 'height': 1920,
               'phone_chip': {'from': 0, 'to': F(tap) - 1, 'x': round(co.x * 1080), 'y': round((1 - co.y) * 1920), 'words': pw},
               'lines': subs}, f, indent=1, ensure_ascii=False)
with open(os.path.join(ROOT, 'audio', 'shots.json'), 'w', encoding='utf-8') as f:
    json.dump(shots_out, f, indent=1)
print('s3_anim done: %d shots, %d claude hops' % (len(shots_out), len(peaks)))
