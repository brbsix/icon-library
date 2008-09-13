#!/usr/bin/env python
# Filename: editor.py

__licence__ = "LGPLv3"
__copyright__ = "Matthew McGowan, 2008"
__author__ = "Matthew McGowan <matthew.joseph.mcgowan@gmail.com>"


import pygtk
pygtk.require("2.0")

import os
import gtk
import colorise


class IconSetEditorDialog(gtk.Dialog):
    def __init__(self, parent_window):
        self.encumbant_focus = None
        gtk.Dialog.__init__(
            self,
            "Edit Icon Set",
            parent_window,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
            )
        self.set_default_size(100, -1)

        hs = gtk.HSeparator()
        self.header = gtk.Label()
        self.hbox0 = gtk.HBox()
        self.size_note = gtk.Label()

        self.vbox.pack_start(self.header, padding=5)
        self.vbox.set_spacing(3)
        self.vbox.pack_start(hs)
        self.vbox.pack_start(self.hbox0)
        self.vbox.pack_start(self.size_note)
        return

    def make_dialog(self, Theme, selected_ico):
        sizes = list( Theme.get_icon_sizes(selected_ico) )
        sizes.sort()
        if sizes[0] == -1:
            del sizes[0]
            sizes += 56,

        self.header.set_markup( "<b>%s</b>" % selected_ico )
        pos = 1
        length = len(sizes)
        for size in sizes:
            path =  Theme.lookup_icon(selected_ico, size, 0).get_filename()
            ip = colorise.IconPreview(
                gtk.gdk.pixbuf_new_from_file(path),
                pos,
                length,
                cb=self.icon_sel_cb
                )
            if size == 56:
                size = "scalable"
            else:
                size = "%sx%s" % (size, size)
            ip.set_tooltip_text(size)
            vbx = gtk.VBox()
            self.hbox0.pack_start(vbx)
            vbx.pack_start(ip, False, padding=5)
            pos += 1
        self.show_all()
        return

    def set_size_note(self, s):
        self.size_note.set_text(s)
        return

    def icon_sel_cb(self, successor):
        e = self.encumbant_focus
        if e and e != successor:
            e.relinquish_focus()
        self.encumbant_focus = successor
        return
