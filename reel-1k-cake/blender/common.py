# Shared helpers for the "1000 followers" cake reel (helpers copied/adapted from reel-agents-dolomites/blender/common.py).
# Every build script does:  import common, importlib; importlib.reload(common); from common import *
# Coordinates: Blender Z-up, metres. The camera looks along +Y. Desk front edge at y = 0, characters behind it
# (y > 0) facing -Y (the camera), window wall at y = WALL_Y.
import bpy, bmesh, math, os, random, json
import numpy as np
from mathutils import Vector, Matrix, Euler

ROOT = r'C:\Users\acer\Downloads\jako-frames\reel-1k-cake'
BL = os.path.join(ROOT, 'blender')
TEX = os.path.join(BL, 'tex')
for _d in (TEX, os.path.join(ROOT, 'previews'), os.path.join(ROOT, 'stills')):
    os.makedirs(_d, exist_ok=True)

FPS = 24
with open(os.path.join(ROOT, 'audio', 'timeline.json'), 'r', encoding='utf-8') as _f:
    TL = json.load(_f)
FRAME_START, FRAME_END = 1, int(TL['total_frames'])
LINE = {l['id']: l for l in TL['lines']}
MIX_WAV = os.path.join(ROOT, 'audio', 'mix_preview.wav')


def F(sec):
    """seconds -> Blender frame (1-based)."""
    return int(round(sec * FPS)) + 1


# ---------------------------------------------------------------- layout
DESK_W, DESK_D, DESK_H = 2.1, 0.72, 0.62       # desk: x -1.05..1.05, y 0..0.72, top at z 0.62
WALL_Y = 2.15                                  # back wall with the window
ROOM_X0, ROOM_X1 = -2.3, 2.3
CEIL = 3.0
JAKO_XY = (0.0, 0.93)                          # Jako sits behind the desk centre
JAKO_Z = 0.27                                  # rig root height: hips at ~0.55 on a tall chair (legs hidden by the desk front)
CLAUDE_XY = (-0.56, 0.36)                      # Claude sits ON the desk, left
CAKE_XY = (0.02, 0.36)
MAC_XY = (0.50, 0.36)


# ---------------------------------------------------------------- colours
def _s2l(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexc(h, a=1.0):
    h = h.lstrip('#')
    return tuple(_s2l(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4)) + (a,)


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
    for coll in (bpy.data.meshes, bpy.data.curves, bpy.data.lights, bpy.data.cameras, bpy.data.armatures):
        for b in list(coll):
            if b.users == 0:
                coll.remove(b)


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


# ---------------------------------------------------------------- materials
def new_mat(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
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
    m.diffuse_color = color
    return m


def wood_mat(name, c_light='#DDB074', c_dark='#BC8749', grain='X', rough=0.45, coat=0.25, planks=0.0, **_):
    """Procedural honey wood: fine grain = noise stretched along `grain` axis, broad colour variation,
    optional plank seams (planks = boards per metre, across the grain). Subtle on purpose (Pixar-soft)."""
    m, nt, out = new_mat(name)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    ax = 'XYZ'.index(grain)
    sc_ = [14.0, 14.0, 14.0]; sc_[ax] = 0.6
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = sc_
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.0; nz.inputs['Detail'].default_value = 8.0
    setin(nz, 'Distortion', 0.6)
    nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
    big = nt.nodes.new('ShaderNodeTexNoise'); big.inputs['Scale'].default_value = 1.2; big.inputs['Detail'].default_value = 2.0
    nt.links.new(tc.outputs['Object'], big.inputs['Vector'])
    mixf = nt.nodes.new('ShaderNodeMix'); mixf.data_type = 'FLOAT'; mixf.inputs[0].default_value = 0.45
    nt.links.new(nz.outputs['Fac'], mixf.inputs[2]); nt.links.new(big.outputs['Fac'], mixf.inputs[3])
    r = nt.nodes.new('ShaderNodeValToRGB')
    r.color_ramp.elements[0].position = 0.30; r.color_ramp.elements[0].color = hexc(c_dark)
    r.color_ramp.elements[1].position = 0.72; r.color_ramp.elements[1].color = hexc(c_light)
    nt.links.new(mixf.outputs[0], r.inputs[0])
    col = r.outputs[0]
    height = mixf.outputs[0]
    if planks:
        across = (ax + 1) % 3 if grain != 'Z' else 0
        sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sep.inputs[0])
        fr = nt.nodes.new('ShaderNodeMath'); fr.operation = 'MULTIPLY'; fr.inputs[1].default_value = planks
        nt.links.new(sep.outputs[across], fr.inputs[0])
        fr2 = nt.nodes.new('ShaderNodeMath'); fr2.operation = 'FRACT'; nt.links.new(fr.outputs[0], fr2.inputs[0])
        seam = nt.nodes.new('ShaderNodeMath'); seam.operation = 'GREATER_THAN'; seam.inputs[1].default_value = 0.985
        nt.links.new(fr2.outputs[0], seam.inputs[0])
        cm = nt.nodes.new('ShaderNodeMix'); cm.data_type = 'RGBA'; cm.blend_type = 'MULTIPLY'
        nt.links.new(seam.outputs[0], cm.inputs[0]); nt.links.new(col, cm.inputs[6]); cm.inputs[7].default_value = (0.55, 0.45, 0.38, 1)
        col = cm.outputs[2]
        hm = nt.nodes.new('ShaderNodeMath'); hm.operation = 'SUBTRACT'
        nt.links.new(height, hm.inputs[0]); nt.links.new(seam.outputs[0], hm.inputs[1])
        height = hm.outputs[0]
    b = bsdf_node(nt, rough=rough, coat=coat, coat_rough=0.3)
    nt.links.new(col, b.inputs['Base Color'])
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.05
    nt.links.new(height, bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    nt.links.new(b.outputs[0], out.inputs[0])
    m.diffuse_color = hexc(c_light)
    return m


# ---------------------------------------------------------------- meshes
def mesh_from(name, verts, faces, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.validate(); me.update()
    if smooth:
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
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


def empty(name, coll, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), size=0.2, kind='PLAIN_AXES', scale=(1, 1, 1)):
    o = obj(name, None, coll, parent, loc, rot, scale)
    o.empty_display_type = kind; o.empty_display_size = size
    return o


def bm_to_mesh(bm, name, smooth=True):
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
    return bm_to_mesh(bm, name, smooth)


def m_box(name, size=(1, 1, 1), center=(0, 0, 0), smooth=False):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0] + center[0], v.co.y * size[1] + center[1], v.co.z * size[2] + center[2]))
    return bm_to_mesh(bm, name, smooth)


