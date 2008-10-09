#!/usr/bin/env python
# Filename: core.py

__licence__ = "LGPLv3"
__copyright__ = "Matthew McGowan, 2008"
__author__ = "Matthew McGowan <matthew.joseph.mcgowan@gmail.com>"


import pygtk
pygtk.require("2.0")

import os
import gtk
import gobject
import sqlite3
import threading

#Initializing the gtk's thread engine
gtk.gdk.threads_init()


class IconLibraryController:
    """ The App class is the controller for this application """
    def __init__(self):
        self.Theme = IconTheme()
        self.Gui = IconLibraryGui()
        self.Gui.make_greeter(self.Theme, self.init_browser_db)
        self.Gui.root.show_all()
        self.Gui.root.connect("destroy", self.destroy_cb )
        return

    def init_browser_db(self, Theme, progressbar):
        """ Load Treeview models and views and load the icon database.
            When completed load the main gui """
        self.IconDB = IconDatabase()

        dbbuilder = threading.Thread(
            target=self.IconDB.db_create,
            args=(Theme, progressbar)
            )
        dbbuilder.start()

        gobject.timeout_add(
            200,
            self.thread_isalive_checker,
            dbbuilder,
            self.init_browser_gui
            )
        return

    def init_browser_gui(self):
        self.IconDB.db_load()
        self.Store = InfoModel(self.Theme)
        self.Display = DisplayModel()

        self.cswatch_focus = None

        self.Gui.make_browser(
            self,
            self.Theme,
            self.IconDB,
            self.Store,
            self.Display
            )
        self.Gui.root.show_all()

        # fire off an initial search to fill icon view
        self.search_and_display(self.Gui.text_entry)
        return

    def thread_isalive_checker(self, thread, callback, args=None):
        if thread.isAlive():
            return True
        else:
            if args:
                callback( *args )
            else:
                callback()
            return False

    def search_and_display(self, entry):
        IconDB = self.IconDB
        term, results = IconDB.do_search(entry)

        self.Gui.set_feedback(
            IconDB,
            term,
            len(results)
            )

        self.Gui.display_results(
            IconDB,
            results
            )
        return

    def change_bg_color_cb(self, successor):
        cs = self.cswatch_focus
        if cs != successor:
            cs.relinquish_focus()

            self.Display.modify_view2_colors(
                self.Gui.view2,
                successor.get_colors()
                )

        self.cswatch_focus = successor
        return

    def change_theme_cb(self, avatar_button):
        import dialogs

        Gui = self.Gui
        Theme = self.Theme
        Dialog = dialogs.ThemeChangeDialog()
        new_theme = Dialog.run(
            Theme,
            Gui.root
            )

        if new_theme:
            Theme.set_theme(new_theme)
            self.IconDB.db_create(Theme)

            avatar_button.set_image(
                Gui.make_avatar(Theme)
                )

            Gui.header_label.set_markup(
                Gui.make_header(Theme)
                )

            # fire off a search to fill icon view on new theme selection
            self.search_and_display("")
        return

    def standard_filter_cb(self, checkbutton):
        self.IconDB.set_standard_filter( checkbutton.get_active() )
        self.search_and_display(self.Gui.text_entry)
        return

    def v2_row_activated_cb(self, treeview, event):
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

    def edit_iconset_cb(self, action, results):
        import dialogs

        Editor = dialogs.IconSetEditorDialog(
            self.Gui.root,
            self.IconDB.update_pixbuf_cache
            )

        Editor.run(
            self.Theme,
            results
            )
        return

    def jump_to_icon_cb(self, action, results):
        path = self.Theme.lookup_icon(results[0], 22, 0).get_filename()
        rpath = os.path.realpath( path )
        rname = os.path.splitext( os.path.split( rpath )[1] )[0]
        found = False
        Gui = self.Gui

        for row in Gui.model2:
            if row[0][0] == "<":
                if row[0][3:-4] == rname:
                    Gui.view2.set_cursor( row.path )
                    found = True
                    break
            elif row[0] == rname:
                Gui.view2.set_cursor( row.path )
                found = True
                break
        if not found:
            import dialogs

            Dialog = dialogs.TargetNotFoundDialog()
            Dialog.run(
                rname,
                rpath,
                Gui.root
                )
        return

    def context_filter_cb(self, treeview):
        """ Filter search results by the select icon context """
        model, path = treeview.get_selection().get_selected()
        ctx = model[path][0]
        self.IconDB.set_context_filter(ctx)
        self.search_and_display(self.Gui.text_entry)
        return

    def search_entry_cb( self, text_entry):
        self.search_and_display(text_entry)
        return

    def search_button_cb( self, *kw ):
        self.search_and_display(self.Gui.text_entry)
        return

    def clear_button_cb( self, *kw ):
        self.Gui.text_entry.set_text("")
        self.search_and_display("")
        return

    def destroy_cb(self, *kw):
        """ Destroy callback to shutdown the app """
        if len(threading.enumerate()) == 1:
            gtk.main_quit()
        else:
            print threading.enumerate()
        return

    def run(self):
        gtk.main()


