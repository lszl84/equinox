#!/usr/bin/env python3
"""Render the built themes to PNGs without touching the desktop.

    python3 tools/preview.py [--scale 2] OUTDIR

Writes OUTDIR/gtk-light.png and gtk-dark.png (a widget showcase drawn
off-screen with the GTK theme) and xfwm4-light.png and xfwm4-dark.png (a
mock window composed from the xfwm4 frame images). Run build.py first.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEMES = ROOT / "build" / "themes"
sys.path.insert(0, str(ROOT))
import build  # noqa: E402  (for NAME and the frame geometry)


def gtk_showcase(out):
    """Runs in a child process with GTK_THEME set; draws the showcase."""
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk

    win = Gtk.OffscreenWindow()
    outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    outer.get_style_context().add_class("background")
    win.add(outer)

    header = Gtk.HeaderBar(title="Equinox", subtitle="GTK3 preview")
    header.pack_start(Gtk.Button.new_from_icon_name("go-previous-symbolic", Gtk.IconSize.BUTTON))
    header.pack_end(Gtk.MenuButton(image=Gtk.Image.new_from_icon_name("open-menu-symbolic", Gtk.IconSize.BUTTON)))
    header.pack_end(Gtk.Button.new_from_icon_name("system-search-symbolic", Gtk.IconSize.BUTTON))
    outer.pack_start(header, False, False, 0)

    paned = Gtk.Box()
    outer.pack_start(paned, True, True, 0)

    side = Gtk.ListBox()
    side.get_style_context().add_class("navigation-sidebar")
    sidebox = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
    sidebox.get_style_context().add_class("sidebar")
    sidebox.set_size_request(150, -1)
    for name in ("Home", "Desktop", "Documents", "Downloads", "Trash"):
        row = Gtk.ListBoxRow()
        row.add(Gtk.Label(label=name, xalign=0, margin=8))
        side.add(row)
    side.select_row(side.get_row_at_index(2))
    sidebox.add(side)
    paned.pack_start(sidebox, False, False, 0)

    grid = Gtk.Grid(column_spacing=12, row_spacing=12, margin=18)
    paned.pack_start(grid, True, True, 0)

    def hbox(*widgets):
        b = Gtk.Box(spacing=8)
        for w in widgets:
            b.pack_start(w, False, False, 0)
        return b

    def styled(widget, *classes):
        for c in classes:
            widget.get_style_context().add_class(c)
        return widget

    toggle = Gtk.ToggleButton(label="Toggled")
    toggle.set_active(True)
    grid.attach(hbox(Gtk.Button(label="Button"),
                     styled(Gtk.Button(label="Suggested"), "suggested-action"),
                     styled(Gtk.Button(label="Delete"), "destructive-action"),
                     toggle,
                     styled(Gtk.Button(label="Flat"), "flat")), 0, 0, 2, 1)

    entry = Gtk.Entry(text="Some text")
    entry.set_hexpand(True)
    combo = Gtk.ComboBoxText()
    for t in ("First", "Second"):
        combo.append_text(t)
    combo.set_active(0)
    grid.attach(entry, 0, 1, 1, 1)
    grid.attach(hbox(combo, Gtk.SpinButton.new_with_range(0, 100, 1)), 1, 1, 1, 1)

    check_on = Gtk.CheckButton(label="Checked")
    check_on.set_active(True)
    radio1 = Gtk.RadioButton(label="Radio")
    radio2 = Gtk.RadioButton(label="Other", group=radio1)
    sw_on = Gtk.Switch(active=True)
    grid.attach(hbox(check_on, Gtk.CheckButton(label="Unchecked"), radio1, radio2,
                     sw_on, Gtk.Switch()), 0, 2, 2, 1)

    scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
    scale.set_value(60)
    scale.set_draw_value(False)
    progress = Gtk.ProgressBar(fraction=0.4, valign=Gtk.Align.CENTER)
    grid.attach(scale, 0, 3, 1, 1)
    grid.attach(progress, 1, 3, 1, 1)

    notebook = Gtk.Notebook()
    store = Gtk.ListStore(str, str)
    for row in (("report.pdf", "1.2 MB"), ("photo.jpg", "3.4 MB"), ("notes.txt", "2 KB")):
        store.append(row)
    tree = Gtk.TreeView(model=store)
    for i, title in enumerate(("Name", "Size")):
        tree.append_column(Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i))
    tree.get_selection().select_path(1)
    notebook.append_page(tree, Gtk.Label(label="Files"))
    notebook.append_page(Gtk.Label(label="Second"), Gtk.Label(label="Settings"))
    notebook.set_size_request(-1, 130)
    grid.attach(notebook, 0, 4, 1, 1)

    info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    info.pack_start(Gtk.Label(label="Regular label", xalign=0), False, False, 0)
    info.pack_start(styled(Gtk.Label(label="Dim label", xalign=0), "dim-label"), False, False, 0)
    link = Gtk.LinkButton(uri="https://example.org", label="A link")
    link.set_halign(Gtk.Align.START)
    info.pack_start(link, False, False, 0)
    bar = Gtk.InfoBar(message_type=Gtk.MessageType.WARNING)
    bar.get_content_area().add(Gtk.Label(label="Warning info bar"))
    info.pack_start(bar, False, False, 0)
    grid.attach(info, 1, 4, 1, 1)

    win.set_default_size(760, -1)
    win.show_all()
    while Gtk.events_pending():
        Gtk.main_iteration()
    win.get_pixbuf().savev(out, "png", [], [])


def read_themerc(path):
    rc = {}
    for line in path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            rc[k] = v
    return rc


def xfwm4_mock(theme_dir, scale, client_bg, out):
    """Compose a window (active and inactive) from the xfwm4 images."""
    import gi
    gi.require_version("Gdk", "3.0")
    gi.require_version("PangoCairo", "1.0")
    import cairo
    from gi.repository import Gdk, GdkPixbuf, Pango, PangoCairo

    d = theme_dir / "xfwm4"
    rc = read_themerc(d / "themerc")
    img = lambda name: GdkPixbuf.Pixbuf.new_from_file(str(d / f"{name}.png"))
    s = scale
    W, C = int(460 * s), int(150 * s)  # frame width, client height
    pad = int(24 * s)
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W + 2 * pad, 2 * (C + 60 * s) + 3 * pad)
    cr = cairo.Context(surface)
    grad = cairo.LinearGradient(0, 0, surface.get_width(), surface.get_height())
    grad.add_color_stop_rgb(0, 0.36, 0.52, 0.70)
    grad.add_color_stop_rgb(1, 0.85, 0.80, 0.72)
    cr.set_source(grad)
    cr.paint()

    def blit(pb, x, y, w=None, h=None):
        cr.save()
        cr.rectangle(x, y, w or pb.get_width(), h or pb.get_height())
        cr.clip()
        Gdk.cairo_set_source_pixbuf(cr, pb, x, y)
        cr.get_source().set_extend(cairo.Extend.REPEAT)
        cr.paint()
        cr.restore()

    def window(y0, state, close_state):
        x0 = pad
        tl, tr = img(f"top-left-{state}"), img(f"top-right-{state}")
        H = tl.get_height()
        blit(tl, x0, y0)
        blit(tr, x0 + W - tr.get_width(), y0)
        # Buttons for the layout "|HMC". xfwm4 places them button_offset
        # inside the side border.
        off = int(rc["button_offset"]) + img(f"right-{state}").get_width()
        bx = x0 + W - off
        buttons = []
        for kind, st in reversed([("hide", state), ("maximize", state), ("close", close_state)]):
            pb = img(f"{kind}-{st}")
            bx -= pb.get_width()
            buttons.append((pb, bx))
        # The title strip fills the rest; xfwm4 never draws it under a button.
        title = img(f"title-3-{state}")
        blit(title, x0 + tl.get_width(), y0, bx - x0 - tl.get_width(), H)
        gap = off - tr.get_width()
        if gap > 0:
            blit(title, x0 + W - off, y0, gap, H)
        for pb, x in buttons:
            blit(pb, x, y0)
        left, rightb, bottom = img(f"left-{state}"), img(f"right-{state}"), img(f"bottom-{state}")
        B = left.get_width()
        blit(left, x0, y0 + H, B, C)
        blit(rightb, x0 + W - B, y0 + H, B, C)
        blit(img(f"bottom-left-{state}"), x0, y0 + H + C)
        blit(img(f"bottom-right-{state}"), x0 + W - B, y0 + H + C)
        blit(bottom, x0 + B, y0 + H + C, W - 2 * B, bottom.get_height())
        # Client area: the GTK window background.
        bg = Gdk.RGBA()
        bg.parse(client_bg)
        cr.set_source_rgb(bg.red, bg.green, bg.blue)
        cr.rectangle(x0 + B, y0 + H, W - 2 * B, C)
        cr.fill()
        # Title text, centered like full_width_title=true.
        color = Gdk.RGBA()
        color.parse(rc["active_text_color" if state == "active" else "inactive_text_color"])
        layout = PangoCairo.create_layout(cr)
        layout.set_text(f"{theme_dir.name} — {state}", -1)
        font = Pango.FontDescription("Sans Bold 9")
        font.set_absolute_size(9 * 96 / 72 * s * Pango.SCALE)
        layout.set_font_description(font)
        tw, th = layout.get_pixel_size()
        cr.move_to(x0 + (W - tw) / 2, y0 + (H - th) / 2)
        cr.set_source_rgb(color.red, color.green, color.blue)
        PangoCairo.show_layout(cr, layout)
        return H + C + bottom.get_height()

    y = pad
    y += window(y, "active", "prelight") + pad
    window(y, "inactive", "inactive")
    surface.write_to_png(str(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir", type=Path)
    ap.add_argument("--scale", type=int, default=1, help="GDK scale and xfwm4 variant (1 or 2)")
    ap.add_argument("--gtk-child", nargs=1, help=argparse.SUPPRESS)
    args = ap.parse_args()

    if args.gtk_child:
        gtk_showcase(args.gtk_child[0])
        return

    args.outdir.mkdir(parents=True, exist_ok=True)
    suffix = {1: "", 2: "-xhdpi"}[args.scale]
    for mode, theme in (("light", build.NAME), ("dark", f"{build.NAME}-dark")):
        env = dict(os.environ, GTK_THEME=theme, XDG_DATA_HOME=str(ROOT / "build"),
                   GDK_SCALE=str(args.scale))
        out = args.outdir / f"gtk-{mode}.png"
        subprocess.run([sys.executable, "-I", __file__, str(args.outdir),
                        "--gtk-child", str(out)], env=env, check=True)
        pal = build.Palette(ROOT / "palettes" / f"{mode}.toml")
        xfwm4_mock(THEMES / (theme + suffix), args.scale, build.hexc(pal.background),
                   args.outdir / f"xfwm4-{mode}.png")
        print(f"{mode}: {out}, {args.outdir / f'xfwm4-{mode}.png'}")


if __name__ == "__main__":
    main()
