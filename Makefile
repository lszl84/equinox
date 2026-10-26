# Equinox: GTK3 + xfwm4 themes and a light/dark panel switch for Xfce.
#
#   make                  build the themes and the panel plugin
#   sudo make install     install system-wide (PREFIX=/usr/local)
#   sudo make uninstall
#   make preview          render the themes to build/preview/ (no install)

PREFIX ?= /usr/local
DATADIR = $(PREFIX)/share
# xfce4-panel 4.20 only looks for plugins in its own directories, not in
# PREFIX: modules in its library dir, .desktop files in its data dir.
PLUGIN_DIR ?= $(shell pkg-config --variable=libdir libxfce4panel-2.0)/xfce4/panel/plugins
PLUGIN_DATA_DIR ?= $(shell pkg-config --variable=prefix libxfce4panel-2.0)/share/xfce4/panel/plugins

PKGS = libxfce4panel-2.0 libxfconf-0 gtk+-3.0
CFLAGS ?= -O2 -g
CFLAGS += -Wall -Wextra -Wno-unused-parameter -fPIC $(shell pkg-config --cflags $(PKGS))
LDLIBS = $(shell pkg-config --libs $(PKGS))

PLUGIN = build/libequinox-switch.so
THEMES = Equinox Equinox-dark Equinox-hdpi Equinox-dark-hdpi Equinox-xhdpi Equinox-dark-xhdpi

all: themes $(PLUGIN)

themes:
	python3 build.py

$(PLUGIN): plugin/equinox-switch.c
	@pkg-config --print-errors --exists $(PKGS) || { \
	  echo "Install: libxfce4panel-2.0-dev libxfce4ui-2-dev libxfconf-0-dev libgtk-3-dev"; exit 1; }
	@mkdir -p build
	$(CC) $(CFLAGS) -DEQUINOX_MODE='"$(PREFIX)/bin/equinox-mode"' -shared -o $@ $< $(LDFLAGS) $(LDLIBS)

preview: themes
	python3 tools/preview.py build/preview

install:
	@test -d build/themes -a -f $(PLUGIN) || { echo "Run 'make' first."; exit 1; }
	install -d $(DESTDIR)$(DATADIR)/themes
	for t in $(THEMES); do rm -rf $(DESTDIR)$(DATADIR)/themes/$$t; done
	cp -r build/themes/. $(DESTDIR)$(DATADIR)/themes/
	install -Dm755 bin/equinox-mode $(DESTDIR)$(PREFIX)/bin/equinox-mode
	install -Dm755 $(PLUGIN) $(DESTDIR)$(PLUGIN_DIR)/libequinox-switch.so
	install -Dm644 plugin/equinox-switch.desktop $(DESTDIR)$(PLUGIN_DATA_DIR)/equinox-switch.desktop
	install -Dm644 -t $(DESTDIR)$(DATADIR)/icons/hicolor/scalable/status icons/*.svg

uninstall:
	for t in $(THEMES); do rm -rf $(DESTDIR)$(DATADIR)/themes/$$t; done
	rm -f $(DESTDIR)$(PREFIX)/bin/equinox-mode
	rm -f $(DESTDIR)$(PLUGIN_DIR)/libequinox-switch.so
	rm -f $(DESTDIR)$(PLUGIN_DATA_DIR)/equinox-switch.desktop
	rm -f $(DESTDIR)$(DATADIR)/icons/hicolor/scalable/status/equinox-light-symbolic.svg
	rm -f $(DESTDIR)$(DATADIR)/icons/hicolor/scalable/status/equinox-dark-symbolic.svg

clean:
	rm -rf build

.PHONY: all themes preview install uninstall clean
