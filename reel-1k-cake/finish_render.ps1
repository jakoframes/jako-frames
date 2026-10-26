# finish_render.ps1 - detached FINAL render of the cake reel. Keeps the PC awake, (re)starts Blender until all 952
# frames exist (0-byte placeholders from a crash are removed first), makes sure the full-res subtitle overlay exists,
# then builds out\reel_1k.mp4 = frames + vignette + burned-in subtitles + audio/mix_preview.wav.
# Start detached:  Start-Process powershell -WindowStyle Hidden -ArgumentList '-ExecutionPolicy','Bypass','-File','C:\Users\acer\Downloads\jako-frames\reel-1k-cake\finish_render.ps1'
# Progress: renders\finish.log ("DONE: ..." at the end). Safe to run again after a reboot.
$root    = 'C:\Users\acer\Downloads\jako-frames\reel-1k-cake'
$blender = 'C:\Users\acer\Blender\blender-4.5.15-windows-x64\blender.exe'
$ffmpeg  = 'C:\Users\acer\ffmpeg\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe'
$edge    = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
$rem     = 'C:\Users\acer\Downloads\jako-frames\reel-what-the-heck'
$frames  = "$root\renders"
$log     = "$frames\finish.log"
$total   = 952
New-Item -ItemType Directory -Force $frames, "$root\out" | Out-Null

Add-Type -Namespace W -Name P -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f);'
[W.P]::SetThreadExecutionState(0x80000001) | Out-Null   # ES_CONTINUOUS | ES_SYSTEM_REQUIRED (released on exit)

function Say($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" | Out-File $log -Append -Encoding utf8 }
function Done { (Get-ChildItem $frames -Filter '*.png' | Where-Object { $_.Length -gt 0 }).Count }

Say "watcher started: $(Done)/$total frames present"
for ($try = 1; (Done) -lt $total -and $try -le 6; $try++) {
    Get-ChildItem $frames -Filter '*.png' | Where-Object { $_.Length -eq 0 } | ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force }
    Say "rendering (try $try), $(Done)/$total done"
    Start-Process -FilePath $blender -ArgumentList '-b', '-y', "`"$root\blender\scene.blend`"", '--python', "`"$root\blender\render_final.py`"" `
        -RedirectStandardOutput "$frames\render_try$try.log" -RedirectStandardError "$frames\render_try$try.err" -WindowStyle Hidden -Wait
}
if ((Done) -lt $total) { Say "STOPPED: only $(Done)/$total frames"; exit 1 }

$subs = "$root\subs\subs_1080.mov"
if (-not (Test-Path $subs)) {
    Say 'rendering full-res subtitle overlay (Remotion)'
    Push-Location $rem
    & npx remotion render src/cake/index.ts CakeSubs $subs --codec=prores --prores-profile=4444 --image-format=png `
        --pixel-format=yuva444p10le --browser-executable="$edge" --log=error | Out-Null
    Pop-Location
}
if (-not (Test-Path $subs)) { Say 'subtitle overlay missing'; exit 1 }

Say 'all frames done, encoding out\reel_1k.mp4'
& $ffmpeg -y -loglevel error -framerate 24 -i "$frames\%04d.png" -i $subs -i "$root\audio\mix_preview.wav" `
    -filter_complex "[0:v]vignette=angle=PI/5:mode=forward[v];[v][1:v]overlay=0:0:format=auto,format=yuv420p[out]" `
    -map "[out]" -map 2:a -c:v libx264 -preset slow -crf 16 -c:a aac -b:a 320k -shortest -movflags +faststart "$root\out\reel_1k.mp4"
# clean version without burned-in subtitles too (for re-editing)
& $ffmpeg -y -loglevel error -framerate 24 -i "$frames\%04d.png" -i "$root\audio\mix_preview.wav" `
    -vf "vignette=angle=PI/5:mode=forward,format=yuv420p" -c:v libx264 -preset slow -crf 16 -c:a aac -b:a 320k -shortest -movflags +faststart "$root\out\reel_1k_nosubs.mp4"
if (Test-Path "$root\out\reel_1k.mp4") { Say "DONE: $root\out\reel_1k.mp4" } else { Say 'ffmpeg failed'; exit 1 }
