#!/usr/bin/env bash
# Remove Theme Drop (does not remove installed icon/cursor themes).
set -euo pipefail

PREFIX="${THEME_DROP_PREFIX:-$HOME/.local}"
BIN="$PREFIX/bin/theme-drop"
DESKTOP="$PREFIX/share/applications/theme-drop.desktop"
SRC="$PREFIX/share/theme-drop"

echo "Uninstalling Theme Drop from $PREFIX"
rm -f "$BIN" "$DESKTOP"
rm -rf "$SRC"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$PREFIX/share/applications" >/dev/null 2>&1 || true
fi

echo "Theme Drop removed."
echo "Your icon/cursor themes in ~/.local/share/icons/ were left alone."
echo "Delete a theme folder there, or reinstall Theme Drop and run: theme-drop uninstall NAME"
