# Equinox: GTK3 + xfwm4 themes, icons and panel plugins for Xfce.
#
#   make                  build the themes and the panel plugins
#   sudo make install     install system-wide (PREFIX=/usr/local)
#   sudo make uninstall
#   make preview          render the themes to build/preview/ (no install)
#   make dev              use the themes straight from build/ and reload them
#   make undev            go back to the installed themes

PREFIX ?= /usr/local
DATADIR = $(PREFIX)/share
# xfce4-panel 4.20 only looks for plugins in its own directories, not in
# PREFIX: modules in its library dir, .desktop files in its data dir.
PLUGIN_DIR ?= $(shell pkg-config --variable=libdir libxfce4panel-2.0)/xfce4/panel/plugins
PLUGIN_DATA_DIR ?= $(shell pkg-config --variable=prefix libxfce4panel-2.0)/share/xfce4/panel/plugins

PKGS = libxfce4panel-2.0 libxfconf-0 gtk+-3.0 libwnck-3.0
CFLAGS ?= -O2 -g
CFLAGS += -Wall -Wextra -Wno-unused-parameter -fPIC

SWITCH = build/libequinox-switch.so
WORKSPACES = build/libequinox-workspaces.so
CENTER = build/libequinox-center.so
PLUGINS = $(SWITCH) $(WORKSPACES) $(CENTER)
THEMES = Equinox Equinox-dark Equinox-hdpi Equinox-dark-hdpi Equinox-xhdpi Equinox-dark-xhdpi

all: themes $(PLUGINS)

themes:
	python3 build.py

check-deps:
	@pkg-config --print-errors --exists $(PKGS) || { \
	  echo "Install: libxfce4panel-2.0-dev libxfce4ui-2-dev libxfconf-0-dev libgtk-3-dev libwnck-3-dev"; exit 1; }
	@mkdir -p build

$(SWITCH): plugin/equinox-switch.c | check-deps
	$(CC) $(CFLAGS) $(shell pkg-config --cflags libxfce4panel-2.0 libxfconf-0 gtk+-3.0) \
	  -DEQUINOX_MODE='"$(PREFIX)/bin/equinox-mode"' -shared -o $@ $< $(LDFLAGS) \
	  $(shell pkg-config --libs libxfce4panel-2.0 libxfconf-0 gtk+-3.0)

$(WORKSPACES): plugin/equinox-workspaces.c | check-deps
	$(CC) $(CFLAGS) $(shell pkg-config --cflags libxfce4panel-2.0 libwnck-3.0) \
	  -shared -o $@ $< $(LDFLAGS) $(shell pkg-config --libs libxfce4panel-2.0 libwnck-3.0)

$(CENTER): plugin/equinox-center.c | check-deps
	$(CC) $(CFLAGS) $(shell pkg-config --cflags libxfce4panel-2.0) \
	  -shared -o $@ $< $(LDFLAGS) $(shell pkg-config --libs libxfce4panel-2.0)

preview: themes
	python3 tools/preview.py build/preview

# ~/.local/share/themes takes precedence over an installed copy, so linking
# build/themes there lets you iterate without root.
dev: themes
	@mkdir -p $(HOME)/.local/share/themes
	@for t in $(THEMES); do ln -sfn $(CURDIR)/build/themes/$$t $(HOME)/.local/share/themes/$$t; done
	@mkdir -p $(HOME)/.local/share/icons
	@ln -sfn $(CURDIR)/build/icons/Equinox $(HOME)/.local/share/icons/Equinox
	bin/equinox-mode reload

undev:
	@for t in $(THEMES); do \
	  if [ -L $(HOME)/.local/share/themes/$$t ]; then rm $(HOME)/.local/share/themes/$$t; fi; done
	@if [ -L $(HOME)/.local/share/icons/Equinox ]; then rm $(HOME)/.local/share/icons/Equinox; fi
	bin/equinox-mode reload

install:
	@test -d build/themes -a -f $(SWITCH) -a -f $(WORKSPACES) -a -f $(CENTER) || { echo "Run 'make' first."; exit 1; }
	install -d $(DESTDIR)$(DATADIR)/themes
	for t in $(THEMES); do rm -rf $(DESTDIR)$(DATADIR)/themes/$$t; done
	cp -r build/themes/. $(DESTDIR)$(DATADIR)/themes/
	install -Dm755 bin/equinox-mode $(DESTDIR)$(PREFIX)/bin/equinox-mode
	install -Dm755 -t $(DESTDIR)$(PLUGIN_DIR) $(PLUGINS)
	install -Dm644 -t $(DESTDIR)$(PLUGIN_DATA_DIR) plugin/*.desktop
	install -Dm644 -t $(DESTDIR)$(DATADIR)/icons/hicolor/scalable/status icons/*.svg
	rm -rf $(DESTDIR)$(DATADIR)/icons/Equinox
	cp -r build/icons/Equinox $(DESTDIR)$(DATADIR)/icons/

uninstall:
	for t in $(THEMES); do rm -rf $(DESTDIR)$(DATADIR)/themes/$$t; done
	rm -f $(DESTDIR)$(PREFIX)/bin/equinox-mode
	for p in switch workspaces center; do \
	  rm -f $(DESTDIR)$(PLUGIN_DIR)/libequinox-$$p.so $(DESTDIR)$(PLUGIN_DATA_DIR)/equinox-$$p.desktop; done
	rm -f $(DESTDIR)$(DATADIR)/icons/hicolor/scalable/status/equinox-light-symbolic.svg
	rm -f $(DESTDIR)$(DATADIR)/icons/hicolor/scalable/status/equinox-dark-symbolic.svg
	rm -f $(DESTDIR)$(DATADIR)/icons/hicolor/scalable/status/equinox-workspace-active-symbolic.svg
	rm -rf $(DESTDIR)$(DATADIR)/icons/Equinox

clean:
	rm -rf build

.PHONY: all themes check-deps preview dev undev install uninstall clean
