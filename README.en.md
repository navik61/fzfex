# fzfex – fzf with previews in real application windows

[Česky](README.md) · **English**

`fzfex` is a wrapper around `fzf`. Instead of showing the preview inside the terminal, it opens the
selected item in an **external window of the application for its mimetype** (image → imv,
PDF → zathura, video → mpv, …, according to your default applications). The window is placed so
that it **does not cover the fzf file list**. Focus stays in the terminal, so the preview window is
only active when you hover it with the mouse (`focus-follows-mouse` in niri). When you move to
another item, the old window closes and the new preview opens.

Built for **niri (Wayland)**: window position and size are controlled via `niri msg`.

> The user interface (menu labels, info panel) is in Czech. The behaviour is described below.

Project files: `fzfex` (the script), `fzfex-menu.py` (translucent "Open with…" menu, GTK4) and
`fzf-tipy.md` (fzf notes, Czech).

## Installation

1. Dependencies (Arch Linux):
   ```sh
   sudo pacman -S --needed python fzf file xdg-utils
   sudo pacman -S --needed python-gobject gtk4   # "Open with…" menu (falls back to rofi)
   sudo pacman -S --needed bat eza               # optional: nicer text and directory previews
   ```
   You need a running **niri** session and one of the supported terminals (see *Terminal*).
2. Clone and link into your `PATH`:
   ```sh
   git clone https://github.com/navik61/fzfex.git ~/Projects/fzfex
   ln -s ~/Projects/fzfex/fzfex ~/.local/bin/fzfex
   ```
   `fzfex-menu.py` must stay in the same directory as the real `fzfex` file (the symlink is
   resolved).
3. Window rules in `~/.config/niri/config.kdl` (recommended). Without them, windows briefly flash
   as tiles when opening and the preview may steal focus:
   ```kdl
   // fzfex – "Open with…" menu
   window-rule {
       match app-id=r"^cz\.fzfex\.menu$"
       open-floating true
       focus-ring { off; }
       border { off; }
   }
   // fzfex – preview windows (text previews in a terminal use app-id fzfex-preview)
   window-rule {
       match app-id=r"^(fzfex-preview|fzfex\.preview|imv|mpv|org\.pwmt\.zathura)$"
       open-floating true
       open-focused false
   }
   ```
   Add the app-ids of your own viewers to the second rule (find them with `niri msg windows`).
4. Optionally, custom preview rules in `~/.config/fzfex/config` (see *Configuration*).

Both the "Open with…" menu and the previews use **the applications installed for the current
user**: `.desktop` files from `~/.local/share/applications` and `/usr/share/applications`, default
applications from the user's `mimeapps.list` (`xdg-mime`) and their `$VISUAL`/`$EDITOR`.

## Quick start

```sh
fzfex                       # files from FZF_DEFAULT_COMMAND
fd -t f | fzfex             # custom input
fd -e pdf | fzfex -m        # any fzf options are passed through
fzfex -E                    # preview on an external monitor (FZFEX_EXTERNAL_TO, else DP-2)
fzfex --external=DVI-I-1    # preview on the given monitor
fzfex -E -m                 # preview next to the terminal, Tab pins it to the external monitor (grid)
```

Without `-E` the preview opens next to the terminal. `-E` and `--external` are the only options of
`fzfex` itself and they don't clash with fzf options (fzf's `-e` = exact match still works).
Everything else is passed to fzf.

### Keys

