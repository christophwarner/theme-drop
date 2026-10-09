"""Command-line and Open With entry point for Theme Drop."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from theme_drop import __version__
from theme_drop.install import (
    ThemeDropError,
    install_themes_from_archive,
    list_installed,
    uninstall_theme,
)


def notify(title: str, body: str, *, urgency: str = "normal") -> None:
    if not shutil.which("notify-send"):
        return
    try:
        subprocess.run(
            [
                "notify-send",
                "--app-name=Theme Drop",
                f"--urgency={urgency}",
                title,
                body,
            ],
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        pass


def cmd_install(args: argparse.Namespace) -> int:
    archive = Path(args.archive).expanduser()
    force = bool(args.force)
    # Open With / kids path: always replace existing themes
    if args.open_with:
        force = True

    try:
        result = install_themes_from_archive(archive, force=force)
    except ThemeDropError as exc:
        print(f"theme-drop: {exc}", file=sys.stderr)
        if args.open_with:
            notify("Theme Drop", str(exc), urgency="critical")
        return 1

    lines = []
    for theme in result.installed:
        lines.append(f"  • {theme.name} ({theme.kind_label}) → {theme.path}")
    summary = "\n".join(lines)
    print(f"Installed {len(result.installed)} theme(s) into {result.target_dir}:")
    print(summary)
    if result.replaced:
        print("Replaced:", ", ".join(result.replaced))

    names = ", ".join(t.name for t in result.installed)
    notify(
        "Theme installed",
        f"{names}\nOpen GNOME Tweaks → Appearance to select it.",
    )
    return 0


def cmd_list(_args: argparse.Namespace) -> int:
    themes = list_installed()
    if not themes:
        print("No icon/cursor themes in ~/.local/share/icons/")
        return 0
    for theme in themes:
        print(f"{theme.path.name}\t{theme.kind_label}\t{theme.name}")
    return 0


def cmd_uninstall(args: argparse.Namespace) -> int:
    try:
        path = uninstall_theme(args.name)
    except ThemeDropError as exc:
        print(f"theme-drop: {exc}", file=sys.stderr)
        return 1
    print(f"Removed {path}")
    notify("Theme removed", path.name)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="theme-drop",
        description="Install GNOME icon and cursor themes from zip/tar archives.",
    )
    parser.add_argument(
        "--version", action="version", version=f"theme-drop {__version__}"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_install = sub.add_parser("install", help="Install themes from an archive")
    p_install.add_argument("archive", help="Path to zip/tar theme archive")
    p_install.add_argument(
        "--force",
        action="store_true",
        help="Replace themes that already exist",
    )
    p_install.add_argument(
        "--open-with",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    p_install.set_defaults(func=cmd_install)

    p_list = sub.add_parser("list", help="List installed icon/cursor themes")
    p_list.set_defaults(func=cmd_list)

    p_uninstall = sub.add_parser("uninstall", help="Remove an installed theme")
    p_uninstall.add_argument("name", help="Folder name or theme Name=")
    p_uninstall.set_defaults(func=cmd_uninstall)

    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    # Desktop Open With: theme-drop /path/to/archive.zip
    if argv and not argv[0].startswith("-") and argv[0] not in {
        "install",
        "list",
        "uninstall",
    }:
        path = Path(argv[0])
        if path.exists() and path.is_file():
            argv = ["install", "--open-with", str(path), *argv[1:]]

    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
