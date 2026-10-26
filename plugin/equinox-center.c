/* Equinox center: an invisible panel item that puts the item before it in
 * the middle of the monitor.
 *
 * Xfce's panel can only center an item between two expanding separators,
 * that is, between whatever sits left and right of them, so a clock drifts
 * as those groups change width. Put an expanding separator before the
 * clock and this item right after it: this item takes exactly the space
 * that puts the clock's center at the monitor's center.
 *
 * It works from its own right edge, where the items after it begin. The
 * separator before the clock fills whatever the panel has left over, so
 * that edge depends only on the items after this one, never on its own
 * size or on anything before the clock. Window buttons coming and going on
 * a workspace switch change only the separator, so the clock can't move.
 * (Sized from the left instead, it had to follow the window buttons, one
 * frame late, and the clock jumped.) If the items after it grow, it
 * measures again during that same layout. */

#include <gtk/gtk.h>
#include <libxfce4panel/libxfce4panel.h>

typedef struct
{
  XfcePanelPlugin *plugin;
  GtkWidget *space;
  GtkWidget *watched; /* the item before, whose size we follow */
  gint size;
  gboolean measuring;
  guint idle_id;
} EquinoxCenter;

static void queue_measure (EquinoxCenter *ec);
static void measure_now (EquinoxCenter *ec);

static GtkWidget *
previous_item (EquinoxCenter *ec)
{
  GtkWidget *parent = gtk_widget_get_parent (GTK_WIDGET (ec->plugin));
  GtkWidget *previous = NULL;
  GList *children, *self;

  if (parent == NULL || !GTK_IS_CONTAINER (parent))
    return NULL;
  children = gtk_container_get_children (GTK_CONTAINER (parent));
  self = g_list_find (children, ec->plugin);
  if (self != NULL && self->prev != NULL)
    previous = self->prev->data;
  g_list_free (children);
  return previous;
}

static void
watch (EquinoxCenter *ec,
       GtkWidget *item)
{
  if (item == ec->watched)
    return;
  if (ec->watched != NULL)
    g_signal_handlers_disconnect_by_data (ec->watched, ec);
  ec->watched = item;
  if (item != NULL)
    {
      g_signal_connect_swapped (item, "size-allocate", G_CALLBACK (measure_now), ec);
      g_signal_connect_swapped (item, "destroy", G_CALLBACK (queue_measure), ec);
    }
}

static void
measure_now (EquinoxCenter *ec)
{
  GtkWidget *widget = GTK_WIDGET (ec->plugin);
  GtkWidget *toplevel = gtk_widget_get_toplevel (widget);
  GtkWidget *centered;
  gboolean horizontal = xfce_panel_plugin_get_orientation (ec->plugin) == GTK_ORIENTATION_HORIZONTAL;
  GdkWindow *window;
  GdkRectangle monitor;
  gint x, y, origin_x, origin_y, centered_size, size;

  /* Setting our size re-runs the layout, which allocates us again. */
  if (ec->measuring)
    return;
  ec->measuring = TRUE;

  centered = previous_item (ec);
  watch (ec, centered);
  if (centered == NULL || !gtk_widget_get_realized (toplevel)
      || !gtk_widget_translate_coordinates (widget, toplevel, 0, 0, &x, &y))
    {
      ec->measuring = FALSE;
      return;
    }

  window = gtk_widget_get_window (toplevel);
  gdk_window_get_origin (window, &origin_x, &origin_y);
  gdk_monitor_get_geometry (gdk_display_get_monitor_at_window (gtk_widget_get_display (widget), window),
                            &monitor);

  /* The centered item ends where this item starts, and this item ends at
   * its current right edge, which doesn't depend on its size. */
  if (horizontal)
    {
      gint end = origin_x + x + gtk_widget_get_allocated_width (widget);

      gtk_widget_get_preferred_width (centered, NULL, &centered_size);
      size = end - (monitor.x + monitor.width / 2) - centered_size / 2;
    }
  else
    {
      gint end = origin_y + y + gtk_widget_get_allocated_height (widget);

      gtk_widget_get_preferred_height (centered, NULL, &centered_size);
      size = end - (monitor.y + monitor.height / 2) - centered_size / 2;
    }
  size = MAX (0, size);

  if (size != ec->size)
    {
      ec->size = size;
      gtk_widget_set_size_request (ec->space, horizontal ? size : -1, horizontal ? -1 : size);
    }
  ec->measuring = FALSE;
}

static gboolean
measure (gpointer data)
{
  EquinoxCenter *ec = data;

  ec->idle_id = 0;
  measure_now (ec);
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

  g_signal_connect_swapped (plugin, "size-allocate", G_CALLBACK (measure_now), ec);
  g_signal_connect_swapped (plugin, "screen-position-changed", G_CALLBACK (queue_measure), ec);
  g_signal_connect_swapped (plugin, "orientation-changed", G_CALLBACK (queue_measure), ec);
  g_signal_connect (plugin, "hierarchy-changed", G_CALLBACK (hierarchy_changed), ec);
  g_signal_connect (plugin, "free-data", G_CALLBACK (free_data), ec);
  hierarchy_changed (GTK_WIDGET (plugin), NULL, ec);
}

XFCE_PANEL_PLUGIN_REGISTER (construct);
