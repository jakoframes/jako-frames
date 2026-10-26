# Jako (Mini Me v2, look "medium") — 3D rebuild script.
#   blender.exe -b --factory-startup --python build_jako.py            -> writes jako.blend next to this file
# Everything is generated from the 2D kit's SVG paths (ref/character.js, 400x500 canvas):
#   1 svg unit = S metres, svg x -> world X (character's right = -X), svg y -> world Z (shoe sole = 0), front = -Y.
# The head is lofted directly from the FACE contour and the hair from the HAIR / HAIR_BACK contours, so the
# front silhouette matches the kit by construction (no eyeballed ellipsoids -> no egg head).
import bpy, bmesh, math, re, os, sys
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils import geometry as mgeo

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'jako.blend')

S = 0.003                     # metres per svg unit  (-> Jako is ~1.37 m)
def X(x): return (x - 200.0) * S
def Z(y): return (485.0 - y) * S
def U(v): return v * S        # svg length -> metres

P = dict(                     # shape parameters (tuned with tools/silhouette_fit.py)
    head_depth=0.90,          # head half-depth / half-width per height
    chin_fwd=6.0,             # chin pushed forward (units)
    head_exp=2.25,            # superellipse exponent of head cross-sections
    hair_front_k=0.84, hair_back_k=0.98, hair_gap=10.0, hair_gap_back=14.0, hair_exp=2.15,
    voxel=0.0032, smooth_iter=6,
)

# ------------------------------------------------------------------ kit shapes (copied from character.js)
FACE = 'M112,165 C110,232 150,268 200,268 C250,268 290,232 288,165 C286,110 250,96 200,96 C150,96 114,110 112,165 Z'
HAIR = ('M106,200 C90,140 104,86 150,60 C178,44 222,42 250,56 C300,78 310,140 294,200 '
        'Q290,212 280,210 Q276,196 268,186 Q264,198 256,202 Q252,184 244,172 Q240,182 230,184 Q226,150 202,122 '
        'Q200,128 198,122 Q174,150 170,184 Q160,182 156,172 Q148,184 144,202 Q136,198 132,186 Q124,196 120,210 '
        'Q110,212 106,200 Z')
HAIR_BACK = ('M106,196 C92,138 104,86 150,60 C178,44 232,40 262,56 C302,78 310,138 294,196 C294,226 266,248 232,252 '
             'L218,246 L208,254 L200,248 L192,254 L182,246 L168,252 C134,248 106,226 106,196 Z')
AHOGE = 'M197,48 Q193,34 182,31 M201,48 Q207,33 218,29'
TORSO = 'M146,290 Q148,277 168,275 L232,275 Q252,277 254,290 L262,384 Q262,393 252,394 Q200,400 148,394 Q138,393 138,384 Z'
SHADES = ('M126,197 Q128,189 140,189 L188,191 Q200,195 212,191 L260,189 Q272,189 274,197 L272,212 Q266,226 242,226 '
          'Q220,226 210,211 Q200,203 190,211 Q180,226 158,226 Q134,226 128,212 Z')
STRANDS_FRONT = ['M194,116 Q176,134 170,160', 'M206,116 Q224,134 230,160', 'M184,96 Q158,118 148,156', 'M216,96 Q242,118 252,156']
STRANDS_BACK = ['M200,64 Q196,120 200,240', 'M160,80 Q142,150 170,240', 'M240,80 Q258,150 230,240']

def hexc(h, a=1.0):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return (*lin, a)
def lerpc(a, b, t): return tuple(a[i] + (b[i] - a[i]) * t for i in range(4))
COL = dict(line='#2a1517', skin='#f6e3d3', skinShade='#eacab4', blush='#f2a39b', mouth='#9c3b3b', hair='#2a1a17',
           strand='#efe6dc', jersey='#f2ece0', maroon='#8e1f35', navy='#1f2c6b', gold='#f0bf2e', red='#c8102e',
           denimDark='#1f1c1e', denimMid='#5a5658', shoe='#fbfaf7', mesh='#c3c6cc', watch='#c9ced6', lcd='#a9ba8f',
           shades='#141113')

# ------------------------------------------------------------------ svg path -> polylines
def parse_path(d, seg=20):
    toks = re.findall(r'[MLCQZ]|-?\d*\.?\d+', d)
    subs, i, cmd, cur = [], 0, None, None
    def num():
        nonlocal i
        v = float(toks[i]); i += 1; return v
    while i < len(toks):
        if toks[i] in ('M', 'L', 'C', 'Q', 'Z'):
            cmd = toks[i]; i += 1
            if cmd == 'Z':
                continue
        if cmd == 'M':
            cur = (num(), num()); subs.append([cur]); cmd = 'L'
        elif cmd == 'L':
            cur = (num(), num()); subs[-1].append(cur)
        elif cmd == 'Q':
            c, p = (num(), num()), (num(), num())
            for k in range(1, seg + 1):
                t = k / seg; a, b, e = (1 - t) ** 2, 2 * (1 - t) * t, t * t
                subs[-1].append((a * cur[0] + b * c[0] + e * p[0], a * cur[1] + b * c[1] + e * p[1]))
            cur = p
        elif cmd == 'C':
            c1, c2, p = (num(), num()), (num(), num()), (num(), num())
            for k in range(1, seg + 1):
                t = k / seg; a, b, e, f = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
                subs[-1].append((a * cur[0] + b * c1[0] + e * c2[0] + f * p[0], a * cur[1] + b * c1[1] + e * c2[1] + f * p[1]))
            cur = p
        else:
            i += 1
    out = []
    for s in subs:
        o = [s[0]]
        for q in s[1:]:
            if abs(q[0] - o[-1][0]) + abs(q[1] - o[-1][1]) > 1e-6:
                o.append(q)
        if len(o) > 2 and abs(o[0][0] - o[-1][0]) + abs(o[0][1] - o[-1][1]) < 1e-6:
            o.pop()
        out.append(o)
    return out

def spans(poly, y):
    xs = []
    n = len(poly)
    for k in range(n):
        (x1, y1), (x2, y2) = poly[k], poly[(k + 1) % n]
        if (y1 <= y < y2) or (y2 <= y < y1):
            xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
    return (min(xs), max(xs)) if xs else None

def sstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)
def spow(v, e): return math.copysign(abs(v) ** e, v)

# ------------------------------------------------------------------ scene reset
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
reset()
SC = bpy.context.scene
COLL = {}
def coll(name):
    if name not in COLL:
        c = bpy.data.collections.new(name); SC.collection.children.link(c); COLL[name] = c
    return COLL[name]

def mesh_obj(name, verts, faces, collection='JAKO', smooth=True, mats=()):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.validate(); me.update()
    ob = bpy.data.objects.new(name, me)
    coll(collection).objects.link(ob)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    if smooth:
        me.shade_smooth()
    for m in mats:
        me.materials.append(m)
    return ob

def skin_rings(rings, top=None, bottom=None, closed_loop=True):
    """rings: list of lists of points (same count). top/bottom: pole points or 'fan' or None."""
    verts, faces = [], []
    n = len(rings[0])
    for r in rings:
        verts.extend(r)
    for i in range(len(rings) - 1):
        for j in range(n if closed_loop else n - 1):
            a, b = i * n + j, i * n + (j + 1) % n
            faces.append((a, b, b + n, a + n))
    for cap, ri in ((top, 0), (bottom, len(rings) - 1)):
        if cap is None:
            continue
        p = cap if not isinstance(cap, str) else sum((Vector(v) for v in rings[ri]), Vector()) / n
        verts.append(Vector(p)); c = len(verts) - 1; base = ri * n
        for j in range(n):
            faces.append((base + j, base + (j + 1) % n, c) if ri == 0 else (base + (j + 1) % n, base + j, c))
    return verts, faces

def superellipse_ring(cx, cy, z, wx, yf, yb, exp, segs):
    pts = []
    for j in range(segs):
        th = 2 * math.pi * j / segs
        c, s = math.cos(th), math.sin(th)
        pts.append(Vector((cx + wx * spow(c, 2 / exp), cy + (yb if s > 0 else yf) * spow(s, 2 / exp), z)))
    return pts

def set_attr(ob, name, vals):
    me = ob.data
    if name in me.attributes:
        me.attributes.remove(me.attributes[name])
    a = me.attributes.new(name, 'FLOAT_VECTOR', 'POINT')
    flat = [c for v in vals for c in v]
    a.data.foreach_set('vector', flat)

def world_to_svg(v):
    return (v.x / S + 200.0, 485.0 - v.z / S, v.y / S)

