

#####################################################################################################
#
# ooooo     ooo ooooo      ooo        ooooo                                             oooo
# `888'     `8' `888'      `88.       .888'                                             `888
#  888       8   888        888b     d'888   .oooo.   ooo. .oo.   oooo  oooo   .oooo.    888
#  888       8   888        8 Y88. .P  888  `P  )88b  `888P"Y88b  `888  `888  `P  )88b   888
#  888       8   888        8  `888'   888   .oP"888   888   888   888   888   .oP"888   888
#  `88.    .8'   888        8    Y     888  d8(  888   888   888   888   888  d8(  888   888
#    `YbodP'    o888o      o8o        o888o `Y888""8o o888o o888o  `V88V"V8P' `Y888""8o o888o
#
#####################################################################################################



import bpy

from .. resources.icons import cust_icon
from .. resources.translate import translate

from . import templates

from .. manual.manager import SC5Toolbox


#   .oooooo.    ooooo     ooo ooooo      ooooo   ooooo  o8o      o8o                     oooo         o8o
#  d8P'  `Y8b   `888'     `8' `888'      `888'   `888'  `"'      `"'                     `888         `"'
# 888            888       8   888        888     888  oooo     oooo  .oooo.    .ooooo.   888  oooo  oooo  ooo. .oo.    .oooooooo
# 888            888       8   888        888ooooo888  `888     `888 `P  )88b  d88' `"Y8  888 .8P'   `888  `888P"Y88b  888' `88b
# 888     ooooo  888       8   888        888     888   888      888  .oP"888  888        888888.     888   888   888  888   888
# `88.    .88'   `88.    .8'   888        888     888   888      888 d8(  888  888   .o8  888 `88b.   888   888   888  `88bod8P'
#  `Y8bood8P'      `YbodP'    o888o      o888o   o888o o888o     888 `Y888""8o `Y8bod8P' o888o o888o o888o o888o o888o `8oooooo.
#                                                                888                                                   d"     YD
#                                                            .o. 88P                                                   "Y88888P'
#                                                            `Y888P

# 88  88 88  88888    db     dP""b8 88  dP        db     dP""b8 888888 88 Yb    dP 888888     888888  dP"Yb   dP"Yb  88     .dP"Y8
# 88  88 88     88   dPYb   dP   `" 88odP        dPYb   dP   `"   88   88  Yb  dP  88__         88   dP   Yb dP   Yb 88     `Ybo."
# 888888 88 o.  88  dP__Yb  Yb      88"Yb       dP__Yb  Yb        88   88   YbdP   88""         88   Yb   dP Yb   dP 88  .o o.`Y8b
# 88  88 88 "bodP' dP""""Yb  YboodP 88  Yb     dP""""Yb  YboodP   88   88    YP    888888       88    YbodP   YbodP  88ood8 8bodP'



OldTools = {}

#Proceeding to hijack the '_tools' dict of 'VIEW3D_PT_tools_active' class. 
#when i use the term "Hijacking" in this addon, i mean TEMPORARILY changing native python code with our own
#Currently hijacking is used here on the toolsystem and header for creating a "fake" custom mode
#Hijack also used on addonprefs for creating our custom manager interface  

#All tools Generated below are fake, It's for display purpose only!
#we have our own toolset of modal operators, and we dynamically switch them by checking which fake tool are active TODO ???? How to send singal?

def hijack_tools_dict():

    import os, sys
    scr = bpy.utils.system_resource('SCRIPTS')
    pth = os.path.join(scr,'startup','bl_ui')
    if pth not in sys.path:
        sys.path.append(pth)

    from bl_ui.space_toolsystem_common import ToolDef
    from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active


    def generate_tool(cls,):
        """Tools Generation -> code sampled "scripts/modules/bpy/utils.__init__.register_tool()"""    

        return ToolDef.from_dict({
            "idname": cls.brush_type,
            "label": cls.bl_label.replace(translate("Brush"),""),
            "description": cls.bl_description,
            "icon": cls.dat_icon,
            "cursor": None,
            "widget": None,
            "keymap": None,
            "data_block": None,
            "operator": None,
            "draw_settings": None,
            "draw_cursor": None,
            })
        
    from .. manual import brushes

    global OldTools
    OldTools = VIEW3D_PT_tools_active._tools

    toolbar=  [ generate_tool(brushes.SCATTER5_OT_manual_dot_brush),
                generate_tool(brushes.SCATTER5_OT_manual_pose_brush),
                generate_tool(brushes.SCATTER5_OT_manual_path_brush),
                generate_tool(brushes.SCATTER5_OT_manual_spatter_brush),
                generate_tool(brushes.SCATTER5_OT_manual_spray_brush),
                None,#=Separator 
                generate_tool(brushes.SCATTER5_OT_manual_move_brush),
                None,#=Separator 
                generate_tool(brushes.SCATTER5_OT_manual_eraser_brush),
                generate_tool(brushes.SCATTER5_OT_manual_dilute_brush),
                None,#=Separator 
                generate_tool(brushes.SCATTER5_OT_manual_rotation_brush),
                generate_tool(brushes.SCATTER5_OT_manual_random_rotation_brush),
                None,#=Separator 
                generate_tool(brushes.SCATTER5_OT_manual_comb_brush),
                generate_tool(brushes.SCATTER5_OT_manual_z_align_brush),
                None,#=Separator 
                generate_tool(brushes.SCATTER5_OT_manual_scale_brush),
                generate_tool(brushes.SCATTER5_OT_manual_scale_grow_shrink_brush),
              ]
    
    # # DEBUG
    # from ..manual import debug
    # if(debug.debug_mode()):
    #     toolbar.append(None, )
    #     toolbar.append(
    #         generate_tool(brushes.SCATTER5_OT_manual_debug_brush_2d),
    #     )
    # # DEBUG
    
    # # DEBUG
    # from ..manual import debug
    # if(debug.debug_mode()):
    #     toolbar.append(None, )
    #     toolbar.append(
    #         generate_tool(brushes.SCATTER5_OT_manual_gizmo_brush),
    #     )
    # # DEBUG
    
    #Add instance index painting tool if instance method is by index
    emitter    = bpy.context.scene.scatter5.emitter
    psy_active = emitter.scatter5.get_psy_active()
    
    if(psy_active.s_instances_method=="ins_collection" and psy_active.s_instances_pick_method=="pick_idx"):
        toolbar+= [ None,#=Separator 
                    generate_tool(brushes.SCATTER5_OT_manual_object_brush),
                  ]

    VIEW3D_PT_tools_active._tools = {
        None: [ ],
        'OBJECT': toolbar
        }
    return 



def restore_tools_dict():

    from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active
    global OldTools
    VIEW3D_PT_tools_active._tools = OldTools
    return 



#  dP""b8 88  88    db    88b 88  dP""b8 888888     .dP"Y8 888888 888888 888888 88 88b 88  dP""b8 .dP"Y8
# dP   `" 88  88   dPYb   88Yb88 dP   `" 88__       `Ybo." 88__     88     88   88 88Yb88 dP   `" `Ybo."
# Yb      888888  dP__Yb  88 Y88 Yb  "88 88""       o.`Y8b 88""     88     88   88 88 Y88 Yb  "88 o.`Y8b
#  YboodP 88  88 dP""""Yb 88  Y8  YboodP 888888     8bodP' 888888   88     88   88 88  Y8  YboodP 8bodP'


