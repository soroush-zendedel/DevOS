# Development

## Builder prerequisites

Use a Debian 13 AMD64 machine with Git and network access to the configured Debian mirrors. The Builder used to validate this configuration runs `live-build` version `20250505+deb13u1`. Install build dependencies with `sudo ./scripts/install-dependencies.sh`.

## Build an ISO

From the repository root, run `sudo ./scripts/build-iso.sh`. The script cleans generated build stages while preserving live-build caches, regenerates configuration, invokes Debian Live Build, and places the result at `build/devos-amd64.iso`. Generated working files and images are ignored by Git.

`auto/config` and the package lists are the version-controlled sources of build settings. The build script regenerates live-build's derived `config/binary`, `config/bootstrap`, `config/chroot`, `config/common`, `config/source`, default package list, and system hook symlinks on each run so stale generated values cannot override the source configuration. The project pins bootstrap, chroot, and binary stages to Trixie, uses the IranServer Debian and security mirrors first, and retries with the official Debian mirrors if a build fails. Mirror URLs can be overridden with `DEVOS_DEBIAN_MIRROR` and `DEVOS_SECURITY_MIRROR`. Automatic installation of every firmware package is disabled; add required firmware packages explicitly after testing them. Check mirror reachability and `lb config --help` on the Builder before changing these settings. `config/hooks/` contains package-provided symlinks and is ignored; force-add project-owned hooks if needed.

Because APT recommends are disabled to keep the image small, packages required for Live boot, automatic console login, and Xorg input must be listed explicitly (including `user-setup` and `xserver-xorg-input-libinput`).

The live user is created with Zsh as its login shell. The user skeleton starts Xorg only for the automatic login on `tty2`; `startx` runs Openbox, whose autostart opens Kitty fullscreen. SSH sessions and other virtual consoles remain text-only.

The live image includes and starts `openssh-server` by default. It embeds the project's dedicated public key for the `user` account; the matching private key stays outside Git and the ISO. Connect with `ssh -i <private-key> user@<live-system-ip>`. The key is intended for this isolated Live test image; remove it before distributing an ISO publicly.

The initramfs explicitly loads the Hyper-V storage bus, virtual storage, optical-drive, ISO9660, and SquashFS modules before `live-boot` scans for the Live medium. This targets the Generation 2 failure seen in Hyper-V; verify both Generation 1 and Generation 2 boot from the resulting ISO before treating the fix as confirmed. The `findiso=${iso_path}` argument in generated GRUB configuration is emitted by Debian `live-build` for loopback boot support and is left unchanged.

## Git workflow

Keep `main` synchronized with `origin/main` before starting work. Make changes in a focused commit, review `git diff --check` and `git status`, then push the commit to GitHub. Treat generated build output as disposable and never commit ISO images, credentials, private keys, or machine-specific state.
