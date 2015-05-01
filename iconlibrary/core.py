#!/usr/bin/env python
# Filename: core.py


from __future__ import print_function

import export
import gobject
import gtk
import gui
import os
import sqlite3
import store
import sys
import threading

import pygtk
pygtk.require('2.0')

__license__ = 'LGPLv3'
__copyright__ = 'Matthew McGowan, 2009'
__author__ = 'Matthew McGowan <matthew.joseph.mcgowan@gmail.com>'


# Initializing the gtk's thread engine
gtk.gdk.threads_init()

# print colors
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'


class IconLibraryController:
    """The App class is the controller for this application."""
    def __init__(self):
        self.Theme = IconTheme()
        self.Gui = gui.IconLibraryGui()
        self.Gui.make_greeter(self.Theme, self.init_database)
        self.Gui.root.show_all()
        self.Gui.root.connect('destroy', self.destroy_cb)
        return

    def init_database(self, Theme, progressbar):
        """
        Function sets initial theme and builds initial theme database.
        On completion initialises browser gui.
        """

        self.IconDB = IconDatabase()

        dbbuilder = threading.Thread(
            target=self.IconDB.create,
            args=(Theme, progressbar)
            )
        dbbuilder.start()

        gobject.timeout_add(
            200,
            self.thread_completed,
            dbbuilder,
            self.init_browser
            )
        return

    def init_browser(self):
        """Function initialises browser gui."""

        self.IconDB.load()
        self.Store = store.InfoModel()
        self.Display = DisplayModel()

        Display = self.Display
        Display.make_filters_view(self.Store.contexts_model)
        Display.make_icon_set_view(self.Store.icon_rows_model)

        self.cswatch_focus = None

        self.Gui.make_browser(
            self,
            self.Theme,
            self.IconDB,
            self.Store,
            Display
            )

        self.Store.contexts_model_set_info(self.Theme)
        self.Gui.root.show_all()
        self.search_and_display(self.Gui.text_entry)
        return

    def start_theme_change(self, Theme, Dialog, new_theme, progress):
        """
        Function sets new theme and builds new theme database.
        Calls finish_theme_change on database completion.
        """

        Theme.set_theme(new_theme)

        dbbuilder = threading.Thread(
            target=self.IconDB.create,
            args=(Theme, progress)
            )
        dbbuilder.start()

        gobject.timeout_add(
            200,
            self.thread_completed,
            dbbuilder,
            self.finish_theme_change,
            (Theme, Dialog)
            )
        return

    def finish_theme_change(self, Theme, Dialog):
        """Alters Gui elements to reflect theme change completion."""

        Dialog.dialog.destroy()
        del Dialog

        self.IconDB.load()
        Gui = self.Gui

        Gui.avatar_button.set_image(
            Gui.make_avatar(Theme)
            )

        Gui.header_label.set_markup(
            Gui.make_header(Theme)
            )

        self.Store.contexts_model_set_info(Theme)
        self.search_and_display(self.Gui.text_entry)
        return

    def thread_completed(self, thread, func, args=None):
        """
        Function checks if a thread is alive. If not runs a callback.
        Use in conjunction with a gobject timeout.
        """

        if thread.isAlive():
            return True
        else:
            if args:
                func(*args)
            else:
                func()
            return False

    def search_and_display(self, entry):
        """
        Function performs IconDB search then displays results in treeview.
        """

        IconDB = self.IconDB
        term, results = IconDB.search(entry)

        self.Gui.set_feedback(
            IconDB,
            term,
            len(results)
            )

        self.Store.icon_rows_model.clear()
        self.Store.icon_rows_model_set_info(
            results,
            IconDB.pixbuf_cache
            )
        return

    def change_bg_color_cb(self, successor):
        """
        ColorSwatch clicked callback. Modify's treeview background color.
        """

        cs = self.cswatch_focus
        if cs != successor:
            cs.relinquish_focus()
            self.Display.icon_set_view_modify_colors(successor.get_colors())
        self.cswatch_focus = successor
        return

    def change_theme_cb(self, avatar_button):
        """
        Theme change button clicked callback. Begins theme change process.
        """

        import dialogs
        Theme = self.Theme

        Dialog = dialogs.ThemeChangeDialog(self.Gui.root)
        new_theme, progress = Dialog.run(Theme)

        if new_theme:
            self.start_theme_change(
                Theme,
                Dialog,
                new_theme,
                progress
                )
        return

    def standard_filter_cb(self, checkbutton):
        """
        Standard filter checkbutton toggled callback. Sets standard filter.
        """

        self.IconDB.set_standard_filter(checkbutton.get_active())
        self.search_and_display(self.Gui.text_entry)
        return

    def inherited_filter_cb(self, checkbutton):
        self.IconDB.set_inherited_filter(checkbutton.get_active())
        self.search_and_display(self.Gui.text_entry)
        return False

    def row_activated_2click_cb(self, treeview, path, column):
        iconset_data = self.IconDB.results[path[0]]
        self.edit_iconset_cb(None, iconset_data)
        return

    def row_activated_cb(self, treeview, event):
        """Iconset (icon_set_view) treeview row activated callback."""

        if event.button == 3:
            import dialogs

            Dialog = dialogs.IconSetPopupDialog()
            popup, menuitems = Dialog.make()

            Dialog.run(
                self,
                popup,
                menuitems,
                treeview,
                event
                )
        return

    def edit_iconset_cb(self, action, iconset_data):
        """Callback that starts the iconset editor for selected iconset."""

        import editor

        Editor = editor.IconSetEditorDialog(self.Gui.root)
        Editor.run(
            self.Theme,
            self.IconDB,
            self.Store,
            iconset_data
            )
        return

    def jump_to_icon_cb(self, action, results):
        """Jump to clicked callback. Jumps to icon symlink target."""

        path = self.Theme.lookup_icon(results[0], 22, 0).get_filename()
        rpath = os.path.realpath(path)
        rname = os.path.splitext(os.path.split(rpath)[1])[0]
        found = False

        Display = self.Display

        for row in self.Store.icon_rows_model:
            if row[0][0] == '<':
                if row[0][3:-4] == rname:
                    Display.icon_set_view.set_cursor(row.path)
                    found = True
                    break
            elif row[0] == rname:
                Display.icon_set_view.set_cursor(row.path)
                found = True
                break
        if not found:
            d = gtk.MessageDialog(
                parent=self.Gui.root,
                flags=(gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT),
                type=gtk.MESSAGE_WARNING,
                buttons=gtk.BUTTONS_CLOSE
                )

            m = '<big><b><span foreground="#FF09FF">%s</span> was not found</b></big>'
            d.set_markup(m % rname)

            s = 'The icon set targeted by this symlink was not discovered.'
            s += '\n\nIf you have filtered the icons by context or word, '
            s += 'then the icon set is probably not in the current list. '
            s += 'In which case, try the action again with an un-filtered view.'

            d.format_secondary_text(s)

            d.set_image(gtk.image_new_from_stock(gtk.STOCK_DIALOG_WARNING,
                                                 gtk.ICON_SIZE_DIALOG))

            d.image.show()
            d.run()
            d.destroy()
        return

    def context_filter_cb(self, combo):
        """Filter search results by selected context."""

        ctx = combo.get_active_text()  # treeview.get_selection().get_selected()
        # print(combo.get_active())
        # if combo.get_active() == 0: ctx = ''
        self.IconDB.set_context_filter(ctx)
        self.search_and_display(self.Gui.text_entry)
        return

    def export(self, button):
        export.HTML(self.Store, self.Theme)
        return

    def search_entry_cb(self, search_entry, text):
        self.search_and_display(text)
        return

    def search_button_cb(self, *kw):
        """Search button clicked callback. Does search."""

        self.search_and_display(self.Gui.text_entry)
        return

    def clear_button_cb(self, *kw):
        """Clear button clicked callback. Does empty search."""

        self.Gui.text_entry.set_text('')
        self.search_and_display('')
        return

    def destroy_cb(self, *kw):
        """Destroy callback to shutdown the app."""

        gtk.main_quit()
        return

    def run(self):
        """Start the app."""

        gtk.main()
        return


