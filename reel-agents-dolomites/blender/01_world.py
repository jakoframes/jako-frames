# 01_world.py - terrain, cliff + foggy valley, Sassolungo massif, spruce forests, meadow grass/flowers,
# hay huts, cliff rocks, valley fog + aerial haze volumes, alpenglow sky world and the low sun.
# Re-runnable: rebuilds collection WORLD (and WORLD_SRC for instancing sources).
import sys, importlib
sys.path.insert(0, r'C:\Users\acer\Downloads\jako-frames\reel-agents-dolomites\blender')
import common; importlib.reload(common)
from common import *

scene = bpy.context.scene
for _n in ('Cube', 'Light', 'Camera'):          # startup-file leftovers
    if bpy.data.objects.get(_n):
        bpy.data.objects.remove(bpy.data.objects[_n], do_unlink=True)
C = reset_coll('WORLD')
SRC = reset_coll('WORLD_SRC')
rng = np.random.default_rng(20261022)


def exclude_from_layer(coll):
    def walk(lc):
        if lc.collection == coll:
            lc.exclude = True
            return True
        return any(walk(ch) for ch in lc.children)
    walk(bpy.context.view_layer.layer_collection)


# ============================================================ terrain
N = 520
u = np.linspace(-1, 1, N)
axis = 70.0 * u + 1230.0 * np.sign(u) * np.abs(u) ** 3          # dense near the campus, sparse far out
xs = axis.copy(); ys = axis.copy() + 60.0                         # shift north a bit (valley + massif side)
X, Y = np.meshgrid(xs, ys)
Z = base_h3(X, -Y)
gy, gx = np.gradient(Z, ys, xs)
nz = 1.0 / np.sqrt(gx * gx + gy * gy + 1.0)
slope = 1.0 - nz
x3, z3 = X, -Y

dark, mid, light = np.array(hex3('#3a5a20')), np.array(hex3('#5d8a2c')), np.array(hex3('#9dbb48'))
rockc, snow = np.array(hex3('#a89a86')), np.array(hex3('#eef0f2'))
f1 = ss(0.3, 0.6, fbm(x3 * 0.03, z3 * 0.03))[..., None]
f2 = (ss(0.55, 0.8, fbm(x3 * 0.07 + 5, z3 * 0.07)) * 0.22)[..., None]
col = dark + (mid - dark) * f1
col = col + (light - col) * f2
rk = np.maximum(ss(0.18, 0.4, slope) * ss(16, 40, Z), ss(0.32, 0.6, slope))[..., None]
col = col + (rockc - col) * rk
col = col + (snow - col) * (ss(70, 95, Z) * ss(0.7, 0.88, nz))[..., None]

# grass density attribute (mask x falloff around the places the cameras look at)
def in_rect(x, y, r, m=0.0):
    return (x > r[0] - m) & (x < r[1] + m) & (y > r[2] - m) & (y < r[3] + m)

NOGRASS3 = [(-8.2, 8.2, -5.7, 4.7), (-2, 2, 4.7, 5.4), (-29, -12, -9, 7), (15, 25, -16, -7), (27.4, 40.6, -14.8, -7.2),
            (22, 38, 2.5, 10), (13, 18, 4.6, 8.4), (-1.1, 1.1, 4.8, 16.5)]
grass = np.ones_like(Z)
for (a0, a1, b0, b1) in NOGRASS3:
    grass[in_rect(X, Y, (a0, a1, -b1, -b0), 0.15)] = 0.0
grass *= (np.hypot(X - FIRE[0], Y - FIRE[1]) > 2.1)
grass *= 1 - ss(0.3, 0.5, slope)
grass *= 1 - ss(56, 64, np.hypot(X, Y + 2))
FOCUS = [JAKO_A, (-2.5, -31.5), FIRE, (3.5, 36.5), (12.5, 30.5), (0, -7), (-8, 27)]
dmin = np.min(np.stack([np.hypot(X - fx, Y - fy) for fx, fy in FOCUS]), axis=0)
grass *= np.clip(1.35 - dmin / 26.0, 0.12, 1.0)

