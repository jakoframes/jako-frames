# ---------------------------------------------------------------- lights: warm pool on the desk + characters, room falls off softly
def area(name, loc, target, energy, size, color, shape='DISK', size_y=None, shadow=True, spread=None):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.color = hexc(color)[:3]; ld.shape = shape; ld.size = size
    if size_y:
        ld.size_y = size_y
    if spread:
        ld.spread = math.radians(spread)
    try:
        ld.use_shadow = shadow
    except Exception:
        pass
    o = obj(name, ld, LIG, loc=loc)
    o.rotation_euler = look_rot(loc, target)
    return o

def spot(name, loc, target, energy, cone, blend, radius, color, shadow=True):
    ld = bpy.data.lights.new(name, 'SPOT'); ld.energy = energy; ld.color = hexc(color)[:3]
    ld.spot_size = math.radians(cone); ld.spot_blend = blend; ld.shadow_soft_size = radius
    try:
        ld.use_shadow = shadow
    except Exception:
        pass
    o = obj(name, ld, LIG, loc=loc)
    o.rotation_euler = look_rot(loc, target)
    return o

def point(name, loc, energy, radius, color, shadow=True):
    ld = bpy.data.lights.new(name, 'POINT'); ld.energy = energy; ld.color = hexc(color)[:3]; ld.shadow_soft_size = radius
    try:
        ld.use_shadow = shadow
    except Exception:
        pass
    return obj(name, ld, LIG, loc=loc)

AIM = (-0.15, 0.55, 0.95)
spot('L_key', (-1.25, -1.75, 2.45), AIM, 1100, 44, 0.85, 0.55, '#FFDDB0')          # soft warm key on desk + both faces
spot('L_fill', (1.6, -1.9, 1.35), AIM, 380, 50, 0.9, 0.9, '#FFE6CC', shadow=False)  # gentle fill from the right
area('L_rim_L', (-1.2, 1.95, 1.9), (-0.55, 0.45, 0.95), 110, 0.7, '#9FB8FF')        # cool window rims
area('L_rim_R', (1.1, 1.95, 1.95), (0.1, 0.9, 1.15), 120, 0.7, '#9FB8FF')
area('L_lamp_pool', (LAMP[0], LAMP[1], LAMP[2] - 0.03), (LAMP[0] - 0.1, LAMP[1] - 0.3, 0), 260, 0.5, '#FFB870', spread=75)
point('L_lamp_bulb', (LAMP[0], LAMP[1], LAMP[2] + 0.06), 25, 0.08, '#FFC27F')
area('L_laptop', (MAC_XY[0] - 0.12, MAC_XY[1] + 0.14, TOP + 0.16), (0.0, 0.93, 1.12), 6, 0.3, '#DCE6FF', 'RECTANGLE', 0.2, shadow=False)
area('L_room_spill', (0.0, -1.2, 2.8), (0.0, 1.2, 1.2), 70, 3.0, '#FFD7AE', shadow=False)   # keeps the room readable, not dark
cl = point('L_candles', (CAKE_XY[0], CAKE_XY[1] - 0.05, TOP + 0.3), 5.0, 0.03, '#FFB04A')
cl.data.keyframe_insert('energy', frame=1)
fc = [f for f in fcurves_of(cl.data) if f.data_path == 'energy']
if fc:
    m = fc[0].modifiers.new('NOISE'); m.strength = 2.0; m.scale = 2.0
for i, fl in enumerate(FLAMES):              # flame flicker
    fl.keyframe_insert('scale', frame=1)
    for idx in range(3):
        add_noise(fl, 'scale', idx, 0.25 if idx == 2 else 0.12, 1.5 + i * 0.3, phase=i * 7.0 + idx)

