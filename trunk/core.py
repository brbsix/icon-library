#!/usr/bin/env python
# Filename: core.py

__licence__ = "LGPLv3"
__copyright__ = "Matthew McGowan, 2009"
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
        self.Gui.make_greeter(self.Theme, self.init_database)
        self.Gui.root.show_all()
        self.Gui.root.connect("destroy", self.destroy_cb )
        return

    def init_database(self, Theme, progressbar):
        """ Function sets initial theme and builds initial theme database.
            On completion initialises browser gui """
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
        """ Function initialises browser gui """
        self.IconDB.load()
        self.Store = InfoModel()
        self.Display = DisplayModel()

        Display = self.Display
        Display.make_view1(self.Store.model1)
        Display.make_view2(self.Store.model2)

        self.cswatch_focus = None

        self.Gui.make_browser(
            self,
            self.Theme,
            self.IconDB,
            self.Store,
            Display
            )

        self.Store.model1_set_info(self.Theme)
        self.Gui.root.show_all()
        self.search_and_display(self.Gui.text_entry)
        return

    def start_theme_change(self, Theme, Dialog, new_theme, progress):
        """ Function sets new theme and builds new theme database.
            Calls finish_theme_change on database completion """
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
        """ Alters Gui elements to reflect theme change completion """
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

        self.Store.model1_set_info(Theme)
        self.search_and_display(self.Gui.text_entry)
        return

    def thread_completed(self, thread, func, args=None):
        """ Function checks if a thread is alive.  If not runs a callback.
            Use in conjunction with a gobject timeout """
        if thread.isAlive():
            return True
        else:
            if args:
                func( *args )
            else:
                func()
            return False

    def search_and_display(self, entry):
        """ Function performs IconDB search then displays results in treeview """
        IconDB = self.IconDB
        term, results = IconDB.search(entry)

        self.Gui.set_feedback(
            IconDB,
            term,
            len(results)
            )

        self.Store.model2.clear()
        self.Store.model2_set_info(
            results,
            IconDB.pixbuf_cache
            )
        return

    def change_bg_color_cb(self, successor):
        """ ColorSwatch clicked callback.  Modify's treeview background color. """
        cs = self.cswatch_focus
        if cs != successor:
            cs.relinquish_focus()
            self.Display.view2_modify_colors( successor.get_colors() )
        self.cswatch_focus = successor
        return

    def change_theme_cb(self, avatar_button):
        """ Theme change button clicked callback.  Begins theme change process """
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
        """ Standard filter checkbutton toggled callback.  Sets standard filter. """
        self.IconDB.set_standard_filter( checkbutton.get_active() )
        self.search_and_display(self.Gui.text_entry)
        return

    def inherited_filter_cb(self, checkbutton):
        self.IconDB.set_inherited_filter( checkbutton.get_active() )
        self.search_and_display(self.Gui.text_entry)
        return False

    def row_activated_2click_cb(self, treeview, path, column):
        iconset_data = self.IconDB.results[path[0]]
        self.edit_iconset_cb(None, iconset_data)
        return

    def row_activated_cb(self, treeview, event):
        """ Iconset (view2) treeview row activated callback """
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
        """ Callback that starts the iconset editor for selected iconset """
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
        """ Jump to clicked callback.  Jumps to icon symlink target. """
        path = self.Theme.lookup_icon(results[0], 22, 0).get_filename()
        rpath = os.path.realpath( path )
        rname = os.path.splitext( os.path.split( rpath )[1] )[0]
        found = False

        Display = self.Display

        for row in self.Store.model2:
            if row[0][0] == "<":
                if row[0][3:-4] == rname:
                    Display.view2.set_cursor( row.path )
                    found = True
                    break
            elif row[0] == rname:
                Display.view2.set_cursor( row.path )
                found = True
                break
        if not found:
            d = gtk.MessageDialog(
                parent=self.Gui.root,
                flags=(gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT),
                type=gtk.MESSAGE_WARNING,
                buttons=gtk.BUTTONS_CLOSE,
                )

            m = "<big><b><span foreground=\"#FF09FF\">%s</span> was not found</b></big>"
            d.set_markup(m % rname)

            s = "The icon set targeted by this symlink was not discovered."
            s += "\n\nIf you have filtered the icons by context or word, "
            s += "then the icon set is probably not in the current list.  "
            s += "In which case, try the action again with an un-filtered view."

            d.format_secondary_text(s)

            d.set_image(
                gtk.image_new_from_stock(
                    gtk.STOCK_DIALOG_WARNING,
                    gtk.ICON_SIZE_DIALOG
                    )
                )

            d.image.show()
            d.run()
            d.destroy()
        return

    def context_filter_cb(self, treeview):
        """ Filter search results by selected context """
        model, path = treeview.get_selection().get_selected()
        ctx = model[path][0]
        self.IconDB.set_context_filter(ctx)
        self.search_and_display(self.Gui.text_entry)
        return

    def search_entry_cb( self, search_entry, text):
        self.search_and_display(text)
        return

    def search_button_cb( self, *kw ):
        """ Search button clicked callback.  Does search. """
        self.search_and_display(self.Gui.text_entry)
        return

    def clear_button_cb( self, *kw ):
        """ Clear button clicked callback. Does empty search. """
        self.Gui.text_entry.set_text("")
        self.search_and_display("")
        return

    def destroy_cb(self, *kw):
        """ Destroy callback to shutdown the app """
        gtk.main_quit()
        return

    def run(self):
        """ Starts the app """
        gtk.main()
        return


