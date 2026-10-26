# 03_jako.py - Jako, the user's "Mini Me", ported from the 2D SVG kit (minime/character.js) to chibi 3D.
# Cream jersey with maroon/navy side panels + #10 on the back, very wide dark denim, white sneakers with navy
# sole, watch on the left wrist, black hair with a two-strand ahoge, sunglasses PUSHED UP onto the head.
# Faces (separate meshes, visibility keyed in 06): FACE_neutral (sleepy), FACE_blink, FACE_surprised, FACE_happy.
# Hierarchy: JAKO (root, ground) > JAKO_hips > JAKO_torso > JAKO_head / JAKO_arm_R / JAKO_arm_L ; hips > legs.
# Front of the character = -Y in its local space. ~1.42 m tall, head+hair ~47%.
import sys, importlib
sys.path.insert(0, r'C:\Users\acer\Downloads\jako-frames\reel-agents-dolomites\blender')
import common; importlib.reload(common)
from common import *

C = reset_coll('JAKO')
K_ = 0.00307                         # metres per SVG unit (400x500 canvas)


def Zs(Y):                           # svg Y -> height above the shoe sole
    return (485.0 - Y) * K_


def Xs(X):
    return (X - 200.0) * K_


P = {  # pivots (absolute, character space)
    'hips': Vector((0, 0, Zs(388))), 'leg_R': Vector((Xs(174), 0, Zs(388))), 'leg_L': Vector((Xs(226), 0, Zs(388))),
    'head': Vector((0, 0, Zs(262))), 'arm_R': Vector((Xs(146), 0, Zs(290))), 'arm_L': Vector((Xs(254), 0, Zs(290))),
}
HEAD_C = Vector((0, 0, Zs(182)))     # face centre
HA, HB, HC_LO, HC_HI = 0.272, 0.25, 0.264, 0.33  # first-variant head shape (user's pick)
INK_OUTLINE = False                                # first variant had no outline

# ------------------------------------------------------------ materials
SKIN = pbr('MAT_jako_skin', '#f6e3d3', 0.5, sss=0.18)
HAIR = pbr('MAT_jako_hair', '#2a1a17', 0.42, sheen=0.3, coat=0.15, coat_rough=0.35)
INK = pbr('MAT_ink', '#2a1517', 0.22, coat=0.6, coat_rough=0.1)
MOUTH = pbr('MAT_mouth', '#9c3b3b', 0.4)
EYEWHITE = emit_mat('MAT_catchlight', '#ffffff', 2.0)
SHADES = pbr('MAT_shades', '#141113', 0.06, coat=1.0, coat_rough=0.03, spec=0.8)
FRAME = pbr('MAT_shades_frame', '#1c1719', 0.3)
WATCH = pbr('MAT_watch', '#c9ced6', 0.25, metal=0.9)
LCD = emit_mat('MAT_watch_lcd', '#a9ba8f', 0.6)
NAVY = pbr('MAT_navy', '#1f2c6b', 0.7, sheen=0.3)
MAROON = pbr('MAT_maroon', '#8e1f35', 0.7, sheen=0.3)
GOLD = pbr('MAT_gold', '#f0bf2e', 0.4, metal=0.3)

# blush: soft pink with radial alpha from UVs
m, nt, out = new_mat('MAT_blush')
uv = nt.nodes.new('ShaderNodeUVMap')
dist = nt.nodes.new('ShaderNodeVectorMath'); dist.operation = 'DISTANCE'
nt.links.new(uv.outputs['UV'], dist.inputs[0]); dist.inputs[1].default_value = (0.5, 0.5, 0)
al = nt.nodes.new('ShaderNodeMapRange'); al.inputs['From Min'].default_value = 0.5; al.inputs['From Max'].default_value = 0.0
al.interpolation_type = 'SMOOTHSTEP'; al.inputs['To Max'].default_value = 0.75
nt.links.new(dist.outputs['Value'], al.inputs['Value'])
b = bsdf_node(nt, hexc('#f2a39b'), 0.6)
nt.links.new(al.outputs['Result'], b.inputs['Alpha']); nt.links.new(b.outputs[0], out.inputs[0])
set_alpha_mode(m, blended=True)
BLUSH = m


