
###################################################################################
# oooooooooooo                 .                                            oooo
# `888'     `8               .o8                                            `888
#  888         oooo    ooo .o888oo  .ooooo.  oooo d8b ooo. .oo.    .oooo.    888
#  888oooo8     `88b..8P'    888   d88' `88b `888""8P `888P"Y88b  `P  )88b   888
#  888    "       Y888'      888   888ooo888  888      888   888   .oP"888   888
#  888       o  .o8"'88b     888 . 888    .o  888      888   888  d8(  888   888
# o888ooooood8 o88'   888o   "888" `Y8bod8P' d888b    o888o o888o `Y888""8o o888o
#
###################################################################################


import bpy
import addon_utils

from .. resources.translate import translate

def is_addon_enabled(addon_name):
    """check if lodify is enabled or is here in general"""
    
    return addon_name in bpy.context.preferences.addons

def is_addon_installed(addon_name):
    """check if Lodify is installed but not yet enabled"""

    return addon_name in [mod.bl_info["name"] for mod in addon_utils.modules(refresh=False)]


# ooooo                        .o8   o8o   .o88o.
# `888'                       "888   `"'   888 `"
#  888          .ooooo.   .oooo888  oooo  o888oo  oooo    ooo
#  888         d88' `88b d88' `888  `888   888     `88.  .8'
#  888         888   888 888   888   888   888      `88..8'
#  888       o 888   888 888   888   888   888       `888'
# o888ooooood8 `Y8bod8P' `Y8bod88P" o888o o888o       .8'
#                                                 .o..P'
#                                                 `Y8P'


def enable_lodify(assets, status=False):
    """enable lodify main toggle"""

    if not is_addon_enabled("Lodify"):
        return 

    for o in assets:
        if o.lod_original:
            o.lod_original.lod_enabled = status

    bpy.ops.lodify.data_refresh()

    return 


#   ooooooooo.
#   `888   `Y88.
#    888   .d88'  .ooooo.   .oooooooo
#    888ooo88P'  d88' `88b 888' `88b
#    888`88b.    888ooo888 888   888
#    888  `88b.  888    .o `88bod8P'
#   o888o  o888o `Y8bod8P' `8oooooo.
#                          d"     YD
#                          "Y88888P'



classes  = [
    
    ]


def register():

    # for cls in classes:
    #     bpy.utils.register_class(cls)

    return 



def unregister():

    # for cls in reversed(classes):
    #     bpy.utils.unregister_class(cls)

    return