class IconLibraryGui:
    def __init__(self):
        # setup the root window
        DefaultTheme = gtk.icon_theme_get_default()

        self.root = gtk.Window(type=gtk.WINDOW_TOPLEVEL)
        self.root.set_default_size(780, 640)
        self.root.set_title( "Icon Library")
        self.root.set_icon_list(
            DefaultTheme.load_icon("gtk-home", 8, 0),
            DefaultTheme.load_icon("gtk-home", 16, 0),
            DefaultTheme.load_icon("gtk-home", 22, 0),
            DefaultTheme.load_icon("gtk-home", 24, 0),
            DefaultTheme.load_icon("gtk-home", 32, 0)
            )
        self.vbox = gtk.VBox()
        self.root.add(self.vbox)
        del DefaultTheme
        return

    def make_greeter(self, Theme, init_db_cb):
        """ Greets the user and offers a range of themes to choose from """
        # list all discoverable themes in a combo box
        theme_sel = gtk.combo_box_new_text()
        theme_sel.set_tooltip_text("Select an icon theme")
        i, active = 0, 0
        themes = Theme.list_themes()
        themes.sort()
        for theme, name, p in themes:
            name = name or "Unnamed"
            if theme == Theme.default:
                name += " (default)"
                active = i
            theme_sel.append_text(name)
            i += 1
        theme_sel.set_active(active)

        header = gtk.Label()
        header.set_justify(gtk.JUSTIFY_CENTER)
        header.set_text("Select the icon theme you would like to view")

        go = gtk.Button()
        go.set_size_request(33, -1)
        go.set_image(
            gtk.image_new_from_icon_name("dialog-ok", gtk.ICON_SIZE_SMALL_TOOLBAR)
            )

        greeter_main_align = gtk.Alignment(xalign=0.5, yalign=0.5)
        greeter_vbox = gtk.VBox()
        greeter_hbox = gtk.HBox()

        greeter_hbox.pack_start(theme_sel, False)
        greeter_hbox.pack_start(go, False)

        greeter_vbox.pack_start(header)
        greeter_vbox.pack_start(greeter_hbox, padding=15)

        greeter_main_align.add(greeter_vbox)
        self.vbox.add(greeter_main_align)

        go.connect(
            "clicked",
            self.loading_cb,
            Theme,
            header,
            themes,
            theme_sel,
            greeter_vbox,
            init_db_cb
            )
        return

    def make_browser(self, Controller, Theme, IconDB, Store, Display):
        vbox = self.vbox

        # remove greeter widgets
        for child in self.vbox.get_children():
            self.vbox.remove(child)
            child.destroy()
            del child

        self.setup_top_toolbar(
            Controller,
            Theme,
            vbox
            )

        scrollers = self.setup_scrolled_panels(vbox)

        views = self.setup_listviews(
            Controller,
            Store,
            Display
            )

        scrollers[0].add(views[0])
        scrollers[1].add(views[1])

        btm_hboxes = self.setup_bottom_toolbar(vbox)

        self.setup_feedback_label(
            IconDB,
            btm_hboxes[1]
            )

        self.setup_color_swatches(Controller, btm_hboxes[2])
        return

    def setup_top_toolbar(self, Controller, Theme, vbox):
        self.avatar_button = gtk.Button()
        self.avatar_button.set_relief(gtk.RELIEF_NONE)
        self.avatar_button.set_tooltip_text("Switch theme")
        self.avatar_button.set_image( self.make_avatar(Theme) )

        self.header_label = gtk.Label()
        self.header_label.set_markup( self.make_header(Theme) )

        self.standard_check = gtk.CheckButton(
            label="Standard icons only",
            use_underline=False
            )
        self.standard_check.set_tooltip_text(
            "Only show icons that conform to the\nfreedesktop.org Icon Naming Specification"
            )

        self.text_entry = gtk.Entry(60)

        srch_btn = gtk.Button("Find")
        srch_btn.set_size_request(80, -1)
        srch_btn.set_image(
            gtk.image_new_from_stock( gtk.STOCK_FIND, gtk.ICON_SIZE_MENU )
            )

        clr_btn = gtk.Button()
        clr_btn.set_tooltip_text("Clear")
        clr_btn.set_image(
            gtk.image_new_from_stock( gtk.STOCK_CLEAR, gtk.ICON_SIZE_MENU )
            )

        srch_vbox = gtk.VBox()
        srch_align = gtk.Alignment(0.5, 0.5)
        srch_align.add(srch_vbox)
        srch_vbox.pack_start(srch_btn, False)

        clr_vbox = gtk.VBox()
        clr_align = gtk.Alignment(0.5, 0.5)
        clr_align.add(clr_vbox)
        clr_vbox.pack_start(clr_btn)

        tbar_hbox = gtk.HBox()

        tbar_hbox.pack_start(self.avatar_button, False, padding=5)
        tbar_hbox.pack_start(self.header_label, False)

        tbar_hbox.pack_end(srch_align, False)
        tbar_hbox.pack_end(clr_align, False)
        tbar_hbox.pack_end(self.text_entry, False)
        tbar_hbox.pack_end(self.standard_check, False, padding=5)

        vbox.pack_start(tbar_hbox, False, padding=5)

        self.avatar_button.connect(
            "clicked",
            Controller.change_theme_cb
            )

        self.standard_check.connect(
            "toggled",
            Controller.standard_filter_cb
            )

        self.text_entry.connect(
            "activate",
            Controller.search_entry_cb
            )

        srch_btn.connect(
            "clicked",
            Controller.search_button_cb
            )

        clr_btn.connect(
            "clicked",
            Controller.clear_button_cb
            )
        return

    def setup_scrolled_panels(self, vbox):
        hpaned = gtk.HPaned()
        hpaned.set_position(135)

        scroller1 = gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
        scroller1.set_policy(gtk.POLICY_ALWAYS, gtk.POLICY_AUTOMATIC)

        scroller2 = gtk.ScrolledWindow(hadjustment=None, vadjustment=None)

        hpaned.pack1(scroller1)
        hpaned.pack2(scroller2)

        vbox.pack_start(hpaned)
        return (scroller1, scroller2)

    def setup_bottom_toolbar(self, vbox):
        btm_hbox = gtk.HBox()
        btm_hbox.set_homogeneous(True)

        btm_hbox0 = gtk.HBox()
        btm_hbox1 = gtk.HBox()
        btm_hbox2 = gtk.HBox()

        btm_hbox.add(btm_hbox0)
        btm_hbox.add(btm_hbox1)
        btm_hbox.add(btm_hbox2)

        vbox.pack_end(btm_hbox, False)
        return  (btm_hbox0, btm_hbox1, btm_hbox2)

    def setup_feedback_label(self, IconDB, btm_hbox):
        self.feedback_note = gtk.Label()
        self.feedback_note.set_alignment(0.5, 0.5)
        self.feedback_note.set_size_request(-1, 24)

        self.feedback_note.set_markup(
            "Displaying <b>%s</b> icons" % ( IconDB.get_length() )
            )

        btm_hbox.pack_end(self.feedback_note)
        return

    def setup_listviews( self, Controller, Store, Display ):
        self.model1 = Store.get_model1()
        self.view1 = Display.make_view1(self.model1)
        self.view1.set_cursor(0)

        self.model2 = Store.get_model2()
        self.view2 = Display.make_view2(self.model2)

        self.view1.connect("cursor-changed", Controller.context_filter_cb)
        self.view2.connect("button-release-event", Controller.v2_row_activated_cb)
        return (self.view1, self.view2)

    def setup_color_swatches(self, Controller, btm_hbox):
        import custom_widgets

        style = self.root.get_style()
        cb = Controller.change_bg_color_cb

        color_sel0 = custom_widgets.ColorSwatch(
            cb,
            style,
            tip="Default",
            default=True
            )

        color_sel1 = custom_widgets.ColorSwatch(
            cb,
            style,
            bg="#FFFFFF",
            tip="White"
            )

        color_sel2 = custom_widgets.ColorSwatch(
            cb,
            style,
            bg="#9C9C9C",
            txt2="#525252",
            tip="Grey"
            )

        color_sel3 = custom_widgets.ColorSwatch(
            cb,
            style,
            bg="#525252",
            txt1="#E6E6E6",
            txt2="#9E9E9E",
            tip="Dark grey"
            )

        Controller.cswatch_focus = color_sel0.give_focus()

        btm_hbox.pack_end(color_sel3, False)
        btm_hbox.pack_end(color_sel2, False)
        btm_hbox.pack_end(color_sel1, False)
        btm_hbox.pack_end(color_sel0, False)
        btm_hbox.show_all()
        return

    def make_header(self, Theme):
        name = Theme.info[1] or "Unnamed"
        comment = Theme.read_comment( Theme.info[2] ) or "No comment"
        markup = "<b>%s</b>\n<span size='small'>%s</span>"
        s = markup % (name, comment)
        return s

    def make_avatar(self, Theme):
        try:
            return gtk.image_new_from_pixbuf( Theme.load_icon("folder", 32, 0) )
        except:
            return gtk.image_new_from_icon_name("folder", gtk.ICON_SIZE_DND)

    def display_results(self, IconDB, results):
        self.model2.clear()

        displayer = ListDisplayer(
            results,
            IconDB.pb_cache,
            self.model2
            )
        displayer.start()
        return

    def set_feedback(self, IconDB, term, num_of_results):
        """ Displays basic search stats in the GUI """
        std = ""
        if IconDB.standard_only:
            std = "standard "
        if term == "":
            s = "<b>%s</b> %sicons in <b>%s</b>" % (num_of_results, std, IconDB.ctx_filter)
        else:
            s = "<b>%s</b> %sresults for <b>%s</b> in <b>%s</b>"
            s = s % (num_of_results, std, term, IconDB.ctx_filter)
        self.feedback_note.set_markup(s)
        return

    def loading_cb(self, go, Theme, header, themes, theme_sel, greeter_vbox, init_db_cb):
        """ Begin loading the theme chosen at the greeter gui """
        Theme.set_theme( themes[theme_sel.get_active()] )
        theme_sel.set_sensitive(False)
        go.set_sensitive(False)

        s = "Loading <b>%s</b>\nThis may take several moments" % Theme.info[1]
        header.set_markup(s)

        progress = gtk.ProgressBar()
        greeter_vbox.pack_end( progress )
        progress.show()

        init_db_cb( Theme, progress )
        return


