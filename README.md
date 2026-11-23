# fzfex – fzf s náhledem v externím okně

**Česky** · [English](README.en.md)

`fzfex` je obal kolem `fzf`. Náhled vybrané položky neukazuje v terminálu, ale v **externím okně
aplikace podle mimetype** (obrázek → imv, PDF → zathura, video → mpv, …; podle výchozích aplikací
uživatele). Okno se umístí tak, aby
**nezakrylo seznam souborů** ve fzf. Fokus po otevření zůstane v terminálu, takže okno je aktivní
jen tehdy, když na něj najedeš myší (`focus-follows-mouse` v niri). Když přejdeš na jinou položku,
staré okno se zavře a otevře se náhled nové.

Určeno pro **niri (Wayland)**: polohu a velikost okna řídí přes `niri msg`.

Soubory v projektu: `fzfex` (skript), `fzfex-menu.py` (průhledná nabídka „Otevřít v…“, GTK4)
a `fzf-tipy.md` (poznámky k fzf).

## Instalace

1. Závislosti (Arch Linux):
   ```sh
   sudo pacman -S --needed python fzf file xdg-utils
   sudo pacman -S --needed python-gobject gtk4   # nabídka „Otevřít v…“ (jinak se použije rofi)
   sudo pacman -S --needed bat eza               # volitelné: hezčí náhled textu a adresářů
   ```
   Potřebuješ běžící **niri** a jeden z podporovaných terminálů (viz *Terminál*).
2. Stažení a odkaz do `PATH`:
   ```sh
   git clone https://github.com/navik61/fzfex.git ~/Projects/fzfex
   ln -s ~/Projects/fzfex/fzfex ~/.local/bin/fzfex
   ```
   `fzfex-menu.py` musí zůstat ve stejném adresáři jako skutečný soubor `fzfex` (odkaz se
   rozbalí).
3. Pravidla oken do `~/.config/niri/config.kdl` (doporučeno). Bez nich okna při otevření krátce
   probliknou jako dlaždice a náhled může vzít fokus:
   ```kdl
   // fzfex – nabídka „Otevřít v…“
   window-rule {
       match app-id=r"^cz\.fzfex\.menu$"
       open-floating true
       focus-ring { off; }
       border { off; }
   }
   // fzfex – náhledová okna (textové náhledy v terminálu mají app-id fzfex-preview)
   window-rule {
       match app-id=r"^(fzfex-preview|fzfex\.preview|imv|mpv|org\.pwmt\.zathura)$"
       open-floating true
       open-focused false
   }
   ```
   Do druhého pravidla doplň app-id svých prohlížečů (zjistíš přes `niri msg windows`).
4. Volitelně vlastní pravidla náhledu v `~/.config/fzfex/config` (viz *Konfigurace*).

Nabídka „Otevřít v…“ i náhledy používají **aplikace nainstalované u daného uživatele**: `.desktop`
soubory z `~/.local/share/applications` a `/usr/share/applications`, výchozí aplikace z jeho
`mimeapps.list` (`xdg-mime`) a jeho `$VISUAL`/`$EDITOR`.

## Rychlé použití

```sh
fzfex                       # soubory z FZF_DEFAULT_COMMAND
fd -t f | fzfex             # vlastní vstup
fd -e pdf | fzfex -m        # libovolné volby fzf se předají dál
fzfex -E                    # náhled na externím monitoru (FZFEX_EXTERNAL_TO, jinak DP-2)
fzfex --external=DVI-I-1    # náhled na zadaném monitoru
fzfex -E -m                 # náhled u terminálu, Tab ho připne na externí monitor (mřížka)
```

Bez `-E` se náhled otevírá vedle terminálu. `-E` a `--external` jsou jediné vlastní volby
`fzfex` a s volbami fzf nekolidují (fzf `-e` = přesná shoda funguje dál). Ostatní volby se
předají fzf.


### Klávesy

