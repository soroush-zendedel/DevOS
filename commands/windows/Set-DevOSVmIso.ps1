[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)] [string] $VMName,
    [Parameter(Mandatory)] [string] $IsoPath
)

$ErrorActionPreference = 'Stop'
Import-Module Hyper-V
if (-not (Test-Path -LiteralPath $IsoPath -PathType Leaf)) { throw "ISO not found: $IsoPath" }
$vm = Get-VM -Name $VMName
if ($vm.State -ne 'Off') {
    throw "VM '$VMName' is $($vm.State). Shut it down yourself, then rerun. This script will not stop or change a running/saved VM."
}

if ($PSCmdlet.ShouldProcess($VMName, "Attach ISO $IsoPath and set DVD boot preference")) {
    $dvd = Get-VMDvdDrive -VMName $VMName | Select-Object -First 1
    if ($dvd) {
        Set-VMDvdDrive -VMName $VMName -ControllerNumber $dvd.ControllerNumber -ControllerLocation $dvd.ControllerLocation -Path $IsoPath
        $dvd = Get-VMDvdDrive -VMName $VMName | Where-Object Path -eq $IsoPath | Select-Object -First 1
    } else {
        $dvd = Add-VMDvdDrive -VMName $VMName -Path $IsoPath -Passthru
    }

    if ($vm.Generation -eq 2) {
        Set-VMFirmware -VMName $VMName -FirstBootDevice $dvd
    } else {
        Set-VMBios -VMName $VMName -StartupOrder @('CD', 'IDE', 'LegacyNetworkAdapter', 'Floppy')
    }
    Get-VMDvdDrive -VMName $VMName | Select-Object VMName, Path, ControllerNumber, ControllerLocation
    Write-Output "ISO attached. VM remains Off; start it manually when ready."
}