class ListDisplayer(threading.Thread):
    """ Renders cells in a thread to minimise GUI unresponsiveness """
    def __init__(self, results, pb_cache, model):
        """ Setup threading """
        threading.Thread.__init__(self)
        self.finished = threading.Event()
        self.results = results
        self.pb_cache = pb_cache
        self.model = model
        return

    def run(self):
        """ Add content to cells """
        while not self.finished.isSet():
            for key, ico, context, standard, scalable in self.results:
                pb0 = self.pb_cache[key][0]
                pb1 = self.pb_cache[key][1]
                pb2 = self.pb_cache[key][2]

                notes = None
                if key != ico:
                    notes = "Symlink"
                if not scalable:
                    if not notes:
                        notes = "Fixed Only"
                    else:
                        notes += ", Fixed Only"
                if standard:
                    ico = "<b>%s</b>" % ico

                gtk.gdk.threads_enter()
                self.model.append( (ico, context, pb0, pb1, pb2, notes) )
                gtk.gdk.threads_leave()
            self.finished.set()
        return


class IconTheme(gtk.IconTheme):
    def __init__(self):
        gtk.IconTheme.__init__(self)
        self.info = None
        self.all_themes = None
        self.default = gtk.settings_get_default().get_property("gtk-icon-theme-name")
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
            if line.startswith("Comment="):
                comment = line.strip()[8:]
                break
        f.close()
        return comment

    def read_name(self, index_path):
        f = open(index_path, 'r')
        name = None
        for line in f:
            if line.startswith("Name="):
                name = line.strip()[5:]
                break
        f.close()
        return name

    def find_any_themes(self, inpath):
        themes = []
        for root, dirs, files in os.walk(inpath):
            index_path = os.path.join(root, "index.theme")
            if os.path.exists(index_path) \
                and not os.path.exists( os.path.join(root, "cursor.theme") ):
                theme = os.path.split(root)[1]
                if theme != "default":
                    name = self.read_name(index_path)
                    themes.append((theme, name, index_path))
        return themes

    def set_theme(self, theme):
        self.info = theme
        self.set_custom_theme(theme[0])
        return