def jersey_mat():
    m, nt, out = new_mat('MAT_jersey')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sep.inputs[0])
    ax = math_node(nt, 'ABSOLUTE', sep.outputs['X'])
    col = ramp(nt, ax, [(0.0, hexc('#f2ece0')), (0.118, hexc('#8e1f35')), (0.142, hexc('#1f2c6b'))], 'CONSTANT')
    b = bsdf_node(nt, rough=0.78, sheen=0.5, spec=0.35)
    nt.links.new(col, b.inputs['Base Color'])
    wv = nt.nodes.new('ShaderNodeTexNoise'); wv.inputs['Scale'].default_value = 60.0
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.08
    nt.links.new(wv.outputs['Fac'], bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    nt.links.new(b.outputs[0], out.inputs[0])
    return m


def sleeve_mat():
    m, nt, out = new_mat('MAT_sleeve')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sep.inputs[0])
    neg = math_node(nt, 'MULTIPLY', sep.outputs['Z'], -1.0)
    col = ramp(nt, neg, [(0.0, hexc('#f2ece0')), (21 * K_, hexc('#8e1f35')), (26 * K_, hexc('#1f2c6b'))], 'CONSTANT')
    b = bsdf_node(nt, rough=0.78, sheen=0.5, spec=0.35)
    nt.links.new(col, b.inputs['Base Color']); nt.links.new(b.outputs[0], out.inputs[0])
    return m


def denim_mat():
    m, nt, out = new_mat('MAT_denim')
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.45
    col = ramp(nt, lw.outputs['Facing'], [(0.0, hexc('#5a5658')), (0.55, hexc('#3a3739')), (1.0, hexc('#1f1c1e'))])
    tc = nt.nodes.new('ShaderNodeTexCoord')
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = 90.0; wv.wave_type = 'BANDS'
    try:
        wv.bands_direction = 'DIAGONAL'
    except Exception:
        pass
    nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
    b = bsdf_node(nt, rough=0.85, sheen=0.2, spec=0.3)
    f = math_node(nt, 'MULTIPLY_ADD', wv.outputs['Fac'], 0.12, 0.94)
    nt.links.new(scale_color(nt, col, f), b.inputs['Base Color'])
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.12
    nt.links.new(wv.outputs['Fac'], bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    nt.links.new(b.outputs[0], out.inputs[0])
    return m


def shoe_mat():
    m, nt, out = new_mat('MAT_sneaker')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sep.inputs[0])
    col = ramp(nt, sep.outputs['Z'], [(0.0, hexc('#1f2c6b')), (0.019, hexc('#fbfaf7'))], 'CONSTANT')
    b = bsdf_node(nt, rough=0.6, spec=0.4)
    nt.links.new(col, b.inputs['Base Color']); nt.links.new(b.outputs[0], out.inputs[0])
    return m


JERSEY, SLEEVE, DENIM, SHOE = jersey_mat(), sleeve_mat(), denim_mat(), shoe_mat()

# ------------------------------------------------------------ rig (empties)
root = empty('JAKO', C, size=0.5, kind='ARROWS')
hips = empty('JAKO_hips', C, root, loc=P['hips'], size=0.15)
torso_p = empty('JAKO_torso', C, hips, loc=(0, 0, 0), size=0.15)
head_p = empty('JAKO_head', C, torso_p, loc=P['head'] - P['hips'], size=0.2)
arm_R = empty('JAKO_arm_R', C, torso_p, loc=P['arm_R'] - P['hips'], size=0.08)
arm_L = empty('JAKO_arm_L', C, torso_p, loc=P['arm_L'] - P['hips'], size=0.08)
leg_R = empty('JAKO_leg_R', C, hips, loc=P['leg_R'] - P['hips'], size=0.08)
leg_L = empty('JAKO_leg_L', C, hips, loc=P['leg_L'] - P['hips'], size=0.08)
arm_R.rotation_euler = (0, math.radians(10), 0); arm_L.rotation_euler = (0, math.radians(-10), 0)   # slight outward splay


def part(name, me, parent, pivot_abs, mats, smooth=True):
    me.transform(Matrix.Translation(-Vector(pivot_abs)))
    return obj(name, me, C, parent, mats=mats)


