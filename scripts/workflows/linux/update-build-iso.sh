#!/usr/bin/env bash
set -euo pipefail

# Resolve the repository from this script so callers can run it from anywhere.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
    echo "Tracked local changes exist. Commit or stash them before updating." >&2
    git status --short
    exit 1
fi

if ! git rev-parse --abbrev-ref '@{upstream}' >/dev/null 2>&1; then
    echo "Current branch has no upstream configured." >&2
    exit 1
fi

git pull --ff-only
printf 'Building repository revision: '
git log -1 --format='%h %s'

sudo ./scripts/build-iso.sh

if ! grep -qx 'xserver-xorg-input-libinput' live-image-amd64.packages; then
    echo "Expected Xorg input driver is absent from the built package manifest." >&2
    exit 1
fi

./scripts/verify-iso.sh
printf '\nBuilder addresses: '
hostname -I