# ------------------------------------------------------------------ materials
def principled(name, color, rough=0.5, metal=0.0, sss=0.0, coat=0.0, coat_rough=0.1, sheen=0.0, spec=0.5, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = color
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Specular IOR Level'].default_value = spec
    if sss:
        b.inputs['Subsurface Weight'].default_value = sss
        b.inputs['Subsurface Radius'].default_value = (1.0, 0.45, 0.3)
        b.inputs['Subsurface Scale'].default_value = 0.02
    if coat:
        b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = coat_rough
    if sheen:
        b.inputs['Sheen Weight'].default_value = sheen; b.inputs['Sheen Roughness'].default_value = 0.4
    if emit:
        b.inputs['Emission Color'].default_value = color; b.inputs['Emission Strength'].default_value = emit
    m.diffuse_color = color
    return m

def node(nt, kind, loc=(0, 0), **kw):
    n = nt.nodes.new(kind); n.location = loc
    for k, v in kw.items():
        setattr(n, k, v)
    return n
def math_n(nt, op, a, b=None, loc=(0, 0)):
    n = node(nt, 'ShaderNodeMath', loc, operation=op)
    for idx, v in ((0, a), (1, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[idx].default_value = v
        else:
            nt.links.new(v, n.inputs[idx])
    return n.outputs[0]
def mix_col(nt, fac, a, b, loc=(0, 0)):
    n = node(nt, 'ShaderNodeMix', loc, data_type='RGBA')
    nt.links.new(fac, n.inputs['Factor'])
    for sock, v in ((n.inputs[6], a), (n.inputs[7], b)):
        if isinstance(v, tuple):
            sock.default_value = v
        else:
            nt.links.new(v, sock)
    return n.outputs[2]
def svg_attr(nt):
    a = node(nt, 'ShaderNodeAttribute', (-900, 0), attribute_type='GEOMETRY', attribute_name='svg')
    sep = node(nt, 'ShaderNodeSeparateXYZ', (-700, 0))
    nt.links.new(a.outputs['Vector'], sep.inputs[0])
    return sep.outputs[0], sep.outputs[1], sep.outputs[2]

M = {}
M['line'] = principled('MAT_line', hexc(COL['line']), 0.25, coat=1.0, coat_rough=0.08)
M['white'] = principled('MAT_white', (1, 1, 1, 1), 0.3, emit=0.3)
M['mouth'] = principled('MAT_mouth', hexc(COL['mouth']), 0.35, coat=0.5)
M['hair'] = principled('MAT_hair', hexc(COL['hair']), 0.55, coat=0.12, coat_rough=0.35, sheen=0.15, spec=0.4)
M['strand'] = principled('MAT_hair_strand', lerpc(hexc(COL['hair']), hexc(COL['strand']), 0.55), 0.45, coat=0.2)
M['maroon'] = principled('MAT_maroon', hexc(COL['maroon']), 0.7, sheen=0.3)
M['navy'] = principled('MAT_navy', hexc(COL['navy']), 0.6)
M['gold'] = principled('MAT_gold', hexc(COL['gold']), 0.4)
M['red'] = principled('MAT_red', hexc(COL['red']), 0.5)
M['crestwhite'] = principled('MAT_crest_white', hexc('#ffffff'), 0.5)
M['shoe'] = principled('MAT_shoe', hexc(COL['shoe']), 0.45, coat=0.2)
M['mesh'] = principled('MAT_shoe_mesh', hexc(COL['mesh']), 0.8)
M['watch'] = principled('MAT_watch', hexc(COL['watch']), 0.22, metal=1.0)
M['lcd'] = principled('MAT_lcd', hexc(COL['lcd']), 0.3, emit=0.15)
M['shades'] = principled('MAT_shades', hexc(COL['shades']), 0.12, coat=1.0, coat_rough=0.03)
M['skinshade'] = principled('MAT_skin_shade', hexc(COL['skinShade']), 0.55, sss=0.15)

SKIN3D = lerpc(hexc(COL['skin']), hexc('#e4a98a'), 0.2)     # kit peach, a touch warmer so form reads in 3D
def skin_mat():
    m = principled('MAT_skin', SKIN3D, 0.5, sss=0.22, spec=0.45)
    nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    xs, ys, yd = svg_attr(nt)
    masks = []
    for cx in (144, 256):
        dx = math_n(nt, 'DIVIDE', math_n(nt, 'SUBTRACT', xs, cx), 19.0)
        dy = math_n(nt, 'DIVIDE', math_n(nt, 'SUBTRACT', ys, 234.0), 11.0)
        d = math_n(nt, 'SQRT', math_n(nt, 'ADD', math_n(nt, 'MULTIPLY', dx, dx), math_n(nt, 'MULTIPLY', dy, dy)))
        mr = node(nt, 'ShaderNodeMapRange', (-200, 0), interpolation_type='SMOOTHSTEP')
        nt.links.new(d, mr.inputs['Value']); mr.inputs['From Min'].default_value = 0.25; mr.inputs['From Max'].default_value = 1.35
        mr.inputs['To Min'].default_value = 1.0; mr.inputs['To Max'].default_value = 0.0
        masks.append(mr.outputs[0])
    front = math_n(nt, 'LESS_THAN', yd, 0.0)
    mask = math_n(nt, 'MULTIPLY', math_n(nt, 'MAXIMUM', masks[0], masks[1]), front)
    val = node(nt, 'ShaderNodeValue', (-300, -300)); val.name = 'BLUSH'; val.label = 'blush (driven)'; val.outputs[0].default_value = 0.0
    fac = math_n(nt, 'MULTIPLY', mask, val.outputs[0])
    col = mix_col(nt, fac, SKIN3D, hexc(COL['blush']))
    nt.links.new(col, b.inputs['Base Color'])
    return m
M['skin'] = skin_mat()

def jersey_mat():
    m = principled('MAT_jersey', hexc(COL['jersey']), 0.78, sheen=0.45, spec=0.35)
    nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    xs, ys, yd = svg_attr(nt)
    ax = math_n(nt, 'ABSOLUTE', math_n(nt, 'SUBTRACT', xs, 200.0))
    t = math_n(nt, 'DIVIDE', math_n(nt, 'SUBTRACT', ys, 280.0), 122.0)
    t8 = math_n(nt, 'MULTIPLY', t, 8.0)
    m1 = math_n(nt, 'GREATER_THAN', ax, math_n(nt, 'ADD', t8, 37.0))
    m2 = math_n(nt, 'GREATER_THAN', ax, math_n(nt, 'ADD', t8, 46.0))
    vlim = math_n(nt, 'MULTIPLY', math_n(nt, 'SUBTRACT', 300.0, ys), 22.0 / 24.0)
    v = math_n(nt, 'MULTIPLY', math_n(nt, 'LESS_THAN', ax, vlim), math_n(nt, 'LESS_THAN', yd, 0.0))
    c = mix_col(nt, m1, hexc(COL['jersey']), hexc(COL['maroon']))
    c = mix_col(nt, m2, c, hexc(COL['navy']))
    c = mix_col(nt, v, c, SKIN3D)
    nt.links.new(c, b.inputs['Base Color'])
    return m
M['jersey'] = jersey_mat()

def sleeve_mat():
    m = principled('MAT_sleeve', hexc(COL['jersey']), 0.78, sheen=0.45, spec=0.35)
    nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    u, h, v = svg_attr(nt)          # local arm coords: h = distance down the arm from the shoulder pivot
    mar = math_n(nt, 'MULTIPLY', math_n(nt, 'GREATER_THAN', h, 21.0), math_n(nt, 'LESS_THAN', h, 26.0))
    nav = math_n(nt, 'GREATER_THAN', h, 26.0)
    c = mix_col(nt, mar, hexc(COL['jersey']), hexc(COL['maroon']))
    c = mix_col(nt, nav, c, hexc(COL['navy']))
    nt.links.new(c, b.inputs['Base Color'])
    return m
M['sleeve'] = sleeve_mat()

def denim_mat():
    m = principled('MAT_denim', hexc(COL['denimDark']), 0.88, sheen=0.5, spec=0.3)
    nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    lw = node(nt, 'ShaderNodeLayerWeight', (-900, 200)); lw.inputs['Blend'].default_value = 0.45
    face = math_n(nt, 'POWER', lw.outputs['Facing'], 0.45)
    tc = node(nt, 'ShaderNodeTexCoord', (-1100, -200))
    nz = node(nt, 'ShaderNodeTexNoise', (-900, -200)); nz.inputs['Scale'].default_value = 9.0; nz.inputs['Detail'].default_value = 6.0
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    wash = math_n(nt, 'MULTIPLY', math_n(nt, 'SUBTRACT', nz.outputs['Fac'], 0.5), 0.9)
    f = math_n(nt, 'ADD', face, wash)
    c = mix_col(nt, f, lerpc(hexc(COL['denimMid']), hexc(COL['denimDark']), 0.25), hexc(COL['denimDark']))
    nt.links.new(c, b.inputs['Base Color'])
    return m
M['denim'] = denim_mat()

# ------------------------------------------------------------------ head (lofted from FACE)
face_poly = parse_path(FACE, 40)[0]
def face_half(y):
    s = spans(face_poly, y)
    return None if s is None else ((s[1] - s[0]) / 2, (s[0] + s[1]) / 2)
FY0, FY1 = 96.0, 268.0
def chin_off(y): return -P['chin_fwd'] * sstep(170, 268, y)
def head_depth(y):
    h = face_half(y)
    return 0.0 if h is None else P['head_depth'] * h[0]

def build_head():
    rings = []
    NR, SEG = 110, 128
    for i in range(1, NR):
        u = i / NR
        y = FY0 + (FY1 - FY0) * (1 - math.cos(math.pi * u)) / 2
        hw, cx = face_half(y)
        d = P['head_depth'] * hw
        rings.append(superellipse_ring(X(cx), U(chin_off(y)), Z(y), U(hw), U(d), U(d), P['head_exp'], SEG))
    v, f = skin_rings(rings, top=Vector((0, U(chin_off(FY0)), Z(FY0))), bottom=Vector((0, U(chin_off(FY1)), Z(FY1))))
    ob = mesh_obj('JAKO_head', v, f, mats=[M['skin']])
    set_attr(ob, 'svg', [world_to_svg(p.co) for p in ob.data.vertices])
    return ob

def ellipsoid(name, c, r, mats, segs=32, rings=20, coll_name='JAKO', rot=None, exp=2.0):
    ring_list = []
    for i in range(1, rings):
        a = math.pi * i / rings
        z, rr = math.cos(a), math.sin(a)
        ring = []
        for j in range(segs):
            th = 2 * math.pi * j / segs
            p = Vector((spow(rr, 2 / exp) * spow(math.cos(th), 2 / exp) * r[0], spow(rr, 2 / exp) * spow(math.sin(th), 2 / exp) * r[1], spow(z, 2 / exp) * r[2]))
            if rot: p = rot @ p
            ring.append(Vector(c) + p)
        ring_list.append(ring)
    top = Vector((0, 0, r[2])); bot = Vector((0, 0, -r[2]))
    if rot: top, bot = rot @ top, rot @ bot
    v, f = skin_rings(ring_list, top=Vector(c) + top, bottom=Vector(c) + bot)
    return mesh_obj(name, v, f, coll_name, mats=mats)

head = build_head()
ears = []
for sx, ex in ((-1, 111), (1, 289)):
    rot = Matrix.Rotation(math.radians(-sx * 18), 3, 'Z')
    e = ellipsoid('JAKO_ear_%s' % ('R' if sx < 0 else 'L'), (X(ex) + sx * U(1.5), U(4), Z(206)), (U(6.5), U(10), U(12)), [M['skin']], rot=rot)
    set_attr(e, 'svg', [(0, 0, 1)] * len(e.data.vertices))    # outside blush mask
    ears.append(e)

# ------------------------------------------------------------------ generic sweep (tubes / ribbons)
def sweep(name, pts, rad_n, rad_b, normals=None, segs=10, mats=(), coll_name='JAKO', cap=True):
    pts = [Vector(p) for p in pts]
    n = len(pts)
    tang = []
    for i in range(n):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, n - 1)]
        tang.append((b - a).normalized())
    frames = []
    if normals is None:
        t0 = tang[0]; ref = Vector((0, 0, 1)) if abs(t0.z) < 0.9 else Vector((1, 0, 0))
        nn = (ref - t0 * ref.dot(t0)).normalized()
        for i in range(n):
            nn = (nn - tang[i] * nn.dot(tang[i])).normalized()
            frames.append(nn.copy())
    else:
        for i in range(n):
            nn = Vector(normals[i]); nn = (nn - tang[i] * nn.dot(tang[i])).normalized(); frames.append(nn)
    rings = []
    for i in range(n):
        nn = frames[i]; bb = tang[i].cross(nn).normalized()
        rn, rb = (rad_n[i] if isinstance(rad_n, (list, tuple)) else rad_n), (rad_b[i] if isinstance(rad_b, (list, tuple)) else rad_b)
        ring = []
        for j in range(segs):
            th = 2 * math.pi * j / segs
            ring.append(pts[i] + nn * (rn * math.cos(th)) + bb * (rb * math.sin(th)))
        rings.append(ring)
    v, f = skin_rings(rings, top='fan' if cap else None, bottom='fan' if cap else None)
    return mesh_obj(name, v, f, coll_name, mats=mats)

def taper(n, lo=0.25, ends=0.18):
    out = []
    for i in range(n):
        u = i / (n - 1)
        k = min(u, 1 - u) / ends
        out.append(lo + (1 - lo) * math.sqrt(max(0.0, min(1.0, k))))
    return out

def bvh_of(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    return BVHTree.FromObject(ob, dg)

def resample(poly, step):
    out = [Vector((poly[0][0], poly[0][1]))]
    for q in poly[1:]:
        a, b = out[-1], Vector(q)
        L = (b - a).length
        k = max(1, int(L / step))
        for j in range(1, k + 1):
            out.append(a.lerp(b, j / k))
    return out

# ------------------------------------------------------------------ hair
hair_front_poly = parse_path(HAIR, 30)[0]
hair_back_poly = parse_path(HAIR_BACK, 30)[0]
def hair_half(y):
    a, b = spans(hair_front_poly, y), spans(hair_back_poly, y)
    def half(s): return None if s is None else (s[1] - s[0]) / 2     # kit is slightly lopsided: split the difference
    if y <= 200 and a is not None:
        hu = half(a) if b is None else max(half(a), (half(b) + half(a)) / 2)
    else:
        hu = half(b) if b is not None else 0.0
    if y > 200:
        fh = face_half(y)
        clamp = (fh[0] - 1.5) if fh else 0.0
        k = sstep(200, 222, y)
        hb = half(b) if b is not None else 0.0
        hu = (1 - k) * hu + k * min(hb, clamp)
    return hu
def hair_top():
    y = 30.0
    while spans(hair_front_poly, y) is None and spans(hair_back_poly, y) is None:
        y += 0.25
    return y
HY0, HY1 = hair_top(), 258.0

def hair_depths(y):
    wh = hair_half(y)
    hd = head_depth(y)
    hf = P['hair_front_k'] * wh
    hb = P['hair_back_k'] * wh
    if hd > 0:
        hf = max(hf, hd - chin_off(y) + P['hair_gap'])
        hb = max(hb, hd + chin_off(y) + P['hair_gap_back'])
    return wh, hf, hb

def build_hair_volume():
    rings = []
    NR, SEG = 140, 128
    for i in range(1, NR):
        u = i / NR
        y = HY0 + (HY1 - HY0) * (1 - math.cos(math.pi * u)) / 2
        wh, hf, hb = hair_depths(y)
        wh = max(wh, 1.0)
        rings.append(superellipse_ring(0.0, 0.0, Z(y), U(wh), U(max(hf, 1.0)), U(max(hb, 1.0)), P['hair_exp'], SEG))
    v, f = skin_rings(rings, top=Vector((0, 0, Z(HY0))), bottom=Vector((0, 0, Z(HY1))))
    return mesh_obj('JAKO_hair_volume', v, f, 'CUTTERS', smooth=False)

def prism(name, poly2d, y0, y1, mirror=False):
    """poly in svg coords, extruded along world Y from y0 to y1 (metres)."""
    bm = bmesh.new()
    def w(p, yy): return Vector(((200 - p[0]) * S if mirror else X(p[0]), yy, Z(p[1])))
    a = [bm.verts.new(w(p, y0)) for p in poly2d]
    b = [bm.verts.new(w(p, y1)) for p in poly2d]
    n = len(poly2d)
    bm.faces.new(a); bm.faces.new(list(reversed(b)))
    for k in range(n):
        bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); coll('CUTTERS').objects.link(ob)
    return ob

def chain_after(poly, start_pt):
    k = min(range(len(poly)), key=lambda i: (poly[i][0] - start_pt[0]) ** 2 + (poly[i][1] - start_pt[1]) ** 2)
    return poly[k:] + [poly[0]]

def build_hair():
    vol = build_hair_volume()
    # A: face opening under the fringe, front half only
    fr = chain_after(hair_front_poly, (294, 200))
    cutA = prism('CUT_face', fr + [(40, 200), (40, 560), (360, 560), (360, 200)], -1.5, 0.0)
    # B: under the back outline (zigzag nape), back half only (back view -> mirrored x)
    bk = chain_after(hair_back_poly, (294, 196))
    cutB = prism('CUT_nape', bk + [(40, 196), (40, 560), (360, 560), (360, 196)], 0.0, 1.5, mirror=True)
    # C: soft centre-part groove from the part apex over the crown
    bvh = bvh_of(vol)
    C0 = Vector((0, 0, Z(150)))
    apex = Vector((0, -U(hair_depths(124)[1]), Z(124)))
    phi0 = math.atan2(apex.z - C0.z, -apex.y)
    pts, rads = [], []
    NG = 40
    for k in range(NG):
        phi = phi0 + (math.radians(84) - phi0) * k / (NG - 1)
        d = Vector((0, -math.cos(phi), math.sin(phi)))
        hit = bvh.ray_cast(C0 + d * 2.0, -d, 4.0)
        if hit[0] is None:
            continue
        # wide, shallow valley (radius 5, centre 3.4 above the surface -> ~1.6 units deep) that fades out on the crown
        pts.append(hit[0] + hit[1] * U(3.4 + 1.6 * (k / (NG - 1)) ** 2))
        rads.append(U(5.0))
    # extend groove forward past the apex so it opens into the parting
    if len(pts) > 2:
        dv = (pts[0] - pts[1]).normalized()
        pts.insert(0, pts[0] + dv * U(10)); rads.insert(0, rads[0])
    cutC = sweep('CUT_part', pts, rads, rads, segs=12, coll_name='CUTTERS')
    # the part groove (cutC) read as a hard seam over the crown; the kit only shows the parting at the fringe apex
    bpy.data.objects.remove(cutC, do_unlink=True)
    for c in (cutA, cutB):
        mo = vol.modifiers.new('bool_' + c.name, 'BOOLEAN'); mo.object = c; mo.operation = 'DIFFERENCE'
        mo.solver = 'MANIFOLD'   # EXACT silently skips cutter A (its back face lies on the loft's Y=0 seam)
    rm = vol.modifiers.new('remesh', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = P['voxel']; rm.adaptivity = 0.0
    sm = vol.modifiers.new('smooth', 'LAPLACIANSMOOTH'); sm.iterations = P['smooth_iter']; sm.lambda_factor = 0.6
    sm.use_volume_preserve = True; sm.use_normalized = True
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(vol.evaluated_get(dg), depsgraph=dg)
    me.name = 'JAKO_hair'
    hair = bpy.data.objects.new('JAKO_hair', me); coll('JAKO').objects.link(hair)
    me.shade_smooth(); me.materials.clear(); me.materials.append(M['hair'])
    for c in (vol, cutA, cutB):
        bpy.data.objects.remove(c, do_unlink=True)
    return hair

hair = build_hair()
hair_bvh = bvh_of(hair)

def project_curve(path_d, bvh, side='front', lift=0.3, step=2.0):
    pts, nors = [], []
    for sub in parse_path(path_d, 30):
        for q in resample(sub, step):
            if side == 'front':
                o, d = Vector((X(q.x), -3.0, Z(q.y))), Vector((0, 1, 0))
            else:
                o, d = Vector(((200 - q.x) * S, 3.0, Z(q.y))), Vector((0, -1, 0))
            h = bvh.ray_cast(o, d, 6.0)
            if h[0] is not None:
                pts.append(h[0] + h[1] * U(lift)); nors.append(h[1])
    return pts, nors

strand_objs = []
for i, d in enumerate(STRANDS_FRONT + STRANDS_BACK):
    side = 'front' if i < len(STRANDS_FRONT) else 'back'
    pts, nors = project_curve(d, hair_bvh, side, lift=0.15)
    if len(pts) < 3:
        continue
    tp = taper(len(pts), 0.15, 0.3)
    w = 1.25 if side == 'front' else 1.0
    strand_objs.append(sweep('JAKO_hair_strand_%02d' % i, pts, [U(0.35) * t for t in tp], [U(w) * t for t in tp],
                             normals=nors, segs=8, mats=[M['strand']]))

# ahoge: two strands rising from the crown
def crown_point():
    best = None
    for k in range(-40, 41):
        o = Vector((0, U(k), 2.0)); h = hair_bvh.ray_cast(o, Vector((0, 0, -1)), 3.0)
        if h[0] is not None and (best is None or h[0].z > best.z):
            best = h[0]
    return best
CROWN = crown_point()
ahoge_objs = []
for k, sub in enumerate(parse_path(AHOGE, 16)):
    pts = []
    for (x, y) in sub:
        t = (48 - y) / 19.0
        k = 1.18      # a touch longer than the kit stroke centre-line: 3D tubes have no ink outline
        pts.append(Vector((X(199 + (x - 199) * k), CROWN.y + U(4.0 * max(0, t)), CROWN.z + U((48 - y) * k) - U(2.5))))
    n = len(pts)
    r = [U(2.4 - 1.7 * (i / (n - 1)) ** 1.2) for i in range(n)]
    ahoge_objs.append(sweep('JAKO_ahoge_%d' % k, pts, r, r, segs=10, mats=[M['hair']]))

# ------------------------------------------------------------------ face decals (2D kit shapes projected onto the head)
def stroke2d(pts, w, cap_segs=6):
    pts = [Vector(p) for p in pts]
    n = len(pts); verts, faces = [], []
    hw = w / 2
    for i in range(n):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, n - 1)]
        t = (b - a).normalized(); nn = Vector((-t.y, t.x))
        verts += [pts[i] + nn * hw, pts[i] - nn * hw]
    for i in range(n - 1):
        faces.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
    for end in (0, n - 1):
        c = pts[end]; a, b = pts[max(end - 1, 0)], pts[min(end + 1, n - 1)]
        t = (b - a).normalized() * (-1 if end == 0 else 1); nn = Vector((-t.y, t.x))
        ci = len(verts); verts.append(c.copy())
        ring = [2 * end, ]
        prev = 2 * end
        for k in range(1, cap_segs):
            ang = math.pi * k / cap_segs
            p = c + nn * (hw * math.cos(ang)) + t * (hw * math.sin(ang))
            verts.append(p); idx = len(verts) - 1
            faces.append((ci, prev, idx) if end == n - 1 else (ci, idx, prev)); prev = idx
        last = 2 * end + 1
        faces.append((ci, prev, last) if end == n - 1 else (ci, last, prev))
    return verts, faces

