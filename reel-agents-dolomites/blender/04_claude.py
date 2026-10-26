# 04_claude.py - Claude: small voxel buddy (from the user's photo) - coral blocky body, two vertical black slit
# eyes, stub side arms, 4 little legs, two hands resting on a black voxel laptop with a pixel glyph on the lid.
# Stays voxel/blocky on purpose (contrast with the smooth world). ~0.34 m tall = about Jako's knee/thigh.
# Hierarchy: CLAUDE (root, ground) > CLAUDE_body (hop/squash pivot at the feet) > meshes. Front = -Y.
import sys, importlib
sys.path.insert(0, r'C:\Users\acer\Downloads\jako-frames\reel-agents-dolomites\blender')
import common; importlib.reload(common)
from common import *

C = reset_coll('CLAUDE')
V = 0.034
rnd = random.Random(11)

occ = {}
for i in range(0, 11):
    for j in range(0, 7):
        for k in range(2, 10):
            occ[(i, j, k)] = 'body'
for (i, k) in ((3, 7), (3, 8), (7, 7), (7, 8)):
    occ[(i, 0, k)] = 'eye'                               # vertical slit eyes on the front face
for i in (-1, -2, 11, 12):                               # stub arms
    for j in (2, 3, 4):
        for k in (5, 6):
            occ[(i, j, k)] = 'body'
for i in (1, 9):                                         # four little legs
    for j in (1, 5):
        for k in (0, 1):
            occ[(i, j, k)] = 'body'
for i in (2, 6):                                         # hands reaching forward onto the laptop
    for j in (-1, -2):
        occ[(i, j, 3)] = 'body'
    occ[(i, -3, 3)] = 'body'

DIRS = [((1, 0, 0), [(1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)]),
        ((-1, 0, 0), [(-1, 1, -1), (-1, -1, -1), (-1, -1, 1), (-1, 1, 1)]),
        ((0, 1, 0), [(1, 1, -1), (-1, 1, -1), (-1, 1, 1), (1, 1, 1)]),
        ((0, -1, 0), [(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)]),
        ((0, 0, 1), [(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]),
        ((0, 0, -1), [(-1, 1, -1), (1, 1, -1), (1, -1, -1), (-1, -1, -1)])]


def voxel_mesh(name, occ, cx=5, cy=3):
    verts, faces, kinds, shade = [], [], [], []
    for (i, j, k), kind in occ.items():
        center = Vector(((i - cx) * V, (j - cy) * V, (k + 0.5) * V))
        tone = 0.9 + rnd.random() * 0.14
        for d, corners in DIRS:
            if (i + d[0], j + d[1], k + d[2]) in occ:
                continue
            b = len(verts)
            for c in corners:
                verts.append(tuple(center + Vector(c) * (V / 2)))
            faces.append((b, b + 1, b + 2, b + 3)); kinds.append(kind)
            sh = tone * (1.0 if d[2] >= 0 else 0.9)
            shade.append(sh)
    me = mesh_from(name, verts, faces, smooth=False)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    bm.to_mesh(me); bm.free()
    ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
    for p in me.polygons:
        p.material_index = 1 if kinds[p.index] == 'eye' else 0
        s = shade[p.index]
        for li in p.loop_indices:
            ca.data[li].color = (s, s, s, 1.0)
    return me


m, nt, out = new_mat('MAT_claude_voxel')
vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'
b = bsdf_node(nt, rough=0.62, spec=0.4, sss=0.05)
mul = nt.nodes.new('ShaderNodeVectorMath'); mul.operation = 'MULTIPLY'
mul.inputs[0].default_value = hexc('#E8845C')[:3]
nt.links.new(vc.outputs['Color'], mul.inputs[1])
nt.links.new(mul.outputs[0], b.inputs['Base Color'])
nt.links.new(b.outputs[0], out.inputs[0])
CORAL = m
EYE = pbr('MAT_claude_eye', '#0b0b0d', 0.2, coat=0.6)
LAPTOP = pbr('MAT_claude_laptop', '#1b1b1f', 0.45)
LAPEDGE = pbr('MAT_claude_laptop_edge', '#3a3a42', 0.4)
GLYPH = emit_mat('MAT_claude_glyph', '#f2f2f2', 1.2)

root = empty('CLAUDE', C, size=0.3, kind='ARROWS')
body = empty('CLAUDE_body', C, root, size=0.15)
bodyo = obj('CLAUDE_voxels', voxel_mesh('claude_voxels', occ), C, body, mats=[CORAL, EYE])
bv = mod_bevel(bodyo, 0.0035, 2)

# voxel laptop (half-size voxels): base + lid hinged at the far edge, lid back faces the viewer
lap = empty('CLAUDE_laptop', C, body, loc=(-0.8 * V, -6.0 * V, 3.0 * V), size=0.05)
obj('CLAUDE_laptop_base', m_box('lb', (7 * V, 4 * V, 0.55 * V), (0, 0, 0.27 * V)), C, lap, mats=[LAPTOP])
obj('CLAUDE_laptop_keys', m_box('lk', (6 * V, 2.4 * V, 0.1 * V), (0, 0.4 * V, 0.6 * V)), C, lap, mats=[LAPEDGE])
lid = empty('CLAUDE_laptop_lid', C, lap, loc=(0, -2 * V, 0.5 * V), rot=(math.radians(14), 0, 0), size=0.04)
obj('CLAUDE_laptop_lidbox', m_box('ll', (7 * V, 0.45 * V, 3.2 * V), (0, 0, 1.6 * V)), C, lid, mats=[LAPTOP])
px = 0.42 * V
for (gx, gy) in ((-2, 2), (-1, 2), (-2, 1), (-1, 1), (1, 2), (2, 1), (3, 0)):   # little pixel glyph
    obj('CLAUDE_glyph', m_box('g', (px, 0.1 * V, px), (gx * px * 1.15 - 0.2 * V, -0.26 * V, 0.7 * V + gy * px * 1.15)), C, lid, mats=[GLYPH])

root.location = (CLAUDE_A[0], CLAUDE_A[1], ground_h(*CLAUDE_A))
root.rotation_euler = (0, 0, math.pi)
print('04_claude done')