| Klávesa  | Akce                                              |
|----------|---------------------------------------------------|
| pohyb    | zavře starý náhled, otevře nový (s debounce)      |
| `alt-p`  | vypne nebo zapne externí náhled                   |
| `Tab`    | (s `-m`) označí soubor; jeho náhled zůstane otevřený (připnutý) i při pohybu na další soubory. S `-E -m` se připnutý náhled přesune na externí monitor |
| `ctrl-o` | otevře položku ve výchozí aplikaci natrvalo (fzfex běží dál) |
| `Enter`  | průhledná nabídka **Otevřít v…**; po otevření souboru fzfex skončí |
| `alt-enter` | vypíše výběr na stdout (původní Enter fzf); náhled se zavře |

Vnitřní preview panel fzf ukazuje informace o souboru: mime, typ, velikost, datum a aplikaci, která
náhled zobrazí.

### Více souborů najednou (`-m`)

S volbou `-m` (`--multi`, předá se fzf) `Tab` **připne** náhled souboru: okno zůstane otevřené
i po přechodu na jiný soubor. Vedle připnutých oken se vždy zobrazuje i náhled aktuálního souboru
pod kurzorem, který se při pohybu mění.

**`-E -m` (rozdělený režim):** náhled aktuálního souboru se zobrazuje **u terminálu na interním
monitoru** (umístění podle `FZFEX_MODE`, stejně jako bez `-E`). Po `Tab` se jeho okno přesune na
externí monitor do mřížky připnutých náhledů. Na externím monitoru jsou tedy jen připnuté soubory.
Po `Shift+Tab` se okno zavře. Pokud se kurzor vrátí na připnutý soubor, interní náhled zmizí,
protože soubor je už vidět na externím monitoru. Režim se zapne jen kombinací `-E` (nebo
`--external=…`) a `-m`/`--multi`. Samotné `-E` dál zobrazuje vše na externím monitoru.

Připnutá okna (v rozděleném režimu jen ta na externím monitoru) se proporcionálně rozmístí do mřížky:

- s `-E` (nebo `FZFEX_EXTERNAL_FROM`) na **celou pracovní plochu externího monitoru**,
- bez něj do místa vedle terminálu (podle `FZFEX_MODE`).

Počet sloupců a řádků se volí podle poměru stran monitoru tak, aby obsah 4:3 byl co největší.
Neúplný poslední řádek je vycentrovaný. Okno se v buňce vycentruje; prohlížeče, které si velikost
určují samy (viim, mpv), dostanou rozměr buňky jako maximum. Při označení nebo odznačení dalšího
souboru zůstanou otevřená okna (jen se přeskládají), nová se otevřou a okna odznačených souborů
se zavřou (`Shift+Tab` připnutí zruší). Když kurzor stojí na už připnutém souboru, nové okno se
neotevře. Dokud není nic označeno, chová se fzfex jako bez `-m` (náhled aktuální položky).

```sh
fd -e jpg -e png | fzfex -E -m
```

### Nabídka „Otevřít v…“ (Enter)

Enter otevře poloprůhledné okno bez rámečku se seznamem aplikací, které umí daný
mimetype otevřít (z `.desktop` souborů přes Gio). Výchozí aplikace je první. U textových souborů
je navíc `$VISUAL`/`$EDITOR` v terminálu, u souborů s vlastním pravidlem položka **Jako náhled
fzfex** a vždy **Vypsat cestu na stdout** (původní chování Enteru).

- Ovládání: `↑`/`↓` (`j`/`k`, `Tab`), `Enter`, čísla `1`–`9` a `0` přímo, myš (najetí a klik),
  `Esc`/`q` = zpět do fzf, `=`/`-` zoom, tažením mimo položky se okno přesune.
- Po výběru aplikace se soubor otevře odpojeně (přežije konec fzfex), **fzfex skončí** s kódem 0
  a náhledová okna se zavřou. S `-E` se okno aplikace přesune na externí monitor (stejný jako
  náhledy) a dostane fokus.
- S `-m` se otevřou všechny označené soubory. Aplikace s `%F`/`%U` v `Exec=` je dostane najednou,
  ostatní se spustí pro každý soubor zvlášť. Nabídka ukazuje jen aplikace, které umí všechny
  mimetypy výběru.
- Bez GTK4 (`python-gobject`) se nabídka zobrazí přes `rofi -dmenu`.

