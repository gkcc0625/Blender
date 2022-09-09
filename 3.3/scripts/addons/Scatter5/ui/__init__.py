
#####################################################################################################
#
#  ooooo     ooo ooooo
#  `888'     `8' `888'
#   888       8   888
#   888       8   888
#   888       8   888
#   `88.    .8'   888
#     `YbodP'    o888o
#
#####################################################################################################


import bpy

from . import templates 
from . import ui_menus
from . import ui_creation
from . import ui_tweaking
from . import ui_extra
from . import ui_choose_emitter
from . import ui_addon
from . import ui_manual
from . import biome_library
from . import open_manager


#   ooooooooo.
#   `888   `Y88.
#    888   .d88'  .ooooo.   .oooooooo
#    888ooo88P'  d88' `88b 888' `88b
#    888`88b.    888ooo888 888   888
#    888  `88b.  888    .o `88bod8P'
#   o888o  o888o `Y8bod8P' `8oooooo.
#                          d"     YD
#                          "Y88888P'

classes  =  []
classes +=  ui_menus.classes
classes +=  ui_creation.classes
classes +=  ui_tweaking.classes
classes +=  ui_extra.classes
classes +=  ui_choose_emitter.classes
classes +=  ui_addon.classes
classes +=  ui_manual.classes
classes +=  biome_library.classes
classes +=  open_manager.classes


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    biome_library.register()

    return 


def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    biome_library.unregister()
    
    return



#if __name__ == "__main__":
#    register()