# fzfex – kontext

- Účel: obal kolem `fzf`, náhled položky v externím okně aplikace podle mimetype; jen niri (Wayland), řízení přes `niri msg`.
- Soubory: `fzfex` (hlavní skript, Python, bez přípony), `fzfex-menu.py` (GTK4 nabídka „Otevřít v…“, musí ležet vedle skutečného `fzfex`), `fzf-tipy.md` (poznámky), `README.md` + `README.en.md` (obě udržovat souběžně).
- Instalace u uživatele: symlink `~/.local/bin/fzfex`; niri config `~/.config/niri/config.kdl`; pravidla `~/.config/fzfex/config`.
- Test: jen ručně v niri (`fd | fzfex`, `fzfex -E -m`); interní podpříkazy `--show/--show-list/--info/--toggle/--menu/--close` potřebují `FZFEX_SESSION` a `FZFEX_TERM_WID`.
- Stav: `$XDG_RUNTIME_DIR/fzfex-<pid>/` (`state`, `term` = wid terminálu, `want` = generace pro debounce, `disabled`, `opened`, `lock`).
- Fokus: `ctrl-v` (`FZFEX_FOCUS_KEY`) / `fzfex --focus` cyklí terminál → náhledy → terminál; bez `FZFEX_SESSION` prochází všechny state dir (kvůli globální zkratce niri, klávesy z náhledu k fzf nedojdou). Niri bind `Mod+P` jen navržen v README, do configu uživatele nepřidán.
- Vlastní volby jen `-E`/`--external[=OUT]`; zbytek jde do fzf. `-E` + `-m` = SPLIT režim. `E_DEFAULT_TO = "DP-2"`.
- Nezřejmé:
  - `{+f}` fzf maže hned po návratu → číst před forkem (double fork, ať fzf nečeká).
  - `{+f}` bez označení obsahuje aktuální položku → připnuté jen při `FZF_SELECT_COUNT != 0`.
  - Cesty vždy absolutní (aplikace běží s cwd = adresář souboru).
  - `focus-window` v niri vytáhne plovoucí okno nahoru → `refocus_terminal()` jen když fokus opravdu ztratil.
  - Přiřazení oken podle session id PID; po 1 s bere i cizí nová okna (jednoinstanční aplikace).
  - Uživatel má `focus-follows-mouse`.
- Commity: česky, uživatel navik61; repo veřejné na GitHubu (navik61/fzfex).
