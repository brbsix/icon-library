#!/usr/bin/env python
# Filename: standards.py


import gtk
import threading


class InfoModel:
    def __init__(self):

        self.contexts_model = gtk.ListStore(str)

        self.icon_rows_model = gtk.ListStore(
            str,
            str,
            gtk.gdk.Pixbuf,
            gtk.gdk.Pixbuf,
            gtk.gdk.Pixbuf,
            str
            )
        return

    def contexts_model_set_info(self, Theme):
        self.theme = Theme
        from standards import StandardIconNamingSpec
        spec = StandardIconNamingSpec()

        self.contexts_model.clear()
        self.contexts_model.append(['All Contexts'])

        ctxs = list(Theme.list_contexts())
        ctxs.sort()
        for ctx in ctxs:
            comments = spec.get_context_comment(ctx)
            self.contexts_model.append([ctx])
        return

    def icon_rows_model_set_info(self, results, pixbuf_cache):
        appender = threading.Thread(
            target=self.__icon_rows_model_appender,
            args=(results, pixbuf_cache)
            )
        appender.start()
        return

    def __icon_rows_model_appender(self, results, pixbuf_cache):
        for key, ico, context, standard, scalable, inherited, inherited_name in results:
            if key in pixbuf_cache:
                pb0 = pixbuf_cache[key][0]
                pb1 = pixbuf_cache[key][1]
                pb2 = pixbuf_cache[key][2]

                notes = None
                if key != ico:
                    notes = 'Symlink'
                if not scalable:
                    if not notes:
                        notes = 'Fixed Only'
                    else:
                        notes += ', Fixed Only'
                if not inherited:
                    if not notes:
                        notes = ""
                    notes += '\nInherited from %s' % inherited_name
                # if standard:
                #     ico = '<b>%s</b>' % ico

                gtk.gdk.threads_enter()
                self.icon_rows_model.append((ico, context, pb0,
                                             pb1, pb2, notes))
                gtk.gdk.threads_leave()
        return
