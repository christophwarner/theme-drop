#!/usr/bin/env bash
# Theme Drop — one-line install:
#   curl -fsSL https://raw.githubusercontent.com/<you>/theme-drop/main/install.sh | bash
set -euo pipefail

REPO="${THEME_DROP_REPO:-christophwarner/theme-drop}"
BRANCH="${THEME_DROP_BRANCH:-main}"
PREFIX="${THEME_DROP_PREFIX:-$HOME/.local}"
BIN_DIR="$PREFIX/bin"
APP_DIR="$PREFIX/share/applications"
SRC_DIR="$PREFIX/share/theme-drop/src"

echo "Theme Drop installer"
echo "  prefix: $PREFIX"

SCRIPT_DIR=""
if [[ -n "${BASH_SOURCE[0]:-}" && -f "${BASH_SOURCE[0]}" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

cleanup() {
  if [[ -n "${TMP_DIR:-}" && -d "${TMP_DIR:-}" ]]; then
    rm -rf "$TMP_DIR"
  fi
}
trap cleanup EXIT

resolve_source() {
  # Local checkout (bash install.sh)
  if [[ -n "$SCRIPT_DIR" && -d "$SCRIPT_DIR/theme_drop" && -f "$SCRIPT_DIR/bin/theme-drop" ]]; then
    SOURCE_ROOT="$SCRIPT_DIR"
    echo "  source: local checkout ($SOURCE_ROOT)"
    return
  fi

  # Piped curl | bash — download tarball from GitHub
  TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/theme-drop-install.XXXXXX")"
  local url="https://github.com/${REPO}/archive/refs/heads/${BRANCH}.tar.gz"
  echo "  source: $url"
  if ! curl -fsSL "$url" | tar -xz -C "$TMP_DIR"; then
    echo "error: could not download theme-drop from GitHub ($REPO @ $BRANCH)" >&2
    echo "hint: set THEME_DROP_REPO=owner/repo if the repo name differs" >&2
    exit 1
  fi
  # github archive extracts to theme-drop-<branch>/
  SOURCE_ROOT="$(find "$TMP_DIR" -maxdepth 1 -type d -name 'theme-drop-*' | head -n1)"
  if [[ -z "$SOURCE_ROOT" || ! -d "$SOURCE_ROOT/theme_drop" ]]; then
    echo "error: unexpected archive layout" >&2
    exit 1
  fi
}

resolve_source

mkdir -p "$BIN_DIR" "$APP_DIR" "$SRC_DIR"
rm -rf "$SRC_DIR/theme_drop"
cp -a "$SOURCE_ROOT/theme_drop" "$SRC_DIR/"
install -m 755 "$SOURCE_ROOT/bin/theme-drop" "$BIN_DIR/theme-drop"

# Desktop file: Exec=theme-drop needs PATH; rewrite to absolute for reliability
DESKTOP_SRC="$SOURCE_ROOT/share/applications/theme-drop.desktop"
DESKTOP_DST="$APP_DIR/theme-drop.desktop"
sed "s|^Exec=theme-drop |Exec=$BIN_DIR/theme-drop |" "$DESKTOP_SRC" >"$DESKTOP_DST"
chmod 644 "$DESKTOP_DST"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APP_DIR" >/dev/null 2>&1 || true
fi

# Ensure ~/.local/bin is on PATH for this user
path_line='export PATH="$HOME/.local/bin:$PATH"'
shell_rc=""
case "${SHELL:-}" in
  */zsh) shell_rc="$HOME/.zshrc" ;;
  */bash) shell_rc="$HOME/.bashrc" ;;
  *) shell_rc="$HOME/.profile" ;;
esac
if [[ -n "$shell_rc" ]] && ! grep -qF '.local/bin' "$shell_rc" 2>/dev/null; then
  if [[ ! -f "$shell_rc" ]] || ! grep -q 'THEME_DROP_PATH' "$shell_rc" 2>/dev/null; then
    {
      echo ""
      echo "# THEME_DROP_PATH — Theme Drop CLI"
      echo "$path_line"
    } >>"$shell_rc"
    echo "  added ~/.local/bin to PATH in $shell_rc (open a new terminal)"
  fi
fi

echo
echo "Installed Theme Drop."
echo "  CLI:  $BIN_DIR/theme-drop"
echo
echo "How to use:"
echo "  1. Download an icon or cursor theme (zip/tar)."
echo "  2. Right-click the file → Open With → Theme Drop"
echo "     or run:  theme-drop install ~/Downloads/theme.zip --force"
echo "  3. Open GNOME Tweaks → Appearance → pick Icons or Cursor"
echo
echo "List installed themes:  theme-drop list"
echo "Uninstall Theme Drop:   curl -fsSL https://raw.githubusercontent.com/${REPO}/main/uninstall.sh | bash"
