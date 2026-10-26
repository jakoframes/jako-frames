# Screenshots every page from render_ref.js with headless Edge into ref\png\
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
node "$here\render_ref.js" | Out-Null
$edge = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
$png = Join-Path $here 'png'
New-Item -ItemType Directory -Force $png | Out-Null
$pages = Get-Content "$here\html\pages.json" -Raw | ConvertFrom-Json
foreach ($p in $pages) {
  $src = 'file:///' + (Join-Path $here "html\$($p.name).html").Replace('\', '/')
  $dst = Join-Path $png "$($p.name).png"
  $args = @('--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
            "--window-size=$($p.w),$($p.h)", "--screenshot=$dst", "--user-data-dir=$env:TEMP\jako_edge_prof", $src)
  $proc = Start-Process -FilePath $edge -ArgumentList $args -Wait -PassThru -WindowStyle Hidden
  Write-Output "$($p.name): exit $($proc.ExitCode) $(Test-Path $dst)"
}
