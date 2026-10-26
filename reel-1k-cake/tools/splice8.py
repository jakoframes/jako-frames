import io
P = r'C:\Users\acer\Downloads\jako-frames\reel-1k-cake\blender\s3_anim.py'
s = io.open(P, encoding='utf-8').read()
reps = [
("HOLD_R = N(0, -8, -35)                   # right stub forward-right, pinching the tablet's edge",
 "HOLD_R = N(0, -8, -80)                   # right stub swung forward, pinching the tablet's right edge"),
("guess = tip0 + (tip0 - CL.matrix_world.translation).normalized() * (TW / 2)\n",
 "front = BODY.matrix_world.to_3x3() @ Vector((0, -1, 0)); front.z = 0; front.normalize()\n"
 "guess = eye_c + front * 0.20 + Vector((0, 0, -0.04))      # held up in front of Claude's face\n"),
("    PHONE.location = tip + xax * (TW / 2 - 0.01)\n", "    PHONE.location = guess + (tip - tip0)\n"),
]
for x, y in reps:
    if x not in s: print('MISSING', x[:60])
    s = s.replace(x, y)
io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
