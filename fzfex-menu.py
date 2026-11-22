#!/usr/bin/env python3
"""Průhledná nabídka pro fzfex („Otevřít v…“) ve stylu slovicka-view.py / poznámek pozt.

Vstup (stdin, JSON): {"title": "...", "subtitle": "...", "items": [{"label": "...", "detail": "..."}]}
Výstup: index zvolené položky na stdout a návratový kód 0; zrušení = kód 1; bez GTK4 = kód 2.

Ovládání: ↑/↓ (k/j, Tab) výběr · Enter otevřít · 1–9 a 0 přímo · Esc/q zpět ·
          = / - zoom · klik na položku = otevřít · tažení mimo položky = přesun okna.
Proměnné: FZFEX_MENU_STYL (0–9, výchozí 0), FZFEX_MENU_ALFA (hex 00–ff, výchozí POZNAMKA_ALFA
nebo d0), FZFEX_MENU_ZOOM (výchozí 1).
"""
import json
import locale
import os
import subprocess
import sys

try:
    locale.setlocale(locale.LC_ALL, "")
except locale.Error:
    os.environ["LC_ALL"] = "C.UTF-8"
    locale.setlocale(locale.LC_ALL, "C.UTF-8")

# Vykreslovat jen na integrovaném AMD GPU (jako slovicka-view.py)
os.environ.setdefault("VK_DRIVER_FILES", "/usr/share/vulkan/icd.d/radeon_icd.json")
os.environ.setdefault("__EGL_VENDOR_LIBRARY_FILENAMES", "/usr/share/glvnd/egl_vendor.d/50_mesa.json")

try:
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Gdk", "4.0")
    gi.require_version("Pango", "1.0")
    gi.require_version("PangoCairo", "1.0")
    from gi.repository import Gdk, Gio, GLib, Gtk, Pango, PangoCairo
except (ImportError, ValueError):
    sys.exit(2)

CSS = b"window, window.background { background: transparent; box-shadow: none; }"
KROK = 1.2

# Styly 0–9 jako ve slovicka-view.py: pozadí, text, zvýraznění, detail, font
STYLY = {
    0: ("#071e22", "#f4c095", "#ffd166", "#7fd1c7", "monospace"),
    1: ("#fff176", "#3e2723", "#bf360c", "#1b5e20", "Sans"),
    2: ("#5A0E24", "#f4c095", "#ffd166", "#f7a8b8", "monospace"),
    3: ("#001F3D", "#cfe3ff", "#ffd166", "#7fdbff", "JetBrainsMono NF"),
    4: ("#2e3440", "#a3be8c", "#ebcb8b", "#88c0d0", "JetBrainsMono NF Light"),
    5: ("#f5ecd7", "#3b2f2f", "#8b1e1e", "#2e5e4e", "DejaVu Serif"),
    6: ("#c8f7dc", "#1b4332", "#9d0208", "#1d3557", "Sans"),
    7: ("#ffb3c7", "#4a0e2e", "#7b002c", "#3d0066", "Sans"),
    8: ("#b71c1c", "#ffffff", "#ffeb3b", "#ffe0b2", "Sans"),
    9: ("#111111", "#fafafa", "#ffd54f", "#80deea", "AtkynsonMono NF"),
}
NAPOVEDA = "↑↓ výběr · Enter otevřít · 1–9 přímo · Esc zpět"


def esc(text):
    return GLib.markup_escape_text(text or "")


def rgb(hex_barva):
    h = hex_barva.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def niri_json(*args):
    try:
        out = subprocess.run(["niri", "msg", "--json", *args], capture_output=True, text=True)
        return json.loads(out.stdout) if out.returncode == 0 and out.stdout.strip() else None
    except (OSError, ValueError):
        return None


