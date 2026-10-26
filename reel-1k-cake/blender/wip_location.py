# wip_location.py - build set + characters and render one wide still (location check). Not part of the final pipeline.
import bpy, os, sys, math
BLD = r'C:\Users\acer\Downloads\jako-frames\reel-1k-cake\blender'
for n in ('s1_set.py', 's2_characters.py'):
    p = os.path.join(BLD, n)
    exec(compile(open(p, encoding='utf-8-sig').read(), p, 'exec'), {'__name__': '__main__', '__file__': p})
from mathutils import Vector
sc = bpy.context.scene
cam = bpy.data.objects.get('CAM_wip') or bpy.data.objects.new('CAM_wip', bpy.data.cameras.new('CAM_wip'))
if cam.name not in sc.collection.objects:
    sc.collection.objects.link(cam)
cam.data.lens = 28
cam.location = (0.0, -2.5, 1.25)
d = Vector((0.0, 0.8, 1.06)) - cam.location
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 4.0; cam.data.dof.focus_distance = (Vector((0, 0.7, 1.0)) - cam.location).length
sc.camera = cam
sc.frame_set(int(sys.argv[-1]) if sys.argv[-1].isdigit() else 30)
pct = int(os.environ.get('WIP_PCT', '100'))
if os.environ.get('VT_LOOK'):
    vt, lk = os.environ['VT_LOOK'].split('|')
    sc.view_settings.view_transform = vt; sc.view_settings.look = lk
sc.render.resolution_percentage = pct
sc.eevee.taa_render_samples = 32
out = os.environ.get('WIP_OUT', r'C:\Users\acer\Downloads\jako-frames\reel-1k-cake\previews\location_wip.png')
sc.render.filepath = out
sc.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)
print('WROTE', out)
