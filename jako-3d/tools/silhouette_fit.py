# Silhouette fit of head + hair against the 2D kit (fill-only seg masks from ref/render_ref.js).
#   blender.exe -b jako-3d/jako.blend --python jako-3d/tools/silhouette_fit.py
# Renders flat-colour orthographic front/back views matched 1:1 to the kit canvas (800x1000 px = 2 px per svg unit),
# then prints IoU / bbox / row-width numbers and writes overlay images (kit-only = red, 3D-only = blue, both = grey).
import bpy, os, sys, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REF = os.path.join(ROOT, 'ref', 'png')
OUTD = os.path.join(HERE, 'fit')
os.makedirs(OUTD, exist_ok=True)
S = 0.003
SC = bpy.context.scene

def flat(name, rgb):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs[0].default_value = (*rgb, 1); e.inputs[1].default_value = 1.0
    o = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(e.outputs[0], o.inputs[0])
    return m
RED, GREEN = flat('SEG_red', (1, 0, 0)), flat('SEG_green', (0, 1, 0))
rig = bpy.data.objects['JAKO_rig']
rig['shades'] = 0

hair_names = lambda n: n.startswith(('JAKO_hair', 'JAKO_ahoge'))
skin_names = lambda n: n in ('JAKO_head', 'JAKO_ear_R', 'JAKO_ear_L')
for ob in bpy.data.objects:
    if ob.type == 'MESH':
        if ob.animation_data:
            ob.animation_data_clear()
        keep = hair_names(ob.name) or skin_names(ob.name)
        ob.hide_render = not keep
        if keep:
            mat = RED if hair_names(ob.name) else GREEN
            ob.data.materials.clear(); ob.data.materials.append(mat)
    elif ob.type == 'LIGHT':
        ob.hide_render = True
SC.world.node_tree.nodes['Background'].inputs[1].default_value = 0.0
r = SC.render
r.resolution_x, r.resolution_y, r.resolution_percentage = 800, 1000, 100
r.film_transparent = False
r.filter_size = 0.5
SC.eevee.taa_render_samples = 8
SC.view_settings.view_transform = 'Standard'; SC.view_settings.look = 'None'
cam = SC.camera
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 500 * S; cam.data.sensor_fit = 'AUTO'

def render(view):
    if view == 'front':
        cam.location = (0, -6, (485 - 250) * S); cam.rotation_euler = (1.5707963, 0, 0)
    else:
        cam.location = (0, 6, (485 - 250) * S); cam.rotation_euler = (1.5707963, 0, 3.14159265)
    path = os.path.join(OUTD, 'seg3d_%s.png' % view)
    r.filepath = path; r.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)
    return path

def load(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1]  # top row first
    bpy.data.images.remove(img)
    return a

def classes(a):
    R, G = a[..., 0], a[..., 1]
    if a.max() > 1.0:
        R, G = R / 255, G / 255
    hair = (R > 0.5) & (G < 0.35)
    skin = (G > 0.5) & (R < 0.35)
    return hair, skin

def bbox(m):
    ys, xs = np.nonzero(m)
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(xs) else None

def iou(a, b):
    u = (a | b).sum(); return float((a & b).sum() / u) if u else 0.0

report = {}
for view in ('front', 'back'):
    kit = load(os.path.join(REF, 'seg_%s.png' % view))
    m3 = load(render(view))
    kh, ks = classes(kit); th, ts = classes(m3)
    rows = slice(0, 2 * 256) if view == 'back' else slice(0, 1000)    # back: above the neck
    kh, ks, th, ts = kh[rows], ks[rows], th[rows], ts[rows]
    ku, tu = kh | ks, th | ts
    kb, tb = bbox(ku), bbox(tu)
    khb, thb = bbox(kh), bbox(th)
    # row width profile of the union (svg units), every 4 svg units
    prof = []
    for y in range(max(kb[1], tb[1]), min(kb[3], tb[3]), 8):
        kr, tr = np.nonzero(ku[y])[0], np.nonzero(tu[y])[0]
        if len(kr) and len(tr):
            prof.append(((kr.max() - kr.min()) - (tr.max() - tr.min())) / 2)
    rep = dict(
        iou_union=round(iou(ku, tu), 4), iou_hair=round(iou(kh, th), 4), iou_skin=round(iou(ks, ts), 4),
        kit_bbox_units=[v / 2 for v in kb], model_bbox_units=[v / 2 for v in tb],
        kit_aspect_w_over_h=round((kb[2] - kb[0]) / (kb[3] - kb[1]), 4), model_aspect_w_over_h=round((tb[2] - tb[0]) / (tb[3] - tb[1]), 4),
        kit_hair_bbox_units=[v / 2 for v in khb], model_hair_bbox_units=[v / 2 for v in thb],
        row_width_mean_abs_err_units=round(float(np.mean(np.abs(prof))) / 2, 2), row_width_max_err_units=round(float(np.max(np.abs(prof))) / 2, 2),
    )
    report[view] = rep
    ov = np.zeros(ku.shape + (3,), dtype=np.float32)
    ov[ku & tu] = (0.75, 0.75, 0.75); ov[ku & ~tu] = (1, 0.1, 0.1); ov[~ku & tu] = (0.1, 0.3, 1)
    ov[kh & th] = (0.45, 0.45, 0.45)
    h, w = ov.shape[:2]
    img = bpy.data.images.new('ov_' + view, w, h, alpha=True)
    px = np.ones((h, w, 4), dtype=np.float32); px[..., :3] = ov
    img.pixels[:] = px[::-1].ravel()
    img.filepath_raw = os.path.join(OUTD, 'overlay_%s.png' % view); img.file_format = 'PNG'; img.save()
print('FITREPORT ' + json.dumps(report))
with open(os.path.join(OUTD, 'fit_report.json'), 'w') as f:
    json.dump(report, f, indent=2)
