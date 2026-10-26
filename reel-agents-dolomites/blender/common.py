# Shared helpers + layout for the "Who are they?" Dolomites reel.
# Every build script does:  import common, importlib; importlib.reload(common); from common import *
# Coordinates: Blender Z-up. North = +Y (Sassolungo), the campus/office sits at the origin.
# jako-hq.html (Three.js, Y-up) maps as  blender(x, y, z) = three(x, -z, y).
import bpy, bmesh, math, os, random
import numpy as np
from mathutils import Vector, Matrix, Euler, Quaternion

ROOT = r'C:\Users\acer\Downloads\jako-frames\reel-agents-dolomites'
BL = os.path.join(ROOT, 'blender')
TEX = os.path.join(BL, 'tex')
PREV = os.path.join(ROOT, 'previews')
for _d in (TEX, PREV):
    os.makedirs(_d, exist_ok=True)

FPS = 24

# ---------------------------------------------------------------- timing from the finished audio (audio/timeline.json)
# timeline.json frames are 0-based with exclusive ends; Blender frames here are 1-based:
#   blender_frame = json_frame + 1, a shot [start, end) -> Blender (start+1 .. end) inclusive.
import json as _json
TIMELINE = os.path.join(ROOT, 'audio', 'timeline.json')
with open(TIMELINE, 'r', encoding='utf-8') as _f:
    TL = _json.load(_f)
FRAME_START, FRAME_END = 1, int(TL['total_frames'])          # 1..1190 (49.57 s)


def _sec(s):
    return int(round(s * FPS)) + 1


SFX = {}
for _s in TL['sfx']:
    SFX[_s['id']] = _sec(_s['start_s'])
CUES = {l['id']: l['speech_start_frame'] + 1 for l in TL['lines']}       # speech onset (hops, acting)
CUE_END = {l['id']: l['speech_end_frame'] + 1 for l in TL['lines']}

SHOTS = []          # (id, first frame, last frame, camera)
for _sh in TL['shots']:
    n = _sh['shot']; a0, a1 = _sh['start_frame'] + 1, _sh['end_frame']
    if n == 4:
        for _sub, _sid in zip(_sh['subshots'], 'abcde'):
            SHOTS.append(('04' + _sid, _sub['start_frame'] + 1, _sub['end_frame'], 'CAM_04' + _sid))
    elif n == 11:
        # 4 cuts locked to the SFX: pops (antennas) -> footsteps (run) -> bloops (screens)
        p3, p4 = SFX['pop_03'], SFX['pop_04']
        run0 = SFX['footsteps_grass_run'] + 3
        scr0 = SFX['bloop_screen_02_chart'] - 1
        SHOTS += [('11a', a0, p3 + 2, 'CAM_11a'), ('11b', p3 + 3, run0 - 1, 'CAM_11b'),
                  ('11c', run0, scr0 - 1, 'CAM_11c'), ('11d', scr0, a1, 'CAM_11d')]
    else:
        SHOTS.append(('%02d' % n, a0, a1, 'CAM_%02d' % n))
SHOT = {s[0]: s for s in SHOTS}

# agent order of the pops / screen bloops in the mix
PERK = {aid: SFX['pop_%02d' % (i + 1)] for i, aid in enumerate(['planner', 'analyst', 'caption-writer', 'video-director', 'trend-scout'])}
SCREEN_ON = {'planner': SFX['bloop_screen_01_calendar'], 'analyst': SFX['bloop_screen_02_chart'], 'caption-writer': SFX['bloop_screen_03_text'],
             'video-director': SFX['bloop_screen_04_timeline'], 'trend-scout': SFX['bloop_screen_05_grid']}
T_CHILL_END = SHOT['11c'][1] - 1     # last frame of the chill poses
T_RUN0 = SHOT['11c'][1]              # agents start running (cut to the wide office)
MIX_WAV = os.path.join(ROOT, 'audio', 'mix_preview.wav')