### Náhled na externím monitoru

**Ručně přepínačem:** `fzfex -E` pošle náhled na monitor z `FZFEX_EXTERNAL_TO`. Když proměnná
není nastavená, použije se `DP-2` (konstanta `E_DEFAULT_TO` ve skriptu). Když `DP-2` neexistuje,
použije se největší jiný monitor. `fzfex --external=VÝSTUP`
zvolí monitor přímo. Pokud je terminál přímo na cílovém monitoru, náhled jde na největší jiný
monitor, aby nezakryl seznam.

**Automaticky podle monitoru terminálu:** když je terminál na notebooku a chceš náhled na velkém
monitoru vždy, i bez `-E`:

```sh
export FZFEX_EXTERNAL_FROM=eDP-1   # ODKUD: monitory, na kterých běží terminál (do ~/.zshrc)
export FZFEX_EXTERNAL_TO=DP-2      # KAM: cílový monitor (volitelné, jinak největší jiný)
```

Pokud terminál běží na jiném výstupu, než je ve `FZFEX_EXTERNAL_FROM`, chová se `fzfex` jako dřív.
Volba se týká monitoru, na kterém je **terminál**. Chceš-li náhled na DVI-I-1 i z terminálu
na DP-2, nastav `FZFEX_EXTERNAL_FROM=eDP-1,DP-2`. Proměnné musí být exportované ve shellu, ze kterého
`fzfex` spouštíš (nejlépe v `~/.zshrc`). Řádek `okno:` ve vnitřním panelu fzf ukazuje, kam se
náhled umístí, na jakém monitoru je terminál a jaké jsou hodnoty `EXTERNAL_FROM` a `EXTERNAL_TO`. Staré názvy `FZFEX_EXTERNAL` a `FZFEX_EXTERNAL_OUTPUT` fungují dál.
Náhled se otevře vycentrovaný na aktivní ploše cílového monitoru (`move-window-to-monitor`).

## Terminál

Textové náhledy (`bat`, `less`, výpis adresáře), aplikace s `Terminal=true` a editor z nabídky se
spouštějí v terminálu. Volí se automaticky:

1. `FZFEX_TERM` / `FZFEX_OPEN_TERM`, pokud jsou nastavené (celý příkaz včetně přepínače pro
   spuštění programu, např. `foot --app-id=fzfex-preview`),
2. jinak terminál z `$TERMINAL`, pokud ho fzfex zná,
3. jinak první nainstalovaný z: `kitty`, `foot`, `alacritty`, `wezterm`, `ghostty`, `konsole`,
   `gnome-terminal`, `xterm`.

Náhledová okna dostanou app-id `fzfex-preview` (ghostty `fzfex.preview`, protože vyžaduje app-id
s tečkou). `konsole` a `gnome-terminal` app-id nastavit neumí, takže na ně pravidlo niri nezabere.
Použitý terminál ukazuje řádek `term.:` ve vnitřním panelu fzf.

## Konfigurace

### Proměnné prostředí