HijackedSettings = {
    "show_region_header" : None,
    "show_region_tool_header" : None,
    "show_region_toolbar":None,
    "show_region_ui" : None,
    "show_text" : None,
    "show_stats" : None,
    "active_tool": None,
    "show_gizmo": None,
}


def change_settings(context):

    global HijackedSettings

    #Show Header
    HijackedSettings["show_region_header"] = context.space_data.show_region_header 
    context.space_data.show_region_header = True

    #Show Toolbar
    HijackedSettings["show_region_toolbar"] = context.space_data.show_region_toolbar 
    context.space_data.show_region_toolbar = True

    #Show Tool Header 
    HijackedSettings["show_region_tool_header"] = context.space_data.show_region_tool_header
    context.space_data.show_region_tool_header = False

    #Hide PropertiesPanel ?
    HijackedSettings["show_region_ui"] = context.space_data.show_region_ui
    context.space_data.show_region_ui = False #Hide? Do not Hide? it's useless to have it but it might be confusing to have it popping out every time...
    #bpy.context.scene.scatter5.ui_enabled = False
    
    #Hide Statistics (we'll prolly draw our own?)
    HijackedSettings["show_text"] = context.space_data.overlay.show_text
    context.space_data.overlay.show_text = False
    HijackedSettings["show_stats"] = context.space_data.overlay.show_stats
    context.space_data.overlay.show_stats = False

    #Hide Gizmos, not used in this mode anyway 
    HijackedSettings["show_gizmo"] = context.space_data.show_gizmo 
    context.space_data.show_gizmo = False

    #Save active tool
    HijackedSettings["active_tool"] = context.workspace.tools.from_space_view3d_mode(context.mode).idname

    return None

def restore_settings(context):

    global HijackedSettings
    
    #Restore Header
    context.space_data.show_region_header = HijackedSettings["show_region_header"]

    #Restore Tool Header 
    context.space_data.show_region_tool_header = HijackedSettings["show_region_tool_header"]

    #Restore Toolbar 
    context.space_data.show_region_toolbar = HijackedSettings["show_region_toolbar"]

    #Restore PropertiesPanel 
    context.space_data.show_region_ui = HijackedSettings["show_region_ui"] #Hide? Do not Hide? it's useless to have it but it might be confusing to have it popping out every time...
    #bpy.context.scene.scatter5.ui_enabled = True

    #Restore Statistics 
    context.space_data.overlay.show_text = HijackedSettings["show_text"]
    context.space_data.overlay.show_stats = HijackedSettings["show_stats"]

    #Restore Gizmos
    context.space_data.show_gizmo = HijackedSettings["show_gizmo"]

    #Restore old active tool 
    bpy.ops.wm.tool_set_by_id(name = HijackedSettings["active_tool"],)

    return None



#  dP""b8 888888 88b 88 888888 88""Yb    db    88         88  88 88  88888    db     dP""b8 88  dP
# dP   `" 88__   88Yb88 88__   88__dP   dPYb   88         88  88 88     88   dPYb   dP   `" 88odP
# Yb  "88 88""   88 Y88 88""   88"Yb   dP__Yb  88  .o     888888 88 o.  88  dP__Yb  Yb      88"Yb
#  YboodP 888888 88  Y8 888888 88  Yb dP""""Yb 88ood8     88  88 88 "bodP' dP""""Yb  YboodP 88  Yb



HijackingStatus = False 
View3DHeader_OriginalDraw = None


def modal_hijacking(context):
    """register impostors"""
    #print("HIJACKING")

    global HijackingStatus
    if HijackingStatus==True:
        return None

    #change a bunch of settings 
    change_settings(context)

    #override header drawing function by one of my own temporarily 
    global View3DHeader_OriginalDraw
    View3DHeader_OriginalDraw = bpy.types.VIEW3D_HT_header.draw
    bpy.types.VIEW3D_HT_header.draw = view3d_overridedraw

    #override _tools dict from class VIEW3D_PT_tools_active with my own temporarily
    hijack_tools_dict()

    HijackingStatus=True
    return None
    

def modal_hijack_restore(context):
    """restore and find original drawing classes"""
    #print("RESTORING")
    
    global HijackingStatus
    if HijackingStatus==False:
        return None

    #restore override
    global View3DHeader_OriginalDraw
    bpy.types.VIEW3D_HT_header.draw = View3DHeader_OriginalDraw
    View3DHeader_OriginalDraw = None 

    #restore override
    restore_tools_dict()

    #restore the settings we changed precedently
    restore_settings(context)

    HijackingStatus=False
    return None



# oooooooooo.                                oooo             ooooo   ooooo                           .o8
# `888'   `Y8b                               `888             `888'   `888'                          "888
#  888     888 oooo d8b oooo  oooo   .oooo.o  888 .oo.         888     888   .ooooo.   .oooo.    .oooo888   .ooooo.  oooo d8b
#  888oooo888' `888""8P `888  `888  d88(  "8  888P"Y88b        888ooooo888  d88' `88b `P  )88b  d88' `888  d88' `88b `888""8P
#  888    `88b  888      888   888  `"Y88b.   888   888        888     888  888ooo888  .oP"888  888   888  888ooo888  888
#  888    .88P  888      888   888  o.  )88b  888   888        888     888  888    .o d8(  888  888   888  888    .o  888
# o888bood8P'  d888b     `V88V"V8P' 8""888P' o888o o888o      o888o   o888o `Y8bod8P' `Y888""8o `Y8bod88P" `Y8bod8P' d888b



def view3d_overridedraw(self, context):
    l = self.layout
    try: 
        headoverr_main(l,context)
    except Exception as e:
        l.alert = True
        l.label(text=str(e))
        l.separator_spacer()
        headoverr_exitbutton(l)
    return 

def headoverr_exitbutton(l):
    exit = l.row()
    exit.alert = True
    exit.operator('scatter5.manual_exit', icon='PANEL_CLOSE', )

def procedural_override_msg(layout=None,scale=False, rotation=False,):

    emitter      = bpy.context.scene.scatter5.emitter
    active_psy   = emitter.scatter5.get_psy_active()
    did_override = False 

    if scale:
        if (active_psy.s_scale_default_allow or active_psy.s_scale_random_allow or active_psy.s_scale_min_allow or active_psy.s_scale_mirror_allow or active_psy.s_scale_shrink_allow or active_psy.s_scale_grow_allow):
            did_override = True 
    if rotation:
        if (active_psy.s_rot_align_z_allow or active_psy.s_rot_align_y_allow or active_psy.s_rot_random_allow or active_psy.s_rot_add_allow):
            did_override = True 

    if did_override and (layout is not None):
        lbl = layout.column()
        lbl.scale_y = 0.8
        lbl.alert = True
        lbl.separator()
        lbl.label(text=translate("Procedural Settings Active"),icon="OBJECT_ORIGIN" if scale else "CON_ROTLIKE")
    return 

