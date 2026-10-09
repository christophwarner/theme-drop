from pathlib import Path

import pytest

from theme_drop.cli import main
from theme_drop.install import (
    ThemeDropError,
    install_themes_from_archive,
    list_installed,
    uninstall_theme,
)

from helpers import write_cursor_theme, write_icon_theme, zip_tree


def test_install_cursor_zip(tmp_path: Path, tmp_icons: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    write_cursor_theme(src)
    archive = tmp_path / "cursors.zip"
    zip_tree(src, archive)

    result = install_themes_from_archive(archive, icons_dir=tmp_icons, force=False)
    assert len(result.installed) == 1
    dest = tmp_icons / "Demo-Cursors"
    assert (dest / "cursors" / "left_ptr").is_file()
    assert (dest / "index.theme").is_file()


def test_install_icon_zip(tmp_path: Path, tmp_icons: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    write_icon_theme(src)
    archive = tmp_path / "icons.zip"
    zip_tree(src, archive)

    result = install_themes_from_archive(archive, icons_dir=tmp_icons, force=True)
    assert result.installed[0].kind_label == "icon"
    assert (tmp_icons / "Demo-Icons" / "48x48" / "apps" / "demo.png").is_file()


def test_refuse_overwrite_without_force(tmp_path: Path, tmp_icons: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    write_cursor_theme(src)
    archive = tmp_path / "c.zip"
    zip_tree(src, archive)
    install_themes_from_archive(archive, icons_dir=tmp_icons, force=False)
    with pytest.raises(ThemeDropError, match="already exists"):
        install_themes_from_archive(archive, icons_dir=tmp_icons, force=False)


def test_force_replaces(tmp_path: Path, tmp_icons: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    write_cursor_theme(src)
    archive = tmp_path / "c.zip"
    zip_tree(src, archive)
    install_themes_from_archive(archive, icons_dir=tmp_icons, force=False)
    result = install_themes_from_archive(archive, icons_dir=tmp_icons, force=True)
    assert "Demo-Cursors" in result.replaced


def test_list_and_uninstall(tmp_path: Path, tmp_icons: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    write_icon_theme(src)
    archive = tmp_path / "i.zip"
    zip_tree(src, archive)
    install_themes_from_archive(archive, icons_dir=tmp_icons, force=True)

    themes = list_installed(tmp_icons)
    assert any(t.path.name == "Demo-Icons" for t in themes)

    removed = uninstall_theme("Demo-Icons", icons_dir=tmp_icons)
    assert not removed.exists()


def test_empty_archive_errors(tmp_path: Path, tmp_icons: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "readme.txt").write_text("no theme", encoding="utf-8")
    archive = tmp_path / "empty.zip"
    zip_tree(src, archive)
    with pytest.raises(ThemeDropError, match="No icon or cursor"):
        install_themes_from_archive(archive, icons_dir=tmp_icons, force=True)


def test_cli_open_with_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    icons = tmp_path / "icons"
    icons.mkdir()
    src = tmp_path / "src"
    src.mkdir()
    write_cursor_theme(src)
    archive = tmp_path / "c.zip"
    zip_tree(src, archive)

    monkeypatch.setattr(
        "theme_drop.install.default_icons_dir", lambda: icons
    )
    # Open With style: theme-drop /path/to.zip
    assert main([str(archive)]) == 0
    assert (icons / "Demo-Cursors" / "index.theme").is_file()
