"""Extract archives and install theme roots into ~/.local/share/icons."""

from __future__ import annotations

import os
import shutil
import tarfile
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from theme_drop.detect import ThemeKind, ThemeRoot, find_theme_roots

ICONS_DIR = Path.home() / ".local" / "share" / "icons"

ARCHIVE_SUFFIXES = (
    ".zip",
    ".tar",
    ".tar.gz",
    ".tgz",
    ".tar.xz",
    ".txz",
    ".tar.bz2",
    ".tbz2",
    ".tar.zst",
    ".tzst",
)


@dataclass
class InstallResult:
    installed: list[ThemeRoot]
    replaced: list[str]
    target_dir: Path


class ThemeDropError(Exception):
    """User-facing install/detect error."""


def default_icons_dir() -> Path:
    return ICONS_DIR


def is_archive(path: Path) -> bool:
    name = path.name.lower()
    return any(name.endswith(suffix) for suffix in ARCHIVE_SUFFIXES)


def _safe_extract_zip(zf: zipfile.ZipFile, dest: Path) -> None:
    dest = dest.resolve()
    for info in zf.infolist():
        # Zip slip protection
        target = (dest / info.filename).resolve()
        if not str(target).startswith(str(dest) + os.sep) and target != dest:
            raise ThemeDropError(f"Refusing unsafe zip path: {info.filename}")
    zf.extractall(dest)


def _safe_extract_tar(tf: tarfile.TarFile, dest: Path) -> None:
    dest = dest.resolve()
    for member in tf.getmembers():
        target = (dest / member.name).resolve()
        if not str(target).startswith(str(dest) + os.sep) and target != dest:
            raise ThemeDropError(f"Refusing unsafe tar path: {member.name}")
        if member.issym() or member.islnk():
            # Skip links that could escape; extract regular files/dirs only
            continue
    # filter='data' is preferred on 3.12+; fall back for older
    try:
        tf.extractall(dest, filter="data")
    except TypeError:
        for member in tf.getmembers():
            if member.issym() or member.islnk():
                continue
            tf.extract(member, dest)


def extract_archive(archive: Path, dest: Path) -> None:
    archive = archive.resolve()
    if not archive.is_file():
        raise ThemeDropError(f"Not a file: {archive}")

    name = archive.name.lower()
    if name.endswith(".zip"):
        with zipfile.ZipFile(archive, "r") as zf:
            _safe_extract_zip(zf, dest)
        return

    if any(
        name.endswith(s)
        for s in (
            ".tar",
            ".tar.gz",
            ".tgz",
            ".tar.xz",
            ".txz",
            ".tar.bz2",
            ".tbz2",
            ".tar.zst",
            ".tzst",
        )
    ):
        try:
            with tarfile.open(archive, "r:*") as tf:
                _safe_extract_tar(tf, dest)
        except tarfile.TarError as exc:
            raise ThemeDropError(f"Could not read archive: {exc}") from exc
        return

    raise ThemeDropError(
        f"Unsupported archive type: {archive.name} "
        f"(need zip/tar/tar.gz/tar.xz/tar.bz2/tar.zst)"
    )


def install_dir_name(root: ThemeRoot) -> str:
    """Prefer folder name for filesystem; keep spaces for GNOME compatibility."""
    # Use the directory basename so multi-variant packs don't collide on Name=
    return root.path.name


def install_themes_from_archive(
    archive: Path,
    *,
    icons_dir: Path | None = None,
    force: bool = False,
) -> InstallResult:
    icons_dir = icons_dir or default_icons_dir()
    icons_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="theme-drop-") as tmp:
        extract_root = Path(tmp)
        extract_archive(archive, extract_root)
        roots = find_theme_roots(extract_root)
        if not roots:
            raise ThemeDropError("No icon or cursor theme found in this archive.")

        installed: list[ThemeRoot] = []
        replaced: list[str] = []

        for root in roots:
            dest_name = install_dir_name(root)
            dest = icons_dir / dest_name
            if dest.exists():
                if not force:
                    raise ThemeDropError(
                        f"Theme already exists: {dest_name}\n"
                        f"Re-run with --force to replace it."
                    )
                shutil.rmtree(dest)
                replaced.append(dest_name)
            shutil.copytree(root.path, dest)
            installed.append(
                ThemeRoot(path=dest, name=root.name, kind=root.kind)
            )

        return InstallResult(
            installed=installed, replaced=replaced, target_dir=icons_dir
        )


def list_installed(icons_dir: Path | None = None) -> list[ThemeRoot]:
    icons_dir = icons_dir or default_icons_dir()
    if not icons_dir.is_dir():
        return []
    results: list[ThemeRoot] = []
    for child in sorted(icons_dir.iterdir()):
        if not child.is_dir():
            continue
        if not (child / "index.theme").is_file():
            continue
        from theme_drop.detect import classify_theme, _read_theme_name

        kind = classify_theme(child)
        if kind == ThemeKind.NONE:
            continue
        name = _read_theme_name(child / "index.theme", fallback=child.name)
        results.append(ThemeRoot(path=child, name=name, kind=kind))
    return results


def uninstall_theme(name: str, icons_dir: Path | None = None) -> Path:
    icons_dir = icons_dir or default_icons_dir()
    target = icons_dir / name
    if not target.is_dir():
        # Try match by index.theme Name=
        matches = [t for t in list_installed(icons_dir) if t.name == name]
        if len(matches) == 1:
            target = matches[0].path
        elif len(matches) > 1:
            raise ThemeDropError(
                f"Multiple themes named {name!r}; uninstall by folder name:\n"
                + "\n".join(f"  {m.path.name}" for m in matches)
            )
        else:
            raise ThemeDropError(f"Theme not found: {name}")
    shutil.rmtree(target)
    return target
