# DevOS

DevOS is a lightweight, development-focused live Linux image based on Debian 13 (Trixie).

## Project command

The project provides a `devos` command for repeatable builder and Hyper-V tasks. Install it from the repository checkout:

```sh
./scripts/workflows/linux/install-devos-command.sh
```

Then run `devos help`. Common Debian builder commands are:

```sh
devos build
devos verify
devos clean
devos update-build
```

On Windows, run `scripts/workflows/windows/Install-DevOSCommand.ps1` once from PowerShell, then use `devos vm-ip`, `devos copy-iso`, and `devos attach-iso`. See [scripts/workflows/README.md](scripts/workflows/README.md) for examples and parameter details. The generated image is written to `build/` and is not tracked by Git. See [docs/development.md](docs/development.md) for setup details and [docs/testing.md](docs/testing.md) for validation steps.

## Safety

Building the ISO does not install DevOS or modify host disks. Do not attempt a permanent installation until the ISO has been tested in a VM and the target disk has been positively identified.
