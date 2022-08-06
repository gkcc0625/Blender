

#####################################################################################################
#
#   .oooooo.                 o8o
#  d8P'  `Y8b                `"'
# 888           oooo  oooo  oooo       oo.ooooo.  oooo d8b  .ooooo.  oo.ooooo.   .oooo.o
# 888           `888  `888  `888        888' `88b `888""8P d88' `88b  888' `88b d88(  "8
# 888     ooooo  888   888   888        888   888  888     888   888  888   888 `"Y88b.
# `88.    .88'   888   888   888        888   888  888     888   888  888   888 o.  )88b
#  `Y8bood8P'    `V88V"V8P' o888o       888bod8P' d888b    `Y8bod8P'  888bod8P' 8""888P'
#                                       888                           888
#                                      o888o                         o888o
#####################################################################################################

#IMPORTANT about this module
#   most of the props are not directly used as a prop, but toggled though an operator
#   (typically "scatter5.property_toggle") so history is not filled with panel opening/closing 
#   there's a lot of addons committing this mistake. user is closing/opening panels then history is full of sh*t
#   maybe there's a simpler way to ignore prop change from a Prop Property directly?
#   i'm not aware of such possibility for the time being, som i'm using this trick for now 

import bpy 
from .. resources.translate import translate

# IMPORTANT 
# These below are used as arg in SCATTER5_PT_settings 
# we need them for being able to transfer an attr from gui to a menu with `menu.context_pointer_set` (unfortunately i don't recall there's other solutions than this..) 

class _type_s_distribution(bpy.types.PropertyGroup): 
    value : bpy.props.StringProperty(default="s_distribution")
    label = translate("Distribution")
class _type_s_scale(bpy.types.PropertyGroup): 
    value : bpy.props.StringProperty(default="s_scale")
    label = translate("Scale")
class _type_s_rot(bpy.types.PropertyGroup): 
    value : bpy.props.StringProperty(default="s_rot")
    label = translate("Rotation")

class _type_s_pattern(bpy.types.PropertyGroup): 
    value : bpy.props.StringProperty(default="s_pattern")
    label = translate("Pattern")

class _type_s_abiotic(bpy.types.PropertyGroup): 
    value : bpy.props.StringProperty(default="s_abiotic")
    label = translate("Abiotic")
class _type_s_proximity(bpy.types.PropertyGroup): 
    value : bpy.props.StringProperty(default="s_proximity")
    label = translate("Proximity")
class _type_s_ecosystem(bpy.types.PropertyGroup): 
    value : bpy.props.StringProperty(default="s_ecosystem")
    label = translate("Ecosystem")
class _type_s_push(bpy.types.PropertyGroup): 
    value : bpy.props.StringProperty(default="s_push")
    label = translate("Offset")
class _type_s_wind(bpy.types.PropertyGroup): 
    value : bpy.props.StringProperty(default="s_wind")
    label = translate("Wind Wave")

class _type_s_visibility(bpy.types.PropertyGroup): 
    value : bpy.props.StringProperty(default="s_visibility")
    label = translate("Visibility")
class _type_s_instances(bpy.types.PropertyGroup): 
    value : bpy.props.StringProperty(default="s_instances")
    label = translate("Instances")
class _type_s_display(bpy.types.PropertyGroup): 
    value : bpy.props.StringProperty(default="s_display")
    label = translate("Display")
    

