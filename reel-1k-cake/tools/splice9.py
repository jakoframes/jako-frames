"""v3 watching beat: Claude turned ~40 deg toward a tablet held at lap level in BOTH stubs, screen tilted up to its
face (back to camera), eyes lowered to the screen; on "Claude." it turns back as it lays the tablet screen-down."""
import io
B = r'C:\Users\acer\Downloads\jako-frames\reel-1k-cake\blender'


def splice(path, start_marker, end_marker, new):
    s = io.open(path, encoding='utf-8').read()
    a = s.index(start_marker); b = s.index(end_marker)
    s = s[:a] + new + s[b:]
    io.open(path, 'w', encoding='utf-8', newline='\n').write(s)


def edit(path, reps):
    s = io.open(path, encoding='utf-8').read()
    for x, y in reps:
        if x not in s:
            print('MISSING in', path, ':', x[:80])
        s = s.replace(x, y)
    io.open(path, 'w', encoding='utf-8', newline='\n').write(s)


P3 = B + r'\s3_anim.py'
edit(P3, [("TURN_PHONE, TURN_JAKO, TURN_CAKE = 36, 28, 48", "TURN_PHONE, TURN_JAKO, TURN_CAKE = -40, 28, 48")])

INTRO = '''# --- intro: turned ~40 deg away (camera-left), tablet held at lap level in BOTH stubs, screen tilted up to its face;
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
'''
splice(P3, "# --- intro: holds the tablet out to its right", "# C01 \"Wait...\" eyes wide", INTRO)

TABLET = '''# ================================================================= the tablet: held at lap level in both stubs (baked follow
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

'''
splice(P3, "# ================================================================= the tablet: held by Claude's left stub",
       "# screen glow on Claude:", TABLET)
edit(P3, [("gl.shape = 'RECTANGLE'; gl.size = 0.22; gl.size_y = 0.13;", "gl.shape = 'RECTANGLE'; gl.size = 0.32; gl.size_y = 0.18;")])

# bigger tablet so the stubs can hold its side edges
edit(B + r'\s1_set.py', [("TW, THh = 0.25, 0.17", "TW, THh = 0.36, 0.24")])
print('done')