class IconDatabase:
    def __init__(self):
        """ Both the DB and pixbuf cache are filled. """
        self.length = 0
        self.model = None
        self.results = None
        self.standard_only = False
        self.ctx_filter = "<b>All Contexts</b>"
        return

    def db_establish_new_connection(self):
        create_table = True
        if os.path.exists( "/tmp/icondb.sqlite3" ):
            create_table = False

        conn = sqlite3.connect("/tmp/icondb.sqlite3")
        cursor = conn.cursor()

        if create_table:
            cursor.execute(
                "CREATE TABLE theme ( \
                    key TEXT, \
                    name TEXT, \
                    context TEXT, \
                    standard BOOLEAN, \
                    scalable BOOLEAN \
                    )"
                )
        else:
            cursor.execute("DELETE FROM theme")

        return conn, cursor

    def db_create(self, Theme, progressbar=None):
        import standards
        NamingSpec = standards.StandardIconNamingSpec()
        conn, cursor = self.db_establish_new_connection()
        i, j = 0, 0

        self.pb_cache = {}
        contexts = Theme.list_contexts()
        total = float( len( contexts ) )

        for ctx in contexts:
            for ico in Theme.list_icons(ctx):
                error = False

                try:
                    k = Theme.lookup_icon(ico, 22, 0).get_filename()
                    k = os.path.realpath( k )
                    k = os.path.splitext( os.path.split(k)[1] )[0]
                    if not self.pb_cache.has_key(k):
                        pb16 = Theme.load_icon( ico, 16, 0 )
                        pb24 = Theme.load_icon( ico, 24, 0 )
                        pb32 = Theme.load_icon( ico, 32, 0 )
                        self.pb_cache[k] = (pb16, pb24, pb32)
                except:
                    error = True
                    print "Error loading icon %s, skipping..." % ico

                if not error:
                    scalable = -1 in Theme.get_icon_sizes(ico)
                    standard = NamingSpec.isstandard(ctx, ico)
                    cursor.execute(
                        "INSERT INTO theme VALUES (?,?,?,?,?)",
                        (k, ico, ctx, standard, scalable)
                        )
                    i += 1
            j += 1
            if progressbar:
                gtk.gdk.threads_enter()
                progressbar.set_fraction( j / total )
                gtk.gdk.threads_leave()

        conn.commit()
        cursor.close()
        self.length = i
        return

    def db_load( self ):
        self.conn = sqlite3.connect("/tmp/icondb.sqlite3")
        self.cursor = self.conn.cursor()
        return

    def do_search(self, entry, mode="like"):
        if len(threading.enumerate()) == 1:
            if type( entry ) != str:
                term = entry.get_text()
            if mode == "like":
                query = self.make_filter_query(term)

            self.cursor.execute(query)
            self.results = self.cursor.fetchall()
        return term, self.results

    def make_filter_query( self, term ):
        if term != "":
            qterm = "\"%" + term + "%\""
            query = "SELECT * FROM theme WHERE name LIKE %s" % qterm
            if self.standard_only:
                query += " AND standard"
            if self.ctx_filter != "<b>All Contexts</b>":
                query += " AND context=\"%s\" ORDER BY name" % self.ctx_filter
            else:
                query += " ORDER BY context, name"
        else:
            query = "SELECT * FROM theme"
            if self.standard_only:
                query += " WHERE standard"
            if self.ctx_filter != "<b>All Contexts</b>":
                if self.standard_only:
                    query += " AND context=\"%s\" ORDER BY name" % self.ctx_filter
                else:
                    query += " WHERE context=\"%s\" ORDER BY name" % self.ctx_filter
            else:
                query += " ORDER BY context, name"
        return query

    def update_pixbuf_cache( self, k, index, pixbuf ):
        pb_list = list( self.pb_cache[k] )
        pb_list[index] = pixbuf
        self.pb_cache[k] = tuple( pb_list )
        return

    def set_context_filter(self, context):
        """ Sets the context filter string """
        self.ctx_filter = context
        return

    def set_standard_filter(self, standard_only):
        """ Sets whether to filter based on standard names only """
        self.standard_only = standard_only
        return

    def get_context_filter(self):
        """ Returns the current context filter """
        return self.ctx_filter

    def get_length(self):
        """ Returns the total number of icons in the IconDB """
        return self.length