def fill2d(poly):
    pts = [Vector((p[0], p[1], 0)) for p in poly]
    tris = mgeo.tessellate_polygon([pts])
    return [Vector((p.x, p.y)) for p in pts], [tuple(t) for t in tris]

def ellipse(cx, cy, rx, ry, n=36):
    return [(cx + rx * math.cos(2 * math.pi * k / n), cy + ry * math.sin(2 * math.pi * k / n)) for k in range(n)]

def decal(name, parts, bvh, lift=0.7, thick=1.0, side='front', mats=None, cuts=2, coll_name='JAKO', origin_fn=None):
    """parts: list of (verts2d, faces, material_index, extra_lift). Builds one projected, solidified object."""
    bm = bmesh.new()
    for (vs, fs, mi, extra) in parts:
        bv = [bm.verts.new((v.x, v.y, extra)) for v in vs]
        for f in fs:
            try:
                face = bm.faces.new([bv[i] for i in f]); face.material_index = mi
            except ValueError:
                pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    if cuts:
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    misses, dists = [], []
    for v in bm.verts:
        x, y, extra = v.co
        if origin_fn:
            o, d = origin_fn(x, y)
        elif side == 'front':
            o, d = Vector((X(x), -3.0, Z(y))), Vector((0, 1, 0))
        else:
            o, d = Vector(((200 - x) * S, 3.0, Z(y))), Vector((0, -1, 0))
        h = bvh.ray_cast(o, d, 6.0)
        if h[0] is None:
            misses.append((v, o, d, extra))
        else:
            v.co = h[0] + h[1] * U(lift + extra); dists.append(h[3])
    md = sum(dists) / len(dists) if dists else 3.0
    for v, o, d, extra in misses:       # ray slipped past the silhouette: snap to the nearest surface instead
        loc, nor, _, _ = bvh.find_nearest(o + d * md)
        v.co = loc + nor * U(lift + extra)
    # orient faces toward the viewer
    for f in bm.faces:
        f.normal_update()
        dview = origin_fn(0, 0)[1] if origin_fn else (Vector((0, 1, 0)) if side == 'front' else Vector((0, -1, 0)))
        if f.normal.dot(dview) > 0:
            f.normal_flip()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); coll(coll_name).objects.link(ob)
    for m in (mats or []):
        me.materials.append(m)
    me.shade_smooth()
    so = ob.modifiers.new('solidify', 'SOLIDIFY'); so.thickness = U(thick); so.offset = -1.0; so.use_even_offset = True
    return ob

