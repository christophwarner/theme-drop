from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tmp_icons(tmp_path: Path) -> Path:
    d = tmp_path / "icons"
    d.mkdir()
    return d
