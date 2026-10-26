# run_all.py - rebuild the whole cake-reel scene and save blender/scene.blend (no rendering).
#   blender.exe -b -y --factory-startup --python reel-1k-cake\blender\run_all.py
# (-y: allow the frame drivers on the rain/glass; --factory-startup: clean scene)
# Order: s1_set (room, props, lights, render settings) -> s2_characters (appends Jako from jako-3d\jako.blend,
# builds Claude) -> s3_anim (acting, tablet, cameras/cuts, sound strip, subs/subs.json + audio/shots.json).
import os, time
import bpy
BLD = r'C:\Users\acer\Downloads\jako-frames\reel-1k-cake\blender'
for n in ('s1_set.py', 's2_characters.py', 's3_anim.py'):
    p = os.path.join(BLD, n)
    t0 = time.time()
    exec(compile(open(p, encoding='utf-8-sig').read(), p, 'exec'), {'__name__': '__main__', '__file__': p})
    print('== %s %.1fs' % (n, time.time() - t0))
for _ in range(2):
    bpy.data.orphans_purge(do_local_ids=True, do_recursive=True)
bpy.ops.file.make_paths_relative()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLD, 'scene.blend'))
print('saved scene.blend')