head_bvh = bvh_of(head)
EYES = (161, 239)
def P2(d): return parse_path(d, 20)
def strokes(d, w, mi=0, extra=0.0):
    return [(*stroke2d(sub, w), mi, extra) for sub in P2(d)]
def fills(d, mi=0, extra=0.0):
    return [(*fill2d(sub), mi, extra) for sub in P2(d)]

def eyes_neutral(lid=203):
    parts = []
    for x in EYES:
        parts += fills(f'M{x-11},{lid} L{x+11},{lid} C{x+11},{lid+13} {x+6},{lid+20} {x},{lid+20} C{x-6},{lid+20} {x-11},{lid+13} {x-11},{lid} Z')
        parts += strokes(f'M{x-14},{lid-1} Q{x},{lid-4} {x+14},{lid-1}', 4.0)
    return parts
def eyes_blink(): return sum((strokes(f'M{x-11},211 Q{x},216 {x+11},211', 4.5) for x in EYES), [])
def eyes_happy(): return sum((strokes(f'M{x-11},213 Q{x},197 {x+11},213', 5.0) for x in EYES), [])
def eyes_surprised():
    parts = []
    for x in EYES:
        parts.append((*fill2d(ellipse(x, 210, 10, 13)), 0, 0.0))
        parts.append((*fill2d(ellipse(x + 3, 205, 2.6, 2.6, 16)), 1, 0.35))
    return parts
