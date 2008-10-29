#!/usr/bin/env python
# Filename: editor.py

__licence__ = "LGPLv3"
__copyright__ = "Matthew McGowan, 2008"
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
            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_APPLY, gtk.RESPONSE_APPLY)
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
        sizes = list( Theme.get_icon_sizes(name) )
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
            iconset += Icon,

        self.use_links = gtk.CheckButton(
            "Replace icons with symlinks (Recommended)",
            False
            )

        self.use_links.set_active(True)
        self.dialog.vbox.pack_start(self.use_links, False, False, padding=3)

        self.use_links.connect(
            "toggled",
            self.use_links_toggled_cb,
            Icon
            )

        self.dialog.vbox.show_all()
        response = self.dialog.run()

        update_needed = False

        if response == gtk.RESPONSE_APPLY:
            for Icon in iconset:
                if Icon.preview.cur_path \
                and Icon.preview.cur_path != Icon.preview.default_path:
                    self.replace(Icon)
                    update_needed = True

            if update_needed:
                IconDB.pixbuf_cache_update(
                    Theme,
                    name,
                    iconset_data[0] # key
                    )

                Store.model2.clear()
                Store.model2_set_info(
                    IconDB.results,
                    IconDB.pixbuf_cache
                    )

        self.dialog.destroy()
        return

    def make_and_append_page(self, Theme, context, name, size, l_color):
        if type(size) == int:
            path = Theme.lookup_icon(name, size, 0).get_filename()
            tab_label = "%sx%s" % (size, size)
        else:
            path = Theme.lookup_icon(name, 64, 0).get_filename()
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

        selector = gtk.Button("Select replacement icon")
        selector.set_image( gtk.image_new_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_MENU) )

        browser = gtk.Button()
        browser.set_image( gtk.image_new_from_stock(gtk.STOCK_DIRECTORY, gtk.ICON_SIZE_MENU) )
        browser.set_tooltip_text("Open containing folder")

        resetter = gtk.Button()
        resetter.set_image( gtk.image_new_from_stock(gtk.STOCK_UNDO, gtk.ICON_SIZE_MENU) )
        resetter.set_tooltip_text("Restore default icon")
        resetter.set_sensitive(False)

        redoer = gtk.Button()
        redoer.set_image( gtk.image_new_from_stock(gtk.STOCK_REDO, gtk.ICON_SIZE_MENU) )
        redoer.set_tooltip_text("Redo last change")
        redoer.set_sensitive(False)
        redoer.set_size_request(24, -1)

        selector.connect(
            "clicked",
            self.icon_chooser_dialog_cb,
            resetter,
            Icon
            )

        browser.connect(
            "clicked",
            self.gnome_open_cb,
            path
            )

        redoer.connect(
            "clicked",
            self.redo_cb,
            redoer,
            resetter,
            Icon
            )

        resetter.connect(
            "clicked",
            self.reset_default_cb,
            redoer,
            resetter,
            Icon
            )

        btn_hbox = gtk.HBox()
        btn_hbox.set_border_width(5)
        btn_hbox.pack_start(selector)
        btn_hbox.pack_start(browser)
        btn_hbox.pack_start(resetter)
        btn_hbox.pack_start(redoer)

        page = gtk.VBox()

        page.pack_start(info_table, False, padding=10)
        page.pack_end(btn_hbox, False, False, padding=3)
        page.pack_end(icon_hbox, False, False, padding=5)

        self.notebook.append_page(page)
        self.notebook.set_tab_label_text(page, tab_label)
        return Icon

    def make_destination(self, Icon):
        theme, context = Icon.theme, Icon.context
        size, name, preview = Icon.size, Icon.name, Icon.preview

        thm_uid = os.lstat( os.path.split(theme)[0] ).st_uid
        trg_uid = os.lstat( os.path.split(preview.default_path)[0] ).st_uid
        usr_uid = pwd.getpwnam( os.getlogin() ).pw_uid

        if trg_uid == usr_uid:
            dst_split = preview.default_path.split('/')
            dst_plsit = self.check_dst_size(size, dst_split)
            dst_split = self.check_dst_ext(preview.cur_path, dst_split)
            dst = '/'
            for folder in dst_split:
                dst = os.path.join(dst, folder)
            return preview.cur_path, dst

        elif thm_uid == usr_uid:
            base_split = theme.split('/')[1:-1]
        else:
            base_split = os.path.join( os.path.expanduser('~')[1:], ".icons" ).split('/')

        trg_split = preview.default_path.split('/')[1:]

        dst_split = base_split + trg_split[len(base_split):]
        dst_split = self.check_dst_size(size, dst_split)
        dst_split = self.check_dst_ext(preview.cur_path, dst_split)
        dst = '/'
        for folder in dst_split:
            dst = os.path.join(dst, folder)
        return preview.cur_path, dst

    def check_dst_size(self, size, dst_split):
        if str(size) not in dst_split[-3]:
            if type(size) == str:
                dst_split[-3] = size
            else:
                dst_split[-3] = "%sx%s" % (size, size)
        return dst_split

    def check_dst_ext(self, src, dst_split):
        src_ext = os.path.splitext(src)[1]
        dst_fn, dst_ext = os.path.splitext(dst_split[-1])

        if src_ext != dst_ext:
            dst_split[-1] = dst_fn + src_ext
        return dst_split

    def backup(self, src):
        backup_dir = os.path.join(os.getcwd(), 'backup')
        backup = os.path.join(
            backup_dir,
            os.path.split(src)[1] + '.backup.' + str( time.time() )
            )

        if not os.path.isdir(backup_dir):
            os.mkdir(backup_dir)
        shutil.copy( src, backup )

        print 'DEBUG: Backup  >', backup
        return

    def replace(self, Icon):
        src, dst = self.make_destination(Icon)

        print '\nDEBUG: REPLACE ICON!'
        print 'DEBUG: Source  >', Icon.preview.cur_path
        print 'DEBUG: Size    >', Icon.size
        print 'DEBUG: Target  >', os.path.split(Icon.preview.default_path)
        print 'DEBUG: Theme   >', os.path.split(Icon.theme)[0]
        print "DEBUG: Outpath >", dst

        try:
            if self.use_links.get_active():
                self.symlink(src, dst)
            else:
                self.copy(src, dst)
        except Exception, inst:
            print "DEBUG: Error   >", inst
        return

    def symlink(self, src, dst):
        if os.path.lexists(dst):
            self.backup(dst)
            os.remove(dst)

        d = os.path.split(dst)[0]
        if not os.path.isdir(d):
            os.makedirs(d)

        os.symlink(src, dst)
        print "DEBUG: Symlinking... Success!"
        return

    def copy(self, src, dst):
        if os.path.lexists(dst):
            self.backup(dst)
            os.remove(dst)

        d = os.path.split(dst)[0]
        if not os.path.isdir(d):
            os.makedirs(d)

        shutil.copy(src, dst)
        print "DEBUG: Copy... Success!"
        return

    def icon_chooser_dialog_cb(self, selector, resetter, Icon):
        title = "Select a %sx%s/%s/%s icon..."
        size = Icon.size
        
        chooser = gtk.FileChooserDialog(
            title % (size, size, Icon.context.lower(), Icon.name),
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK)
            )

        chooser.add_shortcut_folder("/usr/share/icons")
        home_icons = os.path.expanduser("~/.icons")
        if os.path.isdir(home_icons):
            chooser.add_shortcut_folder(home_icons)

        f = gtk.FileFilter()

        f.set_name("Images")
        f.add_mime_type("image/png")
        f.add_mime_type("image/jpeg")
        f.add_mime_type("image/svg+xml")
        f.add_pattern("*.png")
        f.add_pattern("*.jpg")
        f.add_pattern(".svg")
        f.add_pattern(".svgz")
        f.add_pattern("*.xpm")
        chooser.add_filter(f)

        f = gtk.FileFilter()
        f.set_name("All files")
        f.add_pattern("*")
        chooser.add_filter(f)

        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            fn = chooser.get_filename()
            Icon.preview.set_icon(fn)

            src, dst = self.make_destination(Icon)
            Icon.update_table(dst, src, self.use_links.get_active())

            resetter.set_sensitive(True)

        chooser.destroy()
        return

    def gnome_open_cb(self, button, path):
        os.system("gnome-open %s" % os.path.split(path)[0])
        return

    def reset_default_cb(self, event, redoer, resetter, Icon):
        Icon.preview.reset_default_icon()
        Icon.update_table(Icon.preview.default_path)

        redoer.set_sensitive(True)
        resetter.set_sensitive(False)
        return

    def redo_cb(self, event, redoer, resetter, Icon):
        Icon.preview.set_icon(Icon.preview.pre_path)
        src, dst = self.make_destination(Icon)
        Icon.update_table(dst, src, self.use_links.get_active())

        resetter.set_sensitive(True)
        redoer.set_sensitive(False)
        return

    def use_links_toggled_cb(self, checkbutton, Icon):
        cur_path = Icon.preview.cur_path
        if cur_path and cur_path != Icon.preview.default_path:
            src, dst = self.make_destination(Icon)
            Icon.update_table(dst, src, checkbutton.get_active())
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
