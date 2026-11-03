# Development

## Builder prerequisites

Use a host with Python 3.10 or newer and Docker Desktop or Docker Engine with the Compose v2 plugin. Create and activate a virtual environment, then run `python install.py iran` to install this checkout in editable mode. The installer tries the configured Iranian PyPI mirrors in order and then official PyPI. In the built Docker builder and Live image, `/etc/pip.conf` configures the Iranian indexes and official PyPI. `devos build` builds the builder image when needed; use `devos build --up` to force-refresh that image before building the ISO. The Docker builder tries the ordered Iranian mirrors in `config/mirrors/iran/debian.txt`, then official Debian.

## Build an ISO

From the repository root or any directory, run `devos build`. On the first build, the CLI creates `.devos-ssh` and `.devos-ssh.pub` in the project root. Docker Compose mounts only the public key read-only, installs it for the Live `user`, disables SSH password authentication, and enables SSH. The private key stays on the host and is ignored by Git. Docker Compose runs the Debian Trixie builder as a Linux AMD64 container, cleans generated build stages while preserving caches, regenerates configuration, invokes Debian Live Build, and writes the result directly to the host-mounted `build/devos-amd64.iso`. The ISO SHA-256 is recorded next to the image. Generated working files and images are ignored by Git.

Live Build caches APT package indices along with downloaded packages, so repeated builds reuse repository lists instead of downloading them repeatedly. This also means the cached package metadata is not refreshed automatically. Run `devos clean --purge` when you want the next build to download fresh APT lists and packages.

The builder image provides a Debian userland and build tools; like other Linux containers, it uses the Linux kernel provided by Docker Engine rather than carrying a separate running kernel. Docker Desktop runs Linux containers inside its Linux VM, including on Windows and macOS. The builder service is privileged so live-build can mount and prepare chroots. Docker Compose describes this as elevated container privilege with platform-specific effects. Keep Docker Desktop's disk image or Docker Engine storage on a drive with enough free space.

`auto/config` and the package lists are the version-controlled sources of build settings. The build script regenerates live-build's derived configuration, default package list, and system hook symlinks on each run so stale generated values cannot override the source configuration. The project pins bootstrap, chroot, and binary stages to Trixie, uses the IranServer Debian and security mirrors first, and retries with the official Debian mirrors if a build fails. Mirror URLs can be overridden with `DEVOS_DEBIAN_MIRROR` and `DEVOS_SECURITY_MIRROR`; Compose passes these through to the container. Automatic installation of every firmware package is disabled; add required firmware packages explicitly after testing them. Check mirror reachability and `lb config --help` in the builder container before changing these settings. Git ignores generated hook files under `config/hooks/` while allowing the named project-owned hooks; add a narrow `.gitignore` exception when introducing another project hook.

Because APT recommends are disabled to keep the image small, packages required for Live boot, automatic console login, and Xorg input must be listed explicitly (including `user-setup` and `xserver-xorg-input-libinput`).

The live user is created with Zsh as its login shell. A tracked systemd drop-in configures `getty@tty2.service` to automatically log in as `user`, and a chroot hook enables that service in the image. The user skeleton starts Xorg only on `tty2`; `startx` runs Openbox, whose autostart opens Kitty fullscreen. SSH sessions and other virtual consoles remain text-only. Verify the path in a disposable VM with the manual checklist in `docs/testing.md`.

The Live image accepts SSH only with the project's private key. On a Windows host with Hyper-V, run `devos ssh` to discover a running VM, find its address, verify SSH availability, and connect as `user`. Use `devos ssh --vm-name NAME` when multiple VMs are running. The CLI maintains `.devos-known-hosts` in the project directory for the VM host key. No password is set or requested. For detailed builder output, run `devos logs`; use `devos logs --lines 500` to show more lines. The `devos copy-iso` command remains available for copying images from a remote builder.

The initramfs explicitly loads the Hyper-V storage bus, virtual storage, optical-drive, ISO9660, and SquashFS modules before `live-boot` scans for the Live medium. This targets the Generation 2 failure seen in Hyper-V; verify both Generation 1 and Generation 2 boot from the resulting ISO before treating the fix as confirmed. The `findiso=${iso_path}` argument in generated GRUB configuration is emitted by Debian `live-build` for loopback boot support and is left unchanged.

## Git workflow

Keep `main` synchronized with `origin/main` before starting work. Make changes in a focused commit, review `git diff --check` and `git status`, then push the commit to GitHub. Treat generated build output as disposable and never commit ISO images, credentials, private keys, or machine-specific state.
