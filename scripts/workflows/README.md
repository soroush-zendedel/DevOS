# DevOS workflow scripts

These helpers replace repeated command snippets. Run them from any directory; paths are resolved from each script's location or supplied as parameters.

## Debian builder

From the repository checkout, refresh `main` with fast-forward-only semantics, build, check that the Xorg input driver is present, verify the ISO, and show builder addresses:

```sh
./scripts/workflows/linux/update-build-iso.sh
```

The script stops if tracked local edits exist. Generated live-build files are left in place for caching.

## Find the Hyper-V guest address (Windows PowerShell)

If exactly one VM is running, it is selected automatically. With multiple running VMs, name the intended guest:

```powershell
.\scripts\workflows\windows\Get-DevOSVmIp.ps1 -VMName DevOS-Live-Test
```

## Copy and verify the ISO

The script asks the builder for the source SHA-256, copies to a hash-named file, then compares the local hash. Pass your identity file only at runtime if needed; never commit private keys.

```powershell
.\scripts\workflows\windows\Copy-DevOSIso.ps1 `
  -BuilderHost 172.24.x.x `
  -BuilderUser soroush `
  -RemoteIsoPath /home/soroush/devos/build/devos-amd64.iso `
  -DestinationDirectory H:\DevOS\isos `
  -IdentityFile $HOME\.ssh\id_ed25519
```

Omit `-IdentityFile` when the current SSH agent/default key already works. The host/IP, destination, and key are runtime inputs, not repository settings.

## Attach ISO to a Hyper-V VM

The VM must already be **Off**. The script checks state before changing its DVD or boot order. It never stops, starts, or modifies a running or saved VM. `-WhatIf` previews the action.

```powershell
.\scripts\workflows\windows\Set-DevOSVmIso.ps1 `
  -VMName DevOS-Live-Test `
  -IsoPath H:\DevOS\isos\devos-amd64-0123456789ab.iso
```

Start the VM manually in Hyper-V after reviewing the attached ISO.
