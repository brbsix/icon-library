import os
import store
try:    
    from Cheetah.Template import Template
except:
    print 'python-cheetah not installed.'

class HTML:

  def __init__(self,store,theme):
    filenames = []
    icons = {'icons':store.icon_rows_model, 'theme_name':store.theme.info[1], 'theme':theme, 'filenames':filenames}
    template = Template(file="html_export.cheetah.html",searchList=[icons])
    output = open("icons.html","w")
    output.writelines(template.respond())
    os.system('gnome-open icons.html')
    return