def brows(dy): return strokes(f'M150,{183+dy} Q162,{180+dy} 173,{182+dy} M227,{182+dy} Q238,{180+dy} 250,{183+dy}', 4.0)

FACE_SETS = {
    'EYES_neutral': (eyes_neutral(), [M['line']]),
    'EYES_blink': (eyes_blink(), [M['line']]),
    'EYES_happy': (eyes_happy(), [M['line']]),
    'EYES_surprised': (eyes_surprised(), [M['line'], M['white']]),
    'BROWS_neutral': (brows(0), [M['line']]),
    'BROWS_happy': (brows(-4), [M['line']]),
    'BROWS_surprised': (brows(-8), [M['line']]),
    'MOUTH_closed': (strokes('M196,246 L204,246', 3.0), [M['line']]),
    'MOUTH_open': (fills('M193.5,243.5 Q200,245.5 206.5,243.5 Q206,252.5 200,252.5 Q194,252.5 193.5,243.5 Z', 1)
                   + strokes('M193.5,243.5 Q200,245.5 206.5,243.5 Q206,252.5 200,252.5 Q194,252.5 193.5,243.5 Z', 2.6, 0, 0.1), [M['line'], M['mouth']]),
    'MOUTH_happy': (fills('M191,240 Q200,242 209,240 Q207,253 200,253 Q193,253 191,240 Z', 1)
                    + strokes('M191,240 Q200,242 209,240 Q207,253 200,253 Q193,253 191,240 Z', 3.0, 0, 0.1), [M['line'], M['mouth']]),
    'MOUTH_surprised': ([(*fill2d(ellipse(200, 248, 5, 6.5)), 1, 0.0),
                         (*stroke2d(ellipse(200, 248, 5, 6.5) + [ellipse(200, 248, 5, 6.5)[0]], 3.0), 0, 0.1)], [M['line'], M['mouth']]),
}
face_objs = {}
for name, (parts, mats) in FACE_SETS.items():
    face_objs[name] = decal('JAKO_' + name, parts, head_bvh, lift=0.55, thick=0.9, mats=mats)

# ------------------------------------------------------------------ shades (projected wrap-around lenses + arms)
def build_shades():
    parts = [(*fill2d(parse_path(SHADES, 24)[0]), 0, 0.0)]
    # lenses sit on a smooth wrap-around cylinder in front of the face AND the fringe tips (the kit draws them
    # over the hair). Offsetting along face normals instead made the lens edges fold over.
    hf0 = head_depth(207) - chin_off(207)
    Rw, front = 105.0, hf0 + 14.0
    Yc = -front + Rw
    pv, pf = [], []
    NX, NZ = 60, 16
    for i in range(NX + 1):
        xu = -92 + 184 * i / NX
        for j in range(NZ + 1):
            yy = 178 + 60 * j / NZ
            pv.append(Vector((U(xu), U(Yc - math.sqrt(Rw * Rw - xu * xu) + 0.004 * (yy - 207) ** 2), Z(yy))))
    for i in range(NX):
        for j in range(NZ):
            a = i * (NZ + 1) + j
            pf.append((a, a + 1, a + NZ + 2, a + NZ + 1))
    proxy = mesh_obj('tmp_shade_proxy', pv, pf, 'CUTTERS', smooth=False)
    pbvh = bvh_of(proxy)
    sh = decal('JAKO_SHADES_on', parts, pbvh, lift=0.0, thick=3.0, mats=[M['shades']], cuts=3)
    # arms: from the lens corners back along the side of the head to the ear tops
    arms = []
    for sx, (xc, yc) in ((-1, (127.5, 198)), (1, (272.5, 198))):
        o = Vector((X(xc), -3.0, Z(yc))); h = pbvh.ray_cast(o, Vector((0, 1, 0)), 6.0)
        start = h[0] + Vector((0, U(1.5), 0))
        pts = [start]
        for k in range(1, 9):
            yy = start.y + (U(2) - start.y) * k / 8
            o = Vector((sx * 1.0, yy, Z(199)))
            hh = head_bvh.ray_cast(o, Vector((-sx, 0, 0)), 2.0)
            if hh[0] is not None:
                pts.append(hh[0] + hh[1] * U(3.5 + 8.0 * (1 - k / 8) ** 2))
        arms.append(sweep('JAKO_SHADES_arm_%s' % ('R' if sx < 0 else 'L'), pts, U(1.5), U(2.2), segs=8, mats=[M['shades']]))
    # join arms into the lens object
    bpy.ops.object.select_all(action='DESELECT')
    for a in arms:
        a.select_set(True)
    sh_mesh = sh
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(sh.evaluated_get(dg), depsgraph=dg)
    bm = bmesh.new(); bm.from_mesh(me)
    # grid-fill subdivision of the concave lens outline leaves an occasional stray vertex; the lens spans y 189..226
    stray = [v for v in bm.verts if v.co.z > Z(186.5) or v.co.z < Z(229.5)]
    bmesh.ops.delete(bm, geom=stray, context='VERTS')
    print('shades: removed stray verts', len(stray))
    for a in arms:
        bm.from_mesh(a.data)
        bpy.data.objects.remove(a, do_unlink=True)
    bm.to_mesh(me); bm.free()
    sh.modifiers.clear(); old = sh.data; sh.data = me; me.name = 'JAKO_SHADES_on'; bpy.data.meshes.remove(old)
    sh.data.materials.clear(); sh.data.materials.append(M['shades'])
    for p in sh.data.polygons: p.material_index = 0
    sh.data.shade_smooth()
    return sh

shades_on = build_shades()

SHADES_UP_TILT = 52.0
def build_shades_up():
    """Glasses pushed up onto the hair: the same lens outline projected onto the hair along a view tilted up
    by SHADES_UP_TILT degrees about the ear axis, plus short arm stubs that tuck into the hair."""
    pivot = Vector((0, U(3), Z(200)))
    R = Matrix.Rotation(math.radians(-SHADES_UP_TILT), 3, 'X')
    dirv = R @ Vector((0, 1, 0))
    def org(x, y):
        return pivot + R @ Vector((X(x), -3.0, Z(y) - pivot.z)), dirv
    parts = [(*fill2d(parse_path(SHADES, 24)[0]), 0, 0.0)]
    sh = decal('JAKO_SHADES_up', parts, hair_bvh, lift=4.5, thick=3.0, mats=[M['shades']], cuts=3, origin_fn=org)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(sh.evaluated_get(dg), depsgraph=dg)
    bm = bmesh.new(); bm.from_mesh(me)
    for sx, xc in ((-1, 127.5), (1, 272.5)):
        o, d = org(xc, 198)
        h = hair_bvh.ray_cast(o, d, 6.0)
        if h[0] is None:
            continue
        p0 = h[0] + h[1] * U(3.0)
        pts = [p0 + dirv * U(3.0 * k) - h[1] * U(2.2 * k) for k in range(4)]   # short stub that dives into the hair
        stub = sweep('tmp_stub', pts, U(1.5), U(2.2), segs=8)
        bm.from_mesh(stub.data); bpy.data.objects.remove(stub, do_unlink=True)
    bm.to_mesh(me); bm.free()
    sh.modifiers.clear(); old = sh.data; sh.data = me; me.name = 'JAKO_SHADES_up'; bpy.data.meshes.remove(old)
    me.materials.clear(); me.materials.append(M['shades'])
    for p in me.polygons: p.material_index = 0
    me.shade_smooth()
    return sh, SHADES_UP_TILT
shades_up, shades_up_scale = build_shades_up()

# ------------------------------------------------------------------ neck + torso + collar + crest + number
def lathe(name, origin, axis_d, axis_u, axis_v, profile, segs=48, mats=(), ring_fn=None, top=None, bottom=None, ry_scale=1.0, coll_name='JAKO'):
    """profile: list of (h, r) in svg units along axis_d from origin. ring_fn(h, th, r)->r'"""
    rings, local = [], []
    for (h, r) in profile:
        ring = []
        for j in range(segs):
            th = 2 * math.pi * j / segs
            rr = ring_fn(h, th, r) if ring_fn else r
            u, v = rr * math.cos(th), rr * ry_scale * math.sin(th)
            ring.append(origin + axis_d * U(h) + axis_u * U(u) + axis_v * U(v))
            local.append((u, h, v))
        rings.append(ring)
    def cap(c):
        if c is None: return None
        if c == 'fan': return 'fan'
        h = c; return origin + axis_d * U(h)
    vv, ff = skin_rings(rings, top=cap(top), bottom=cap(bottom))
    ob = mesh_obj(name, vv, ff, coll_name, mats=mats)
    extra = len(vv) - len(local)
    caps = []
    if top is not None: caps.append((0, profile[0][0], 0))
    if bottom is not None: caps.append((0, profile[-1][0], 0))
    set_attr(ob, 'svg', local + caps[:extra])
    return ob