| Key         | Action                                              |
|-------------|-----------------------------------------------------|
| movement    | closes the old preview, opens a new one (debounced) |
| `alt-p`     | toggles the external preview off/on                 |
| `Tab`       | (with `-m`) marks the file; its preview stays open (pinned) while you move to other files. With `-E -m` the pinned preview moves to the external monitor |
| `ctrl-o`    | opens the item in the default application permanently (fzfex keeps running) |
| `Enter`     | translucent **Open with…** menu; fzfex exits after opening the file |
| `alt-enter` | prints the selection to stdout (fzf's original Enter); previews close |
| `Mod+P`  | (niri shortcut, see below) switches focus terminal ↔ preview |

The fzf preview pane shows file information: mimetype, type, size, date, the application used for
the preview (`náhled:`), the window placement (`okno:`) and the terminal (`term.:`).

### Switching focus (`fzfex --focus`)

`fzfex --focus` moves focus to the preview window (e.g. to zoom, pan or control playback from
the keyboard) and back. Keys pressed in the preview do not reach fzf, so it is a global niri
shortcut rather than an fzf key:

```kdl
binds {
    Mod+P hotkey-overlay-title="fzfex: focus terminal ↔ preview" { spawn "~/.local/bin/fzfex" "--focus"; }
}
```

`fzfex --focus` cycles terminal → preview → next preview → … → terminal. It finds the fzfex
session by the focused window; when focus is elsewhere, it switches to the terminal of the most
recently started fzfex. The full path in `spawn` is needed if niri does not have `~/.local/bin`
in its `PATH`.

### Multiple files (`-m`)

With `-m` (`--multi`, passed to fzf), `Tab` **pins** a file's preview: the window stays open after
you move to another file. Next to the pinned windows, the preview of the file under the cursor is
always shown and follows the cursor.

**`-E -m` (split mode):** the preview of the current file is shown **next to the terminal on the
internal monitor** (placed according to `FZFEX_MODE`, as without `-E`). After `Tab`, its window
moves to the external monitor into the grid of pinned previews, so the external monitor only shows
pinned files. `Shift+Tab` closes the window. When the cursor returns to a pinned file, the internal
preview disappears because the file is already visible on the external monitor. Split mode is only
enabled by combining `-E` (or `--external=…`) with `-m`/`--multi`. Plain `-E` still shows
everything on the external monitor.

Pinned windows (in split mode only those on the external monitor) are laid out proportionally in a
grid:

- with `-E` (or `FZFEX_EXTERNAL_FROM`) across **the whole work area of the external monitor**,
- otherwise in the space next to the terminal (according to `FZFEX_MODE`).

The number of columns and rows is chosen from the monitor's aspect ratio so that 4:3 content is as
large as possible. An incomplete last row is centered. Each window is centered in its cell; viewers
that size themselves (viim, mpv) get the cell size as their maximum. When you mark or unmark
another file, open windows stay (they are only re-arranged), new ones open and windows of unmarked
files close (`Shift+Tab` unpins). When the cursor is on an already pinned file, no new window is
opened. As long as nothing is marked, fzfex behaves as without `-m` (preview of the current item).

```sh
fd -e jpg -e png | fzfex -E -m
```

### "Open with…" menu (Enter)

Enter opens a translucent borderless window listing the applications that can open the mimetype
(from `.desktop` files via Gio). The default application is first. Text files additionally get
`$VISUAL`/`$EDITOR` in a terminal, files with a custom rule get **"Jako náhled fzfex"** (as the fzfex
preview), and there is always **"Vypsat cestu na stdout"** (print the path to stdout – the original
Enter behaviour).

- Controls: `↑`/`↓` (`j`/`k`, `Tab`), `Enter`, digits `1`–`9` and `0` directly, mouse (hover and
  click), `Esc`/`q` = back to fzf, `=`/`-` zoom, drag outside the items to move the window.
- After choosing an application the file is opened detached (it survives fzfex exiting),
  **fzfex exits** with code 0 and the preview windows close. With `-E` the application window
  moves to the external monitor (same as the previews) and gets focus.
- With `-m` all marked files are opened. Applications with `%F`/`%U` in `Exec=` get them all at
  once, others are started once per file. The menu only lists applications that can handle every
  mimetype in the selection.
- Without GTK4 (`python-gobject`) the menu is shown via `rofi -dmenu`.

### Preview on an external monitor

**Manually with a flag:** `fzfex -E` sends the preview to the monitor from `FZFEX_EXTERNAL_TO`. If
the variable isn't set, `DP-2` is used (constant `E_DEFAULT_TO` in the script). If `DP-2` doesn't
exist, the largest other monitor is used. `fzfex --external=OUTPUT` picks the monitor directly. If
the terminal is on the target monitor itself, the preview goes to the largest other monitor so it
doesn't cover the list.

**Automatically by the terminal's monitor:** if your terminal is on a laptop screen and you always
want the preview on the big monitor, even without `-E`:

```sh
export FZFEX_EXTERNAL_FROM=eDP-1   # FROM: monitors the terminal runs on (put in ~/.zshrc)
export FZFEX_EXTERNAL_TO=DP-2      # TO: target monitor (optional, else the largest other one)
```

If the terminal is on an output not listed in `FZFEX_EXTERNAL_FROM`, `fzfex` behaves as usual. The
setting refers to the monitor the **terminal** is on. To get the preview on DVI-I-1 also from a
terminal on DP-2, set `FZFEX_EXTERNAL_FROM=eDP-1,DP-2`. The variables must be exported in the shell
you run `fzfex` from (ideally in `~/.zshrc`). The `okno:` line in the fzf preview pane shows where
the preview will be placed, which monitor the terminal is on and the values of `EXTERNAL_FROM` and
`EXTERNAL_TO`. The old names `FZFEX_EXTERNAL` and `FZFEX_EXTERNAL_OUTPUT` still work. The preview
opens centered on the active workspace of the target monitor (`move-window-to-monitor`).

## Terminal

Text previews (`bat`, `less`, directory listing), applications with `Terminal=true` and the editor
from the menu run in a terminal. It is chosen automatically:

1. `FZFEX_TERM` / `FZFEX_OPEN_TERM` if set (the full command including the option that runs a
   program, e.g. `foot --app-id=fzfex-preview`),
2. otherwise the terminal from `$TERMINAL`, if fzfex knows it,
3. otherwise the first installed one of: `kitty`, `foot`, `alacritty`, `wezterm`, `ghostty`,
   `konsole`, `gnome-terminal`, `xterm`.

Preview windows get the app-id `fzfex-preview` (`fzfex.preview` for ghostty, which requires an
app-id with a dot). `konsole` and `gnome-terminal` can't set an app-id, so niri window rules won't
match them. The terminal in use is shown on the `term.:` line of the fzf preview pane.

## Configuration

### Environment variables

| Variable           | Default                            | Meaning |
|--------------------|------------------------------------|---------|
| `FZFEX_MODE`       | `auto`                             | `beside` = next to the terminal, `pane` = over the fzf preview pane (right part of the terminal), `fixed` = per `FZFEX_GEOM`, `auto` = `beside` if there are at least `FZFEX_MIN_W` px free next to the terminal, else `pane` |
| `FZFEX_PANE`       | `50`                               | width of the fzf preview pane in % (also the area in `pane` mode) |
| `FZFEX_MIN_W`      | `500`                              | minimum free space for `beside` mode |
| `FZFEX_MIN_W_FLOAT`| `300`                              | same for a floating terminal (overlap is avoided more, see Troubleshooting) |
| `FZFEX_MAX_W`      | `1400`                             | maximum window width in `beside` mode |
| `FZFEX_MIN_H`      | `600`                              | minimum window height in `beside` mode |
| `FZFEX_EXTERNAL_FROM` (formerly `FZFEX_EXTERNAL`) | – (off) | comma-separated outputs (e.g. `eDP-1`). If the terminal runs on one of them, the preview opens on another monitor |
| `FZFEX_EXTERNAL_TO` (formerly `FZFEX_EXTERNAL_OUTPUT`) | – (largest other monitor) | target monitor, e.g. `DVI-I-1` (names: `niri msg outputs`) |
| `FZFEX_EXTERNAL_SIZE` | `90`                            | maximum preview size on the external monitor in % of the work area; the window is centered |
| `FZFEX_GEOM`       | `1200,40,1300,1300`                | `x,y,w,h` for `fixed` mode |
| `FZFEX_TERM_GEOM`  | –                                  | manual terminal position `x,y,w,h` (if the estimate is wrong) |
| `FZFEX_GAPS`       | from `gaps` in `~/.config/niri/config.kdl` | gaps between windows in niri |
| `FZFEX_DEBOUNCE`   | `0.15`                             | delay in seconds before opening (fast scrolling doesn't open every window) |
| `FZFEX_TIMEOUT`    | `5`                                | how long to wait for the application window (s) |
| `FZFEX_TERM`       | automatic (see *Terminal*)         | terminal for text previews and `Terminal=true` applications |
| `FZFEX_OPEN_TERM`  | automatic (see *Terminal*)         | terminal for applications opened from the "Open with…" menu |
| `FZFEX_MENU_STYL`  | `0`                                | menu colours and font, styles 0–9 (0 dark green, 3 dark blue, 4 Nord…) |
| `FZFEX_MENU_ALFA`  | `POZNAMKA_ALFA`, else `d0`         | menu background opacity, hex `00`–`ff` |
| `FZFEX_MENU_ZOOM`  | `1`                                | menu zoom |
| `FZFEX_MENU_AMD`   | `1`                                | on hybrid graphics with an AMD GPU, render the menu on the AMD GPU (`0` = keep the default GPU) |

### Rules by mimetype – `~/.config/fzfex/config`

Each line is `mime-glob = command`. The first matching rule wins. `{}` is replaced with the file
path; if it's missing, the path is appended. `{w}` and `{h}` are replaced with the width and
height of the preview area. A rule using them treats the application as sizing itself, so the
window isn't resized, only moved to be fully visible. The value `xdg` means the default
application (`xdg-mime`) and `none` means no external preview.

```ini
# images in swayimg
image/* = swayimg {}
# custom application with a maximum window size
image/gif = viim -W {w} -H {h} {}
# video muted and looping
video/* = mpv --mute=yes --loop {}
# no preview for zip
application/zip = none
# Markdown in the default application (otherwise it would go to bat)
text/markdown = xdg
```

Built-in rules (applied after the rules from the config):

- `text/*`, JSON, XML, JS, shell, TOML, YAML, empty files → terminal with `bat --paging=always`
  (`less` without `bat`)
- `inode/directory` → terminal with `eza --tree --level=2 | less` (`ls -la` without `eza`)
- everything else → default application from `xdg-mime query default` (the `Exec=` line of the
  `.desktop` file), falling back to `xdg-open`

To change the default preview application, e.g. images in imv:
`xdg-mime default imv.desktop image/png` (and similarly for other types), or add a rule to
`~/.config/fzfex/config`.

Tip: for images, try [viim](https://github.com/navik61/viim), a minimalist transparent viewer by
the same author. Its window is sized exactly to the image and fzfex passes it the maximum size
(`-W`/`-H`), so the preview always fits.

## How it works

1. At start, `fzfex` remembers the terminal window ID (`niri msg focused-window`).
2. fzf has `--bind focus:…` and `multi:execute-silent(fzfex --show-list {+f} {f})`. `{+f}` is a
   file with the marked items (the current item when nothing is marked), `{f}` a file with the item
   under the cursor. The command reads both (removing duplicates) and immediately detaches into the
   background (double fork), so fzf doesn't wait. Pinned items are recognised via the
   `FZF_SELECT_COUNT` variable exported by fzf, since `{+f}` contains the current item when nothing
   is marked. In `-E -m` mode, pinned items go to the grid on the external monitor and the current
   one next to the terminal. A window that changes monitor is moved (`move-window-to-monitor`) and
   resized to its new cell.
3. The background process waits `FZFEX_DEBOUNCE`. If another selection arrived meanwhile, it exits.
   Otherwise, under a lock, it compares the requested files with the open windows (state in
   `state`): windows of files no longer selected are closed (`close-window`, or SIGTERM to the
   process group), and applications for new files are started, each in a new session.
4. It waits for new windows to appear in `niri msg windows`. A window belongs to the application
   whose session the window's PID is in; after 1 s it also takes other new windows (applications
   that open the window in an already running instance). With multiple files, the preview area is
   split into a grid (see `-m`).
5. The window is made floating, sized and positioned (`move-window-to-floating`,
   `set-window-width/height`, `move-floating-window`). Focus is returned to the terminal
   (`focus-window`) only if the preview actually took it, because `focus-window` raises a floating
   window. The check is repeated after 0.25, 0.75 and 1.75 s, since applications resize after
   loading content. If the window is still larger than the area, it is moved to be fully on screen.
   The work area height is estimated from the tile heights on the workspace.
6. When fzf exits, the previews close and the state in `$XDG_RUNTIME_DIR/fzfex-<pid>/` is removed.
7. Enter is `transform(fzfex --menu {+f})`: fzfex builds the application list, runs
   `fzfex-menu.py` (JSON on stdin, chosen index on stdout; the window floats and centers itself in
   niri) and prints an fzf action: `abort` after opening (and writes an `opened` flag so the exit
   code is 0), `accept` to print to stdout, nothing on `Esc` (fzf keeps running).

**Window size:** applications that size themselves by content get the maximum size at start:
`mpv --autofit-larger=WxH` and `viim -W w -H h` ([viim](https://github.com/navik61/viim), the author's minimalist viewer). More can be added to
`SIZE_HINTS` in the script. Their windows aren't resized, so the image fits entirely. Other
applications are resized via niri.

**Terminal position:** for a floating terminal niri reports it exactly. For a tiled one niri
doesn't, so it's estimated from column widths and `gaps`. The estimate assumes the view isn't
scrolled, or that the terminal is aligned to the right edge. If it's wrong, set `FZFEX_TERM_GEOM`
or use `FZFEX_MODE=pane` or `fixed`.

## Dependencies

`python3`, `fzf` ≥ 0.53 (`multi` event, `transform` action), `niri` (IPC `niri msg`), `file`,
`xdg-utils` (`xdg-mime`, `xdg-open`). For the menu `python-gobject` with GTK4 (else `rofi`). A
terminal (see *Terminal*). Optionally `bat`, `eza` and applications per mimetype (imv, zathura,
mpv…).

## Troubleshooting

- **The preview is hidden behind the terminal.** With a floating terminal, niri always raises the
  focused window. Therefore:
  1. The preview application should have the window rule `open-focused false` so it never takes
     focus. The script then doesn't need to return focus and the preview stays on top.
  2. With a floating terminal, `auto` mode places the preview beside the terminal from just 300 px
     of free space (`FZFEX_MIN_W_FLOAT`), because an overlapping preview would hide under the
     terminal every time you hover it.
  This doesn't happen with a tiled terminal, since floating windows are always above tiles.
- **The window briefly flashes as a tile or scrolls the view.** niri first opens it according to
  its own rules and only then does the script make it floating. A window rule helps (see
  *Installation*, step 3).
- **The window doesn't close, or a different window closes.** Single-instance applications (e.g.
  Zed, browsers) open the window in a running process and the script takes "the first new window".
  Configure a different application for such types.
- **The window is in the wrong place.** See *Terminal position* above (`FZFEX_TERM_GEOM`,
  `FZFEX_MODE`).
- **Nothing opens.** Check `xdg-mime query default <mime>` and whether the application opens a
  window within `FZFEX_TIMEOUT`. Manual test:
  `FZFEX_SESSION=t FZFEX_TERM_WID=<id> fzfex --show file`.
- **The window extends off screen.** The application probably forced a larger window. The script
  moves it on screen, even if it then partly covers the terminal. For your own viewer, add a rule
  with `{w}`/`{h}` or add it to `SIZE_HINTS` in the script.
- **The "Open with…" menu briefly flashes as a tile.** Add the `cz.fzfex.menu` window rule (see
  *Installation*, step 3).
- **An application is missing from the menu.** The menu takes applications from `.desktop` files
  with a matching `MimeType=` (like "Open with" in file managers). For a selection with mixed
  types, only those that handle all of them. Check: `gio mime <mimetype>`.
- **Outside niri** the script exits with an error (it requires `NIRI_SOCKET`).
- **A text preview opens in the wrong terminal or not at all.** Check the `term.:` line in the fzf
  preview pane and set `FZFEX_TERM` if needed, e.g.
  `export FZFEX_TERM="foot --app-id=fzfex-preview"`.
- **The menu doesn't render (empty or black window).** Try `FZFEX_MENU_AMD=0`. Without GTK4,
  `rofi -dmenu` is used.

## Support

If fzfex saves you time, you can buy me a coffee:

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/Q7Z72B5QVS)

## License

MIT, see [`LICENSE`](LICENSE).
