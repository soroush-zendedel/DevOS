#!/bin/sh
set -eu

mkdir -p /workspace /host-output

# Copy only build inputs into Docker's Linux filesystem. The host .git folder,
# virtual environment, and ignored private keys are never mounted in the container.
for item in assets auto config scripts; do
    rm -rf "/workspace/$item"
    cp -a "/source/$item" "/workspace/$item"
done
chmod 0755 \
    /workspace/auto/config \
    /workspace/scripts/build-iso.sh \
    /workspace/scripts/install-dependencies.sh \
    /workspace/scripts/verify-iso.sh

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
if [ -f /host-output/devos-amd64.iso ]; then
    cp /host-output/devos-amd64.iso /workspace/build/devos-amd64.iso
fi

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
        cp "$iso" /host-output/devos-amd64.iso.partial
        source_hash=$(sha256sum "$iso" | cut -d ' ' -f1)
        copied_hash=$(sha256sum /host-output/devos-amd64.iso.partial | cut -d ' ' -f1)
        if [ "$source_hash" != "$copied_hash" ]; then
            echo "ISO hash mismatch while copying it to the host output directory." >&2
            exit 1
        fi
        mv -f /host-output/devos-amd64.iso.partial /host-output/devos-amd64.iso
        printf '%s  %s\n' "$source_hash" devos-amd64.iso > /host-output/devos-amd64.iso.sha256
        echo "Copied ISO to host and verified SHA-256: $source_hash"
        ;;
    *)
        exec "$@"
        ;;
esac
