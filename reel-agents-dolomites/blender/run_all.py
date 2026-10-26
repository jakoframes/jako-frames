# run_all.py - rebuild the whole reel scene in order and save reel.blend (no rendering).
# In Blender: Scripting tab > open this file > Run Script. Or run each 0X_*.py on its own (each is idempotent).
import os, time
BLD = r'C:\Users\acer\Downloads\jako-frames\reel-agents-dolomites\blender'
ORDER = ['01_world.py', '02_office.py', '03_jako.py', '04_claude.py', '05_agents.py', '06_cameras_shots.py', '07_render_settings.py']


def run(name):
    p = os.path.join(BLD, name)
    t0 = time.time()
    with open(p, 'r', encoding='utf-8-sig') as f:
        code = compile(f.read(), p, 'exec')
    exec(code, {'__name__': '__main__', '__file__': p})
    print('== %s %.1fs' % (name, time.time() - t0))


for n in ORDER:
    run(n)
import bpy
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLD, 'reel.blend'))
print('saved reel.blend')