DOWN, RIGHT, BACK = Vector((0, 0, -1)), Vector((1, 0, 0)), Vector((0, 1, 0))
neck = lathe('JAKO_neck', Vector((0, U(4), Z(228))), DOWN, RIGHT, BACK,
             [(0, 12.0), (20, 12.5), (40, 13.0), (56, 13.5)], segs=32, mats=[M['skin']], top='fan', bottom='fan')
set_attr(neck, 'svg', [(0, 0, 1)] * len(neck.data.vertices))

torso_poly = parse_path(TORSO, 24)[0]
def build_torso():
    rings = []
    SEG = 96
    # rounded top (shoulder line -> neck)
    tops = [(270.0, 17.0, 15.0), (271.5, 25.0, 20.0), (273.5, 30.0, 23.0)]
    for (y, hw, d) in tops:
        rings.append(superellipse_ring(0, U(2), Z(y), U(hw), U(d), U(d), 2.6, SEG))
    ys = [276 + (397.5 - 276) * k / 70 for k in range(71)]
    for y in ys:
        s = spans(torso_poly, y)
        if s is None:
            continue
        hw = (s[1] - s[0]) / 2
        d = max(0.6 * hw, 24.0) + 3.0 * sstep(300, 340, y) * (1 - sstep(360, 397, y))   # slight tummy
        rings.append(superellipse_ring(X((s[0] + s[1]) / 2), U(2), Z(y), U(hw), U(d), U(d * 0.95), 2.8, SEG))
    v, f = skin_rings(rings, top=Vector((0, U(2), Z(269.0))), bottom='fan')
    ob = mesh_obj('JAKO_torso', v, f, mats=[M['jersey']])
    set_attr(ob, 'svg', [world_to_svg(p.co) for p in ob.data.vertices])
    return ob
torso = build_torso()
torso_bvh = bvh_of(torso)

def build_collar():
    pts, nors = [], []
    def hit_front(x, y):
        return torso_bvh.ray_cast(Vector((X(x), -3.0, Z(y))), Vector((0, 1, 0)), 6.0)
    def hit_back(x, y):
        return torso_bvh.ray_cast(Vector((X(x), 3.0, Z(y))), Vector((0, -1, 0)), 6.0)
    seq = []
    for q in resample([(222, 276.5), (200, 298), (178, 276.5)], 2.0):
        seq.append(('f', q.x, q.y))
    # over the left shoulder (screen-left = character's right), around the back, and back to the start
    seq_top = lambda x: [('t', x, k / 6) for k in range(1, 6)]
    seq += seq_top(178)
    for q in resample([(178, 276.0), (190, 281.5), (200, 283), (210, 281.5), (222, 276.0)], 2.0):
        seq.append(('b', q.x, q.y))
    seq += [('t', 222, 1 - k / 6) for k in range(1, 6)]
    yf = hit_front(178, 276.5)[0].y; yb = hit_back(178, 276.0)[0].y
    for kind, x, y in seq:
        if kind == 'f':
            h = hit_front(x, y)
        elif kind == 'b':
            h = hit_back(x, y)
        else:
            yy = yf + (yb - yf) * y
            h = torso_bvh.ray_cast(Vector((X(x), yy, 2.0)), Vector((0, 0, -1)), 3.0)
        if h[0] is not None:
            pts.append(h[0] + h[1] * U(1.2)); nors.append(h[1])
    pts.append(pts[0]); nors.append(nors[0])
    return sweep('JAKO_collar', pts, U(1.8), U(4.6), normals=nors, segs=12, mats=[M['maroon']], cap=False)
collar = build_collar()

def crest_parts():
    o = Vector((225, 318))
    def sh(d): return d
    sh_path = 'M-9,-11 L9,-11 L9,1 Q9,9 0,13 Q-9,9 -9,1 Z'
    def tr(poly, sc=1.0): return [(o.x + p[0] * sc, o.y + p[1] * sc) for p in poly]
    shield = parse_path(sh_path, 12)[0]
    parts = [(*fill2d(tr(shield, 1.2)), 0, 0.0), (*fill2d(tr(shield)), 1, 0.25)]
    def rect(x0, y0, x1, y1, mi, ex):
        return (*fill2d(tr([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])), mi, ex)
    parts += [rect(-8, -10, -0.5, -3.5, 2, 0.5), rect(-5.5, -10, -3.5, -3.5, 3, 0.7), rect(-8, -8, -0.5, -6, 3, 0.7),
              rect(0.5, -10, 8, -3.5, 4, 0.5), rect(2, -10, 3.6, -3.5, 3, 0.7), rect(5.4, -10, 7, -3.5, 3, 0.7),
              rect(-3, -3, 3, 11, 5, 0.5), (*fill2d(tr(ellipse(0, 4, 2.8, 2.8, 16))), 4, 0.8)]
    return parts
crest = decal('JAKO_crest', crest_parts(), torso_bvh, lift=0.3, thick=0.6,
              mats=[M['line'], M['navy'], M['crestwhite'], M['red'], M['gold'], M['maroon']], cuts=2)

def build_number():
    font_path = r'C:\Windows\Fonts\ariblk.ttf'
    objs = []
    for nm, off, mat, lift in (('JAKO_number_outline', U(1.2), M['maroon'], 0.4), ('JAKO_number', 0.0, M['navy'], 0.9)):
        cu = bpy.data.curves.new(nm, 'FONT'); cu.body = '10'
        if os.path.exists(font_path):
            cu.font = bpy.data.fonts.load(font_path, check_existing=True)
        cu.size = U(56) * 1.0; cu.align_x = 'CENTER'; cu.offset = off; cu.resolution_u = 6
        to = bpy.data.objects.new(nm + '_tmp', cu); coll('CUTTERS').objects.link(to)
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(to.evaluated_get(dg), depsgraph=dg)
        bpy.data.objects.remove(to, do_unlink=True)
        objs.append((nm, me, mat, lift))
    # centre: kit text baseline y=366, cap height ~40 -> centre ~346
    out = []
    ref = objs[1][1]
    ys_ = [v.co.y for v in ref.vertices]; xs_ = [v.co.x for v in ref.vertices]
    cy = (min(ys_) + max(ys_)) / 2; cx = (min(xs_) + max(xs_)) / 2
    for nm, me, mat, lift in objs:
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=3, use_grid_fill=False)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        for v in bm.verts:
            wx = -(v.co.x - cx); wz = Z(346) + (v.co.y - cy)
            h = torso_bvh.ray_cast(Vector((wx, 3.0, wz)), Vector((0, -1, 0)), 6.0)
            v.co = (h[0] + h[1] * U(lift)) if h[0] is not None else Vector((wx, 0.2, wz))
        for f in bm.faces:
            f.normal_update()
            if f.normal.y < 0: f.normal_flip()
        bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new(nm, me); coll('JAKO').objects.link(ob)
        me.materials.append(mat)
        so = ob.modifiers.new('solidify', 'SOLIDIFY'); so.thickness = U(0.8); so.offset = -1.0
        out.append(ob)
    return out
number = build_number()

# ------------------------------------------------------------------ arms
ARM_ANGLE = math.radians(14)
def arm_frame(sx):
    O = Vector((X(146 if sx < 0 else 254), 0, Z(290)))
    d = Vector((sx * math.sin(ARM_ANGLE), 0, -math.cos(ARM_ANGLE)))
    u = Vector((sx * math.cos(ARM_ANGLE), 0, math.sin(ARM_ANGLE)))
    return O, d, u, Vector((0, 1, 0))

arm_parts = {}
for sx in (-1, 1):
    side = 'R' if sx < 0 else 'L'
    O, d, u, v = arm_frame(sx)
    prof = [(-6 - 13 * math.cos(math.radians(a)), 17 * math.sin(math.radians(a))) for a in range(6, 90, 6)]
    prof += [(-6 + 36 * k / 10, 17 + 2 * k / 10) for k in range(11)]
    prof += [(30.5, 18.6), (30.8, 17.5), (29.5, 12.0)]
    sleeve = lathe('JAKO_sleeve_' + side, O, d, u * sx, v, prof, segs=48, mats=[M['sleeve']], top=-19.0, bottom='fan', ry_scale=0.92)
    fprof = [(18 + 8.5 - 8.5 * math.cos(math.radians(a)), 8.5 * math.sin(math.radians(a))) for a in range(10, 91, 10)]
    fprof += [(26 + 30 * k / 6, 8.5 - 0.4 * k / 6) for k in range(1, 7)]
    fprof += [(56 + 8 * math.sin(math.radians(a)), 8.1 * math.cos(math.radians(a))) for a in range(10, 90, 10)]
    forearm = lathe('JAKO_forearm_' + side, O, d, u * sx, v, fprof, segs=32, mats=[M['skin']], top=18.0, bottom=64.0)
    hc = O + d * U(68)
    rot = Matrix(((u.x * sx, v.x, -d.x), (u.y * sx, v.y, -d.y), (u.z * sx, v.z, -d.z)))
    hand = ellipsoid('JAKO_hand_' + side, hc, (U(11.0), U(9.8), U(11.8)), [M['skin']], rot=rot)
    thumb = ellipsoid('JAKO_thumb_' + side, O + d * U(63) + u * U(-6.5) + v * U(-6.0), (U(4.2), U(4.0), U(6.0)), [M['skin']], rot=rot)
    for ob in (forearm, hand, thumb):
        set_attr(ob, 'svg', [(0, 0, 1)] * len(ob.data.vertices))
    arm_parts[side] = dict(sleeve=sleeve, forearm=forearm, hand=hand, thumb=thumb, O=O, d=d, u=u)

