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
    def __init__(self, parent_window):
        self.encumbant_focus = None
        gtk.Dialog.__init__(
            self,
            "Icon Set Editor",
            parent_window,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_APPLY, gtk.RESPONSE_APPLY)
            )

        hs = gtk.HSeparator()
        self.header = gtk.Label()
        hbox0 = gtk.HBox()
        align = gtk.Alignment(xalign=0.5, yalign=0.5)
        self.hbox1 = gtk.HBox()
        self.notes = gtk.Label("Select an icon...")
        self.notes.set_line_wrap(True)
        self.notes.set_justify(gtk.JUSTIFY_CENTER)

        btn_box = gtk.HBox()
        self.selector = gtk.Button("Select a replacement icon")
        self.selector.set_image( gtk.image_new_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_MENU) )
        self.selector.set_sensitive(False)
        self.selector.connect("clicked", self.icon_chooser_dialog_cb)

        self.resetter = gtk.Button()
        self.resetter.set_image( gtk.image_new_from_stock(gtk.STOCK_UNDO, gtk.ICON_SIZE_MENU) )
        self.resetter.set_tooltip_text("Restore default icon")
        self.resetter.set_sensitive(False)
        self.resetter.set_size_request(36, -1)
        self.resetter.connect("clicked", self.reset_default_icon_path_cb)

        self.redoer = gtk.Button()
        self.redoer.set_image( gtk.image_new_from_stock(gtk.STOCK_REDO, gtk.ICON_SIZE_MENU) )
        self.redoer.set_tooltip_text("Redo change")
        self.redoer.set_sensitive(False)
        self.redoer.set_size_request(36, -1)
        self.redoer.connect("clicked", self.redo_cb)

        self.vbox.pack_start(self.header, padding=5)
        self.vbox.pack_start(self.notes)
        self.vbox.set_spacing(3)
        self.vbox.pack_start(hs)
        self.vbox.pack_start(hbox0)
        hbox0.add(align)
        align.add(self.hbox1)
        self.vbox.pack_end(btn_box)
        btn_box.pack_start(self.selector)
        btn_box.pack_start(self.resetter)
        btn_box.pack_start(self.redoer)
        return

    def make_dialog(self, Theme, selected_ico):
        self.ico_name = selected_ico
        sizes = list( Theme.get_icon_sizes(selected_ico) )
        sizes.sort()
        if sizes[0] == -1:
            del sizes[0]
            sizes += "scalable",

        self.header.set_markup( "<b>%s</b>" % selected_ico )
        self.ip_list = ()
        pos = 1
        length = len(sizes)
        for size in sizes:
            if type(size) == int:
                path = Theme.lookup_icon(selected_ico, size, 0).get_filename()
                size = "%sx%s" % (size, size)
            else:
                path = Theme.lookup_icon(selected_ico, 64, 0).get_filename()

            ip = colorise.IconPreview(
                path,
                pos,
                length,
                size,
                w_ok=os.access(path, os.W_OK),
                cb=self.icon_sel_cb
                )
            self.ip_list += ip,

            ip.set_tooltip_text(size)
            vbx = gtk.VBox()
            self.hbox1.pack_start(vbx, False, False)
            vbx.pack_start(ip, False, False, padding=5)
            pos += 1
        self.vbox.show_all()

        response = self.run()
        if response == gtk.RESPONSE_APPLY:
            for ip in self.ip_list:
                if ip.cur_path and ip.write_ok:
                    self.backup_and_replace_icon(ip)
        elif response == gtk.RESPONSE_CANCEL:
            pass
        self.destroy()
        return

    def backup_and_replace_icon(self, icon):
        import time
        import shutil
        # backup
        backup_dir = os.path.join(os.getcwd(), 'backup')
        backup = os.path.join( 
            backup_dir,
            os.path.split( icon.default_path)[1]+'.backup'+str( time.time() )
            )
        print '\nA backup has been made:\n', backup
        if not os.path.isdir(backup_dir):
            os.mkdir(backup_dir)
        shutil.copy( icon.default_path, backup )

        # actual file overwrite
        shutil.copy( icon.cur_path, icon.default_path )
        return

    def format_notes(self, i=None):
        if i.write_ok:
            s = str(i.size_label)
        else:
            s = "%s%s" % (i.size_label, ", read-only")
        self.notes.set_text(s)
        return

    def icon_sel_cb(self, successor):
        e = self.encumbant_focus
        if e and e != successor:
            e.relinquish_focus()
        self.format_notes(successor)
        if successor.write_ok and not self.selector.get_property("sensitive"):
            self.selector.set_sensitive(True)
        self.encumbant_focus = successor
        return

    def icon_chooser_dialog_cb(self, *kw):
        e = self.encumbant_focus
        chooser = gtk.FileChooserDialog(
            title="Select a %s %s icon..." % (e.size_label, self.ico_name),
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK)
            )
        chooser.set_default_response(gtk.RESPONSE_CANCEL)
        chooser.add_shortcut_folder("/usr/share/icons")

        filter = gtk.FileFilter()
        if e.size_label != "scalable":
            filter.set_name("Images")
            filter.add_mime_type("image/png")
            filter.add_mime_type("image/jpeg")
            filter.add_mime_type("image/gif")
            filter.add_mime_type("image/svg+xml")
            filter.add_pattern("*.png")
            filter.add_pattern("*.jpg")
            filter.add_pattern(".svg")
            filter.add_pattern(".svgz")
        else:
            filter.set_name("SVG")
            filter.add_mime_type("image/svg+xml")
            filter.add_pattern(".svg")
            filter.add_pattern(".svgz")
        chooser.add_filter(filter)

        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        chooser.add_filter(filter)

        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            self.update_icon_preview(chooser.get_filename(), e)
        elif response == gtk.RESPONSE_CANCEL:
            pass
        chooser.destroy()
        return

    def reset_default_icon_path_cb(self, *kw):
        gobject.idle_add( self.encumbant_focus.reset_default_icon )
        self.redoer.set_sensitive(True)
        kw[0].set_sensitive(False)
        return

    def redo_cb(self, *kw):
        e = self.encumbant_focus
        gobject.idle_add(e.set_icon, e.pre_path)
        self.resetter.set_sensitive(True)
        kw[0].set_sensitive(False)
        return

    def update_icon_preview(self, path, e):
        gobject.idle_add(e.set_icon, path)
        self.resetter.set_sensitive(True)
        return
