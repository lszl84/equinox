#!/usr/bin/env python3
"""Build the Equinox GTK3 and xfwm4 themes from palettes/*.toml.

Writes build/themes/:

  Equinox/              GTK3 light (its gtk-dark.css is the dark variant)
                        and xfwm4 at 1x
  Equinox-dark/         GTK3 dark and xfwm4 at 1x
  Equinox-hdpi/         xfwm4 at 1.5x, and Equinox-dark-hdpi
  Equinox-xhdpi/        xfwm4 at 2x, and Equinox-dark-xhdpi

and build/icons/Equinox/, an icon theme that inherits Adwaita and swaps in
Omarchy's bar icons for the panel: wifi, volume, microphone and reboot.

xfwm4 doesn't scale its themes, so the window scaling factor picks the
variant: Equinox-xhdpi for 2x. equinox-mode does that automatically.

Needs Python 3.11+ (tomllib) and rsvg-convert (librsvg2-bin).
"""

import shutil
import subprocess
import sys
import tomllib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

NAME = "Equinox"  # Codename. The final name only needs changing here,
                  # in bin/equinox-mode and in the plugin.
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "build" / "themes"
ICONS_OUT = ROOT / "build" / "icons"
SCALES = {"": 1, "-hdpi": 1.5, "-xhdpi": 2}

# xfwm4 frame geometry, in logical pixels (multiplied by the scale).
#
# xfwm4 cuts frames with a 1-bit X Shape mask: a pixel is either frame or
# see-through, never in between. So the rounded top corners work like the
# stock Default theme's: a solid outline (a translucent one would be cut
# away) drawn with hard outer edges, so every pixel of it survives the cut,
# and antialiased only towards the title bar fill.
TITLE_HEIGHT = 34
CORNER_RADIUS = 8  # the GTK theme's window radius, which Firefox follows too
BORDER = 3         # sides and bottom, including the 1px outline

# Window buttons copy Firefox's on Linux (browser.css, .titlebar-button): a
# 16px Adwaita symbolic icon in a 24px circle that only shows on hover
# (15% of the icon color, 30% when pressed), 6.5px of padding on each side
# of a button, and 10px between the last button and the window edge. Each
# button image is just the circle; the padding becomes xfwm4's
# button_spacing, so no button covers a rounded corner.
BUTTON_SIZE = 24
BUTTON_PADDING = 6.5
BUTTON_END_SPACING = 10
ICON_DIR = Path("/usr/share/icons/Adwaita/symbolic")
ICONS = {
    "close": "ui/window-close",
    "maximize": "ui/window-maximize",
    "maximize-toggled": "ui/window-restore",
    "hide": "ui/window-minimize",
    "menu": "actions/view-more-horizontal",
    "shade": "ui/pan-up",
    "shade-toggled": "ui/pan-down",
    "stick": "actions/view-pin",
    "stick-toggled": "actions/view-pin",
}


# ── Colors ───────────────────────────────────────────────────────────────
# Same math as GTK's mix() and alpha(), so the xfwm4 frame matches the
# GTK header bars pixel for pixel.

def parse(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (1.0,)


def mix(a, b, f):
    return tuple(x + (y - x) * f for x, y in zip(a, b))


def alpha(c, f):
    return c[:3] + (c[3] * f,)


def over(top, bottom):
    """Composite a translucent color over an opaque one."""
    a = top[3]
    return tuple(t * a + b * (1 - a) for t, b in zip(top[:3], bottom[:3])) + (1.0,)


def hexc(c):
    return "#" + "".join(f"{round(x * 255):02x}" for x in c[:3])


def svg_fill(c):
    return f'fill="{hexc(c)}"' + (f' fill-opacity="{c[3]:.3f}"' if c[3] < 1 else "")


def luminance(c):
    def ch(v):
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2])


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


BLACK = parse("#000000")
WHITE = parse("#ffffff")


def on_color(surface, bg, fg):
    """Text color for a filled surface: the palette's own background or
    foreground when either reads well (WCAG 4.5:1), else white or black."""
    best, best_ratio = None, 0
    for candidate in (bg, fg, WHITE, BLACK):
        if candidate in (WHITE, BLACK) and best_ratio >= 4.5:
            continue
        ratio = contrast(surface, candidate)
        if ratio > best_ratio:
            best, best_ratio = candidate, ratio
    return best


