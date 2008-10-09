#!/usr/bin/env python
# Filename: editor.py

__licence__ = "LGPLv3"
__copyright__ = "Matthew McGowan, 2008"
__author__ = "Matthew McGowan <matthew.joseph.mcgowan@gmail.com>"


import pygtk
pygtk.require("2.0")

import os
import gtk


class IconSetPopupDialog:
    def make(self):
        popup = gtk.Menu()

        edit_action = gtk.Action(
            "Edit",
            "Icon set properties",
            None,
            gtk.STOCK_EDIT
            )

        jump_action = gtk.Action(
            "JumpTo",
            "Jump to target icon",
            None,
            gtk.STOCK_JUMP_TO
            )

        popup.add( edit_action.create_menu_item() )
        popup.add( jump_action.create_menu_item() )
        return popup, (edit_action, jump_action)

    def run(self, Controller, popup, menuitems, treeview, event):
        x = int(event.x)
        y = int(event.y)
        time = event.time
        pthinfo = treeview.get_path_at_pos(x, y)

        if pthinfo is not None:
            treeview.grab_focus()
            path, col, cellx, celly = pthinfo
            results = Controller.IconDB.results[path[0]]

            edit_action, jump_action = menuitems
            if not results[0] != results[1]:
                jump_action.set_sensitive(False)

            edit_action.connect("activate", Controller.edit_iconset_cb, results)
            jump_action.connect("activate", Controller.jump_to_icon_cb, results)

            popup.popup( None, None, None, event.button, time)
        return


class TargetNotFoundDialog:
    def run(self, rname, rpath, root):
        dialog = gtk.Dialog(
            "Target icon not found",
            root,
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


class ThemeChangeDialog:
    def __init__(self, root):
        self.dialog = gtk.Dialog(
            "Change Icon Theme",
            root,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
            )
        self.dialog.set_has_separator(False)
        return

    def run(self, Theme):
        # list all discoverable themes in a combo box 
        theme_sel = gtk.combo_box_new_text() 
        theme_sel.set_tooltip_text("Select an icon theme")

        themes = Theme.list_themes()
        i, active = 0, 0 
        for theme, name, p in themes: 
            name = name or "Unnamed" 
            if theme == Theme.default:
                name += " (default)"
                active = i
            theme_sel.append_text(name)
            i += 1

        theme_sel.set_active(active)
        theme_sel.set_tooltip_text("Select an icon theme") 

        header = gtk.Label() 
        header.set_justify( gtk.JUSTIFY_CENTER )
        header.set_text("Select a new icon theme to view") 

        dialog = self.dialog
        dialog.vbox.pack_start(header, False, False, 8) 
        dialog.vbox.pack_start(theme_sel, False, False, 8)

        dialog.vbox.show_all()
        response = dialog.run()

        if response == gtk.RESPONSE_ACCEPT:
            new_theme = themes[theme_sel.get_active()]

            dialog.action_area.set_sensitive(False)
            theme_sel.set_sensitive(False)

            s = "Loading <b>%s</b>\nThis may take several moments" % new_theme[1]
            header.set_markup(s)

            progress = gtk.ProgressBar()
            progress.show()

            dialog.vbox.pack_end( progress, padding=8 )
            return new_theme, progress
        else:
            dialog.destroy()
            return None, None


class IconSetEditorDialog():
    def __init__(self, root, pb_update_cb ):
        self.pb_update_cb = pb_update_cb
        self.dialog = gtk.Dialog(
            "Icon Set Properties",
            root,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_APPLY, gtk.RESPONSE_APPLY)
            )
        self.dialog.set_has_separator( False )

        self.header = gtk.Label()
        self.header.set_alignment( 0.5, 0.5 )

        self.notebook = gtk.Notebook()
        self.notebook.set_tab_pos( gtk.POS_BOTTOM )
        self.notebook.set_size_request( 300, -1 )
        self.notebook.set_scrollable( True )
        
        self.dialog.vbox.pack_start( self.header, padding=6 )
        self.dialog.vbox.pack_start( self.notebook, padding=8 )
        return

    def run(self, Theme, iconset_data):
        context = iconset_data[2]
        name = iconset_data[1]
        key = iconset_data[0]

        iconset = ()
        sizes = list( Theme.get_icon_sizes(name) )
        sizes.sort()

        if sizes[0] == -1:
            del sizes[0]
            sizes += "scalable",

        self.header.set_markup(
            "<b>%s</b>\n<span size=\"small\">%s</span>" % ( name, context )
            )
        self.header.set_justify( gtk.JUSTIFY_CENTER )

        color = self.dialog.get_style().text[gtk.STATE_INSENSITIVE].to_string()
        for size in sizes:
            icon = self.make_and_append_page(
                Theme,
                context,
                name,
                size,
                color
                )
            iconset += icon,

        self.makelinks = gtk.CheckButton( "Replace with symlinks", False )
        self.makelinks.set_active( True )
        self.dialog.vbox.pack_start( self.makelinks, False, False, padding=3 )

        self.dialog.vbox.show_all()
        response = self.dialog.run()
        if response == gtk.RESPONSE_APPLY:
            for icon in iconset:
                if icon.cur_path and icon.cur_path != icon.default_path:
                    self.replace_icon( Theme.info[2], context, icon, key )
        self.dialog.destroy()
        return

    def make_and_append_page( self, Theme, iconset_context, iconset_name, size, color ):
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

            l_name.set_markup( "<span foreground=\"%s\"><b>Name</b></span>" % color )
            l_type.set_markup( "<span foreground=\"%s\"><b>Type</b></span>" % color )
            l_link.set_markup( "<span foreground=\"%s\"><b>Path</b></span>" % color )
            l_targ.set_markup( "<span foreground=\"%s\"><b>Target</b></span>" % color )

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

            r_name.set_size_request(225, -1)
            r_path.set_size_request(225, -1)
            r_targ.set_size_request(225, -1)

            r_name.set_line_wrap( True )
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

            l_name.set_markup( "<span foreground=\"%s\"><b>Name</b></span>" % color )
            l_type.set_markup( "<span foreground=\"%s\"><b>Type</b></span>" % color )
            l_path.set_markup( "<span foreground=\"%s\"><b>Path</b></span>" % color )

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

            r_name.set_size_request(225, -1)
            r_path.set_size_request(225, -1)

            r_name.set_line_wrap( True )
            r_path.set_line_wrap( True )

            r_name.set_selectable( True )
            r_path.set_selectable( True )

            info_table.attach( r_name, 1, 2, 0, 1, xpadding=10, ypadding=3 )
            info_table.attach( r_path, 1, 2, 1, 2, xpadding=10, ypadding=3 )
            info_table.attach( r_type, 1, 2, 2, 3, xpadding=10, ypadding=3 )

        import custom_widgets
        icon = custom_widgets.IconDataPreview(path, size)

        icon_hbox = gtk.HBox()
        icon_hbox.pack_start( icon, padding=5 )

        selector = gtk.Button("Select replacement icon")
        selector.set_image( gtk.image_new_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_MENU) )

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

    def replace_icon(self, theme, context, icon, key):
        makelinks = self.makelinks.get_active()
        print self.determine_output_location( theme, context, icon )

