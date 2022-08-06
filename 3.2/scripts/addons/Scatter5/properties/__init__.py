

#####################################################################################################
#
# ooooooooo.                                                        .    o8o
# `888   `Y88.                                                    .o8    `"'
#  888   .d88' oooo d8b  .ooooo.  oo.ooooo.   .ooooo.  oooo d8b .o888oo oooo   .ooooo.   .oooo.o
#  888ooo88P'  `888""8P d88' `88b  888' `88b d88' `88b `888""8P   888   `888  d88' `88b d88(  "8
#  888          888     888   888  888   888 888ooo888  888       888    888  888ooo888 `"Y88b.
#  888          888     888   888  888   888 888    .o  888       888 .  888  888    .o o.  )88b
# o888o        d888b    `Y8bod8P'  888bod8P' `Y8bod8P' d888b      "888" o888o `Y8bod8P' 8""888P'
#                                  888
################################# o888o ##############################################################

"""

>>>DEPENDENCIES Precised below

>>>NOTE that in this module you'll find all properties registration of addon_prefs/window_manager/object/scene
   Some are stored in this module, some are not. See below, if `import from ..` 

>>>THERE ARE MORE PROPERTIES for dynamic enums:

   -bpy.types.WindowManager.scatter5_bitmap_library ->Dynamic Enum
   -bpy.types.WindowManager.scatter5_preset_gallery ->Dynamic Enum
   -bpy.types.Texture.scatter5 

>>>IMPORTANT ANNOYING ISSUE WITH PROPERTIES 

    Will never be able to use custom icons from properties like this, why?
    because when importing a module it will initialize everything in it (somehow)
    So i guess that i should figure out a better registering method, 
    and a way cleaner way of redistributing my modules

""" 

import bpy 

from . import main_settings
from . import addon_settings
from . import gui_settings
from . import manual_settings
from . import mask_settings
from . import particle_settings


# ooooooooo.
# `888   `Y88.
#  888   .d88' oooo d8b  .ooooo.  oo.ooooo.   .oooo.o
#  888ooo88P'  `888""8P d88' `88b  888' `88b d88(  "8
#  888          888     888   888  888   888 `"Y88b.
#  888          888     888   888  888   888 o.  )88b
# o888o        d888b    `Y8bod8P'  888bod8P' 8""888P'
#                                  888
#                                 o888o

######### PER ADDON

#bpy.context.preferences.addons["Scatter5"].preferences
from . addon_settings import SCATTER5_AddonPref

######### PER OBJECT

#bpy.context.object.scatter5
from . main_settings import SCATTER5_PROP_Object
#bpy.context.object.scatter5.particle_systems
from . particle_settings import SCATTER5_PROP_particle_systems
#bpy.context.object.scatter5.mask_systems
from . mask_settings import SCATTER5_PROP_procedural_vg

######### PER SCENE 

#bpy.context.scene.scatter5
from . main_settings import SCATTER5_PROP_Scene
#bpy.context.scene.scatter5.ui 
from . gui_settings import SCATTER5_PROP_ui
#bpy.context.scene.scatter5.ui.type_s_category
from . gui_settings import (
     _type_s_distribution,
     _type_s_scale,
     _type_s_rot,
     _type_s_pattern,
     _type_s_abiotic,
     _type_s_proximity,
     _type_s_ecosystem,
     _type_s_push,  
     _type_s_wind,
     _type_s_visibility,
     _type_s_instances,
     _type_s_display,
     ) 
#bpy.context.scene.scatter5.manual
from . manual_settings import SCATTER5_PROP_scene_manual
#bpy.context.scene.scatter5.manual.lambda_brushes
from . manual_settings import (
    SCATTER5_manual_default_brush,
    SCATTER5_manual_default_brush_2d,
    SCATTER5_manual_dot_brush,
    SCATTER5_manual_spatter_brush,
    SCATTER5_manual_pose_brush,
    SCATTER5_manual_path_brush,
    SCATTER5_manual_spray_brush,
    SCATTER5_manual_move_brush,
    SCATTER5_manual_eraser_brush,
    SCATTER5_manual_dilute_brush,
    # SCATTER5_manual_rotation_align_brush,
    # SCATTER5_manual_rotation_set_brush,
    # SCATTER5_manual_rotation_random_brush,
    SCATTER5_manual_rotation_brush,
    # SCATTER5_manual_scale_set_brush,
    # SCATTER5_manual_scale_random_brush,
    SCATTER5_manual_scale_brush,
    # SCATTER5_manual_scale_grow_brush,
    # SCATTER5_manual_scale_shrink_brush,
    SCATTER5_manual_scale_grow_shrink_brush,
    SCATTER5_manual_comb_brush,
    SCATTER5_manual_object_brush,
    SCATTER5_manual_random_rotation_brush,
    SCATTER5_manual_z_align_brush,
    SCATTER5_manual_gizmo_brush,
    # SCATTER5_manual_debug_brush_2d,
    )