class IconTheme(gtk.IconTheme):
    def __init__(self):
        gtk.IconTheme.__init__(self)
        self.info = None
        self.all_themes = None
        self.default = gtk.settings_get_default().get_property('gtk-icon-theme-name')
        return

    def list_themes(self):
        if not self.all_themes:
            all_themes = []
            for path in self.get_search_path():
                all_themes += self.find_any_themes(path)
            self.all_themes = all_themes
            return all_themes
        else:
            return self.all_themes

    def read_comment(self, index_path):
        f = open(index_path, 'r')
        comment = None
        for line in f:
            if line.startswith('Comment='):
                comment = line.strip()[8:]
                break
        f.close()
        return comment

    def read_name(self, index_path):
        f = open(index_path, 'r')
        name = None
        for line in f:
            if line.startswith('Name='):
                name = line.strip()[5:]
                break
        f.close()
        return name

    def find_any_themes(self, inpath):
        themes = []
        for root, dirs, files in os.walk(inpath):
            index_path = os.path.join(root, 'index.theme')
            if os.path.exists(index_path) and not \
                    os.path.exists(os.path.join(root, 'cursor.theme')):
                theme = os.path.split(root)[1]
                if theme != 'default':
                    name = self.read_name(index_path)
                    themes.append((theme, name, index_path))
        return themes

    def set_theme(self, theme):
        self.info = theme
        self.set_custom_theme(theme[0])
        return


