"""Helpers to build tiny synthetic icon/cursor theme archives."""

from __future__ import annotations

import zipfile
from pathlib import Path


def write_cursor_theme(root: Path, folder: str = "Demo-Cursors") -> Path:
    theme = root / folder
    cursors = theme / "cursors"
    cursors.mkdir(parents=True)
    (cursors / "left_ptr").write_bytes(b"fake-cursor")
    (theme / "index.theme").write_text(
        "[Icon Theme]\nName=Demo Cursors\nComment=test\n",
        encoding="utf-8",
    )
    return theme


def write_icon_theme(root: Path, folder: str = "Demo-Icons") -> Path:
    theme = root / folder
    (theme / "48x48" / "apps").mkdir(parents=True)
    (theme / "48x48" / "apps" / "demo.png").write_bytes(b"\x89PNG\r\n")
    (theme / "index.theme").write_text(
        "[Icon Theme]\n"
        "Name=Demo Icons\n"
        "Comment=test\n"
        "Directories=48x48/apps\n"
        "\n"
        "[48x48/apps]\n"
        "Size=48\n"
        "Context=Applications\n"
        "Type=Fixed\n",
        encoding="utf-8",
    )
    return theme


def zip_tree(src_root: Path, zip_path: Path) -> Path:
    with zipfile.ZipFile(zip_path, "w") as zf:
        for path in src_root.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(src_root).as_posix())
    return zip_path
