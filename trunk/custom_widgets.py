#!/usr/bin/env python
# Filename: custom_widgets.py

__licence__ = "LGPLv3"
__copyright__ = "Matthew McGowan, 2008"
__author__ = "Matthew McGowan <matthew.joseph.mcgowan@gmail.com>"


import pygtk
pygtk.require("2.0")

import gtk
import cairo
if cairo.version_info < (1, 4, 0):
	print 'Cairo must be version 1.4.0 or more recent.'
	print 'For more info on Cairo see http://cairographics.org/\n'
	raise SystemExit
from math import pi


class ColorSwatch(gtk.DrawingArea):
    def __init__(self, cb, style, bg=None, txt1=None, txt2=None, tip=None, default=False):
        gtk.DrawingArea.__init__(self)
        self.default = default

        self.bg = bg or style.base[gtk.STATE_NORMAL].to_string()
        self.text_normal = txt1 or style.text[gtk.STATE_NORMAL].to_string()
        self.text_insensitive = txt2 or style.text[gtk.STATE_INSENSITIVE].to_string()

        self.swatch_color_f = self.to_floats(self.bg)
        self.BORDER_COLOR = self.to_floats( style.dark[gtk.STATE_NORMAL] )
        self.SELECTED_COLOR = self.to_floats( style.bg[gtk.STATE_SELECTED] )
        self.unset_focus_cb = cb

        if tip:
            self.set_tooltip_text(tip)

        self.isactive = False
        self.set_size_request(18, 18)
        self.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.connect("expose_event", self.expose)
        self.connect("button-press-event", self.attain_focus_cb)
        return

    def expose(self, widget, event):
        cr = widget.window.cairo_create()
        self.draw(cr)
        return False

    def draw(self, cr):
        rect = self.get_allocation()
        self.draft_rounded_rectangle(cr, rect.width, rect.height, (4,4,4,4), 2, 2+(rect.height-18)/2)
        cr.set_source_rgb(*self.swatch_color_f)
        cr.fill_preserve()
        if self.isactive:
            cr.set_source_rgb( *self.inc_saturation(self.SELECTED_COLOR) )
        else:
            cr.set_line_width(0.5)
            cr.set_source_rgb( *self.BORDER_COLOR )
        cr.stroke()
        if self.default:
            cr.select_font_face(
                "Sans",
                cairo.FONT_SLANT_NORMAL,
                cairo.FONT_WEIGHT_BOLD
                )
            cr.set_font_size(9.0)
            cr.set_source_rgb( *self.SELECTED_COLOR )
            cr.move_to(5.0, 16.0)
            cr.show_text("d")
        return

    def draft_rounded_rectangle(self, cr, width, height, radii, xpad=0, ypad=0):
        nw, ne, se, sw = radii
        cr.new_sub_path()
        cr.arc(nw+xpad, nw+ypad, nw, 180 * (pi / 180), 270 * (pi / 180))
        cr.arc(width-ne-xpad, ne+ypad, ne, 270 * (pi / 180), 0 * (pi / 180))
        cr.arc(width-se-xpad, height-se-ypad, se, 0 * (pi / 180), 90 * (pi / 180))
        cr.arc(sw+xpad, height-sw-ypad, sw, 90 * (pi / 180), 180 * (pi / 180))
        cr.close_path()
        return

    def to_floats(self, rgb, div=255.0):
        # hex to cairo rgb floats
        if type(rgb) == str:
            rgb = rgb[1:]
            step = len(rgb)/3
            if step == 4:
                div = 65535.0
            r = int(rgb[:step], 16) / div
            g = int(rgb[step:2*step], 16) / div
            b = int(rgb[2*step:3*step], 16) / div
        # gtk.gdk.Color to cairo rgb floats
        elif type(rgb) == gtk.gdk.Color:
            r = rgb.red / 65535.0
            g = rgb.green / 65535.0
            b = rgb.blue / 65535.0
        return r, g, b

    def darken(self, rgb, amount=0.175):
        return rgb[0] - amount, rgb[1] - amount, rgb[2] - amount

    def lighten(self, rgb, amount=0.0175):
        return rgb[0] + amount, rgb[1] + amount, rgb[2] + amount

    def inc_saturation(self, rgb, amount=0.15):
        rgb = list(rgb)
        index = [0, 1, 2]
        del index[rgb.index( max(rgb) )]
        for i in index:
            rgb[i] -= amount
            if rgb[i] < 0:
                rgb[i] = 0
        return rgb[0], rgb[1], rgb[2]

    def give_focus(self):
        self.isactive = True
        return self

    def attain_focus_cb(self, *kw):
        self.isactive = True
        self.queue_draw()
        self.unset_focus_cb(self)
        return

    def relinquish_focus(self, *kw):
        self.isactive = False
        self.queue_draw()
        return

    def get_colors(self):
        return self.bg, self.text_normal, self.text_insensitive, self.default


class IconDataPreview(gtk.DrawingArea):
    def __init__(self, path, size, w_ok=False):
        gtk.DrawingArea.__init__(self)
        self.path = path
        self.write_ok = w_ok
        self.size = size
        self.default_path = path
        self.cur_path = None
        self.pre_path = None
        self.pixbuf = gtk.gdk.pixbuf_new_from_file(path)

        x, y = self.pixbuf.get_width(), self.pixbuf.get_height()
        if max(x,y) > 64:
            self.set_size_request(
                x + 8,
                y + 8
                )
        else:
            self.set_size_request(64, 64)

        self.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.connect("expose_event", self.expose)
        return

    def expose(self, widget, event):
        cr = widget.window.cairo_create()
        cr.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
        cr.clip()
        alloc = self.get_allocation()
        self.draw(cr, alloc)
        pb = self.pixbuf
        dest_x = ( alloc.width - pb.get_width() ) / 2
        dest_y = ( alloc.height - pb.get_height() ) / 2
        widget.window.draw_pixbuf(None, pb, 0, 0, dest_x, dest_y, -1, -1)
        return False

    def draw(self, cr, alloc):
        r = 6
        self.draft_rounded_rectangle(cr, alloc.width, alloc.height, (r,r,r,r), 0, 0)
        cr.set_source_rgba(1, 1, 1, 0.85)
        cr.fill()
        return

    def draft_rounded_rectangle(self, cr, width, height, radii, xpad=0, ypad=0):
        nw, ne, se, sw = radii
        if nw:
            cr.new_sub_path()
            cr.arc(nw+xpad, nw+ypad, nw, 180 * (pi / 180), 270 * (pi / 180))
        else:
            cr.move_to(0, 0)
        if ne:
            cr.arc(width-ne-xpad, ne+ypad, ne, 270 * (pi / 180), 0 * (pi / 180))
        else:
            cr.rel_line_to(width-nw, 0)
        if se:
            cr.arc(width-se-xpad, height-se-ypad, se, 0 * (pi / 180), 90 * (pi / 180))
        else:
            cr.rel_line_to(0, height-ne)
        if sw:
            cr.arc(sw+xpad, height-sw-ypad, sw, 90 * (pi / 180), 180 * (pi / 180))
        else:
            cr.rel_line_to(-(width-se), 0)
        cr.close_path()
        return

    def set_icon(self, path):
        self.pre_path = self.cur_path
        self.cur_path = path
        self.pixbuf = gtk.gdk.pixbuf_new_from_file(path)
        self.queue_draw()
        return False

    def reset_default_icon(self):
        self.pre_path = self.cur_path
        self.cur_path = self.default_path
        self.pixbuf = gtk.gdk.pixbuf_new_from_file(self.default_path)
        self.queue_draw()
        return False
