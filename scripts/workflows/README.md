# DevOS workflow scripts

These helpers replace repeated command snippets. Run them from any directory; paths are resolved from each script's location or supplied as parameters.

Install the `devos` command once:

```sh
./scripts/workflows/linux/install-devos-command.sh
```

Then use `devos help` to see commands. The launcher resolves the repository from its own location.

## Debian builder

From any directory, run `devos build` to build the current checkout or `devos update-build` to fast-forward from the configured Git upstream first, build, check that the Xorg input driver is present, verify the ISO, and show builder addresses:

```sh
devos build
devos verify
devos update-build
```

`devos build` builds the current checkout. `devos update-build` fast-forwards from GitHub first, then builds and verifies. `devos clean` removes generated live-build state while retaining caches; `devos clean --purge` also removes caches. The update-build workflow stops if tracked local edits exist.

## Find the Hyper-V guest address (Windows PowerShell)

Install the PowerShell command once:

```powershell
.\scripts\workflows\windows\Install-DevOSCommand.ps1
. $PROFILE
```

If exactly one VM is running, `devos vm-ip` selects it automatically. With multiple running VMs, name the intended guest:

```powershell
devos vm-ip -VMName DevOS-Live-Test
```

## Copy and verify the ISO

The script asks the builder for the source SHA-256, copies to a hash-named file, then compares the local hash. Pass your identity file only at runtime if needed; never commit private keys.

```powershell
devos copy-iso `
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
devos attach-iso `
  -VMName DevOS-Live-Test `
  -IsoPath H:\DevOS\isos\devos-amd64-0123456789ab.iso
```

Start the VM manually in Hyper-V after reviewing the attached ISO.