| Proměnná           | Výchozí                            | Význam |
|--------------------|------------------------------------|--------|
| `FZFEX_MODE`       | `auto`                             | `beside` = vedle terminálu, `pane` = přes preview panel fzf (pravá část terminálu), `fixed` = podle `FZFEX_GEOM`, `auto` = `beside`, pokud je vedle terminálu aspoň `FZFEX_MIN_W` px volného místa, jinak `pane` |
| `FZFEX_PANE`       | `50`                               | šířka preview panelu fzf v % (určuje i plochu v režimu `pane`) |
| `FZFEX_MIN_W`      | `500`                              | minimum volného místa pro režim `beside` |
| `FZFEX_MIN_W_FLOAT`| `300`                              | totéž pro plovoucí terminál (u něj se překrytí vyhýbáme víc, viz Řešení problémů) |
| `FZFEX_MAX_W`      | `1400`                             | maximální šířka okna v režimu `beside` |
| `FZFEX_MIN_H`      | `600`                              | minimální výška okna v režimu `beside` |
| `FZFEX_EXTERNAL_FROM` (dříve `FZFEX_EXTERNAL`) | – (vypnuto) | seznam výstupů oddělených čárkou (např. `eDP-1`). Když na některém z nich běží terminál, náhled se otevře na jiném monitoru |
| `FZFEX_EXTERNAL_TO` (dříve `FZFEX_EXTERNAL_OUTPUT`) | – (největší jiný monitor) | cílový monitor, např. `DVI-I-1` (názvy: `niri msg outputs`) |
| `FZFEX_EXTERNAL_SIZE` | `90`                            | maximální velikost náhledu na externím monitoru v % pracovní plochy; okno je vycentrované |
| `FZFEX_GEOM`       | `1200,40,1300,1300`                | `x,y,š,v` pro režim `fixed` |
| `FZFEX_TERM_GEOM`  | –                                  | ruční poloha terminálu `x,y,š,v` (pokud odhad nesedí) |
| `FZFEX_GAPS`       | z `gaps` v `~/.config/niri/config.kdl` | mezery mezi okny v niri |
| `FZFEX_DEBOUNCE`   | `0.15`                             | prodleva v s před otevřením (rychlé listování neotvírá každé okno) |
| `FZFEX_TIMEOUT`    | `5`                                | jak dlouho čekat na okno aplikace (s) |
| `FZFEX_TERM`       | automaticky (viz *Terminál*)       | terminál pro textové náhledy a pro aplikace s `Terminal=true` |
| `FZFEX_OPEN_TERM`  | automaticky (viz *Terminál*)       | terminál pro aplikace otevřené z nabídky „Otevřít v…“ |
| `FZFEX_MENU_STYL`  | `0`                                | barvy a font nabídky, styly 0–9 (0 tmavě zelená, 3 tmavě modrá, 4 Nord…) |
| `FZFEX_MENU_ALFA`  | `POZNAMKA_ALFA`, jinak `d0`        | krytí pozadí nabídky, hex `00`–`ff` |
| `FZFEX_MENU_ZOOM`  | `1`                                | zvětšení nabídky |
| `FZFEX_MENU_AMD`   | `1`                                | na hybridní grafice s AMD GPU vykreslovat nabídku na AMD (`0` = nechat výchozí GPU) |

### Pravidla podle mimetype – `~/.config/fzfex/config`

Na každém řádku je `mime-glob = příkaz`. Platí první pravidlo, které sedí. `{}` se nahradí cestou
k souboru; když v příkazu chybí, cesta se přidá na konec. `{w}` a `{h}` se nahradí šířkou a výškou
místa pro náhled. Pravidlo s nimi bere aplikaci jako „sama si určuje velikost“, takže okno
nepřetahuje, jen ho posune, aby bylo celé vidět. Hodnota `xdg` znamená výchozí aplikaci
(`xdg-mime`) a `none` znamená bez externího náhledu.

```ini
# obrázky přes swayimg místo viim
image/* = swayimg {}
# vlastní aplikace s maximální velikostí okna
image/gif = viim -W {w} -H {h} {}
# video bez zvuku a ve smyčce
video/* = mpv --mute=yes --loop {}
# zip bez náhledu
application/zip = none
# Markdown ve výchozí aplikaci (jinak by šel do bat)
text/markdown = xdg
```

Vestavěná pravidla (platí až po pravidlech z configu):

- `text/*`, JSON, XML, JS, shell, TOML, YAML, prázdné soubory → terminál s `bat --paging=always`
  (bez `bat` se použije `less`)
- `inode/directory` → terminál s `eza --tree --level=2 | less` (bez `eza` se použije `ls -la`)
- všechno ostatní → výchozí aplikace z `xdg-mime query default` (řádek `Exec=` z `.desktop`),
  záložně `xdg-open`

## Jak to funguje

