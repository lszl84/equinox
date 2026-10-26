# Icons

These are the glyphs [Omarchy](https://github.com/omacom/omarchy)'s bar uses,
as symbolic SVGs, extracted from the Nerd Fonts symbols font by
`tools/omarchy-icons.py`.

Every status icon gets the same ink height: 10.5 of a 16px canvas, so 21px
on a 2x panel, centered by ink. That's the glyphs' own proportion: in the
font the Material Design and Font Awesome glyphs share a height of about
0.8em, with wide ones simply wider. So the row reads as evenly as the
glyphs set as text, and sits level with the panel's 13px digits.

Fitting the longest side instead, as Omarchy's current `OpticalGlyph` does,
shrinks wide icons: on the panel the volume icon was 16px tall next to a
24px battery. The active-workspace square keeps that fit (longest side 12 of
16), because the workspaces plugin draws it at the font's pixel size.

- `*.svg` go to `hicolor`, for the panel plugins.
- `theme/*.svg` go into the Equinox icon theme, under the names the Xfce
  panel plugins (volume, power manager), nm-applet, Blueman and genmon ask
  for.

| File | Omarchy uses it for | Nerd Font glyph | Source |
| --- | --- | --- | --- |
| `equinox-light-symbolic` | weather, clear sky by day | `weather-day_sunny` U+E30D | Weather Icons |
| `equinox-dark-symbolic` | weather, clear sky at night | `weather-night_clear` U+E32B | Weather Icons |
| `equinox-workspace-active-symbolic` | workspaces, the active one | `md-square_rounded` U+F14FB | Material Design Icons |
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
| `blueman-tray-symbolic`, `bluetooth-symbolic`, `bluetooth-active-symbolic` | Bluetooth on | `md-bluetooth` U+F00AF | Material Design Icons |
| `blueman-active-symbolic` | Bluetooth, a device connected | `md-bluetooth_connect` U+F00B1 | Material Design Icons |
| `blueman-disabled-symbolic`, `bluetooth-disabled-symbolic` | Bluetooth off | `md-bluetooth_off` U+F00B2 | Material Design Icons |
| `battery-level-{0,10,…,100}-symbolic` | battery, on battery: `floor(percent / 10)`, capped at 9, picks `md-battery_10` … `md-battery_90` then `md-battery` | U+F007A … U+F0082, U+F0079 | Material Design Icons |
| `battery-level-{0,10,…,100}-charging-symbolic` | battery, plugged in: same steps, `md-battery_charging_10` … `md-battery_charging_100` | U+F089C … U+F0085 | Material Design Icons |
| `battery-level-100-charged-symbolic` | fully charged | `md-battery_charging_100` U+F0085 | Material Design Icons |

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
