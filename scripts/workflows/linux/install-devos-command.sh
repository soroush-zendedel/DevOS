#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
COMMAND="$SCRIPT_DIR/devos"
BIN_DIR="${HOME:?HOME is not set}/.local/bin"
LINK="$BIN_DIR/devos"

mkdir -p "$BIN_DIR"
if [ -e "$LINK" ] || [ -L "$LINK" ]; then
    if [ "$(readlink -f "$LINK" 2>/dev/null || true)" = "$COMMAND" ]; then
        echo "DevOS command already installed: $LINK"
        exit 0
    fi
    echo "$LINK already exists and does not point to this repository; refusing to replace it." >&2
    exit 1
fi

ln -s "$COMMAND" "$LINK"
echo "Installed: $LINK"
case ":${PATH}:" in
    *":$BIN_DIR:"*) ;;
    *) echo "Add this to your shell profile if needed: export PATH=\"\$HOME/.local/bin:\$PATH\"" ;;
esac
echo "Run: devos help"
