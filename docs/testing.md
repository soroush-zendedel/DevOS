# Testing

1. Build from a clean checkout on the Debian 13 AMD64 builder.
2. Run `./scripts/verify-iso.sh` and retain the SHA-256 digest with test notes.
3. Boot the ISO in disposable Hyper-V Generation 1 and Generation 2 VMs without virtual disks.
4. Confirm Live boot, automatic login to the `user` account on `tty2`, and that the terminal-first Xorg/Openbox session opens Kitty fullscreen. Confirm the shell is Zsh. On each fresh session, set a temporary password and confirm SSH access; also confirm SSH works without launching X on the SSH session.
5. Confirm the text consoles remain available with `Ctrl`+`Alt`+`F3` and that returning to `tty2` restores the graphical session.
6. Confirm booting and using Live mode does not alter any attached disk.
7. Record failures and the builder/live-build versions before adding features.

Physical USB and permanent installation testing are later milestones.
