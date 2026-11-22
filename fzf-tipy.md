# fzf – rozšířené použití a nejlepší tipy

> Psáno pro **fzf 0.75**, **zsh**, Arch Linux. Počítá s nástroji, které už máš: `fd`, `rg`, `bat`, `eza`, `delta`, `zoxide`, `tmux`, `fzf-tab`.

---

## 1. Základ: vyhledávací syntaxe (to, co lidé nejčastěji neznají)

Do promptu fzf můžeš psát víc výrazů oddělených mezerou – všechny musí platit (AND).

| Zápis      | Význam                                   | Příklad              |
|------------|------------------------------------------|----------------------|
| `abc`      | fuzzy shoda                              | `cfgzsh`             |
| `'abc`     | přesná shoda (exact)                     | `'config`            |
| `'abc'`    | přesná shoda na hranici slova            | `'test'`             |
| `^abc`     | začíná na                                | `^src`               |
| `abc$`     | končí na                                 | `.md$`               |
| `!abc`     | NEobsahuje                               | `!node_modules`      |
| `!^abc`    | nezačíná na                              | `!^.git`             |
| `!abc$`    | nekončí na                               | `!.lock$`            |
| `a \| b`   | NEBO                                     | `.py$ \| .sh$`       |

Kombinace: `^src .ts$ !test` = soubory ze `src`, končící `.ts`, bez „test“.

Užitečné přepínače:

- `-e` / `--exact` – výchozí exact režim (fuzzy pak zapneš apostrofem).
- `-i` / `+i` – vynutit case-insensitive / sensitive (výchozí je „smart case“).
- `--scheme=path` – lepší skórování pro cesty (fd/find výstup), `--scheme=history` pro historii.
- `--tiebreak=begin,length` – při shodném skóre preferuj kratší / dřívější shodu.

---

## 2. Klávesy uvnitř fzf (výchozí)

| Klávesa              | Akce                                        |
|----------------------|---------------------------------------------|
| `Ctrl-J/K`, `Ctrl-N/P` | pohyb dolů/nahoru                         |
| `Tab` / `Shift-Tab`  | označit položku (jen s `-m`)                |
| `Ctrl-A`, `Ctrl-E`   | začátek / konec řádku promptu               |
| `Ctrl-W`, `Ctrl-U`   | smazat slovo / celý dotaz                   |
| `Alt-B`, `Alt-F`     | o slovo zpět / vpřed                        |
| `Shift-↑/↓`          | scroll v preview                            |
| `Esc`, `Ctrl-C`, `Ctrl-G` | zrušit                                 |

Vlastní bindingy přidáš přes `--bind` (viz sekce 4).

---

## 3. Globální konfigurace (`~/.zshrc`)

Momentálně máš jen `source /usr/share/fzf/key-bindings.zsh` bez proměnných. Tohle je doporučený základ:

```zsh
# --- Zdroj souborů: fd je rychlejší než find a respektuje .gitignore ---
export FZF_DEFAULT_COMMAND='fd --type f --hidden --follow --exclude .git'

# --- Výchozí vzhled a chování pro každé volání fzf ---
export FZF_DEFAULT_OPTS="
  --height=60% --layout=reverse --border=rounded --info=inline-right
  --style=full
  --highlight-line --cycle --multi
  --preview-window='right,55%,border-left,hidden'
  --bind='ctrl-/:toggle-preview'
  --bind='ctrl-a:toggle-all'
  --bind='ctrl-y:execute-silent(echo -n {+} | wl-copy)+abort'
  --bind='alt-up:preview-half-page-up,alt-down:preview-half-page-down'
  --bind='ctrl-s:toggle-sort'
"
# (na X11 místo wl-copy použij: xclip -selection clipboard)

# --- Ctrl-T: vložit soubor(y) do příkazové řádky ---
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
export FZF_CTRL_T_OPTS="
  --walker-skip .git,node_modules,target,.venv
  --preview 'bat -n --color=always --line-range :300 {}'
  --preview-window 'right,60%,border-left'
  --bind 'ctrl-/:change-preview-window(down|hidden|)'"

# --- Alt-C: cd do adresáře, s náhledem stromu ---
export FZF_ALT_C_COMMAND='fd --type d --hidden --follow --exclude .git'
export FZF_ALT_C_OPTS="--preview 'eza --tree --level=2 --color=always --icons {}'"

# --- Ctrl-R: historie s náhledem celého (i víceřádkového) příkazu ---
export FZF_CTRL_R_OPTS="
  --preview 'echo {2..}' --preview-window up:3:hidden:wrap
  --bind 'ctrl-/:toggle-preview'
  --bind 'ctrl-y:execute-silent(echo -n {2..} | wl-copy)+abort'
  --color header:italic
  --header 'Ctrl-Y: zkopírovat | Ctrl-/: náhled'"
```