class Palette:
    def __init__(self, path):
        raw = tomllib.loads(path.read_text())
        self.mode = raw["mode"]
        self.source = path.relative_to(ROOT)
        for key in ("background", "foreground", "accent", "red", "green",
                    "yellow", "blue", "magenta", "cyan"):
            setattr(self, key, parse(raw[key]))
        bg, fg = self.background, self.foreground
        light = self.mode == "light"

        self.extreme = WHITE if light else BLACK
        self.knob = WHITE if light else mix(fg, WHITE, 0.65)
        self.shadow = alpha(BLACK, 0.12 if light else 0.35)
        self.outline = alpha(BLACK, 0.14 if light else 0.5)
        for key in ("accent", "red", "green", "yellow"):
            setattr(self, key + "_fg", on_color(getattr(self, key), bg, fg))

        # Derived exactly like base.css does it.
        self.headerbar = mix(bg, fg, 0.05)
        self.dim = mix(fg, bg, 0.35)
        self.faint = mix(fg, bg, 0.55)
        self.border = over(alpha(fg, 0.12), self.headerbar)
        # xfwm4 can't draw translucent frame pixels, so its outline is the
        # GTK outline flattened onto the title bar color.
        # A little stronger in light mode, where a faint line would vanish
        # against a light wallpaper.
        self.frame_outline = over(alpha(BLACK, 0.2) if light else self.outline, self.headerbar)

    def css(self):
        def rgba(c):
            return f"alpha(black, {c[3]:g})"
        lines = [
            f"/* Equinox {self.mode} palette, generated by build.py from {self.source}. */",
            "",
        ]
        for key in ("bg:background", "fg:foreground", "accent", "accent_fg",
                    "red", "red_fg", "green", "green_fg", "yellow", "yellow_fg",
                    "blue", "magenta", "cyan", "extreme", "knob"):
            name, _, attr = key.partition(":")
            lines.append(f"@define-color eqx_{name} {hexc(getattr(self, attr or name))};")
        lines.append(f"@define-color eqx_shadow {rgba(self.shadow)};")
        lines.append(f"@define-color eqx_outline {rgba(self.outline)};")
        return "\n".join(lines) + "\n\n"


# ── GTK3 ─────────────────────────────────────────────────────────────────

INDEX_THEME = """[Desktop Entry]
Type=X-GNOME-Metatheme
Name={name}
Comment={comment}
Encoding=UTF-8

[X-GNOME-Metatheme]
GtkTheme={name}
"""


def build_gtk(light, dark):
    base = (ROOT / "gtk-3.0" / "base.css").read_text()
    for theme, main, other in ((NAME, light, dark), (f"{NAME}-dark", dark, dark)):
        gtk = OUT / theme / "gtk-3.0"
        gtk.mkdir(parents=True)
        (gtk / "gtk.css").write_text(main.css() + base)
        # Apps that ask for a dark variant (prefer-dark) load gtk-dark.css.
        (gtk / "gtk-dark.css").write_text(other.css() + base)
        (OUT / theme / "index.theme").write_text(INDEX_THEME.format(
            name=theme, comment=f"Modern {main.mode} theme for Xfce"))


# ── xfwm4 ────────────────────────────────────────────────────────────────

def load_icon(name):
    """The inner markup of an Adwaita symbolic icon, with its colors removed
    so the button can fill it."""
    import xml.etree.ElementTree as ET
    path = ICON_DIR / f"{name}-symbolic.svg"
    if not path.exists():
        sys.exit(f"build.py: {path} not found (apt install adwaita-icon-theme)")
    root = ET.parse(path).getroot()
    parts = []
    for el in root.iter():
        if el is root or "d" not in el.attrib and el.tag.split("}")[-1] not in ("rect", "circle", "ellipse"):
            continue
        attrs = {k: v for k, v in el.attrib.items() if k not in ("fill", "style", "class", "fill-opacity")}
        tag = el.tag.split("}")[-1]
        parts.append(f"<{tag} " + " ".join(f'{k}="{v}"' for k, v in attrs.items()) + "/>")
    return "".join(parts)