class IconLibraryGui:
    def __init__(self):
        # setup the root window
        self.root = gtk.Window(type=gtk.WINDOW_TOPLEVEL)
        self.root.set_default_size(850, 640)
        self.root.set_title( "Icon Library")
        self.vbox = gtk.VBox()
        self.root.add(self.vbox)
        return

    def make_greeter(self, Theme, callback):
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
                name += " (in use)"
                active = i
            theme_sel.append_text(name)
            i += 1
        theme_sel.set_active(active)

        header = gtk.Label()
        header.set_justify(gtk.JUSTIFY_CENTER)
        header.set_text("Select the icon theme you would like to view")

        go = gtk.Button()
        go.set_tooltip_text("Load selected icon theme")
        go.set_size_request(33, -1)
        go.set_image(
            gtk.image_new_from_icon_name("dialog-ok", gtk.ICON_SIZE_SMALL_TOOLBAR)
            )

        custom = gtk.Button()
        custom.set_tooltip_text("Import an icon theme")
        custom.set_size_request(33, -1)
        custom.set_image(
            gtk.image_new_from_icon_name("document-open", gtk.ICON_SIZE_SMALL_TOOLBAR)
            )

        greeter_main_align = gtk.Alignment(xalign=0.5, yalign=0.5)
        greeter_vbox = gtk.VBox()
        greeter_hbox = gtk.HBox()

        greeter_hbox.pack_start(theme_sel, False)
        greeter_hbox.pack_start(custom, False)
        greeter_hbox.pack_start(go, False)

        greeter_vbox.pack_start(header)
        greeter_vbox.pack_start(greeter_hbox, padding=16)

        greeter_main_align.add(greeter_vbox)
        self.vbox.add(greeter_main_align)

        custom.connect(
            "clicked",
            self.custom_cb,
            Theme,
            theme_sel
            )

        go.connect(
            "clicked",
            self.loading_cb,
            Theme,
            header,
            themes,
            theme_sel,
            custom,
            greeter_vbox,
            callback
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

        self.setup_listviews(
            Controller,
            Display,
            scrollers
            )

        btm_hboxes = self.setup_bottom_toolbar(vbox)

        self.setup_feedback_label(
            IconDB,
            btm_hboxes[1]
            )

        self.setup_color_swatches(Controller, btm_hboxes[2])
        return

    def setup_top_toolbar(self, Controller, Theme, vbox):
        import pango
        import searchentry

        self.avatar_button = gtk.Button()
        self.avatar_button.set_relief(gtk.RELIEF_NONE)
        self.avatar_button.set_tooltip_text("Switch theme")
        self.avatar_button.set_image( self.make_avatar(Theme) )

        self.header_label = gtk.Label()
        self.header_label.set_max_width_chars(40)
        self.header_label.set_ellipsize(pango.ELLIPSIZE_END)
        self.header_label.set_markup( self.make_header(Theme) )

        self.standard_check = gtk.CheckButton(
            label="Hide non-standard icons",
            use_underline=False
            )
        self.standard_check.set_tooltip_text(
            "Choose to display icons that conform to the\nfreedesktop.org Icon Naming Specification"
            )

        self.inherited_check = gtk.CheckButton(
            label="Hide inherited icons",
            use_underline=False
            )
        self.inherited_check.set_tooltip_text(
            "Choose to display icons that have been\ninherited from other themes"
            )

        self.text_entry = searchentry.SearchEntry()

        rbtn_align = gtk.Alignment(0.5, 0.5)
        rbtn_vbox = gtk.VBox()
        rbtn_hbox = gtk.HBox()

        rbtn_align.add(rbtn_vbox)
        rbtn_vbox.pack_start(rbtn_hbox, False)

        tbar_hbox = gtk.HBox(spacing=3)
        check_vbox = gtk.VBox(spacing=3)

        check_vbox.pack_start(self.standard_check, False)
        check_vbox.pack_start(self.inherited_check, False)

        tbar_hbox.pack_start(self.avatar_button, False, padding=5)
        tbar_hbox.pack_start(self.header_label, False)

        tbar_hbox.pack_end(rbtn_align, False)
        tbar_hbox.pack_end(self.text_entry, False)
        tbar_hbox.pack_end(check_vbox, False, padding=5)

        vbox.pack_start(tbar_hbox, False, padding=5)

        self.avatar_button.connect(
            "clicked",
            Controller.change_theme_cb
            )

        self.standard_check.connect(
            "toggled",
            Controller.standard_filter_cb
            )

        self.inherited_check.connect(
            "toggled",
            Controller.inherited_filter_cb
            )

        self.text_entry.connect(
            "terms-changed",
            Controller.search_entry_cb
            )
        return

    def setup_scrolled_panels(self, vbox):
        hpaned = gtk.HPaned()
        hpaned.set_position(135)
        hpaned.set_border_width(3)

        scroller1 = gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
        scroller1.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroller1.set_shadow_type(gtk.SHADOW_IN)

        scroller2 = gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
        scroller2.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroller2.set_shadow_type(gtk.SHADOW_IN)

        hpaned.pack1(scroller1)
        hpaned.pack2(scroller2)

        vbox.pack_start(hpaned)
        return (scroller1, scroller2)

    def setup_listviews(self, Controller, Display, scrollers):
        view1, view2 = Display.view1, Display.view2

        scrollers[0].add(view1)
        scrollers[1].add(view2)

        view1.connect("cursor-changed", Controller.context_filter_cb) 
        view2.connect_after("button-release-event", Controller.row_activated_cb)
        view2.connect("row-activated", Controller.row_activated_2click_cb)
        return

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
        self.feedback_label = gtk.Label()
        self.feedback_label.set_alignment(0.5, 0.5)
        self.feedback_label.set_size_request(-1, 24)

        self.feedback_label.set_markup(
            "Displaying <b>%s</b> icons" % ( IconDB.get_length() )
            )

        btm_hbox.pack_end(self.feedback_label)
        return

    def setup_color_swatches(self, Controller, btm_hbox):
        import custom_widgets

        style = self.root.get_style()
        cb = Controller.change_bg_color_cb

        sel0 = custom_widgets.ColorSwatch(
            cb,
            style,
            tip="Default",
            default=True
            )

        sel1 = custom_widgets.ColorSwatch(
            cb,
            style,
            bg="#FFFFFF",
            tip="White"
            )

        sel2 = custom_widgets.ColorSwatch(
            cb,
            style,
            bg="#9C9C9C",
            txt2="#525252",
            tip="Grey"
            )

        sel3 = custom_widgets.ColorSwatch(
            cb,
            style,
            bg="#525252",
            txt1="#E6E6E6",
            txt2="#9E9E9E",
            tip="Dark grey"
            )

        Controller.cswatch_focus = sel0.give_focus()

        for sel in sel3, sel2, sel1, sel0:
            a = gtk.Alignment(0.5,0.5)
            a.add(sel)
            btm_hbox.pack_end(a, False)

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
        self.feedback_label.set_markup(s)
        return

    def custom_cb(self, button, Theme, theme_sel):
        chooser = gtk.FileChooserDialog(
            "Import an icon theme",
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK)
            )

        fltr = gtk.FileFilter()
        fltr.set_name("Theme Index")
        fltr.add_pattern("index.theme")
        chooser.add_filter(fltr)

        fltr = gtk.FileFilter()
        fltr.set_name("All files")
        fltr.add_pattern("*")
        chooser.add_filter(fltr)

        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            index_path = chooser.get_filename()
            theme_root = chooser.get_current_folder()

            theme = (
                os.path.split(theme_root)[1],
                Theme.read_name(index_path),
                index_path
                )

            theme_sel.append_text(theme[1])
            theme_sel.set_active( len(Theme.all_themes) )
            Theme.all_themes.append(theme)
            Theme.prepend_search_path( os.path.split(theme_root)[0] )

        chooser.destroy()
        return

    def loading_cb(self, go, Theme, header, themes, theme_sel, custom, greeter_vbox, callback):
        """ Begin loading the theme chosen at the greeter gui """
        Theme.set_theme( themes[theme_sel.get_active()] )

        go.set_sensitive(False)
        for w in (theme_sel, custom, go):
            w.set_sensitive(False)

        s = "Loading <b>%s</b>\nThis may take several moments" % Theme.info[1]
        header.set_markup(s)

        progress = gtk.ProgressBar()
        greeter_vbox.pack_end( progress )
        progress.show()

        callback(Theme, progress)
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
        self.conn = None
        self.cursor = None
        self.length = 0
        self.model = None
        self.results = None
        self.standard_only = False
        self.inherited_only = False
        self.ctx_filter = "<b>All Contexts</b>"
        return

    def new_conn(self):
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
                    scalable BOOLEAN, \
                    inherited BOOLEAN, \
                    inherited_name TEXT \
                    )"
                )
        else:
            cursor.execute("DELETE FROM theme")

        return conn, cursor

    def create(self, Theme, progressbar=None):
        from standards import StandardIconNamingSpec
        spec = StandardIconNamingSpec()

        conn, cursor = self.new_conn()
        i, j = 0, 0

        self.pixbuf_cache = {}
        contexts = Theme.list_contexts()
        total = float( len( contexts ) )

        for ctx in contexts:
            for ico in Theme.list_icons(ctx):

                k, inherited = self.iconset_key(Theme, ico)
                tn = Theme.info[0]

                if self.pixbuf_cache_append(Theme, ico, k, ctx):
                    scalable = -1 in Theme.get_icon_sizes(ico)
                    standard = spec.isstandard(ctx, ico)
                    cursor.execute(
                        "INSERT INTO theme VALUES (?,?,?,?,?,?,?)",
                        (k, ico, ctx, standard, scalable, inherited == tn, inherited)
                        )
                    i += 1
                else:
                    print "Error: %s - Failed to load a pixbuf. Skipping..." % ico

            j += 1

            if progressbar:
                gtk.gdk.threads_enter()
                progressbar.set_fraction( j / total )
                progressbar.set_text( "Loading %s..." % ctx )
                gtk.gdk.threads_leave()

        conn.commit()
        cursor.close()
        self.length = i
        return

    def load( self ):
        if self.cursor != None:
            self.cursor.close()
            del self.conn, self.cursor
        self.conn = sqlite3.connect("/tmp/icondb.sqlite3")
        self.cursor = self.conn.cursor()
        return

    def iconset_key(self, Theme, name):
        p = Theme.lookup_icon(name, 24, 0).get_filename()
        p = os.path.realpath( p )
        k = os.path.splitext( os.path.split(p)[1] )[0]
        return k, p.split('/')[4]   # return key and inheritance

    def pixbuf_cache_append(self, Theme, name, k, ctx):
        try:
            if not self.pixbuf_cache.has_key(k):
                if ctx != 'Animations':
                    self.pixbuf_cache[k] = self.load_icons(Theme, name)
                else:
                    self.pixbuf_cache[k] = self.load_animations(Theme, name)
        except Exception, e:
            print e
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
            if type( term ) != str:
                term = term.get_text()

            query = self.make_query(term)
            self.cursor.execute(query)
            self.results = self.cursor.fetchall()
        return term, self.results

    def make_query( self, term ):
        if term != "":
            qterm = "\"%" + term + "%\""
            query = "SELECT * FROM theme WHERE name LIKE %s" % qterm
            if self.standard_only:
                query += " AND standard"
            if self.inherited_only:
                query += " AND inherited"
            if self.ctx_filter != "<b>All Contexts</b>":
                query += " AND context=\"%s\" ORDER BY name" % self.ctx_filter
            else:
                query += " ORDER BY context, name"
        else:
            query = "SELECT * FROM theme"
            if self.standard_only:
                query += " WHERE standard"
            if self.inherited_only:
                if self.standard_only:
                    query += " AND inherited"
                else:
                    query += " WHERE inherited"
            if self.ctx_filter != "<b>All Contexts</b>":
                if self.standard_only or self.inherited_only:
                    query += " AND context=\"%s\" ORDER BY name" % self.ctx_filter
                else:
                    query += " WHERE context=\"%s\" ORDER BY name" % self.ctx_filter
            else:
                query += " ORDER BY context, name"
        return query

    def set_context_filter(self, context):
        """ Sets the context filter string """
        self.ctx_filter = context
        return

    def set_standard_filter(self, standard_only):
        """ Sets whether to filter based on standard names only """
        self.standard_only = standard_only
        return

    def set_inherited_filter(self, inherited_only):
        self.inherited_only = inherited_only
        return

    def get_context_filter(self):
        """ Returns the current context filter """
        return self.ctx_filter

    def get_length(self):
        """ Returns the total number of icons in the IconDB """
        return self.length


