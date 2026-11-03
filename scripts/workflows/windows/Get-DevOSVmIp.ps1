[CmdletBinding()]
param(
    [Parameter()]
    [string] $VMName,
    [switch] $Quiet
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Module -ListAvailable -Name Hyper-V)) {
    throw 'The Hyper-V PowerShell module is not available on this computer.'
}
Import-Module Hyper-V

if ($VMName) {
    $vms = @(Get-VM -Name $VMName)
} else {
    $vms = @(Get-VM | Where-Object State -eq 'Running')
    if ($vms.Count -gt 1) {
        $vms | Select-Object Name, State | Format-Table -AutoSize
        throw 'More than one VM is running. Re-run with -VMName to choose one.'
    }
}

if ($vms.Count -eq 0) { throw 'No matching VM was found.' }
$results = foreach ($vm in $vms) {
    $adapters = @(Get-VMNetworkAdapter -VMName $vm.Name)
    foreach ($adapter in $adapters) {
        $ips = @($adapter.IPAddresses | Where-Object {
            $_ -match '^\d{1,3}(\.\d{1,3}){3}$' -and $_ -notmatch '^169\.254\.'
        })
        if ($ips.Count -eq 0) {
            $mac = $adapter.MacAddress -replace '[^0-9A-Fa-f]', ''
            $ips = @(Get-NetNeighbor -AddressFamily IPv4 -ErrorAction SilentlyContinue |
                Where-Object { (($_.LinkLayerAddress -replace '[^0-9A-Fa-f]', '').ToUpper()) -eq $mac.ToUpper() } |
                Select-Object -ExpandProperty IPAddress -Unique)
        }
        foreach ($ip in $ips) {
            [pscustomobject]@{
                VMName = $vm.Name
                IPAddress = $ip
                Adapter = $adapter.Name
                VMState = $vm.State
            }
        }
    }
}

if (-not $results) { throw 'No guest IPv4 address found. Confirm the VM is running and has network connectivity.' }
if ($Quiet) { $results | Select-Object -First 1 | ConvertTo-Json -Compress }
else { $results | Format-Table -AutoSize }