class IconDatabase:
    def __init__(self):
        """Both the DB and pixbuf cache are filled."""

        self.conn = None
        self.cursor = None
        self.length = 0
        self.model = None
        self.results = None
        self.standard_only = False
        self.inherited_only = False
        self.ctx_filter = 'All Contexts'
        return

    def new_conn(self):
        create_table = True
        if os.path.exists('/tmp/icondb.sqlite3'):
            create_table = False

        conn = sqlite3.connect('/tmp/icondb.sqlite3')
        cursor = conn.cursor()

        if create_table:
            cursor.execute(
                'CREATE TABLE theme ( \
                    key TEXT, \
                    name TEXT, \
                    context TEXT, \
                    standard BOOLEAN, \
                    scalable BOOLEAN, \
                    inherited BOOLEAN, \
                    inherited_name TEXT \
                    )'
                )
        else:
            cursor.execute('DELETE FROM theme')

        return conn, cursor

    def create(self, Theme, progressbar=None):
        from standards import StandardIconNamingSpec
        spec = StandardIconNamingSpec()

        conn, cursor = self.new_conn()
        i, j = 0, 0

        self.pixbuf_cache = {}
        contexts = Theme.list_contexts()
        total = float(len(contexts))

        for ctx in contexts:
            for ico in Theme.list_icons(ctx):

                k, inherited = self.iconset_key(Theme, ico)
                tn = Theme.info[0]

                if self.pixbuf_cache_append(Theme, ico, k, ctx):
                    scalable = -1 in Theme.get_icon_sizes(ico)
                    standard = spec.isstandard(ctx, ico)
                    cursor.execute(
                        'INSERT INTO theme VALUES (?,?,?,?,?,?,?)',
                        (k, ico, ctx, standard, scalable, inherited == tn, inherited)
                        )
                    i += 1
                else:
                    print('Error: %s - Failed to load a pixbuf. Skipping...' % ico, file=sys.stderr)

            j += 1

            if progressbar:
                gtk.gdk.threads_enter()
                progressbar.set_fraction(j / total)
                progressbar.set_text('Loading %s...' % ctx)
                gtk.gdk.threads_leave()

        conn.commit()
        cursor.close()
        self.length = i
        return

    def load(self):
        if self.cursor is not None:
            self.cursor.close()
            del self.conn, self.cursor
        self.conn = sqlite3.connect('/tmp/icondb.sqlite3')
        self.cursor = self.conn.cursor()
        return

    def iconset_key(self, Theme, name):
        p = Theme.lookup_icon(name, 24, 0).get_filename()
        p = os.path.realpath(p)
        k = os.path.splitext(os.path.split(p)[1])[0]
        return k, p.split('/')[4]  # return key and inheritance

    def pixbuf_cache_append(self, Theme, name, k, ctx):
        try:
            if not self.pixbuf_cache.has_key(k):
                if ctx != 'Animations':
                    self.pixbuf_cache[k] = self.load_icons(Theme, name)
                else:
                    self.pixbuf_cache[k] = self.load_animations(Theme, name)
        except Exception as e:
            print(e, file=sys.stderr)
            return False
        return True

    def load_icons(self, Theme, name):
        pbs = []
        for size in (16, 22, 32):
            pbs.append(Theme.load_icon(name, size, 0))
        return pbs

    def load_animations(self, Theme, name):
        pbs = []
        for size in (16, 22, 32):
            pb = Theme.load_icon(name, size, 0)
            if pb.get_width() >= 2*size:
                pbs.append(pb.subpixbuf(size, 0, size, size))
            else:
                pbs.append(pb.subpixbuf(0, 0, size, size))
        return pbs

    def search(self, term):
        if len(threading.enumerate()) == 1:
            if type(term) != str:
                term = term.get_text()

            query = self.make_query(term)
            self.cursor.execute(query)
            self.results = self.cursor.fetchall()
        return term, self.results

    def make_query(self, term):
        if term != '':
            qterm = '"%' + term + '%"'
            query = 'SELECT * FROM theme WHERE name LIKE %s' % qterm
            if self.standard_only:
                query += ' AND standard'
            if self.inherited_only:
                query += ' AND inherited'
            if self.ctx_filter != 'All Contexts':
                query += ' AND context="%s" ORDER BY name' % self.ctx_filter
            else:
                query += ' ORDER BY context, name'
        else:
            query = 'SELECT * FROM theme'
            if self.standard_only:
                query += ' WHERE standard'
            if self.inherited_only:
                if self.standard_only:
                    query += ' AND inherited'
                else:
                    query += ' WHERE inherited'
            if self.ctx_filter != 'All Contexts':
                if self.standard_only or self.inherited_only:
                    query += ' AND context="%s" ORDER BY name' % self.ctx_filter
                else:
                    query += ' WHERE context="%s" ORDER BY name' % self.ctx_filter
            else:
                query += ' ORDER BY context, name'
        return query

    def set_context_filter(self, context):
        """Sets the context filter string."""
        self.ctx_filter = context
        return

    def set_standard_filter(self, standard_only):
        """Sets whether to filter based on standard names only."""
        self.standard_only = standard_only
        return

    def set_inherited_filter(self, inherited_only):
        self.inherited_only = inherited_only
        return

    def get_context_filter(self):
        """Returns the current context filter."""
        return self.ctx_filter

    def get_length(self):
        """Returns the total number of icons in the IconDB."""
        return self.length


