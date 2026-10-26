/* Equinox center: an invisible panel item that puts the item after it in
 * the middle of the monitor.
 *
 * Xfce's panel can only center an item between two expanding separators,
 * that is, between whatever sits left and right of them, so a clock drifts
 * as those groups change width. Put this item just before the clock, and
 * an expanding separator after it: this item takes exactly the space that
 * puts the clock's center at the monitor's center. It measures again
 * whenever anything before it, or the clock itself, changes size. With no
 * room left of the center it takes no space, and the clock simply follows
 * the items before it. */

#include <gtk/gtk.h>
#include <libxfce4panel/libxfce4panel.h>

typedef struct
{
  XfcePanelPlugin *plugin;
  GtkWidget *space;
  GtkWidget *watched; /* the next item, whose size we follow */
  gint size;
  guint idle_id;
} EquinoxCenter;

static void queue_measure (EquinoxCenter *ec);

static GtkWidget *
next_item (EquinoxCenter *ec)
{
  GtkWidget *parent = gtk_widget_get_parent (GTK_WIDGET (ec->plugin));
  GtkWidget *next = NULL;
  GList *children, *self;

  if (parent == NULL || !GTK_IS_CONTAINER (parent))
    return NULL;
  children = gtk_container_get_children (GTK_CONTAINER (parent));
  self = g_list_find (children, ec->plugin);
  if (self != NULL && self->next != NULL)
    next = self->next->data;
  g_list_free (children);
  return next;
}

static void
watch (EquinoxCenter *ec,
       GtkWidget *next)
{
  if (next == ec->watched)
    return;
  if (ec->watched != NULL)
    g_signal_handlers_disconnect_by_data (ec->watched, ec);
  ec->watched = next;
  if (next != NULL)
    {
      g_signal_connect_swapped (next, "size-allocate", G_CALLBACK (queue_measure), ec);
      g_signal_connect_swapped (next, "destroy", G_CALLBACK (queue_measure), ec);
    }
}

static gboolean
measure (gpointer data)
{
  EquinoxCenter *ec = data;
  GtkWidget *widget = GTK_WIDGET (ec->plugin);
  GtkWidget *toplevel = gtk_widget_get_toplevel (widget);
  GtkWidget *next = next_item (ec);
  gboolean horizontal = xfce_panel_plugin_get_orientation (ec->plugin) == GTK_ORIENTATION_HORIZONTAL;
  GdkWindow *window;
  GdkRectangle monitor;
  gint x, y, origin_x, origin_y, size;

  ec->idle_id = 0;
  watch (ec, next);
  if (next == NULL || !gtk_widget_get_realized (toplevel)
      || !gtk_widget_translate_coordinates (widget, toplevel, 0, 0, &x, &y))
    return G_SOURCE_REMOVE;

  window = gtk_widget_get_window (toplevel);
  gdk_window_get_origin (window, &origin_x, &origin_y);
  gdk_monitor_get_geometry (gdk_display_get_monitor_at_window (gtk_widget_get_display (widget), window),
                            &monitor);

  /* Where this item starts on screen is set by the items before it, not by
   * its own size, so the result settles at once. */
  if (horizontal)
    size = monitor.x + monitor.width / 2 - gtk_widget_get_allocated_width (next) / 2 - (origin_x + x);
  else
    size = monitor.y + monitor.height / 2 - gtk_widget_get_allocated_height (next) / 2 - (origin_y + y);
  size = MAX (0, size);

  if (size != ec->size)
    {
      ec->size = size;
      gtk_widget_set_size_request (ec->space, horizontal ? size : -1, horizontal ? -1 : size);
    }
  return G_SOURCE_REMOVE;
}

static void
queue_measure (EquinoxCenter *ec)
{
  if (ec->idle_id == 0)
    ec->idle_id = g_idle_add (measure, ec);
}

static gboolean
toplevel_configured (GtkWidget *toplevel,
                     GdkEvent *event,
                     EquinoxCenter *ec)
{
  queue_measure (ec);
  return FALSE;
}

static void
hierarchy_changed (GtkWidget *widget,
                   GtkWidget *previous,
                   EquinoxCenter *ec)
{
  GtkWidget *toplevel = gtk_widget_get_toplevel (widget);

  if (previous != NULL)
    g_signal_handlers_disconnect_by_data (previous, ec);
  if (gtk_widget_is_toplevel (toplevel))
    g_signal_connect (toplevel, "configure-event", G_CALLBACK (toplevel_configured), ec);
  queue_measure (ec);
}

static void
free_data (XfcePanelPlugin *plugin,
           EquinoxCenter *ec)
{
  GtkWidget *toplevel = gtk_widget_get_toplevel (GTK_WIDGET (plugin));

  if (ec->idle_id != 0)
    g_source_remove (ec->idle_id);
  watch (ec, NULL);
  if (toplevel != NULL)
    g_signal_handlers_disconnect_by_data (toplevel, ec);
  g_free (ec);
}

static void
construct (XfcePanelPlugin *plugin)
{
  EquinoxCenter *ec = g_new0 (EquinoxCenter, 1);

  ec->plugin = plugin;
  ec->space = gtk_drawing_area_new ();
  gtk_container_add (GTK_CONTAINER (plugin), ec->space);
  gtk_widget_show (ec->space);

  g_signal_connect_swapped (plugin, "size-allocate", G_CALLBACK (queue_measure), ec);
  g_signal_connect_swapped (plugin, "screen-position-changed", G_CALLBACK (queue_measure), ec);
  g_signal_connect_swapped (plugin, "orientation-changed", G_CALLBACK (queue_measure), ec);
  g_signal_connect (plugin, "hierarchy-changed", G_CALLBACK (hierarchy_changed), ec);
  g_signal_connect (plugin, "free-data", G_CALLBACK (free_data), ec);
  hierarchy_changed (GTK_WIDGET (plugin), NULL, ec);
}

XFCE_PANEL_PLUGIN_REGISTER (construct);
