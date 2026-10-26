# Waits for the Blender render, resumes it if it stopped early, then builds out\reel.mp4 with the audio.
# Keeps the PC from idle-sleeping while it runs (released automatically when this script exits).
param([int]$RenderPid = 0)

$root    = 'C:\Users\acer\Downloads\jako-frames\reel-agents-dolomites'
$blender = 'C:\Users\acer\Blender\blender-4.5.15-windows-x64\blender.exe'
$ffmpeg  = 'C:\Users\acer\ffmpeg\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe'
$log     = "$root\renders\finish.log"
$total   = 1190

Add-Type -Namespace W -Name P -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f);'
[W.P]::SetThreadExecutionState(0x80000001) | Out-Null   # ES_CONTINUOUS | ES_SYSTEM_REQUIRED

function Say($m) { "$(Get-Date -Format 'HH:mm:ss') $m" | Out-File $log -Append -Encoding utf8 }
function Done { (Get-ChildItem "$root\renders" -Filter 'frame_*.png').Count }

Say "watcher started, render pid $RenderPid"
if ($RenderPid) { try { Wait-Process -Id $RenderPid -ErrorAction Stop } catch {} }

for ($try = 1; (Done) -lt $total -and $try -le 3; $try++) {
    Say "only $(Done)/$total frames, resuming render (try $try)"
    Start-Process -FilePath $blender -ArgumentList '-b', "`"$root\blender\reel.blend`"", '-x', '1', '-a' `
        -RedirectStandardOutput "$root\renders\render_resume$try.log" -WindowStyle Hidden -Wait
}

if ((Done) -lt $total) { Say "STOPPED: still $(Done)/$total frames"; exit 1 }

New-Item -ItemType Directory -Force "$root\out" | Out-Null
Say 'all frames done, encoding mp4'
& $ffmpeg -y -loglevel error -framerate 24 -i "$root\renders\frame_%04d.png" -i "$root\audio\mix_preview.wav" `
    -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 320k -shortest "$root\out\reel.mp4"
if (Test-Path "$root\out\reel.mp4") { Say "DONE: $root\out\reel.mp4" } else { Say 'ffmpeg failed'; exit 1 }
