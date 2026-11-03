$ErrorActionPreference = 'Stop'
$Command = if ($args.Count -gt 0) { [string]$args[0] } else { 'help' }
$Arguments = if ($args.Count -gt 1) { @($args | Select-Object -Skip 1) } else { @() }
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

function Show-Usage {
    @'
DevOS project command (Windows PowerShell)

Usage: devos <command> [parameters]

  vm-ip       Find the IP for a running Hyper-V guest
  copy-iso    Copy ISO from Debian and compare source/local SHA-256
  attach-iso  Attach ISO to a Hyper-V VM only when its state is Off

Example:
  devos vm-ip -VMName DevOS-Live-Test
  devos copy-iso -BuilderHost 172.24.x.x -DestinationDirectory H:\DevOS\isos
  devos attach-iso -VMName DevOS-Live-Test -IsoPath H:\DevOS\isos\devos.iso

Build, clean, deps, update, update-build, and verify run on the Debian builder.
'@
}

switch ($Command.ToLowerInvariant()) {
    { $_ -in 'help', '-h', '--help' } { Show-Usage; break }
    'vm-ip' {
        & (Join-Path $scriptRoot 'workflows\windows\Get-DevOSVmIp.ps1') @Arguments
        break
    }
    'copy-iso' {
        & (Join-Path $scriptRoot 'workflows\windows\Copy-DevOSIso.ps1') @Arguments
        break
    }
    'attach-iso' {
        & (Join-Path $scriptRoot 'workflows\windows\Set-DevOSVmIso.ps1') @Arguments
        break
    }
    { $_ -in 'build', 'clean', 'verify', 'deps', 'update', 'update-build' } {
        throw "'$Command' runs on the Debian builder. Use the Linux devos command there."
    }
    default { throw "Unknown DevOS command '$Command'. Run 'devos help'." }
}