def headoverr_main(l,context):    

    emitter    = context.scene.scatter5.emitter
    psy_active = emitter.scatter5.get_psy_active()

    # FIXME: SC5Toolbox.get() not working after reload is of course caused by import system as i suspected. somewhere is either wrong order or classes here are not reloaded. because import on top, if not everything reloaded in proper order (manager classes must be reloaded first, always) imported reference this time is still pointing to old SC5Toolbox before reloading. manual package by itself reloads properly (i encountered this issue in past). so long story short, importing it again here is quick fix for it.. but better to solve it once and for all.
    # TODO: alright, first is ui_manual reloaded, then manager, so ui_manual keeps reference to SC5Toolbox before reload, i.e. old one with tool as None, and is never set to anything again.. so we got two options, one reloading system or use this quick fix everywhere outside manual package..
    from ..manual.manager import SC5Toolbox
    active_brush = SC5Toolbox.get()

    if active_brush is None:
        l.alert = True
        l.label(text="ERROR: Active Brush is None! how did you do that?")
        l.separator_spacer()
        headoverr_exitbutton(l)
        return  

    brush_label = active_brush.bl_label
    brush_icon  = active_brush.icon
    brush_type  = active_brush.brush_type

    ico = l.row()
    if brush_icon.startswith("W_"):
          ico.label(text=brush_label+"   ", icon_value=cust_icon(brush_icon) )
    else: ico.label(text=brush_label+"   ", icon=brush_icon )
    
    # # brush space, uncomment to make it accessible while drawing..
    # l.prop( psy_active, "s_distribution_space", expand=True, )

    #Brush
    if brush_type in ["comb_brush", "random_rotation_brush", "z_align_brush", ]:
        l.popover("SCATTER5_PT_brush_settings_menu", text=translate("Brush")) #Note that We could write the settings directly within the header like blender is also doing
    
    # from ..manual import debug
    # if(debug.debug_mode()):
    #     if(brush_type in ('debug_brush_2d', )):
    #         l.popover("SCATTER5_PT_brush_settings_menu", text=translate("Brush"))
    
    #Instance 
    if brush_type in ["object_brush","dot_brush","spatter_brush","path_brush","spray_brush","pose_brush"]:
        if(psy_active.s_instances_method=="ins_collection" and psy_active.s_instances_pick_method=="pick_idx"):
            l.popover("SCATTER5_PT_brush_instance_menu", text=translate("Instances"))

    #Rotation
    if brush_type in ["dot_brush","path_brush","spatter_brush","spray_brush","rotation_brush","move_brush","pose_brush"]:
        l.popover("SCATTER5_PT_brush_rotation_menu", text=translate("Rotation"))

    #Scale 
    if brush_type in ["dot_brush","path_brush","spatter_brush","spray_brush","scale_brush","scale_grow_shrink_brush","pose_brush"]:
        l.popover("SCATTER5_PT_brush_scale_menu", text=translate("Scale"))

    #Stroke
    if brush_type not in ("dot_brush", "pose_brush", ):
        l.popover("SCATTER5_PT_brush_stroke_menu", text=translate("Stroke"))
    
    #Points
    l.menu("SCATTER5_MT_brush_point_menu", text=translate("Points"))
    # systems menu
    l.menu("SCATTER5_MT_systems_menu", text=translate("Systems"))

    l.separator_spacer()

    #Below == Rendering Tab on the right
    #Code below = exact sample from native code

    tool_settings = context.tool_settings
    view = context.space_data
    shading = view.shading
    show_region_tool_header = view.show_region_tool_header
    overlay = view.overlay
    obj = context.active_object
    
    object_mode = 'OBJECT' if obj is None else obj.mode
    has_pose_mode = (
        (object_mode == 'POSE') or
        (object_mode == 'WEIGHT_PAINT' and context.pose_object is not None)
    )
    
    # # Viewport Settings
    # l.popover(
    #     panel="VIEW3D_PT_object_type_visibility",
    #     icon_value=view.icon_from_show_object_viewport,
    #     text="",
    # )

    # # Gizmo toggle & popover.
    # row = l.row(align=True)
    # # FIXME: place-holder icon.
    # row.prop(view, "show_gizmo", text="", toggle=True, icon='GIZMO')
    # sub = row.row(align=True)
    # sub.active = view.show_gizmo
    # sub.popover(
    #     panel="VIEW3D_PT_gizmo_display",
    #     text="",
    # )

    # Overlay toggle & popover.
    row = l.row(align=True)
    row.prop(overlay, "show_overlays", icon='OVERLAY', text="")
    sub = row.row(align=True)
    sub.active = overlay.show_overlays
    sub.popover(panel="VIEW3D_PT_overlay", text="")

    row = l.row()
    row.active = (object_mode == 'EDIT') or (shading.type in {'WIREFRAME', 'SOLID'})

    # While exposing 'shading.show_xray(_wireframe)' is correct.
    # this hides the key shortcut from users: T70433.
    if has_pose_mode:
        draw_depressed = overlay.show_xray_bone
    elif shading.type == 'WIREFRAME':
        draw_depressed = shading.show_xray_wireframe
    else:
        draw_depressed = shading.show_xray
    row.operator(
        "view3d.toggle_xray",
        text="",
        icon='XRAY',
        depress=draw_depressed,
    )

    row = l.row(align=True)
    row.prop(shading, "type", text="", expand=True)
    sub = row.row(align=True)
    # TODO, currently render shading type ignores mesh two-side, until it's supported
    # show the shading popover which shows double-sided option.

    # sub.enabled = shading.type != 'RENDERED'
    sub.popover(panel="VIEW3D_PT_shading", text="")

    #Exit Button

    headoverr_exitbutton(l)
    
    return None


# oooooooooo.                                oooo              .oooooo..o               .       .    o8o
# `888'   `Y8b                               `888             d8P'    `Y8             .o8     .o8    `"'
#  888     888 oooo d8b oooo  oooo   .oooo.o  888 .oo.        Y88bo.       .ooooo.  .o888oo .o888oo oooo  ooo. .oo.    .oooooooo  .oooo.o
#  888oooo888' `888""8P `888  `888  d88(  "8  888P"Y88b        `"Y8888o.  d88' `88b   888     888   `888  `888P"Y88b  888' `88b  d88(  "8
#  888    `88b  888      888   888  `"Y88b.   888   888            `"Y88b 888ooo888   888     888    888   888   888  888   888  `"Y88b.
#  888    .88P  888      888   888  o.  )88b  888   888       oo     .d8P 888    .o   888 .   888 .  888   888   888  `88bod8P'  o.  )88b
# o888bood8P'  d888b     `V88V"V8P' 8""888P' o888o o888o      8""88888P'  `Y8bod8P'   "888"   "888" o888o o888o o888o `8oooooo.  8""888P'
#                                                                                                                     d"     YD
#                                                                                                                     "Y88888P'


#TOJAKUB: i just move all code from `SCATTER5_PT_dev_manual_effect` and `SCATTER5_PT_dev_manual_brush`
# in all 4 Header being Brush/Rotation/Scale/Stroke
# Note that There's some settings will change, we need to discuss about all this


