#!/bin/sh
set -eu

ISO=${1:-build/devos-amd64.iso}
if [ ! -f "$ISO" ]; then
    echo "ISO not found: $ISO" >&2
    exit 1
fi

if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$ISO"
elif command -v sha256 >/dev/null 2>&1; then
    sha256 "$ISO"
else
    echo "Install coreutils or use a system with sha256sum." >&2
    exit 1
fi

if command -v xorriso >/dev/null 2>&1; then
    xorriso -indev "$ISO" -report_el_torito plain
else
    echo "xorriso is unavailable; skipped boot catalog inspection." >&2
fi