#bpy.context.scene.scatter5.sync_channels
from .. scattering.synchronize import SCATTER5_PROP_sync_channels
#bpy.context.scene.scatter5.sync_channels[].members
from .. scattering.synchronize import SCATTER5_PROP_channel_members

######### PER WINDOW_MANAGER

#bpy.context.window_manager.scatter5
from . main_settings import SCATTER5_PROP_Window
#bpy.context.window_manager.scatter5.library
from .. ui.biome_library import SCATTER5_PROP_library
#bpy.context.window_manager.scatter5.folder_navigation
from .. ui.biome_library import SCATTER5_PROP_folder_navigation

######### PER NODEGROUP

#bpy.context.node_tree.scatter5
from . main_settings import SCATTER5_PROP_node_group
#bpy.context.node_tree.scatter5.texture
from ..scattering.texture_datablock import SCATTER5_PROP_node_texture


# ooooooooo.                        
# `888   `Y88.                      
#  888   .d88'  .ooooo.   .oooooooo 
#  888ooo88P'  d88' `88b 888' `88b  
#  888`88b.    888ooo888 888   888  
#  888  `88b.  888    .o `88bod8P'  
# o888o  o888o `Y8bod8P' `8oooooo.  
#                        d"     YD
#                        "Y88888P'


#Children types children aways first! 
classes = [
        
    SCATTER5_AddonPref,

    SCATTER5_PROP_folder_navigation, 
    SCATTER5_PROP_library, 
    SCATTER5_PROP_Window,

    SCATTER5_PROP_node_texture,
    SCATTER5_PROP_node_group,

    SCATTER5_manual_default_brush,
    SCATTER5_manual_default_brush_2d,
    SCATTER5_manual_dot_brush,
    SCATTER5_manual_spatter_brush,
    SCATTER5_manual_pose_brush,
    SCATTER5_manual_path_brush,
    SCATTER5_manual_spray_brush,
    SCATTER5_manual_move_brush,
    SCATTER5_manual_eraser_brush,
    SCATTER5_manual_dilute_brush,
    # SCATTER5_manual_rotation_align_brush,
    # SCATTER5_manual_rotation_set_brush,
    # SCATTER5_manual_rotation_random_brush,
    SCATTER5_manual_rotation_brush,
    # SCATTER5_manual_scale_set_brush,
    # SCATTER5_manual_scale_random_brush,
    SCATTER5_manual_scale_brush,
    # SCATTER5_manual_scale_grow_brush,
    # SCATTER5_manual_scale_shrink_brush,
    SCATTER5_manual_scale_grow_shrink_brush,
    SCATTER5_manual_comb_brush,
    SCATTER5_manual_object_brush,
    SCATTER5_manual_random_rotation_brush,
    SCATTER5_manual_z_align_brush,
    SCATTER5_manual_gizmo_brush,
    # SCATTER5_manual_debug_brush_2d,

    SCATTER5_PROP_scene_manual,

    SCATTER5_PROP_channel_members,
    SCATTER5_PROP_sync_channels,

    _type_s_distribution,
    _type_s_scale,
    _type_s_rot,
    _type_s_pattern,
    _type_s_abiotic,
    _type_s_proximity,
    _type_s_ecosystem,
    _type_s_push,
    _type_s_wind,
    _type_s_visibility,
    _type_s_instances,
    _type_s_display,

    SCATTER5_PROP_ui,

    SCATTER5_PROP_Scene,
    SCATTER5_PROP_procedural_vg,
    SCATTER5_PROP_particle_systems,
    
    SCATTER5_PROP_Object,

    ]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.scatter5         = bpy.props.PointerProperty(type=SCATTER5_PROP_Scene)
    bpy.types.Object.scatter5        = bpy.props.PointerProperty(type=SCATTER5_PROP_Object)
    bpy.types.WindowManager.scatter5 = bpy.props.PointerProperty(type=SCATTER5_PROP_Window)
    bpy.types.NodeTree.scatter5      = bpy.props.PointerProperty(type=SCATTER5_PROP_node_group)

    #update directories globals with new addon_prefs.library_path
    from .. resources.directories import update_lib
    update_lib()

    return 

def unregister():

    del bpy.types.Scene.scatter5
    del bpy.types.Object.scatter5
    del bpy.types.WindowManager.scatter5

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    return 

#if __name__ == "__main__":
#    register()