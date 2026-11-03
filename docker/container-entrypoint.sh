#!/bin/sh
set -eu

mkdir -p /workspace

# Copy only build inputs into Docker's Linux filesystem. The host .git folder,
# virtual environment, and ignored private keys are never mounted in the container.
for item in assets auto config scripts; do
    rm -rf "/workspace/$item"
    cp -a "/source/$item" "/workspace/$item"
done
mirror_country=${DEVOS_MIRROR_COUNTRY:-iran}
install -D -m 0644 \
    "/workspace/config/mirrors/$mirror_country/pip.conf" \
    /workspace/config/includes.chroot/etc/pip.conf
install -D -m 0644 /source/ssh/devos-ssh.pub /workspace/config/includes.chroot/etc/ssh/devos-ssh.pub
chmod 0755 \
    /workspace/auto/config \
    /workspace/scripts/build-iso.sh \
    /workspace/scripts/install-dependencies.sh \
    /workspace/scripts/verify-iso.sh
if [ -f /workspace/config/hooks/normal/1300-devos-ssh-key.hook.chroot ]; then
    chmod 0755 /workspace/config/hooks/normal/1300-devos-ssh-key.hook.chroot
fi
if [ -f /workspace/config/hooks/normal/1400-devos-tty2-autologin.hook.chroot ]; then
    chmod 0755 /workspace/config/hooks/normal/1400-devos-tty2-autologin.hook.chroot
fi

# Never use generated host live-build state as configuration input.
rm -f \
    /workspace/config/binary \
    /workspace/config/bootstrap \
    /workspace/config/chroot \
    /workspace/config/common \
    /workspace/config/source \
    /workspace/config/package-lists/live.list.chroot
if [ -d /workspace/config/hooks ]; then
    find /workspace/config/hooks -type l -delete
fi

mkdir -p /workspace/build

cd /workspace
case "${1:-}" in
    ./scripts/build-iso.sh|scripts/build-iso.sh)
        "$@"
        if ! grep -qx 'xserver-xorg-input-libinput' /workspace/live-image-amd64.packages; then
            echo "Required package xserver-xorg-input-libinput is missing from the image." >&2
            exit 1
        fi
        iso=/workspace/build/devos-amd64.iso
        if [ ! -f "$iso" ]; then
            echo "Build completed but the expected ISO was not created: $iso" >&2
            exit 1
        fi
        source_hash=$(sha256sum "$iso" | cut -d ' ' -f1)
        printf '%s  %s\n' "$source_hash" devos-amd64.iso > /workspace/build/devos-amd64.iso.sha256
        echo "ISO is available in the host build folder; SHA-256: $source_hash"
        ;;
    *)
        exec "$@"
        ;;
esac