def build_watch():
    O, d, u, v = arm_frame(1)
    prof = []
    for k in range(24):
        a = 2 * math.pi * k / 24
        prof.append((54 + 4.6 * spow(math.cos(a), 0.5), 9.9 + 1.0 * spow(math.sin(a), 0.5)))
    rings = []
    for (h, r) in prof:
        ring = []
        for j in range(40):
            th = 2 * math.pi * j / 40
            ring.append(O + d * U(h) + u * U(r * math.cos(th)) + v * U(r * 0.95 * math.sin(th)))
        rings.append(ring)
    rings.append(rings[0])
    vv, ff = skin_rings(rings[:-1])
    n = 40; L = len(prof)
    ff += [((L - 1) * n + j, (L - 1) * n + (j + 1) % n, (j + 1) % n, j) for j in range(n)]
    band = mesh_obj('JAKO_watch_band', vv, ff, mats=[M['watch']])
    rot = Matrix(((u.x, -v.x, -d.x), (u.y, -v.y, -d.y), (u.z, -v.z, -d.z)))
    rot = Matrix(((u.x, d.x, v.x), (u.y, d.y, v.y), (u.z, d.z, v.z)))
    face = ellipsoid('JAKO_watch_face', O + d * U(54) - v * U(10.6), (U(10.5), U(5.2), U(2.6)), [M['watch']], rot=rot, exp=4.0)
    lcd = ellipsoid('JAKO_watch_lcd', O + d * U(54) - v * U(12.6), (U(5.6), U(3.3), U(0.9)), [M['lcd']], rot=rot, exp=4.0)
    return [band, face, lcd]
watch = build_watch()

# ------------------------------------------------------------------ legs, hips, shoes
LEG_SPLAY = math.radians(2.5)
def leg_frame(sx):
    O = Vector((X(174 if sx < 0 else 226), 0, Z(388)))
    d = Vector((sx * math.sin(LEG_SPLAY), 0, -math.cos(LEG_SPLAY)))
    u = Vector((sx * math.cos(LEG_SPLAY), 0, sx * sx * math.sin(LEG_SPLAY)))
    return O, d, u, Vector((0, 1, 0))

def pant_r(h, th, r):
    k = sstep(16, 40, h) * (1 - sstep(74, 79, h))
    fold = 0.055 * k * math.sin(2 * math.pi * (h - 16) / 12.5 + 0.9 * math.sin(2 * th + h * 0.15))
    wob = 0.025 * sstep(0, 30, h) * math.sin(3 * th + h * 0.21)
    return r * (1 + fold + wob)
legs = {}
for sx in (-1, 1):
    side = 'R' if sx < 0 else 'L'
    O, d, u, v = leg_frame(sx)
    prof = [(-14 + 92 * k / 60, 21 + 7 * sstep(-14, 78, -14 + 92 * k / 60)) for k in range(61)]
    prof += [(78.6, 27.0), (78.4, 22.0)]
    pant = lathe('JAKO_pant_' + side, O, d, u, v, prof, segs=64, mats=[M['denim']], ring_fn=pant_r, top='fan', bottom=74.0, ry_scale=0.95)
    legs[side] = dict(pant=pant, O=O, d=d, u=u)
hips = ellipsoid('JAKO_hips', (0, U(1), Z(381)), (U(50), U(29), U(16)), [M['denim']])

def shoe_station(u):
    w = 21.5 * (0.78 + 0.22 * math.sin(math.pi * min(1.0, u * 1.1)))
    if u > 0.78: w *= math.sqrt(max(0.0, 1 - ((u - 0.78) / 0.22) ** 2))
    if u < 0.12: w *= math.sqrt(max(0.0, 1 - ((0.12 - u) / 0.12) ** 2))
    top = 62.0 + 13.0 * sstep(0.30, 0.62, u) + 4.0 * sstep(0.8, 1.0, u)
    return w, top
def build_shoes():
    out = []
    for sx in (-1, 1):
        side = 'R' if sx < 0 else 'L'
        O, d, uu, vv = leg_frame(sx)
        cx = (O + d * U(76)).x
        Yh, Yt = 24.0, -46.0
        rings = []
        NS = 40
        for k in range(1, NS):
            t = k / NS
            w, top = shoe_station(t)
            bot = 88.5
            hh = (bot - top) / 2; zc = (bot + top) / 2
            y = Yh + (Yt - Yh) * t
            ring = []
            for j in range(40):
                th = 2 * math.pi * j / 40
                c, s = math.cos(th), math.sin(th)
                ring.append(Vector((cx + U(w * spow(c, 2 / 3.0)), U(y), Z(388 + zc - hh * spow(s, 2 / (2.4 if s > 0 else 4.0))))))
            rings.append(ring)
        v_, f_ = skin_rings(rings, top='fan', bottom='fan')
        upper = mesh_obj('JAKO_shoe_' + side, v_, f_, mats=[M['shoe']])
        rings = []
        for k in range(1, NS):
            t = k / NS
            w, _ = shoe_station(t)
            y = Yh + 2.5 + (Yt - 2.5 - Yh - 2.5) * t
            ring = []
            for j in range(40):
                th = 2 * math.pi * j / 40
                c, s = math.cos(th), math.sin(th)
                ring.append(Vector((cx + U((w + 2.2) * spow(c, 2 / 4.0)), U(y), Z(388 + 92.6 - 4.4 * spow(s, 2 / 4.0)))))
            rings.append(ring)
        v_, f_ = skin_rings(rings, top='fan', bottom='fan')
        sole = mesh_obj('JAKO_sole_' + side, v_, f_, mats=[M['navy']])
        sb = bvh_of(upper)
        def side_origin(px, py, sx=sx, cx=cx):
            return Vector((cx + sx * 1.0, U(px), Z(388 + py))), Vector((-sx, 0, 0))
        # swoosh + mesh panel on the outer side (px = Y in units, py = svg height)
        sw = [(*stroke2d([(p.x, p.y) for p in resample(parse_path('M12,85 Q-8,74 -26,84', 12)[0], 1.5)], 3.2), 0, 0.0)]
        mp = [(*fill2d([(-30, 77.5), (-40, 78.5), (-41, 86), (-30, 86)]), 1, 0.0)]
        out += [upper, sole, decal('JAKO_shoe_deco_' + side, sw + mp, sb, lift=0.3, thick=0.5, mats=[M['navy'], M['mesh']], cuts=2, origin_fn=side_origin)]
    return out
shoes = build_shoes()

# ------------------------------------------------------------------ rig
def build_rig():
    arm = bpy.data.armatures.new('JAKO_rig'); rig = bpy.data.objects.new('JAKO_rig', arm)
    coll('JAKO').objects.link(rig)
    bpy.context.view_layer.objects.active = rig; rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm.edit_bones
    def bone(name, h, t, parent=None, connect=False):
        b = eb.new(name); b.head = h; b.tail = t
        if parent: b.parent = eb[parent]; b.use_connect = connect
        return b
    bone('root', (0, 0, 0), (0, U(-40), 0))
    bone('hips', (0, 0, Z(392)), (0, 0, Z(360)), 'root')
    bone('spine', (0, 0, Z(360)), (0, 0, Z(322)), 'hips', True)
    bone('chest', (0, 0, Z(322)), (0, 0, Z(280)), 'spine', True)
    bone('neck', (0, U(4), Z(280)), (0, U(4), Z(262)), 'chest')
    bone('head', (0, U(4), Z(262)), (0, U(4), Z(110)), 'neck', True)
    for sx in (-1, 1):
        s = 'R' if sx < 0 else 'L'
        O, d, u, v = arm_frame(sx)
        bone('upper_arm.' + s, O, O + d * U(36), 'chest')
        bone('forearm.' + s, O + d * U(36), O + d * U(60), 'upper_arm.' + s, True)
        bone('hand.' + s, O + d * U(60), O + d * U(80), 'forearm.' + s, True)
        O, d, u, v = leg_frame(sx)
        bone('thigh.' + s, O, O + d * U(36), 'hips')
        bone('shin.' + s, O + d * U(36), O + d * U(70), 'thigh.' + s, True)
        fh = O + d * U(76)
        bone('foot.' + s, Vector((fh.x, 0, Z(470))), Vector((fh.x, U(-40), Z(478))), 'shin.' + s)
    for b in eb:
        b.roll = 0.0
    bpy.ops.object.mode_set(mode='OBJECT')
    rig.show_in_front = True
    return rig
