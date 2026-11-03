# DevOS

DevOS is a work-in-progress project for building a lightweight, development-focused Debian 13 (Trixie) Live ISO for AMD64. A Python command-line tool drives Debian Live Build inside a Debian Docker container; Windows helpers support Hyper-V VM workflows.

The current project creates Live media only. It does not include a permanent installer, hardware detection, or a claim of support for physical machines. The image and VM workflow still need end-to-end validation.

## What the project contains

- **Image build:** Debian Live Build configuration, package lists, chroot hooks, and an ISO verification script.
- **Included software in the tracked package lists:** Zsh, Kitty, Openbox, Xorg, Git, OpenSSH, basic command-line utilities, build-essential, Python 3, Python virtual environments, and rsync. The optional package list is empty.
- **Intended session:** a terminal-first Xorg/Openbox session that starts Kitty. Tracked sources configure automatic login on tty2; the built ISO still needs a VM boot check (see [known gaps](#known-gaps-from-source-review)).
- **CLI:** `devos build`, `verify`, `clean`, `deps`, `update`, `update-build`, `status`, and `logs` manage the build. `ssh`, `vm-ip`, `copy-iso`, and `attach-iso` support Windows/OpenSSH/Hyper-V workflows.
- **Build isolation:** the builder uses a persistent Docker volume for its Linux workspace and caches. Source inputs are mounted read-only, and the host `build` folder is mounted directly at the builder output path, so the ISO is written to `build/devos-amd64.iso` and hashed there. The builder container is privileged because Live Build needs to prepare chroots.

The project does not currently include the planned VS Code, Firefox, Thunar, Starship, JetBrainsMono Nerd Font, Docker Engine, Ollama, or LiteLLM setup described in [PROPOSAL.md](PROPOSAL.md).

### CLI command overview

| Command | Purpose |
| --- | --- |
| `devos build` | Build the ISO through Docker Compose. |
| `devos verify` | Print the ISO SHA-256 and inspect its boot catalog. |
| `devos clean [--purge]` | Remove generated build state; `--purge` also deletes the builder volume and caches. |
| `devos build --up` | Refresh the Debian builder image without cache, then build the ISO. |
| `devos deps` | Refresh the Debian builder image only; kept as a standalone maintenance command. |
| `devos update` | Fast-forward the current Git branch from its upstream. |
| `devos update-build` | Pull, build, and verify; currently checks tracked changes only. |
| `devos status` | Show Git checkout status. |
| `devos logs` | Request recent builder service logs; see the limitation below. |
| `devos ssh`, `vm-ip`, `copy-iso`, `attach-iso` | Windows, OpenSSH, and Hyper-V workflows described below. |

## Build the ISO

Requirements: Python 3.10+, Docker Desktop or Docker Engine with Docker Compose v2, and an available Debian mirror. The CLI and its Python dependencies are installed in a project-local virtual environment; the ISO builder tools are installed in the container.

From the repository root:

```sh
python -m venv .venv
source .venv/bin/activate
python install.py iran
devos build
devos verify
```

In Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python install.py iran
devos build
devos verify
```

`python install.py iran` installs this checkout in editable mode in the active virtual environment, trying the Iranian PyPI mirrors in order and then official PyPI. This avoids downloading an unrelated package with the same name. `install.py` discovers country arguments from `config/mirrors/<country>/pypi.txt`, so adding and committing a new country file makes that argument available automatically. `devos build` builds the ISO and builds the Docker image if needed. Docker image APT packages use the ordered Iranian Debian mirrors in `config/mirrors/iran/debian.txt`, then official Debian mirrors. The Docker builder and resulting Live image both receive `/etc/pip.conf` with Novin, Chabokan, and HyperClouds before official PyPI. For other Python package operations, use `python scripts/pip-mirror.py ...` for strict sequential fallback. Set `DEVOS_PYPI_MIRRORS` to provide a comma-separated mirror list. Override Debian URLs with `DEVOS_DEBIAN_MIRROR` and `DEVOS_SECURITY_MIRROR`. Live Build caches APT package indices across builds to avoid repeatedly downloading repository lists; run `devos clean --purge` when you want to discard those cached lists and fetch fresh repository metadata. Use `devos build --up` to force-refresh the builder image before building the ISO. `devos clean` removes generated Live Build state while retaining caches; `devos clean --purge` also deletes the Docker build volume and its caches. Both commands leave the host ISO in `build/` intact.

The CLI creates `.devos-ssh` and `.devos-ssh.pub` on the first build. The private key is generated without a passphrase and is ignored by Git; protect it with the host's file permissions and do not share it. Only the public key is passed to the build container. The tracked Live Build hook places that public key in the live user's skeleton so it is copied into the user's home when Live Config creates the account at boot.

## Windows and Hyper-V workflows

```powershell
devos vm-ip --vm-name ExampleVM
devos ssh --vm-name ExampleVM
devos logs --lines 500
devos attach-iso --vm-name ExampleVM --iso-path H:\DevOS\devos-amd64.iso --what-if
```

`devos vm-ip` can auto-select when exactly one VM is running. `devos ssh` discovers a guest address and uses the project key; the first connection asks whether to trust the scanned host fingerprint. `devos attach-iso` changes a VM only while it is Off and does not start it. `devos copy-iso` copies an ISO from a remote Linux builder and compares remote and local SHA-256 hashes. See [scripts/workflows/README.md](scripts/workflows/README.md) for full examples.

## Known gaps from source review

Reviewed on 2026-11-03. These findings come from the repository source and current workspace state. An ISO build was attempted, but Docker could not resolve the Debian APT mirrors; no ISO was produced and no VM boot test was run.

### Resolved in this update

The project hook `config/hooks/normal/1300-devos-ssh-key.hook.chroot` is now allowed by a narrow `.gitignore` rule, so it can be included in a clean checkout. The hook provisions `/etc/skel/.ssh/authorized_keys` instead of assuming the Live `user` already exists during image creation; Live Config creates that user at boot and copies the skeleton into its home. The hook still configures key-only SSH and enables the SSH service. The Docker entrypoint explicitly marks the hook executable in its Linux build workspace. This resolves the source-tracking and build-time user assumption; the resulting ISO still needs a clean-checkout build and VM SSH test.

The tty2 login path is now configured in tracked sources: a systemd drop-in starts `agetty` with `--autologin user`, and a chroot hook enables `getty@tty2.service` in the built image. The Docker entrypoint marks the hook executable. This makes the tty2-to-Zsh-to-Xorg startup reproducible; an ISO build and VM boot check are still required to confirm it at runtime.

### Remaining gaps

1. **The Hyper-V initramfs claim does not match the module list.** The tracked initramfs file lists optical-media, SquashFS, and generic USB HID modules. It does not explicitly list the Hyper-V storage or VMBus modules described in the development documentation. Confirm the required modules and test both Hyper-V Generation 1 and Generation 2.
2. **ISO verification is informational rather than a complete bootability check.** `verify-iso.sh` prints a SHA-256 and asks `xorriso` to report the El Torito catalog, but it does not assert that BIOS and UEFI boot entries are present or boot the ISO. Keep VM boot checks as release requirements and strengthen the script's assertions.
3. **`devos logs` cannot reliably show build output from previous builds.** Builds run with `docker compose run --rm`, which removes the one-off builder container when it exits. The command then uses `docker compose logs builder`, which reads service-container logs and does not retain those removed run-container logs. Capture build output to a persistent host log or adjust the build container lifecycle.
4. **The named-VM IP lookup can accept a non-running VM.** `Get-VM` filters to Running VMs only when no name is supplied. With `-VMName`, it queries that VM regardless of state and can return a stale adapter address. Check VM state in both paths before returning an address.
5. **`update-build` checks tracked changes only.** Its clean-tree check omits untracked files, including ignored local build hooks. Such files can alter the image even as the command pulls and builds another revision. Make build inputs explicit and report local overrides before updating.
6. **The build is configured for repeatability, but not pinned to an immutable toolchain.** The Debian builder image uses the moving `debian:trixie-slim` tag and package versions are not locked. Mirror contents change over time, so rebuilding the same Git revision may produce a different image. Record the build toolchain and package manifest; consider pinning the builder image and defining an update policy.
7. **There is no automated test suite in the repository.** `docs/testing.md` is a manual VM checklist. CLI behavior, shell/PowerShell workflows, package manifests, and clean-checkout builds need automated or repeatable checks.

## Planned work

Prioritize in this order:

1. Build from a clean checkout and verify key-only SSH access in a disposable VM.
2. Build and verify the configured tty2 automatic-login path; verify Live boot, console access, SSH behavior, and the graphical session in Hyper-V Generation 1 and 2.
3. Correct and validate initramfs support for Hyper-V storage, then verify ISO BIOS/UEFI boot entries and strengthen `devos verify`.
4. Make builder logs useful after failed and completed builds; make `vm-ip` reject stopped VMs; add automated checks for CLI and Windows helper behavior.
5. Improve build traceability with pinned or recorded tool versions, package manifests, and a documented mirror/update policy.
6. Add hardware-aware driver and firmware profiles, then test USB/UEFI boot on real hardware. Firmware is not automatically included in the current configuration.
7. Design a safe permanent installer as a separate milestone, with explicit target-disk confirmation and documented backup requirements.
8. Evaluate the planned developer tools and theme/font setup from [PROPOSAL.md](PROPOSAL.md), keeping large or always-on services optional.

## Safety and support boundary

Building the ISO writes build outputs to the project directory and uses a privileged Linux container; review the Compose configuration before building an unfamiliar checkout. Live boot is the only intended use today. Do not use this ISO to install to a physical disk: an installer and its disk-selection safeguards do not exist yet. Test only in a disposable VM until boot behavior has been validated.

## Project guides

- [Architecture](docs/architecture.md)
- [Installation status and limits](docs/installation.md)
- [Development and build details](docs/development.md)
- [Manual testing checklist](docs/testing.md)
- [Windows and Hyper-V command examples](scripts/workflows/README.md)
