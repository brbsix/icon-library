#!/usr/bin/env python
# Filename: searchentry.py

"""
coding: utf-8

SearchEntry - An enhanced search entry with alternating background colouring
              and timeout support

Copyright (C) 2007 Sebastian Heinlein
              2007-2009 Canonical Ltd.

Authors:
 Sebastian Heinlein <glatzor@ubuntu.com>

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; version 3.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along with
this program; if not, write to the Free Software Foundation, Inc., 59 Temple
Place, Suite 330, Boston, MA 02111-1307 USA
"""


import gobject
import gtk

from gettext import gettext as _


class SearchEntry(gtk.Entry):

    # FIMXE: we need 'can-undo', 'can-redo' signals
    __gsignals__ = {'terms-changed': (gobject.SIGNAL_RUN_FIRST,
                                      gobject.TYPE_NONE,
                                      (gobject.TYPE_STRING,))}

    SEARCH_TIMEOUT = 200

    def __init__(self, icon_theme=None):
        """
        Creates an enhanced IconEntry that supports a time out when typing
        and uses a different background colour when the search is active.
        """

        gtk.Entry.__init__(self)
        if not icon_theme:
            icon_theme = gtk.icon_theme_get_default()
        self._handler_changed = self.connect_after('changed',
                                                   self._on_changed)
        self.connect('icon-press', self._on_icon_pressed)

        self.set_icon_from_stock(gtk.ENTRY_ICON_PRIMARY, gtk.STOCK_FIND)
        self.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY, None)

        # Do not draw a yellow bg if an a11y theme is used
        settings = gtk.settings_get_default()
        theme = settings.get_property('gtk-theme-name')
        self._a11y = (theme.startswith('HighContrast') or
                      theme.startswith('LowContrast'))

        # set sensible atk name
        atk_desc = self.get_accessible()
        atk_desc.set_name(_('Search'))

        # data
        self._timeout_id = 0
        self._undo_stack = ['']
        self._redo_stack = []

    def _on_icon_pressed(self, widget, icon, mouse_button):
        """
        Emit the terms-changed signal without any time out when the clear
        button was clicked.
        """

        if icon == gtk.ENTRY_ICON_SECONDARY:
            # clear with no signal and emit manually to avoid the
            # search-timeout
            self.clear_with_no_signal()
            self.grab_focus()
            self.emit('terms-changed', '')
        elif icon == gtk.ENTRY_ICON_PRIMARY:
            self.select_region(0, -1)
            self.grab_focus()

    def undo(self):
        if len(self._undo_stack) <= 1:
            return
        # pop top element and push on redo stack
        text = self._undo_stack.pop()
        self._redo_stack.append(text)
        # the next element is the one we want to display
        text = self._undo_stack.pop()
        self.set_text(text)
        self.set_position(-1)

    def redo(self):
        if not self._redo_stack:
            return
        # just reply the redo stack
        text = self._redo_stack.pop()
        self.set_text(text)
        self.set_position(-1)

    def clear(self):
        self.set_text('')
        self._check_style()

    def clear_with_no_signal(self):
        """Clear and do not send a term-changed signal."""
        self.handler_block(self._handler_changed)
        self.clear()
        self.handler_unblock(self._handler_changed)

    def _emit_terms_changed(self):
        text = self.get_text()
        # add to the undo stack once a term changes
        self._undo_stack.append(text)
        self.emit('terms-changed', text)

    def _on_changed(self, widget):
        """
        Call the actual search method after a small timeout to allow the user
        to enter a longer search term.
        """

        self._check_style()
        if self._timeout_id > 0:
            gobject.source_remove(self._timeout_id)
        self._timeout_id = gobject.timeout_add(self.SEARCH_TIMEOUT,
                                               self._emit_terms_changed)

    def _check_style(self):
        """Use a different background colour if a search is active."""

        # show/hide icon
        if self.get_text() != '':
            self.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY,
                                     gtk.STOCK_CLEAR)
        else:
            self.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY,
                                     None)
        # Based on the Rhythmbox code
        yellowish = gtk.gdk.Color(63479, 63479, 48830)
        black = gtk.gdk.Color(0, 0, 0)
        if self._a11y is True:
            return
        if self.get_text() == '':
            self.modify_base(gtk.STATE_NORMAL, None)
            self.modify_text(gtk.STATE_NORMAL, None)
        else:
            self.modify_base(gtk.STATE_NORMAL, yellowish)
            self.modify_text(gtk.STATE_NORMAL, black)


def on_entry_changed(self, terms):
    print(terms)

if __name__ == '__main__':
    icons = gtk.icon_theme_get_default()
    entry = SearchEntry(icons)
    entry.connect('terms-changed', on_entry_changed)

    win = gtk.Window()
    win.add(entry)
    win.set_size_request(400, 400)
    win.show_all()

    gtk.main()