class DisplayModel:
    def make_filters_view(self, contexts_model):
        """Make the view for the context filter list store."""

        self.filters_view = gtk.ComboBox()  # gtk.TreeView(contexts_model)
        self.filters_view.set_model(contexts_model)

        cell = gtk.CellRendererText()
        self.filters_view.pack_start(cell, True)
        self.filters_view.add_attribute(cell, 'text', 0)
        # context_item_renderer.set_property('xpad', 5)

        # context_filter_column = gtk.TreeViewColumn('Context Filter', context_item_renderer, markup=0)
        # self.filters_view.append_column(context_filter_column)

        # self.filters_view.set_tooltip_column(1)
        return self.filters_view

    def filters_view_query_tooltip_cb(self, *args):
        print(args)
        return

    def make_icon_set_view(self, icon_rows_model):
        """Make the main view for the icon view list store."""

        import pango

        self.icon_set_view = gtk.TreeView(icon_rows_model)
        self.icon_set_view.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        # setup the icon name cell-renderer
        self.name_column_renderer = gtk.CellRendererText()
        self.name_column_renderer.set_property('xpad', 5)
        self.name_column_renderer.set_property('wrap-width', 225)
        self.name_column_renderer.set_property('wrap-mode', pango.WRAP_WORD)

        self.context_column_renderer = gtk.CellRendererText()
        self.context_column_renderer.set_property('wrap-width', 125)
        self.context_column_renderer.set_property('wrap-mode', pango.WRAP_WORD)

        # setup the icon pixbuf cell-renderers
        self.icon_renderers = []
        for i in range(0, 3):
            r = gtk.CellRendererPixbuf()
            r.set_property('width', 56)
            r.set_property('height', 48)
            self.icon_renderers.append(r)

        # setup the icon islink cell-render
        self.notes_column_renderer = gtk.CellRendererText()
        self.notes_column_renderer.set_property('xpad', 5)
        self.notes_column_renderer.set_property('size-points', 7)
        self.notes_column_renderer.set_property(
            'foreground',
            self.icon_set_view.get_style().text[gtk.STATE_INSENSITIVE].to_string()
            )

        # connect columns to columns in icon view model
        name_column = gtk.TreeViewColumn(
            'Name', self.name_column_renderer, markup=0)

        context_column = gtk.TreeViewColumn(
            'Context', self.context_column_renderer, text=1)

        graphics_column = gtk.TreeViewColumn('Graphics')

        notes_column = gtk.TreeViewColumn(
            'Notes', self.notes_column_renderer, text=5)

        # pack pixbuf cell renderers into 'Graphics' column
        for i, r in enumerate(self.icon_renderers):
            graphics_column.pack_start(r, False)
            graphics_column.set_attributes(r, pixbuf=i + 2)

        # append column to icon view
        for column in name_column, context_column, graphics_column, notes_column:
            self.icon_set_view.append_column(column)

        name_column.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        context_column.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        graphics_column.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)

        return self.icon_set_view

    def icon_set_view_modify_colors(self, colors):
        bg, txt_norm, txt_insens, default = colors
        if default:
            bg_copy = bg
            bg = None
        # text rendereres
        rndrs = self.name_column_renderer, self.context_column_renderer
        for r in rndrs:
            r.set_property('foreground', txt_norm)
            r.set_property('cell-background', bg)

        for r in self.icon_renderers:
            r.set_property('cell-background', bg)
        # notes
        self.notes_column_renderer.set_property('foreground', txt_insens)
        self.notes_column_renderer.set_property('cell-background', bg)
        # base, and redraw
        if default:
            self.icon_set_view.modify_base(gtk.STATE_NORMAL,
                                           gtk.gdk.color_parse(bg_copy))
        else:
            self.icon_set_view.modify_base(gtk.STATE_NORMAL,
                                           gtk.gdk.color_parse(bg))
        return


def main():
    print('\nIcon Library')
    print('Matthew McGowan, 2008-2010\n')
    app = IconLibraryController()
    app.run()
