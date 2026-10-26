# 08_preview_stills.py - low-res (540x960) EEVEE stills of key shots into reel-agents-dolomites\previews\.
# Set STILLS below (shot id -> frame offset inside the shot, 0..1). Restores the full-res settings afterwards.
import sys, importlib
sys.path.insert(0, r'C:\Users\acer\Downloads\jako-frames\reel-agents-dolomites\blender')
import common; importlib.reload(common)
from common import *

STILLS = globals().get('STILLS_OVERRIDE') or [('01', 0.6), ('04a', 0.5), ('06', 0.7), ('11c', 0.85), ('14', 0.35)]
SAMPLES = globals().get('SAMPLES_OVERRIDE') or 32
scene = bpy.context.scene
r = scene.render
old = (r.resolution_percentage, scene.eevee.taa_render_samples, r.filepath, scene.frame_current, scene.camera)
r.resolution_percentage = 50
scene.eevee.taa_render_samples = SAMPLES
done = []
import time
for sid, t in STILLS:
    _, f0, f1, cam = SHOT[sid]
    f = int(round(f0 + (f1 - f0) * t))
    scene.frame_set(f)
    scene.camera = bpy.data.objects[cam]
    r.filepath = os.path.join(PREV, 'shot%s_f%04d.png' % (sid, f))
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    done.append('%s f%d %.1fs -> %s' % (sid, f, time.time() - t0, r.filepath))
r.resolution_percentage, scene.eevee.taa_render_samples, r.filepath = old[0], old[1], old[2]
scene.frame_set(old[3]); scene.camera = old[4]
print('\n'.join(done))
