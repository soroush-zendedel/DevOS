# Testing

1. From a clean checkout, create and activate a Python virtual environment, install the CLI with `python -m pip install --editable .`, run `devos deps`, then build with `devos build`.
2. Run `devos verify` and retain the SHA-256 digest with test notes.
3. Boot the ISO in disposable Hyper-V Generation 1 and Generation 2 VMs without virtual disks.
4. Confirm Live boot, automatic login to the `user` account on `tty2`, and that the terminal-first Xorg/Openbox session opens Kitty fullscreen. Confirm the shell is Zsh. From the Live console run `sudo passwd user` to set a temporary password, then confirm SSH access with `ssh user@<guest-ip>`; also confirm SSH works without launching X on the SSH session. Repeat after reboot and verify the old password no longer works.
5. Confirm the text consoles remain available with `Ctrl`+`Alt`+`F3` and that returning to `tty2` restores the graphical session.
6. Confirm booting and using Live mode does not alter any attached disk.
7. Record failures and the builder/live-build versions before adding features.

Physical USB and permanent installation testing are later milestones.
