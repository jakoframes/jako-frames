# Jako 3D (Mini Me v2, look "medium") — status

Built 2026-10-26 from scratch. `reel-agents-dolomites/` was not touched; its 03_jako.py was only read, to avoid repeating its mistakes. That build used hand-tuned ellipsoids (HA/HB/HC), which gave an egg-shaped head, plus a normal-offset cap for the hair.

## What was built
- `jako.blend`: the reusable asset. Collections: `JAKO` (character + rig) and `STUDIO` (cyclorama, 4 area lights, camera).
- **Head**: lofted straight from the kit's `FACE` path, one superellipse ring per height. Its width comes from the contour and its depth is 0.9 × width, so the front silhouette is the kit's own shape: 176 wide × 172 tall, round, not an egg.
- **Hair**: one solid helmet lofted from the `HAIR` / `HAIR_BACK` outlines.
  - Two prism cuts shape it: the kit's fringe zigzag cuts the face opening (front half), and the back outline cuts the nape zigzag (back half).
  - It is then voxel-remeshed and Laplacian-smoothed for soft Pixar edges.
  - Strand highlights (the kit's paths, ray-projected), plus a two-strand ahoge.
- **Face**: kit shapes (eyes, lids, brows, mouths) projected onto the head as thin raised decals. Blush lives in the skin shader.
- **Outfit**:
  - Cream jersey: maroon V collar, navy and maroon side panels, crest, maroon-edged navy "10" on the back.
  - Sleeves with maroon and navy hem stripes.
  - Wide stacked washed-black jeans with procedural folds.
  - White high-tops with navy sole, swoosh and grey mesh panel.
  - Silver digital watch on the LEFT wrist (+X).
- **Shades**: wrap-around lenses on a smooth cylinder in front of the face and fringe, with arms to the ears. A second "pushed up" pair is projected onto the hair.

## Controls (custom properties on `JAKO_rig`, driver-based)
| prop | values |
|---|---|
| `eyes` | 0 neutral (sleepy half-lid), 1 blink, 2 happy (adds blush), 3 surprised. Brows follow automatically |
| `mouth` | 0 closed (flat), 1 open / talk, 2 happy, 3 surprised |
| `shades` | 0 off (default), 1 on the eyes, 2 pushed up on the head |
| `blush` | 0..1 extra blush |

Animate these (constant interpolation) for blinks and lip flaps. The face states are separate decal objects whose visibility is driven by these props, not shape keys.

## Rig
Armature `JAKO_rig`:
- Spine: root > hips > spine > chest > neck > head.
- Arms: upper_arm / forearm / hand .L/.R.
- Legs: thigh / shin / foot .L/.R.

Every mesh is parented to the rig with an Armature modifier and position-based weights: blended at the elbow, knee and spine; rigid everywhere else. Tested: rotating head, forearm and shin moves hair, eyes, hand, watch and pants correctly.

## Rebuild
```
blender.exe -b --factory-startup --python jako-3d\build_jako.py           # -> jako-3d\jako.blend (~1 min)
blender.exe -b jako-3d\jako.blend --python jako-3d\render_previews.py      # -> previews\ (add -- --quick for 40% drafts)
blender.exe -b jako-3d\jako.blend --python jako-3d\tools\silhouette_fit.py # -> tools\fit\ overlays + fit_report.json
powershell -File jako-3d\ref\render_ref.ps1                                 # kit reference PNGs via headless Edge
```
Blender: `C:\Users\acer\Blender\blender-4.5.15-windows-x64\blender.exe`. Shape parameters are in the `P` dict at the top of `build_jako.py`. Scale: 1 kit unit = 3 mm, so Jako is about 1.37 m tall.

## Silhouette fit (head + hair, orthographic, fill-only kit masks)
| view | IoU union | IoU hair | IoU skin | bbox aspect kit / 3D | mean row-width error |
|---|---|---|---|---|---|
| front | 0.982 | 0.975 | 0.990 | 0.836 / 0.829 | 0.8 units (max 4.8) |
| back | 0.937 | 0.945 | 0.14 (ears only, tiny area) | 0.885 / 0.872 | 2.0 units (max 16) |

The front view wins when the two kit views disagree. The kit's front and back drawings cannot both be met by one rigid head: the back nape is wider than the cheeks, and the two drawings bulge on opposite sides. So below the cheeks the back hair is a few units narrower than the back drawing.

## Weak spots / what's left
- Jeans are narrower than the 2D kit. The kit's legs overlap in the middle, which 3D legs cannot do. Shoes point forward, so from the front they look narrower than the kit's profile-drawn shoes.
- No hand detail: ball mitts as in the kit, plus a thumb nub. They can't grip a laptop or cake knife convincingly. Typing poses will need posing care, or real fingers later.
- Face states are object swaps. Blinks pop rather than squash (fine for this style). Lip-sync is open/closed only.
- Hair is a solid helmet with painted strand highlights. Close-ups show it as smooth plastic, not strands (intended Pixar look).
- The jersey's navy side panel covers the whole flank in side and 3/4 views.
- Not done yet: sitting pose test, export (GLB/FBX), the reel itself.