# ---------------------------------------------------------------- layout (Blender coords)
DECK = 0.3
SPA = 0.2
JAKO_A = (0.8, -18.5)        # meadow spot at the end of the stone path, Jako faces north
CLAUDE_A = (1.42, -18.2)     # at Jako's right foot
DOOR = (0.0, -5.15)          # office doorway (on the step) for shots 12-13
FIRE = (-10.0, 33.0)         # campfire by the cliff edge (shot 14)
HX, HZ = 40.0, -430.0        # Sassolungo massif centre in three coords -> blender (40, 430)
MASSIF_SCALE = 1.35          # a bit taller than jako-hq for the vertical frame

AGENTS = [
    dict(id='analyst', color='#3D8BFF', screen='chart', monitor=True),
    dict(id='caption-writer', color='#FF8A3D', screen='text', monitor=False),
    dict(id='planner', color='#F2B90F', screen='calendar', monitor=False),
    dict(id='video-director', color='#9B5CFF', screen='timeline', monitor=True),
    dict(id='trend-scout', color='#2FBF66', screen='grid', monitor=False),
]
AG = {a['id']: a for a in AGENTS}
# chill spots before "Come to the office!"
CHILL = {
    'planner': (-6.2, -31.8),         # hammock (along X)
    'analyst': (0.2, -29.4),          # lying in the grass
    'caption-writer': (-2.9, -35.2),  # bench
    'video-director': (12.5, 30.5),   # tripod, filming the pink peaks
    'trend-scout': (3.5, 37.0),       # rock at the cliff edge, binoculars
}


def station(i):
    """Desk i on the arc (jako-hq buildAgent). Returns (x, y, rot_z). Agent sits north of desk facing south."""
    th = (i - 2) * 0.27
    return (math.sin(th) * 10.0, math.cos(th) * 10.0 - 8.0, -th)


# ---------------------------------------------------------------- colours
def _s2l(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexc(h, a=1.0):
    h = h.lstrip('#')
    return tuple(_s2l(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4)) + (a,)


def hex3(h):
    return hexc(h)[:3]


def lerpc(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))


# ---------------------------------------------------------------- noise (port of jako-hq.html)
def hash2(x, z):
    s = np.sin(x * 127.1 + z * 311.7) * 43758.5453
    return s - np.floor(s)


def vnoise(x, z):
    x = np.asarray(x, dtype=np.float64); z = np.asarray(z, dtype=np.float64)
    xi = np.floor(x); zi = np.floor(z); xf = x - xi; zf = z - zi
    u = xf * xf * (3 - 2 * xf); v = zf * zf * (3 - 2 * zf)
    a = hash2(xi, zi); b = hash2(xi + 1, zi); c = hash2(xi, zi + 1); d = hash2(xi + 1, zi + 1)
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v


def fbm(x, z):
    s = 0.0; a = 0.5; f = 1.0
    for _ in range(4):
        s = s + a * vnoise(x * f, z * f); f *= 2; a *= 0.5
    return s / 0.9375


def ridged(x, z):
    s = 0.0; a = 0.5; f = 1.0
    for _ in range(5):
        n = 1 - np.abs(vnoise(x * f, z * f) * 2 - 1)
        s = s + a * n * n; f *= 2.03; a *= 0.5
    return s / 0.97


