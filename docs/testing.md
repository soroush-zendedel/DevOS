# Testing

1. From a clean checkout, create and activate a Python virtual environment, run `python install.py iran` to install the local CLI, then build with `devos build` (or `devos build --up` to refresh the builder image first).
2. Run `devos verify` and retain the SHA-256 digest with test notes.
3. Boot the ISO in disposable Hyper-V Generation 1 and Generation 2 VMs without virtual disks.
4. Confirm the booted image contains the tty2 getty drop-in with `systemctl cat getty@tty2.service`; it should show `--autologin user`. Confirm `getty@tty2.service` is enabled and active with `systemctl is-enabled getty@tty2.service` and `systemctl is-active getty@tty2.service`.
5. Confirm Live boot reaches the `user` account on `tty2` without a password prompt. From the graphical Kitty terminal, confirm the shell is Zsh and the terminal-first Xorg/Openbox session opens Kitty fullscreen. Use `devos ssh` from the project host; confirm key-based access works without setting or requesting a password and without launching X on the SSH session.
6. Confirm the text consoles remain available with `Ctrl`+`Alt`+`F3` and that returning to `tty2` restores the graphical session.
7. Confirm booting and using Live mode does not alter any attached disk.
8. Record failures and the builder/live-build versions before adding features.

Physical USB and permanent installation testing are later milestones.