### Moderní způsob načtení integrace

Místo `source /usr/share/fzf/key-bindings.zsh` lze použít (od 0.48):

```zsh
source <(fzf --zsh)   # key-bindings + completion najednou
```

> Pozor: ty používáš **fzf-tab**, který přebírá `Tab`. `fzf --zsh` přidá i `**<Tab>` completion – obvykle to s fzf-tab koexistuje, ale pokud by se praly, nech jen `key-bindings.zsh` jako teď.

### Bonus: `**<Tab>` completion (pokud ji zapneš)

```zsh
vim **<Tab>        # soubory
cd **<Tab>         # adresáře
kill -9 **<Tab>    # procesy
ssh **<Tab>        # hosty z ~/.ssh/config a /etc/hosts
export **<Tab>     # proměnné prostředí
```

Aby completion používala `fd`:

```zsh
_fzf_compgen_path() { fd --hidden --follow --exclude .git . "$1" }
_fzf_compgen_dir()  { fd --type d --hidden --follow --exclude .git . "$1" }
```

---

## 4. Akce a `--bind` – tady je skutečná síla fzf

Syntaxe: `--bind 'KLÁVESA_NEBO_UDÁLOST:akce1+akce2'`

### Nejužitečnější akce

| Akce                         | Co dělá                                                         |
|------------------------------|-----------------------------------------------------------------|
| `execute(cmd)`               | spustí příkaz a vrátí se do fzf (např. otevřít v editoru)       |
| `execute-silent(cmd)`        | totéž bez překreslení (kopírování do schránky…)                 |
| `become(cmd)`                | **nahradí** fzf příkazem (lepší než `$(fzf)` + if)              |
| `reload(cmd)`                | znovu načte seznam (dynamické zdroje)                           |
| `reload-sync(cmd)`           | reload bez probliknutí                                          |
| `change-prompt(text)`        | změní prompt – pro „režimy“                                     |
| `change-preview(cmd)`        | změní příkaz náhledu                                            |
| `change-preview-window(a\|b\|c)` | cykluje rozvržení náhledu                                   |
| `transform(cmd)`             | výstup příkazu se interpretuje jako akce → podmíněná logika     |
| `transform-query(cmd)`       | nastaví dotaz podle výstupu příkazu                             |
| `search(str)`                | spustí hledání bez změny textu v promptu                        |
| `toggle-preview`, `toggle-sort`, `toggle-all`, `select-all`, `deselect-all` | přepínače |
| `first`, `last`, `jump`      | skoky (`jump` = EasyMotion styl štítků)                         |
| `put(text)`                  | vloží text do dotazu                                            |

### Události (místo kláves)

`start`, `load`, `change` (změna dotazu), `focus` (změna vybraného řádku), `result`, `one` (zbyl jen 1 výsledek), `zero` (žádný), `resize`.

```zsh
# Když zbyde jediný výsledek, rovnou ho vyber
fzf --bind 'one:accept'
```

### Placeholdery