def ss(a, b, x):
    t = np.clip((np.asarray(x, dtype=np.float64) - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


PADS = [(11, 42, -17, 11), (-31, -11, -11, 13)]   # three coords x0,x1,z0,z1 (courts, lounge)


def pad_mask(x, z):
    m = np.zeros_like(np.asarray(x, dtype=np.float64))
    for x0, x1, z0, z1 in PADS:
        dx = np.maximum(np.maximum(x0 - x, 0), x - x1)
        dz = np.maximum(np.maximum(z0 - z, 0), z - z1)
        m = np.maximum(m, 1 - ss(0, 8, np.hypot(dx, dz)))
    return m


def hero_mask(x, z):
    return 1 - ss(170, 320, np.hypot(x - HX, (z - HZ) * 1.4))


def cliff_edge(xb):
    """Blender-Y of the cliff lip north of the campus (new vs jako-hq: gives the 'cliff edge' + a foggy valley)."""
    xb = np.asarray(xb, dtype=np.float64)
    return 40.0 + 5.0 * np.sin(xb * 0.045) + 4.0 * (vnoise(xb * 0.04 + 2.0, 1.3) - 0.5)


def base_h3(x, z):
    """Terrain height, three coords (x, z)."""
    x = np.asarray(x, dtype=np.float64); z = np.asarray(z, dtype=np.float64)
    d = np.hypot(x, z + 0.5)
    near = ss(12, 55, d) * (1 - pad_mask(x, z))
    h = ((fbm(x * 0.012 + 3, z * 0.012 + 7) - 0.45) * 12 * near
         + np.sin(x * 0.021 + 1) * np.cos(z * 0.017) * 2.5 * near
         + ss(60, 300, d) * 14)
    ring = ss(330, 500, d)
    r = ridged(x * 0.0065 + 11, z * 0.0065 - 4)
    h = h + ring * r * r * 95 * (1 - hero_mask(x, z) * 0.9)
    # valley + cliff between the campus and Sassolungo
    yb = -z
    e0 = cliff_edge(x)
    drop = 44.0 * ss(e0, e0 + 16.0, yb) * (1 - ss(230, 330, yb))
    h = h - drop * (1 - hero_mask(x, z))
    # keep the cliff-top meadow flat-ish
    return h


def ground_h(xb, yb):
    """Terrain height at blender (x, y). Scalar in -> float out."""
    return float(base_h3(np.array([xb], dtype=np.float64), np.array([-yb], dtype=np.float64))[0])


PEAKS = [(-100, 10, 70, 34), (-62, 0, 108, 40), (-34, 12, 92, 26), (-10, -6, 99, 30), (16, 10, 82, 26), (38, -2, 72, 24)]


def massif(lx, lz):
    rock = np.zeros_like(lx)
    for px, pz, H, r in PEAKS:
        d = np.hypot(lx - px, (lz - pz) * 1.3); p = 1 - d / r
        rock = np.maximum(rock, np.where(p > 0, H * ss(0, 0.42, p) * (0.72 + 0.28 * p), 0.0))
    t = np.minimum(1, (lx - 50) / 150)
    slab = (90 - 62 * t) * ss(0, 10, lx - 48) * ss(0, 9, 24 - lz) * ss(0, 30, lz + 48) * (1 - ss(0.9, 1, t))
    rock = np.where(lx > 40, np.maximum(rock, slab), rock)
    w = ss(5, 40, rock)
    add = ((ridged(lx * 0.2 + vnoise(lz * 0.05, lx * 0.01) * 3, lz * 0.035) - 0.45) * 10 * w
           + (vnoise(lx * 0.12, lz * 0.12) - 0.5) * 14 * ss(40, 100, rock))
    rock = np.where(rock > 4, rock + add, rock)
    sk1 = 1 - np.hypot(lx / 175, (lz - 4) / 72)
    sk2 = 1 - np.hypot((lx - 115) / 120, lz / 62)
    scree = np.maximum(np.where(sk1 > 0, 36 * np.power(np.maximum(sk1, 0), 1.4), 0),
                       np.where(sk2 > 0, 26 * np.power(np.maximum(sk2, 0), 1.4), 0)) + (vnoise(lx * 0.08, lz * 0.08) - 0.5) * 3
    return np.maximum(rock, scree)


# ---------------------------------------------------------------- collections
def ensure_coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
    par = parent or bpy.context.scene.collection
    if c.name not in [ch.name for ch in par.children]:
        try:
            par.children.link(c)
        except Exception:
            pass
    return c


def purge_orphans():
    for coll in (bpy.data.meshes, bpy.data.curves, bpy.data.lights, bpy.data.cameras):
        for b in list(coll):
            if b.users == 0:
                coll.remove(b)
    for ng in list(bpy.data.node_groups):
        if ng.users == 0 and ng.name.startswith('GN_'):
            bpy.data.node_groups.remove(ng)


def reset_coll(name, parent=None):
    """Idempotent rebuild: delete everything inside collection `name` (recursively) and return it empty."""
    c = bpy.data.collections.get(name)
    if c is not None:
        subs = list(c.children_recursive)
        for ch in subs + [c]:
            for o in list(ch.objects):
                bpy.data.objects.remove(o, do_unlink=True)
        for ch in reversed(subs):
            bpy.data.collections.remove(ch)
    purge_orphans()
    return ensure_coll(name, parent)


def link(o, coll):
    coll.objects.link(o)
    return o


# ---------------------------------------------------------------- materials
def new_mat(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (600, 0)
    return m, nt, out


def setin(node, names, val):
    if isinstance(names, str):
        names = [names]
    for n in names:
        if n in node.inputs:
            try:
                node.inputs[n].default_value = val
                return True
            except Exception:
                pass
    return False


def bsdf_node(nt, color=(0.8, 0.8, 0.8, 1), rough=0.6, metal=0.0, coat=0.0, coat_rough=0.2, sss=0.0,
              emission=None, estr=0.0, alpha=1.0, sheen=0.0, spec=0.5):
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    setin(b, 'Base Color', color)
    setin(b, 'Roughness', rough)
    setin(b, 'Metallic', metal)
    setin(b, ['Specular IOR Level', 'Specular'], spec)
    if coat:
        setin(b, ['Coat Weight', 'Clearcoat'], coat); setin(b, ['Coat Roughness', 'Clearcoat Roughness'], coat_rough)
    if sss:
        setin(b, ['Subsurface Weight', 'Subsurface'], sss)
        setin(b, 'Subsurface Radius', (0.6, 0.25, 0.15))
        setin(b, 'Subsurface Scale', 0.03)
    if sheen:
        setin(b, ['Sheen Weight', 'Sheen'], sheen)
    if emission is not None:
        setin(b, ['Emission Color', 'Emission'], emission); setin(b, 'Emission Strength', estr)
    if alpha < 1.0:
        setin(b, 'Alpha', alpha)
    return b


def pbr(name, color, rough=0.6, **kw):
    m, nt, out = new_mat(name)
    if isinstance(color, str):
        color = hexc(color)
    b = bsdf_node(nt, color, rough, **kw)
    nt.links.new(b.outputs[0], out.inputs[0])
    m.diffuse_color = color
    return m


def emit_mat(name, color, strength=5.0):
    m, nt, out = new_mat(name)
    if isinstance(color, str):
        color = hexc(color)
    e = nt.nodes.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = color; e.inputs['Strength'].default_value = strength
    nt.links.new(e.outputs[0], out.inputs[0])
    return m


def mix_rgb(nt, fac, a, b, blend='MIX'):
    """ShaderNodeMix in RGBA mode. fac/a/b can be sockets or values. Returns output socket."""
    n = nt.nodes.new('ShaderNodeMix')
    n.data_type = 'RGBA'
    n.blend_type = blend
    for idx, v in ((0, fac), (6, a), (7, b)):
        if hasattr(v, 'is_output'):
            nt.links.new(v, n.inputs[idx])
        else:
            n.inputs[idx].default_value = v
    return n.outputs[2]


def math_node(nt, op, a, b=None, c=None, clamp=False):
    n = nt.nodes.new('ShaderNodeMath'); n.operation = op; n.use_clamp = clamp
    for i, v in enumerate((a, b, c)):
        if v is None:
            continue
        if hasattr(v, 'is_output'):
            nt.links.new(v, n.inputs[i])
        else:
            n.inputs[i].default_value = v
    return n.outputs[0]


def ramp(nt, fac, stops, interp='LINEAR'):
    """stops: list of (pos, rgba). Returns color output socket."""
    r = nt.nodes.new('ShaderNodeValToRGB')
    cr = r.color_ramp
    cr.interpolation = interp
    stops = sorted(stops, key=lambda s: s[0])
    while len(cr.elements) > 1:
        cr.elements.remove(cr.elements[-1])
    cr.elements[0].position = stops[0][0]; cr.elements[0].color = stops[0][1]
    for p, c in stops[1:]:
        el = cr.elements.new(p); el.color = c
    if hasattr(fac, 'is_output'):
        nt.links.new(fac, r.inputs[0])
    else:
        r.inputs[0].default_value = fac
    return r.outputs[0]


def scale_color(nt, col, fac):
    n = nt.nodes.new('ShaderNodeVectorMath'); n.operation = 'SCALE'
    nt.links.new(col, n.inputs[0]) if hasattr(col, 'is_output') else setattr(n.inputs[0], 'default_value', col[:3])
    if hasattr(fac, 'is_output'):
        nt.links.new(fac, n.inputs['Scale'])
    else:
        n.inputs['Scale'].default_value = fac
    return n.outputs[0]


def set_alpha_mode(m, blended=False):
    try:
        m.surface_render_method = 'BLENDED' if blended else 'DITHERED'
    except Exception:
        try:
            m.blend_method = 'BLEND' if blended else 'HASHED'
        except Exception:
            pass


# ---------------------------------------------------------------- meshes
def mesh_from(name, verts, faces, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.validate(); me.update()
    if smooth:
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    return me


def grid_mesh(name, xs, ys, Z):
    """Fast quad grid. Z has shape (len(ys), len(xs)). Normals up."""
    nx, ny = len(xs), len(ys)
    X, Y = np.meshgrid(xs, ys)
    verts = np.stack([X.ravel(), Y.ravel(), np.asarray(Z).ravel()], 1).astype(np.float32)
    idx = np.arange(nx * ny, dtype=np.int64).reshape(ny, nx)
    a = idx[:-1, :-1].ravel(); b = idx[:-1, 1:].ravel(); c = idx[1:, 1:].ravel(); d = idx[1:, :-1].ravel()
    faces = np.stack([a, b, c, d], 1).astype(np.int32)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(verts)); me.vertices.foreach_set('co', verts.ravel())
    nf = len(faces)
    me.loops.add(nf * 4); me.loops.foreach_set('vertex_index', faces.ravel())
    me.polygons.add(nf); me.polygons.foreach_set('loop_start', (np.arange(nf) * 4).astype(np.int32))
    try:
        me.polygons.foreach_set('loop_total', np.full(nf, 4, np.int32))
    except Exception:
        pass
    me.update(calc_edges=True)
    me.validate()
    me.polygons.foreach_set('use_smooth', np.ones(nf, dtype=bool))
    return me


def obj(name, data, coll, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), mats=()):
    o = bpy.data.objects.new(name, data)
    coll.objects.link(o)
    if parent is not None:
        o.parent = parent
        o.matrix_parent_inverse = Matrix.Identity(4)
    o.location = loc; o.rotation_euler = rot; o.scale = scale
    if data is not None and hasattr(data, 'materials'):
        for m in mats:
            data.materials.append(m)
    return o


def empty(name, coll, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), size=0.2, kind='PLAIN_AXES'):
    o = obj(name, None, coll, parent, loc, rot)
    o.empty_display_type = kind; o.empty_display_size = size
    return o


def _bm_to_mesh(bm, name, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    if smooth:
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    return me


def m_sphere(name, r=(1, 1, 1), center=(0, 0, 0), seg=32, rings=16, smooth=True):
    if not isinstance(r, (tuple, list)):
        r = (r, r, r)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * r[0] + center[0], v.co.y * r[1] + center[1], v.co.z * r[2] + center[2]))
    return _bm_to_mesh(bm, name, smooth)


