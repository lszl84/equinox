/* Equinox workspaces: an Xfce panel workspace switcher drawn the way
 * Omarchy's bar draws its workspaces (shell/plugins/bar/widgets/
 * Workspaces.qml): a number per workspace, a rounded square on the active
 * one, and workspaces without windows at half opacity. Click a number to
 * switch to it; scroll over the switcher to step through them.
 *
 * The square is an icon (equinox-workspace-active-symbolic, Omarchy's
 * md-square_rounded glyph), drawn at the font's pixel size: the glyph is
 * 0.75em, and the icon's ink fills 0.75 of its canvas, so it matches the
 * digits as it would in a Nerd Font. */

#define WNCK_I_KNOW_THIS_IS_UNSTABLE
#include <gtk/gtk.h>
#include <libwnck/libwnck.h>
#include <libxfce4panel/libxfce4panel.h>

#define ACTIVE_ICON "equinox-workspace-active-symbolic"
#define BUTTON_WIDTH 20 /* Omarchy: Style.space(20) per workspace */

typedef struct
{
  XfcePanelPlugin *plugin; /* NULL when run standalone */
  WnckHandle *handle;
  WnckScreen *screen;
  GtkWidget *box;
  guint idle_id;
} EquinoxWorkspaces;

static void queue_update (EquinoxWorkspaces *ew);

/* A workspace counts as occupied if a normal window is on it. Pinned
 * (all-workspaces) windows, docks and the desktop don't count. */
static gboolean
workspace_occupied (EquinoxWorkspaces *ew,
                    WnckWorkspace *workspace)
{
  for (GList *l = wnck_screen_get_windows (ew->screen); l != NULL; l = l->next)
    {
      WnckWindow *window = l->data;
      WnckWindowType type = wnck_window_get_window_type (window);

      if (type == WNCK_WINDOW_DESKTOP || type == WNCK_WINDOW_DOCK
          || wnck_window_is_skip_pager (window) || wnck_window_is_pinned (window))
        continue;
      if (wnck_window_get_workspace (window) == workspace)
        return TRUE;
    }
  return FALSE;
}

/* The widget's font size in pixels, whether set in points or pixels. */
static gint
font_pixels (GtkWidget *widget)
{
  const PangoFontDescription *font =
    pango_context_get_font_description (gtk_widget_get_pango_context (widget));
  gdouble size = pango_font_description_get_size (font) / (gdouble) PANGO_SCALE;

  if (!pango_font_description_get_size_is_absolute (font))
    size *= gdk_screen_get_resolution (gtk_widget_get_screen (widget)) / 72.0;
  return MAX (8, (gint) (size + 0.5));
}

static void
clicked (GtkButton *button,
         EquinoxWorkspaces *ew)
{
  WnckWorkspace *workspace = g_object_get_data (G_OBJECT (button), "workspace");

  if (workspace != NULL && workspace != wnck_screen_get_active_workspace (ew->screen))
    wnck_workspace_activate (workspace, gtk_get_current_event_time ());
}

static gboolean
scrolled (GtkWidget *widget,
          GdkEventScroll *event,
          EquinoxWorkspaces *ew)
{
  WnckWorkspace *active = wnck_screen_get_active_workspace (ew->screen);
  gint count = wnck_screen_get_workspace_count (ew->screen);
  gint index, step = 0;

  if (active == NULL)
    return FALSE;
  if (event->direction == GDK_SCROLL_UP || event->direction == GDK_SCROLL_LEFT)
    step = -1;
  else if (event->direction == GDK_SCROLL_DOWN || event->direction == GDK_SCROLL_RIGHT)
    step = 1;

  index = wnck_workspace_get_number (active) + step;
  if (step != 0 && index >= 0 && index < count)
    wnck_workspace_activate (wnck_screen_get_workspace (ew->screen, index), event->time);
  return TRUE;
}

static gboolean
update (gpointer data)
{
  EquinoxWorkspaces *ew = data;
  WnckWorkspace *active = wnck_screen_get_active_workspace (ew->screen);
  gint count = wnck_screen_get_workspace_count (ew->screen);
  GList *children = gtk_container_get_children (GTK_CONTAINER (ew->box));

  ew->idle_id = 0;
  for (GList *l = children; l != NULL; l = l->next)
    gtk_widget_destroy (l->data);
  g_list_free (children);

  for (gint i = 0; i < count; i++)
    {
      WnckWorkspace *workspace = wnck_screen_get_workspace (ew->screen, i);
      GtkWidget *button = xfce_panel_create_button ();
      GtkWidget *child;

      if (workspace == active)
        {
          child = gtk_image_new_from_icon_name (ACTIVE_ICON, GTK_ICON_SIZE_BUTTON);
          gtk_image_set_pixel_size (GTK_IMAGE (child), font_pixels (button));
        }
      else
        {
          gchar *number = g_strdup_printf ("%d", i + 1);
          child = gtk_label_new (number);
          g_free (number);
        }

      gtk_container_add (GTK_CONTAINER (button), child);
      gtk_widget_set_size_request (button, BUTTON_WIDTH, -1);
      gtk_widget_set_opacity (button,
                              workspace == active || workspace_occupied (ew, workspace) ? 1.0 : 0.5);
      gtk_widget_set_tooltip_text (button, wnck_workspace_get_name (workspace));
      g_object_set_data (G_OBJECT (button), "workspace", workspace);
      g_signal_connect (button, "clicked", G_CALLBACK (clicked), ew);
      if (ew->plugin != NULL)
        xfce_panel_plugin_add_action_widget (ew->plugin, button);
      gtk_box_pack_start (GTK_BOX (ew->box), button, FALSE, FALSE, 0);
    }

  gtk_widget_show_all (ew->box);
  return G_SOURCE_REMOVE;
}