me = grid_mesh('GROUND', xs, ys, Z)
ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
rgba = np.concatenate([col.reshape(-1, 3), np.ones((col.size // 3, 1))], 1).astype(np.float32)
ca.data.foreach_set('color', rgba.ravel())
ga = me.attributes.new('grass', 'FLOAT', 'POINT')
ga.data.foreach_set('value', grass.ravel().astype(np.float32))

# ground material: vertex colours, soft noise variation, matte
m, nt, out = new_mat('MAT_ground')
vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'
tc = nt.nodes.new('ShaderNodeTexCoord')
nz1 = nt.nodes.new('ShaderNodeTexNoise'); nz1.inputs['Scale'].default_value = 0.35; nz1.inputs['Detail'].default_value = 6
nt.links.new(tc.outputs['Object'], nz1.inputs['Vector'])
fac = math_node(nt, 'MULTIPLY_ADD', nz1.outputs['Fac'], 0.5, 0.75)
b = bsdf_node(nt, rough=0.95, spec=0.3)
nt.links.new(scale_color(nt, vc.outputs['Color'], fac), b.inputs['Base Color'])
bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.25
nz2 = nt.nodes.new('ShaderNodeTexNoise'); nz2.inputs['Scale'].default_value = 3.0
nt.links.new(tc.outputs['Object'], nz2.inputs['Vector']); nt.links.new(nz2.outputs['Fac'], bump.inputs['Height'])
nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
nt.links.new(b.outputs[0], out.inputs[0])
ground = obj('GROUND', me, C, mats=[m])
print('ground verts', len(me.vertices))

# ============================================================ Sassolungo / Sassopiatto massif
NX, NY = 400, 180
lxs = np.linspace(-260, 260, NX)
ybs = np.linspace(-HZ - 115, -HZ + 115, NY)        # blender y 315..545
LX, YB = np.meshgrid(lxs, ybs)
LZ = -YB - HZ
MV = massif(LX, LZ) * MASSIF_SCALE
ZM = base_h3(LX + HX, LZ + HZ) + MV - 1.5
gy, gx = np.gradient(ZM, ybs, lxs)
nzm = 1.0 / np.sqrt(gx * gx + gy * gy + 1.0)
meadow, scree = np.array(hex3('#6f8c3a')), np.array(hex3('#a59f93'))
snowm, rockA, rockB, rockD = np.array(hex3('#f1f0ec')), np.array(hex3('#b99d82')), np.array(hex3('#d6c2a8')), np.array(hex3('#8f7d6c'))
r = rockA + (rockB - rockA) * vnoise(LX * 0.05, ZM * 0.04)[..., None]
r = r + (rockD - r) * (ss(0.6, 0.9, vnoise(LX * 0.3, ZM * 0.12)) * 0.5)[..., None]
r = r * (0.84 + 0.16 * vnoise(ZM * 0.18, LX * 0.008))[..., None]
c = meadow + (scree - meadow) * ss(2, 16, MV)[..., None]
w = np.maximum(ss(0.25, 0.45, 1 - nzm) * ss(8, 22, MV), ss(40, 60, MV) * ss(0.15, 0.4, 1 - nzm))[..., None]
c = c + (r - c) * w
c = c + (snowm - c) * (ss(0.7, 0.88, nzm) * ss(45, 65, MV))[..., None]
mm = grid_mesh('MASSIF', lxs + HX, ybs, ZM)
ca = mm.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
ca.data.foreach_set('color', np.concatenate([c.reshape(-1, 3), np.ones((c.size // 3, 1))], 1).astype(np.float32).ravel())
m, nt, out = new_mat('MAT_massif')
vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'
b = bsdf_node(nt, rough=0.9, spec=0.35)
nt.links.new(vc.outputs['Color'], b.inputs['Base Color'])
tc = nt.nodes.new('ShaderNodeTexCoord')
mus = nt.nodes.new('ShaderNodeTexNoise'); mus.inputs['Scale'].default_value = 0.08; mus.inputs['Detail'].default_value = 10
try:
    mus.noise_dimensions = '3D'
except Exception:
    pass
mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1.0, 1.0, 0.25)   # vertical streaks
nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], mus.inputs['Vector'])
bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.6; bump.inputs['Distance'].default_value = 2.0
nt.links.new(mus.outputs['Fac'], bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
nt.links.new(b.outputs[0], out.inputs[0])
obj('MASSIF', mm, C, mats=[m])

# ============================================================ instancing helper (geometry nodes)
def active_sock(socks, name):
    for s in socks:
        if s.name == name and getattr(s, 'enabled', True):
            return s
    return socks[name]


def gn_points_instancer(name, inst_obj):
    ng = bpy.data.node_groups.get(name)
    if ng:
        bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    n = ng.nodes; L = ng.links
    gi = n.new('NodeGroupInput'); go = n.new('NodeGroupOutput')
    oi = n.new('GeometryNodeObjectInfo'); oi.inputs['Object'].default_value = inst_obj
    iop = n.new('GeometryNodeInstanceOnPoints')
    nr = n.new('GeometryNodeInputNamedAttribute'); nr.data_type = 'FLOAT'; nr.inputs['Name'].default_value = 'rotz'
    ns = n.new('GeometryNodeInputNamedAttribute'); ns.data_type = 'FLOAT_VECTOR'; ns.inputs['Name'].default_value = 'scl'
    cx = n.new('ShaderNodeCombineXYZ')
    L.new(active_sock(nr.outputs, 'Attribute'), cx.inputs['Z'])
    L.new(gi.outputs[0], iop.inputs['Points']); L.new(oi.outputs['Geometry'], iop.inputs['Instance'])
    L.new(cx.outputs[0], iop.inputs['Rotation']); L.new(active_sock(ns.outputs, 'Attribute'), iop.inputs['Scale'])
    L.new(iop.outputs['Instances'], go.inputs[0])
    return ng


def points_object(name, pts, rotz, scl, coll, inst_obj):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in pts], [], [])
    a = me.attributes.new('rotz', 'FLOAT', 'POINT'); a.data.foreach_set('value', np.asarray(rotz, np.float32))
    a = me.attributes.new('scl', 'FLOAT_VECTOR', 'POINT'); a.data.foreach_set('vector', np.asarray(scl, np.float32).ravel())
    o = obj(name, me, coll)
    md = o.modifiers.new('Instancer', 'NODES'); md.node_group = gn_points_instancer('GN_' + name, inst_obj)
    return o


# ============================================================ spruce templates
def spruce_mesh(name, tiers, seg=11, jag=0.18, droop=0.05, seed=1):
    rr = random.Random(seed)
    verts, faces, hs = [], [], []
    for (z0, z1, R) in tiers:
        apex = len(verts); verts.append((0, 0, z1)); hs.append(z1)
        ring = len(verts)
        n = seg * 2
        for i in range(n):
            a = 2 * math.pi * i / n + rr.random() * 0.1
            k = 1.0 if i % 2 == 0 else 1 - jag
            rad = R * k * (0.9 + rr.random() * 0.2)
            zz = z0 - (droop * R if i % 2 == 0 else 0) + rr.uniform(-0.01, 0.01)
            verts.append((math.cos(a) * rad, math.sin(a) * rad, zz)); hs.append(zz)
        inner = len(verts)
        for i in range(n):
            a = 2 * math.pi * i / n
            verts.append((math.cos(a) * R * 0.45, math.sin(a) * R * 0.45, z0 + (z1 - z0) * 0.12)); hs.append(z0)
        for i in range(n):
            j = (i + 1) % n
            faces.append((apex, ring + i, ring + j))
            faces.append((ring + j, ring + i, inner + i, inner + j))
    # trunk
    t0 = len(verts)
    for k, z in enumerate((0.0, tiers[0][0] + 0.05)):
        rad = 0.032 if k == 0 else 0.02
        for i in range(6):
            a = 2 * math.pi * i / 6
            verts.append((math.cos(a) * rad, math.sin(a) * rad, z)); hs.append(-0.2)
    for i in range(6):
        j = (i + 1) % 6
        faces.append((t0 + i, t0 + j, t0 + 6 + j, t0 + 6 + i))
    me = mesh_from(name, verts, faces, smooth=True)
    a = me.attributes.new('h', 'FLOAT', 'POINT'); a.data.foreach_set('value', np.asarray(hs, np.float32))
    return me


m, nt, out = new_mat('MAT_spruce')
at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'h'
oi = nt.nodes.new('ShaderNodeObjectInfo')
colr = ramp(nt, at.outputs['Fac'], [(0.0, hexc('#3b2a1c')), (0.04, hexc('#13261a')), (0.5, hexc('#1d3a22')), (1.0, hexc('#365a2e'))])
b = bsdf_node(nt, rough=0.85, spec=0.3)
var = math_node(nt, 'MULTIPLY_ADD', oi.outputs['Random'], 0.35, 0.8)
nt.links.new(scale_color(nt, colr, var), b.inputs['Base Color'])
nt.links.new(b.outputs[0], out.inputs[0])
MAT_SPRUCE = m

far_tpl = obj('SRC_spruce_far', spruce_mesh('SRC_spruce_far', [(0.06, 0.54, 0.30), (0.31, 0.73, 0.24), (0.56, 0.92, 0.16), (0.79, 1.01, 0.08)], seg=7, jag=0.12), SRC, mats=[MAT_SPRUCE])
hero_tiers = []
for k in range(9):
    t = k / 8.0
    z0 = 0.08 + t * 0.78
    hero_tiers.append((z0, z0 + 0.2 - t * 0.05, 0.27 * (1 - t) ** 0.95 + 0.035))
hero_tpl = obj('SRC_spruce_hero', spruce_mesh('SRC_spruce_hero', hero_tiers, seg=13, jag=0.22, droop=0.12, seed=7), SRC, mats=[MAT_SPRUCE])

# far forests (port of jako-hq: 70 singles + clumped forests)
pts, rots, scls = [], [], []
guard = 0
while len(pts) < 3400 and guard < 300000:
    guard += 1
    single = len(pts) < 80
    a = rng.random() * math.tau
    rr_ = 34 + rng.random() * 90 if single else 110 + rng.random() ** 0.9 * 320
    x, z = math.sin(a) * rr_, math.cos(a) * rr_
    if not single and fbm(np.array(x * 0.012), np.array(z * 0.012)) < 0.5:
        continue
    if hero_mask(x, z) > 0.35 or pad_mask(np.array(x), np.array(z)) > 0:
        continue
    yb = -z
    if z < 0 and rr_ < 160 and abs(math.atan2(x, -z)) < 0.4 and yb < cliff_edge(x):
        continue                                   # keep the mountain view open from the meadow
    if abs(yb - float(cliff_edge(x))) < 22:        # nothing on the cliff face
        continue
    h = ground_h(x, yb)
    if h > 34 or abs(ground_h(x + 3, yb) - h) > 2.2:
        continue
    if yb < 45 and math.hypot(x, yb) < 45:         # keep the campus meadow clear (hero pines do that job)
        continue
    th = 9 + rng.random() * 7
    w_ = th * (0.85 + rng.random() * 0.3)
    pts.append((x, yb, h - 0.2)); rots.append(rng.random() * math.tau); scls.append((w_, w_, th))
points_object('PINES_far', pts, rots, scls, C, far_tpl)
print('far spruces', len(pts))

# hero pines framing the shots (positions chosen to stay out of the camera lines)
HERO = [(-8.6, -33.4, 8.5), (-10.8, -30.2, 10.5), (-13.2, -35.8, 12.0), (-4.4, -39.5, 9.0), (6.8, -38.0, 11.0),
        (9.8, -33.5, 8.0), (12.5, -37.2, 12.5), (-17.0, -26.0, 10.0), (14.5, -26.5, 9.5), (-21.0, -40.0, 13.0),
        (-18.0, 29.0, 11.0), (-21.5, 33.5, 13.0), (-15.0, 36.6, 9.0), (19.0, 33.0, 10.5), (23.0, 27.5, 12.0),
        (17.5, 37.5, 8.5), (-26.0, 24.0, 12.0), (28.0, 21.0, 11.5), (-30.0, -18.0, 13.0), (33.0, -22.0, 12.5),
        (-24.0, 14.0, 10.0), (36.0, 16.0, 11.0), (-36.0, 5.0, 13.5), (45.0, -4.0, 12.0)]
pts, rots, scls = [], [], []
for (x, y, th) in HERO:
    pts.append((x, y, ground_h(x, y) - 0.1)); rots.append(rng.random() * math.tau)
    w_ = th * (0.9 + rng.random() * 0.2); scls.append((w_, w_, th))
points_object('PINES_hero', pts, rots, scls, C, hero_tpl)

# ============================================================ hay huts
wall = pbr('MAT_hut_wall', '#6e4b31', 0.9)
roofm = pbr('MAT_hut_roof', '#3b2a20', 0.85)
for i, (x3_, z3_) in enumerate([(-38, -60), (-75, -110), (55, -95), (95, -150), (-130, -40), (140, -60), (-20, -175), (30, 70)]):
    x, y = x3_, -z3_
    gz = ground_h(x, y) - 0.3
    piv = empty('HUT_%d' % i, C, loc=(x, y, gz), rot=(0, 0, i * 0.9))
    obj('HUT_%d_body' % i, m_box('hutb', (5, 4, 3.2), (0, 0, 1.6)), C, piv, mats=[wall])
    rv = [(-2.9, -2.3, 3.0), (2.9, -2.3, 3.0), (2.9, 0, 4.9), (-2.9, 0, 4.9), (-2.9, 2.3, 3.0), (2.9, 2.3, 3.0)]
    obj('HUT_%d_roof' % i, mesh_from('hutr', rv, [(0, 1, 2, 3), (3, 2, 5, 4), (0, 3, 4), (1, 5, 2)], smooth=False), C, piv, mats=[roofm])

# ============================================================ rocks along the cliff lip
rockmat = pbr('MAT_rock', '#a59f93', 0.85)
for i, x in enumerate(np.arange(-70, 70, 4.5)):
    x = float(x + rng.uniform(-1.5, 1.5))
    if abs(x - FIRE[0]) < 3.5:
        continue
    y = float(cliff_edge(x)) + rng.uniform(0.5, 3.5)
    rad = rng.uniform(0.5, 1.6)
    obj('ROCK_%02d' % i, m_rock('rock', rad, (0, 0, 0), seed=i, squash=0.6), C,
        loc=(x, y, ground_h(x, y) - rad * 0.2), rot=(0, 0, rng.random() * 6.28), mats=[rockmat])

# ============================================================ meadow: grass clumps + flowers (GN on the ground)
GRS = ensure_coll('WORLD_SRC_grass', SRC)


def clump_mesh(name, nbl, hmin, hmax, seed):
    rr = random.Random(seed)
    verts, faces, hs = [], [], []
    for k in range(nbl):
        a = rr.random() * math.tau; rad = rr.random() * 0.05
        bx, by = math.cos(a) * rad, math.sin(a) * rad
        h = rr.uniform(hmin, hmax); w = rr.uniform(0.008, 0.014)
        lean = rr.uniform(0.15, 0.55); la = rr.random() * math.tau
        face_a = rr.random() * math.tau
        sx, sy = math.cos(face_a) * w, math.sin(face_a) * w
        base = len(verts)
        segs = 4
        for s in range(segs + 1):
            t = s / segs
            off = lean * h * t * t
            cx = bx + math.cos(la) * off; cy = by + math.sin(la) * off; cz = h * t * (1 - 0.15 * t * lean)
            ww = 1 - t * 0.92
            verts.append((cx - sx * ww, cy - sy * ww, cz)); hs.append(t)
            verts.append((cx + sx * ww, cy + sy * ww, cz)); hs.append(t)
        for s in range(segs):
            i0 = base + s * 2
            faces.append((i0, i0 + 1, i0 + 3, i0 + 2))
    me = mesh_from(name, verts, faces)
    a = me.attributes.new('h', 'FLOAT', 'POINT'); a.data.foreach_set('value', np.asarray(hs, np.float32))
    return me


m, nt, out = new_mat('MAT_grass')
at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'h'
geo = nt.nodes.new('ShaderNodeNewGeometry')
pn = nt.nodes.new('ShaderNodeTexNoise'); pn.inputs['Scale'].default_value = 0.12
nt.links.new(geo.outputs['Position'], pn.inputs['Vector'])
tip = mix_rgb(nt, pn.outputs['Fac'], hexc('#5f8a24'), hexc('#a3a83a'))
basec = hexc('#16260a')
colg = mix_rgb(nt, at.outputs['Fac'], basec, tip)
oi = nt.nodes.new('ShaderNodeObjectInfo')
var = math_node(nt, 'MULTIPLY_ADD', oi.outputs['Random'], 0.4, 0.8)
colg = scale_color(nt, colg, var)
b = bsdf_node(nt, rough=0.7, spec=0.35)
nt.links.new(colg, b.inputs['Base Color'])
tr = nt.nodes.new('ShaderNodeBsdfTranslucent')
nt.links.new(colg, tr.inputs['Color'])
ms = nt.nodes.new('ShaderNodeMixShader'); ms.inputs[0].default_value = 0.3
nt.links.new(b.outputs[0], ms.inputs[1]); nt.links.new(tr.outputs[0], ms.inputs[2])
nt.links.new(ms.outputs[0], out.inputs[0])
MAT_GRASS = m
for k in range(3):
    obj('SRC_clump_%d' % k, clump_mesh('clump%d' % k, 9, 0.07, 0.17, 30 + k), GRS, mats=[MAT_GRASS])

FLW = ensure_coll('WORLD_SRC_flowers', SRC)
stem = pbr('MAT_stem', '#3c5a1c', 0.8)
for k, (hexcol, shape) in enumerate([('#ffcf1a', 'ball'), ('#8a3a8c', 'cone'), ('#f6f3ea', 'ball'), ('#ffcf1a', 'ball')]):
    fm = pbr('MAT_flower_%d' % k, hexcol, 0.55, sss=0.2)
    h = 0.13 + 0.03 * k
    piv = obj('SRC_flower_%d' % k, m_cyl('stem', 0.004, 0.003, h, (0, 0, h / 2), seg=5), FLW, mats=[stem])
    head = m_sphere('fh', (0.03, 0.03, 0.018), (0, 0, h), 10, 6) if shape == 'ball' else m_cyl('fc', 0.022, 0.0, 0.07, (0, 0, h + 0.02), 8)
    hm = head.materials; hm.append(fm)
    # merge head into the same mesh
    bm = bmesh.new(); bm.from_mesh(piv.data); bm.from_mesh(head)
    bm.to_mesh(piv.data); bm.free()
    piv.data.materials.append(fm)
    for p in piv.data.polygons:
        p.material_index = 1 if p.center.z > h - 0.025 else 0
exclude_from_layer(SRC)


GRASS_DENS = 14.0     # clumps per m2 at full mask (~60k clumps in the 60 m meadow)


def gn_meadow():
    name = 'GN_meadow'
    ng = bpy.data.node_groups.get(name)
    if ng:
        bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    n = ng.nodes; L = ng.links
    gi = n.new('NodeGroupInput'); go = n.new('NodeGroupOutput')
    join = n.new('GeometryNodeJoinGeometry')
    L.new(gi.outputs[0], join.inputs[0])
    na = n.new('GeometryNodeInputNamedAttribute'); na.data_type = 'FLOAT'; na.inputs['Name'].default_value = 'grass'
    vp = n.new('GeometryNodeIsViewport')
    vpf = n.new('ShaderNodeMath'); vpf.operation = 'MULTIPLY_ADD'
    L.new(vp.outputs[0], vpf.inputs[0]); vpf.inputs[1].default_value = -0.9; vpf.inputs[2].default_value = 1.0
    for (coll, dens, seed, smin, smax) in ((GRS, GRASS_DENS, 3, 0.8, 1.5), (FLW, 1.6, 9, 0.8, 1.3)):
        mul = n.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
        L.new(active_sock(na.outputs, 'Attribute'), mul.inputs[0]); mul.inputs[1].default_value = dens
        mul2 = n.new('ShaderNodeMath'); mul2.operation = 'MULTIPLY'
        L.new(mul.outputs[0], mul2.inputs[0]); L.new(vpf.outputs[0], mul2.inputs[1])
        dp = n.new('GeometryNodeDistributePointsOnFaces'); dp.distribute_method = 'RANDOM'
        L.new(gi.outputs[0], dp.inputs['Mesh']); L.new(mul2.outputs[0], active_sock(dp.inputs, 'Density'))
        active_sock(dp.inputs, 'Seed').default_value = seed
        ci = n.new('GeometryNodeCollectionInfo'); ci.inputs['Collection'].default_value = coll
        ci.inputs['Separate Children'].default_value = True; ci.inputs['Reset Children'].default_value = True
        iop = n.new('GeometryNodeInstanceOnPoints')
        L.new(dp.outputs['Points'], iop.inputs['Points']); L.new(ci.outputs[0], iop.inputs['Instance'])
        iop.inputs['Pick Instance'].default_value = True
        rv = n.new('FunctionNodeRandomValue'); rv.data_type = 'FLOAT'
        active_sock(rv.inputs, 'Min').default_value = 0.0; active_sock(rv.inputs, 'Max').default_value = 6.283
        active_sock(rv.inputs, 'Seed').default_value = seed + 1
        cx = n.new('ShaderNodeCombineXYZ'); L.new(active_sock(rv.outputs, 'Value'), cx.inputs['Z'])
        L.new(cx.outputs[0], iop.inputs['Rotation'])
        rs = n.new('FunctionNodeRandomValue'); rs.data_type = 'FLOAT'
        active_sock(rs.inputs, 'Min').default_value = smin; active_sock(rs.inputs, 'Max').default_value = smax
        active_sock(rs.inputs, 'Seed').default_value = seed + 2
        L.new(active_sock(rs.outputs, 'Value'), iop.inputs['Scale'])
        L.new(iop.outputs['Instances'], join.inputs[0])
    L.new(join.outputs[0], go.inputs[0])
    return ng


md = ground.modifiers.new('Meadow', 'NODES'); md.node_group = gn_meadow()
# rough instance estimate (area-weighted grass attribute)
cell = np.outer(np.gradient(ys), np.gradient(xs))
print('approx grass clumps', int((grass * cell).sum() * GRASS_DENS))

# ============================================================ fog + haze volumes
def volume_box(name, x0, x1, y0, y1, z0, z1, mat):
    me = m_box(name, (x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    o = obj(name, me, C, mats=[mat])
    return o


m, nt, out = new_mat('MAT_valley_fog')
tc = nt.nodes.new('ShaderNodeTexCoord')
sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sep.inputs[0])
hgr = math_node(nt, 'POWER', math_node(nt, 'SUBTRACT', 1.0, sep.outputs['Z'], clamp=True), 2.2)
fn = nt.nodes.new('ShaderNodeTexNoise'); fn.inputs['Scale'].default_value = 0.012; fn.inputs['Detail'].default_value = 4
nt.links.new(tc.outputs['Object'], fn.inputs['Vector'])
nm = math_node(nt, 'MULTIPLY_ADD', fn.outputs['Fac'], 2.2, -0.45, clamp=False)
nm = math_node(nt, 'MAXIMUM', nm, 0.05)
dens = math_node(nt, 'MULTIPLY', math_node(nt, 'MULTIPLY', hgr, nm), 0.25)
pv = nt.nodes.new('ShaderNodeVolumePrincipled')
pv.inputs['Color'].default_value = hexc('#ffd6c8')
pv.inputs['Anisotropy'].default_value = 0.35
nt.links.new(dens, pv.inputs['Density'])
# EEVEE leaves the valley volume in the cliff's shadow -> soft self-glow proportional to density
nt.links.new(math_node(nt, 'MULTIPLY', dens, 4.5), pv.inputs['Emission Strength'])
pv.inputs['Emission Color'].default_value = hexc('#d9a7b8')
nt.links.new(pv.outputs[0], out.inputs['Volume'])
volume_box('FOG_valley', -520, 520, 50, 340, -52, -10, m)

m, nt, out = new_mat('MAT_haze')
tc = nt.nodes.new('ShaderNodeTexCoord')
sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sep.inputs[0])
hgr = math_node(nt, 'POWER', math_node(nt, 'SUBTRACT', 1.0, sep.outputs['Z'], clamp=True), 2.5)
dens = math_node(nt, 'MULTIPLY_ADD', hgr, 0.0012, 0.0002)
pv = nt.nodes.new('ShaderNodeVolumePrincipled')
pv.inputs['Color'].default_value = hexc('#f4c6b6')
pv.inputs['Anisotropy'].default_value = 0.5
nt.links.new(dens, pv.inputs['Density'])
nt.links.new(pv.outputs[0], out.inputs['Volume'])
volume_box('HAZE', -900, 900, -650, 900, -60, 260, m)

# ============================================================ sky world (alpenglow gradient, sun glow, cirrus, stars)
SUN_AZ = math.radians(14.6)       # east of south (jako-hq DUSK dir)


def sun_dir(el_deg):
    el = math.radians(el_deg)
    return Vector((math.sin(SUN_AZ) * math.cos(el), -math.cos(SUN_AZ) * math.cos(el), math.sin(el)))


w = bpy.data.worlds.get('WORLD_alpenglow') or bpy.data.worlds.new('WORLD_alpenglow')
scene.world = w
try:
    w.use_nodes = True
except Exception:
    pass
nt = w.node_tree; nt.nodes.clear()
out = nt.nodes.new('ShaderNodeOutputWorld')
tc = nt.nodes.new('ShaderNodeTexCoord')
nrm = nt.nodes.new('ShaderNodeVectorMath'); nrm.operation = 'NORMALIZE'
nt.links.new(tc.outputs['Generated'], nrm.inputs[0])
sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(nrm.outputs[0], sep.inputs[0])
hpos = math_node(nt, 'MAXIMUM', sep.outputs['Z'], 0.0)
sky = ramp(nt, hpos, [(0.0, hexc('#ffb48a')), (0.035, hexc('#f79c8c')), (0.11, hexc('#dc8fa3')),
                      (0.26, hexc('#9a7fae')), (0.52, hexc('#4d5592')), (1.0, hexc('#20295a'))])
# sun glow
sd = nt.nodes.new('ShaderNodeCombineXYZ'); sd.name = 'SUN_DIR'
v = sun_dir(7.0); sd.inputs[0].default_value, sd.inputs[1].default_value, sd.inputs[2].default_value = v.x, v.y, v.z
dot = nt.nodes.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
nt.links.new(nrm.outputs[0], dot.inputs[0]); nt.links.new(sd.outputs[0], dot.inputs[1])
s = math_node(nt, 'MAXIMUM', dot.outputs['Value'], 0.0)
glow = math_node(nt, 'ADD', math_node(nt, 'MULTIPLY', math_node(nt, 'POWER', s, 5.0), 0.9),
                 math_node(nt, 'MULTIPLY', math_node(nt, 'POWER', s, 80.0), 2.0))
glow = math_node(nt, 'ADD', glow, math_node(nt, 'MULTIPLY', math_node(nt, 'POWER', s, 3000.0), 40.0))
lowband = math_node(nt, 'SUBTRACT', 1.0, math_node(nt, 'MULTIPLY', hpos, 2.2), clamp=True)
glow = math_node(nt, 'MULTIPLY', glow, math_node(nt, 'MULTIPLY_ADD', lowband, 0.8, 0.2))
warm = scale_color(nt, hexc('#ff9566'), glow)
addg = nt.nodes.new('ShaderNodeVectorMath'); addg.operation = 'ADD'
nt.links.new(sky, addg.inputs[0]); nt.links.new(warm, addg.inputs[1])
# cirrus streaks lit pink
mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (2.2, 2.2, 16.0)
nt.links.new(nrm.outputs[0], mp.inputs['Vector'])
cn = nt.nodes.new('ShaderNodeTexNoise'); cn.inputs['Scale'].default_value = 1.6; cn.inputs['Detail'].default_value = 8
cn.inputs['Roughness'].default_value = 0.6
nt.links.new(mp.outputs['Vector'], cn.inputs['Vector'])
cmask = nt.nodes.new('ShaderNodeMapRange'); cmask.inputs['From Min'].default_value = 0.52; cmask.inputs['From Max'].default_value = 0.74
nt.links.new(cn.outputs['Fac'], cmask.inputs['Value'])
band = nt.nodes.new('ShaderNodeMapRange'); band.interpolation_type = 'SMOOTHSTEP'
band.inputs['From Min'].default_value = 0.02; band.inputs['From Max'].default_value = 0.12
nt.links.new(hpos, band.inputs['Value'])
band2 = nt.nodes.new('ShaderNodeMapRange'); band2.interpolation_type = 'SMOOTHSTEP'
band2.inputs['From Min'].default_value = 0.55; band2.inputs['From Max'].default_value = 0.25
nt.links.new(hpos, band2.inputs['Value'])
cloud_f = math_node(nt, 'MULTIPLY', math_node(nt, 'MULTIPLY', cmask.outputs['Result'], band.outputs['Result']), band2.outputs['Result'])
cloud_f = math_node(nt, 'MULTIPLY', cloud_f, 0.65)
skyc = mix_rgb(nt, cloud_f, addg.outputs[0], hexc('#ffb39c'))
# stars
vor = nt.nodes.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 240.0
nt.links.new(nrm.outputs[0], vor.inputs['Vector'])
star = math_node(nt, 'LESS_THAN', vor.outputs['Distance'], 0.055)
starh = nt.nodes.new('ShaderNodeMapRange'); starh.interpolation_type = 'SMOOTHSTEP'
starh.inputs['From Min'].default_value = 0.12; starh.inputs['From Max'].default_value = 0.5
nt.links.new(hpos, starh.inputs['Value'])
star_amt = nt.nodes.new('ShaderNodeValue'); star_amt.name = 'STARS'; star_amt.outputs[0].default_value = 0.0
starv = math_node(nt, 'MULTIPLY', math_node(nt, 'MULTIPLY', star, starh.outputs['Result']), star_amt.outputs[0])
starv = math_node(nt, 'MULTIPLY', starv, 3.0)
adds = nt.nodes.new('ShaderNodeVectorMath'); adds.operation = 'ADD'
nt.links.new(skyc, adds.inputs[0]); nt.links.new(scale_color(nt, (1.0, 0.95, 0.9, 1), starv), adds.inputs[1])
# below the horizon: warm haze ground
below = nt.nodes.new('ShaderNodeMapRange'); below.inputs['From Min'].default_value = 0.0; below.inputs['From Max'].default_value = -0.08
nt.links.new(sep.outputs['Z'], below.inputs['Value'])
final = mix_rgb(nt, below.outputs['Result'], adds.outputs[0], hexc('#9a7c84'))
dim = nt.nodes.new('ShaderNodeValue'); dim.name = 'SKY_DIM'; dim.outputs[0].default_value = 1.0
final = scale_color(nt, final, dim.outputs[0])
bg = nt.nodes.new('ShaderNodeBackground'); bg.inputs['Strength'].default_value = 1.0
nt.links.new(final, bg.inputs['Color']); nt.links.new(bg.outputs[0], out.inputs['Surface'])

# keyframes: light drops over the minute, stars arrive for shot 14
dim.outputs[0].default_value = 1.0; dim.outputs[0].keyframe_insert('default_value', frame=1)
dim.outputs[0].default_value = 0.78; dim.outputs[0].keyframe_insert('default_value', frame=FRAME_END)
star_amt.outputs[0].default_value = 0.0; star_amt.outputs[0].keyframe_insert('default_value', frame=SHOT['14'][1] - 10)
star_amt.outputs[0].default_value = 1.0; star_amt.outputs[0].keyframe_insert('default_value', frame=FRAME_END)

# ============================================================ sun (low, warm, from the south - alpenglow on the north peaks)
ld = bpy.data.lights.new('SUN', 'SUN')
sun = obj('SUN', ld, C)
ld.angle = math.radians(1.4)
for f, el, col_, en in ((1, 8.0, '#ff8f80', 5.0), (FRAME_END // 2, 6.0, '#ff8278', 4.6), (FRAME_END, 3.2, '#ff7070', 3.4)):
    sun.rotation_euler = sun_dir(el).to_track_quat('Z', 'Y').to_euler()
    sun.keyframe_insert('rotation_euler', frame=f)
    ld.color = hex3(col_); ld.keyframe_insert('color', frame=f)
    ld.energy = en; ld.keyframe_insert('energy', frame=f)
try:
    ld.use_shadow = True
    ld.shadow_maximum_resolution = 0.002
except Exception:
    pass

print('01_world done')
