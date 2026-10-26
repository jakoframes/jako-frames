# render_stills.py - render single frames of scene.blend at full quality.
#   blender.exe -b -y blender\scene.blend --python blender\render_stills.py -- <frame>:<out.png> [<frame>:<out.png> ...] [--pct 100] [--samples 64]
import bpy, sys
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
pct, samples, jobs = 100, 64, []
i = 0
while i < len(args):
    if args[i] == '--pct':
        pct = int(args[i + 1]); i += 2; continue
    if args[i] == '--samples':
        samples = int(args[i + 1]); i += 2; continue
    f, out = args[i].split(':', 1)
    jobs.append((int(f), out)); i += 1
sc = bpy.context.scene
sc.render.resolution_percentage = pct
sc.eevee.taa_render_samples = samples
sc.render.image_settings.file_format = 'PNG'
for f, out in jobs:
    sc.frame_set(f)
    for m in sorted(sc.timeline_markers, key=lambda m: m.frame):      # marker-bound camera for this frame
        if m.frame <= f and m.camera:
            sc.camera = m.camera
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print('WROTE', f, sc.camera.name, out)