class InfoModel:
    def __init__(self):
        self.model1 = self.make_model1()
        self.model2 = self.make_model2()
        return

    def make_model1(self):
        model1 = gtk.ListStore(str, str)
        return model1

    def make_model2(self):
        model2 = gtk.ListStore(
            str,
            str,
            gtk.gdk.Pixbuf,
            gtk.gdk.Pixbuf,
            gtk.gdk.Pixbuf,
            str
            )
        return model2

    def model1_set_info(self, Theme):
        from standards import StandardIconNamingSpec
        spec = StandardIconNamingSpec()

        self.model1.clear()
        self.model1.append( ("<b>All Contexts</b>", "") )
        ctxs = list( Theme.list_contexts() )
        ctxs.sort()
        for ctx in ctxs:
            comments = spec.get_context_comment(ctx)
            self.model1.append((ctx, comments or ctx))
        return

    def model2_set_info(self, results, pixbuf_cache):
        appender = threading.Thread(
            target=self.__model2_appender,
            args=(results, pixbuf_cache)
            )
        appender.start()
        return

    def __model2_appender(self, results, pixbuf_cache):
        for key, ico, context, standard, scalable, inherited, inherited_name in results:
            if key in pixbuf_cache:
                pb0 = pixbuf_cache[key][0]
                pb1 = pixbuf_cache[key][1]
                pb2 = pixbuf_cache[key][2]

                notes = None
                if key != ico:
                    notes = "Symlink"
                if not scalable:
                    if not notes:
                        notes = "Fixed Only"
                    else:
                        notes += ", Fixed Only"
                if not inherited:
                    if not notes: notes = ""
                    notes += "\nInherited from %s" % inherited_name
                if standard:
                    ico = "<b>%s</b>" % ico

                gtk.gdk.threads_enter()
                self.model2.append( (ico, context, pb0, pb1, pb2, notes) )
                gtk.gdk.threads_leave()
        return


