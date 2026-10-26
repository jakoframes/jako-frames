"""Coordinator bug list after v3: specular ellipses, Jako skin tone, tighter wide, clean Claude stub arms (native poses)."""
import io
B = r'C:\Users\acer\Downloads\jako-frames\reel-1k-cake\blender'


def edit(path, reps):
    s = io.open(path, encoding='utf-8').read()
    for x, y in reps:
        if x not in s:
            print('MISSING in', path, ':', x[:90])
        s = s.replace(x, y)
    io.open(path, 'w', encoding='utf-8', newline='\n').write(s)


# 1) the pale ellipses = mirror-like highlights of the round key/lamp lights -> lower their specular contribution
edit(B + r'\s1_set.py', [
    ("cl = point('L_candles',",
     "for _ln in ('L_key', 'L_fill', 'L_lamp_pool', 'L_lamp_bulb', 'L_laptop', 'L_window_glow'):\n"
     "    _ld = bpy.data.objects[_ln].data\n"
     "    for _k, _v in (('specular_factor', 0.12), ('diffuse_factor', 1.0)):\n"
     "        try:\n"
     "            setattr(_ld, _k, _v)\n"
     "        except Exception:\n"
     "            pass\n"
     "cl = point('L_candles',"),
])
# 3) layout: Claude and the MacBook closer to the centre so a tighter wide holds everything
edit(B + r'\common.py', [
    ("CLAUDE_XY = (-0.66, 0.36)", "CLAUDE_XY = (-0.56, 0.36)"),
    ("MAC_XY = (0.64, 0.34)", "MAC_XY = (0.50, 0.36)"),
])
# 2) Jako skin: scene-side override on the APPENDED copy of MAT_skin (jako-3d files untouched)
edit(B + r'\s2_characters.py', [
    ("for k, v in (('eyes', 0), ('mouth', 0), ('shades', 0), ('blush', 0.0)):\n    rig[k] = v",
     "for k, v in (('eyes', 0), ('mouth', 0), ('shades', 0), ('blush', 0.0)):\n    rig[k] = v\n"
     "# warm peach skin with soft shading (scene-side override; the asset in jako-3d keeps its own colour)\n"
     "skin = bpy.data.objects['JAKO_head'].data.materials[0]\n"
     "for n in skin.node_tree.nodes:\n"
     "    if n.type == 'MIX' and getattr(n, 'data_type', '') == 'RGBA':\n"
     "        n.inputs[6].default_value = hexc('#EDB994')            # A = base skin\n"
     "    if n.type == 'BSDF_PRINCIPLED':\n"
     "        setin(n, ['Subsurface Weight', 'Subsurface'], 0.3)\n"
     "        setin(n, 'Subsurface Radius', (0.9, 0.4, 0.25))\n"
     "        setin(n, 'Roughness', 0.62)\n"
     "        setin(n, ['Specular IOR Level', 'Specular'], 0.25)\n"
     "skin['scene_override'] = 'base #EDB994, sss 0.3, rough 0.62 (reel-1k-cake s2_characters.py)'"),
])
# 4) Claude arms: all gestures authored natively for the horizontal stubs (rest = straight out).
#    arm_R: Ry(-) raises, Ry(+) lowers, Rz(-) swings forward.  arm_L: Ry(+) raises, Rz(+) swings forward.
s3 = B + r'\s3_anim.py'
edit(s3, [
    ("armR=(-25, -78, 0))      # point", "armR=N(0, -15, -25))      # point"),
    ("armR=(-28, -74, 0))", "armR=N(0, -18, -28))"),
    ("cpose(E('C01') + 0.35, lean=(6, 0, 0), armR=(-10, -20, 0))", "cpose(E('C01') + 0.35, lean=(6, 0, 0), armR=N(0, 15, -10))"),
    ("armL=(-65, -30, 0), armR=(-65, 30, 0)", "armL=N(0, 0, 80), armR=N(0, 0, -80)"),
    ("armL=(-50, -25, 0), armR=(-50, 25, 0)", "armL=N(0, 0, 60), armR=N(0, 0, -60)"),
    ("armL=(-66, -30, 0), armR=(-66, 30, 0)", "armL=N(0, 0, 82), armR=N(0, 0, -82)"),
    ("armR=(-20 + (18 if k % 2 else -18), -95, 0))", "armR=N(0, (-45 if k % 2 else -75), 0))"),
    ("armR=(-10, -30, 0), lean=(10, 12, 0)", "armR=N(0, 10, -15), lean=(10, 12, 0)"),
    ("armR=(-60, -20, 0), lean=(14, 14, 0)", "armR=N(0, -5, -55), lean=(14, 14, 0)"),
    ("armR=(-15, -10, 0), lean=(4, 6, 0)", "armR=N(0, 10, -10), lean=(4, 6, 0)"),
    ("armL=(0, 145, 0), armR=(0, -145, 0)", "armL=N(0, 65, 0), armR=N(0, -65, 0)"),
    ("armL=(0, 150, 0), armR=(0, -150, 0)", "armL=N(0, 75, 0), armR=N(0, -75, 0)"),
    ("armL=(0, 60, 0), armR=(0, -60, 0), lean=(0, 0, 0)", "armL=N(0, 25, 0), armR=N(0, -25, 0), lean=(0, 0, 0)"),
    ("armR=(0, -160, 0)", "armR=N(0, -80, 0)"),
    ("armR=(0, -165, 0)", "armR=N(0, -85, 0)"),
    ("armR=(-20, -80, 0), lean=(8, 6, 0)", "armR=N(0, -10, 15), lean=(8, 6, 0)"),
    ("armR=(-30, -75, 0), lean=(16, 10, 0)", "armR=N(0, -15, 20), lean=(16, 10, 0)"),
    ("armR=(-10, -15, 0), lean=(6, 4, 0)", "armR=N(0, 15, 0), lean=(6, 4, 0)"),
    ("armL=(-20, 75, 0), armR=(-20, -75, 0)", "armL=N(0, 25, -15), armR=N(0, -25, 15)"),
    ("armL=(-25, 85, 0), armR=(-25, -85, 0)", "armL=N(0, 30, -20), armR=N(0, -30, 20)"),
    ("armL=(-62, -28, 0), armR=(-62, 28, 0)", "armL=N(0, 0, 82), armR=N(0, 0, -82)"),
    ("armL=(-48, -24, 0), armR=(-48, 24, 0)", "armL=N(0, 0, 60), armR=N(0, 0, -60)"),
    ("armL=(-20, 0, 0), armR=(-20, 0, 0)", "armL=N(0, -10, 20), armR=N(0, 10, -20)"),
    ("armL=(-70, -38, 0), armR=(-70, 38, 0)", "armL=N(0, -8, 100), armR=N(0, 8, -100)"),
    ("armL=(-40, 45, 0), armR=(-40, -45, 0)", "armL=N(0, 20, 50), armR=N(0, -20, -50)"),
    ("armR=(-55, -60, 0))", "armR=N(0, 5, -40))"),
    ("armR=(-62, -55, 0))", "armR=N(0, 8, -45))"),
    ("armR=(-60, -55, 0))", "armR=N(0, 8, -45))"),
    ("armR=(-40, -40, 0))", "armR=N(0, 20, -30))"),
    ("armR=(-20, -20, 0), lean=(-2, 0, 0)", "armR=N(0, 20, -10), lean=(-2, 0, 0)"),
    ("armL=A0, armR=(-10, -10, 0))", "armL=A0, armR=N(0, 15, -5))"),
    ("armL=(0, 125, 0), armR=(0, -125, 0)", "armL=N(0, 60, 0), armR=N(0, -60, 0)"),
    ("armL=(-40, -20, 0), armR=(-40, 20, 0)", "armL=N(0, -25, 35), armR=N(0, 25, -35)"),
    ("armL=(-30, -15, 0), armR=(-30, 15, 0)", "armL=N(0, -20, 25), armR=N(0, 20, -25)"),
    # tablet lands between Claude and the cake
    ("loc=(-0.42, 0.09, TOP + 0.006)", "loc=(-0.33, 0.08, TOP + 0.006)"),
    # 3) tighter wides: lens 40, centred a little left, eye-level slightly high -> characters fill the frame
    ("[(V(0.02, -2.75, 1.12), V(-0.02, 0.7, 1.06)), (V(-0.10, -2.05, 1.10), V(-0.12, 0.7, 1.02))], 32, 2.8, MID, None))",
     "[(V(-0.06, -2.55, 1.30), V(-0.06, 0.55, 1.20)), (V(-0.12, -2.0, 1.26), V(-0.12, 0.55, 1.15))], 40, 2.8, MID, None))"),
    ("[(V(-0.08, -1.95, 1.10), V(-0.12, 0.7, 1.02)), (V(0.02, -2.95, 1.30), V(0.0, 0.75, 1.08))], 32, 2.8, MID, None))",
     "[(V(-0.10, -2.0, 1.26), V(-0.10, 0.55, 1.16)), (V(-0.04, -2.7, 1.34), V(-0.04, 0.55, 1.22))], 40, 2.8, MID, None))"),
])
print('done')
