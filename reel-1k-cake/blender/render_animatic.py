# render_animatic.py - low-res timing preview: 540x960, EEVEE 12 samples, no ray tracing -> previews/animatic_frames/####.png
#   blender.exe -b -y blender\scene.blend --python blender\render_animatic.py
import bpy, os
sc = bpy.context.scene
OUT = r'C:\Users\acer\Downloads\jako-frames\reel-1k-cake\previews\animatic_frames'
os.makedirs(OUT, exist_ok=True)
sc.render.resolution_percentage = 50
sc.eevee.taa_render_samples = 12
try:
    sc.eevee.use_raytracing = False
except Exception:
    pass
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGB'
sc.render.filepath = os.path.join(OUT, '')
sc.render.use_overwrite = False          # resumable: existing frames are skipped
sc.render.use_placeholder = True
bpy.ops.render.render(animation=True)
print('ANIMATIC DONE')
