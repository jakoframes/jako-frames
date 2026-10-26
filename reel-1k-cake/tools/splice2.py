import io
B = r'C:\Users\acer\Downloads\jako-frames\reel-1k-cake\blender'
T = r'C:\Users\acer\Downloads\jako-frames\reel-1k-cake\tools'


def edit(path, reps):
    s = io.open(path, encoding='utf-8').read()
    for x, y in reps:
        if x not in s:
            print('MISSING in', path, ':', x[:70])
        s = s.replace(x, y)
    io.open(path, 'w', encoding='utf-8', newline='\n').write(s)


gifts = io.open(T + r'\sec_gifts.py', encoding='utf-8').read()
edit(B + r'\s1_set.py', [
    ("# ---------------------------------------------------------------- Claude's tablet", gifts + "# ---------------------------------------------------------------- Claude's tablet"),
    ("area('L_rim_L', (-1.2, 1.95, 1.9), (-0.55, 0.45, 0.95), 110, 0.7, '#9FB8FF')        # cool window rims\n"
     "area('L_rim_R', (1.1, 1.95, 1.95), (0.1, 0.9, 1.15), 120, 0.7, '#9FB8FF')",
     "spot('L_rim_L', (-0.35, 1.85, 2.15), (-0.66, 0.36, 0.9), 260, 22, 0.8, 0.25, '#A8C0FF')     # cool window rims (narrow spots,\n"
     "spot('L_rim_R', (0.45, 1.85, 2.2), (0.0, 0.93, 1.2), 300, 24, 0.8, 0.25, '#A8C0FF')        # so the window frame stays calm)"),
    ("area('L_room_spill', (0.0, -1.2, 2.8), (0.0, 1.2, 1.2), 70, 3.0, '#FFD7AE', shadow=False)",
     "area('L_room_spill', (0.0, -1.2, 2.8), (0.0, 1.2, 1.2), 45, 3.0, '#FFD7AE', shadow=False)"),
    ("ALU = pbr('MAT_macbook_alu', '#D5D7DB', 0.3, metal=1.0, coat=0.2)", "ALU = pbr('MAT_macbook_alu', '#E4E6EA', 0.34, metal=0.65, coat=0.2)"),
    ("comp = cnt.nodes.new('CompositorNodeComposite')\ncnt.links.new(rl.outputs['Image'], gla.inputs['Image']); cnt.links.new(gla.outputs['Image'], comp.inputs['Image'])",
     "comp = cnt.nodes.new('CompositorNodeComposite')\ncnt.links.new(rl.outputs['Image'], gla.inputs['Image'])\n"
     "# soft vignette: edges -25 % so the eye stays on the desk + characters\n"
     "ell = cnt.nodes.new('CompositorNodeEllipseMask'); ell.width = 0.95; ell.height = 0.78; ell.y = 0.52\n"
     "blr = cnt.nodes.new('CompositorNodeBlur'); blr.filter_type = 'GAUSS'; blr.use_relative = True; blr.factor_x = 0.25; blr.factor_y = 0.25\n"
     "cnt.links.new(ell.outputs['Mask'], blr.inputs['Image'])\n"
     "mr = cnt.nodes.new('CompositorNodeMapRange'); mr.inputs['To Min'].default_value = 0.72; cnt.links.new(blr.outputs['Image'], mr.inputs['Value'])\n"
     "vg = cnt.nodes.new('CompositorNodeMixRGB'); vg.blend_type = 'MULTIPLY'\n"
     "cnt.links.new(mr.outputs['Value'], vg.inputs[0]); cnt.links.new(gla.outputs['Image'], vg.inputs[1]); vg.inputs[2].default_value = (0.0, 0.0, 0.0, 1)\n"
     "inv = cnt.nodes.new('CompositorNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; cnt.links.new(mr.outputs['Value'], inv.inputs[1])\n"
     "cnt.links.new(inv.outputs[0], vg.inputs[0])\n"
     "cnt.links.new(vg.outputs['Image'], comp.inputs['Image'])"),
])
edit(B + r'\s2_characters.py', [
    ("NX, NY, K0, K1 = 14, 8, 3, 11", "NX, NY, K0, K1 = 14, 5, 3, 11"),
    ("mul.inputs[0].default_value = hexc('#E8825F')[:3]", "mul.inputs[0].default_value = hexc('#E4683A')[:3]"),
    ("for j0 in (1, NY - 3):", "for j0 in (0, NY - 2):"),
])
edit(B + r'\s3_anim.py', [
    ("TURN_PHONE, TURN_JAKO, TURN_CAKE = -55, 28, 48", "TURN_PHONE, TURN_JAKO, TURN_CAKE = -38, 28, 48"),
    ("SH.append(('S01', 0.0, cut_before('J02'), [(V(0.02, -2.55, 1.30), V(0.0, 0.75, 1.02)), (V(-0.10, -1.80, 1.20), V(-0.12, 0.72, 0.98))], 28, 5.6, MID, None))",
     "SH.append(('S01', 0.0, cut_before('J02'), [(V(0.02, -2.75, 1.12), V(-0.02, 0.7, 1.06)), (V(-0.10, -2.05, 1.10), V(-0.12, 0.7, 1.02))], 32, 5.6, MID, None))"),
    ("[(V(-0.08, -1.70, 1.15), V(-0.12, 0.72, 0.98)), (V(0.02, -2.70, 1.42), V(0.0, 0.80, 1.06))], 28, 5.6, MID, None))",
     "[(V(-0.08, -1.95, 1.10), V(-0.12, 0.7, 1.02)), (V(0.02, -2.95, 1.30), V(0.0, 0.75, 1.08))], 32, 5.6, MID, None))"),
])
print('done')