class SCATTER5_PT_brush_settings_menu(bpy.types.Panel):
 
    bl_idname      = "SCATTER5_PT_brush_settings_menu"
    bl_label       = ""
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER"


    def draw(self, context):
        l = self.layout
        
        # TODO: reloading issue, ui is reloaded after manager, so it keeps reference to old manager classes
        from ..manual.manager import SC5Toolbox
        active_brush = SC5Toolbox.get()
        brush_type = active_brush.brush_type
        bs = context.scene.scatter5.manual
        
        #So far they could just be written in the header, menu not needed IMO but some tool might need specific settings so we'll decide that for later 
        
        if(brush_type == "comb_brush"):

            bsb = bs.comb_brush
            
            l.prop(bsb, 'mode')
            l.prop(bsb, 'axis')
            
            if(bsb.mode == 'SPIN'):
                # l.prop(bsb, 'speed')
                # l.prop(bsb, 'speed_pressure')
                
                r = l.row(align=True, )
                r.prop(bsb, 'speed')
                r.prop(bsb, 'speed_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
                
                l.prop(bsb, 'speed_random')
                # r = l.row()
                # r.prop(bsb, 'speed_random_range')
            else:
                # l.prop(bsb, 'strength')
                # l.prop(bsb, 'strength_pressure')
                
                r = l.row(align=True, )
                r.prop(bsb, 'strength')
                r.prop(bsb, 'strength_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
                
                l.prop(bsb, 'direction_smoothing_steps')
                
                l.prop(bsb, 'strength_random')
                # r = l.row()
                # r.prop(bsb, 'strength_random_range')

            procedural_override_msg(layout=l,rotation=True,)
            
            return 

        elif(brush_type == "random_rotation_brush"):

            bsb = bs.random_rotation_brush
            l.prop(bsb, 'angle')
            
            r = l.row(align=True)
            r.prop(bsb, 'speed')
            r.prop(bsb, 'speed_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )

            procedural_override_msg(layout=l,rotation=True,)
            
            return 
        
        elif(brush_type == "z_align_brush"):

            bsb = bs.z_align_brush
            
            r = l.row(align=True)
            r.prop(bsb, 'strength')
            r.prop(bsb, 'strength_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )

            procedural_override_msg(layout=l,rotation=True,)

            return
        
        # elif(brush_type == 'debug_brush_2d'):
        #     bsb = bs.debug_brush_2d
        #     l.prop(bsb, 'cursor')
        #     l.prop(bsb, 'radius')
        #     l.prop(bsb, 'radius_increment')
        #     l.prop(bsb, 'strength')
        #     l.prop(bsb, 'count')
        #     l.prop(bsb, 'length')

        return 
            


# oooooooooo.                                oooo             ooooooooo.                 .                 .    o8o                          
# `888'   `Y8b                               `888             `888   `Y88.             .o8               .o8    `"'                          
#  888     888 oooo d8b oooo  oooo   .oooo.o  888 .oo.         888   .d88'  .ooooo.  .o888oo  .oooo.   .o888oo oooo   .ooooo.  ooo. .oo.     
#  888oooo888' `888""8P `888  `888  d88(  "8  888P"Y88b        888ooo88P'  d88' `88b   888   `P  )88b    888   `888  d88' `88b `888P"Y88b    
#  888    `88b  888      888   888  `"Y88b.   888   888        888`88b.    888   888   888    .oP"888    888    888  888   888  888   888    
#  888    .88P  888      888   888  o.  )88b  888   888        888  `88b.  888   888   888 . d8(  888    888 .  888  888   888  888   888    
# o888bood8P'  d888b     `V88V"V8P' 8""888P' o888o o888o      o888o  o888o `Y8bod8P'   "888" `Y888""8o   "888" o888o `Y8bod8P' o888o o888o   


class SCATTER5_PT_brush_rotation_menu(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_brush_rotation_menu"
    bl_label       = ""
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER"

    def draw(self, context):
        l = self.layout
        
        # TODO: reloading issue, ui is reloaded after manager, so it keeps reference to old manager classes
        from ..manual.manager import SC5Toolbox
        active_brush = SC5Toolbox.get()
        brush_type = active_brush.brush_type
        
        man = context.scene.scatter5.manual
        bps = getattr(man, brush_type)
        
        if(brush_type in ('dot_brush', 'path_brush', 'spray_brush', 'spatter_brush', )):
            c = l.column()
            c.prop(bps, 'rotation_align')
            
            r = c.row()
            r.prop(bps, 'rotation_up')
            # if(brush_type == "path_brush"):
            if(brush_type in ("path_brush", "spray_brush", )):
                if(bps.align):
                    r.enabled = False
            # if(brush_type=="path_brush"):
            if(brush_type in ("path_brush", "spray_brush", "spatter_brush", )):
                l.prop(bps, 'align')
            if(brush_type in ("path_brush", )):
                r = l.row()
                r.prop(bps, 'chain')
                if(not bps.align):
                    r.enabled = False
            
            c = l.column()
            c.scale_y = 0.9
            c.prop(bps, 'rotation_base')
            c.prop(bps, 'rotation_random')

        elif(brush_type == "rotation_brush"):
            
            l.prop(bps, 'use_rotation_align')
            c = l.column()
            c.prop(bps, 'rotation_align')
            c.prop(bps, 'rotation_up')
            if(not bps.use_rotation_align):
                c.enabled = False
            
            l.prop(bps, 'use_rotation_base')
            c = l.column()
            c.scale_y = 0.9
            c.prop(bps, 'rotation_base')
            if(not bps.use_rotation_base):
                c.enabled = False
            
            l.prop(bps, 'use_rotation_random')
            c = l.column()
            c.scale_y = 0.9
            c.prop(bps, 'rotation_random')
            if(not bps.use_rotation_random):
                c.enabled = False

        elif(brush_type == 'move_brush'):
            l.prop(bps, 'use_align_surface')
        
        elif(brush_type == 'pose_brush'):
            l.prop(bps, 'rotation_align')
        
        # elif(brush_type == "rotation_align_brush"):
        #     c = l.column()
        #     c.prop(bps, 'rotation_align')
        #     c.prop(bps, 'rotation_up')
        # elif(brush_type == "rotation_set_brush"):
        #     # c = l.column()
        #     # c.prop(bps, 'rotation_align')
        #     # c.prop(bps, 'rotation_up')
        #     c = l.column()
        #     c.scale_y = 0.9
        #     c.prop(bps, 'rotation_base')
        #     # c.prop(bps, 'rotation_random')
        # elif(brush_type == "rotation_random_brush"):
        #     # c = l.column()
        #     # c.prop(bps, 'rotation_align')
        #     # c.prop(bps, 'rotation_up')
        #     c = l.column()
        #     c.scale_y = 0.9
        #     # c.prop(bps, 'rotation_base')
        #     c.prop(bps, 'rotation_random')

        procedural_override_msg(layout=l,rotation=True,)

        return 


# oooooooooo.                                oooo              .oooooo..o                     oooo            
# `888'   `Y8b                               `888             d8P'    `Y8                     `888            
#  888     888 oooo d8b oooo  oooo   .oooo.o  888 .oo.        Y88bo.       .ooooo.   .oooo.    888   .ooooo.  
#  888oooo888' `888""8P `888  `888  d88(  "8  888P"Y88b        `"Y8888o.  d88' `"Y8 `P  )88b   888  d88' `88b 
#  888    `88b  888      888   888  `"Y88b.   888   888            `"Y88b 888        .oP"888   888  888ooo888 
#  888    .88P  888      888   888  o.  )88b  888   888       oo     .d8P 888   .o8 d8(  888   888  888    .o 
# o888bood8P'  d888b     `V88V"V8P' 8""888P' o888o o888o      8""88888P'  `Y8bod8P' `Y888""8o o888o `Y8bod8P' 
        


class SCATTER5_PT_brush_scale_menu(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_brush_scale_menu"
    bl_label       = ""
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER"

    def draw(self, context):
        l = self.layout
        
        # TODO: reloading issue, ui is reloaded after manager, so it keeps reference to old manager classes
        from ..manual.manager import SC5Toolbox
        active_brush = SC5Toolbox.get()
        brush_type = active_brush.brush_type
        
        man = context.scene.scatter5.manual
        bps = getattr(man, brush_type)
        
        if(brush_type in ["dot_brush","path_brush","spray_brush","spatter_brush"]):
            c = l.column()
            c.scale_y = 0.9
            c.prop(bps, 'scale_default')
            if brush_type in ["path_brush","spray_brush","spatter_brush"]:
                c.prop(bps, 'scale_default_use_pressure')
            c.prop(bps, 'scale_random_factor')
            c = l.column(align=True)
            c.label(text=translate("Randomization Type:"))
            r = c.row()
            r.prop(bps, 'scale_random_type', expand=True, )
        # elif(brush_type == "scale_set_brush"):
        #     c = l.column()
        #     c.scale_y = 0.9
        #     c.prop(bps, 'scale_default')
        # elif(brush_type == "scale_random_brush"):
        #     c = l.column()
        #     c.scale_y = 0.9
        #     c.prop(bps, 'scale_random_factor')
        #     c = l.column(align=True)
        #     c.label(text=translate("Randomization Type:"))
        #     r = c.row()
        #     r.prop(bps, 'scale_random_type', expand=True, )
        elif(brush_type == "scale_brush"):
            
            l.prop(bps, 'use_scale_default')
            c = l.column()
            c.scale_y = 0.9
            c.prop(bps, 'scale_default')
            if(not bps.use_scale_default):
                c.enabled = False
            
            l.prop(bps, 'use_scale_random_factor')
            c = l.column()
            c.scale_y = 0.9
            c.prop(bps, 'scale_random_factor')
            if(not bps.use_scale_random_factor):
                c.enabled = False
            c = l.column(align=True)
            c.label(text=translate("Randomization Type:"))
            r = c.row()
            r.prop(bps, 'scale_random_type', expand=True, )
            if(not bps.use_scale_random_factor):
                c.enabled = False
        
        # elif(brush_type == "scale_grow_brush"):
        #     c = l.column()
        #     c.scale_y = 0.9
        #     c.prop(bps, 'change')
        #     c.prop(bps, 'use_limits')
        #     l.prop(bps, 'change_pressure')
        #     r = c.row()
        #     r.prop(bps, 'limits')
        #     if(not bps.use_limits):
        #         r.enabled = False
        # elif(brush_type == "scale_shrink_brush"):
        #     c = l.column()
        #     c.scale_y = 0.9
        #     c.prop(bps, 'change')
        #     c.prop(bps, 'use_limits')
        #     l.prop(bps, 'change_pressure')
        #     r = c.row()
        #     r.prop(bps, 'limits')
        #     if(not bps.use_limits):
        #         r.enabled = False
        elif(brush_type == "scale_grow_shrink_brush"): 
            c = l.column()
            c.scale_y = 0.9

            r = c.row()
            r.prop(bps, 'change_mode', expand=True)

            c.prop(bps, 'change')
            c.prop(bps, 'use_change_random')
            
            c.prop(bps, 'use_limits')
            l.prop(bps, 'change_pressure')
            r = c.row()
            r.prop(bps, 'limits')
            if(not bps.use_limits):
                r.enabled = False
        elif(brush_type == "pose_brush"): 
            c = l.column()
            c.scale_y = 0.9
            c.prop(bps, 'scale_default')
            l.prop(bps, 'scale_multiplier')
        
        procedural_override_msg(layout=l,scale=True,)

        return 

# oooooooooo.                                oooo             ooooo                          .
# `888'   `Y8b                               `888             `888'                        .o8
#  888     888 oooo d8b oooo  oooo   .oooo.o  888 .oo.         888  ooo. .oo.    .oooo.o .o888oo  .oooo.   ooo. .oo.    .ooooo.   .ooooo.
#  888oooo888' `888""8P `888  `888  d88(  "8  888P"Y88b        888  `888P"Y88b  d88(  "8   888   `P  )88b  `888P"Y88b  d88' `"Y8 d88' `88b
#  888    `88b  888      888   888  `"Y88b.   888   888        888   888   888  `"Y88b.    888    .oP"888   888   888  888       888ooo888
#  888    .88P  888      888   888  o.  )88b  888   888        888   888   888  o.  )88b   888 . d8(  888   888   888  888   .o8 888    .o
# o888bood8P'  d888b     `V88V"V8P' 8""888P' o888o o888o      o888o o888o o888o 8""888P'   "888" `Y888""8o o888o o888o `Y8bod8P' `Y8bod8P'




class SCATTER5_PT_brush_instance_menu(bpy.types.Panel):
 
    bl_idname      = "SCATTER5_PT_brush_instance_menu"
    bl_label       = ""
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER"


    def draw(self, context):
        l = self.layout
        
        # TODO: reloading issue, ui is reloaded after manager, so it keeps reference to old manager classes
        from ..manual.manager import SC5Toolbox
        active_brush = SC5Toolbox.get()
        brush_type = active_brush.brush_type
        bs = context.scene.scatter5.manual
        
        #So far they could just be written in the header, menu not needed IMO but some tool might need specific settings so we'll decide that for later 
        i = None 

        if (brush_type == "object_brush"):

            bsb = bs.object_brush
            l.prop(bsb, 'index')
            i = bsb.index 

        elif (brush_type =='dot_brush'):

            bsb = bs.dot_brush
            l.prop(bsb, 'instance_index')
            i = bsb.instance_index
        
        elif (brush_type =='pose_brush'):
            
            bsb = bs.pose_brush
            l.prop(bsb, 'instance_index')
            i = bsb.instance_index
            
        elif (brush_type =='path_brush'):

            bsb = bs.path_brush
            l.prop(bsb, 'instance_index')
            i = bsb.instance_index

        elif (brush_type =='spray_brush'):

            bsb = bs.spray_brush
            l.prop(bsb, 'instance_index')
            i = bsb.instance_index
        
        elif (brush_type =='spatter_brush'):

            bsb = bs.spatter_brush
            l.prop(bsb, 'instance_index')
            i = bsb.instance_index

        emitter    = bpy.context.scene.scatter5.emitter
        psy_active = emitter.scatter5.get_psy_active()
        

        coll = psy_active.s_instances_coll_ptr
        lbl = l.row()
        if coll is None:
            lbl.active = False
            lbl.label(text=translate("Pointer not assigned"))
            return None 

        obj = None 
        for idx,o in enumerate(sorted(coll.objects, key= lambda o:o.name)):
            if idx==i:
                obj = o

        if obj is None: 
              lbl.active = False
              lbl.label(text=translate("Pointer not assigned"))
        else: lbl.label(text=obj.name, icon="OBJECT_DATA")

        return None 


# oooooooooo.                                oooo              .oooooo..o     .                      oooo
# `888'   `Y8b                               `888             d8P'    `Y8   .o8                      `888
#  888     888 oooo d8b oooo  oooo   .oooo.o  888 .oo.        Y88bo.      .o888oo oooo d8b  .ooooo.   888  oooo   .ooooo.
#  888oooo888' `888""8P `888  `888  d88(  "8  888P"Y88b        `"Y8888o.    888   `888""8P d88' `88b  888 .8P'   d88' `88b
#  888    `88b  888      888   888  `"Y88b.   888   888            `"Y88b   888    888     888   888  888888.    888ooo888
#  888    .88P  888      888   888  o.  )88b  888   888       oo     .d8P   888 .  888     888   888  888 `88b.  888    .o
# o888bood8P'  d888b     `V88V"V8P' 8""888P' o888o o888o      8""88888P'    "888" d888b    `Y8bod8P' o888o o888o `Y8bod8P'



class SCATTER5_PT_brush_stroke_menu(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_brush_stroke_menu"
    bl_label       = ""
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER"

    no_props_message = translate("No Effect Properties..")

    def _dot_brush(self, context, l, ): #We don't care menu won't be even drawn for this brush_type
        bs = context.scene.scatter5.manual
        bsb = bs.dot_brush
        l.label(text=self.no_props_message)
    
    def _path_brush(self, context, l, ):
        bs = context.scene.scatter5.manual
        bsb = bs.path_brush
        
        r = l.row(align=True)
        r.prop(bsb, 'path_distance')
        r.prop(bsb, 'path_distance_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        # l.prop(bsb, 'path_distance_random')
        
        r = l.row(align=True)
        r.prop(bsb, 'divergence_distance')
        r.prop(bsb, 'divergence_distance_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
    
    def _spray_brush(self, context, l, ):
        bs = context.scene.scatter5.manual
        bsb = bs.spray_brush
        
        l.prop(bsb, 'interval')
        
        # l.prop(bsb, 'radius')
        r = l.row(align=True)
        r.prop(bsb, 'radius')
        r.prop(bsb, 'radius_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        
        # l.prop(bsb, 'num_dots')
        r = l.row(align=True)
        r.prop(bsb, 'num_dots')
        r.prop(bsb, 'num_dots_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        
        l.prop(bsb, 'jet')
        l.prop(bsb, 'reach')
        
        l.prop(bsb, 'use_minimal_distance')
        
        r = l.row()
        r.prop(bsb, 'minimal_distance')
        r.prop(bsb, 'minimal_distance_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        if(not bsb.use_minimal_distance):
            r.enabled = False
    
    def _spatter_brush(self, context, l, ):
        bs = context.scene.scatter5.manual
        bsb = bs.spatter_brush
        
        r = l.row(align=True)
        r.prop(bsb, 'random_location')
        r.prop(bsb, 'random_location_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        
        r = l.row()
        r.prop(bsb, 'interval')
        if(bsb.draw_on == 'MOUSEMOVE'):
            r.enabled = False
        r = l.row(align=True)
        r.prop(bsb, 'draw_on', expand=True, )
    
    def _move_brush(self, context, l, ):
        bs = context.scene.scatter5.manual
        bsb = bs.move_brush
        
        # l.prop(bsb, 'radius')
        r = l.row(align=True)
        r.prop(bsb, 'radius')
        #r.prop(bsb, 'radius_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, ) #pressure useless for move brush
        
        # l.prop(bsb, 'falloff_distance')
        
        r = l.row(align=True)
        c = r.column(align=True)
        c.prop(bsb, 'affect_portion')
        r.prop(bsb, 'affect_portion_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        if(bsb.affect_portion_pressure):
            c.active = False
        
        # l.prop(bsb, 'use_align_surface')
    
    def _eraser_brush(self, context, l, ):
        bs = context.scene.scatter5.manual
        bsb = bs.eraser_brush
        
        l.prop(bsb, 'interval')
        
        # l.prop(bsb, 'radius')
        r = l.row(align=True)
        r.prop(bsb, 'radius')
        r.prop(bsb, 'radius_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        
        # l.prop(bsb, 'falloff_distance')
        
        r = l.row(align=True)
        c = r.column(align=True)
        c.prop(bsb, 'affect_portion')
        r.prop(bsb, 'affect_portion_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        if(bsb.affect_portion_pressure):
            c.active = False
        
        r = l.row(align=True)
        r.prop(bsb, 'draw_on', expand=True, )
    
    def _dilute_brush(self, context, l, ):
        bs = context.scene.scatter5.manual
        bsb = bs.dilute_brush
        
        l.prop(bsb, 'interval')
        
        # l.prop(bsb, 'radius')
        r = l.row(align=True)
        r.prop(bsb, 'radius')
        r.prop(bsb, 'radius_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        
        # l.prop(bsb, 'falloff_distance')
        
        r = l.row(align=True)
        c = r.column(align=True)
        c.prop(bsb, 'affect_portion')
        r.prop(bsb, 'affect_portion_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        if(bsb.affect_portion_pressure):
            c.active = False
        
        l.prop(bsb, 'minimal_distance')
        r = l.row(align=True)
        r.prop(bsb, 'draw_on', expand=True, )
    
    '''
    def _rotation_align_brush(self, context, l, ):
        bs = context.scene.scatter5.manual
        bsb = bs.rotation_align_brush
        
        l.prop(bsb, 'interval')
        
        # l.prop(bsb, 'radius')
        r = l.row(align=True)
        r.prop(bsb, 'radius')
        r.prop(bsb, 'radius_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        
        # l.prop(bsb, 'falloff_distance')
        
        r = l.row(align=True)
        c = r.column(align=True)
        c.prop(bsb, 'affect_portion')
        r.prop(bsb, 'affect_portion_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        if(bsb.affect_portion_pressure):
            c.active = False
        
        r = l.row(align=True)
        r.prop(bsb, 'draw_on', expand=True, )
    
    def _rotation_set_brush(self, context, l, ):
        bs = context.scene.scatter5.manual
        bsb = bs.rotation_set_brush
        
        l.prop(bsb, 'interval')
        
        # l.prop(bsb, 'radius')
        r = l.row(align=True)
        r.prop(bsb, 'radius')
        r.prop(bsb, 'radius_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        
        # l.prop(bsb, 'falloff_distance')
        
        r = l.row(align=True)
        c = r.column(align=True)
        c.prop(bsb, 'affect_portion')
        r.prop(bsb, 'affect_portion_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        if(bsb.affect_portion_pressure):
            c.active = False
        
        r = l.row(align=True)
        r.prop(bsb, 'draw_on', expand=True, )
    
    def _rotation_random_brush(self, context, l, ):
        bs = context.scene.scatter5.manual
        bsb = bs.rotation_random_brush
        
        l.prop(bsb, 'interval')
        
        # l.prop(bsb, 'radius')
        r = l.row(align=True)
        r.prop(bsb, 'radius')
        r.prop(bsb, 'radius_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        
        # l.prop(bsb, 'falloff_distance')
        
        r = l.row(align=True)
        c = r.column(align=True)
        c.prop(bsb, 'affect_portion')
        r.prop(bsb, 'affect_portion_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        if(bsb.affect_portion_pressure):
            c.active = False
        
        r = l.row(align=True)
        r.prop(bsb, 'draw_on', expand=True, )
    '''
    
    def _rotation_brush(self, context, l, ):
        bs = context.scene.scatter5.manual
        bsb = bs.rotation_brush
        
        l.prop(bsb, 'interval')
        
        # l.prop(bsb, 'radius')
        r = l.row(align=True)
        r.prop(bsb, 'radius')
        r.prop(bsb, 'radius_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        
        # l.prop(bsb, 'falloff_distance')
        
        r = l.row(align=True)
        c = r.column(align=True)
        c.prop(bsb, 'affect_portion')
        r.prop(bsb, 'affect_portion_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        if(bsb.affect_portion_pressure):
            c.active = False
        
        r = l.row(align=True)
        r.prop(bsb, 'draw_on', expand=True, )
    
    '''
    def _scale_set_brush(self, context, l, ):
        bs = context.scene.scatter5.manual
        bsb = bs.scale_set_brush
        
        l.prop(bsb, 'interval')
        
        # l.prop(bsb, 'radius')
        r = l.row(align=True)
        r.prop(bsb, 'radius')
        r.prop(bsb, 'radius_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        
        # l.prop(bsb, 'falloff_distance')
        
        r = l.row(align=True)
        c = r.column(align=True)
        c.prop(bsb, 'affect_portion')
        r.prop(bsb, 'affect_portion_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        if(bsb.affect_portion_pressure):
            c.active = False
        
        r = l.row(align=True)
        r.prop(bsb, 'draw_on', expand=True, )
    
    def _scale_random_brush(self, context, l, ):
        bs = context.scene.scatter5.manual
        bsb = bs.scale_random_brush
        
        l.prop(bsb, 'interval')
        
        # l.prop(bsb, 'radius')
        r = l.row(align=True)
        r.prop(bsb, 'radius')
        r.prop(bsb, 'radius_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        
        # l.prop(bsb, 'falloff_distance')
        
        r = l.row(align=True)
        c = r.column(align=True)
        c.prop(bsb, 'affect_portion')
        r.prop(bsb, 'affect_portion_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        if(bsb.affect_portion_pressure):
            c.active = False
        
        r = l.row(align=True)
        r.prop(bsb, 'draw_on', expand=True, )
    '''
    
    def _scale_brush(self, context, l, ):
        bs = context.scene.scatter5.manual
        bsb = bs.scale_brush
        
        l.prop(bsb, 'interval')
        
        # l.prop(bsb, 'radius')
        r = l.row(align=True)
        r.prop(bsb, 'radius')
        r.prop(bsb, 'radius_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        
        # l.prop(bsb, 'falloff_distance')
        
        r = l.row(align=True)
        c = r.column(align=True)
        c.prop(bsb, 'affect_portion')
        r.prop(bsb, 'affect_portion_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        if(bsb.affect_portion_pressure):
            c.active = False
        
        r = l.row(align=True)
        r.prop(bsb, 'draw_on', expand=True, )
    
    '''
    def _scale_grow_brush(self, context, l, ):
        bs = context.scene.scatter5.manual
        bsb = bs.scale_grow_brush
        
        l.prop(bsb, 'interval')
        
        # l.prop(bsb, 'radius')
        r = l.row(align=True)
        r.prop(bsb, 'radius')
        r.prop(bsb, 'radius_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        
        # l.prop(bsb, 'falloff_distance')
        
        r = l.row(align=True)
        c = r.column(align=True)
        c.prop(bsb, 'affect_portion')
        r.prop(bsb, 'affect_portion_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        if(bsb.affect_portion_pressure):
            c.active = False
        
        r = l.row(align=True)
        r.prop(bsb, 'draw_on', expand=True, )
    
    def _scale_shrink_brush(self, context, l, ):
        bs = context.scene.scatter5.manual
        bsb = bs.scale_shrink_brush
        
        l.prop(bsb, 'interval')
        
        # l.prop(bsb, 'radius')
        r = l.row(align=True)
        r.prop(bsb, 'radius')
        r.prop(bsb, 'radius_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        
        # l.prop(bsb, 'falloff_distance')
        
        r = l.row(align=True)
        c = r.column(align=True)
        c.prop(bsb, 'affect_portion')
        r.prop(bsb, 'affect_portion_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        if(bsb.affect_portion_pressure):
            c.active = False
        
        r = l.row(align=True)
        r.prop(bsb, 'draw_on', expand=True, )
    '''
    
    def _scale_grow_shrink_brush(self, context, l, ):
        bs = context.scene.scatter5.manual
        bsb = bs.scale_grow_shrink_brush
        
        l.prop(bsb, 'interval')
        
        # l.prop(bsb, 'radius')
        r = l.row(align=True)
        r.prop(bsb, 'radius')
        r.prop(bsb, 'radius_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        
        # l.prop(bsb, 'falloff_distance')
        
        r = l.row(align=True)
        c = r.column(align=True)
        c.prop(bsb, 'affect_portion')
        r.prop(bsb, 'affect_portion_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        if(bsb.affect_portion_pressure):
            c.active = False
        
        r = l.row(align=True)
        r.prop(bsb, 'draw_on', expand=True, )
    
    def _comb_brush(self, context, l, ):
        bs = context.scene.scatter5.manual
        bsb = bs.comb_brush
        
        # l.prop(bsb, 'interval')
        
        # l.prop(bsb, 'radius')
        r = l.row(align=True)
        r.prop(bsb, 'radius')
        r.prop(bsb, 'radius_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        
        # l.prop(bsb, 'falloff_distance')
        
        r = l.row(align=True)
        c = r.column(align=True)
        c.prop(bsb, 'affect_portion')
        r.prop(bsb, 'affect_portion_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        if(bsb.affect_portion_pressure):
            c.active = False
        
        # r = l.row(align=True)
        # r.prop(bsb, 'draw_on', expand=True, )
    
    def _object_brush(self, context, l, ):
        bs = context.scene.scatter5.manual
        bsb = bs.object_brush
        
        l.prop(bsb, 'interval')
        
        # l.prop(bsb, 'radius')
        r = l.row(align=True)
        r.prop(bsb, 'radius')
        r.prop(bsb, 'radius_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        
        # l.prop(bsb, 'falloff_distance')
        
        r = l.row(align=True)
        c = r.column(align=True)
        c.prop(bsb, 'affect_portion')
        r.prop(bsb, 'affect_portion_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        if(bsb.affect_portion_pressure):
            c.active = False
        
        r = l.row(align=True)
        r.prop(bsb, 'draw_on', expand=True, )
    
    def _random_rotation_brush(self, context, l, ):
        bs = context.scene.scatter5.manual
        bsb = bs.random_rotation_brush
        
        l.prop(bsb, 'interval')
        
        # l.prop(bsb, 'radius')
        r = l.row(align=True)
        r.prop(bsb, 'radius')
        r.prop(bsb, 'radius_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        
        # l.prop(bsb, 'falloff_distance')
        
        r = l.row(align=True)
        c = r.column(align=True)
        c.prop(bsb, 'affect_portion')
        r.prop(bsb, 'affect_portion_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        if(bsb.affect_portion_pressure):
            c.active = False
        
        r = l.row(align=True)
        r.prop(bsb, 'draw_on', expand=True, )
    
    def _z_align_brush(self, context, l, ):
        bs = context.scene.scatter5.manual
        bsb = bs.z_align_brush
        
        # l.prop(bsb, 'interval')
        
        # l.prop(bsb, 'radius')
        r = l.row(align=True)
        r.prop(bsb, 'radius')
        r.prop(bsb, 'radius_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        
        # l.prop(bsb, 'falloff_distance')
        
        r = l.row(align=True)
        c = r.column(align=True)
        c.prop(bsb, 'affect_portion')
        r.prop(bsb, 'affect_portion_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        if(bsb.affect_portion_pressure):
            c.active = False
        
        l.prop(bsb, 'falloff')
        
        # r = l.row(align=True)
        # r.prop(bsb, 'draw_on', expand=True, )
    
    '''
    def _debug_brush_2d(self, context, l, ):
        bs = context.scene.scatter5.manual
        bsb = bs.debug_brush_2d
        
        l.prop(bsb, 'interval')
        
        # l.prop(bsb, 'radius')
        r = l.row(align=True)
        r.prop(bsb, 'radius')
        r.prop(bsb, 'radius_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        
        # l.prop(bsb, 'falloff_distance')
        
        r = l.row(align=True)
        c = r.column(align=True)
        c.prop(bsb, 'affect_portion')
        r.prop(bsb, 'affect_portion_pressure', text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
        if(bsb.affect_portion_pressure):
            c.active = False
        
        r = l.row(align=True)
        r.prop(bsb, 'draw_on', expand=True, )
    '''
    
    def draw(self, context):
        layout = self.layout

        col = layout.column()
        # TODO: reloading issue, ui is reloaded after manager, so it keeps reference to old manager classes
        from ..manual.manager import SC5Toolbox
        active_brush = SC5Toolbox.get()
        brush_type = None
        if(active_brush is not None):
            try:
                brush_type = active_brush.brush_type
            except ReferenceError:
                # NOTE: no reliable way to find what modal operator is running i guess and if any exception is raised, this will get invalidated and might even crash
                # NOTE: found this using ctypes: https://blenderartists.org/t/detect-if-modal-operator-is-running/1204971
                # NOTE: and this: https://devtalk.blender.org/t/is-there-any-way-to-detect-an-active-modal-operation/7184/5
                # NOTE: too messy for my taste. lets leave it to try except handling. i don't need any props, it's existence and class name is enough
                # NOTE: it is doing only once per redraw, it should be ok..
                pass
        
        if(brush_type == "dot_brush"):
            self._dot_brush(context, col, )
        elif(brush_type == "path_brush"):
            self._path_brush(context, col, )
        elif(brush_type == "spray_brush"):
            self._spray_brush(context, col, )
        elif(brush_type == "spatter_brush"):
            self._spatter_brush(context, col, )
        elif(brush_type == "move_brush"):
            self._move_brush(context, col, )
        elif(brush_type == "eraser_brush"):
            self._eraser_brush(context, col, )
        elif(brush_type == "dilute_brush"):
            self._dilute_brush(context, col, )
        # elif(brush_type == "rotation_align_brush"):
        #     self._rotation_align_brush(context, col, )
        # elif(brush_type == "rotation_set_brush"):
        #     self._rotation_set_brush(context, col, )
        # elif(brush_type == "rotation_random_brush"):
        #     self._rotation_random_brush(context, col, )
        elif(brush_type == "rotation_brush"):
            self._rotation_brush(context, col, )
        elif(brush_type == "random_rotation_brush"):
            self._random_rotation_brush(context, col, )
        # elif(brush_type == "scale_set_brush"):
        #     self._scale_set_brush(context, col, )
        # elif(brush_type == "scale_random_brush"):
        #     self._scale_random_brush(context, col, )
        elif(brush_type == "scale_brush"):
            self._scale_brush(context, col, )
        # elif(brush_type == "scale_grow_brush"):
        #     self._scale_grow_brush(context, col, )
        # elif(brush_type == "scale_shrink_brush"):
        #     self._scale_shrink_brush(context, col, )
        elif(brush_type == "scale_grow_shrink_brush"):
            self._scale_grow_shrink_brush(context, col, )
        elif(brush_type == "comb_brush"):
            self._comb_brush(context, col, )
        elif(brush_type == "object_brush"):
            self._object_brush(context, col, )
        # elif(brush_type == "debug_brush_2d"):
        #     self._debug_brush_2d(context, col, )
        elif(brush_type == "z_align_brush"):
            self._z_align_brush(context, col, )
        else:
            col.label(text="Unrecognized brush?")


# ooooooooo.              o8o                  .        ooo        ooooo
# `888   `Y88.            `"'                .o8        `88.       .888'
#  888   .d88'  .ooooo.  oooo  ooo. .oo.   .o888oo       888b     d'888   .ooooo.  ooo. .oo.   oooo  oooo
#  888ooo88P'  d88' `88b `888  `888P"Y88b    888         8 Y88. .P  888  d88' `88b `888P"Y88b  `888  `888
#  888         888   888  888   888   888    888         8  `888'   888  888ooo888  888   888   888   888
#  888         888   888  888   888   888    888 .       8    Y     888  888    .o  888   888   888   888
# o888o        `Y8bod8P' o888o o888o o888o   "888"      o8o        o888o `Y8bod8P' o888o o888o  `V88V"V8P'



class SCATTER5_MT_brush_point_menu(bpy.types.Menu):

    bl_idname = "SCATTER5_MT_brush_point_menu"
    bl_label  = ""
    bl_description = translate("Operations on Points")

    def draw(self, context):
        layout=self.layout

        layout.operator("scatter5.manual_apply_brush")
        layout.operator("scatter5.manual_disable_procedural")
        layout.operator("scatter5.manual_drop",)
        layout.operator("scatter5.manual_clear",).confirmed = True 

        return None 


#  .oooooo..o                          .                                    ooo        ooooo
# d8P'    `Y8                        .o8                                    `88.       .888'
# Y88bo.      oooo    ooo  .oooo.o .o888oo  .ooooo.  ooo. .oo.  .oo.         888b     d'888   .ooooo.  ooo. .oo.   oooo  oooo
#  `"Y8888o.   `88.  .8'  d88(  "8   888   d88' `88b `888P"Y88bP"Y88b        8 Y88. .P  888  d88' `88b `888P"Y88b  `888  `888
#      `"Y88b   `88..8'   `"Y88b.    888   888ooo888  888   888   888        8  `888'   888  888ooo888  888   888   888   888
# oo     .d8P    `888'    o.  )88b   888 . 888    .o  888   888   888        8    Y     888  888    .o  888   888   888   888
# 8""88888P'      .8'     8""888P'   "888" `Y8bod8P' o888o o888o o888o      o8o        o888o `Y8bod8P' o888o o888o  `V88V"V8P'
#             .o..P'
#             `Y8P'


class SCATTER5_MT_systems_menu(bpy.types.Menu):

    bl_label = translate("Systems List")
    bl_idname = "SCATTER5_MT_systems_menu"
    bl_description = translate("Change Active Manual System")
    
    def draw(self, context, ):
        layout = self.layout

        #wait, what if system is hidden? no way to hide/unhide? Hmmm

        emitter = bpy.context.scene.scatter5.emitter
        for p in emitter.scatter5.particle_systems:
            if (p.s_distribution_method == 'manual_all'): #what if user want to convert procedural to manual from here? maybe 
                row = layout.row()
                row.operator('scatter5.manual_switch', text=p.name, icon="DOT" if p.active else "BLANK1" ).name = p.name

        return None



# # -- SWITCHER v2 --

#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = [
    SCATTER5_PT_brush_settings_menu, 
    SCATTER5_PT_brush_instance_menu, 
    SCATTER5_PT_brush_scale_menu,
    SCATTER5_PT_brush_rotation_menu,
    SCATTER5_PT_brush_stroke_menu, 
    SCATTER5_MT_brush_point_menu,
    SCATTER5_MT_systems_menu,
]

