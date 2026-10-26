# 07_render_settings.py - EEVEE (laptop friendly), 1080x1920 @ 24 fps, frames 1..1190 (audio/timeline.json),
# AgX, soft DOF (per camera), motion blur (whip-pans), volumetrics for the valley fog/haze, compositor glare (warm
# bloom) + soft vignette, output path for the later full render, and audio/mix_preview.wav in the VSE for sync.
# Does NOT render anything. Re-runnable.
import sys, importlib
sys.path.insert(0, r'C:\Users\acer\Downloads\jako-frames\reel-agents-dolomites\blender')
import common; importlib.reload(common)
from common import *

scene = bpy.context.scene
r = scene.render
log = []


def tryset(obj_, attr, val):
    try:
        setattr(obj_, attr, val); return True
    except Exception as e:
        log.append('skip %s.%s (%s)' % (type(obj_).__name__, attr, str(e)[:60])); return False


for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        r.engine = eng
        break
    except TypeError:
        continue
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps, r.fps_base = FPS, 1.0
scene.frame_start, scene.frame_end = FRAME_START, FRAME_END
tryset(r, 'filter_size', 1.5)
r.film_transparent = False
# motion blur (4.2+: on scene.render; older EEVEE: on scene.eevee)
if not tryset(r, 'use_motion_blur', True):
    tryset(scene.eevee, 'use_motion_blur', True)
tryset(r, 'motion_blur_shutter', 0.5)

ee = scene.eevee
for attr, val in (('taa_render_samples', 64), ('taa_samples', 16), ('use_shadows', True), ('shadow_ray_count', 1),
                  ('shadow_step_count', 6), ('use_raytracing', True), ('ray_tracing_method', 'SCREEN'),
                  ('use_fast_gi', True), ('fast_gi_distance', 2.0), ('use_gtao', True), ('gtao_distance', 0.6),
                  ('volumetric_tile_size', '8'), ('volumetric_samples', 64), ('volumetric_start', 0.1),
                  ('volumetric_end', 900.0), ('volumetric_sample_distribution', 0.85), ('use_volumetric_shadows', True),
                  ('volumetric_shadow_samples', 12), ('volumetric_light_clamp', 0.0), ('light_threshold', 0.02),
                  ('use_bloom', True), ('bloom_threshold', 1.0), ('bloom_intensity', 0.04), ('bloom_color', (1.0, 0.75, 0.6)),
                  ('use_soft_shadows', True), ('clamp_surface_indirect', 10.0)):
    if hasattr(ee, attr):
        tryset(ee, attr, val)
try:
    ee.ray_tracing_options.resolution_scale = '2'
except Exception:
    pass

# colour management: AgX
vs = scene.view_settings
tryset(scene.display_settings, 'display_device', 'sRGB')
tryset(vs, 'view_transform', 'AgX')
for look in ('AgX - Medium High Contrast', 'Medium High Contrast', 'AgX - Punchy', 'Punchy', 'None'):
    if tryset(vs, 'look', look):
        break
vs.exposure = 0.0; vs.gamma = 1.0

# output (for the final render later - not rendered here)
os.makedirs(os.path.join(ROOT, 'renders'), exist_ok=True)
r.filepath = os.path.join(ROOT, 'renders', 'frame_')
r.image_settings.file_format = 'PNG'
tryset(r.image_settings, 'color_depth', '8')
tryset(r, 'use_sequencer', True)

# ------------------------------------------------------------ compositor: warm glare + soft vignette
def build_compositor():
    if bpy.app.version >= (5, 0, 0) and hasattr(scene, 'compositing_node_group'):
        tree = bpy.data.node_groups.get('COMP_reel') or bpy.data.node_groups.new('COMP_reel', 'CompositorNodeTree')
        tree.nodes.clear()
        if not tree.interface.items_tree:
            tree.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
        scene.compositing_node_group = tree
        out = tree.nodes.new('NodeGroupOutput')
    else:
        scene.use_nodes = True
        tree = scene.node_tree
        tree.nodes.clear()
        out = tree.nodes.new('CompositorNodeComposite')
    n, L = tree.nodes, tree.links
    rl = n.new('CompositorNodeRLayers')
    gl = n.new('CompositorNodeGlare')
    for attr, val in (('glare_type', 'FOG_GLOW'), ('quality', 'HIGH'), ('threshold', 0.9), ('mix', -0.55), ('size', 8)):
        if not tryset(gl, attr, val):
            key = {'glare_type': 'Type', 'threshold': 'Threshold', 'mix': 'Strength', 'size': 'Size', 'quality': 'Quality'}[attr]
            if key in gl.inputs:
                try:
                    gl.inputs[key].default_value = {'mix': 0.35, 'size': 0.6}.get(attr, val)
                except Exception:
                    pass
    L.new(rl.outputs['Image'], gl.inputs['Image'])
    last = gl.outputs['Image']
    try:   # vignette
        el = n.new('CompositorNodeEllipseMask'); el.width = 1.05; el.height = 0.95
        bl = n.new('CompositorNodeBlur'); bl.size_x = 300; bl.size_y = 300; bl.use_relative = False
        L.new(el.outputs['Mask'], bl.inputs['Image'])
        mx = n.new('CompositorNodeMixRGB'); mx.blend_type = 'MULTIPLY'
        mr = n.new('CompositorNodeMapRange')
        mr.inputs['From Min'].default_value = 0.0; mr.inputs['From Max'].default_value = 1.0
        mr.inputs['To Min'].default_value = 0.72; mr.inputs['To Max'].default_value = 1.0
        L.new(bl.outputs['Image'], mr.inputs['Value'])
        mx.inputs['Fac'].default_value = 1.0
        L.new(last, mx.inputs[1]); L.new(mr.outputs['Value'], mx.inputs[2])
        last = mx.outputs['Image']
    except Exception as e:
        log.append('vignette skipped: %s' % e)
    L.new(last, out.inputs[0])
    try:
        v = n.new('CompositorNodeViewer'); L.new(last, v.inputs[0])
    except Exception:
        pass


try:
    build_compositor()
except Exception as e:
    log.append('compositor skipped: %s' % e)

# ------------------------------------------------------------ audio preview in the VSE
try:
    se = scene.sequence_editor or scene.sequence_editor_create()
    strips = getattr(se, 'strips', None)
    if strips is None:
        strips = se.sequences
    for s in list(strips):
        if s.name.startswith('MIX_preview'):
            strips.remove(s)
    snd = strips.new_sound('MIX_preview', MIX_WAV, 1, FRAME_START)
    tryset(scene, 'sync_mode', 'AUDIO_SYNC')
    log.append('audio strip %d..%d' % (snd.frame_final_start, snd.frame_final_end))
except Exception as e:
    log.append('audio strip failed: %s' % e)

print('engine', r.engine, 'res', r.resolution_x, r.resolution_y, 'frames', scene.frame_start, scene.frame_end, 'look', vs.look)
print('\n'.join(log))
print('07_render_settings done')
