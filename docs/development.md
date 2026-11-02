# Development

## Builder prerequisites

Use a Debian 13 AMD64 machine with Git and network access to the configured Debian mirrors. The Builder used to validate this configuration runs `live-build` version `20250505+deb13u1`. Install build dependencies with `sudo ./scripts/install-dependencies.sh`.

## Build an ISO

From the repository root, run `sudo ./scripts/build-iso.sh`. The script invokes Debian Live Build and places the result at `build/devos-amd64.iso`. Generated working files and images are ignored by Git.

`auto/config` is the version-controlled source of build settings. Its options must be supported by the Debian Builder's installed `live-build`; check `lb config --help` before changing them. In particular, this project uses the singular `--architecture` option, sets both `--distribution-chroot` and `--distribution-binary` to `trixie`, and uses `--debian-installer none` to disable the installer. Verify the generated values in `config/bootstrap` and `config/binary` after running `lb config`.

## Git workflow

Keep `main` synchronized with `origin/main` before starting work. Make changes in a focused commit, review `git diff --check` and `git status`, then push the commit to GitHub. Treat generated build output as disposable and never commit ISO images, credentials, private keys, or machine-specific state.
