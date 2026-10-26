# Preview stills of jako.blend (EEVEE).  Does not save the .blend.
#   blender.exe -b jako-3d/jako.blend --python jako-3d/render_previews.py -- [--quick] [--shots front,34,side,back,head,faces,compare]
import bpy, os, sys, math
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'previews')
os.makedirs(OUT, exist_ok=True)
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
QUICK = '--quick' in argv
SHOTS = ['front', '34', 'side', 'back', 'head', 'faces', 'compare']
if '--shots' in argv:
    SHOTS = argv[argv.index('--shots') + 1].split(',')
S = 0.003
SC = bpy.context.scene
rig = bpy.data.objects['JAKO_rig']
cam = SC.camera
r = SC.render
SC.eevee.taa_render_samples = 16 if QUICK else 96
r.resolution_percentage = 40 if QUICK else 100
r.image_settings.file_format = 'PNG'
rig.hide_render = True

def state(eyes=0, mouth=0, shades=0):
    rig['eyes'], rig['mouth'], rig['shades'] = eyes, mouth, shades
    rig.update_tag()
    bpy.context.view_layer.update()
    SC.frame_set(SC.frame_current)

def look_at(loc, target, lens):
    cam.data.type = 'PERSP'; cam.data.lens = lens; cam.data.sensor_fit = 'AUTO'
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    cam.data.dof.use_dof = False

from mathutils import Matrix
STUDIO = [o for o in bpy.data.objects if o.name.startswith(('STUDIO_', 'KEY', 'FILL', 'RIM'))]
STUDIO_M = {o.name: o.matrix_world.copy() for o in STUDIO}
def orbit_studio(az_deg):
    """keep backdrop + light rig fixed relative to the camera, so every angle is lit the same way"""
    R = Matrix.Rotation(math.radians(az_deg), 4, 'Z')
    for o in STUDIO:
        o.matrix_world = R @ STUDIO_M[o.name]

def shot(name, az_deg, dist, h, target_z, lens=85, res=(864, 1080), suffix=''):
    r.resolution_x, r.resolution_y = res
    orbit_studio(az_deg)
    a = math.radians(az_deg)          # 0 = front (-Y); positive = toward the character's left (+X)
    loc = (math.sin(a) * dist, -math.cos(a) * dist, h)
    look_at(loc, (0, 0, target_z), lens)
    r.filepath = os.path.join(OUT, name + suffix + '.png')
    bpy.ops.render.render(write_still=True)
    return r.filepath

def read_px(path):
    img = bpy.data.images.load(path); w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1].copy()
    bpy.data.images.remove(img); return a
def write_px(path, a):
    h, w = a.shape[:2]
    img = bpy.data.images.new('tmp', w, h, alpha=True)
    img.pixels[:] = a[::-1].ravel()
    img.filepath_raw = path; img.file_format = 'PNG'; img.save(); bpy.data.images.remove(img)

body_z = 0.70
if 'front' in SHOTS:
    state(shades=1); shot('jako_front', 0, 4.2, 0.78, body_z)
if '34' in SHOTS:
    state(shades=2); shot('jako_34', 38, 4.2, 0.95, body_z)
if 'side' in SHOTS:
    state(); shot('jako_side', 90, 4.2, 0.78, body_z)
if 'back' in SHOTS:
    state(); shot('jako_back', 180, 4.2, 0.85, body_z)
if 'head' in SHOTS:
    state(); shot('jako_head', 18, 2.15, 1.08, 0.97, lens=85, res=(1080, 1080))
if 'faces' in SHOTS:
    tiles = []
    for k, (e, m, lbl) in enumerate(((1, 0, 'blink'), (2, 2, 'happy'), (3, 3, 'surprised'), (0, 1, 'talk'))):
        state(eyes=e, mouth=m)
        tiles.append(read_px(shot('_tmp_face_%s' % lbl, 0, 1.45, 0.98, 0.93, lens=85, res=(540, 540))))
    write_px(os.path.join(OUT, 'jako_faces_blink_happy_surprised_talk.png'), np.concatenate(tiles, axis=1))
    for f in os.listdir(OUT):
        if f.startswith('_tmp_face_'):
            os.remove(os.path.join(OUT, f))
    state()
if 'compare' in SHOTS:
    # 3D front in orthographic, same framing as the kit canvas (400x500 units -> 864x1080)
    state(shades=0)
    r.resolution_x, r.resolution_y = 864, 1080
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 500 * S
    cam.location = (0, -6, (485 - 250) * S); cam.rotation_euler = (math.pi / 2, 0, 0)
    r.film_transparent = True
    r.filepath = os.path.join(OUT, '_tmp_ortho.png'); bpy.ops.render.render(write_still=True)
    r.film_transparent = False
    m3 = read_px(r.filepath); os.remove(r.filepath)
    kit = read_px(os.path.join(HERE, 'ref', 'png', 'kit_compare.png'))
    bg = np.array([0xef, 0xe9, 0xdf, 255], dtype=np.float32) / 255
    bg = np.array([c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in bg[:3]] + [1.0], dtype=np.float32)
    # image pixels are linear for render results? both were saved as sRGB PNG and re-read -> same space; composite in that space
    bgs = np.array([0xef, 0xe9, 0xdf, 255], dtype=np.float32) / 255
    al = m3[..., 3:4]
    m3c = m3 * al + bgs * (1 - al); m3c[..., 3] = 1
    sep = np.ones((m3.shape[0], 12, 4), dtype=np.float32) * np.array([0.2, 0.2, 0.2, 1], dtype=np.float32)
    write_px(os.path.join(OUT, 'jako_compare_kit_vs_3d.png'), np.concatenate([kit[..., :4], sep, m3c], axis=1))
print('PREVIEWS DONE', SHOTS)