def m_box(name, size=(1, 1, 1), center=(0, 0, 0), smooth=False):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0] + center[0], v.co.y * size[1] + center[1], v.co.z * size[2] + center[2]))
    return _bm_to_mesh(bm, name, smooth)


def m_cyl(name, r1, r2, h, center=(0, 0, 0), seg=24, smooth=True, caps=True):
    """Cylinder/cone along Z, centred on `center`."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, cap_tris=False, segments=seg, radius1=r1, radius2=r2, depth=h)
    for v in bm.verts:
        v.co += Vector(center)
    me = _bm_to_mesh(bm, name, smooth)
    return me


def m_torus(name, R, r, arc=2 * math.pi, seg=32, rseg=10, start=0.0):
    """Torus (or arc of one) in the XZ plane around the Y axis... returned in XY plane, axis Z."""
    verts, faces = [], []
    closed = abs(arc - 2 * math.pi) < 1e-6
    nseg = seg if closed else seg + 1
    for i in range(nseg):
        a = start + arc * i / seg
        cx, cy = math.cos(a) * R, math.sin(a) * R
        for j in range(rseg):
            b = 2 * math.pi * j / rseg
            rr = R + math.cos(b) * r
            verts.append((math.cos(a) * rr, math.sin(a) * rr, math.sin(b) * r))
    for i in range(seg):
        i2 = (i + 1) % nseg if closed else i + 1
        for j in range(rseg):
            j2 = (j + 1) % rseg
            faces.append((i * rseg + j, i2 * rseg + j, i2 * rseg + j2, i * rseg + j2))
    return mesh_from(name, verts, faces)


def m_tube(name, pts, radii, rseg=10, caps=True):
    """Tube along a polyline pts (list of Vector-like) with per-point radius."""
    pts = [Vector(p) for p in pts]
    if not isinstance(radii, (list, tuple)):
        radii = [radii] * len(pts)
    verts, faces = [], []
    n = len(pts)
    prev_side = None
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        ref = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
        side = t.cross(ref).normalized() if prev_side is None else (prev_side - t * prev_side.dot(t)).normalized()
        prev_side = side
        up = side.cross(t).normalized()
        for j in range(rseg):
            b = 2 * math.pi * j / rseg
            verts.append(tuple(p + (side * math.cos(b) + up * math.sin(b)) * radii[i]))
    for i in range(n - 1):
        for j in range(rseg):
            j2 = (j + 1) % rseg
            faces.append((i * rseg + j, i * rseg + j2, (i + 1) * rseg + j2, (i + 1) * rseg + j))
    if caps:
        c0 = len(verts); verts.append(tuple(pts[0]))
        c1 = len(verts); verts.append(tuple(pts[-1]))
        for j in range(rseg):
            j2 = (j + 1) % rseg
            faces.append((c0, j2, j))
            faces.append((c1, (n - 1) * rseg + j, (n - 1) * rseg + j2))
    return mesh_from(name, verts, faces)


def superellipse(rx, ry, n=3.0, seg=32):
    pts = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        c, s = math.cos(a), math.sin(a)
        x = rx * math.copysign(abs(c) ** (2.0 / n), c)
        y = ry * math.copysign(abs(s) ** (2.0 / n), s)
        pts.append((x, y))
    return pts


def m_loft(name, sections, seg=32, n=3.0, cap_bottom=True, cap_top=True, offsets=None):
    """Loft rounded-rect sections along Z. sections: list of (z, rx, ry[, cx, cy])."""
    verts, faces = [], []
    for s in sections:
        z, rx, ry = s[0], s[1], s[2]
        cx = s[3] if len(s) > 3 else 0.0
        cy = s[4] if len(s) > 4 else 0.0
        for (x, y) in superellipse(rx, ry, n, seg):
            verts.append((x + cx, y + cy, z))
    ns = len(sections)
    for i in range(ns - 1):
        for j in range(seg):
            j2 = (j + 1) % seg
            faces.append((i * seg + j, i * seg + j2, (i + 1) * seg + j2, (i + 1) * seg + j))
    if cap_bottom:
        c = len(verts); s0 = sections[0]
        verts.append((s0[3] if len(s0) > 3 else 0, s0[4] if len(s0) > 4 else 0, s0[0]))
        for j in range(seg):
            faces.append((c, (j + 1) % seg, j))
    if cap_top:
        c = len(verts); s1 = sections[-1]
        verts.append((s1[3] if len(s1) > 3 else 0, s1[4] if len(s1) > 4 else 0, s1[0]))
        for j in range(seg):
            faces.append((c, (ns - 1) * seg + j, (ns - 1) * seg + (j + 1) % seg))
    return mesh_from(name, verts, faces)


def m_rock(name, r=1.0, center=(0, 0, 0), seed=0, squash=0.7, rough=0.25):
    rnd = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    off = (rnd.random() * 10, rnd.random() * 10)
    for v in bm.verts:
        n = v.co.normalized()
        k = 1 + rough * (math.sin(n.x * 3.1 + off[0]) * math.cos(n.y * 2.7 + off[1]) + 0.5 * math.sin(n.z * 5.3 + off[0]))
        v.co = Vector((n.x * r * k * (1 + rnd.random() * 0.08), n.y * r * k, n.z * r * k * squash)) + Vector(center)
    return _bm_to_mesh(bm, name, smooth=True)


def mod_bevel(o, w=0.01, seg=2):
    m = o.modifiers.new('Bevel', 'BEVEL'); m.width = w; m.segments = seg
    try:
        m.limit_method = 'ANGLE'
    except Exception:
        pass
    return m


def mod_subsurf(o, lv=1, render=None):
    m = o.modifiers.new('Subsurf', 'SUBSURF'); m.levels = lv; m.render_levels = lv if render is None else render
    return m


def mod_solidify(o, t=0.01, offset=1.0):
    m = o.modifiers.new('Solidify', 'SOLIDIFY'); m.thickness = t; m.offset = offset
    return m


def aim(o, target, roll=0.0):
    """Point object -Z at target (cameras / lights), Y up."""
    d = Vector(target) - o.location
    q = d.to_track_quat('-Z', 'Y')
    e = q.to_euler()
    if roll:
        e.rotate_axis('Z', roll)
    o.rotation_euler = e
    return o


def look_rot(src, target, roll=0.0):
    d = Vector(target) - Vector(src)
    e = d.to_track_quat('-Z', 'Y').to_euler()
    if roll:
        e.rotate_axis('Z', math.radians(roll))
    return e


# ---------------------------------------------------------------- animation
def K(target, prop, f, val=None, index=-1):
    if val is not None:
        setattr(target, prop, val)
    target.keyframe_insert(prop, frame=f, index=index)


def KO(o, f, loc=None, rot=None, scl=None):
    """Key an object transform. rot in degrees (tuple of 3)."""
    if loc is not None:
        o.location = loc; o.keyframe_insert('location', frame=f)
    if rot is not None:
        o.rotation_euler = tuple(math.radians(a) for a in rot); o.keyframe_insert('rotation_euler', frame=f)
    if scl is not None:
        if not isinstance(scl, (tuple, list)):
            scl = (scl, scl, scl)
        o.scale = scl; o.keyframe_insert('scale', frame=f)


def KH(o, f, hidden):
    """Key visibility (render + viewport)."""
    o.hide_render = hidden; o.hide_viewport = hidden
    o.keyframe_insert('hide_render', frame=f); o.keyframe_insert('hide_viewport', frame=f)


def fcurves_of(idb):
    ad = getattr(idb, 'animation_data', None)
    if not ad or not ad.action:
        return []
    act = ad.action
    slot = getattr(ad, 'action_slot', None)
    if slot is not None:      # 4.4+: object and its data can share one action with 2 slots
        try:
            from bpy_extras import anim_utils
            cb = anim_utils.action_get_channelbag_for_slot(act, slot)
            if cb is not None:
                return list(cb.fcurves)
        except Exception:
            pass
    try:
        return list(act.fcurves)
    except Exception:
        pass
    out = []
    try:
        for layer in act.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    out += list(cb.fcurves)
    except Exception:
        pass
    return out


def set_interp(idb, interp='CONSTANT', path=None, easing=None):
    for fc in fcurves_of(idb):
        if path and not fc.data_path.startswith(path):
            continue
        for kp in fc.keyframe_points:
            kp.interpolation = interp
            if easing:
                kp.easing = easing


def add_noise(idb, path, index=0, strength=0.1, scale=10.0, phase=None):
    for fc in fcurves_of(idb):
        if fc.data_path == path and fc.array_index == index:
            m = fc.modifiers.new('NOISE')
            m.strength = strength; m.scale = scale
            m.phase = random.random() * 100 if phase is None else phase
            return m
    return None


def add_cycles(idb, path=None):
    for fc in fcurves_of(idb):
        if path and fc.data_path != path:
            continue
        fc.modifiers.new('CYCLES')


def clear_anim(o):
    if o.animation_data:
        o.animation_data_clear()


# ---------------------------------------------------------------- images
def save_image(name, arr):
    """arr: float32 (H, W, 4) sRGB 0..1, row 0 = TOP. Saves PNG into TEX and returns bpy image."""
    h, w = arr.shape[:2]
    path = os.path.join(TEX, name + '.png')
    img = bpy.data.images.get(name)
    if img is not None:
        bpy.data.images.remove(img)
    img = bpy.data.images.new(name, w, h, alpha=True)
    img.pixels.foreach_set(np.ascontiguousarray(arr[::-1]).astype(np.float32).ravel())
    img.filepath_raw = path; img.file_format = 'PNG'
    img.save()
    return img


def canvas(w, h, bg):
    a = np.zeros((h, w, 4), np.float32)
    a[:, :] = rgb255(bg)
    return a


def rgb255(h, alpha=1.0):
    h = h.lstrip('#')
    return [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)] + [alpha]


def rect(a, x, y, w, h, col, alpha=1.0):
    H, W = a.shape[:2]
    x0, y0, x1, y1 = max(0, int(x)), max(0, int(y)), min(W, int(x + w)), min(H, int(y + h))
    if x1 <= x0 or y1 <= y0:
        return
    c = np.array(rgb255(col) if isinstance(col, str) else col, np.float32)
    a[y0:y1, x0:x1, :3] = a[y0:y1, x0:x1, :3] * (1 - alpha) + c[:3] * alpha


def disc(a, cx, cy, r, col, alpha=1.0):
    H, W = a.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W]
    m = ((xx - cx) ** 2 + (yy - cy) ** 2) <= r * r
    c = np.array(rgb255(col), np.float32)
    a[m, :3] = a[m, :3] * (1 - alpha) + c[:3] * alpha


def image_mat(name, img, rough=0.6, emission=0.0, base_dark=False):
    m, nt, out = new_mat(name)
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img
    b = bsdf_node(nt, rough=rough)
    if base_dark:
        setin(b, 'Base Color', (0.005, 0.005, 0.008, 1))
    else:
        nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    if emission:
        nt.links.new(t.outputs['Color'], b.inputs['Emission Color'] if 'Emission Color' in b.inputs else b.inputs['Emission'])
        setin(b, 'Emission Strength', emission)
    nt.links.new(b.outputs[0], out.inputs[0])
    return m


def m_plane(name, w, h, center=(0, 0, 0), axis='Z'):
    """UV-mapped plane. axis Z: lies in XY; axis Y: stands in XZ facing -Y."""
    hw, hh = w / 2, h / 2
    if axis == 'Z':
        v = [(-hw, -hh, 0), (hw, -hh, 0), (hw, hh, 0), (-hw, hh, 0)]
    else:
        v = [(-hw, 0, -hh), (hw, 0, -hh), (hw, 0, hh), (-hw, 0, hh)]
    v = [(a + center[0], b + center[1], c + center[2]) for a, b, c in v]
    me = mesh_from(name, v, [(0, 1, 2, 3)], smooth=False)
    uv = me.uv_layers.new(name='UVMap')
    for i, (u, vv) in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[i].uv = (u, vv)
    return me


print('common loaded')