def m_cyl(name, r1, r2, h, center=(0, 0, 0), seg=32, smooth=True, caps=True):
    """Cylinder/cone along Z, centred on `center`."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, cap_tris=False, segments=seg, radius1=r1, radius2=r2, depth=h)
    for v in bm.verts:
        v.co += Vector(center)
    return bm_to_mesh(bm, name, smooth)


def m_tube(name, pts, radii, rseg=10, caps=True):
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


def rbox(name, size, center=(0, 0, 0), bevel=0.01, seg=3, coll=None, mats=(), parent=None, loc=(0, 0, 0), rot=(0, 0, 0)):
    """Box object with a soft bevel modifier (Pixar-soft edges)."""
    o = obj(name, m_box(name, size, center), coll, parent, loc, rot, mats=mats)
    mod_bevel(o, bevel, seg)
    return o


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


def text_obj(name, body, coll, font_path=None, size=0.1, extrude=0.01, bevel=0.003, align='CENTER', mats=(), parent=None, loc=(0, 0, 0), rot=(0, 0, 0)):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body; cu.size = size; cu.extrude = extrude; cu.bevel_depth = bevel; cu.bevel_resolution = 3
    cu.align_x = align; cu.align_y = 'BOTTOM'
    if font_path and os.path.exists(font_path):
        cu.font = bpy.data.fonts.load(font_path, check_existing=True)
    o = obj(name, cu, coll, parent, loc, rot, mats=mats)
    return o


def look_rot(src, target, roll=0.0):
    d = Vector(target) - Vector(src)
    e = d.to_track_quat('-Z', 'Y').to_euler()
    if roll:
        e.rotate_axis('Z', math.radians(roll))
    return e


# ---------------------------------------------------------------- animation
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


def KP(idb, key, f, val):
    """Key a custom property."""
    idb[key] = val
    idb.keyframe_insert('["%s"]' % key, frame=f)


def KH(o, f, hidden):
    o.hide_render = hidden; o.hide_viewport = hidden
    o.keyframe_insert('hide_render', frame=f); o.keyframe_insert('hide_viewport', frame=f)


def fcurves_of(idb):
    ad = getattr(idb, 'animation_data', None)
    if not ad or not ad.action:
        return []
    act = ad.action
    slot = getattr(ad, 'action_slot', None)
    if slot is not None:
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


print('common loaded')
