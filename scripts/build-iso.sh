#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

if [ "$(id -u)" -ne 0 ]; then
    echo "Run with sudo: sudo ./scripts/build-iso.sh" >&2
    exit 1
fi

command -v lb >/dev/null 2>&1 || {
    echo "live-build is missing. Run ./scripts/install-dependencies.sh first." >&2
    exit 1
}

mkdir -p build
lb config
lb build

set -- ./*.iso
if [ ! -f "$1" ]; then
    echo "Build completed but no ISO was found." >&2
    exit 1
fi
mv -- "$1" build/devos-amd64.iso
echo "Created: $ROOT/build/devos-amd64.iso"