| Placeholder | Význam                                              |
|-------------|-----------------------------------------------------|
| `{}`        | aktuální řádek (automaticky citovaný)               |
| `{+}`       | všechny označené řádky                              |
| `{q}`       | aktuální dotaz                                      |
| `{1}`, `{2..}`, `{-1}` | pole dle `--delimiter`                   |
| `{n}`       | index řádku (od 0)                                  |
| `{f}`       | cesta k dočasnému souboru s řádkem (pro velké výběry) |
| `{r}`       | necitovaná (raw) hodnota                            |

---

## 5. Práce se sloupci: `--delimiter`, `--with-nth`, `--nth`, `--accept-nth`

```zsh
# Zobraz jen 2. sloupec dál, hledej jen v něm, ale vrať 1. sloupec (PID)
ps -eo pid,user,%cpu,cmd --sort=-%cpu \
  | fzf --header-lines=1 --nth=4.. --accept-nth=1 -m \
  | xargs -r kill
```

- `--with-nth` – co se **zobrazí**
- `--nth` – v čem se **hledá**
- `--accept-nth` – co se **vrátí** na stdout (od 0.60, šetří `awk`/`cut`)
- `--header-lines=N` – první N řádků vstupu je hlavička (nehledá se v ní)

---

## 6. Hotové funkce – zkopíruj do `~/.funkce/funkce`

### 6.1 Interaktivní ripgrep (live grep jako v IDE)

Hledá **rg** při každém stisku klávesy, fzf jen zobrazuje. `Enter` otevře soubor v nvim na správném řádku.

```zsh
rgl() {
  local RG="rg --column --line-number --no-heading --color=always --smart-case"
  fzf --ansi --disabled --query "${*:-}" \
      --bind "start:reload:$RG {q} || true" \
      --bind "change:reload:sleep 0.1; $RG {q} || true" \
      --delimiter : \
      --preview 'bat --color=always {1} --highlight-line {2}' \
      --preview-window 'up,60%,border-bottom,+{2}+3/3,~3' \
      --bind 'enter:become(nvim {1} +{2})'
}
```

### 6.2 Ripgrep ↔ fzf přepínání režimů (Ctrl-T)

Nejdřív hrubě hledáš ripgrepem, pak `Ctrl-T` → fuzzy filtruješ ve výsledcích.

```zsh
rgl2() {
  local RG="rg --column --line-number --no-heading --color=always --smart-case"
  fzf --ansi --disabled --query "${*:-}" \
      --bind "start:reload($RG {q} || true)+unbind(ctrl-r)" \
      --bind "change:reload:sleep 0.1; $RG {q} || true" \
      --bind "ctrl-f:unbind(change,ctrl-f)+change-prompt(fzf> )+enable-search+rebind(ctrl-r)+transform-query(echo {q} > /tmp/rg-fzf-r; cat /tmp/rg-fzf-f 2>/dev/null)" \
      --bind "ctrl-r:unbind(ctrl-r)+change-prompt(rg> )+disable-search+reload($RG {q} || true)+rebind(change,ctrl-f)+transform-query(echo {q} > /tmp/rg-fzf-f; cat /tmp/rg-fzf-r)" \
      --prompt 'rg> ' --delimiter : \
      --header 'Ctrl-R: ripgrep | Ctrl-F: fzf' \
      --preview 'bat --color=always {1} --highlight-line {2}' \
      --preview-window 'up,60%,border-bottom,+{2}+3/3,~3' \
      --bind 'enter:become(nvim {1} +{2})'
}
```

### 6.3 Najdi soubor a otevři ho

```zsh
fe() {
  fd --type f --hidden --exclude .git | fzf -m \
    --preview 'bat -n --color=always {}' \
    --bind 'enter:become(nvim {+})' \
    --bind 'ctrl-o:execute(xdg-open {} &>/dev/null &)'
}
```

### 6.4 Přepínání mezi soubory / adresáři v jednom okně

