#!/bin/sh
set -eu

ISO=${1:-build/devos-amd64.iso}
if [ ! -f "$ISO" ]; then
    echo "ISO not found: $ISO" >&2
    exit 1
fi

if command -v sha256sum >/dev/null 2>&1; then
    digest=$(sha256sum "$ISO" | cut -d ' ' -f1)
elif command -v sha256 >/dev/null 2>&1; then
    digest=$(sha256 -q "$ISO")
else
    echo "Install coreutils or use a system with sha256sum." >&2
    exit 1
fi
echo "PASS: SHA-256 $digest ($ISO)"

if command -v xorriso >/dev/null 2>&1; then
    report=$(xorriso -indev "$ISO" -report_el_torito plain 2>&1) || {
        printf '%s\n' "$report" >&2
        echo "FAIL: xorriso could not read the ISO boot catalog." >&2
        exit 1
    }
    printf '%s\n' "$report"
    if ! printf '%s\n' "$report" | grep -Eq 'El Torito boot img[[:space:]]*:[[:space:]]*[0-9]+[[:space:]]+BIOS'; then
        echo "FAIL: the ISO has no BIOS El Torito boot image." >&2
        exit 1
    fi
    if ! printf '%s\n' "$report" | grep -Eq 'El Torito boot img[[:space:]]*:[[:space:]]*[0-9]+[[:space:]]+UEFI'; then
        echo "FAIL: the ISO has no UEFI El Torito boot image." >&2
        exit 1
    fi
    echo "PASS: BIOS and UEFI boot images are present."
else
    echo "FAIL: xorriso is unavailable; boot catalog was not verified." >&2
    exit 1
fi
