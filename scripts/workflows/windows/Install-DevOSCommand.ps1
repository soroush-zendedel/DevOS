[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$cli = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) 'devos.ps1'
if (-not (Test-Path -LiteralPath $cli -PathType Leaf)) { throw "DevOS PowerShell CLI not found: $cli" }

$profilePath = $PROFILE.CurrentUserCurrentHost
$profileDirectory = Split-Path -Parent $profilePath
New-Item -ItemType Directory -Force -Path $profileDirectory | Out-Null
if (Test-Path -LiteralPath $profilePath) { $profileText = Get-Content -LiteralPath $profilePath -Raw } else { $profileText = '' }
$marker = '# DevOS command launcher'
if ($profileText.Contains($marker)) {
    Write-Output "DevOS launcher is already configured in $profilePath. Reopen PowerShell or dot-source the profile."
    return
}

$escapedCli = $cli.Replace("'", "''")
$launcher = @"
$marker
function devos {
    & '$escapedCli' @args
}
"@
Add-Content -LiteralPath $profilePath -Value $launcher
Write-Output "Added devos command to $profilePath. Run `. `$PROFILE` to enable it now, or open a new PowerShell window."