```zsh
fdf() {
  fd --type f | fzf --prompt 'Soubory> ' \
    --header 'Ctrl-D: adresáře | Ctrl-F: soubory' \
    --bind 'ctrl-d:change-prompt(Adresáře> )+reload(fd --type d)' \
    --bind 'ctrl-f:change-prompt(Soubory> )+reload(fd --type f)' \
    --preview '[[ -d {} ]] && eza --tree --level=2 --color=always {} || bat --color=always {}'
}
```

### 6.5 zoxide + fzf

```zsh
zf() {
  local dir
  dir=$(zoxide query -l | fzf --scheme=path --no-sort \
        --preview 'eza -la --color=always --icons {}') && cd "$dir"
}
```

(zoxide má i vestavěné `zi`, které fzf používá.)

### 6.6 Git

```zsh
# Přepnutí větve s náhledem logu
gco() {
  git branch -a --color=always | grep -v '/HEAD\s' | fzf --ansi --no-multi \
    --preview 'git log --oneline --graph --date=short --color=always \
               $(sed s/^..// <<< {} | cut -d" " -f1) | head -50' \
  | sed 's/^..//' | cut -d' ' -f1 | sed 's#^remotes/[^/]*/##' \
  | xargs -r git switch
}

# Prohlížeč commitů s delta náhledem; Enter = celý diff
glf() {
  git log --color=always --format='%C(auto)%h%d %s %C(green)%cr %C(blue)%an' |
  fzf --ansi --no-sort --reverse \
      --preview 'git show --color=always {1} | delta' \
      --bind 'enter:execute(git show --color=always {1} | delta --paging=always)' \
      --bind 'ctrl-y:execute-silent(echo -n {1} | wl-copy)+abort'
}

# Interaktivní git add
gaf() {
  git -c color.status=always status --short | fzf --ansi -m --nth 2.. \
    --preview 'git diff --color=always -- {-1} | delta' \
    --accept-nth -1 | xargs -r git add --
}
```

> Pro git existuje i hotový projekt **junegunn/fzf-git.sh** (Ctrl-G Ctrl-F soubory, Ctrl-G Ctrl-B větve, Ctrl-G Ctrl-H commity…). Stojí za vyzkoušení.

### 6.7 Procesy (s live reloadem)

```zsh
fkill() {
  (date; ps -ef) | fzf -m --header-lines=2 \
    --header 'Ctrl-R: obnovit' \
    --bind 'ctrl-r:reload(date; ps -ef)' \
    --preview 'echo {}' --preview-window down,3,wrap \
    --accept-nth 2 | xargs -r kill -"${1:-15}"
}
```

### 6.8 Pacman / yay

```zsh
# Instalace z repozitářů
pin() {
  pacman -Slq | fzf -m --preview 'pacman -Si {}' --preview-window right,60% \
    | xargs -ro sudo pacman -S
}
# Instalace z AUR
yin() {
  yay -Slq | fzf -m --preview 'yay -Si {}' | xargs -ro yay -S
}
# Odinstalace (náhled: info + soubory)
prm() {
  pacman -Qq | fzf -m --preview 'pacman -Qil {}' | xargs -ro sudo pacman -Rns
}
```

### 6.9 systemd služby

```zsh
fsys() {
  systemctl list-units --type=service --all --no-legend --plain \
  | fzf --accept-nth 1 \
      --preview 'SYSTEMD_COLORS=1 systemctl status {1}' \
      --bind 'ctrl-r:execute(sudo systemctl restart {1})+refresh-preview' \
      --bind 'ctrl-l:execute(journalctl -u {1} -e)' \
      --header 'Ctrl-R: restart | Ctrl-L: journal'
}
```

### 6.10 Man stránky, env proměnné, aliasy

```zsh
fman() {
  man -k . | fzf --preview 'man {1} 2>/dev/null | col -bx | bat -l man -p --color=always' \
    --accept-nth 1 | xargs -r man
}

fenv() { env | sort | fzf --delimiter = --preview 'echo {2..}' --preview-window down,3,wrap }

# Lepší verze tvého aliasu `alg` – vrátí jen název aliasu do příkazové řádky
falias() {
  local a=$(alias | fzf --delimiter = --accept-nth 1)
  [[ -n $a ]] && print -z -- "$a "
}
```

