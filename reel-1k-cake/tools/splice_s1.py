import io, re
P = r'C:\Users\acer\Downloads\jako-frames\reel-1k-cake\blender\s1_set.py'
T = r'C:\Users\acer\Downloads\jako-frames\reel-1k-cake\tools'
s = io.open(P, encoding='utf-8').read()
desk = io.open(T + r'\sec_desk.py', encoding='utf-8').read()
lights = io.open(T + r'\sec_lights.py', encoding='utf-8').read()
a = s.index('# ---------------------------------------------------------------- desk')
b = s.index('# ---------------------------------------------------------------- lights')
s = s[:a] + desk + s[b:]
a = s.index('# ---------------------------------------------------------------- lights')
b = s.index('# world:')
s = s[:a] + lights + s[b:]
rep = [("bg.inputs['Strength'].default_value = 0.35", "bg.inputs['Strength'].default_value = 0.10"),
       ("'#DDBB92', '#C99F72', grain='Z'", "'#C9A37A', '#B08657', grain='Z'"),
       ("'#DDBB92', '#C99F72', grain='Y'", "'#C2996D', '#A97F52', grain='Y'"),
       ("WOOD_FLOOR = wood_mat('MAT_wood_floor', '#C08A52', '#9C6A3B'", "WOOD_FLOOR = wood_mat('MAT_wood_floor', '#A87545', '#875831'"),
       ("em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = 1.1\nnt.links.new(c2.outputs[2]",
        "em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = 0.8\nnt.links.new(c2.outputs[2]")]
for x, y in rep:
    if x not in s:
        print('MISSING', x[:60])
    s = s.replace(x, y)
io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('ok', len(s))