1. Na začátku si `fzfex` zapamatuje ID okna terminálu (`niri msg focused-window`).
2. fzf má `--bind focus:…` a `multi:execute-silent(fzfex --show-list {+f} {f})`. `{+f}` je soubor
   s označenými položkami (bez označení s aktuální položkou), `{f}` soubor s položkou pod kurzorem.
   Příkaz oba načte (duplicity odstraní) a hned se odpojí na pozadí (double fork), takže fzf nečeká.
   Připnuté položky pozná podle proměnné `FZF_SELECT_COUNT`, kterou fzf exportuje, protože `{+f}`
   bez označení obsahuje aktuální položku. V režimu `-E -m` jdou připnuté do mřížky na externí
   monitor a aktuální k terminálu. Okno, které mění monitor, se přesune
   (`move-window-to-monitor`) a dostane velikost nové buňky.
3. Proces na pozadí počká `FZFEX_DEBOUNCE`. Pokud mezitím přišel jiný výběr, skončí. Jinak pod
   zámkem porovná požadované soubory s otevřenými okny (stav v `state`): okna souborů, které už
   nejsou ve výběru, zavře (`close-window`, případně SIGTERM skupině procesů), pro nové soubory
   spustí aplikace, každou v nové session.
4. Čeká, až se v `niri msg windows` objeví nová okna. Okno patří té aplikaci, do jejíž session
   patří PID okna; po 1 s vezme i jiná nová okna (aplikace, které okno otvírají v už běžící
   instanci). Místo pro náhled se při více souborech rozdělí na mřížku (viz `-m`).
5. Okno přepne na plovoucí, nastaví mu velikost a polohu (`move-window-to-floating`,
   `set-window-width/height`, `move-floating-window`). Fokus vrátí do terminálu (`focus-window`)
   jen tehdy, když ho náhled opravdu sebral, protože `focus-window` plovoucí okno vytáhne nahoru.
   Kontrolu opakuje po 0,25, 0,75 a 1,75 s, protože aplikace si velikost mění po načtení obsahu.
   Když je okno i tak větší, než se do vymezeného místa vejde, posune ho tak, aby bylo celé na
   obrazovce. Výšku pracovní plochy odhaduje z výšky dlaždic na dané ploše.

**Velikost okna:** aplikacím, které si velikost určují samy podle obsahu, se maximální rozměr
předá už při spuštění: `mpv --autofit-larger=šxv` a `viim -W š -H v` (vlastní prohlížeč autora).
Další lze doplnit do `SIZE_HINTS` ve skriptu. Skript jim okno nepřetahuje,
takže obrázek se do místa vejde celý. Ostatním aplikacím se velikost nastaví přes niri.
6. Když fzf skončí, zavřou se náhledy a smaže se stav v `$XDG_RUNTIME_DIR/fzfex-<pid>/`.
7. Enter je `transform(fzfex --menu {+f})`: fzfex sestaví seznam aplikací, spustí `fzfex-menu.py`
   (JSON na stdin, index volby na stdout; okno se samo přepne v niri na plovoucí a vycentruje) a
   podle volby vypíše akci pro fzf: `abort` po otevření (a zapíše příznak `opened`, takže návratový
   kód je 0), `accept` pro výpis na stdout, nic při `Esc` (fzf běží dál).

**Poloha terminálu:** u plovoucího terminálu ji niri hlásí přesně. U dlaždicového ji niri
nesděluje, proto se odhaduje ze šířek sloupců a `gaps`. Odhad předpokládá, že pohled není
odscrollovaný, případně že je terminál zarovnaný k pravému okraji. Když nesedí, nastav
`FZFEX_TERM_GEOM` nebo použij `FZFEX_MODE=pane` či `fixed`.

## Výchozí aplikace pro náhled

Náhled otevírá výchozí aplikaci pro daný mimetype. Změna, např. obrázky v imv:
`xdg-mime default imv.desktop image/png` (a podobně pro další typy), nebo pravidlo
v `~/.config/fzfex/config`.

Poznámka autora: u mě je pro obrázky výchozí `viim.desktop` (záloha původního nastavení
`~/.config/mimeapps.list.bak-fzfex`).

## Závislosti

`python3`, `fzf` ≥ 0.53 (události `multi`, akce `transform`), `niri` (IPC `niri msg`), `file`,
`xdg-utils` (`xdg-mime`, `xdg-open`). Pro nabídku `python-gobject` s GTK4 (jinak `rofi`).
Terminál (viz *Terminál*). Volitelně `bat`, `eza` a aplikace podle mimetype (imv, zathura,
mpv…).

