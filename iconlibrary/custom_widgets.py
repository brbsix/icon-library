#!/usr/bin/env python
# Filename: custom_widgets.py


import cairo
import gtk
import pygtk

__license__ = 'LGPLv3'
__copyright__ = 'Matthew McGowan, 2009'
__author__ = 'Matthew McGowan <matthew.joseph.mcgowan@gmail.com>'

if cairo.version_info < (1, 4, 0):
    print('Cairo must be version 1.4.0 or more recent.')
    print('For more info on Cairo see http://cairographics.org/\n')
    raise SystemExit

pygtk.require('2.0')

# pi constants
M_PI = 3.1415926535897931
PI_OVER_180 = 0.017453292519943295


class ColorSwatch(gtk.DrawingArea):
    def __init__(self, cb, style,
                 bg=None,
                 default=False,
                 insensitive_color=None,
                 normal_color=None,
                 tip=None):

        gtk.DrawingArea.__init__(self)
        self.default = default

        self.bg = bg or style.base[gtk.STATE_NORMAL].to_string()
        self.text_normal = normal_color \
            or style.text[gtk.STATE_NORMAL].to_string()
        self.text_insensitive = insensitive_color \
            or style.text[gtk.STATE_INSENSITIVE].to_string()

        self.swatch_color_f = self.to_floats(self.bg)
        self.BORDER_COLOR = self.to_floats(style.dark[gtk.STATE_NORMAL])
        self.SELECTED_COLOR = self.to_floats(style.bg[gtk.STATE_SELECTED])
        self.unset_focus_cb = cb

        if tip:
            self.set_tooltip_text(tip)

        self.isactive = False
        self.set_size_request(18, 18)
        self.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.connect('expose_event', self.expose)
        self.connect('button-press-event', self.attain_focus_cb)
        return

    def expose(self, widget, event):
        cr = widget.window.cairo_create()
        self.draw(cr)
        return False

    def draw(self, cr):
        cr.save()
        cr.translate(0.5, 0.5)
        cr.set_line_width(1)
        rect = self.get_allocation()
        self.draft_rounded_rectangle(cr, rect.width, rect.height, 2, 2,
                                     2 + (rect.height - 18) / 2)
        cr.set_source_rgb(*self.swatch_color_f)
        cr.fill_preserve()

        if self.isactive:
            cr.set_source_rgb(*self.inc_saturation(self.SELECTED_COLOR))
        else:
            cr.set_source_rgb(*self.BORDER_COLOR)

        cr.stroke()
        cr.restore()
        return

    def draft_rounded_rectangle(self, cr, width, height, r, xpad=0, ypad=0):
        global M_PI, PI_OVER_180
        cr.new_sub_path()
        cr.arc(r + xpad, r + ypad, r, M_PI, 270 * PI_OVER_180)
        cr.arc(width - r - xpad, r + ypad, r, 270 * PI_OVER_180, 0)
        cr.arc(width - r - xpad, height - r - ypad, r, 0, 90 * PI_OVER_180)
        cr.arc(r + xpad, height - r - ypad, r, 90 * PI_OVER_180, M_PI)
        cr.close_path()
        return

    def to_floats(self, rgb, div=255.0):
        # hex to cairo rgb floats
        if isinstance(rgb, str):
            rgb = rgb[1:]
            step = len(rgb) / 3
            if step == 4:
                div = 65535.0
            r = int(rgb[:step], 16) / div
            g = int(rgb[step:2 * step], 16) / div
            b = int(rgb[2 * step:3 * step], 16) / div
        # gtk.gdk.Color to cairo rgb floats
        elif isinstance(rgb, gtk.gdk.Color):
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
        del index[rgb.index(max(rgb))]
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


class IconPreview(gtk.DrawingArea):
    def __init__(self, pixbuf):
        gtk.DrawingArea.__init__(self)

        x, y = pixbuf.get_width(), pixbuf.get_height()
        if max(x, y) >= 72:
            self.set_size_request(x + 8, y + 8)
        else:
            self.set_size_request(72, 72)

        self.connect('expose_event', self.expose, pixbuf)
        return

    def expose(self, widget, event, pixbuf):
        cr = widget.window.cairo_create()
        cr.rectangle(event.area)
        cr.clip()
        alloc = self.get_allocation()
        self.draw(cr, alloc, pixbuf)
        del cr
        return False

    def draw(self, cr, alloc, pb):
        self.draft_rounded_rectangle(cr, 0, 0, alloc.width, alloc.height, 4)
        cr.set_source_rgba(1, 1, 1, 0.85)
        cr.fill()

        dst_x = (alloc.width - pb.get_width()) / 2
        dst_y = (alloc.height - pb.get_height()) / 2
        cr.set_source_pixbuf(pb, dst_x, dst_y)
        cr.paint()
        return

    def draft_rounded_rectangle(self, cr, x, y, w, h, r):
        global M_PI, PI_OVER_180
        cr.new_sub_path()
        cr.arc(r + x, r + y, r, M_PI, 270 * PI_OVER_180)
        cr.arc(w - r, r + y, r, 270 * PI_OVER_180, 0)
        cr.arc(w - r, h - r, r, 0, 90 * PI_OVER_180)
        cr.arc(r + x, h - r, r, 90 * PI_OVER_180, M_PI)
        cr.close_path()
        return