# ------------------------------------------------------------ head
def head_surface(nx, ny, nz):
    c = HC_HI if nz > 0 else HC_LO
    chin = 1.0 - 0.12 * max(0.0, -nz) ** 2
    return Vector((HA * nx * chin, HB * ny, c * nz))


verts, faces = [], []
SEG, RING = 72, 36
verts.append(tuple(HEAD_C + head_surface(0, 0, -1)))
for j in range(1, RING):
    th = math.pi * j / RING
    nz = -math.cos(th); rh = math.sin(th)
    for i in range(SEG):
        az = 2 * math.pi * i / SEG
        verts.append(tuple(HEAD_C + head_surface(rh * math.sin(az), -rh * math.cos(az), nz)))
verts.append(tuple(HEAD_C + head_surface(0, 0, 1)))
top = len(verts) - 1
for i in range(SEG):
    faces.append((0, 1 + (i + 1) % SEG, 1 + i))
for j in range(RING - 2):
    for i in range(SEG):
        a = 1 + j * SEG + i; b2 = 1 + j * SEG + (i + 1) % SEG
        faces.append((a, b2, b2 + SEG, a + SEG))
base = 1 + (RING - 2) * SEG
for i in range(SEG):
    faces.append((base + i, base + (i + 1) % SEG, top))
head = part('JAKO_head_mesh', mesh_from('jako_head', verts, faces), head_p, P['head'], [SKIN])
for sx in (-1, 1):
    ear = m_sphere('ear', (0.03, 0.026, 0.042), HEAD_C + Vector((sx * (HA + 0.012), 0.012, -0.085)), 18, 12)
    part('JAKO_ear_%s' % ('R' if sx < 0 else 'L'), ear, head_p, P['head'], [SKIN])

# ------------------------------------------------------------ hair: rounded bob cap with centre-part curtains + strand lines + ahoge
def hair_off(nz):
    # rounded mushroom/bob: wider than the face at the sides, tall dome on top
    return 0.1 + 0.14 * max(0.0, nz) ** 2 + 0.085 * max(0.0, 1 - abs(nz + 0.08) * 2.2) ** 1.5


def thr(az):
    """Lower hair edge (unit-sphere nz) per azimuth. Front = centre part: an inverted V opening on the forehead,
    curtains sweeping down/out to pointed locks at eye/cheek level; sides cover the ear tops; back to the nape."""
    a = abs(math.degrees(az))
    if a <= 18:                         # narrow centre-part V: only a slim triangle of forehead shows
        e = 0.55 - 0.6 * (a / 18.0) ** 0.6
    elif a <= 50:                       # curtains hang to brow level, lock tips just touch the eyes
        e = -0.05 - 0.15 * (a - 18) / 32.0
    elif a <= 95:                       # sides cover the cheeks and the tops of the ears
        e = -0.2 - 0.12 * (a - 50) / 45.0
    else:
        e = -0.32 - 0.66 * float(ss(95, 165, a))
    if 8 < a < 56:                      # three pointed locks per side, like the sheet
        u = ((a - 8) / 16.0) % 1.0
        e -= 0.15 * (1 - abs(u * 2 - 1)) ** 2.2
    return e


def hair_point(az, nz, extra=0.0):
    nz = max(-1.0, min(1.0, nz)); rh = math.sqrt(max(0.0, 1 - nz * nz))
    p = head_surface(rh * math.sin(az), -rh * math.cos(az), nz)
    return HEAD_C + p * (1.0 + hair_off(nz) + extra)


verts, faces = [], []
NA, NR = 288, 34
verts.append(tuple(hair_point(0, 1.0)))
for j in range(1, NR + 1):
    for i in range(NA):
        az = -math.pi + 2 * math.pi * i / NA
        t = j / NR
        nz = 1.0 - (1.0 - thr(az)) * t ** 1.15
        verts.append(tuple(hair_point(az, nz)))
for i in range(NA):
    faces.append((0, 1 + i, 1 + (i + 1) % NA))
for j in range(NR - 1):
    for i in range(NA):
        a = 1 + j * NA + i; b2 = 1 + j * NA + (i + 1) % NA
        faces.append((a, a + NA, b2 + NA, b2))
cap = part('JAKO_hair_cap', mesh_from('hair_cap', verts, faces), head_p, P['head'], [HAIR])
mod_solidify(cap, 0.02, -1.0)   # dense enough without subsurf; keeps the lock points sharp

