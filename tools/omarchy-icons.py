#!/usr/bin/env python3
"""Extract the panel icons from Omarchy's bar glyphs, as symbolic SVGs.

    python3 tools/omarchy-icons.py SymbolsNerdFont-Regular.ttf [FONTTOOLS_DIR]

Omarchy (github.com/omacom/omarchy, shell/) draws its bar icons as Nerd Font
glyphs. Here every status icon gets the same ink height: 10.5 of a 16px
canvas, centered by ink. That's the glyphs' own proportion in the font:
the Material Design and Font Awesome glyphs share a height of about 0.8em,
with wide ones simply wider. At the panel's 13px font that's 10.5px, level
with the digits. Fitting the longest side instead (Omarchy's current
OpticalGlyph) shrinks wide icons: the volume icon came out 2/3 the height
of the battery. Icons wider than the canvas allows are fit to its width.

The active-workspace square is the exception. The workspaces plugin draws
it at the font's pixel size, so it keeps the font's own fit: the glyph is
0.75em, so its longest side is 12 of 16.

The font is SymbolsNerdFont-Regular.ttf from the Nerd Fonts release
(NerdFontsSymbolsOnly). Its glyphs are the same artwork as Omarchy's
JetBrainsMono Nerd Font, and the fit makes the font's own scale irrelevant.
FONTTOOLS_DIR is an unpacked fontTools wheel, if fontTools isn't installed.

Writes icons/*.svg (the panel switch, installed to hicolor) and
icons/theme/*.svg (copied into the Equinox icon theme by build.py).
"""

import sys
from pathlib import Path

CANVAS = 16
HEIGHT = 10.5     # ink height of every status icon, in canvas units
MAX_WIDTH = 15.5  # wide icons are fit to the canvas
BOX = 12          # longest side, for icons drawn at the font's size
FIT_BOX = {"equinox-workspace-active-symbolic"}

# file stem: (codepoint, where Omarchy uses it)
ICONS = {
    # Light/dark switch: Omarchy's clear-sky weather glyphs.
    "equinox-light-symbolic": (0xE30D, "weather panel, clear sky by day"),
    "equinox-dark-symbolic": (0xE32B, "weather panel, clear sky at night"),
    # Workspaces plugin: Omarchy's mark for the active workspace.
    "equinox-workspace-active-symbolic": (0xF14FB, "workspaces, the active one"),
    # nm-applet (indicator mode): Omarchy's network panel.
    "theme/nm-signal-00-symbolic": (0xF092F, "network panel, wifi 0 bars"),
    "theme/nm-signal-25-symbolic": (0xF091F, "network panel, wifi 1 bar"),
    "theme/nm-signal-50-symbolic": (0xF0922, "network panel, wifi 2 bars"),
    "theme/nm-signal-75-symbolic": (0xF0925, "network panel, wifi 3 bars"),
    "theme/nm-signal-100-symbolic": (0xF0928, "network panel, wifi 4 bars"),
    "theme/nm-no-connection-symbolic": (0xF092E, "network panel, disconnected"),
    "theme/nm-device-wired-symbolic": (0xF0200, "network panel, ethernet"),
    # xfce4-pulseaudio-plugin: Omarchy's audio panel and OSD.
    "theme/audio-volume-muted-symbolic": (0xEEE8, "audio panel, muted"),
    "theme/audio-volume-low-symbolic": (0xF026, "audio panel, volume > 0"),
    "theme/audio-volume-medium-symbolic": (0xF027, "audio panel, volume >= 34%"),
    "theme/audio-volume-high-symbolic": (0xF028, "audio panel, volume >= 67%"),
    "theme/microphone-sensitivity-high-symbolic": (0xF036C, "microphone widget"),
    "theme/microphone-sensitivity-medium-symbolic": (0xF036C, "microphone widget"),
    "theme/microphone-sensitivity-low-symbolic": (0xF036C, "microphone widget"),
    "theme/microphone-sensitivity-muted-symbolic": (0xF036D, "microphone widget, muted"),
    # Reboot required: Omarchy's OSD reboot glyph.
    "theme/system-reboot-symbolic": (0xF0709, "OSD, reboot"),
    # xfce4-power-manager's panel plugin, see below.
    "theme/battery-level-100-charged-symbolic": (0xF0085, "power panel, fully charged"),
}

# Battery: Omarchy's power panel (panels/power/Model.js) picks one of ten
# glyphs by floor(percentage * 10), capped at 9. xfce4-power-manager asks
# for battery-level-{0,10,...,100}[-charging]-symbolic, so level L gets
# glyph min(L / 10, 9): md-battery_10 ... md-battery, md-battery_charging_10
# ... md-battery_charging_100.
DISCHARGING = [0xF007A, 0xF007B, 0xF007C, 0xF007D, 0xF007E, 0xF007F, 0xF0080, 0xF0081, 0xF0082, 0xF0079]
CHARGING = [0xF089C, 0xF0086, 0xF0087, 0xF0088, 0xF089D, 0xF0089, 0xF089E, 0xF008A, 0xF008B, 0xF0085]
for level in range(0, 101, 10):
    i = min(level // 10, 9)
    ICONS[f"theme/battery-level-{level}-symbolic"] = (DISCHARGING[i], f"power panel, {level}%")
    ICONS[f"theme/battery-level-{level}-charging-symbolic"] = (CHARGING[i], f"power panel, {level}% charging")


def main():
    if len(sys.argv) > 2:
        sys.path.insert(0, sys.argv[2])
    from fontTools.pens.boundsPen import BoundsPen
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.ttLib import TTFont

    font = TTFont(sys.argv[1])
    cmap = font.getBestCmap()
    glyphs = font.getGlyphSet()
    out = Path(__file__).resolve().parent.parent / "icons"
    (out / "theme").mkdir(parents=True, exist_ok=True)

    for stem, (codepoint, _) in ICONS.items():
        name = cmap[codepoint]
        bounds = BoundsPen(glyphs)
        glyphs[name].draw(bounds)
        x0, y0, x1, y1 = bounds.bounds
        if stem in FIT_BOX:
            scale = BOX / max(x1 - x0, y1 - y0)
        else:
            scale = min(HEIGHT / (y1 - y0), MAX_WIDTH / (x1 - x0))
        # Font units are y-up; center the ink box in the canvas, y-down.
        dx = CANVAS / 2 - (x0 + x1) / 2 * scale
        dy = CANVAS / 2 + (y0 + y1) / 2 * scale
        pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.3f}".rstrip("0").rstrip("."))
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, dx, dy)))
        (out / f"{stem}.svg").write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS}" height="{CANVAS}" '
            f'viewBox="0 0 {CANVAS} {CANVAS}">\n'
            f'<!-- Omarchy bar glyph {name} (U+{codepoint:04X}), Nerd Fonts. See icons/README.md. -->\n'
            f'<path fill="#2e3436" d="{pen.getCommands()}"/>\n</svg>\n')
        print(f"{stem:45} U+{codepoint:04X} {name}")


if __name__ == "__main__":
    main()