> `print -z` vloží text do bufferu zsh – příkaz nevykoná, jen připraví k editaci. Skvělé i pro tvůj `pprf` (soubor použitých příkazů):
>
> ```zsh
> pprf() { print -z -- "$(fzf --tac --no-sort < ~/Documents/Soubory/pouzite_prikazy)" }
> ```

### 6.11 Widget na klávesu (ZLE)

Libovolnou funkci můžeš navázat na zkratku, výsledek se vloží na pozici kurzoru:

```zsh
fzf-git-branch-widget() {
  local b=$(git branch --format='%(refname:short)' 2>/dev/null | fzf --height 40%)
  LBUFFER+="$b"
  zle reset-prompt
}
zle -N fzf-git-branch-widget
bindkey '^g^b' fzf-git-branch-widget   # Ctrl-G Ctrl-B
```

---

## 7. Vzhled a rozložení

```zsh
fzf --style=full                # moderní vzhled (rámečky pro input/list/preview)
fzf --style=minimal             # minimalistický
fzf --tmux center,80%           # otevře se jako tmux popup (mimo tmux normálně)
fzf --height=~50%               # ~ = adaptivní výška (menší seznam → menší okno)
fzf --layout=reverse            # prompt nahoře
fzf --border-label=' Soubory ' --preview-label=' Náhled '
fzf --footer 'Enter: otevřít'   # patička (od 0.63)
fzf --raw                       # neshodné řádky se zobrazí ztlumeně (od 0.66)
fzf --ghost 'Hledej…'           # placeholder v prázdném promptu
fzf --gap                       # mezera mezi položkami (dobré pro víceřádkové)
fzf --read0 --gap               # víceřádkové položky oddělené \0
```

### Barevné schéma (příklad – Catppuccin Mocha)

```zsh
export FZF_DEFAULT_OPTS="$FZF_DEFAULT_OPTS
  --color=bg+:#313244,bg:-1,spinner:#f5e0dc,hl:#f38ba8
  --color=fg:#cdd6f4,header:#f38ba8,info:#cba6f7,pointer:#f5e0dc
  --color=marker:#b4befe,fg+:#cdd6f4,prompt:#cba6f7,hl+:#f38ba8
  --color=selected-bg:#45475a,border:#6c7086,label:#cdd6f4"
```

`bg:-1` = průhledné pozadí terminálu.

### Responzivní preview

```zsh
# Na úzkém terminálu dej náhled dolů, jinak doprava
--preview-window 'right,50%,<80(down,40%)'
```

---

## 8. fzf-tab tipy (máš ho nainstalovaný)

```zsh
# Náhled adresáře při cd <Tab>
zstyle ':fzf-tab:complete:cd:*' fzf-preview 'eza -1 --color=always --icons $realpath'
# Náhled souborů pro nvim/bat/cat
zstyle ':fzf-tab:complete:(nvim|vim|bat|cat|less):*' fzf-preview \
  '[[ -d $realpath ]] && eza -1 --color=always $realpath || bat --color=always -n --line-range :200 $realpath'
# Procesy pro kill
zstyle ':completion:*:*:*:*:processes' command 'ps -u $USER -o pid,user,comm -w -w'
zstyle ':fzf-tab:complete:(kill|ps):argument-rest' fzf-preview \
  '[[ $group == "[process ID]" ]] && ps --pid=$word -o cmd --no-headers -w -w'
zstyle ':fzf-tab:complete:(kill|ps):argument-rest' fzf-flags --preview-window=down:3:wrap
# systemctl
zstyle ':fzf-tab:complete:systemctl-*:*' fzf-preview 'SYSTEMD_COLORS=1 systemctl status $word'
# Proměnné prostředí
zstyle ':fzf-tab:complete:(-command-|-parameter-|-brace-parameter-|export|unset|expand):*' \
  fzf-preview 'echo ${(P)word}'
# git
zstyle ':fzf-tab:complete:git-(add|diff|restore):*' fzf-preview 'git diff $word | delta'
zstyle ':fzf-tab:complete:git-log:*' fzf-preview 'git log --color=always $word'
zstyle ':fzf-tab:complete:git-checkout:*' fzf-preview \
  'case $group in "modified file") git diff $word | delta ;; *) git log --color=always $word ;; esac'
# Popup v tmuxu
zstyle ':fzf-tab:*' fzf-command ftb-tmux-popup
# Použij výchozí FZF_DEFAULT_OPTS i ve fzf-tab
zstyle ':fzf-tab:*' use-fzf-default-opts yes
```