class Frame:
    """One xfwm4 theme: a palette at one scale."""

    def __init__(self, pal, scale, icons):
        self.p = pal
        self.s = scale
        self.icons = icons
        px = lambda v: max(1, round(v * scale))
        even = lambda v: 2 * round(v * scale / 2)
        # Even sizes keep the icons' centers on whole pixels, so they're crisp.
        self.h = even(TITLE_HEIGHT)
        self.bw = even(BUTTON_SIZE)
        self.r = px(CORNER_RADIUS)
        self.b = px(BORDER)
        self.o = px(1)    # outline
        self.sep = px(1)  # line under the title bar

    def svg(self, w, h, body):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
                f'viewBox="0 0 {w} {h}">{body}</svg>')

    def rect(self, x, y, w, h, color):
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" {svg_fill(color)}/>'

    def mirror(self, w, body):
        return f'<g transform="translate({w} 0) scale(-1 1)">{body}</g>'

    def title_bg(self, w):
        """Title bar strip: outline on top, title bar color, separator."""
        p, h, o, sep = self.p, self.h, self.o, self.sep
        return (self.rect(0, 0, w, h, p.headerbar)
                + self.rect(0, 0, w, o, p.frame_outline)
                + self.rect(0, h - sep, w, sep, p.border))

    def corner_top(self):
        """Rounded top-left corner. The outer shape is drawn without
        antialiasing so the 1-bit cut keeps all of it; the fill on top is
        antialiased against the outline."""
        p, h, r, o, sep = self.p, self.h, self.r, self.o, self.sep
        ri = r - o
        outer = (f'<path d="M0 {h} V{r} A{r} {r} 0 0 1 {r} 0 V{h} Z" '
                 f'shape-rendering="crispEdges" {svg_fill(p.frame_outline)}/>')
        inner = f'<path d="M{o} {h} V{r} A{ri} {ri} 0 0 1 {r} {o} V{h} Z" {svg_fill(p.headerbar)}/>'
        return outer + inner + self.rect(o, h - sep, r - o, sep, p.border)

    def side(self, n=8):
        p, b, o = self.p, self.b, self.o
        return self.rect(0, 0, b, n, p.background) + self.rect(0, 0, o, n, p.frame_outline)

    def bottom(self, n=8):
        p, b, o = self.p, self.b, self.o
        return self.rect(0, 0, n, b, p.background) + self.rect(0, b - o, n, o, p.frame_outline)

    def corner_bottom(self):
        p, b, o = self.p, self.b, self.o
        return (self.rect(0, 0, b, b, p.background)
                + self.rect(0, 0, o, b, p.frame_outline)
                + self.rect(0, b - o, b, o, p.frame_outline))

    def button(self, kind, state):
        p = self.p
        color = p.dim if state == "inactive" else p.foreground
        circle = {"prelight": 0.15, "pressed": 0.30}.get(state)
        # A toggled button (shade, stick) keeps its circle, like a checked toggle.
        if circle is None and kind.endswith("-toggled") and kind != "maximize-toggled":
            circle = 0.15
        cx, cy = self.bw / 2, self.h / 2
        body = self.title_bg(self.bw)
        if circle is not None:
            body += (f'<circle cx="{cx}" cy="{cy}" r="{BUTTON_SIZE * self.s / 2:g}" '
                     f'{svg_fill(alpha(color, circle))}/>')
        k = self.s  # the icons are drawn on a 16px grid
        body += (f'<g fill="{hexc(color)}" transform="translate({cx - 8 * k:g} {cy - 8 * k:g}) '
                 f'scale({k:g})">{self.icons[kind]}</g>')
        return self.svg(self.bw, self.h, body)

    def themerc(self):
        p = self.p
        # xfwm4 starts the buttons button_offset inside the side border. Put
        # the last circle BUTTON_END_SPACING from the window edge, like Firefox,
        # but never over the rounded corner.
        offset = max(round(BUTTON_END_SPACING * self.s) - self.b, self.r - self.b)
        spacing = round(2 * BUTTON_PADDING * self.s)
        return "\n".join([
            f"# {NAME} xfwm4 theme, {p.mode} at {self.s:g}x. Generated by build.py.",
            f"active_text_color={hexc(p.foreground)}",
            f"inactive_text_color={hexc(p.dim)}",
            "title_alignment=center",
            "full_width_title=true",
            "title_shadow_active=false",
            "title_shadow_inactive=false",
            "title_horizontal_offset=0",
            "title_vertical_offset_active=0",
            "title_vertical_offset_inactive=0",
            f"button_offset={offset}",
            f"button_spacing={spacing}",
            "show_app_icon=false",
            "maximized_offset=0",
        ]) + "\n"

    def images(self):
        """Yield (file stem, svg) for every image xfwm4 looks for."""
        tw = max(1, round(4 * self.s))
        h, b = self.h, self.b
        pieces = {
            "top-left": self.svg(self.r, h, self.corner_top()),
            "top-right": self.svg(self.r, h, self.mirror(self.r, self.corner_top())),
            "left": self.svg(b, 8, self.side()),
            "right": self.svg(b, 8, self.mirror(b, self.side())),
            "bottom": self.svg(8, b, self.bottom()),
            "bottom-left": self.svg(b, b, self.corner_bottom()),
            "bottom-right": self.svg(b, b, self.mirror(b, self.corner_bottom())),
        }
        for i in range(1, 6):
            pieces[f"title-{i}"] = self.svg(tw, h, self.title_bg(tw))
        for name, svg in pieces.items():
            for state in ("active", "inactive"):
                yield f"{name}-{state}", svg
        for kind in ICONS:
            for state in ("active", "inactive", "prelight", "pressed"):
                yield f"{kind}-{state}", self.button(kind, state)