rig = build_rig()

def bind(ob, weights):
    """weights: {bone: 1.0 | callable(svg_local)->w} using vertex positions (world rest) or the 'svg' attribute."""
    ob.parent = rig
    ob.matrix_parent_inverse = rig.matrix_world.inverted()
    for bname, w in weights.items():
        vg = ob.vertex_groups.new(name=bname)
        if not callable(w):
            vg.add(list(range(len(ob.data.vertices))), w, 'REPLACE')
        else:
            for vx in ob.data.vertices:
                ww = w(vx.co)
                if ww > 1e-4:
                    vg.add([vx.index], min(1.0, ww), 'REPLACE')
    mo = ob.modifiers.new('rig', 'ARMATURE'); mo.object = rig

head_group = [head, hair, shades_on, shades_up] + [e for e in ears if e] + strand_objs + ahoge_objs + list(face_objs.values())
for ob in head_group:
    bind(ob, {'head': 1.0})
bind(neck, {'neck': 1.0})
def tz(co): return 485.0 - co.z / S
def w_hips(c): return sstep(372, 394, tz(c))
def w_chest(c): return (1 - w_hips(c)) * (1 - sstep(300, 336, tz(c)))
bind(torso, {'hips': w_hips, 'chest': w_chest, 'spine': lambda c: max(0.0, 1 - w_hips(c) - w_chest(c))})
for ob in [collar, crest] + number:
    bind(ob, {'chest': 1.0})
for sx in (-1, 1):
    s = 'R' if sx < 0 else 'L'
    ap = arm_parts[s]
    O, d = ap['O'], ap['d']
    def hpos(c, O=O, d=d): return (c - O).dot(d) / S
    bind(ap['sleeve'], {'upper_arm.' + s: 1.0})
    bind(ap['forearm'], {'upper_arm.' + s: lambda c, h=hpos: 1 - sstep(30, 42, h(c)), 'forearm.' + s: lambda c, h=hpos: sstep(30, 42, h(c))})
    bind(ap['hand'], {'hand.' + s: 1.0}); bind(ap['thumb'], {'hand.' + s: 1.0})
    lg = legs[s]
    def lpos(c, O=lg['O'], d=lg['d']): return (c - O).dot(d) / S
    bind(lg['pant'], {'thigh.' + s: lambda c, h=lpos: 1 - sstep(24, 46, h(c)), 'shin.' + s: lambda c, h=lpos: sstep(24, 46, h(c))})
for ob in watch:
    bind(ob, {'forearm.L': 1.0})
bind(hips, {'hips': 1.0})
for ob in shoes:
    side = ob.name[-1]
    bind(ob, {'foot.' + side: 1.0})

# ------------------------------------------------------------------ face-state controls (custom props + drivers)
def prop(name, val, lo, hi, desc):
    rig[name] = val
    ui = rig.id_properties_ui(name); ui.update(min=lo, max=hi, soft_min=lo, soft_max=hi, description=desc)
prop('eyes', 0, 0, 3, '0 neutral (sleepy), 1 blink, 2 happy, 3 surprised')
prop('mouth', 0, 0, 3, '0 closed, 1 open (talk), 2 happy, 3 surprised')
prop('shades', 0, 0, 2, '0 off, 1 on the eyes, 2 pushed up on the head')
prop('blush', 0.0, 0.0, 1.0, 'extra cheek blush (happy eyes add 0.85 automatically)')

def drive_hide(ob, expr, var_names):
    for path in ('hide_render', 'hide_viewport'):
        fc = ob.driver_add(path); dr = fc.driver; dr.type = 'SCRIPTED'
        for vn in var_names:
            var = dr.variables.new(); var.name = vn; var.type = 'SINGLE_PROP'
            var.targets[0].id = rig; var.targets[0].data_path = '["%s"]' % vn
        dr.expression = expr
for k, n in enumerate(['neutral', 'blink', 'happy', 'surprised']):
    drive_hide(face_objs['EYES_' + n], 'eyes != %d' % k, ['eyes'])
for k, n in enumerate(['closed', 'open', 'happy', 'surprised']):
    drive_hide(face_objs['MOUTH_' + n], 'mouth != %d' % k, ['mouth'])
drive_hide(face_objs['BROWS_neutral'], 'eyes >= 2', ['eyes'])
drive_hide(face_objs['BROWS_happy'], 'eyes != 2', ['eyes'])
drive_hide(face_objs['BROWS_surprised'], 'eyes != 3', ['eyes'])
drive_hide(shades_on, 'shades != 1', ['shades'])
drive_hide(shades_up, 'shades != 2', ['shades'])
bn = M['skin'].node_tree.nodes['BLUSH']
fc = bn.outputs[0].driver_add('default_value'); dr = fc.driver; dr.type = 'SCRIPTED'
for vn in ('blush', 'eyes'):
    var = dr.variables.new(); var.name = vn; var.type = 'SINGLE_PROP'
    var.targets[0].id_type = 'OBJECT'; var.targets[0].id = rig; var.targets[0].data_path = '["%s"]' % vn
dr.expression = 'max(blush, 0.85 if eyes == 2 else 0.0)'

# ------------------------------------------------------------------ studio: cyclorama, lights, world, camera
def build_studio():
    prof = [(-4.0, 0.0)]
    R = 1.2
    for k in range(1, 13):
        a = math.pi / 2 * k / 12
        prof.append((2.0 + R * math.sin(a), R - R * math.cos(a)))
    prof.append((2.0 + R, 4.5))
    verts, faces = [], []
    for (y, z) in prof:
        verts += [Vector((-5, y, z)), Vector((5, y, z))]
    for k in range(len(prof) - 1):
        faces.append((2 * k, 2 * k + 1, 2 * k + 3, 2 * k + 2))
    m = principled('MAT_backdrop', hexc('#e7dfd2'), 0.95, spec=0.2)
    ob = mesh_obj('STUDIO_cyclorama', verts, faces, 'STUDIO', mats=[m])
    def area(name, loc, size, power, color, target=(0, 0, 0.75)):
        ld = bpy.data.lights.new(name, 'AREA'); ld.size = size; ld.energy = power; ld.color = color; ld.shape = 'DISK'
        lo = bpy.data.objects.new(name, ld); coll('STUDIO').objects.link(lo); lo.location = loc
        dvec = Vector(target) - Vector(loc); lo.rotation_euler = dvec.to_track_quat('-Z', 'Y').to_euler()
        return lo
    area('KEY', (-1.9, -2.6, 2.6), 2.2, 230, (1.0, 0.95, 0.88))
    area('FILL', (2.4, -2.0, 1.4), 2.8, 70, (0.88, 0.93, 1.0))
    area('RIM', (1.2, 2.2, 2.6), 1.4, 260, (1.0, 0.96, 0.92), (0, 0, 1.0))
    area('RIM2', (-1.6, 2.0, 2.0), 1.2, 130, (0.92, 0.95, 1.0), (0, 0, 1.0))
    w = bpy.data.worlds.new('WORLD'); SC.world = w; w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs[0].default_value = hexc('#d9d4cc'); bg.inputs[1].default_value = 0.32
    cd = bpy.data.cameras.new('CAM'); cam = bpy.data.objects.new('CAM', cd); coll('STUDIO').objects.link(cam)
    cd.lens = 70; cam.location = (0, -5.2, 0.78); cam.rotation_euler = (math.radians(90), 0, 0)
    SC.camera = cam
build_studio()

def render_setup():
    r = SC.render
    for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
        try:
            r.engine = eng; break
        except TypeError:
            pass
    r.resolution_x, r.resolution_y = 864, 1080
    e = SC.eevee
    e.taa_render_samples = 64
    for k, v in (('use_raytracing', True), ('use_shadows', True), ('shadow_ray_count', 2), ('shadow_step_count', 8),
                 ('use_gtao', True), ('fast_gi_method', 'GLOBAL_ILLUMINATION')):
        try: setattr(e, k, v)
        except Exception: pass
    vs = SC.view_settings
    try: vs.view_transform = 'AgX'
    except TypeError: pass
    looks = [i.identifier for i in bpy.types.ColorManagedViewSettings.bl_rna.properties['look'].enum_items] if False else None
    for lk in ('AgX - Medium High Contrast', 'Medium High Contrast'):
        try: vs.look = lk; break
        except TypeError: pass
    vs.exposure = -0.35
render_setup()

for o in list(coll('CUTTERS').objects):
    bpy.data.objects.remove(o, do_unlink=True)
bpy.data.collections.remove(coll('CUTTERS'))

SC['jako_info'] = 'svg unit = %.4f m; shades_up scale %.2f' % (S, shades_up_scale)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print('SAVED', OUT, 'objects', len(bpy.data.objects), 'shades_up_scale', shades_up_scale)
