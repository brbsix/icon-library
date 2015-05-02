#!/usr/bin/env python
# Filename: editor.py


import gtk
import os
import pygtk

from custom_widgets import IconPreview

__license__ = 'LGPLv3'
__copyright__ = 'Matthew McGowan, 2009'
__author__ = 'Matthew McGowan <matthew.joseph.mcgowan@gmail.com>'

pygtk.require('2.0')

# pi constants
M_PI = 3.1415926535897931
PI_OVER_180 = 0.017453292519943295


class IconSetEditorDialog:
    def __init__(self, root):
        self.dialog = gtk.Dialog(
            'Icon Set Properties',
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

        self.dialog.set_border_width(3)
        self.dialog.vbox.pack_start(self.header, padding=6)
        self.dialog.vbox.pack_start(self.notebook, padding=8)
        return

    def run(self, Theme, IconDB, Store, iconset_data):
        context = iconset_data[2]
        name = iconset_data[1]
        sizes, msizes = self.get_sizes(Theme, name)

        self.header.set_markup(
            '<b>%s</b>\n<span size="small">%s - %s</span>' % (name,
                                                              Theme.info[1],
                                                              context)
            )
        self.header.set_justify(gtk.JUSTIFY_CENTER)

        iconset = ()
        l_color = self.dialog.get_style().text[gtk.STATE_INSENSITIVE].to_string()
        for size in msizes:
            Icon = self.make_and_append_page(
                Theme, context, name, size, l_color)
            if Icon:
                iconset += Icon,

        if len(sizes) != len(msizes):
            def bg(note, event):
                cr = note.window.cairo_create()
                a = note.allocation
                cr.rectangle(a)
                cr.clip()
                rounded_rectangle(
                    cr, a.x + 0.5, a.y + 0.5, a.width - 1, a.height - 1, 3)
                cr.set_source_rgb(*floats_from_string('#FFE2D6'))
                cr.fill_preserve()
                cr.set_source_rgb(*floats_from_string('#FF743B'))
                cr.set_line_width(1)
                cr.stroke()
                del cr
                return

            note = gtk.Label()
            note.set_line_wrap(True)
            note.set_markup('<small>The IconTheme incorrectly reports available icon sizes\nSizes discovered: %s\nSizes reported by %s: %s</small>' % (msizes, Theme.info[1], sizes))

            note_align = gtk.Alignment(0.0, 0.5)
            note_align.set_border_width(5)
            note_align.add(note)

            note_align.connect('expose-event', bg)

            self.dialog.vbox.pack_start(note_align, False, padding=3)

        self.notebook.grab_focus()
        self.dialog.vbox.show_all()
        response = self.dialog.run()
        self.dialog.destroy()
        return

    def get_sizes(self, Theme, name):
        theme_sizes = list(Theme.get_icon_sizes(name))

        path = Theme.lookup_icon(name, 24, 0).get_filename()
        if self.is_size_context_fstruct(path):
            manual_sizes = self.size_context_manually_find_sizes(path, name)
        else:
            manual_sizes = self.context_size_manually_find_sizes(path, name)

        theme_sizes.sort()
        manual_sizes.sort()
        return theme_sizes, manual_sizes

    def is_size_context_fstruct(self, path):
        search_path = '/'+os.path.join(*path.split('/')[:-3])

        is_digit = False
        i = 0
        for f in os.listdir(search_path):
            p = os.path.join(search_path, f)
            if os.path.isdir(p) and f[0].isdigit():
                if i > 2:
                    break
                is_digit = True
                break
            elif os.path.isdir(p):
                i += 1

        return is_digit

    def size_context_manually_find_sizes(self, path, name):
        search_path = '/'+os.path.join(*path.split('/')[:-3])
        ctx = path.split('/')[-2]

        manual_sizes = []
        for f in os.listdir(search_path):
            d = os.path.join(search_path, f, ctx)
            if os.path.isdir(d):
                for fn in os.listdir(d):
                    if os.path.splitext(fn)[0] == name:
                        manual_sizes.append(self.parse_size(f))
                        break
        return manual_sizes

    def context_size_manually_find_sizes(self, path, name):
        search_path = '/'+os.path.join(*path.split('/')[:-2])
        manual_sizes = []
        for f in os.listdir(search_path):
            d = os.path.join(search_path, f)
            if os.path.isdir(d):
                for fn in os.listdir(d):
                    if os.path.splitext(fn)[0] == name:
                        manual_sizes.append(self.parse_size(f))
                        break
        return manual_sizes

    def parse_size(self, size):
        if isinstance(size, int) or size == 'scalable':
            return size
        try:
            size = int(size)
            return size
        except:
            pass
        try:
            size = int(size.split('x')[0])
            return size
        except:
            print('Size not parsable:', size)
        return size

    def make_and_append_page(self, Theme, context, name, size, l_color):
        if isinstance(size, int):
            path = Theme.lookup_icon(name, size, 0).get_filename()
            pixbuf = Theme.load_icon(name, size, 0)
            tab_label = '%sx%s' % (size, size)
        else:
            path = Theme.lookup_icon(
                name, 64, gtk.ICON_LOOKUP_FORCE_SVG).get_filename()
            pixbuf = Theme.load_icon(
                name, 64, gtk.ICON_LOOKUP_FORCE_SVG)
            tab_label = size

        Icon = IconInfo(l_color)
        Icon.set_info(
            Theme.info[2],
            context,
            name,
            size,
            path,
            pixbuf
            )

        info_table = Icon.get_table()
        preview = Icon.get_preview()

        icon_hbox = gtk.HBox()
        icon_hbox.pack_start(preview, padding=5)

        browser = gtk.Button()
        browser.set_image(gtk.image_new_from_stock(gtk.STOCK_DIRECTORY,
                                                   gtk.ICON_SIZE_MENU))
        browser.set_tooltip_text('Open containing folder')

        gimper = gtk.Button('Open with...')

        browser.connect(
            'clicked',
            self.open_folder_cb,
            path
            )

        gimper.connect(
            'clicked',
            self.open_file_cb,
            path
            )

        btn_hbox = gtk.HBox()
        btn_hbox.set_border_width(5)
        btn_hbox.pack_end(browser, False)
        btn_hbox.pack_end(gimper, False)

        page = gtk.VBox()

        page.pack_start(info_table, False, padding=10)
        page.pack_end(btn_hbox, False, False, padding=3)
        page.pack_end(icon_hbox, False, False, padding=5)

        self.notebook.append_page(page)
        self.notebook.set_tab_label_text(page, tab_label)
        return Icon

    def open_folder_cb(self, button, path):
        folder = os.path.split(path)[0]
        os.system('gnome-open %s &' % folder)
        return

    def open_file_cb(self, button, path):
        os.system('gnome-open %s &' % path)
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
            'Name': (0, 1, l_name, r_name),
            'Path': (1, 2, l_path, r_path),
            'Type': (2, 3, l_type, r_type),
            'Target': (3, 4, l_targ, r_targ)
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
                '<span foreground="%s"><b>%s</b></span>' % (l_color, k)
                )

            r_label.set_size_request(225, -1)
            r_label.set_alignment(0, 0.5)
            r_label.set_selectable(True)
            r_label.set_line_wrap(True)

            table.attach(l_label, 0, 1, i, j, xoptions=gtk.SHRINK)
            table.attach(r_label, 1, 2, i, j, xpadding=10, ypadding=3)
        return

    def set_info(self, theme, context, name, size, path, pixbuf):
        self.theme = theme
        self.context = context
        self.name = name
        self.size = size
        self.path = path
        self.pixbuf = pixbuf
        self.target = None

        self.preview = IconPreview(pixbuf)
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
        labels['Name'][3].set_text(n)
        labels['Path'][3].set_text(p)
        labels['Type'][3].set_text(t)
        labels['Target'][3].set_text(targ)
        return

    def format_link_info(self, path):
        p, n = os.path.split(path)
        t = '%s ' % os.path.splitext(n)[1][1:].upper()
        t += '(Linked to %s)' % os.path.splitext(os.path.realpath(path))[1][1:].upper()
        return p, n, t, os.path.realpath(path)

    def format_real_info(self, path):
        p, n = os.path.split(path)
        t = '%s' % os.path.splitext(n)[1][1:].upper()
        return p, n, t, 'n/a'

    def format_unwritten_link_info(self, src, dst):
        p, n = os.path.split(dst)
        t = '%s ' % os.path.splitext(n)[1][1:].upper()
        t += '(Linked to %s) [Pending write]' % os.path.splitext(src)[1][1:].upper()
        return p, n, t, src

    def format_unwritten_real_info(self, dst):
        p, n = os.path.split(dst)
        t = '%s [Pending write]' % os.path.splitext(n)[1][1:].upper()
        return p, n, t, 'n/a'

    def get_table(self):
        return self.table

    def get_preview(self):
        return self.preview


def floats_from_string(spec):
    color = gtk.gdk.color_parse(spec)
    return color.red_float, color.green_float, color.blue_float


def rounded_rectangle(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.translate(x, y)
    cr.arc(r, r, r, M_PI, 270 * PI_OVER_180)
    cr.arc(w - r, r, r, 270 * PI_OVER_180, 0)
    cr.arc(w - r, h - r, r, 0, 90 * PI_OVER_180)
    cr.arc(r, h - r, r, 90 * PI_OVER_180, M_PI)
    cr.close_path()
    return
