# Architecture

DevOS targets Debian 13 Trixie on AMD64 and uses Debian Live Build to produce a hybrid ISO. Package lists and files installed into the image live under `config/`; `auto/config` records the reproducible build settings.

The initial image is a minimal Xorg/Openbox environment with Kitty and Zsh. The live user gets Zsh as the default shell. On the automatic login on `tty2`, Zsh starts Xorg with Openbox and Openbox opens Kitty fullscreen. SSH and other text consoles do not start X automatically. This terminal-first startup must be validated in both Hyper-V generations before being treated as supported.
