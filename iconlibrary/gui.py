#!/usr/bin/env python
# Filename: gui.py


import gtk


class IconLibraryGui:
    def __init__(self):
        # setup the root window
        self.root = gtk.Window(type=gtk.WINDOW_TOPLEVEL)
        self.root.set_default_size(900, 640)
        self.root.set_title('Icon Library')
        self.vbox = gtk.VBox()
        self.root.add(self.vbox)
        return

    def make_greeter(self, Theme, callback):
        """Greets the user and offers a range of themes to choose from."""
        # list all discoverable themes in a combo box
        theme_sel = gtk.combo_box_new_text()
        theme_sel.set_tooltip_text('Select an icon theme')

        i, active = 0, 0
        themes = Theme.list_themes()
        themes.sort()
        for theme, name, p in themes:
            name = name or 'Unnamed'
            if theme == Theme.default:
                name += ' (in use)'
                active = i
            theme_sel.append_text(name)
            i += 1
        theme_sel.set_active(active)

        header = gtk.Label()
        header.set_justify(gtk.JUSTIFY_CENTER)
        header.set_text('Select the icon theme you would like to view')

        go = gtk.Button()
        go.set_tooltip_text('Load selected icon theme')
        go.set_size_request(33, -1)
        go.set_image(
            gtk.image_new_from_icon_name('dialog-ok',
                                         gtk.ICON_SIZE_SMALL_TOOLBAR)
            )

        custom = gtk.Button()
        custom.set_tooltip_text('Import an icon theme')
        custom.set_size_request(33, -1)
        custom.set_image(
            gtk.image_new_from_icon_name('document-open',
                                         gtk.ICON_SIZE_SMALL_TOOLBAR)
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
            'clicked',
            self.custom_cb,
            Theme,
            theme_sel
            )

        go.connect(
            'clicked',
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

        self.setup_top_toolbar(Controller, Theme, vbox)

        self.icons_scroller = self.create_scroller()
        vbox.add(self.icons_scroller)

        self.setup_listviews(Controller, Display)

        self.setup_export_button(Controller)

        self.setup_bottom_toolbar(vbox, Display)

        self.setup_feedback_label(IconDB, self.status_hbox)

        self.setup_color_swatches(Controller, self.color_swatches_hbox)
        return

    def setup_top_toolbar(self, Controller, Theme, vbox):
        import pango
        import searchentry

        self.avatar_button = gtk.Button()
        self.avatar_button.set_relief(gtk.RELIEF_NONE)
        self.avatar_button.set_tooltip_text('Switch theme')
        self.avatar_button.set_image(self.make_avatar(Theme))

        self.header_label = gtk.Label()
        self.header_label.set_max_width_chars(40)
        self.header_label.set_ellipsize(pango.ELLIPSIZE_END)
        self.header_label.set_markup(self.make_header(Theme))

        self.standard_check = gtk.CheckButton(
            label='Hide non-standard icons',
            use_underline=False
            )
        self.standard_check.set_tooltip_text(
            'Choose to display icons that conform to the\nfreedesktop.org Icon Naming Specification'
            )

        self.inherited_check = gtk.CheckButton(
            label='Hide inherited icons',
            use_underline=False
            )
        self.inherited_check.set_tooltip_text(
            'Choose to display icons that have been\ninherited from other themes'
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
            'clicked',
            Controller.change_theme_cb
            )

        self.standard_check.connect(
            'toggled',
            Controller.standard_filter_cb
            )

        self.inherited_check.connect(
            'toggled',
            Controller.inherited_filter_cb
            )

        self.text_entry.connect(
            'terms-changed',
            Controller.search_entry_cb
            )
        return

    def create_scroller(self):
        scroller = gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
        scroller.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroller.set_shadow_type(gtk.SHADOW_IN)
        return scroller

    def setup_listviews(self, Controller, Display):
        filters_view, icon_set_view = Display.filters_view, \
                                      Display.icon_set_view

        # self.icons_scroller.add(filters_view)
        self.icons_scroller.add(icon_set_view)

        filters_view.connect('changed',
                             Controller.context_filter_cb)

        icon_set_view.connect_after('button-release-event',
                                    Controller.row_activated_cb)

        icon_set_view.connect('row-activated',
                              Controller.row_activated_2click_cb)
        return

    def setup_export_button(self, Controller):
        button = gtk.Button()

        button.set_image(
            gtk.image_new_from_icon_name('document-export',
                                         gtk.ICON_SIZE_SMALL_TOOLBAR))

        button.set_label('Export HTML')

        button.connect('clicked', Controller.export)

        self.export_button = button
        return

    def setup_bottom_toolbar(self, vbox, Display):
        btm_hbox = gtk.HBox()
        btm_hbox.set_homogeneous(False)

        self.status_hbox = gtk.HBox()
        self.color_swatches_hbox = gtk.HBox()

        for widget in [Display.filters_view,
                       self.color_swatches_hbox,
                       self.status_hbox,
                       self.export_button]:

            btm_hbox.add(widget)
            btm_hbox.set_child_packing(
                widget, False, False, 0, gtk.PACK_START)

        btm_hbox.set_child_packing(
            self.status_hbox, True, True, 0, gtk.PACK_START)

        vbox.pack_end(btm_hbox, False)
        return

    def setup_feedback_label(self, IconDB, btm_hbox):
        self.feedback_label = gtk.Label()
        self.feedback_label.set_alignment(0.5, 0.5)
        self.feedback_label.set_size_request(-1, 24)

        self.feedback_label.set_markup(
            'Displaying <b>%s</b> icons' % (IconDB.get_length())
            )

        btm_hbox.pack_end(self.feedback_label)
        return

    def setup_color_swatches(self, Controller, btm_hbox):
        import custom_widgets

        style = self.root.get_style()
        cb = Controller.change_bg_color_cb

        options = [
            {'name': 'Default', 'default': True},
            {'name': 'White', 'color': '#FFFFFF'},
            {'name': 'Grey', 'color': '#9C9C9C', 'insensitive': '#525252'},
            {'name': 'Dark Grey', 'color': '#525252', 'normal': '#E6E6E6', 'insensitive': '#9E9E9E'}
        ]

        color_widgets = []

        for o in options:
            w = custom_widgets.ColorSwatch(
                cb, style,
                bg=o.get('color', None),
                default=o.get('default', False),
                insensitive_color=o.get('insensitive', None),
                normal_color=o.get('normal', None),
                tip=o['name'])

            color_widgets.append(w)

        Controller.cswatch_focus = color_widgets[0].give_focus()

        for sel in reversed(color_widgets):
            a = gtk.Alignment(0.5, 0.5)
            a.add(sel)
            btm_hbox.pack_end(a, False)

        btm_hbox.show_all()
        return

    def make_header(self, Theme):
        name = Theme.info[1] or 'Unnamed'
        comment = Theme.read_comment(Theme.info[2]) or 'No comment'
        return '<b>%s</b>\n<span size=\'small\'>%s</span>' % (name, comment)

    def make_avatar(self, Theme):
        try:
            return gtk.image_new_from_pixbuf(Theme.load_icon('folder', 32, 0))
        except:
            return gtk.image_new_from_icon_name('folder', gtk.ICON_SIZE_DND)

    def set_feedback(self, IconDB, term, num_of_results):
        """Displays basic search stats in the GUI."""
        std = ''
        if IconDB.standard_only:
            std = 'standard '
        if term == '':
            s = '<b>%s</b> %sicons in <b>%s</b>' % (num_of_results,
                                                    std,
                                                    IconDB.ctx_filter)
        else:
            s = '<b>%s</b> %sresults for <b>%s</b> in <b>%s</b>'
            s = s % (num_of_results, std, term, IconDB.ctx_filter)
        self.feedback_label.set_markup(s)
        return

    def custom_cb(self, button, Theme, theme_sel):

        from os.path import split

        chooser = gtk.FileChooserDialog(
            'Import an icon theme',
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL,
                     gtk.RESPONSE_CANCEL,
                     gtk.STOCK_OPEN,
                     gtk.RESPONSE_OK)
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
                split(theme_root)[1],
                Theme.read_name(index_path),
                index_path
                )

            theme_sel.append_text(theme[1])
            theme_sel.set_active(len(Theme.all_themes))
            Theme.all_themes.append(theme)
            Theme.prepend_search_path(split(theme_root)[0])

        chooser.destroy()
        return

    def loading_cb(self, go, Theme, header, themes, theme_sel,
                   custom, greeter_vbox, callback):
        """Begin loading the theme chosen at the greeter gui."""

        Theme.set_theme(themes[theme_sel.get_active()])

        go.set_sensitive(False)
        for w in (theme_sel, custom, go):
            w.set_sensitive(False)

        s = 'Loading <b>%s</b>\nThis may take several moments' % Theme.info[1]
        header.set_markup(s)

        progress = gtk.ProgressBar()
        greeter_vbox.pack_end(progress)
        progress.show()

        callback(Theme, progress)
        return
