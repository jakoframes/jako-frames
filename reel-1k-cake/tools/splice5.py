"""Low-key restyle after the user's style refs (ref/style_ref_4..7.png)."""
import io, re
B = r'C:\Users\acer\Downloads\jako-frames\reel-1k-cake\blender'
T = r'C:\Users\acer\Downloads\jako-frames\reel-1k-cake\tools'


def edit(path, reps):
    s = io.open(path, encoding='utf-8').read()
    for x, y in reps:
        if x not in s:
            print('MISSING in', path, ':', x[:80])
        s = s.replace(x, y)
    io.open(path, 'w', encoding='utf-8', newline='\n').write(s)


p1 = B + r'\s1_set.py'
s = io.open(p1, encoding='utf-8').read()
# replace the outside block
a = s.index('# outside: rainy dusk backdrop'); b = s.index('# falling rain sheet')
s = s[:a] + io.open(T + r'\sec_outside.py', encoding='utf-8').read() + s[b:]
# drop balloons, gifts, floor balloons, confetti
a = s.index('# balloons (celebration'); b = s.index("# ---------------------------------------------------------------- Claude's tablet")
s = s[:a] + s[b:]
io.open(p1, 'w', encoding='utf-8', newline='\n').write(s)

edit(p1, [
    ("WOOD_WALL = wood_mat('MAT_wood_wall', '#C9A37A', '#B08657'", "WOOD_WALL = wood_mat('MAT_wood_wall', '#4E433B', '#433932'"),
    ("WOOD_CEIL = wood_mat('MAT_wood_ceiling', '#C2996D', '#A97F52'", "WOOD_CEIL = wood_mat('MAT_wood_ceiling', '#3A322C', '#312A25'"),
    ("WOOD_DESK = wood_mat('MAT_wood_desk', '#D6A673', '#B5834F', grain='X', rough=0.32, coat=0.35)",
     "WOOD_DESK = wood_mat('MAT_wood_desk', '#5C4B40', '#4D3F35', grain='X', rough=0.45, coat=0.15)"),
    ("WOOD_FLOOR = wood_mat('MAT_wood_floor', '#A87545', '#875831'", "WOOD_FLOOR = wood_mat('MAT_wood_floor', '#3A2F28', '#2F2620'"),
    ("WOOD_FRAME = wood_mat('MAT_wood_frame', '#D9A86C', '#BA8448'", "WOOD_FRAME = wood_mat('MAT_wood_frame', '#3E3631', '#352E29'"),
    ("RUG = pbr('MAT_rug', '#CDB08E', 0.95, sheen=0.6)", "RUG = pbr('MAT_rug', '#4A423C', 0.95, sheen=0.4)"),
    ("RUG_EDGE = pbr('MAT_rug_edge', '#C9765A', 0.95, sheen=0.6)", "RUG_EDGE = pbr('MAT_rug_edge', '#3A332E', 0.95, sheen=0.4)"),
    ("BOOKCOLS = ['#E8E1D3', '#C9765A', '#3F5A7A', '#D9B36B', '#7A8F6A', '#F1EDE5', '#A4553E', '#2E3E52', '#E6C9A8', '#8B6F9E']",
     "BOOKCOLS = ['#6B645C', '#5A524B', '#4A4540', '#7A7066', '#3F3B37', '#857B70', '#544B44', '#383532']"),
    ("plant('plant_big_R', (1.55, 0.55, 0.0), 0.2, 0.36, POT_T, 11, 0.42, 1.0, 5)\n", ""),
    ("plant('plant_floor_L', (-1.75, 0.9, 0.0), 0.17, 0.42, POT_W, 9, 0.34, 1.05, 8)\n", ""),
    ("plant('plant_sill_L', (-0.95, WALL_Y - 0.08, WZ0 + 0.02), 0.08, 0.14, POT_W, 7, 0.17, 0.42, 11)\n", ""),
    ("plant('plant_shelf', (1.95, BS_Y, 2.13 + 0.02), 0.07, 0.11, POT_W, 7, 0.16, 0.35, 21)\n", ""),
    ("fac.inputs[1].default_value = 0.22; fac.inputs[2].default_value = 0.015", "fac.inputs[1].default_value = 0.10; fac.inputs[2].default_value = 0.01"),
    ("mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 0.2",
     "mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 0.07"),
    ("CR, CH = 0.19, 0.12", "CR, CH = 0.155, 0.10"),
    ("SZ = 0.135", "SZ = 0.115"),
    ("SPR = [pbr('MAT_spr_%d' % i, c, 0.4) for i, c in enumerate(['#F7C548', '#7FC8F8', '#FFFFFF', '#9B5CFF', '#2FBF66'])]",
     "SPR = [pbr('MAT_spr_%d' % i, c, 0.4) for i, c in enumerate(['#F3E2C0', '#FFFFFF', '#E8845C'])]"),
    ("for i in range(70):                       # sprinkles", "for i in range(40):                       # sprinkles"),
    ("for i, (x, y) in enumerate(((-0.96, 0.16), (0.30, 0.66))):", "for i, (x, y) in enumerate(((0.30, 0.66),)):"),
    ("obj('mug', m_cyl('mug', 0.042, 0.042, 0.095, (0, 0, 0.0475), 32), PROPS, loc=(0.36, 0.66, TOP), mats=[pbr('MAT_mug', '#3F5A7A', 0.3, coat=0.5)])",
     "obj('mug', m_cyl('mug', 0.042, 0.042, 0.095, (0, 0, 0.0475), 32), PROPS, loc=(0.36, 0.66, TOP), mats=[WHITE_CER])"),
    ("    mats=[pbr('MAT_mug', '#3F5A7A', 0.3, coat=0.5)])", "    mats=[WHITE_CER])"),
    ("obj('pencil_cup', m_cyl('pc', 0.035, 0.035, 0.1, (0, 0, 0.05), 24), PROPS, loc=(-0.9, 0.62, TOP), mats=[WHITE_CER])\nfor i in range(5):",
     "for i in range(0):"),
    ("rbox('claude_book_%d' % i, (0.40, 0.28, h), (0, 0, h / 2), 0.004, 2, PROPS, [pbr('MAT_cbook_%d' % i, c, 0.6)],",
     "rbox('claude_book_%d' % i, (0.40, 0.28, h), (0, 0, h / 2), 0.004, 2, PROPS, [pbr('MAT_cbook_%d' % i, ('#2F3540', '#8C8378')[i], 0.6)],"),
    # lights: low-key. Soft warm key on the characters, dim lamp, window backlight, nearly no ambient
    ("spot('L_key', (-1.25, -1.75, 2.45), AIM, 900, 44, 0.85, 0.55, '#FFDDB0')          # soft warm key on desk + both faces",
     "area('L_key', (-1.1, -1.35, 1.85), AIM, 170, 1.3, '#FFD9B0')                    # soft warm key on both faces (large = soft)"),
    ("spot('L_fill', (1.6, -1.9, 1.35), AIM, 380, 50, 0.9, 0.9, '#FFE6CC', shadow=False)  # gentle fill from the right",
     "area('L_fill', (1.5, -1.6, 1.25), AIM, 35, 1.8, '#E8D8D0', shadow=False)         # faint fill, keeps shadows soft"),
    ("spot('L_rim_L', (-0.35, 1.85, 2.15), (-0.66, 0.36, 0.9), 260, 22, 0.8, 0.25, '#A8C0FF')",
     "spot('L_rim_L', (-0.35, 1.85, 2.15), (-0.66, 0.36, 0.9), 140, 22, 0.8, 0.25, '#E9C2C8')"),
    ("spot('L_rim_R', (0.45, 1.85, 2.2), (0.0, 0.93, 1.2), 300, 24, 0.8, 0.25, '#A8C0FF')",
     "spot('L_rim_R', (0.45, 1.85, 2.2), (0.0, 0.93, 1.2), 160, 24, 0.8, 0.25, '#C9D2F0')"),
    ("area('L_lamp_pool', (LAMP[0], LAMP[1], LAMP[2] - 0.03), (LAMP[0] - 0.1, LAMP[1] - 0.3, 0), 260, 0.5, '#FFB870', spread=75)",
     "area('L_lamp_pool', (LAMP[0], LAMP[1], LAMP[2] - 0.03), (LAMP[0] - 0.1, LAMP[1] - 0.5, 0), 45, 0.5, '#FFB870', spread=60)"),
    ("point('L_lamp_bulb', (LAMP[0], LAMP[1], LAMP[2] + 0.06), 25, 0.08, '#FFC27F')", "point('L_lamp_bulb', (LAMP[0], LAMP[1], LAMP[2] + 0.06), 8, 0.08, '#FFC27F')"),
    ("area('L_room_spill', (0.0, -1.2, 2.8), (0.0, 1.2, 1.2), 45, 3.0, '#FFD7AE', shadow=False)   # keeps the room readable, not dark",
     "area('L_window_glow', (-0.15, WALL_Y - 0.15, 1.7), (-0.15, 0.4, 0.9), 60, 2.0, '#D8B4C0', 'RECTANGLE', 1.6, shadow=False)  # window spill on desk/backs"),
    ("glow = emit_mat('MAT_dome_glow', '#FFD9A0', 6.0)", "glow = emit_mat('MAT_dome_glow', '#FFD9A0', 2.5)"),
    ("dome = obj('lamp_dome', dome_me, PROPS, loc=LAMP, mats=[pbr('MAT_dome', '#EDE4D2', 0.55, sheen=0.2)])",
     "dome = obj('lamp_dome', dome_me, PROPS, loc=LAMP, mats=[pbr('MAT_dome', '#3A3A3E', 0.5, sheen=0.2)])"),
    ("bg.inputs['Color'].default_value = hexc('#6E5A4C'); bg.inputs['Strength'].default_value = 0.10",
     "bg.inputs['Color'].default_value = hexc('#4A4550'); bg.inputs['Strength'].default_value = 0.04"),
    ("sc.view_settings.exposure = -0.15", "sc.view_settings.exposure = 0.0"),
    ("ell = cnt.nodes.new('CompositorNodeEllipseMask'); ell.width = 0.95; ell.height = 0.78; ell.y = 0.52",
     "ell = cnt.nodes.new('CompositorNodeEllipseMask'); ell.width = 1.0; ell.height = 0.85; ell.y = 0.52"),
])
# Claude: taller slit eyes
edit(B + r'\s2_characters.py', [
    ("e = obj('CLAUDE_eye_mesh', m_box('eye', (0.027, 0.006, 0.07)), C, piv, mats=[EYE])",
     "e = obj('CLAUDE_eye_mesh', m_box('eye', (0.026, 0.006, 0.10)), C, piv, mats=[EYE])"),
    ("EZ = Z_TOP - 0.43 * (Z_TOP - Z_BOT)", "EZ = Z_TOP - 0.42 * (Z_TOP - Z_BOT)"),
])
# cameras: shallow DOF in close-ups, slightly soft wides
s3 = B + r'\s3_anim.py'
edit(s3, [
    ("    SH.append((i, t0, t1, [(p0, base), (p1, base + V(0, 0, -0.01))], lens, 2.2, J_HEAD, 'jako'))",
     "    SH.append((i, t0, t1, [(p0, base), (p1, base + V(0, 0, -0.01))], lens, 1.2, J_HEAD, 'jako'))"),
    ("    SH.append((i, t0, t1, [(p0, base), (p1, base)], lens, 2.0, C_HEAD, 'claude'))",
     "    SH.append((i, t0, t1, [(p0, base), (p1, base)], lens, 1.1, C_HEAD, 'claude'))"),
    ("V(0.0, 0.66, 0.99))], 40, 3.2, J_HEAD, 'jako'))", "V(0.0, 0.66, 0.99))], 40, 1.6, J_HEAD, 'jako'))"),
    ("V(-0.38, 0.36, 0.87))], 36, 3.2, C_HEAD, 'claude'))", "V(-0.38, 0.36, 0.87))], 36, 1.6, C_HEAD, 'claude'))"),
    ("V(-0.12, 0.7, 1.02))], 32, 5.6, MID, None))", "V(-0.12, 0.7, 1.02))], 32, 2.8, MID, None))"),
    ("V(0.0, 0.75, 1.08))], 32, 5.6, MID, None))", "V(0.0, 0.75, 1.08))], 32, 2.8, MID, None))"),
])
print('done')