# thin light strand lines (#efe6dc at low opacity in the 2D kit): curtain curves on the front, 3 long lines on the back
STRAND = pbr('MAT_hair_strand', lerpc(hexc('#2a1a17'), hexc('#efe6dc'), 0.38), 0.5)


def strand(name, pts_deg, r=0.0028):
    pts = [hair_point(math.radians(a), nz, 0.006) for (a, nz) in pts_deg]
    part(name, m_tube(name, pts, [r * (0.4 + 0.6 * math.sin(math.pi * (k + 0.5) / len(pts))) for k in range(len(pts))], rseg=6),
         head_p, P['head'], [STRAND])


for sx in (-1, 1):
    strand('JAKO_strand_in_%d' % sx, [(sx * a, nz) for a, nz in ((2, 0.82), (6, 0.66), (11, 0.48), (16, 0.3), (21, 0.14), (25, 0.02))])
    strand('JAKO_strand_out_%d' % sx, [(sx * a, nz) for a, nz in ((8, 0.9), (14, 0.74), (21, 0.55), (29, 0.33), (37, 0.12), (44, -0.02))], 0.0024)
for a0 in (162, 180, 198):
    strand('JAKO_strand_back_%d' % a0, [(a0 + (a0 - 180) * 0.15 * k / 6, 0.88 - 1.5 * k / 6) for k in range(7)], 0.003)
# dark nape fill under the back hair (low cameras otherwise see scalp under the bob edge)
part('JAKO_hair_nape', m_sphere('nape', (0.215, 0.165, 0.11), HEAD_C + Vector((0, 0.07, -0.15)), 32, 16), head_p, P['head'], [HAIR])
crown = hair_point(0, 1.0) + Vector((0, 0.02, -0.01))
for sx, pts in ((-1, [(0, 0, 0), (-0.01, -0.005, 0.05), (-0.035, -0.008, 0.085), (-0.07, -0.004, 0.09)]),
                (1, [(0, 0, 0), (0.014, -0.004, 0.06), (0.045, -0.006, 0.1), (0.085, -0.002, 0.1)])):
    pp = [crown + Vector((sx * 0.006, 0, -0.01)) + Vector(p) for p in pts]
    part('JAKO_ahoge_%d' % sx, m_tube('ahoge', pp, [0.013, 0.011, 0.007, 0.0025], rseg=8), head_p, P['head'], [HAIR])

# ------------------------------------------------------------ sunglasses resting on top of the head
def qb(p0, p1, p2, n=8):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
            for t in [i / n for i in range(1, n + 1)]]


def cb(p0, p1, p2, p3, n=10):
    out_ = []
    for i in range(1, n + 1):
        t = i / n; u_ = 1 - t
        out_.append((u_ ** 3 * p0[0] + 3 * u_ * u_ * t * p1[0] + 3 * u_ * t * t * p2[0] + t ** 3 * p3[0],
                     u_ ** 3 * p0[1] + 3 * u_ * u_ * t * p1[1] + 3 * u_ * t * t * p2[1] + t ** 3 * p3[1]))
    return out_


sh = [(126, 197)] + qb((126, 197), (128, 189), (140, 189)) + [(188, 191)] + qb((188, 191), (200, 195), (212, 191)) + [(260, 189)] \
     + qb((260, 189), (272, 189), (274, 197)) + [(272, 212)] + qb((272, 212), (266, 226), (242, 226)) + qb((242, 226), (220, 226), (210, 211)) \
     + qb((210, 211), (200, 203), (190, 211)) + qb((190, 211), (180, 226), (158, 226)) + qb((158, 226), (134, 226), (128, 212))
sh = [p for i, p in enumerate(sh) if i == 0 or (abs(p[0] - sh[i - 1][0]) + abs(p[1] - sh[i - 1][1])) > 0.5]
bm = bmesh.new()
bv = [bm.verts.new(((x - 200) * K_ * 0.96, 0.0, -(y - 207) * K_ * 0.96)) for (x, y) in sh]
bm.faces.new(bv)
bmesh.ops.triangulate(bm, faces=bm.faces[:])
bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=2, use_grid_fill=True)
R_BEND = 0.30
for v in bm.verts:
    x = v.co.x
    v.co.x = R_BEND * math.sin(x / R_BEND)
    v.co.y = R_BEND * (1 - math.cos(x / R_BEND))
