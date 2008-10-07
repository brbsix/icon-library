#!/usr/bin/env python
# Filename: editor.py

__licence__ = "LGPLv3"
__copyright__ = "Matthew McGowan, 2008"
__author__ = "Matthew McGowan <matthew.joseph.mcgowan@gmail.com>"


import pygtk
pygtk.require("2.0")

import os
import gtk
import gobject
import colorise


class IconSetEditorDialog(gtk.Dialog):
    def __init__(self, parent_window, pb_update_cb ):
        self.pb_update_cb = pb_update_cb
        gtk.Dialog.__init__(
            self,
            "Icon Set Properties",
            parent_window,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_APPLY, gtk.RESPONSE_APPLY)
            )

        self.set_has_separator( False )
        self.header = gtk.Label()
        self.header.set_alignment( 0.5, 0.5 )
        self.vbox.pack_start( self.header, padding=6 )

        self.notebook = gtk.Notebook()
        self.notebook.set_tab_pos( gtk.POS_BOTTOM )
        self.notebook.set_size_request( 300, -1 )
        self.notebook.set_scrollable( True )
        self.vbox.pack_start( self.notebook, padding=8 )
        return

    def make_dialog(self, Theme, iconset_data ):
        iconset_context = iconset_data[2]
        iconset_name = iconset_data[1]

        iconset = ()
        sizes = list( Theme.get_icon_sizes(iconset_name) )
        sizes.sort()

        if sizes[0] == -1:
            del sizes[0]
            sizes += "scalable",

        self.header.set_markup(
            "<b>%s</b>\n<span size=\"small\">%s</span>" % ( iconset_name, iconset_context )
            )
        self.header.set_justify( gtk.JUSTIFY_CENTER )

        subtle_color = self.get_style().text[gtk.STATE_INSENSITIVE].to_string()
        for size in sizes:
            icon = self.make_and_append_page(
                Theme,
                iconset_context,
                iconset_name,
                size,
                subtle_color
                )
            iconset += icon,

        islink = gtk.CheckButton( "Save as symlinks", False )
        islink.set_active( True )
        self.vbox.pack_start( islink, False, False, padding=3 )

        self.vbox.show_all()
        response = self.run()
        if response == gtk.RESPONSE_APPLY:
            self.backup_and_replace_icon( iconset, iconset_data[0] )
        elif response == gtk.RESPONSE_CANCEL:
            pass
        self.destroy()
        return

    def make_and_append_page( self, Theme, iconset_context, iconset_name, size, subtle_color ):
        if type(size) == int:
            path = Theme.lookup_icon(iconset_name, size, 0).get_filename()
            tab_label = "%sx%s" % (size, size)
        else:
            path = Theme.lookup_icon(iconset_name, 64, 0).get_filename()
            tab_label = size

        page = gtk.VBox()

        if os.path.islink( path ):
            info_table = gtk.Table(rows=4, columns=2)

            l_name = gtk.Label()
            l_type = gtk.Label()
            l_link = gtk.Label()
            l_targ = gtk.Label()

            l_name.set_markup( "<span foreground=\"%s\"><b>Name</b></span>" % subtle_color )
            l_type.set_markup( "<span foreground=\"%s\"><b>Type</b></span>" % subtle_color )
            l_link.set_markup( "<span foreground=\"%s\"><b>Path</b></span>" % subtle_color )
            l_targ.set_markup( "<span foreground=\"%s\"><b>Target</b></span>" % subtle_color )

            l_name.set_size_request(48, -1)
            l_type.set_size_request(48, -1)
            l_link.set_size_request(48, -1)
            l_targ.set_size_request(48, -1)

            l_name.set_alignment(1, 0.5)
            l_type.set_alignment(1, 0.5)
            l_link.set_alignment(1, 0.5)
            l_targ.set_alignment(1, 0.5)

            info_table.attach( l_name, 0, 1, 0, 1, xoptions=gtk.SHRINK )
            info_table.attach( l_link, 0, 1, 1, 2, xoptions=gtk.SHRINK )
            info_table.attach( l_type, 0, 1, 2, 3, xoptions=gtk.SHRINK )
            info_table.attach( l_targ, 0, 1, 3, 4, xoptions=gtk.SHRINK )

            p,n = os.path.split(path)

            r_name = gtk.Label(n)
            r_type = gtk.Label("Linked %s" % os.path.splitext(n)[1][1:].upper() )
            r_path = gtk.Label(p)
            r_targ = gtk.Label( os.path.realpath(path) )

            r_name.set_alignment(0, 0.5)
            r_type.set_alignment(0, 0.5)
            r_path.set_alignment(0, 0.5)
            r_targ.set_alignment(0, 0.5)

            r_path.set_size_request(225, -1)
            r_targ.set_size_request(225, -1)

            r_path.set_line_wrap( True )
            r_targ.set_line_wrap( True )

            r_name.set_selectable( True )
            r_path.set_selectable( True )
            r_targ.set_selectable( True )

            info_table.attach( r_name, 1, 2, 0, 1, xpadding=10, ypadding=3 )
            info_table.attach( r_path, 1, 2, 1, 2, xpadding=10, ypadding=3 )
            info_table.attach( r_type, 1, 2, 2, 3, xpadding=10, ypadding=3 )
            info_table.attach( r_targ, 1, 2, 3, 4, xpadding=10, ypadding=3 )
        else:
            info_table = gtk.Table(rows=3, columns=2)

            l_name = gtk.Label()
            l_type = gtk.Label()
            l_path = gtk.Label()

            l_name.set_markup( "<span foreground=\"%s\"><b>Name</b></span>" % subtle_color )
            l_type.set_markup( "<span foreground=\"%s\"><b>Type</b></span>" % subtle_color )
            l_path.set_markup( "<span foreground=\"%s\"><b>Path</b></span>" % subtle_color )

            l_name.set_size_request(48, -1)
            l_type.set_size_request(48, -1)
            l_path.set_size_request(48, -1)

            l_name.set_alignment(1, 0.5)
            l_type.set_alignment(1, 0.5)
            l_path.set_alignment(1, 0.5)

            info_table.attach( l_name, 0, 1, 0, 1, xoptions=gtk.SHRINK )
            info_table.attach( l_path, 0, 1, 1, 2, xoptions=gtk.SHRINK )
            info_table.attach( l_type, 0, 1, 2, 3, xoptions=gtk.SHRINK )

            p,n = os.path.split(path)

            r_name = gtk.Label(n)
            r_type = gtk.Label("%s" % os.path.splitext(n)[1][1:].upper() )
            r_path = gtk.Label(p)

            r_name.set_alignment(0, 0.5)
            r_type.set_alignment(0, 0.5)
            r_path.set_alignment(0, 0.5)

            r_path.set_size_request(225, -1)
            r_path.set_line_wrap( True )

            r_name.set_selectable( True )
            r_path.set_selectable( True )

            info_table.attach( r_name, 1, 2, 0, 1, xpadding=10, ypadding=3 )
            info_table.attach( r_path, 1, 2, 1, 2, xpadding=10, ypadding=3 )
            info_table.attach( r_type, 1, 2, 2, 3, xpadding=10, ypadding=3 )

        icon = colorise.IconDataPreview(
            path,
            size,
            w_ok=os.access(path, os.W_OK),
            )

        icon_hbox = gtk.HBox()
        icon_hbox.pack_start( icon, padding=5 )

        selector = gtk.Button("Select replacement icon")
        selector.set_image( gtk.image_new_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_MENU) )
        if not icon.write_ok: selector.set_sensitive(False)

        guesser = gtk.Button()
        guesser.set_image( gtk.image_new_from_stock(gtk.STOCK_SORT_DESCENDING, gtk.ICON_SIZE_MENU) )
        guesser.set_tooltip_text("Guess other replacement icons")
        guesser.set_sensitive(False)

        resetter = gtk.Button()
        resetter.set_image( gtk.image_new_from_stock(gtk.STOCK_UNDO, gtk.ICON_SIZE_MENU) )
        resetter.set_tooltip_text("Restore default icon")
        resetter.set_sensitive(False)

        redoer = gtk.Button()
        redoer.set_image( gtk.image_new_from_stock(gtk.STOCK_REDO, gtk.ICON_SIZE_MENU) )
        redoer.set_tooltip_text("Redo change")
        redoer.set_sensitive(False)
        redoer.set_size_request(24, -1)

        selector.connect(
            "clicked",
            self.icon_chooser_dialog_cb,
            resetter,
            icon,
            iconset_context,
            iconset_name
            )

        redoer.connect(
            "clicked",
            self.redo_cb,
            redoer,
            resetter,
            icon
            )

        resetter.connect(
            "clicked",
            self.reset_default_icon_path_cb,
            redoer,
            resetter,
            icon
            )

        btn_hbox = gtk.HBox()
        btn_hbox.set_border_width( 5 )
        btn_hbox.pack_start(selector)
        btn_hbox.pack_start(guesser)
        btn_hbox.pack_start(resetter)
        btn_hbox.pack_start(redoer)

        page.pack_start( info_table, False, padding=10 )
        page.pack_start( icon_hbox, False, False, padding=5 )
        page.pack_start( btn_hbox, False, False, padding=3 )

        self.notebook.append_page( page )
        self.notebook.set_tab_label_text( page, tab_label )
        return icon

    def backup_and_replace_icon(self, iconset, key):
        import time
        import shutil
        # backup
        for icon in iconset:
            if icon.cur_path and icon.cur_path != icon.default_path and icon.write_ok:

                if icon.size == 16:
                    self.pb_update_cb( key, 0, icon.pixbuf )
                elif icon.size == 24:
                    self.pb_update_cb( key, 1, icon.pixbuf )
                elif icon.size == 32:
                    self.pb_update_cb( key, 2, icon.pixbuf )

                backup_dir = os.path.join(os.getcwd(), 'backup')
                backup = os.path.join(
                    backup_dir,
                    os.path.split( icon.default_path)[1]+'.backup'+str( time.time() )
                    )

                # backup
                print '\nA backup has been made:\n', backup
                if not os.path.isdir(backup_dir):
                    os.mkdir(backup_dir)
                shutil.copy( icon.default_path, backup )

                # actual file overwrite
                shutil.copy( icon.cur_path, icon.default_path )
        return

    def icon_chooser_dialog_cb(self, selector, resetter, icon, iconset_context, iconset_name ):
        title = "Select a %sx%s/%s/%s icon..." % (icon.size, icon.size, iconset_context.lower(), iconset_name)
        chooser = gtk.FileChooserDialog(
            title,
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK)
            )

        chooser.add_shortcut_folder("/usr/share/icons")
        home_icons = os.path.expanduser( "~/.icons" )
        if os.path.isdir( home_icons ):
            chooser.add_shortcut_folder( home_icons )

        fltr = gtk.FileFilter()
        if icon.size != "scalable":
            fltr.set_name("Images")
            fltr.add_mime_type("image/png")
            fltr.add_mime_type("image/jpeg")
            fltr.add_mime_type("image/svg+xml")
            fltr.add_pattern("*.png")
            fltr.add_pattern("*.jpg")
            fltr.add_pattern(".svg")
            fltr.add_pattern(".svgz")
            fltr.add_pattern("*.xpm")
        else:
            fltr.set_name("SVG")
            fltr.add_mime_type("image/svg+xml")
            fltr.add_pattern(".svg")
            fltr.add_pattern(".svgz")
        chooser.add_filter(fltr)

        fltr = gtk.FileFilter()
        fltr.set_name("All files")
        fltr.add_pattern("*")
        chooser.add_filter(fltr)

        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            self.update_icon_preview(chooser.get_filename(), resetter, icon)
        elif response == gtk.RESPONSE_CANCEL:
            pass
        chooser.destroy()
        return

    def reset_default_icon_path_cb(self, event, redoer, resetter, icon):
        gobject.idle_add( icon.reset_default_icon )
        redoer.set_sensitive(True)
        resetter.set_sensitive(False)
        return

    def redo_cb(self, event, redoer, resetter, icon):
        gobject.idle_add(icon.set_icon, icon.pre_path)
        resetter.set_sensitive(True)
        redoer.set_sensitive(False)
        return

    def update_icon_preview(self, path, resetter, icon):
        gobject.idle_add(icon.set_icon, path)
        resetter.set_sensitive(True)
        return