---

## 9. Pokročilé triky

### Ovládání běžícího fzf zvenku (`--listen`)

```zsh
fzf --listen 6266
# z jiného terminálu:
curl -XPOST localhost:6266 -d 'reload(ls)+change-prompt(nový> )'
```

### Podmíněná logika přes `transform`

```zsh
# Enter: na adresáři se do něj „zanoř“, na souboru otevři editor
fd | fzf --bind 'enter:transform:[[ -d {} ]] \
  && echo "reload(fd . {})+change-prompt({}> )" \
  || echo "become(nvim {})"'
```

### Výběr s výstupem více klíčů (`--expect`)

```zsh
out=$(fd --type f | fzf --expect=ctrl-v,ctrl-x)
key=$(head -1 <<< "$out"); file=$(tail -n +2 <<< "$out")
case $key in
  ctrl-v) nvim -O "$file" ;;   # vertikální split
  ctrl-x) xdg-open "$file" ;;
  *)      nvim "$file" ;;
esac
```

(Dnes často elegantněji přes `--bind 'ctrl-v:become(...)'`.)

### Filtr bez UI (skriptování)

```zsh
fd | fzf --filter 'config .toml$'   # vypíše shody a skončí – jako chytrý grep
```

### Náhled obrázků

`fzf` umí v preview zobrazit obrázky (kitty / sixel / iTerm2 protokol). Použij přibalený skript:

```zsh
fzf --preview '/usr/share/fzf/fzf-preview.sh {}'
```

Funguje v kitty, WezTerm, Ghostty, foot (sixel) – jinak spadne na `chafa`.

### Rychlost na obřích vstupech

- `--no-sort` u už seřazených dat (historie, log).
- `--algo=v1` – rychlejší, méně přesný algoritmus.
- Zdroj omez rovnou ve `fd` (`--exclude`, `--max-depth`) místo filtrování ve fzf.
- `--walker-skip` u vestavěného walkeru (když není `FZF_DEFAULT_COMMAND`).

---

## 10. Taháky na závěr

| Chci…                                 | Příkaz / zkratka                         |
|---------------------------------------|------------------------------------------|
| Vložit soubor do příkazu              | `Ctrl-T`                                 |
| cd do podadresáře                     | `Alt-C`                                  |
| Hledat v historii                     | `Ctrl-R` (znovu `Ctrl-R` = přepnutí řazení) |
| Live grep v projektu                  | `rgl`                                    |
| Otevřít soubor(y)                     | `fe`                                     |
| Skočit do častého adresáře            | `zi` / `zf`                              |
| Přepnout git větev                    | `gco`                                    |
| Prohlížet commity                     | `glf`                                    |
| Zabít proces                          | `fkill`                                  |
| Instalovat / odebrat balík            | `pin` / `yin` / `prm`                    |
| Spravovat služby                      | `fsys`                                   |

### Zdroje

- `man fzf` – úplný seznam akcí, událostí a voleb (pro tvou verzi 0.75)
- https://github.com/junegunn/fzf/blob/master/ADVANCED.md – pokročilé příklady od autora
- https://github.com/junegunn/fzf/wiki/examples – stovky hotových funkcí
- https://github.com/junegunn/fzf-git.sh – git integrace
- https://github.com/Aloxaf/fzf-tab/wiki – konfigurace fzf-tab