## Řešení problémů

- **Náhled je schovaný za terminálem.** U plovoucího terminálu niri vytáhne nahoru vždy to okno,
  které má fokus. Proto:
  1. Aplikace pro náhled by měla mít window-rule `open-focused false`, aby fokus vůbec nebrala.
     viim, imv a pqiv ho už mají. Skript pak fokus nevrací a náhled zůstane nahoře.
  2. U plovoucího terminálu volí režim `auto` umístění vedle terminálu už od 300 px volného místa
     (`FZFEX_MIN_W_FLOAT`). Překrytý náhled by se totiž schoval pod terminál pokaždé, když na
     terminál najedeš myší.
  U dlaždicového terminálu problém nevzniká, protože plovoucí okna jsou vždy nad dlaždicemi.

- **Okno při otevření krátce probleskne jako dlaždice nebo posune pohled.** niri ho nejdřív otevře
  podle svých pravidel a teprve potom ho skript přepne na plovoucí. Pomůže window-rule pro
  konkrétní aplikaci v `~/.config/niri/config.kdl`:
  ```kdl
  window-rule {
      match app-id="^(imv|mpv|org.pwmt.zathura|fzfex-preview)$"
      open-floating true
      open-focused false
  }
  ```
- **Okno se nezavře nebo se zavře jiné okno.** Aplikace s jednou instancí (např. Zed, prohlížeče)
  otevírají okno v běžícím procesu a skript pak bere „první nové okno“. Pro takové typy nastav
  v configu jinou aplikaci.
- **Okno je na špatném místě.** Viz *Poloha terminálu* výše (`FZFEX_TERM_GEOM`, `FZFEX_MODE`).
- **Nic se neotevře.** Zkontroluj `xdg-mime query default <mime>` a jestli aplikace během
  `FZFEX_TIMEOUT` otevře okno. Ruční test: `FZFEX_SESSION=t FZFEX_TERM_WID=<id> fzfex --show soubor`.
- **Soubory z podadresářů se neotevřou** (vypadá to jako problém s velkými obrázky). Opraveno:
  fzf předává cesty relativně a aplikace se spouští v adresáři souboru, takže dostávala
  špatnou cestu. Skript teď cesty vždy převádí na absolutní.
- **Okno přesahuje mimo obrazovku.** Aplikace si nejspíš vynutila větší okno. Skript ho posune na
  obrazovku, i když pak může částečně zakrýt terminál. Pro vlastní prohlížeč přidej pravidlo
  s `{w}`/`{h}` nebo ho doplň do `SIZE_HINTS` ve skriptu.
- **Nabídka „Otevřít v…“ krátce probleskne jako dlaždice.** Skript ji přepne na plovoucí až po
  otevření. Pomůže window-rule (app-id `cz.fzfex.menu`) v `~/.config/niri/config.kdl`:
  ```kdl
  window-rule {
      match app-id=r"^cz\.fzfex\.menu$"
      open-floating true
      focus-ring { off; }
      border { off; }
  }
  ```
- **V nabídce chybí aplikace.** Nabídka bere aplikace z `.desktop` souborů s daným `MimeType=`
  (stejně jako „Otevřít pomocí“ ve správcích souborů). U výběru s různými typy jen ty, které umí
  všechny. Kontrola: `gio mime <mimetype>`.
- **Mimo niri** skript skončí s chybou (vyžaduje `NIRI_SOCKET`).
- **Textový náhled se otevře ve špatném terminálu nebo vůbec.** Zkontroluj řádek `term.:` ve
  vnitřním panelu fzf a případně nastav `FZFEX_TERM`, např.
  `export FZFEX_TERM="foot --app-id=fzfex-preview"`.
- **Nabídka se nevykreslí (prázdné nebo černé okno).** Zkus `FZFEX_MENU_AMD=0`. Bez GTK4 se
  použije `rofi -dmenu`.

## Podpora

Pokud ti fzfex ušetří čas, můžeš mi koupit kafe:

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/Q7Z72B5QVS)

## Licence

MIT, viz soubor [`LICENSE`](LICENSE).
