# ================================================================= CLAUDE
# Voxel Claude mascot (ref/claude_ref.jpg; occupancy approach from reel-agents-dolomites/blender/04_claude.py):
# wide flat coral-orange block body, two tall thin black slit eyes, rectangular stub arms out of the sides,
# four small rectangular legs. Crisp hard edges, per-voxel tone jitter. NO laptop.
C = reset_coll('CLAUDE')
rnd = random.Random(11)
SEAT_Z = sc.get('claude_seat_z', DESK_H + 0.075)
V = 0.03
NX, NY, K0, K1 = 14, 8, 3, 11            # body: 14 x 8 voxels footprint, rows k 3..10 (legs below)
BW, BD = NX * V, NY * V                   # 0.42 x 0.24 m
Z_BOT, Z_TOP = K0 * V, K1 * V             # body from 0.09 to 0.33 above the feet

m_, nt, out = new_mat('MAT_claude_voxel')
vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'
b = bsdf_node(nt, rough=0.6, spec=0.35)
mul = nt.nodes.new('ShaderNodeVectorMath'); mul.operation = 'MULTIPLY'
mul.inputs[0].default_value = hexc('#E8825F')[:3]
nt.links.new(vc.outputs['Color'], mul.inputs[1]); nt.links.new(mul.outputs[0], b.inputs['Base Color'])
nt.links.new(b.outputs[0], out.inputs[0])
m_.diffuse_color = hexc('#E8825F')
CORAL = m_
EYE = pbr('MAT_claude_eye', '#0b0b0d', 0.35, coat=0.3)

DIRS = [((1, 0, 0), [(1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)]),
        ((-1, 0, 0), [(-1, 1, -1), (-1, -1, -1), (-1, -1, 1), (-1, 1, 1)]),
        ((0, 1, 0), [(1, 1, -1), (-1, 1, -1), (-1, 1, 1), (1, 1, 1)]),
        ((0, -1, 0), [(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)]),
        ((0, 0, 1), [(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]),
        ((0, 0, -1), [(-1, 1, -1), (1, 1, -1), (1, -1, -1), (-1, -1, -1)])]


def voxel_mesh(name, occ, origin=(0, 0, 0), size=V):
    """occ: set of (i, j, k); voxel (i,j,k) centre = origin + (i+0.5, j+0.5, k+0.5)*size. Vertex colour = tone jitter."""
    verts, faces, shade = [], [], []
    ox, oy, oz = origin
    for (i, j, k) in occ:
        c = Vector((ox + (i + 0.5) * size, oy + (j + 0.5) * size, oz + (k + 0.5) * size))
        tone = 0.93 + rnd.random() * 0.1
        for d, corners in DIRS:
            if (i + d[0], j + d[1], k + d[2]) in occ:
                continue
            base = len(verts)
            for cc in corners:
                verts.append(tuple(c + Vector(cc) * (size / 2)))
            faces.append((base, base + 1, base + 2, base + 3))
            shade.append(tone * (1.0 if d[2] >= 0 else 0.88))
    me = mesh_from(name, verts, faces, smooth=False)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-6)
    bm.to_mesh(me); bm.free()
    ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
    for p in me.polygons:
        s = shade[p.index] if p.index < len(shade) else 1.0
        for li in p.loop_indices:
            ca.data[li].color = (s, s, s, 1.0)
    return me


root = empty('CLAUDE', C, loc=(CLAUDE_XY[0], CLAUDE_XY[1], SEAT_Z), size=0.25, kind='ARROWS')
body = empty('CLAUDE_body', C, root, size=0.15)                      # hop / turn pivot at the feet
torso = empty('CLAUDE_torso', C, body, loc=(0, 0, 0.06), size=0.1)   # lean + syllable squash pivot
occ_body = {(i, j, k) for i in range(NX) for j in range(NY) for k in range(K0, K1)}
bo = obj('CLAUDE_mesh', voxel_mesh('claude_body', occ_body, (-BW / 2, -BD / 2, 0)), C, torso, loc=(0, 0, -0.06), mats=[CORAL])
mod_bevel(bo, 0.0025, 1)
# four legs: 2x2 voxels, 3 tall
occ_legs = set()
for i0 in (1, NX - 3):
    for j0 in (1, NY - 3):
        for i in (i0, i0 + 1):
            for j in (j0, j0 + 1):
                for k in range(0, K0):
                    occ_legs.add((i, j, k))
lo = obj('CLAUDE_legs', voxel_mesh('claude_legs', occ_legs, (-BW / 2, -BD / 2, 0)), C, body, mats=[CORAL])
mod_bevel(lo, 0.002, 1)

# eyes: tall thin black slits on the front face (ref: centres at +-31.5 % of the width, 43 % down from the top)
EYES = []
EZ = Z_TOP - 0.43 * (Z_TOP - Z_BOT)
for sx in (-1, 1):
    x = sx * 0.315 * BW
    piv = empty('CLAUDE_eye_%s' % ('L' if sx < 0 else 'R'), C, torso, loc=(x, -BD / 2 - 0.002, EZ - 0.06), size=0.02)
    e = obj('CLAUDE_eye_mesh', m_box('eye', (0.027, 0.006, 0.07)), C, piv, mats=[EYE])
    mod_bevel(e, 0.0015, 1)
    # happy eyes: pixel chevrons "^", hidden until keyed on
    hp = empty('CLAUDE_eyehappy_%s' % ('L' if sx < 0 else 'R'), C, torso, loc=(x, -BD / 2 - 0.002, EZ - 0.06 + 0.005), size=0.02)
    for s2 in (-1, 1):
        obj('CLAUDE_eyehappy_bar', m_box('ehb', (0.032, 0.006, 0.013), (s2 * 0.013, 0, -0.006)), C, hp,
            rot=(0, math.radians(-s2 * 40), 0), mats=[EYE])
    hp.hide_render = True; hp.hide_viewport = True
    EYES.append((piv, hp))

# stub arms: rectangular, sticking straight out of the sides (rest = horizontal); pivot at the body side
ARM_Z = Z_BOT + 0.25 * (Z_TOP - Z_BOT)
for sx, nm in ((-1, 'L'), (1, 'R')):        # L = screen-left (-X); names follow the screen
    sh = empty('CLAUDE_arm_%s' % nm, C, torso, loc=(sx * BW / 2, -0.01, ARM_Z - 0.06), size=0.03)
    occ_arm = {(i, j, k) for i in range(3) for j in range(2) for k in range(2)}
    am = voxel_mesh('claude_arm_%s' % nm, occ_arm, (0 if sx > 0 else -3 * V * 0.8, -V * 0.8, -V * 0.8), size=V * 0.8)
    a = obj('CLAUDE_arm_mesh', am, C, sh, mats=[CORAL])
    mod_bevel(a, 0.002, 1)
    empty('CLAUDE_hand_%s' % nm, C, sh, loc=(sx * 3 * V * 0.8, 0, 0), size=0.02)

sc['claude_dims'] = json.dumps({'BW': BW, 'BD': BD, 'Z_TOP': Z_TOP, 'Z_BOT': Z_BOT, 'ARM_Z': ARM_Z, 'ARM_LEN': 3 * V * 0.8})
root.rotation_euler = (0, 0, 0)
print('s2_characters done')
