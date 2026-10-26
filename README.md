# Equinox

> Codename. The final name is still to be decided.

A modern light and dark theme for Xfce on Debian, with a panel button to
switch between them.

- **GTK3 theme** in a light and a dark variant: flat, rounded and
  libadwaita-inspired, based on [Omagtk](https://github.com/lszl84/omagtk).
- **Matching xfwm4 theme**: title bars in the header-bar color, with
  window buttons drawn the way Firefox draws its own (the Adwaita icons,
  and a soft circle only on hover), and rounded top corners at the same
  8px radius as Firefox and the GTK theme. Built at 1x, 1.5x and 2x,
  because xfwm4 doesn't scale its themes.

  xfwm4 cuts frames with a 1-bit mask, so the corners use the stock Default
  theme's technique: a solid outline drawn with hard outer edges, so the cut
  keeps all of it, antialiased only towards the title bar. No theme draws a
  shadow; the only one is the compositor's own, from Window Manager Tweaks.
- **Icon theme** (select **Equinox** in Settings → Appearance → Icons):
  Adwaita, plus nm-applet's wifi icons redrawn as crisp symbolic signal
  bars. nm-applet only ships them as 22x22 bitmaps, which are blurry on a
  HiDPI panel. Run nm-applet with `--indicator`, and turn on the tray's
  "symbolic icons", so the panel draws the bars in its own text color.
- **Light/dark switch** for the Xfce panel: a sun in light mode, a moon in
  dark mode. Click it to switch the GTK theme, the window frames, and the
  color-scheme preference that GTK4/libadwaita apps, Firefox and Chromium
  follow, all at once.

## Requirements

- Xfce 4.20 (Debian 13 "trixie"); GTK 3.24 apps
- To build: `python3`, `rsvg-convert`, the Adwaita icons (for the window
  buttons), a C compiler, `make`, and the Xfce panel headers:

  ```sh
  sudo apt install librsvg2-bin adwaita-icon-theme build-essential pkg-config \
    libxfce4panel-2.0-dev libxfce4ui-2-dev libxfconf-0-dev libgtk-3-dev
  ```

## Install

```sh
git clone https://github.com/lszl84/equinox.git
cd equinox
make
sudo make install
```

This installs the themes, the `equinox-mode` command and the icons under
`/usr/local`. The panel plugin goes into xfce4-panel's own directories under
`/usr`, the only places it looks. `sudo make uninstall` removes it all.

Then add the switch to a panel: **Panel → Panel Preferences → Items → +**,
then pick **Light/Dark Mode Switch**. Or, from a terminal:

```sh
xfce4-panel -r                       # the panel only scans for plugins at startup
xfce4-panel --add=equinox-switch
```

## Usage

Click the panel button, or use the command line:

```sh
equinox-mode light     # or: dark, toggle, reload, status
```

To switch with a key, bind `equinox-mode toggle` in **Settings → Keyboard →
Application Shortcuts**.

`equinox-mode` sets:

| Setting | Light | Dark |
| --- | --- | --- |
| GTK theme (`xsettings /Net/ThemeName`) | `Equinox` | `Equinox-dark` |
| Window frames (`xfwm4 /general/theme`) | `Equinox`, `-hdpi` or `-xhdpi` | `Equinox-dark`, `-hdpi` or `-xhdpi` |
| `org.gnome.desktop.interface color-scheme` | `default` | `prefer-dark` |

The xfwm4 variant follows the one you already use. Otherwise it is picked
from the window scaling factor: `-xhdpi` at 2x.

To switch between other themes, or to switch the icon theme as well, set any
of these in `~/.config/equinox/mode.conf`:

```sh
LIGHT_THEME=Adwaita
DARK_THEME=Adwaita-dark
LIGHT_WM_THEME=Default-xhdpi    # default: derived from the GTK theme
DARK_WM_THEME=Default-xhdpi
LIGHT_ICON_THEME=Papirus-Light  # default: leave the icon theme alone
DARK_ICON_THEME=Papirus-Dark
```

The panel button shows a moon whenever the GTK theme's name ends in "dark".

> [!NOTE]
> The panel itself only follows the theme when its background style is
> **None (use system style)**, in Panel Preferences → Appearance. A solid
> color set there stays the same in both modes.

## How it works

```
palettes/light.toml ┐               ┌▶ Equinox/gtk-3.0/gtk.css       (GTK3)
palettes/dark.toml  ┴─▶ build.py ───┼▶ Equinox*/xfwm4/*.png, themerc  (xfwm4)
gtk-3.0/base.css ───────────┘       └▶ Equinox-dark/…
```

- `gtk-3.0/base.css` is the whole GTK theme. It never names a concrete
  color: everything is mixed from a dozen palette colors, the same way
  Omagtk does it. `build.py` puts a palette in front of it for each variant.
  It also picks readable text for filled surfaces (accent, red, …) by WCAG
  contrast.
- `build.py` draws the xfwm4 frame as SVG with the same color math as GTK's
  `mix()`, so the title bars match the GTK header bars. It then renders them
  to PNG at each scale.
- The panel plugin (`plugin/equinox-switch.c`) is a button that runs
  `equinox-mode`. It watches the GTK theme setting to keep its icon current,
  including when you change the theme in **Settings → Appearance**.

To tweak the colors, edit `palettes/*.toml`, then run `make` and
`sudo make install`.

To check a change without installing it, run `make preview`. It renders a
widget showcase and a mock window for both modes into `build/preview/`.

To try a change on the desktop without root, run `make dev`. It links the
built themes into `~/.local/share/themes`, which takes precedence over the
installed copy, then reloads them. Run it again after each edit, and
`make undev` when you're done.

## Layout

| Path | What |
| --- | --- |
| `palettes/` | The light and dark palettes |
| `gtk-3.0/base.css` | The GTK3 stylesheet |
| `build.py` | Builds the GTK and xfwm4 themes into `build/themes/` |
| `bin/equinox-mode` | Switches modes |
| `plugin/` | The panel plugin |
| `icons/` | Sun and moon symbolic icons for the panel switch |
| `tools/preview.py` | Off-screen previews |

## License

[MIT](LICENSE). The GTK stylesheet is based on
[Omagtk](https://github.com/lszl84/omagtk), also MIT.
