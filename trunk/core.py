#!/usr/bin/env python
# Filename: core.py

__licence__ = "LGPLv3"
__copyright__ = "Matthew McGowan, 2008"
__author__ = "Matthew McGowan <matthew.joseph.mcgowan@gmail.com>"


import pygtk
pygtk.require("2.0")

import os
import gtk
import pango
import editor
import gobject
import sqlite3
import colorise
import threading
import standards

#Initializing the gtk's thread engine
gtk.gdk.threads_init()


class IconLibraryController:
    """ The App class is the controller for this application """
    def __init__(self):
        # setup the root window
        DefaultTheme = gtk.icon_theme_get_default()
        self.root = gtk.Window(type=gtk.WINDOW_TOPLEVEL)
        self.root.set_default_size(780, 640)
        self.root.set_title( "Icon Library")
        self.root.connect("destroy", self.destroy_cb)
        self.root.set_icon_list(
            DefaultTheme.load_icon("gtk-home", 8, 0),
            DefaultTheme.load_icon("gtk-home", 16, 0),
            DefaultTheme.load_icon("gtk-home", 22, 0),
            DefaultTheme.load_icon("gtk-home", 24, 0),
            DefaultTheme.load_icon("gtk-home", 32, 0)
            )
        del DefaultTheme

        self.Theme = IconTheme()
        # start the greeter gui
        self.gui_setup_greeter(self.Theme)
        return

    def run(self):
        gtk.main()

    def gui_setup_greeter(self, Theme):
        """ Greets the user and offers a range of themes to choose from """
        align = gtk.Alignment(xalign=0.5, yalign=0.5)
        align2 = gtk.Alignment(xalign=0.5)
        vbox = gtk.VBox()
        hbox = gtk.HBox()
        hbox2 = gtk.HBox()

        # list all discoverable themes in a combo box
        theme_sel = gtk.combo_box_new_text()
        theme_sel.set_tooltip_text("Select an icon theme")
        i, active = 0, 0
        self.themes = Theme.list_themes()
        self.themes.sort()
        for theme, name, p in self.themes:
            name = name or "Unnamed"
            if theme == Theme.default:
                name += " (default)"
                active = i
            theme_sel.append_text(name)
            i += 1
        theme_sel.set_active(active)

        # an informative label
        welcome = gtk.Label()
        welcome.set_justify(gtk.JUSTIFY_CENTER)
        welcome.set_text("Select the icon theme you would like to view")

        # button to submit theme for viewing
        go = gtk.Button()
        go.set_size_request(33, -1)
        go.set_image( gtk.image_new_from_icon_name("dialog-ok", gtk.ICON_SIZE_SMALL_TOOLBAR) )

        # position widgets
        self.root.add(align)
        align.add(vbox)
        vbox.pack_start(welcome, padding=15)
        vbox.pack_start(hbox)
        hbox.add(align2)
        align2.add(hbox2)
        hbox2.pack_start(theme_sel, False)
        hbox2.pack_start(go, False)

        self.root.show_all()
        go.connect("clicked", self.ok_cb, vbox, theme_sel, (hbox2, welcome))
        return

    def init_icon_db(self, Theme, progressbar):
        """ Load Treeview models and views and load the icon database.
            When completed load the main gui """
        self.IconDB = IconDatabase()

        t = threading.Thread(
            target=self.IconDB.db_create,
            args=(Theme, progressbar)
            )
        t.start()
        gobject.timeout_add(200, self.icon_db_completion_checker, t)
        return

    def icon_db_completion_checker(self, thread):
        if thread.isAlive():
            return True
        else:
            self.gui_setup_browser()
            return False

    def gui_setup_browser(self):
        self.IconDB.db_load()
        self.Store = InfoModel(self.Theme)
        self.Display = DisplayModel()

        IconDB, Store, Display = self.IconDB, self.Store, self.Display
        vbox = gtk.VBox()

        # remove greeter widgets
        for child in self.root.get_children():
            self.root.remove(child)
            child.destroy()
            del child

        hbox = gtk.HBox()
        vbox.pack_start(hbox, False, padding=5)

        srch_btn = self.gui_setup_toolbar( hbox )
        scroller1, scroller2, btm_hbox1, btm_hbox2 = self.gui_setup_panels( vbox )
        self.gui_setup_search_note( btm_hbox1 )
        view1, view2 = self.gui_setup_listviews( Store, Display )

        scroller1.add(view1)
        scroller2.add(view2)

        # set the target note and treeview model callbacks
        IconDB.set_target_note(self.srch_note)
        IconDB.set_target_model(self.mdl2)

        self.srch_entry.connect("activate", IconDB.do_search, "like")
        srch_btn.connect("clicked", IconDB.do_search, self.srch_entry, "like")

        # set initial notes based on initial loading of icon theme database
        self.srch_note.set_markup(
            "Displaying <b>%s</b> icons" % ( IconDB.get_length() )
            )

        self.gui_setup_iconview_popup()

        self.root.add(vbox)
        self.root.show_all()

        self.gui_setup_color_swatches( btm_hbox2 )

        # fire off an initial search to fill icon view upon main gui launch
        IconDB.do_search(self.srch_entry, "like")
        return

    def gui_setup_toolbar(self, hbox):
        # theme change button/theme avatar
        self.theme_change = gtk.Button()
        self.gui_make_theme_avatar()
        self.theme_change.set_relief(gtk.RELIEF_NONE)
        self.theme_change.set_tooltip_text("Switch theme")
        hbox.pack_start(self.theme_change, False, padding=5)
        self.theme_change.connect("clicked", self.theme_change_dialog_cb)

        # label naming the current viewable theme, plus comment
        self.cur_theme = gtk.Label()
        self.gui_make_theme_header()
        hbox.pack_start(self.cur_theme, False)

        # check button that filters out icons whose names are not in the Standard Naming Spec
        self.stndrd_check = gtk.CheckButton(label="Standard icons only", use_underline=False)
        self.stndrd_check.set_tooltip_text("Only show icons that conform to the\nfreedesktop.org Icon Naming Specification")
        # filter the view for icon names matching the search term
        self.srch_entry = gtk.Entry(60)
        srch_btn = gtk.Button(stock=gtk.STOCK_FIND)
        self.stndrd_check.connect("toggled", self.theme_filter_by_standard_names_cb)

        srch_vbox = gtk.VBox()
        srch_align = gtk.Alignment(yalign=0.5)
        hbox.pack_end(srch_align, False)
        srch_align.add(srch_vbox)

        srch_vbox.pack_start(srch_btn, False)
        hbox.pack_end(self.srch_entry, False)
        hbox.pack_end(self.stndrd_check, False, padding=5)
        return srch_btn

    def gui_setup_panels( self, vbox ):
        # setup two panels
        hpaned = gtk.HPaned()
        hpaned.set_position(135)
        vbox.pack_start(hpaned)

        scroller1 = gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
        scroller1.set_policy(gtk.POLICY_ALWAYS, gtk.POLICY_AUTOMATIC)
        hpaned.pack1(scroller1)

        scroller2 = gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
        hpaned.pack2(scroller2)

        # bottom layout
        btm_hbox = gtk.HBox()
        btm_hbox.set_homogeneous(True)

        btm_hbox0 = gtk.HBox()
        btm_hbox1 = gtk.HBox()
        btm_hbox2 = gtk.HBox()

        btm_hbox.add(btm_hbox0)
        btm_hbox.add(btm_hbox1)
        btm_hbox.add(btm_hbox2)

        vbox.pack_end(btm_hbox, False)
        return scroller1, scroller2, btm_hbox1, btm_hbox2

    def gui_setup_search_note( self, btm_hbox1 ):
        # a note to provide basic search stats
        self.srch_note = gtk.Label()
        self.srch_note.set_alignment(0.5, 0.5)
        btm_hbox1.pack_end(self.srch_note)
        self.srch_note.set_size_request(-1, 24)
        return

    def gui_setup_listviews( self, Store, Display ):
        # make the context filter
        self.mdl1 = Store.get_model1()
        self.view1 = Display.make_view1(self.mdl1)
        self.view1.set_cursor(0)
        self.view1.connect("cursor-changed", self.filter_by_context_cb)

        # make the icon view
        self.mdl2 = Store.get_model2()
        self.view2 = Display.make_view2(self.mdl2)
        self.view2.connect("button-release-event", self.view2_row_activated_cb)
        return self.view1, self.view2

    def gui_setup_iconview_popup( self ):
        # view2 popup menu
        self.popup = gtk.Menu()
        self.popup.show_all()
        edit_action = gtk.Action("Editor", "Icon set properties", None, gtk.STOCK_EDIT)
        self.jump_action = gtk.Action("Jump to", "Jump to target icon", None, gtk.STOCK_JUMP_TO)
        self.popup.add( edit_action.create_menu_item() )
        self.popup.add( self.jump_action.create_menu_item() )
        edit_action.connect("activate", self.edit_iconset_dialog_cb)
        self.jump_action.connect("activate", self.jump_to_target_icon_cb)
        return

    def gui_setup_color_swatches( self, btm_hbox2 ):
        # swatchery
        # make color swatch to change the base color of the icon view
        self.encumbant_focus = None
        style = self.view2.get_style()
        cb = self.gui_bg_color_change_cb

        color_sel0 = colorise.ColorSwatch(cb, style, tip="Default", default=True)
        color_sel1 = colorise.ColorSwatch(cb,  style, bg="#FFFFFF", tip="White")
        color_sel2 = colorise.ColorSwatch(cb,  style, bg="#9C9C9C", txt2="#525252", tip="Grey")
        color_sel3 = colorise.ColorSwatch(cb,  style, bg="#525252", txt1="#E6E6E6", txt2="#9E9E9E", tip="Dark grey")
        self.encumbant_focus = color_sel0.give_focus()

        btm_hbox2.pack_end(color_sel3, False)
        btm_hbox2.pack_end(color_sel2, False)
        btm_hbox2.pack_end(color_sel1, False)
        btm_hbox2.pack_end(color_sel0, False)
        btm_hbox2.show_all()
        return

    def gui_make_theme_header(self):
        Theme = self.Theme
        name = Theme.info[1] or "Unnamed"
        comment = Theme.read_comment( Theme.info[2] ) or "No comment"
        markup = "<b>%s</b>\n<span size='small'>%s</span>"
        s = markup % (name, comment)
        self.cur_theme.set_markup(s)
        return

    def gui_make_theme_avatar(self):
        try:
            self.theme_change.set_image(
                gtk.image_new_from_pixbuf(
                    self.Theme.load_icon("folder", 32, 0)
                    )
                )
        except:
            self.theme_change.set_image( gtk.image_new_from_icon_name("folder", gtk.ICON_SIZE_DND) )
        return

    def gui_bg_color_change_cb(self, successor):
        e = self.encumbant_focus
        if e != successor:
            e.relinquish_focus()
            gobject.idle_add(
                self.Display.modify_view2_colors, successor.get_colors()
                )
        self.encumbant_focus = successor
        return

    def theme_change_dialog_cb(self, *kw):
        # TODO: Make more HIGy
        dialog = gtk.Dialog(
            "Change Icon Theme",
            self.root,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
            )
        dialog.set_has_separator(False)

        # list all discoverable themes in a combo box
        theme_sel = gtk.combo_box_new_text()
        theme_sel.set_tooltip_text("Select an icon theme")
        i, active = 0, 0
        for theme, name, p in self.themes:
            name = name or "Unnamed"
            if theme == self.Theme.default:
                name += " (default)"
                active = i
            theme_sel.append_text(name)
            i += 1
        theme_sel.set_active(active)
        theme_sel.set_tooltip_text("Select an icon theme")

        header = gtk.Label()
        header.set_justify(gtk.JUSTIFY_CENTER)
        header.set_text("Select a new icon theme to view")

        dialog.vbox.pack_start(header, False, False, 5)
        dialog.vbox.pack_start(theme_sel, False, False, 10)

        dialog.vbox.show_all()
        response = dialog.run()
        if response == gtk.RESPONSE_ACCEPT:
            self.Theme.set_theme( self.themes[theme_sel.get_active()] )
            self.IconDB.db_create(self.Theme)
            # set theme avatar
            self.gui_make_theme_avatar()
            self.gui_make_theme_header()
            # fire off a search to fill icon view on new theme selection
            self.IconDB.do_search(self.srch_entry, "like")
        dialog.destroy()
        return

    def theme_filter_by_standard_names_cb(self, *kw):
        """ Filter search results by icon names which exist in the Icon Naming Specification """
        stndrd_only = kw[0].get_active()
        self.IconDB.set_standard_filter(stndrd_only)
        gobject.idle_add(self.IconDB.do_search, self.srch_entry, "like")
        return

    def view2_row_activated_cb(self, *kw):
        treeview = kw[0]
        event = kw[-1]
        if event.button == 3:
            self.view2_display_iconview_popup( treeview, event )
        return

    def view2_display_iconview_popup( self, treeview, event ):
        x = int(event.x)
        y = int(event.y)
        time = event.time
        pthinfo = treeview.get_path_at_pos(x, y)
        if pthinfo is not None:
            treeview.grab_focus()
            path, col, cellx, celly = pthinfo
            results = self.IconDB.results[path[0]]
            self.selected_icon_data = results
            if results[0] != results[1]:
                self.jump_action.set_sensitive( True )
            else:
                self.jump_action.set_sensitive( False )
            self.popup.popup( None, None, None, event.button, time)
        return

    def edit_iconset_dialog_cb(self, *kw):
        set_editor = editor.IconSetEditorDialog(
            self.root,
            self.IconDB.update_pixbuf_cache
            )
        set_editor.make_dialog( self.Theme, self.selected_icon_data )
        return

    def jump_to_target_icon_cb( self, *kw ):
        path = self.Theme.lookup_icon(self.selected_icon_data[1], 22, 0).get_filename()
        rpath = os.path.realpath( path )
        rname = os.path.splitext( os.path.split( rpath )[1] )[0]
        found = False

        for row in self.IconDB.model:
            if row[0][0] == "<":
                if row[0][3:-4] == rname:
                    self.view2.set_cursor( row.path )
                    found = True
                    break
            elif row[0] == rname:
                self.view2.set_cursor( row.path )
                found = True
                break

        if not found:
            self.IconDB.do_search( rname, "exact" )
            self.prompt_target_icon_not_in_theme( rname, rpath )
        return

    def prompt_target_icon_not_in_theme(self, rname, rpath ):
        dialog = gtk.Dialog(
            "Target icon not found",
            self.root,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_OK, gtk.RESPONSE_OK)
            )
        dialog.set_has_separator(False)
        s = "<b>%s</b>\n" % rname
        s += "%s\n\n" % rpath
        s += "The icon targeted by this symlink (%s) was not discovered!" % rname
        notice = gtk.Label()
        notice.set_justify( gtk.JUSTIFY_CENTER )
        notice.set_size_request( 300, -1 )
        notice.set_line_wrap( True )
        notice.set_markup( s )
        dialog.vbox.pack_start( notice, padding=8 )
        dialog.vbox.show_all()

        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            pass
        dialog.destroy()
        return

    def filter_by_context_cb(self, *kw):
        """ Filter search results by the select icon context """
        model, path = self.view1.get_selection().get_selected()
        ctx = model[path][0]
        self.IconDB.set_context_filter(ctx)
        gobject.idle_add(self.IconDB.do_search, self.srch_entry, "like")
        return

    def ok_cb(self, btn, vbox, theme_sel, insens_widgets):
        """ Begin loading the theme chosen at the greeter gui """
        for w in insens_widgets:
            w.set_sensitive(False)

        Theme = self.Theme
        Theme.set_theme( self.themes[theme_sel.get_active()] )

        loading = gtk.Label()
        loading.set_justify(gtk.JUSTIFY_CENTER)
        loading.set_markup(
            "Loading icon data for the theme <b>%s</b>...\nThis may take several moments." % Theme.info[1]
            )
        vbox.pack_start(loading, padding=15)
        loading.show()

        progress = gtk.ProgressBar()
        vbox.pack_end( progress )
        progress.show()

        self.init_icon_db( Theme, progress )
        return

    def destroy_cb(self, *kw):
        """ Destroy callback to shutdown the app """
        if len(threading.enumerate()) == 1:
            gtk.main_quit()
        else:
            print threading.enumerate()
        return


