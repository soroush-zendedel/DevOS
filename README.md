# DevOS

DevOS is a lightweight, development-focused live Linux image based on Debian 13 (Trixie).

## Current status

Repository scaffolding is in progress. No custom ISO has been built or validated yet.

## Build

On a Debian 13 AMD64 builder with `live-build` installed, run:

```sh
sudo ./scripts/build-iso.sh
```

The generated image is written to `build/` and is not tracked by Git. See [docs/development.md](docs/development.md) for setup details and [docs/testing.md](docs/testing.md) for validation steps.

## Safety

Building the ISO does not install DevOS or modify host disks. Do not attempt a permanent installation until the ISO has been tested in a VM and the target disk has been positively identified.