class DisplayModel:
    def make_view1(self, model1):
        """ Make the view for the context filter list store """
        self.view1 = gtk.TreeView(model1)
        renderer10 = gtk.CellRendererText()
        renderer10.set_property("xpad", 5)

        column10 = gtk.TreeViewColumn("Context Filter", renderer10, markup=0)
        self.view1.append_column(column10)

        self.view1.set_tooltip_column(1)
        return self.view1

    def view1_query_tooltip_cb(self, *args):
        print args
        return

    def make_view2(self, model2):
        """ Make the main view for the icon view list store """
        import pango

        self.view2 = gtk.TreeView(model2)
        self.view2.set_events( gtk.gdk.BUTTON_PRESS_MASK )
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
            self.view2.get_style().text[gtk.STATE_INSENSITIVE].to_string()
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
        self.view2.append_column(column20)
        self.view2.append_column(column21)
        self.view2.append_column(column22)
        self.view2.append_column(column23)

        column20.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        column21.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        column22.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        return self.view2

    def view2_modify_colors(self, colors):
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
            self.view2.modify_base( gtk.STATE_NORMAL, gtk.gdk.color_parse(bg_copy) )
        else:
            self.view2.modify_base( gtk.STATE_NORMAL, gtk.gdk.color_parse(bg) )
        return