class IconTheme(gtk.IconTheme):
    def __init__(self):
        gtk.IconTheme.__init__(self)
        self.info = None
        self.default = gtk.settings_get_default().get_property("gtk-icon-theme-name")

    def list_themes(self):
        all_themes = []
        for path in self.get_search_path():
            all_themes += self.find_any_themes(path)
        return all_themes

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
            if os.path.exists(index_path) and not os.path.exists( os.path.join(root, "cursor.theme") ):
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
    """ IconDatabase creates an in memory SQLite DB that provides the app both storage of icon info (context, islink)
        and provides basic search functionality as well.  Moreover, as the db is created a icon pixbuf cache is filled
        to speed-up runtime usage. """
    def __init__(self):
        """ Both the DB and pixbuf cache are filled. """
        self.term = ""
        self.length = 0
        self.note = None
        self.model = None
        self.results = None
        self.standard_only = False
        self.ctx_filter = "<b>All Contexts</b>"
        self.NamingSpec = standards.StandardIconNamingSpec()
        return

    def db_establish_new_connection(self):
        create = True
        if os.path.exists( "/tmp/icondb.sqlite3" ):
            create = False

        conn = sqlite3.connect("/tmp/icondb.sqlite3")
        cursor = conn.cursor()

        if create:
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
                    standard = self.NamingSpec.isstandard(ctx, ico)
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
        """ do_search provides basic search functionality.
            It allows one term, the text taken from the gtk.Entry, plus a context filter. """
        if len(threading.enumerate()) == 1:
            if type( entry ) == str:
                self.term = entry
            else:
                self.term = entry.get_text()
            if mode == "like":
                query = self.query_like_search( self.term )
            elif mode == "exact":
                query = self.query_exact_search( self.term )

            try:
                self.cursor.execute(query)
            except Exception, inst:
                print query
                print "\nBadQuery:", query
                print inst
                return False

            self.results = self.cursor.fetchall()

            # feedback basic search stats to the main gui
            if self.note:
                self.give_feedback(self.term, len(self.results))

            # start the ListDisplayer thread
            self.model.clear()
            displayer = ListDisplayer(self.results, self.pb_cache, self.model)
            displayer.start()
        return False    # run once -- do_search is called by a gobject.idle

    def query_like_search( self, term ):
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

    def query_exact_search( self, term ):
        return "SELECT * FROM theme WHERE name=\"%s\"" % term

    def give_feedback(self, term, num_of_results):
        """ Displays basic search stats in the GUI """
        std = ""
        if self.standard_only:
            std = "<b>standard</b> "
        if term == "":
            info = "<b>%s</b> %sicons in <b>%s</b>" % (num_of_results, std, self.ctx_filter)
        else:
            info = "<b>%s</b> %sresults for <b>%s</b> in <b>%s</b>"
            info = info % (num_of_results, std, term, self.ctx_filter)
        self.note.set_markup(info)
        return

    def update_pixbuf_cache( self, key, index, pixbuf ):
        pb_list = list( self.IconDB.pb_cache[key] )
        pb_list[index] = pixbuf
        self.IconDB.pb_cache[key] = tuple( pb_list )
        return

    def set_target_model(self, model):
        """ Sets the target model """
        self.model = model
        return

    def set_target_note(self, note):
        """ Sets the note.  The note allows the DB to feedback some basic stats to the GUI. """
        self.note = note
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

    def get_term(self):
        """ Returns the current search term """
        return self.term

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
        renderer10.set_property("wrap-width", 135)
        renderer10.set_property("wrap-mode", pango.WRAP_WORD)

        column10 = gtk.TreeViewColumn("Context Filter", renderer10, markup=0)

        view1.append_column(column10)
        return view1

    def make_view2(self, model):
        """ Make the main view for the icon view list store """
        self.view2 = gtk.TreeView(model)
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

        # append columsn to icon view
        self.view2.append_column(column20)
        self.view2.append_column(column21)
        self.view2.append_column(column22)
        self.view2.append_column(column23)

        column20.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        column21.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        column22.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        return self.view2

    def modify_view2_colors(self, colors):
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
        return False # run once, called by a gobject.idle_add()


class ListDisplayer(threading.Thread):
    """ Renders cells in a thread to minimise GUI unresponsiveness """
    def __init__(self, results, pb_cache, model):
        """ Setup threading """
        threading.Thread.__init__(self)
        self.finished = threading.Event()
        self.results = results
        self.pb_cache = pb_cache
        self.mdl = model
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
                self.mdl.append( (ico, context, pb0, pb1, pb2, notes) )
                gtk.gdk.threads_leave()
            self.finished.set()
        return
