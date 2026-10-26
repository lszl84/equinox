# Icons

These are the glyphs [Omarchy](https://github.com/omacom/omarchy)'s bar uses,
as symbolic SVGs. `tools/omarchy-icons.py` extracts them from the Nerd Fonts
symbols font, using the fit Omarchy's `OpticalGlyph` applies: the tight ink box
scaled so its longest side is 12px, centered by ink in a 16px canvas. So the
icons share one optical size however the panel draws them.

- `*.svg` go to `hicolor`, for the panel switch.
- `theme/*.svg` go into the Equinox icon theme, under the names the Xfce
  panel plugins and nm-applet ask for.

| File | Omarchy uses it for | Nerd Font glyph | Source |
| --- | --- | --- | --- |
| `equinox-light-symbolic` | weather, clear sky by day | `weather-day_sunny` U+E30D | Weather Icons |
| `equinox-dark-symbolic` | weather, clear sky at night | `weather-night_clear` U+E32B | Weather Icons |
| `nm-signal-00-symbolic` | wifi, 0 bars | `md-wifi_strength_outline` U+F092F | Material Design Icons |
| `nm-signal-25-symbolic` | wifi, 1 bar | `md-wifi_strength_1` U+F091F | Material Design Icons |
| `nm-signal-50-symbolic` | wifi, 2 bars | `md-wifi_strength_2` U+F0922 | Material Design Icons |
| `nm-signal-75-symbolic` | wifi, 3 bars | `md-wifi_strength_3` U+F0925 | Material Design Icons |
| `nm-signal-100-symbolic` | wifi, 4 bars | `md-wifi_strength_4` U+F0928 | Material Design Icons |
| `nm-no-connection-symbolic` | disconnected | `md-wifi_strength_off_outline` U+F092E | Material Design Icons |
| `nm-device-wired-symbolic` | ethernet | `md-ethernet` U+F0200 | Material Design Icons |
| `audio-volume-muted-symbolic` | muted | `fa-volume_xmark` U+EEE8 | Font Awesome Free |
| `audio-volume-low-symbolic` | volume above 0 | `fa-volume_off` U+F026 | Font Awesome Free |
| `audio-volume-medium-symbolic` | volume from 34% | `fa-volume_low` U+F027 | Font Awesome Free |
| `audio-volume-high-symbolic` | volume from 67% | `fa-volume_up` U+F028 | Font Awesome Free |
| `microphone-sensitivity-{high,medium,low}-symbolic` | microphone | `md-microphone` U+F036C | Material Design Icons |
| `microphone-sensitivity-muted-symbolic` | microphone, muted | `md-microphone_off` U+F036D | Material Design Icons |
| `system-reboot-symbolic` | reboot | `md-restart` U+F0709 | Material Design Icons |

To regenerate them, get `SymbolsNerdFont-Regular.ttf` from the
`NerdFontsSymbolsOnly` archive of a [Nerd Fonts release](https://github.com/ryanoasis/nerd-fonts/releases),
then run:

```sh
python3 tools/omarchy-icons.py SymbolsNerdFont-Regular.ttf [unpacked-fonttools-wheel]
```

## Licenses

The glyphs keep their upstream licenses, not this repo's MIT license:

- [Material Design Icons](https://pictogrammers.com/library/mdi/) by
  Pictogrammers: Apache License 2.0.
- [Font Awesome Free](https://fontawesome.com/license/free) by Fonticons:
  CC BY 4.0.
- [Weather Icons](https://erikflowers.github.io/weather-icons/) by Erik Flowers:
  SIL Open Font License 1.1.

[Nerd Fonts](https://www.nerdfonts.com/) collects them (MIT).