class InfoModel:
    """ The model class holds the information we want to display
        in both the context filter and the main icon view """
    def __init__(self, Theme):
        """ Create two list store.  One for the context filter and one for the main
            icon view.  The context filter list store is filled, while the main view
            list store is not. """
        self.list_store1 = gtk.ListStore( str )
        self.list_store1.append( ("<b>All Contexts</b>",) )
        ctxs = list( Theme.list_contexts() )
        ctxs.sort()
        for ctx in ctxs:
            self.list_store1.append( (ctx,) )

        self.list_store2 = gtk.ListStore( str,
                                          str,
                                          gtk.gdk.Pixbuf,
                                          gtk.gdk.Pixbuf,
                                          gtk.gdk.Pixbuf,
                                          str
                                          )
        return

    def get_model1(self):
       """ Returns the model """
       return self.list_store1

    def get_model2(self):
       """ Returns the model """
       return self.list_store2


class DisplayModel:
    """ Displays the Info_Model model in a view """
    def make_view1(self, model):
        """ Make the view for the context filter list store """
        view1 = gtk.TreeView(model)
        renderer10 = gtk.CellRendererText()
        renderer10.set_property("xpad", 5)

        column10 = gtk.TreeViewColumn("Context Filter", renderer10, markup=0)

        view1.append_column(column10)
        return view1

    def make_view2(self, model):
        """ Make the main view for the icon view list store """
        import pango

        view2 = gtk.TreeView(model)
        view2.set_events( gtk.gdk.BUTTON_PRESS_MASK )
        # setup the icon name cell-renderer
        self.renderer20 = gtk.CellRendererText()
        self.renderer20.set_property("xpad", 5)
        self.renderer20.set_property("wrap-width", 225)
        self.renderer20.set_property("wrap-mode", pango.WRAP_WORD)

        self.renderer21 = gtk.CellRendererText()
        self.renderer21.set_property("wrap-width", 125)
        self.renderer21.set_property("wrap-mode", pango.WRAP_WORD)

        # Setup the icon pixbuf cell-renderers
        self.renderer22 = gtk.CellRendererPixbuf()
        self.renderer23 = gtk.CellRendererPixbuf()
        self.renderer24 = gtk.CellRendererPixbuf()

        self.renderer22.set_property('width', 56)
        self.renderer23.set_property('width', 56)
        self.renderer24.set_property('width', 56)

        self.renderer22.set_property('height', 48)
        self.renderer23.set_property('height', 48)
        self.renderer24.set_property('height', 48)

        # Setup the icon islink cell-render
        self.renderer25 = gtk.CellRendererText()
        self.renderer25.set_property('xpad', 5)
        self.renderer25.set_property('size-points', 7)
        self.renderer25.set_property(
            'foreground',
            view2.get_style().text[gtk.STATE_INSENSITIVE].to_string()
            )

        # Connect columns to columns in icon view model
        column20 = gtk.TreeViewColumn("Name", self.renderer20, markup=0)
        column21 = gtk.TreeViewColumn("Context", self.renderer21, text=1)
        column22 = gtk.TreeViewColumn("Graphics")
        column23 = gtk.TreeViewColumn("Notes", self.renderer25, text=5)

        # pack pixbuf cell renderers into "Graphics" column
        column22.pack_start(self.renderer22, False)
        column22.pack_start(self.renderer23, False)
        column22.pack_start(self.renderer24, False)

        # Connect pixbuf renderers to columns in icon view model
        column22.set_attributes(self.renderer22, pixbuf=2)
        column22.set_attributes(self.renderer23, pixbuf=3)
        column22.set_attributes(self.renderer24, pixbuf=4)

        # append column to icon view
        view2.append_column(column20)
        view2.append_column(column21)
        view2.append_column(column22)
        view2.append_column(column23)

        column20.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        column21.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        column22.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        return view2

    def modify_view2_colors(self, view2, colors):
        bg, txt_norm, txt_insens, default = colors
        if default:
            bg_copy = bg
            bg = None
        # text rendereres
        rndrs = self.renderer20, self.renderer21
        for r in rndrs:
            r.set_property('foreground', txt_norm)
            r.set_property('cell-background', bg)
        # pixbuf renderers
        rndrs = self.renderer22, self.renderer23, self.renderer24
        for r in rndrs:
            r.set_property('cell-background', bg)
        # notes
        self.renderer25.set_property('foreground', txt_insens)
        self.renderer25.set_property('cell-background', bg)
        # base, and redraw
        if default:
            view2.modify_base( gtk.STATE_NORMAL, gtk.gdk.color_parse(bg_copy) )
        else:
            view2.modify_base( gtk.STATE_NORMAL, gtk.gdk.color_parse(bg) )
        return
