# Theme Drop

Install **GNOME icon** and **cursor** themes from a downloaded zip/tar — then pick them in **GNOME Tweaks → Appearance**.

Built for parents and kids: one-line install, then right-click → **Open With → Theme Drop**.

## Install (one line)

```bash
curl -fsSL https://cdn.jsdelivr.net/gh/christophwarner/theme-drop@main/install.sh | bash
```

If the GitHub username/repo differs:

```bash
THEME_DROP_REPO=yourname/theme-drop curl -fsSL https://cdn.jsdelivr.net/gh/yourname/theme-drop@main/install.sh | bash
```

Needs: Python 3, `curl`, GNOME (or any desktop that reads `~/.local/share/icons/` + Tweaks).

## Use it

1. Download an icon or cursor theme archive (`.zip`, `.tar.gz`, `.tar.xz`, …).
2. Right-click the file → **Open With** → **Theme Drop**  
   — or in a terminal:
   ```bash
   theme-drop install ~/Downloads/SomeTheme.zip --force
   ```
3. Open **GNOME Tweaks** → **Appearance** → choose **Icons** or **Cursor**.

### CLI

```bash
theme-drop install FILE.zip [--force]
theme-drop list
theme-drop uninstall ThemeFolderName
```

## Uninstall Theme Drop

```bash
curl -fsSL https://cdn.jsdelivr.net/gh/christophwarner/theme-drop@main/uninstall.sh | bash
```

This only removes the Theme Drop app. Themes already copied into `~/.local/share/icons/` stay until you delete them or run `theme-drop uninstall …`.

## What it looks for

Inside the archive, Theme Drop finds folders with an `index.theme` file:

| Kind | Clue |
|------|------|
| Cursor | `cursors/` directory |
| Icon | `Directories=` in `index.theme`, or size folders like `48x48` / `scalable` |

Mixed packs (icons + cursors) install every theme found.

## Develop

```bash
cd theme-drop
./install.sh                  # install from this checkout
python3 -m pytest -q
```

## License

MIT
