# Assemble the low-res animatic: Blender frames + preview mix + subtitle overlay + soft vignette -> previews\animatic.mp4
$root   = 'C:\Users\acer\Downloads\jako-frames\reel-1k-cake'
$ffmpeg = 'C:\Users\acer\ffmpeg\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe'
& $ffmpeg -y -loglevel error -framerate 24 -i "$root\previews\animatic_frames\%04d.png" -i "$root\subs\subs_540.mov" -i "$root\audio\mix_preview.wav" `
    -filter_complex "[0:v]vignette=angle=PI/5:mode=forward[v];[v][1:v]overlay=0:0:format=auto,format=yuv420p[out]" `
    -map "[out]" -map 2:a -c:v libx264 -preset medium -crf 20 -c:a aac -b:a 192k -shortest -movflags +faststart "$root\previews\animatic.mp4"
if (Test-Path "$root\previews\animatic.mp4") { "OK $root\previews\animatic.mp4" } else { 'FAILED' }
