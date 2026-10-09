from pathlib import Path

from theme_drop.detect import ThemeKind, find_theme_roots

from helpers import write_cursor_theme, write_icon_theme


def test_detect_cursor_theme(tmp_path: Path) -> None:
    write_cursor_theme(tmp_path)
    roots = find_theme_roots(tmp_path)
    assert len(roots) == 1
    assert roots[0].kind == ThemeKind.CURSOR
    assert roots[0].name == "Demo Cursors"


def test_detect_icon_theme(tmp_path: Path) -> None:
    write_icon_theme(tmp_path)
    roots = find_theme_roots(tmp_path)
    assert len(roots) == 1
    assert roots[0].kind == ThemeKind.ICON
    assert roots[0].name == "Demo Icons"


def test_detect_mixed_pack(tmp_path: Path) -> None:
    write_cursor_theme(tmp_path / "pack")
    write_icon_theme(tmp_path / "pack")
    roots = find_theme_roots(tmp_path)
    kinds = {r.kind for r in roots}
    assert ThemeKind.CURSOR in kinds
    assert ThemeKind.ICON in kinds
    assert len(roots) == 2


def test_skips_macosx(tmp_path: Path) -> None:
    junk = tmp_path / "__MACOSX" / "Demo"
    junk.mkdir(parents=True)
    (junk / "cursors").mkdir()
    (junk / "cursors" / "left_ptr").write_bytes(b"x")
    (junk / "index.theme").write_text(
        "[Icon Theme]\nName=Junk\n", encoding="utf-8"
    )
    write_cursor_theme(tmp_path)
    roots = find_theme_roots(tmp_path)
    assert len(roots) == 1
    assert roots[0].name == "Demo Cursors"


def test_ignores_index_without_theme_payload(tmp_path: Path) -> None:
    empty = tmp_path / "Empty"
    empty.mkdir()
    (empty / "index.theme").write_text(
        "[Icon Theme]\nName=Empty\n", encoding="utf-8"
    )
    assert find_theme_roots(tmp_path) == []
