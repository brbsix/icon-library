#!/usr/bin/env python
# Filename: editor.py

__licence__ = "LGPLv3"
__copyright__ = "Matthew McGowan, 2009"
__author__ = "Matthew McGowan <matthew.joseph.mcgowan@gmail.com>"


import pygtk
pygtk.require("2.0")

import os
import gtk
import pwd
import time
import shutil
from custom_widgets import IconPreview


class IconSetEditorDialog:
    def __init__(self, root):
        self.dialog = gtk.Dialog(
            "Icon Set Properties",
            root,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CLOSE, gtk.RESPONSE_REJECT)
            )
        self.dialog.set_has_separator(False)

        self.header = gtk.Label()
        self.header.set_alignment(0.5, 0.5)

        self.notebook = gtk.Notebook()
        self.notebook.set_tab_pos(gtk.POS_BOTTOM)
        self.notebook.set_size_request(300, -1)
        self.notebook.set_scrollable(True)

        self.dialog.vbox.pack_start(self.header, padding=6)
        self.dialog.vbox.pack_start(self.notebook, padding=8)
        return

    def run(self, Theme, IconDB, Store, iconset_data):
        context = iconset_data[2]
        name = iconset_data[1]

        iconset = ()
        sizes = list(Theme.get_icon_sizes(name))
        sizes.sort()

        if sizes[0] == -1:
            del sizes[0]
            sizes += "scalable",

        self.header.set_markup(
            "<b>%s</b>\n<span size=\"small\">%s - %s</span>" % (name, Theme.info[1], context)
            )
        self.header.set_justify(gtk.JUSTIFY_CENTER)

        l_color = self.dialog.get_style().text[gtk.STATE_INSENSITIVE].to_string()
        for size in sizes:
            Icon = self.make_and_append_page(
                Theme,
                context,
                name,
                size,
                l_color
                )
            if Icon: iconset += Icon,

        self.dialog.vbox.show_all()
        response = self.dialog.run()
        self.dialog.destroy()
        return

    def make_and_append_page(self, Theme, context, name, size, l_color):
        if type(size) == int:
            path = Theme.lookup_icon(name, size, 0).get_filename()
            tab_label = "%sx%s" % (size, size)
        else:
            path = Theme.lookup_icon(name, 64, gtk.ICON_LOOKUP_FORCE_SVG).get_filename()
            tab_label = size

        Icon = IconInfo(l_color)
        Icon.set_info(
            Theme.info[2],
            context,
            name,
            size,
            path
            )

        info_table = Icon.get_table()
        preview = Icon.get_preview()

        icon_hbox = gtk.HBox()
        icon_hbox.pack_start(preview, padding=5)

        browser = gtk.Button()
        browser.set_label('Locate on disk')
        browser.set_image(gtk.image_new_from_stock(gtk.STOCK_DIRECTORY, gtk.ICON_SIZE_MENU))
        browser.set_tooltip_text("Open containing folder")

        gimper = gtk.Button()
        gimper.set_label('Open with the GIMP')
        gimper.set_image(gtk.image_new_from_icon_name("gimp", gtk.ICON_SIZE_MENU))

        browser.connect(
            "clicked",
            self.gnome_open_cb,
            path
            )

        gimper.connect(
            "clicked",
            self.open_with_gimp_cb,
            path
            )

        btn_hbox = gtk.HBox()
        btn_hbox.set_border_width(5)
        btn_hbox.pack_start(browser)
        btn_hbox.pack_start(gimper)

        page = gtk.VBox()

        page.pack_start(info_table, False, padding=10)
        page.pack_end(btn_hbox, False, False, padding=3)
        page.pack_end(icon_hbox, False, False, padding=5)

        self.notebook.append_page(page)
        self.notebook.set_tab_label_text(page, tab_label)
        return Icon

    def gnome_open_cb(self, button, path):
        folder = os.path.split(path)[0]
        print "Opening", folder
        os.system("gnome-open %s &" % folder)
        return

    def open_with_gimp_cb(self, button, path):
        print "Gimping", path
        os.system("gimp %s &" % path)
        return


class IconInfo:
    def __init__(self, l_color):
        self.l_color = l_color

        l_name = gtk.Label()
        l_type = gtk.Label()
        l_path = gtk.Label()
        l_targ = gtk.Label()

        r_name = gtk.Label()
        r_type = gtk.Label()
        r_path = gtk.Label()
        r_targ = gtk.Label()

        self.table = gtk.Table(rows=4, columns=2)

        self.labels = {
            "Name":(0, 1, l_name, r_name),
            "Path":(1, 2, l_path, r_path),
            "Type":(2, 3, l_type, r_type),
            "Target":(3, 4, l_targ, r_targ)
            }
            
        self.setup_layout(
            self.table,
            self.labels,
            self.l_color
            )
        return

    def setup_layout(self, table, labels, l_color):
        for k, label in labels.iteritems():
            i, j, l_label, r_label = label
            l_label.set_size_request(48, -1)
            l_label.set_alignment(1, 0.5)
            l_label.set_markup(
                "<span foreground=\"%s\"><b>%s</b></span>" % (l_color, k)
                )

            r_label.set_size_request(225, -1)
            r_label.set_alignment(0, 0.5)
            r_label.set_selectable(True)
            r_label.set_line_wrap(True)

            table.attach(l_label, 0, 1, i, j, xoptions=gtk.SHRINK)
            table.attach(r_label, 1, 2, i, j, xpadding=10, ypadding=3)
        return

    def set_info(self, theme, context, name, size, path):
        self.theme = theme
        self.context = context
        self.name = name
        self.size = size
        self.path = path
        self.target = None

        self.preview = IconPreview(path, size)
        self.update_table(path)
        return

    def update_table(self, path, src=None, use_links=False):
        if src and use_links:
            p, n, t, targ = self.format_unwritten_link_info(src, path)
        elif src and not use_links:
            p, n, t, targ = self.format_unwritten_real_info(path)
        elif os.path.islink(path):
            p, n, t, targ = self.format_link_info(path)
        else:
            p, n, t, targ = self.format_real_info(path)

        labels = self.labels
        labels["Name"][3].set_text(n)
        labels["Path"][3].set_text(p)
        labels["Type"][3].set_text(t)
        labels["Target"][3].set_text(targ)
        return

    def format_link_info(self, path):
        p,n = os.path.split(path)
        t = "%s " % os.path.splitext(n)[1][1:].upper()
        t += "(Linked to %s)" % os.path.splitext( os.path.realpath(path) )[1][1:].upper()
        return p, n, t, os.path.realpath(path)

    def format_real_info(self, path):
        p, n = os.path.split(path)
        t = "%s" % os.path.splitext(n)[1][1:].upper()
        return p, n, t, "n/a"

    def format_unwritten_link_info(self, src, dst):
        p,n = os.path.split(dst)
        t = "%s " % os.path.splitext(n)[1][1:].upper()
        t += "(Linked to %s) [Pending write]" % os.path.splitext(src)[1][1:].upper()
        return p, n, t, src

    def format_unwritten_real_info(self, dst):
        p, n = os.path.split(dst)
        t = "%s [Pending write]" % os.path.splitext(n)[1][1:].upper()
        return p, n, t, "n/a"

    def get_table(self):
        return self.table

    def get_preview(self):
        return self.preview
