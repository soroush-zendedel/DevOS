# DevOS

DevOS is a lightweight, development-focused live Linux image based on Debian 13 (Trixie).

## Install the project command

Install the CLI and its dependencies in a project-local Python virtual environment. Run these commands from the repository root.

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

The `devos` command is then available while that virtual environment is active. Docker Desktop or Docker Engine with the Compose v2 plugin must also be installed and running. The ISO builder and its Debian dependencies run in a Linux container, so they are not installed on the host. See `devos --help` for the full command list.

Common Debian builder commands:

```sh
devos build
devos verify
devos clean
devos update-build
```

On Windows, activate the same virtual environment and use `devos build`, `devos verify`, and `devos clean` through Docker Compose, as well as `devos vm-ip`, `devos copy-iso`, and `devos attach-iso` for Hyper-V. The generated ISO is written to `build/` and is not tracked by Git. See [scripts/workflows/README.md](scripts/workflows/README.md) for examples and [docs/development.md](docs/development.md) for build details.

## Planned work

- Add a later hardware-aware build option that detects the target computer's hardware and includes matching drivers plus universal drivers. This is a future phase; the current build does not inspect hardware.

## Safety

Building the ISO does not install DevOS or modify host disks. Do not attempt a permanent installation until the ISO has been tested in a VM and the target disk has been positively identified.
