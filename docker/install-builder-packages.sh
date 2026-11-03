#!/bin/sh
set -eu

mirror_pairs=${1:?Pass comma-separated archive|security mirror pairs}
source_file=/etc/apt/sources.list.d/debian.sources
original_file=/tmp/debian.sources.original
cp "$source_file" "$original_file"

old_archive=http://deb.debian.org/debian
old_security=http://deb.debian.org/debian-security
old_security_alt=http://security.debian.org/debian-security

old_ifs=$IFS
IFS=,
for pair in $mirror_pairs; do
    IFS=$old_ifs
    archive=${pair%%|*}
    security=${pair#*|}
    cp "$original_file" "$source_file"
    sed -i \
        -e "s|$old_archive|${archive%/}|g" \
        -e "s|$old_security|${security%/}|g" \
        -e "s|$old_security_alt|${security%/}|g" \
        "$source_file"
    if apt-get -o APT::Update::Error-Mode=any update \
        && apt-get install --yes --no-install-recommends \
            ca-certificates debootstrap findutils live-build squashfs-tools xorriso; then
        rm -rf /var/lib/apt/lists/* "$original_file"
        exit 0
    fi
    echo "Debian mirror pair failed: $archive; trying the next configured mirror." >&2
    IFS=,
done
IFS=$old_ifs
echo 'All configured Debian mirror pairs failed.' >&2
exit 1
