[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string] $BuilderHost,
    [Parameter()] [string] $BuilderUser = 'soroush',
    [Parameter()] [string] $RemoteIsoPath = '/home/soroush/devos/build/devos-amd64.iso',
    [Parameter(Mandatory)] [string] $DestinationDirectory,
    [Parameter()] [string] $IdentityFile
)

$ErrorActionPreference = 'Stop'
foreach ($tool in 'ssh', 'scp') {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { throw "OpenSSH command '$tool' is not available." }
}
if ($RemoteIsoPath -notmatch '^/[A-Za-z0-9._/-]+$') {
    throw 'RemoteIsoPath must be an absolute Linux path containing only letters, numbers, dots, underscores, slashes, or hyphens.'
}
if ($BuilderHost -match '[\s`''"]' -or $BuilderUser -match '[\s@`''"]') { throw 'BuilderHost or BuilderUser contains unsupported characters.' }
if ($IdentityFile -and -not (Test-Path -LiteralPath $IdentityFile -PathType Leaf)) { throw "Identity file not found: $IdentityFile" }

$sshOptions = @('-o', 'BatchMode=yes')
if ($IdentityFile) { $sshOptions += @('-i', $IdentityFile) }
$target = "${BuilderUser}@${BuilderHost}"
$remoteOutput = & ssh @sshOptions $target "sha256sum -- '$RemoteIsoPath'"
if ($LASTEXITCODE -ne 0) { throw 'Could not calculate the ISO hash on the builder.' }
$remoteText = $remoteOutput -join "`n"
if ($remoteText -notmatch '(?m)^([0-9a-fA-F]{64})\s+') { throw "Unexpected sha256sum output: $remoteText" }
$expectedHash = $Matches[1].ToUpperInvariant()

New-Item -ItemType Directory -Force -Path $DestinationDirectory | Out-Null
$localPath = Join-Path $DestinationDirectory ("devos-amd64-{0}.iso" -f $expectedHash.Substring(0, 12))
if (Test-Path -LiteralPath $localPath) {
    $existingHash = (Get-FileHash -LiteralPath $localPath -Algorithm SHA256).Hash
    if ($existingHash -eq $expectedHash) {
        Write-Output "Already present and verified: $localPath ($expectedHash)"
        return
    }
    throw "Destination exists with a different hash; refusing to overwrite: $localPath"
}

$partialPath = "$localPath.partial"
$scpOptions = @('-o', 'BatchMode=yes')
if ($IdentityFile) { $scpOptions += @('-i', $IdentityFile) }
& scp @scpOptions "${target}:$RemoteIsoPath" $partialPath
if ($LASTEXITCODE -ne 0) { throw "SCP failed; partial transfer, if any, is at $partialPath and can be overwritten by a retry." }
$actualHash = (Get-FileHash -LiteralPath $partialPath -Algorithm SHA256).Hash
if ($actualHash -ne $expectedHash) {
    throw "Hash mismatch after copy. Remote: $expectedHash Local: $actualHash Partial file: $partialPath"
}
Move-Item -LiteralPath $partialPath -Destination $localPath
Write-Output "Copied and verified: $localPath ($actualHash)"