gl_me = bpy.data.meshes.new('shades'); bm.to_mesh(gl_me); bm.free()
gl_me.polygons.foreach_set('use_smooth', [True] * len(gl_me.polygons))
EL = math.radians(47)
anchor = hair_point(0, math.sin(EL), 0.005)
nrm = (Vector((0, -math.cos(EL) / HB, math.sin(EL) / HC_HI))).normalized()
shades_p = empty('JAKO_shades', C, head_p, loc=anchor + nrm * 0.03 - P['head'] + Vector((0, 0.02, 0.015)),
                 rot=(math.radians(-24), 0, 0), size=0.1)   # stood up a bit so the lens shape reads from the front
lens = obj('JAKO_shades_lens', gl_me, C, shades_p, mats=[SHADES])
mod_solidify(lens, 0.012, 0.0); mod_subsurf(lens, 1, 1)
for sx in (-1, 1):
    x0 = sx * 0.218
    a0 = Vector((R_BEND * math.sin(x0 / R_BEND), R_BEND * (1 - math.cos(x0 / R_BEND)), 0.025))
    pts = [a0, a0 + Vector((sx * 0.012, 0.06, 0.0)), a0 + Vector((sx * 0.004, 0.17, -0.03)), a0 + Vector((-sx * 0.02, 0.27, -0.09))]
    obj('JAKO_shades_arm_%d' % sx, m_tube('arm', pts, 0.006, 6), C, shades_p, mats=[FRAME])

# ------------------------------------------------------------ face decals (projected onto the head)
def poly2d(pts, rings=(0.5,)):
    cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
    n = len(pts)
    v = [(cx, cy)]
    for r in rings:
        v += [(cx + (p[0] - cx) * r, cy + (p[1] - cy) * r) for p in pts]
    v += list(pts)
    f = []
    for i in range(n):
        f.append((0, 1 + i, 1 + (i + 1) % n))
    for k in range(len(rings)):
        o0 = 1 + k * n; o1 = o0 + n
        for i in range(n):
            j = (i + 1) % n
            f.append((o0 + i, o1 + i, o1 + j, o0 + j))
    return v, f


def stroke2d(pts, w):
    v, f = [], []
    n = len(pts)
    for i, p in enumerate(pts):
        a = pts[max(0, i - 1)]; b2 = pts[min(n - 1, i + 1)]
        dx, dy = b2[0] - a[0], b2[1] - a[1]; L = math.hypot(dx, dy) or 1
        nx_, ny_ = -dy / L, dx / L
        ww = w / 2 * (0.55 + 0.45 * math.sin(math.pi * i / (n - 1))) if n > 2 else w / 2
        v.append((p[0] + nx_ * ww, p[1] + ny_ * ww)); v.append((p[0] - nx_ * ww, p[1] - ny_ * ww))
    for i in range(n - 1):
        f.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
    return v, f