#        if icon.size == 16:
#            self.pb_update_cb( key, 0, icon.pixbuf )
#        elif icon.size == 24:
#            self.pb_update_cb( key, 1, icon.pixbuf )
#        elif icon.size == 32:
#            self.pb_update_cb( key, 2, icon.pixbuf )

#        backup_dir = os.path.join(os.getcwd(), 'backup')
#        backup = os.path.join(
#            backup_dir,
#            os.path.split( icon.default_path)[1]+'.backup'+str( time.time() )
#            )

#        # backup
#        print '\nA backup has been made:\n', backup
#        if not os.path.isdir(backup_dir):
#            os.mkdir(backup_dir)
#        shutil.move( icon.default_path, backup )

#        if self.makelinks.get_active():
#            # replace icon with a symlink to new icon
#            os.symlink( icon.cur_path, icon.default_path )
#        else:
#            shutil.copy( icon.cur_path, icon.default_path )
        return

    def determine_output_location( self, theme, context, icon ):
        ddst, src = icon.default_path.split('/'), icon.cur_path
        home = os.path.expanduser('~').split('/')
#        ddst_write_ok = os.lstat(ddst).st_uid == pwd.getpwnam( os.getlogin() )[2]

        for i in range( len(home) ):
            ddst[i] = home[i]
        ddst[i+1] = ".icons"
        path = src[0]
        for folder in ddst:
            path = os.path.join( path, folder )

#        if not os.path.exists( os.path.split(path)[0] ):
#            os.makedirs( os.path.split(path)[0] )

#        if makelinks:
#            os.symlink( icon.cur_path, path )
#        else:
#            import shutil
#            shutil.copy( icon.cur_path, path )
        return path

    def icon_chooser_dialog_cb(self, selector, resetter, icon, iconset_context, iconset_name ):
        title = "Select a %sx%s/%s/%s icon..." 
        title = title % (icon.size, icon.size, iconset_context.lower(), iconset_name)

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
        chooser.destroy()
        return

    def reset_default_icon_path_cb(self, event, redoer, resetter, icon):
        icon.reset_default_icon()
        redoer.set_sensitive(True)
        resetter.set_sensitive(False)
        return

    def redo_cb(self, event, redoer, resetter, icon):
        icon.set_icon( icon.pre_path )
        resetter.set_sensitive(True)
        redoer.set_sensitive(False)
        return

    def update_icon_preview(self, path, resetter, icon):
        icon.set_icon( path )
        resetter.set_sensitive(True)
        return
