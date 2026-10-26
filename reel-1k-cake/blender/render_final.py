# render_final.py - full-quality frames: 1080x1920, EEVEE 64 samples, ray tracing on -> renders/####.png (resumable)
#   blender.exe -b -y blender\scene.blend --python blender\render_final.py
import bpy, os
sc = bpy.context.scene
OUT = r'C:\Users\acer\Downloads\jako-frames\reel-1k-cake\renders'
os.makedirs(OUT, exist_ok=True)
sc.render.resolution_percentage = 100
sc.eevee.taa_render_samples = 64
try:
    sc.eevee.use_raytracing = True
except Exception:
    pass
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGB'
sc.render.image_settings.compression = 30
sc.render.filepath = os.path.join(OUT, '')
sc.render.use_overwrite = False          # existing frames are skipped -> safe to restart
sc.render.use_placeholder = True
bpy.ops.render.render(animation=True)
print('FINAL FRAMES DONE')
