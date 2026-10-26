/* Equinox light/dark switch: an Xfce panel button that shows a sun in light
 * mode and a moon in dark mode, and switches mode when clicked.
 *
 * The switching itself is done by equinox-mode, so the button, the command
 * line and any keyboard shortcut all behave the same. The button only
 * watches the GTK theme setting to keep its icon current, which also picks
 * up a theme changed in Settings > Appearance. */

#include <gtk/gtk.h>
#include <libxfce4panel/libxfce4panel.h>
#include <string.h>
#include <xfconf/xfconf.h>

#ifndef EQUINOX_MODE
#define EQUINOX_MODE "equinox-mode"
#endif

#define THEME_PROPERTY "/Net/ThemeName"

typedef struct
{
  XfcePanelPlugin *plugin;
  GtkWidget *button;
  GtkWidget *image;
  XfconfChannel *xsettings;
  gboolean dark;
} EquinoxSwitch;

/* Same rule as equinox-mode: a theme whose name ends in "dark". */
static gboolean
theme_is_dark (const gchar *name)
{
  gsize len = name != NULL ? strlen (name) : 0;

  return len >= 4 && g_ascii_strcasecmp (name + len - 4, "dark") == 0;
}

static void
update (EquinoxSwitch *sw)
{
  gchar *theme = xfconf_channel_get_string (sw->xsettings, THEME_PROPERTY, NULL);

  sw->dark = theme_is_dark (theme);
  g_free (theme);

  gtk_image_set_from_icon_name (GTK_IMAGE (sw->image),
                                sw->dark ? "equinox-dark-symbolic" : "equinox-light-symbolic",
                                GTK_ICON_SIZE_BUTTON);
  gtk_image_set_pixel_size (GTK_IMAGE (sw->image),
                            xfce_panel_plugin_get_icon_size (sw->plugin));
  gtk_widget_set_tooltip_text (sw->button,
                               sw->dark ? "Dark mode — click for light mode"
                                        : "Light mode — click for dark mode");
}

static void
theme_changed (XfconfChannel *channel,
               const gchar *property,
               const GValue *value,
               EquinoxSwitch *sw)
{
  update (sw);
}

static void
clicked (GtkButton *button,
         EquinoxSwitch *sw)
{
  /* Ask for the mode the icon promises, rather than "toggle", so a click
   * always does what the tooltip says. */
  gchar *argv[] = { EQUINOX_MODE, sw->dark ? "light" : "dark", NULL };
  GError *error = NULL;

  if (!g_spawn_async (NULL, argv, NULL, G_SPAWN_SEARCH_PATH, NULL, NULL, NULL, &error))
    {
      GtkWidget *dialog = gtk_message_dialog_new (NULL, 0, GTK_MESSAGE_ERROR, GTK_BUTTONS_CLOSE,
                                                  "Could not switch the theme");

      gtk_message_dialog_format_secondary_text (GTK_MESSAGE_DIALOG (dialog), "%s", error->message);
      g_signal_connect (dialog, "response", G_CALLBACK (gtk_widget_destroy), NULL);
      gtk_widget_show (dialog);
      g_error_free (error);
    }
}

static gboolean
size_changed (XfcePanelPlugin *plugin,
              gint size,
              EquinoxSwitch *sw)
{
  size /= xfce_panel_plugin_get_nrows (plugin);
  gtk_widget_set_size_request (sw->button, size, size);
  gtk_image_set_pixel_size (GTK_IMAGE (sw->image), xfce_panel_plugin_get_icon_size (plugin));

  return TRUE;
}

static void
free_data (XfcePanelPlugin *plugin,
           EquinoxSwitch *sw)
{
  g_signal_handlers_disconnect_by_data (sw->xsettings, sw);
  g_free (sw);
  xfconf_shutdown ();
}

static void
construct (XfcePanelPlugin *plugin)
{
  EquinoxSwitch *sw;
  GError *error = NULL;

  if (!xfconf_init (&error))
    {
      g_warning ("equinox-switch: could not connect to xfconf: %s", error->message);
      g_error_free (error);
      return;
    }

  sw = g_new0 (EquinoxSwitch, 1);
  sw->plugin = plugin;
  sw->xsettings = xfconf_channel_get ("xsettings");

  sw->button = xfce_panel_create_button ();
  sw->image = gtk_image_new ();
  gtk_container_add (GTK_CONTAINER (sw->button), sw->image);
  gtk_container_add (GTK_CONTAINER (plugin), sw->button);
  xfce_panel_plugin_add_action_widget (plugin, sw->button);
  xfce_panel_plugin_set_small (plugin, TRUE);

  g_signal_connect (sw->button, "clicked", G_CALLBACK (clicked), sw);
  g_signal_connect (plugin, "size-changed", G_CALLBACK (size_changed), sw);
  g_signal_connect (plugin, "free-data", G_CALLBACK (free_data), sw);
  g_signal_connect (sw->xsettings, "property-changed::" THEME_PROPERTY,
                    G_CALLBACK (theme_changed), sw);

  update (sw);
  gtk_widget_show_all (sw->button);
}

XFCE_PANEL_PLUGIN_REGISTER (construct);
