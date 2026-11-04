# Issue: Keyboard and Mouse Unresponsive / Blank Screen After Live Boot in VirtualBox/VMs

## Description

When booting the generated DevOS Live ISO in VirtualBox or other hypervisors, users experience an unresponsive graphical session or appear unable to type/interact after the system reaches the desktop environment.

## Root Cause Analysis

1. **Missing Openbox Autostart Entry (`kitty`)**: 
   The current session starts Xorg automatically on `tty2` via `.zprofile` executing `startx` (`openbox-session`), but there is no Openbox autostart configuration (`~/.config/openbox/autostart`) launching the default terminal emulator (`kitty`). This results in an empty Openbox root window (gray screen with an X cursor), making it appear as if the system is frozen or non-interactive.
2. **Input Driver Detection (`libinput`)**:
   VirtualBox and generic hypervisors require proper input driver handling. While `xserver-xorg-input-libinput` is tracked in package lists, missing guest integration or uninitialized input focus on virtual consoles can cause keyboard/mouse events to drop before reaching Xorg.
3. **Console Focus & TTY Switching**:
   Because auto-login lands directly on `tty2` and immediately triggers `startx`, any race condition between systemd getty initialization and X server startup can leave keyboard focus trapped in the Linux kernel console rather than the X server instance.

---

## Proposed Solutions

1. **Add Openbox Autostart Configuration**:
   Create [`config/includes.chroot/etc/skel/.config/openbox/autostart`](config/includes.chroot/etc/skel/.config/openbox/autostart) containing:
   ```sh
   # Launch default terminal fullscreen on session start
   kitty &
   ```
2. **Verify Input Drivers in Package Lists**:
   Ensure `xserver-xorg-input-all` and `xserver-xorg-input-libinput` are explicitly verified in the chroot package manifests.
3. **Add Fallback Keybindings / Terminal Launchers**:
   Configure Openbox rc.xml bindings to ensure `Super+T` or `Ctrl+Alt+T` spawns `kitty` if the initial autostart fails.