class SCATTER5_PROP_ui(bpy.types.PropertyGroup): 
    """scat_ui = bpy.context.scene.scatter5.ui, props used for opening/closing gui"""
        
    type_s_distribution : bpy.props.PointerProperty(type = _type_s_distribution)
    type_s_scale : bpy.props.PointerProperty(type = _type_s_scale)
    type_s_rot : bpy.props.PointerProperty(type = _type_s_rot)

    type_s_pattern : bpy.props.PointerProperty(type = _type_s_pattern)

    type_s_abiotic : bpy.props.PointerProperty(type = _type_s_abiotic)
    type_s_proximity : bpy.props.PointerProperty(type = _type_s_proximity)
    type_s_ecosystem : bpy.props.PointerProperty(type = _type_s_ecosystem)
    type_s_push : bpy.props.PointerProperty(type = _type_s_push)
    type_s_wind : bpy.props.PointerProperty(type = _type_s_wind)

    type_s_visibility : bpy.props.PointerProperty(type = _type_s_visibility)
    type_s_instances : bpy.props.PointerProperty(type = _type_s_instances)
    type_s_display : bpy.props.PointerProperty(type = _type_s_display)

    general_info : bpy.props.BoolProperty(default=1)    

    #creation 

    scattering_main : bpy.props.BoolProperty(default=1)
    scattering_sub1 : bpy.props.BoolProperty(default=1) 

    biomes_main : bpy.props.BoolProperty(default=0)
    biomes_sub1 : bpy.props.BoolProperty(default=1) 

    options_main : bpy.props.BoolProperty(default=0)
    options_sub1 : bpy.props.BoolProperty(default=1)
    options_sub2 : bpy.props.BoolProperty(default=1)
    options_sub3 : bpy.props.BoolProperty(default=1)
    options_sub4 : bpy.props.BoolProperty(default=1)

    security_main : bpy.props.BoolProperty(default=0)
    security_sub1 : bpy.props.BoolProperty(default=1)

    terrain_main : bpy.props.BoolProperty(default=0)
    terrain_sub1 : bpy.props.BoolProperty(default=1)
    terrain_sub2 : bpy.props.BoolProperty(default=1)

    remesh_main : bpy.props.BoolProperty(default=0)
    remesh_sub1 : bpy.props.BoolProperty(default=1)

    sync_main : bpy.props.BoolProperty(default=0)
    sync_sub1 : bpy.props.BoolProperty(default=1)

    upd_main : bpy.props.BoolProperty(default=0)
    upd_sub1 : bpy.props.BoolProperty(default=1)
    
    statistics_main : bpy.props.BoolProperty(default=0)
    statistics_sub1 : bpy.props.BoolProperty(default=1)
    statistics_sub2 : bpy.props.BoolProperty(default=0)

    manual_main : bpy.props.BoolProperty(default=0)
    manual_sub1 : bpy.props.BoolProperty(default=1)
    manual_arr1 : bpy.props.BoolProperty(default=1)
    manual_arr2 : bpy.props.BoolProperty(default=1)

    masks_f_sub1 : bpy.props.BoolProperty(default=1) #graph_remap

    #tweaking 

    selection_main : bpy.props.BoolProperty(default=1)
    selection_sub1 : bpy.props.BoolProperty(default=1)

    distribution_main : bpy.props.BoolProperty(default=0)
    distribution_sub1 : bpy.props.BoolProperty(default=1)

    densmask_main : bpy.props.BoolProperty(default=0)
    densmask_sub1 : bpy.props.BoolProperty(default=1)

    rotation_main : bpy.props.BoolProperty(default=0)
    rotation_sub1 : bpy.props.BoolProperty(default=1)

    scale_main : bpy.props.BoolProperty(default=0)
    scale_sub1 : bpy.props.BoolProperty(default=1)

    push_main : bpy.props.BoolProperty(default=0)
    push_sub1 : bpy.props.BoolProperty(default=1)

    pattern_main : bpy.props.BoolProperty(default=0)
    pattern_sub1 : bpy.props.BoolProperty(default=1)

    geo_filter_main : bpy.props.BoolProperty(default=0)
    geo_filter_sub1 : bpy.props.BoolProperty(default=1)

    proxi_filter_main : bpy.props.BoolProperty(default=0)
    proxi_filter_sub1 : bpy.props.BoolProperty(default=1)

    ecosystem_main : bpy.props.BoolProperty(default=0)
    ecosystem_sub1 : bpy.props.BoolProperty(default=1)

    wind_main : bpy.props.BoolProperty(default=0)
    wind_sub1 : bpy.props.BoolProperty(default=1)

    instances_main : bpy.props.BoolProperty(default=0)
    instances_sub1 : bpy.props.BoolProperty(default=1)

    visibility_main : bpy.props.BoolProperty(default=0)
    visibility_sub1 : bpy.props.BoolProperty(default=1)

    display_main : bpy.props.BoolProperty(default=0)
    display_sub1 : bpy.props.BoolProperty(default=1)
    display_sub2 : bpy.props.BoolProperty(default=1)

    masks_main : bpy.props.BoolProperty(default=0)
    masks_sub1 : bpy.props.BoolProperty(default=1)

    export_main : bpy.props.BoolProperty(default=0)
    export_sub1 : bpy.props.BoolProperty(default=1)

    baking_sub1 : bpy.props.BoolProperty(default=1)
    baking_sub2 : bpy.props.BoolProperty(default=1)
    baking_sub3 : bpy.props.BoolProperty(default=1)

    #addon 

    add_pack : bpy.props.BoolProperty(default=1)  
    add_fetch: bpy.props.BoolProperty(default=1)  
    add_path : bpy.props.BoolProperty(default=1)  
    add_lang : bpy.props.BoolProperty(default=1)  
    add_work : bpy.props.BoolProperty(default=1)   
    add_shortcut : bpy.props.BoolProperty(default=1)   
    add_gui : bpy.props.BoolProperty(default=1)  
    add_dev : bpy.props.BoolProperty(default=1)  
    add_win : bpy.props.BoolProperty(default=1) 
    add_short: bpy.props.BoolProperty(default=1) 

    add_preset_save : bpy.props.BoolProperty(default=1)    
    add_preset_apply : bpy.props.BoolProperty(default=1)    

    add_biome_dialog_info : bpy.props.BoolProperty(default=1) 
    add_biome_thumb : bpy.props.BoolProperty(default=1) 

