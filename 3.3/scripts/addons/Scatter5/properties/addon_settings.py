

#####################################################################################################
#
#       .o.             .o8        .o8                        ooooooooo.                       .o88o.
#      .888.           "888       "888                        `888   `Y88.                     888 `"
#     .8"888.      .oooo888   .oooo888   .ooooo.  ooo. .oo.    888   .d88' oooo d8b  .ooooo.  o888oo
#    .8' `888.    d88' `888  d88' `888  d88' `88b `888P"Y88b   888ooo88P'  `888""8P d88' `88b  888
#   .88ooo8888.   888   888  888   888  888   888  888   888   888          888     888ooo888  888
#  .8'     `888.  888   888  888   888  888   888  888   888   888          888     888    .o  888
# o88o     o8888o `Y8bod88P" `Y8bod88P" `Y8bod8P' o888o o888o o888o        d888b    `Y8bod8P' o888o
#
#####################################################################################################


import bpy 

from .. ui import ui_addon #need to draw addon prefs from here..

from .. resources.translate import translate
from .. resources import directories

from ..manual import config


class SCATTER5_AddonPref(bpy.types.AddonPreferences):
    """bpy.context.preferences.addons["Scatter5"].preferences"""
    
    bl_idname = "Scatter5"

    # 8b    d8    db    88""Yb 88  dP 888888 888888 
    # 88b  d88   dPYb   88__dP 88odP  88__     88   
    # 88YbdP88  dP__Yb  88"Yb  88"Yb  88""     88   
    # 88 YY 88 dP""""Yb 88  Yb 88  Yb 888888   88   

    fetch_automatic_allow : bpy.props.BoolProperty(
        default=True,
        )
    fetch_automatic_daycount : bpy.props.IntProperty(
        default=3,
        min=1, max=31,
        )

    #  dP""b8    db    888888 888888  dP""b8  dP"Yb  88""Yb Yb  dP
    # dP   `"   dPYb     88   88__   dP   `" dP   Yb 88__dP  YbdP
    # Yb       dP__Yb    88   88""   Yb  "88 Yb   dP 88"Yb    8P
    #  YboodP dP""""Yb   88   888888  YboodP  YbodP  88  Yb  dP

    manager_category : bpy.props.EnumProperty(
        default    = "prefs",
        items      = [ ("library" ,translate("Biomes Library") ,"" ),
                       ("market"  ,translate("Scatpack") ,"" ),
                       None,
                       ("stats",translate("Statistics") ,"" ),
                       ("prefs"   ,translate("Preferences") ,"" ),
                     ],
        ) 

    # 88     88 88""Yb 88""Yb    db    88""Yb Yb  dP
    # 88     88 88__dP 88__dP   dPYb   88__dP  YbdP
    # 88  .o 88 88""Yb 88"Yb   dP__Yb  88"Yb    8P
    # 88ood8 88 88oodP 88  Yb dP""""Yb 88  Yb  dP

    library_path : bpy.props.StringProperty(
        default= directories.lib_default,
        subtype="DIR_PATH",
        )

    # 888888 8b    d8 88 888888     8b    d8 888888 888888 88  88  dP"Yb  8888b.
    # 88__   88b  d88 88   88       88b  d88 88__     88   88  88 dP   Yb  8I  Yb
    # 88""   88YbdP88 88   88       88YbdP88 88""     88   888888 Yb   dP  8I  dY
    # 888888 88 YY 88 88   88       88 YY 88 888888   88   88  88  YbodP  8888Y"

    emitter_method  : bpy.props.EnumProperty(
        default    = "remove",
        items      = [ ("remove" ,translate("Remove & Choose New") ,"","EYEDROPPER",1 ),
                       ("set_active"  ,translate("Set Active Operator") ,"","RESTRICT_SELECT_OFF",2 ),
                       ("pin",translate("Always Active & Pin") ,"","PINNED",3 ),
                     ],
        ) 

    emitter_use_set_active : bpy.props.BoolProperty(
        default=False,
        description=translate("Show 'Set active as Emitter-Target' Operator."),
        )

    # 88 88b 88 888888 888888 88""Yb 888888    db     dP""b8 888888
    # 88 88Yb88   88   88__   88__dP 88__     dPYb   dP   `" 88__
    # 88 88 Y88   88   88""   88"Yb  88""    dP__Yb  Yb      88""
    # 88 88  Y8   88   888888 88  Yb 88     dP""""Yb  YboodP 888888

    ui_use_dark_box : bpy.props.BoolProperty(
        default=True,
        )
    ui_use_arrow : bpy.props.BoolProperty(
        default=True,
        )
    ui_use_active : bpy.props.BoolProperty(
        default=True,
        )

    ui_selection_y : bpy.props.FloatProperty(
        default=0.85,
        soft_min=0.7,
        max=1.25,
        )
    ui_scale_y      : bpy.props.FloatProperty(
        default=1.80,
        min=0.75,
        max=3,
        )

    ui_main_when_open : bpy.props.FloatProperty(
        default=1,
        max=10,
        )

    ui_bool_use_standard : bpy.props.BoolProperty(
        default=True,
        )
    ui_bool_use_panelclose : bpy.props.BoolProperty(
        default=False,
        )

    ui_word_wrap_max_char_factor : bpy.props.FloatProperty(
        default=1.0,
        min=0.1,
        max=3,
        )
    ui_word_wrap_y : bpy.props.FloatProperty(
        default=0.8,
        min=0.1,
        max=3,
        )

    # Yb        dP 88 88b 88     88""Yb  dP"Yb  88""Yb
    #  Yb  db  dP  88 88Yb88     88__dP dP   Yb 88__dP
    #   YbdPYbdP   88 88 Y88     88"""  Yb   dP 88"""
    #    YP  YP    88 88  Y8     88      YbodP  88

    win_pop_size : bpy.props.FloatVectorProperty(
        name=translate("Pop Window Scale"),
        default=(700,900),
        min=100,
        size=2,
        precision=0,
        )
    win_pop_location : bpy.props.FloatVectorProperty(
        name=translate("Pop Window Position"),
        default=(0,0),
        size=2,
        precision=0,
        )
    
    # manual mode brush shortcuts
    manual_key_config: bpy.props.PointerProperty(type=config.SCATTER5_manual_key_config, )
    
    # 8888b.  888888 88""Yb 88   88  dP""b8
    #  8I  Yb 88__   88__dP 88   88 dP   `"
    #  8I  dY 88""   88""Yb Y8   8P Yb  "88
    # 8888Y"  888888 88oodP `YbodP'  YboodP

    debug             : bpy.props.BoolProperty(default=False)
    debug_depsgraph   : bpy.props.BoolProperty(default=False)


    #drawing part in ui module
    def draw(self,context):
        layout = self.layout
        ui_addon.draw_addon(self,layout) #need to draw addon prefs from here..
