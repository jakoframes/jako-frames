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
