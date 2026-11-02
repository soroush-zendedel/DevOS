# Development

## Builder prerequisites

Use a Debian 13 AMD64 machine with Git and network access to the configured Debian mirrors. Install build dependencies with `sudo ./scripts/install-dependencies.sh`.

## Build an ISO

From the repository root, run `sudo ./scripts/build-iso.sh`. The script invokes Debian Live Build and places the result at `build/devos-amd64.iso`. Generated working files and images are ignored by Git.

Review `lb config --help` and the installed `live-build` version when changing build options; behavior can vary by package version. Commit only source configuration and documentation.