# ── Icons ────────────────────────────────────────────────────────────────

ICON_INDEX = """[Icon Theme]
Name={name}
Comment=Adwaita with Omarchy's panel icons
Inherits=Adwaita,hicolor
Directories=scalable/status

[scalable/status]
Size=16
MinSize=8
MaxSize=512
Type=Scalable
Context=Status
"""


def build_icons():
    """The icon theme: icons/theme/*.svg, Omarchy's bar glyphs extracted by
    tools/omarchy-icons.py. nm-applet asks for a -secure variant on secured
    networks; it gets the same icon."""
    status = ICONS_OUT / NAME / "scalable" / "status"
    status.mkdir(parents=True)
    (ICONS_OUT / NAME / "index.theme").write_text(ICON_INDEX.format(name=NAME))
    for svg in sorted((ROOT / "icons" / "theme").glob("*.svg")):
        shutil.copy(svg, status / svg.name)
        if svg.name.startswith("nm-signal-"):
            shutil.copy(svg, status / svg.name.replace("-symbolic", "-secure-symbolic"))


def rasterize(job):
    svg, png = job
    subprocess.run(["rsvg-convert", "-f", "png", "-o", str(png)],
                   input=svg.encode(), check=True)


def build_xfwm4(light, dark):
    icons = {kind: load_icon(name) for kind, name in ICONS.items()}
    jobs = []
    for pal, theme in ((light, NAME), (dark, f"{NAME}-dark")):
        for suffix, scale in SCALES.items():
            frame = Frame(pal, scale, icons)
            xfwm4 = OUT / (theme + suffix) / "xfwm4"
            xfwm4.mkdir(parents=True, exist_ok=True)
            (xfwm4 / "themerc").write_text(frame.themerc())
            jobs += [(svg, xfwm4 / f"{stem}.png") for stem, svg in frame.images()]
    with ThreadPoolExecutor() as pool:
        list(pool.map(rasterize, jobs))
    return len(jobs)


def main():
    if shutil.which("rsvg-convert") is None:
        sys.exit("build.py: rsvg-convert not found (apt install librsvg2-bin)")
    light = Palette(ROOT / "palettes" / "light.toml")
    dark = Palette(ROOT / "palettes" / "dark.toml")
    shutil.rmtree(OUT, ignore_errors=True)
    shutil.rmtree(ICONS_OUT, ignore_errors=True)
    build_gtk(light, dark)
    build_icons()
    count = build_xfwm4(light, dark)
    for pal in (light, dark):
        print(f"{pal.mode:5}  accent {hexc(pal.accent)} text {hexc(pal.accent_fg)} "
              f"({contrast(pal.accent, pal.accent_fg):.1f}:1)  "
              f"red text {hexc(pal.red_fg)} ({contrast(pal.red, pal.red_fg):.1f}:1)")
    print(f"Built {len(list(OUT.iterdir()))} themes ({count} xfwm4 images) in {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
