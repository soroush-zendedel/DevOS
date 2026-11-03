# Development

## Builder prerequisites

Use a Debian 13 AMD64 machine with Git and network access to the configured Debian mirrors. The Builder used to validate this configuration runs `live-build` version `20250505+deb13u1`. Install build dependencies with `sudo ./scripts/install-dependencies.sh`.

## Build an ISO

From the repository root, run `sudo ./scripts/build-iso.sh`. The script cleans generated build stages while preserving live-build caches, regenerates configuration, invokes Debian Live Build, and places the result at `build/devos-amd64.iso`. Generated working files and images are ignored by Git.

`auto/config` and the package lists are the version-controlled sources of build settings. The build script regenerates live-build's derived `config/binary`, `config/bootstrap`, `config/chroot`, `config/common`, `config/source`, default package list, and system hook symlinks on each run so stale generated values cannot override the source configuration. The project pins bootstrap, chroot, and binary stages to Trixie, uses the IranServer Debian and security mirrors, and disables automatic installation of every firmware package. Add required firmware packages explicitly after testing them. Check mirror reachability and `lb config --help` on the Builder before changing these settings. `config/hooks/` contains package-provided symlinks and is ignored; force-add project-owned hooks if needed.

Because APT recommends are disabled to keep the image small, packages required for Live boot and automatic console login must be listed explicitly (including `user-setup`).

## Git workflow

Keep `main` synchronized with `origin/main` before starting work. Make changes in a focused commit, review `git diff --check` and `git status`, then push the commit to GitHub. Treat generated build output as disposable and never commit ISO images, credentials, private keys, or machine-specific state.
