#!/usr/bin/env python
# Filename: dialogs.py


import gtk
import os
import pygtk

__license__ = 'LGPLv3'
__copyright__ = 'Matthew McGowan, 2009'
__author__ = 'Matthew McGowan <matthew.joseph.mcgowan@gmail.com>'

pygtk.require('2.0')


class IconSetPopupDialog:
    def make(self):
        popup = gtk.Menu()

        edit_action = gtk.Action(
            'Edit',
            'Icon set properties',
            None,
            gtk.STOCK_EDIT
            )

        jump_action = gtk.Action(
            'JumpTo',
            'Jump to target icon',
            None,
            gtk.STOCK_JUMP_TO
            )

        popup.add(edit_action.create_menu_item())
        popup.add(jump_action.create_menu_item())
        return popup, (edit_action, jump_action)

    def run(self, Controller, popup, menuitems, treeview, event):
        x = int(event.x)
        y = int(event.y)
        time = event.time
        pthinfo = treeview.get_path_at_pos(x, y)

        if pthinfo is not None:
            treeview.grab_focus()
            path, col, cellx, celly = pthinfo
            iconset_data = Controller.IconDB.results[path[0]]

            edit_action, jump_action = menuitems
            if not iconset_data[0] != iconset_data[1]:
                jump_action.set_sensitive(False)

            edit_action.connect(
                'activate',
                Controller.edit_iconset_cb,
                iconset_data
                )

            jump_action.connect(
                'activate',
                Controller.jump_to_icon_cb,
                iconset_data
                )

            popup.popup(None, None, None, event.button, time)
        return


class ThemeChangeDialog:
    def __init__(self, root):
        self.dialog = gtk.Dialog(
            'Change Icon Theme',
            root,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CANCEL,
             gtk.RESPONSE_REJECT,
             gtk.STOCK_OK,
             gtk.RESPONSE_ACCEPT)
            )
        self.dialog.set_size_request(300, 192)
        self.dialog.set_has_separator(False)
        return

    def run(self, Theme):
        # list all discoverable themes in a combo box
        theme_sel = gtk.combo_box_new_text()
        theme_sel.set_tooltip_text('Select an icon theme')

        themes = Theme.list_themes()
        i, active = 0, 0
        for theme, name, p in themes:
            name = name or 'Unnamed'
            if theme == Theme.default:
                name += ' (in use)'
                active = i
            theme_sel.append_text(name)
            i += 1

        theme_sel.set_active(active)
        theme_sel.set_tooltip_text('Select an icon theme')

        header = gtk.Label()
        header.set_justify(gtk.JUSTIFY_CENTER)
        header.set_text('Select a new icon theme to view')

        custom = gtk.Button()
        custom.set_tooltip_text('Import an icon theme')
        custom.set_size_request(33, -1)

        custom.set_image(
            gtk.image_new_from_stock(
                gtk.STOCK_OPEN,
                gtk.ICON_SIZE_SMALL_TOOLBAR
                )
            )

        greeter_main_align = gtk.Alignment(xalign=0.5, yalign=0.5)
        greeter_vbox = gtk.VBox()
        greeter_hbox = gtk.HBox()

        greeter_hbox.pack_start(theme_sel, False)
        greeter_hbox.pack_start(custom, False)

        greeter_vbox.pack_start(header, padding=5)
        greeter_vbox.pack_start(greeter_hbox, padding=16)

        greeter_main_align.add(greeter_vbox)

        dialog = self.dialog
        dialog.vbox.add(greeter_main_align)

        custom.connect(
            'clicked',
            self.custom_cb,
            Theme,
            theme_sel
            )

        dialog.vbox.show_all()
        response = dialog.run()

        if response == gtk.RESPONSE_ACCEPT:
            new_theme = themes[theme_sel.get_active()]

            dialog.action_area.set_sensitive(False)
            theme_sel.set_sensitive(False)
            custom.set_sensitive(False)

            s = 'Loading <b>%s</b>\nThis may take several moments' % new_theme[1]
            header.set_markup(s)

            progress = gtk.ProgressBar()
            progress.show()

            greeter_vbox.pack_end(progress, padding=8)
            return new_theme, progress
        else:
            dialog.destroy()
            return None, None

    def custom_cb(self, button, Theme, theme_sel):
        chooser = gtk.FileChooserDialog(
            'Import an icon theme',
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(
                gtk.STOCK_CANCEL,
                gtk.RESPONSE_CANCEL,
                gtk.STOCK_OPEN,
                gtk.RESPONSE_OK
                )
            )

        fltr = gtk.FileFilter()
        fltr.set_name('Theme Index')
        fltr.add_pattern('index.theme')
        chooser.add_filter(fltr)

        fltr = gtk.FileFilter()
        fltr.set_name('All files')
        fltr.add_pattern('*')
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
            theme_sel.set_active(len(Theme.all_themes))
            Theme.all_themes.append(theme)
            Theme.prepend_search_path(os.path.split(theme_root)[0])

        chooser.destroy()
        return
