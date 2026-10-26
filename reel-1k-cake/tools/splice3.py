import io
B = r'C:\Users\acer\Downloads\jako-frames\reel-1k-cake\blender'


def edit(path, reps):
    s = io.open(path, encoding='utf-8').read()
    for x, y in reps:
        if x not in s:
            print('MISSING in', path, ':', x[:70])
        s = s.replace(x, y)
    io.open(path, 'w', encoding='utf-8', newline='\n').write(s)


edit(B + r'\s1_set.py', [
    ("spot('L_key', (-1.25, -1.75, 2.45), AIM, 1100,", "spot('L_key', (-1.25, -1.75, 2.45), AIM, 900,"),
    ("for i, (x, y) in enumerate(((-0.30, 0.13), (0.30, 0.66))):", "for i, (x, y) in enumerate(((-0.96, 0.16), (0.30, 0.66))):"),
    ("    gb = empty('gift_%d' % i, PROPS, loc=(x, y, z0), rot=(0, 0, math.radians(rz)), size=0.1)",
     "    gb = empty('gift_%d' % i, PROPS, loc=(x * 0.95, y * 0.55 - 0.02, z0 * 0.85), rot=(0, 0, math.radians(rz)), scale=(0.85, 0.85, 0.85), size=0.1)"),
])
edit(B + r'\common.py', [
    ("def empty(name, coll, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), size=0.2, kind='PLAIN_AXES'):\n    o = obj(name, None, coll, parent, loc, rot)",
     "def empty(name, coll, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), size=0.2, kind='PLAIN_AXES', scale=(1, 1, 1)):\n    o = obj(name, None, coll, parent, loc, rot, scale)"),
])
edit(B + r'\s3_anim.py', [
    ("TURN_PHONE, TURN_JAKO, TURN_CAKE = -38, 28, 48", "TURN_PHONE, TURN_JAKO, TURN_CAKE = 36, 28, 48"),
    ("# --- intro: holds the tablet out to its left (3/4 profile), little chuckles on \"dude\"\n"
     "HOLD_L = N(0, -8, 35)                    # left stub forward-left, pinching the tablet's edge\n"
     "DOWN_L = N(0, -40, 40)                   # left stub lowered (tablet goes down to the desk)\n"
     "cpose(0.0, turn=TURN_PHONE, slide=(0, 0), lean=(8, 0, 0), armL=HOLD_L, armR=A0, puff=1.0)",
     "# --- intro: holds the tablet out to its right, toward the centre of the desk (3/4), little chuckles on \"dude\"\n"
     "HOLD_R = N(0, -8, -35)                   # right stub forward-right, pinching the tablet's edge\n"
     "DOWN_R = N(0, 40, -40)                   # right stub lowered (tablet goes down to the desk)\n"
     "cpose(0.0, turn=TURN_PHONE, slide=(0, 0), lean=(8, 0, 0), armL=A0, armR=HOLD_R, puff=1.0)"),
    ("cpose(2.86, lean=(5, 0, 0), armL=HOLD_L)", "cpose(2.86, lean=(5, 0, 0), armR=HOLD_R)"),
    ("cpose(tap - 0.10, armL=HOLD_L)\ncpose(tap, armL=N(0, -16, 38), lean=(10, 0, 0))                       # tap: the holding stub jabs\ncpose(tap + 0.08, armL=HOLD_L)",
     "cpose(tap - 0.10, armR=HOLD_R)\ncpose(tap, armR=N(0, -16, -38), lean=(10, 0, 0))                      # tap: the holding stub jabs\ncpose(tap + 0.08, armR=HOLD_R)"),
    ("cpose(PUT_DOWN[1], armL=DOWN_L, lean=(14, -4, 0), turn=TURN_PHONE + 5)\ncpose(PUT_DOWN[1] + 0.12, armL=A0)",
     "cpose(PUT_DOWN[1], armR=DOWN_R, lean=(14, 4, 0), turn=TURN_PHONE + 4)\ncpose(PUT_DOWN[1] + 0.12, armR=A0)"),
    ("hand = O['CLAUDE_hand_L']", "hand = O['CLAUDE_hand_R']"),
    ("key_obj(PHONE, PUT_DOWN[1] + 0.05, loc=(-0.80, 0.10, TOP + 0.006), rot=tuple(math.degrees(a) for a in flat))\n"
     "key_obj(PHONE, PUT_DOWN[1] + 0.12, loc=(-0.80, 0.10, TOP + 0.006), rot=tuple(math.degrees(a) for a in flat))",
     "key_obj(PHONE, PUT_DOWN[1] + 0.05, loc=(-0.42, 0.09, TOP + 0.006), rot=tuple(math.degrees(a) for a in flat))\n"
     "key_obj(PHONE, PUT_DOWN[1] + 0.12, loc=(-0.42, 0.09, TOP + 0.006), rot=tuple(math.degrees(a) for a in flat))"),
])
print('done')
