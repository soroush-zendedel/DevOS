# Testing

1. Build from a clean checkout on the Debian 13 AMD64 builder.
2. Run `./scripts/verify-iso.sh` and retain the SHA-256 digest with test notes.
3. Boot the ISO in a disposable Hyper-V VM without a virtual disk.
4. Confirm Live boot, automatic console login to the `user` account, network access, and shell. Test Xorg/Openbox and Kitty separately once the session startup configuration is in place.
5. Confirm booting and using Live mode does not alter any attached disk.
6. Record failures and the builder/live-build versions before adding features.

Physical USB and permanent installation testing are later milestones.
