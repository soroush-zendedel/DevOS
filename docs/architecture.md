# Architecture

DevOS targets Debian 13 Trixie on AMD64 and uses Debian Live Build to produce a hybrid ISO. Package lists and files installed into the image live under `config/`; `auto/config` records the reproducible build settings.

The initial image is a minimal Xorg/Openbox environment with Kitty and Zsh. A graphical login policy, terminal-first session, branding, third-party applications, and optional services remain future work and must be validated in a VM before being treated as supported.
