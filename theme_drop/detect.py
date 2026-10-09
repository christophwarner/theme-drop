"""Detect icon and cursor theme roots inside extracted archives."""

from __future__ import annotations

import configparser
import re
from dataclasses import dataclass
from enum import Flag, auto
from pathlib import Path

SKIP_DIR_NAMES = {"__MACOSX", ".DS_Store", "Thumbs.db"}
SIZE_DIR_RE = re.compile(r"^(\d+x\d+|scalable|symbolic|cursors)$", re.IGNORECASE)


class ThemeKind(Flag):
    NONE = 0
    CURSOR = auto()
    ICON = auto()
    BOTH = CURSOR | ICON


@dataclass(frozen=True)
class ThemeRoot:
    path: Path
    name: str
    kind: ThemeKind

    @property
    def kind_label(self) -> str:
        if self.kind == ThemeKind.BOTH:
            return "icon+cursor"
        if self.kind == ThemeKind.CURSOR:
            return "cursor"
        if self.kind == ThemeKind.ICON:
            return "icon"
        return "unknown"


def _read_theme_name(index_theme: Path, fallback: str) -> str:
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        text = index_theme.read_text(encoding="utf-8", errors="replace")
        parser.read_string(text)
    except (OSError, configparser.Error):
        return fallback

    for section in ("Icon Theme", "Icon theme"):
        if parser.has_section(section) and parser.has_option(section, "Name"):
            name = parser.get(section, "Name").strip()
            if name:
                return name
    return fallback


def _has_directories_key(index_theme: Path) -> bool:
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        text = index_theme.read_text(encoding="utf-8", errors="replace")
        parser.read_string(text)
    except (OSError, configparser.Error):
        return False
    for section in ("Icon Theme", "Icon theme"):
        if parser.has_section(section) and parser.has_option(section, "Directories"):
            value = parser.get(section, "Directories").strip()
            if value:
                return True
    return False


def _has_size_dirs(theme_dir: Path) -> bool:
    for child in theme_dir.iterdir():
        if not child.is_dir():
            continue
        if SIZE_DIR_RE.match(child.name) and child.name.lower() != "cursors":
            return True
    return False


def classify_theme(theme_dir: Path) -> ThemeKind:
    """Classify a directory that contains index.theme."""
    kind = ThemeKind.NONE
    cursors = theme_dir / "cursors"
    if cursors.is_dir() and any(cursors.iterdir()):
        kind |= ThemeKind.CURSOR

    index = theme_dir / "index.theme"
    if _has_directories_key(index) or _has_size_dirs(theme_dir):
        kind |= ThemeKind.ICON

    # Cursor-only packs often ship a minimal index.theme without Directories=
    # and without size folders — already covered by CURSOR above.
    # Icon packs without Directories= but with size dirs are covered.
    # If we only have index.theme and no cursors/size dirs, treat as nothing.
    return kind


def find_theme_roots(extract_root: Path) -> list[ThemeRoot]:
    """Walk extract_root and return every valid icon/cursor theme root."""
    roots: list[ThemeRoot] = []
    seen: set[Path] = set()

    for index in sorted(extract_root.rglob("index.theme")):
        if not index.is_file():
            continue
        theme_dir = index.parent
        # Skip junk paths
        if any(part in SKIP_DIR_NAMES for part in theme_dir.parts):
            continue
        try:
            resolved = theme_dir.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue

        kind = classify_theme(theme_dir)
        if kind == ThemeKind.NONE:
            continue

        seen.add(resolved)
        name = _read_theme_name(index, fallback=theme_dir.name)
        roots.append(ThemeRoot(path=theme_dir, name=name, kind=kind))

    return roots