/* Many events arrive at once (a window moving fires several), so redraw
 * once when they settle. */
static void
queue_update (EquinoxWorkspaces *ew)
{
  if (ew->idle_id == 0)
    ew->idle_id = g_idle_add (update, ew);
}

static void
window_opened (WnckScreen *screen,
               WnckWindow *window,
               EquinoxWorkspaces *ew)
{
  g_signal_connect_swapped (window, "workspace-changed", G_CALLBACK (queue_update), ew);
  g_signal_connect_swapped (window, "state-changed", G_CALLBACK (queue_update), ew);
  queue_update (ew);
}

static EquinoxWorkspaces *
equinox_workspaces_new (XfcePanelPlugin *plugin)
{
  EquinoxWorkspaces *ew = g_new0 (EquinoxWorkspaces, 1);

  ew->plugin = plugin;
  ew->handle = wnck_handle_new (WNCK_CLIENT_TYPE_PAGER);
  ew->screen = wnck_handle_get_default_screen (ew->handle);
  wnck_screen_force_update (ew->screen);

  ew->box = gtk_box_new (GTK_ORIENTATION_HORIZONTAL, 1); /* Omarchy: space(1) */
  gtk_widget_add_events (ew->box, GDK_SCROLL_MASK);

  g_signal_connect_swapped (ew->screen, "active-workspace-changed", G_CALLBACK (queue_update), ew);
  g_signal_connect_swapped (ew->screen, "workspace-created", G_CALLBACK (queue_update), ew);
  g_signal_connect_swapped (ew->screen, "workspace-destroyed", G_CALLBACK (queue_update), ew);
  g_signal_connect_swapped (ew->screen, "window-closed", G_CALLBACK (queue_update), ew);
  g_signal_connect (ew->screen, "window-opened", G_CALLBACK (window_opened), ew);
  for (GList *l = wnck_screen_get_windows (ew->screen); l != NULL; l = l->next)
    window_opened (ew->screen, l->data, ew);
  /* The active square follows the font size. */
  g_signal_connect_swapped (ew->box, "style-updated", G_CALLBACK (queue_update), ew);

  update (ew);
  return ew;
}

#ifdef EQUINOX_STANDALONE

/* A test window: cc -DEQUINOX_STANDALONE ... && ./equinox-workspaces */
int
main (int argc, char **argv)
{
  GtkWidget *window;
  EquinoxWorkspaces *ew;

  gtk_init (&argc, &argv);
  window = gtk_window_new (GTK_WINDOW_TOPLEVEL);
  gtk_window_set_default_size (GTK_WINDOW (window), 200, 40);
  ew = equinox_workspaces_new (NULL);
  gtk_container_add (GTK_CONTAINER (window), ew->box);
  g_signal_connect (ew->box, "scroll-event", G_CALLBACK (scrolled), ew);
  g_signal_connect (window, "destroy", G_CALLBACK (gtk_main_quit), NULL);
  gtk_widget_show_all (window);
  gtk_main ();
  return 0;
}

#else

static void
orientation_changed (XfcePanelPlugin *plugin,
                     GtkOrientation orientation,
                     EquinoxWorkspaces *ew)
{
  gtk_orientable_set_orientation (GTK_ORIENTABLE (ew->box), orientation);
}

static void
free_data (XfcePanelPlugin *plugin,
           EquinoxWorkspaces *ew)
{
  if (ew->idle_id != 0)
    g_source_remove (ew->idle_id);
  g_signal_handlers_disconnect_by_data (ew->screen, ew);
  for (GList *l = wnck_screen_get_windows (ew->screen); l != NULL; l = l->next)
    g_signal_handlers_disconnect_by_data (l->data, ew);
  g_object_unref (ew->handle);
  g_free (ew);
}

static void
construct (XfcePanelPlugin *plugin)
{
  EquinoxWorkspaces *ew = equinox_workspaces_new (plugin);

  gtk_container_add (GTK_CONTAINER (plugin), ew->box);
  orientation_changed (plugin, xfce_panel_plugin_get_orientation (plugin), ew);
  gtk_widget_add_events (GTK_WIDGET (plugin), GDK_SCROLL_MASK);

  g_signal_connect (plugin, "scroll-event", G_CALLBACK (scrolled), ew);
  g_signal_connect (plugin, "orientation-changed", G_CALLBACK (orientation_changed), ew);
  g_signal_connect (plugin, "free-data", G_CALLBACK (free_data), ew);
  gtk_widget_show_all (ew->box);
}

XFCE_PANEL_PLUGIN_REGISTER (construct);

#endif