def niri_action(*args):
    try:
        subprocess.run(["niri", "msg", "action", *map(str, args)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        pass


class Nabidka(Gtk.ApplicationWindow):
    def __init__(self, app, data, vysledek):
        super().__init__(application=app, decorated=False, resizable=False)
        self.set_title("fzfex – " + (data.get("title") or "nabídka"))
        self.titulek = data.get("title") or ""
        self.podtitulek = data.get("subtitle") or ""
        self.polozky = data.get("items") or []
        self.vysledek = vysledek
        self.vyber = 0
        self.radky = []                     # [(y0, y1)] položek pro myš
        styl = int(os.environ.get("FZFEX_MENU_STYL", "0") or 0)
        self.bg, self.fg, self.akcent, self.detail, self.font = STYLY.get(styl, STYLY[0])
        alfa = os.environ.get("FZFEX_MENU_ALFA") or os.environ.get("POZNAMKA_ALFA") or "d0"
        self.alfa = int(alfa, 16) / 255
        self.zoom = float(os.environ.get("FZFEX_MENU_ZOOM", "1") or 1)

        self.plocha = Gtk.DrawingArea()
        self.plocha.set_draw_func(self.kresli)
        self.set_child(self.plocha)

        klavesy = Gtk.EventControllerKey()
        klavesy.connect("key-pressed", self.klavesa)
        self.add_controller(klavesy)
        klik = Gtk.GestureClick()
        klik.connect("pressed", self.klik)
        self.plocha.add_controller(klik)
        pohyb = Gtk.EventControllerMotion()
        pohyb.connect("motion", self.najeti)
        self.plocha.add_controller(pohyb)

        self.prekresli()
        self.pokusu = 0
        if os.environ.get("NIRI_SOCKET"):
            GLib.timeout_add(60, self.umisti)

    # ── Rozměry a texty ─────────────────────────────────────────
    def pt(self, body):
        return f'size="{round(body * 1024 * self.zoom)}"'

    def okraj(self):
        return round(26 * self.zoom)

    def layout(self, markup):
        lay = self.plocha.create_pango_layout(None)
        lay.set_font_description(Pango.FontDescription.from_string(self.font))
        lay.set_markup(markup, -1)
        return lay

    def hlavicka(self):
        m = f'<span {self.pt(17)} weight="bold" foreground="{self.akcent}">{esc(self.titulek)}</span>'
        if self.podtitulek:
            m += f'\n<span {self.pt(10)} alpha="65%">{esc(self.podtitulek)}</span>'
        return self.layout(m)

    def radek(self, i):
        p = self.polozky[i]
        cislo = str((i + 1) % 10) if i < 10 else " "
        barva = f' foreground="{self.akcent}" weight="bold"' if i == self.vyber else ""
        m = (f'<span {self.pt(10)} alpha="55%">{cislo}</span>  '
             f'<span {self.pt(13)}{barva}>{esc(p.get("label"))}</span>')
        if p.get("detail"):
            m += f'   <span {self.pt(10)} foreground="{self.detail}" alpha="80%">{esc(p["detail"])}</span>'
        return self.layout(m)

    def pata(self):
        return self.layout(f'<span {self.pt(9)} alpha="55%">{esc(NAPOVEDA)}</span>')

    def rozmery(self):
        m = self.okraj()
        mezera = round(6 * self.zoom)
        hl, pa = self.hlavicka(), self.pata()
        rady = [self.radek(i) for i in range(len(self.polozky))]
        sirka = max([hl.get_pixel_size()[0], pa.get_pixel_size()[0]]
                    + [r.get_pixel_size()[0] for r in rady]) + 2 * m + round(24 * self.zoom)
        sirka = max(sirka, round(420 * self.zoom))
        y = m + hl.get_pixel_size()[1] + round(16 * self.zoom)
        self.radky = []
        for r in rady:
            h = r.get_pixel_size()[1] + 2 * mezera
            self.radky.append((y, y + h))
            y += h
        vyska = y + round(14 * self.zoom) + pa.get_pixel_size()[1] + m
        return sirka, vyska, hl, rady, pa

    def prekresli(self):
        sirka, vyska, *_ = self.rozmery()
        self.plocha.set_content_width(sirka)
        self.plocha.set_content_height(vyska)
        self.plocha.queue_draw()

    def kresli(self, _plocha, cr, sirka, vyska):
        _, _, hl, rady, pa = self.rozmery()
        r, g, b = rgb(self.bg)
        cr.set_source_rgba(r, g, b, self.alfa)
        cr.paint()
        m = self.okraj()
        fr, fg, fb = rgb(self.fg)
        cr.set_source_rgb(fr, fg, fb)
        cr.move_to(m, m)
        PangoCairo.show_layout(cr, hl)
        for i, (lay, (y0, y1)) in enumerate(zip(rady, self.radky)):
            if i == self.vyber:                            # zvýrazněný řádek
                ar, ag, ab = rgb(self.akcent)
                cr.set_source_rgba(ar, ag, ab, 0.16)
                cr.rectangle(m - round(10 * self.zoom), y0, sirka - 2 * m + round(20 * self.zoom), y1 - y0)
                cr.fill()
                cr.set_source_rgba(ar, ag, ab, 0.9)
                cr.rectangle(m - round(10 * self.zoom), y0, round(3 * self.zoom), y1 - y0)
                cr.fill()
            cr.set_source_rgb(fr, fg, fb)
            cr.move_to(m, y0 + (y1 - y0 - lay.get_pixel_size()[1]) / 2)
            PangoCairo.show_layout(cr, lay)
        cr.set_source_rgb(fr, fg, fb)
        cr.move_to(m, vyska - m - pa.get_pixel_size()[1])
        PangoCairo.show_layout(cr, pa)

    # ── Umístění v niri: plovoucí, na střed monitoru ────────────
    def umisti(self):
        self.pokusu += 1
        okno = next((w for w in niri_json("windows") or [] if w.get("pid") == os.getpid()), None)
        if not okno:
            return self.pokusu < 30                        # zkoušet ~2 s
        if not okno.get("is_floating"):
            niri_action("move-window-to-floating", "--id", okno["id"])
        ws_out = {w["id"]: w["output"] for w in niri_json("workspaces") or []}
        vystup = (niri_json("outputs") or {}).get(ws_out.get(okno["workspace_id"]), {})
        lo = vystup.get("logical") or {}
        sirka, vyska, *_ = self.rozmery()
        if lo:
            x = max(0, (lo["width"] - sirka) // 2)
            y = max(0, (lo["height"] - vyska) // 3)
            niri_action("move-floating-window", "--id", okno["id"], "-x", x, "-y", y)
        niri_action("focus-window", "--id", okno["id"])
        return False

    # ── Ovládání ────────────────────────────────────────────────
    def potvrd(self, i):
        if 0 <= i < len(self.polozky):
            self.vysledek.append(i)
            self.get_application().quit()

    def posun(self, o):
        if self.polozky:
            self.vyber = (self.vyber + o) % len(self.polozky)
            self.prekresli()

    def klavesa(self, _ctl, keyval, _code, stav):
        k = Gdk.keyval_name(keyval) or ""
        ctrl = bool(stav & Gdk.ModifierType.CONTROL_MASK)
        if k in ("Escape", "q", "Q") or (ctrl and k in ("c", "g")):
            self.get_application().quit()
        elif k in ("Return", "KP_Enter", "space", "l", "Right"):
            self.potvrd(self.vyber)
        elif k in ("Down", "j", "Tab", "KP_Down") or (ctrl and k in ("n", "j")):
            self.posun(1)
        elif k in ("Up", "k", "ISO_Left_Tab", "KP_Up") or (ctrl and k in ("p", "k")):
            self.posun(-1)
        elif k in ("Home", "g"):
            self.vyber = 0
            self.prekresli()
        elif k in ("End", "G"):
            self.vyber = max(0, len(self.polozky) - 1)
            self.prekresli()
        elif k.isdigit() or (k.startswith("KP_") and k[3:].isdigit()):
            n = int(k[-1])
            self.potvrd(9 if n == 0 else n - 1)
        elif k in ("equal", "plus", "KP_Add"):
            self.zoom *= KROK
            self.prekresli()
        elif k in ("minus", "KP_Subtract"):
            self.zoom /= KROK
            self.prekresli()
        else:
            return False
        return True

    def index_na(self, y):
        return next((i for i, (y0, y1) in enumerate(self.radky) if y0 <= y < y1), None)

    def najeti(self, _ctl, _x, y):
        i = self.index_na(y)
        if i is not None and i != self.vyber:
            self.vyber = i
            self.prekresli()

    def klik(self, gesto, _n, x, y):
        i = self.index_na(y)
        if i is not None:
            self.potvrd(i)
            return
        povrch = self.get_surface()
        if isinstance(povrch, Gdk.Toplevel):
            povrch.begin_move(gesto.get_device(), gesto.get_current_button(), x, y,
                              gesto.get_current_event_time())


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 1
    if not data.get("items"):
        return 1
    vysledek = []
    app = Gtk.Application(application_id="cz.fzfex.menu", flags=Gio.ApplicationFlags.NON_UNIQUE)

    def start(app):
        css = Gtk.CssProvider()
        css.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        Nabidka(app, data, vysledek).present()

    app.connect("activate", start)
    app.run([sys.argv[0]])
    if vysledek:
        print(vysledek[0])
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