def ell(cx, cy, rx, ry, n=28):
    return [(cx + rx * math.cos(2 * math.pi * i / n), cy - ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


bpy.context.view_layer.update()
DG = bpy.context.evaluated_depsgraph_get()


def project_build(name, shapes, target, pivot_abs, parent, side=-1, offset=0.0028):
    """shapes: list of (verts2d_svg, faces, material_index, uv_mode). Ray-casts onto target from the front (side=-1)
    or back (side=+1). Verts are given in SVG units, or in metres when uv_mode endswith 'm'."""
    allv, allf, mi, uvs = [], [], [], []
    for (v2, f2, mat_i, mode) in shapes:
        base_i = len(allv)
        xs_ = [p[0] for p in v2]; ys_ = [p[1] for p in v2]
        x0, x1, y0, y1 = min(xs_), max(xs_), min(ys_), max(ys_)
        for (X, Y) in v2:
            if mode.endswith('m'):
                lx, lz = X, Y
            else:
                lx, lz = Xs(X) - pivot_abs[0], Zs(Y) - pivot_abs[2]
            if side > 0:
                lx = -lx
            org = Vector((lx, side * 1.0, lz)); d = Vector((0, -side, 0))
            hit, loc, nor, idx = target.ray_cast(org, d, distance=3.0, depsgraph=DG)
            if not hit:
                loc, nor = Vector((lx, side * 0.1, lz)), Vector((0, side, 0))
            allv.append(tuple(loc + nor * offset))
            uvs.append(((X - x0) / max(1e-6, x1 - x0), (Y - y0) / max(1e-6, y1 - y0)))
        for f in f2:
            allf.append(tuple(base_i + i for i in (f if side < 0 else f[::-1])))
            mi.append(mat_i)
    me = mesh_from(name, allv, allf)
    uvl = me.uv_layers.new(name='UVMap')
    for p in me.polygons:
        p.material_index = mi[p.index]
        for li in p.loop_indices:
            uvl.data[li].uv = uvs[me.loops[li].vertex_index]
    o = obj(name, me, C, parent)
    return o


EYES = (161, 239)


def sleepy(lid=198):
    sh = []
    for x in EYES:
        pts = [(x - 11, lid), (x, lid), (x + 11, lid)] + cb((x + 11, lid), (x + 11, lid + 16), (x + 6, lid + 24), (x, lid + 24), 8) \
              + cb((x, lid + 24), (x - 6, lid + 24), (x - 11, lid + 16), (x - 11, lid), 8)[:-1]
        v, f = poly2d(pts); sh.append((v, f, 0, 'p'))
        lidp = [(x - 14, lid - 1)] + qb((x - 14, lid - 1), (x, lid - 4), (x + 14, lid - 1), 10)
        v, f = stroke2d(lidp, 4.2); sh.append((v, f, 0, 's'))
        v, f = poly2d(ell(x + 4, lid + 8, 3.0, 3.0, 12)); sh.append((v, f, 2, 'p'))
    return sh


def brows(dy=0):
    sh = []
    for (a, c_, e) in (((150, 183), (162, 180), (173, 182)), ((227, 182), (238, 180), (250, 183))):
        pts = [(a[0], a[1] + dy)] + qb((a[0], a[1] + dy), (c_[0], c_[1] + dy), (e[0], e[1] + dy), 8)
        v, f = stroke2d(pts, 4.2); sh.append((v, f, 0, 's'))
    return sh


def blush(alpha_scale=1.0):
    sh = []
    for cx in (144, 256):
        v, f = poly2d(ell(cx, 234, 20 * alpha_scale, 11 * alpha_scale, 24), rings=(0.33, 0.66)); sh.append((v, f, 3, 'p'))
    return sh


mouth_flat = [stroke2d([(194, 246), (197, 246.4), (200, 246.6), (203, 246.4), (206, 246)], 3.2) + (0, 's')]
FACE_MATS = [INK, MOUTH, EYEWHITE, BLUSH]
faces_def = {
    'neutral': sleepy() + mouth_flat + blush(0.8),
    'blink': [stroke2d([(x - 11, 211)] + qb((x - 11, 211), (x, 216), (x + 11, 211), 10), 4.6) + (0, 's') for x in EYES] + mouth_flat,
    'surprised': [poly2d(ell(x, 210, 10, 13)) + (0, 'p') for x in EYES] + [poly2d(ell(x + 3, 205, 2.8, 2.8, 12)) + (2, 'p') for x in EYES]
                 + [poly2d(ell(200, 248, 5.5, 7, 20)) + (1, 'p')],
    'happy': [stroke2d([(x - 11, 213)] + qb((x - 11, 213), (x, 197), (x + 11, 213), 12), 5.2) + (0, 's') for x in EYES]
             + [poly2d([(191, 240)] + qb((191, 240), (200, 242), (209, 240), 6) + qb((209, 240), (207, 253), (200, 253), 6)
                       + qb((200, 253), (193, 253), (191, 240), 6)[:-1]) + (1, 'p')] + blush(1.0),
}
for fname, shapes in faces_def.items():
    o = project_build('FACE_' + fname, shapes, head, P['head'], head_p)
    for mm in FACE_MATS:
        o.data.materials.append(mm)
    if fname != 'neutral':
        o.hide_render = True; o.hide_viewport = True

# ------------------------------------------------------------ neck + torso (jersey)
neck = part('JAKO_neck', m_cyl('neck', 0.046, 0.044, 0.11, (0, 0.005, 0.69), 20), torso_p, P['hips'], [SKIN])
TS = [(0.275, 0.188, 0.128), (0.295, 0.193, 0.132), (0.40, 0.188, 0.129), (0.50, 0.18, 0.124), (0.57, 0.174, 0.12),
      (0.612, 0.162, 0.112), (0.638, 0.13, 0.094), (0.652, 0.085, 0.068), (0.66, 0.05, 0.045)]
torso = part('JAKO_torso_mesh', m_loft('torso', TS, seg=40, n=3.2), torso_p, P['hips'], [JERSEY])
mod_subsurf(torso, 2, 2)
bpy.context.view_layer.update()
DG = bpy.context.evaluated_depsgraph_get()
tpiv = P['hips']
# V-neck: skin triangle + maroon collar band (front)
vskin = poly2d([(179, 276), (200, 299), (221, 276), (200, 270)])
vband = poly2d([(170, 275), (200, 307), (230, 275), (220, 275), (200, 296), (180, 275)], rings=())
band_sh = [(lambda v_f: (v_f[0], v_f[1], 0, 'p'))(poly2d([(170, 275), (180, 275), (200, 295), (220, 275), (230, 275), (200, 306)], rings=()))]
band_sh = [stroke2d([(170, 276), (185, 291), (200, 304), (215, 291), (230, 276)], 8.0) + (0, 's')]
cb_o = project_build('JAKO_collar_band', band_sh, torso, tpiv, torso_p, offset=0.004)
cb_o.data.materials.append(MAROON)
# crest (viewer-right chest)
crest = project_build('JAKO_crest', [poly2d([(216, 307), (234, 307), (234, 319)] + qb((234, 319), (234, 327), (225, 331), 4) + qb((225, 331), (216, 327), (216, 319), 4)) + (0, 'p'),
                                     poly2d(ell(225, 322, 2.8, 2.8, 10)) + (1, 'p')], torso, tpiv, torso_p, offset=0.003)
crest.data.materials.append(NAVY); crest.data.materials.append(GOLD)
# back number "10"
fpath = r'C:\Windows\Fonts\ariblk.ttf'
cu = bpy.data.curves.new('num10', 'FONT'); cu.body = '10'
if os.path.exists(fpath):
    try:
        cu.font = bpy.data.fonts.load(fpath, check_existing=True)
    except Exception:
        pass
cu.size = 0.15; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.resolution_u = 6
tmp = bpy.data.objects.new('tmp10', cu); C.objects.link(tmp)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
nme = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
bpy.data.objects.remove(tmp, do_unlink=True); bpy.data.curves.remove(cu)
bm = bmesh.new(); bm.from_mesh(nme)
bmesh.ops.triangulate(bm, faces=bm.faces[:])
bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=1, use_grid_fill=True)
bm.to_mesh(nme); bm.free()
v2 = [(v.co.x, v.co.y + Zs(352) - tpiv[2]) for v in nme.vertices]
f2 = [tuple(p.vertices) for p in nme.polygons]
bpy.data.meshes.remove(nme)
num_out = project_build('JAKO_number_outline', [([(x * 1.07, (y - (Zs(352) - tpiv[2])) * 1.07 + (Zs(352) - tpiv[2])) for (x, y) in v2], f2, 0, 'pm')],
                        torso, tpiv, torso_p, side=1, offset=0.002)
num_out.data.materials.append(MAROON)
num = project_build('JAKO_number', [(v2, f2, 0, 'pm')], torso, tpiv, torso_p, side=1, offset=0.0035)
num.data.materials.append(NAVY)

# ------------------------------------------------------------ arms (sleeve, arm, hand, watch on the left wrist)
for side, piv in (('R', arm_R), ('L', arm_L)):
    pa = P['arm_' + side]
    sl = m_loft('sleeve', [(-0.094, 0.057, 0.052), (-0.06, 0.056, 0.051), (-0.02, 0.054, 0.05), (0.01, 0.05, 0.047),
                           (0.03, 0.04, 0.038), (0.042, 0.022, 0.022)], seg=24, n=2.4)
    so = obj('JAKO_sleeve_' + side, sl, C, piv, mats=[SLEEVE]); mod_subsurf(so, 1, 2)
    obj('JAKO_forearm_' + side, m_cyl('arm', 0.03, 0.028, 0.15, (0, 0, -0.13), 16), C, piv, mats=[SKIN])
    obj('JAKO_hand_' + side, m_sphere('hand', (0.04, 0.038, 0.044), (0, 0, -0.212), 20, 12), C, piv, mats=[SKIN])
    if side == 'L':
        obj('JAKO_watch', m_cyl('watch', 0.034, 0.034, 0.032, (0, 0, -0.166), 20), C, piv, mats=[WATCH])
        obj('JAKO_watch_face', m_box('lcd', (0.03, 0.012, 0.022), (0, -0.032, -0.166)), C, piv, mats=[LCD])

# ------------------------------------------------------------ legs: very wide stacked denim + sneakers
def pant_sections():
    out_ = []
    for i, z in enumerate(np.linspace(0.045, -0.232, 14)):
        t = (0.045 - z) / 0.277
        r = 0.071 + 0.032 * t ** 1.3
        r *= 1 + 0.045 * max(0, t - 0.55) * math.sin(t * 38)
        out_.append((float(z), r, r * 0.88))
    return out_


for side, piv in (('R', leg_R), ('L', leg_L)):
    pl = obj('JAKO_pants_' + side, m_loft('pants', pant_sections(), seg=28, n=2.3), C, piv, mats=[DENIM]); mod_subsurf(pl, 1, 2)
    secs = [(0.105, 0.044, 0.05), (0.07, 0.052, 0.062), (0.0, 0.056, 0.064), (-0.06, 0.057, 0.056), (-0.11, 0.051, 0.046),
            (-0.14, 0.036, 0.036), (-0.152, 0.016, 0.022)]
    v, f = [], []
    SEGS = 24
    for (y, hw, h) in secs:
        for (x, s_) in superellipse(hw, 1.0, 2.6, SEGS):
            v.append((x, y, h / 2 + s_ * h / 2))
    ns_ = len(secs)
    for i in range(ns_ - 1):
        for j in range(SEGS):
            j2 = (j + 1) % SEGS
            f.append((i * SEGS + j, (i + 1) * SEGS + j, (i + 1) * SEGS + j2, i * SEGS + j2))
    c0 = len(v); v.append((0, secs[0][0], secs[0][2] / 2)); c1 = len(v); v.append((0, secs[-1][0], secs[-1][2] / 2))
    for j in range(SEGS):
        f.append((c0, j, (j + 1) % SEGS)); f.append((c1, (ns_ - 1) * SEGS + (j + 1) % SEGS, (ns_ - 1) * SEGS + j))
    shoe = obj('JAKO_shoe_' + side, mesh_from('shoe', v, f), C, piv, loc=(0, -0.02, -P['hips'][2]), mats=[SHOE])
    mod_subsurf(shoe, 1, 2)

# place Jako at the meadow spot, facing north (front -Y rotated 180 deg)
root.location = (JAKO_A[0], JAKO_A[1], ground_h(*JAKO_A))
root.rotation_euler = (0, 0, math.pi)

# ------------------------------------------------------------ ink outline (inverted hull), like the 2D kit's dark line
OUTLINE = bpy.data.materials.get('MAT_jako_outline') or bpy.data.materials.new('MAT_jako_outline')
OUTLINE.use_nodes = True
_nt = OUTLINE.node_tree; _nt.nodes.clear()
_em = _nt.nodes.new('ShaderNodeEmission'); _em.inputs['Color'].default_value = (*hexc('#2a1517')[:3], 1.0)
_em.inputs['Strength'].default_value = 0.15
_o = _nt.nodes.new('ShaderNodeOutputMaterial'); _nt.links.new(_em.outputs[0], _o.inputs[0])
OUTLINE.use_backface_culling = True
for ob in (list(C.all_objects) if INK_OUTLINE else []):
    skip = ('strand', 'FACE_', 'lens', 'collar', 'crest', 'number', 'watch_face', 'nape')
    if ob.type != 'MESH' or any(s in ob.name for s in skip):
        continue
    big = max(ob.dimensions) > 0.12
    ob.data.materials.append(OUTLINE)
    m = ob.modifiers.new('ink', 'SOLIDIFY')
    m.thickness = 0.008 if big else 0.004
    m.offset = 1.0
    m.use_flip_normals = True
    m.use_rim = False
    m.material_offset = len(ob.data.materials) - 1
print('03_jako done')
