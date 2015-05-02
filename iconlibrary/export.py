#!/usr/bin/env python
# Filename: export.py


from os.path import abspath, dirname, exists, join, pardir

try:
    from Cheetah.Template import Template
except:
    print('python-cheetah not installed')


class HTML:

    def __init__(self, store, theme):
        DATA_PATH = get_data_path()
        TEMPLATE_PATH = join(DATA_PATH, 'export_template.html')

        filenames = []
        icons = {
            'filenames': filenames,
            'icons': store.icon_rows_model,
            'theme': theme,
            'theme_name': store.theme.info[1]
            }
        template = Template(file=TEMPLATE_PATH, searchList=[icons])

        with open('icons.html', 'w') as wfile:
            wfile.writelines(template.respond())

        return


def get_data_path():
    path = abspath(dirname(__file__))

    while path != '/':
        path = abspath(join(path, pardir))

        testpath = join(path, 'share', 'iconlibrary')

        if exists(testpath):
            return testpath

    raise Exception('Unable to determine BASE_PATH')
