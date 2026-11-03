# DevOS command reference

The Python CLI dispatches to these workflow scripts where an OS-specific tool is needed. Run `devos --help` for the full command list.

## Set up the Python environment

Run from the repository root:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install --editable .
```

On Windows PowerShell, use:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --editable .
```

The `devos` command is available while the virtual environment is active; no shell profile changes are made.

## Debian builder

```sh
devos build
devos verify
devos clean
devos clean --purge
devos update
devos update-build
devos deps
```

`devos build` builds the current checkout. `devos update-build` fast-forwards from the configured Git upstream first, then builds and verifies. `devos clean` removes generated live-build state while retaining caches; `devos clean --purge` also removes caches. The update-build workflow stops if tracked local edits exist.

## Find the Hyper-V guest address (Windows PowerShell)

If exactly one VM is running, `devos vm-ip` selects it automatically. With multiple running VMs, specify the intended guest:

```powershell
devos vm-ip --vm-name DevOS-Live-Test
```

## Copy and verify the ISO

The command asks the builder for the source SHA-256, copies to a hash-named file, then compares the local hash. Host address, username, source path, destination, and optional key are passed at runtime.

```powershell
devos copy-iso `
  --builder-host YOUR_BUILDER_IP `
  --builder-user YOUR_LINUX_USER `
  --remote-iso-path /home/YOUR_LINUX_USER/devos/build/devos-amd64.iso `
  --destination-directory H:\DevOS\isos `
  --identity-file $HOME\.ssh\id_ed25519
```

Omit `--identity-file` when the current SSH agent/default key already works. Private keys and machine-specific IPs are never stored in the repository.

## Attach ISO to a Hyper-V VM

The VM must already be **Off**. The command checks its state before changing the DVD or boot order. It never stops or starts the VM. `--what-if` previews the action.

```powershell
devos attach-iso `
  --vm-name DevOS-Live-Test `
  --iso-path H:\DevOS\isos\devos-amd64-0123456789ab.iso
```

Start the VM manually after reviewing the attached ISO.
