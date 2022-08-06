
#####################################################################################################
#
# ooooo     ooo ooooo      ooooooooooooo                                      oooo         o8o
# `888'     `8' `888'      8'   888   `8                                      `888         `"'
#  888       8   888            888      oooo oooo    ooo  .ooooo.   .oooo.    888  oooo  oooo  ooo. .oo.    .oooooooo
#  888       8   888            888       `88. `88.  .8'  d88' `88b `P  )88b   888 .8P'   `888  `888P"Y88b  888' `88b
#  888       8   888            888        `88..]88..8'   888ooo888  .oP"888   888888.     888   888   888  888   888
#  `88.    .8'   888            888         `888'`888'    888    .o d8(  888   888 `88b.   888   888   888  `88bod8P'
#    `YbodP'    o888o          o888o         `8'  `8'     `Y8bod8P' `Y888""8o o888o o888o o888o o888o o888o `8oooooo.
#                                                                                                           d"     YD
#####################################################################################################       "Y88888P'


import bpy

from .. resources.icons import cust_icon
from .. resources.translate import translate

from . import templates

#from .. external import is_addon_enabled

from .. utils.extra_utils import is_rendered_view


from .. utils.str_utils import word_wrap
from .. utils.vg_utils import is_vg_active

from .. scattering.synchronize import sync_info
from .. scattering.emitter import is_ready_for_scattering

from .. manual import brushes

from .. scattering.texture_datablock import draw_texture_datablock


#####################################################################################################


def get_props():
    """get useful props used in interface"""

    addon_prefs = bpy.context.preferences.addons["Scatter5"].preferences
    scat_scene  = bpy.context.scene.scatter5
    scat_ui     = bpy.context.scene.scatter5.ui
    scat_win    = bpy.context.window_manager.scatter5
    emitter     = scat_scene.emitter

    return (addon_prefs, scat_scene, scat_ui, scat_win, emitter)


def warnings(layout, active=True, selection=False, created=True, no_manual_support=False):

    emitter = bpy.context.scene.scatter5.emitter
    if emitter is not None:
        psys       = emitter.scatter5.particle_systems
        psy_active = emitter.scatter5.get_psy_active()
        psys_sel   = emitter.scatter5.get_psys_selected()

    if not emitter:
        txt = layout.row()
        txt.alert = True
        txt.alignment = "CENTER"
        txt.label(text=translate("Please choose an emitter."), icon_value=cust_icon("W_EMITTER_RED"))
        templates.sub_spacing(layout)
        return True

    elif created and len(psys)==0:
        txt = layout.row()
        txt.active=False
        txt.alignment = "CENTER"
        txt.label(text=translate("No System(s) Created."), icon="BLANK1")
        templates.sub_spacing(layout)
        return True

    elif active and (psy_active is None):
        txt = layout.row()
        txt.active=False
        txt.alignment = "CENTER"
        txt.label(text=translate("No Active System."), icon="BLANK1")
        templates.sub_spacing(layout)
        return True

    elif selection and len(psys_sel)==0:
        txt = layout.row()
        txt.active=False
        txt.alignment = "CENTER"
        txt.label(text=translate("No Selected System(s)."), icon="RESTRICT_SELECT_ON")
        templates.sub_spacing(layout)
        return True

    elif no_manual_support and (psy_active.s_distribution_method=="manual_all"):
        txt = layout.row()
        txt.active=False
        txt.alignment = "CENTER"
        txt.label(text=translate("Manual Distribution Not Supported."), icon="BRUSHES_ALL")
        templates.sub_spacing(layout)
        return True

    return False


def lock_check(layout, psy, category):
    if psy.is_locked(category):
        txt = layout.row()
        txt.active=False
        txt.alignment = "CENTER"
        txt.label(text=translate("Settings are Locked."), icon="LOCKED")
        templates.sub_spacing(layout)
        return True 
    return False


def draw_manual_brush_buttons(layout=None, cls=None):
    brush_icon = cls.icon

    #evaluate if tool is active
    from ..manual.manager import SC5Toolbox
    active_brush = SC5Toolbox.get()
    if active_brush is None:
          depressing = False
    else: depressing = ( cls.brush_type==active_brush.brush_type)
    
    #draw tool operator
    if brush_icon.startswith("W_"):
          layout.operator(cls.bl_idname, text=cls.bl_label, depress=depressing, icon_value=cust_icon(brush_icon))
    else: layout.operator(cls.bl_idname, text=cls.bl_label, depress=depressing, icon=brush_icon)

    return None 


# ooooo     ooo              o8o                                                    oooo       ooo        ooooo                    oooo
# `888'     `8'              `"'                                                    `888       `88.       .888'                    `888
#  888       8  ooo. .oo.   oooo  oooo    ooo  .ooooo.  oooo d8b  .oooo.o  .oooo.    888        888b     d'888   .oooo.    .oooo.o  888  oooo   .oooo.o
#  888       8  `888P"Y88b  `888   `88.  .8'  d88' `88b `888""8P d88(  "8 `P  )88b   888        8 Y88. .P  888  `P  )88b  d88(  "8  888 .8P'   d88(  "8
#  888       8   888   888   888    `88..8'   888ooo888  888     `"Y88b.   .oP"888   888        8  `888'   888   .oP"888  `"Y88b.   888888.    `"Y88b.
#  `88.    .8'   888   888   888     `888'    888    .o  888     o.  )88b d8(  888   888        8    Y     888  d8(  888  o.  )88b  888 `88b.  o.  )88b
#    `YbodP'    o888o o888o o888o     `8'     `Y8bod8P' d888b    8""888P' `Y888""8o o888o      o8o        o888o `Y888""8o 8""888P' o888o o888o 8""888P'





def draw_universal_masks(layout=None, psy_api=None, emitter=None, mask_api="",):
    """every universal masks api should have _mask_ptr _mask_reverse"""

    _mask_ptr_str = f"{mask_api}_mask_ptr"
    _mask_ptr_val = getattr(psy_api, f"{mask_api}_mask_ptr")
    _mask_method_val = getattr(psy_api,f"{mask_api}_mask_method")
    _mask_color_sample_method_val = getattr(psy_api,f"{mask_api}_mask_color_sample_method")

    col = layout.column(align=True)

    col.separator(factor=0.5)

    title = col.row(align=True)
    title.scale_y = 0.9
    title.label(text=translate("Feature Mask")+":",)
    
    method = col.row(align=True)
    method.prop(psy_api,f"{mask_api}_mask_method", text="",)# icon_only=True, emboss=True,)

    if (_mask_method_val=="none"):
        return None 

    #### #### #### vg method

    if _mask_method_val == "mask_vg":
            
        #Mask 

        mask = col.row(align=True)
        mask.prop_search( psy_api, _mask_ptr_str, emitter, "vertex_groups",text="")
            
        buttons = mask.row(align=True)
        buttons.scale_x = 0.93

        if (_mask_ptr_val!=""):
            buttons.prop( psy_api, f"{mask_api}_mask_reverse",text="",icon="ARROW_LEFTRIGHT")
            #buttons.operator( "scatter5.dummy", text="",icon="FCURVE") #TODO FOR LATER ?

        op = buttons.operator("scatter5.vg_quick_paint",text="",icon="BRUSH_DATA" if (_mask_ptr_val!="") else "ADD", depress=is_vg_active(emitter,_mask_ptr_val),)
        op.group_name = _mask_ptr_val
        op.mode       = "vg" 
        op.api        = f"emitter.scatter5.particle_systems['{psy_api.name}'].{_mask_ptr_str}"

    #### #### #### vcol method

    elif _mask_method_val == "mask_vcol":

        set_color = (0,0,0)

        if (_mask_ptr_val!=""):

            #pick method 

            meth = col.row(align=True)

            #custom color 

            if (_mask_color_sample_method_val=="id_picker"):
                color = meth.row(align=True)
                color.scale_x = 0.35
                color.prop(psy_api, f"{mask_api}_mask_id_color_ptr",text="")
                set_color = getattr(psy_api,f"{mask_api}_mask_id_color_ptr")
            else: 
                equivalence = {"id_greyscale":(1,1,1),"id_red":(1,0,0),"id_green":(0,1,0),"id_blue":(0,0,1),"id_black":(0,0,0),"id_white":(1,1,1),"id_saturation":(1,1,1),"id_value":(1,1,1)}
                set_color = equivalence[_mask_color_sample_method_val]

            #sample method

            meth.prop( psy_api, f"{mask_api}_mask_color_sample_method", text="")

        #Mask

        mask = col.row(align=True)
        mask.prop_search( psy_api, _mask_ptr_str, emitter.data, "vertex_colors",text="")

        buttons = mask.row(align=True)
        buttons.scale_x = 0.93

        if (_mask_ptr_val!=""):

            buttons.prop( psy_api, f"{mask_api}_mask_reverse",text="",icon="ARROW_LEFTRIGHT")
            #buttons.operator( "scatter5.dummy", text="",icon="FCURVE") #TODO FOR LATER ?

        op = buttons.operator("scatter5.vg_quick_paint",text="",icon="BRUSH_DATA" if _mask_ptr_val else "ADD", depress=is_vg_active(emitter, _mask_ptr_val))
        op.group_name =_mask_ptr_val
        op.set_color = set_color
        op.mode = "vcol"
        op.api = f"emitter.scatter5.particle_systems['{psy_api.name}'].{_mask_ptr_str}"


    #### #### #### bitmap method

    # elif _mask_method_val == "mask_img":

    #     if (_mask_ptr_val!=""):

    #         #pick method 

    #         meth = col.row(align=True)

    #         #custom color 

    #         if (_mask_color_sample_method_val=="id_picker"):
    #             color = row.row(align=True)
    #             color.scale_x = 0.35
    #             color.prop(psy_api, f"{mask_api}_mask_id_color_ptr",text="")

    #         #sample method

    #         meth.prop( psy_api, f"{mask_api}_mask_color_sample_method", text="")

    #     #Mask

    #     mask = col.row(align=True)
    #     mask.prop_search( psy_api, _mask_ptr_str, bpy.data, "images",text="")

    #     buttons = mask.row(align=True)
    #     buttons.scale_x = 0.93

    #     if (_mask_ptr_val==""):

    #         op = buttons.operator("scatter5.image_utils",text="", icon="ADD",)
    #         op.option = "new"
    #         op.img_name = psy_api.s_mask_bitmap_ptr
    #         op.api = f"emitter.scatter5.particle_systems['{psy_api.name}'].s_mask_bitmap_ptr"

    #     else:

    #         buttons.prop( psy_api, f"{mask_api}_mask_reverse",text="",icon="ARROW_LEFTRIGHT")
    #         buttons.operator( "scatter5.dummy", text="",icon="FCURVE")

    #         op = buttons.operator("scatter5.image_utils",text="", icon="BRUSH_DATA", depress=(bpy.context.mode=="PAINT_TEXTURE") and (bpy.context.scene.tool_settings.image_paint.mode=='IMAGE') and (bpy.context.scene.tool_settings.image_paint.canvas==bpy.data.images.get(psy_api.s_mask_bitmap_ptr)))
    #         op.option = "paint"
    #         op.paint_color = (1,1,1) #if (psy_api.s_mask_bitmap_color_sample_method=="bitmap_id_none") else psy_api.s_mask_bitmap_id_color_ptr[:3] if (psy_api.s_mask_bitmap_color_sample_method=="bitmap_id_color") else (1,0,0) if (psy_api.s_mask_bitmap_id_channel=="Red") else (0,1,0) if (psy_api.s_mask_bitmap_id_channel=="Green") else (0,0,1) if (psy_api.s_mask_bitmap_id_channel=="Blue") else (0,0,0)
    #         op.uv_ptr = "None" #psy_api.s_mask_bitmap_uv_ptr
    #         op.img_name= _mask_ptr_val
    #         op.api =f"emitter.scatter5.particle_systems['{psy_api.name}'].{_mask_ptr_str}"

    #         #Uv Ptr

    #         uvpt = col.row(align=True)
    #         uvpt.scale_y = 0.95
    #         uvpt.prop_search( psy_api, f"{mask_api}_mask_uv_ptr", emitter.data, "uv_layers",text="")

    ### ### ### noise method

    elif _mask_method_val == "mask_noise":

            noise_sett = col.column(align=True)
            noise_sett.scale_y = 0.9
            noise_sett.prop(psy_api, f"{mask_api}_mask_noise_scale",)
            noise_sett.prop(psy_api, f"{mask_api}_mask_noise_brightness",)
            noise_sett.prop(psy_api, f"{mask_api}_mask_noise_contrast",)


    #TODO, if multi-surface. will need to leave a warning message if all surfaces object do not have the uv/vg/vcol given

    return col 



# oooooo   oooooo     oooo oooo                  oooo                 ooooooooo.                                   oooo
#  `888.    `888.     .8'  `888                  `888                 `888   `Y88.                                 `888
#   `888.   .8888.   .8'    888 .oo.    .ooooo.   888   .ooooo.        888   .d88'  .oooo.   ooo. .oo.    .ooooo.   888
#    `888  .8'`888. .8'     888P"Y88b  d88' `88b  888  d88' `88b       888ooo88P'  `P  )88b  `888P"Y88b  d88' `88b  888
#     `888.8'  `888.8'      888   888  888   888  888  888ooo888       888          .oP"888   888   888  888ooo888  888
#      `888'    `888'       888   888  888   888  888  888    .o       888         d8(  888   888   888  888    .o  888
#       `8'      `8'       o888o o888o `Y8bod8P' o888o `Y8bod8P'      o888o        `Y888""8o o888o o888o `Y8bod8P' o888o



def draw_tweaking_panel(self,layout):
    """draw main tweaking panel"""

    addon_prefs, scat_scene, scat_ui, scat_win, emitter = get_props()

    main = layout.column()
    main.enabled = scat_scene.ui_enabled

    #selection 
    infomulti = " "+translate("If multiple systems are selected you can hold [ALT] to change multiple settings at once")

    is_open = templates.main_panel(self,main,
        prop_str = "selection_main",
        icon = "PARTICLES",
        name = translate("Systems List"),
        )
    if is_open:
            draw_particle_selection(self,main)
            templates.main_spacing(main)
    
    is_open = templates.main_panel(self,main,
        prop_str = "distribution_main",
        icon = "STICKY_UVS_DISABLE",
        name = translate("Distribution"),
        )
    if is_open:
            draw_particle_distribution(self,main)
            templates.main_spacing(main)

    is_open = templates.main_panel(self,main,
        prop_str = "densmask_main",
        icon = "MOD_MASK",
        name = translate("Remove Density"),
        )
    if is_open:
            draw_particle_masks(self,main)
            templates.main_spacing(main)

    is_open = templates.main_panel(self,main,
        prop_str = "rotation_main",
        icon = "CON_ROTLIKE",
        name = translate("Rotation"),
        )
    if is_open:
            draw_particle_rot(self, main)
            templates.main_spacing(main)

    is_open = templates.main_panel(self,main,
        prop_str = "scale_main",
        icon = "OBJECT_ORIGIN",
        name = translate("Scale"),
        )
    if is_open:
            draw_particle_scale(self, main)
            templates.main_spacing(main)

    is_open = templates.main_panel(self,main,
        prop_str = "pattern_main",
        icon = "TEXTURE",
        name = translate("Pattern"),
        )
    if is_open:
            draw_pattern(self,main)
            templates.main_spacing(main)

    is_open = templates.main_panel(self,main,
        prop_str = "geo_filter_main",
        icon = "W_TERRAIN",
        name = translate("Abiotic"),
        )
    if is_open:
            draw_geo_filter(self,main)
            templates.main_spacing(main)

    is_open = templates.main_panel(self,main,
        prop_str = "proxi_filter_main",
        icon = "W_SNAP",
        name = translate("Proximity"),
        )
    if is_open:
            draw_proximity(self,main)
            templates.main_spacing(main)

    is_open = templates.main_panel(self,main,
        prop_str = "ecosystem_main",
        icon = "W_ECOSYSTEM",
        name = translate("Ecosystem"),
        )
    if is_open:
            draw_ecosystem(self,main)
            templates.main_spacing(main)

    is_open = templates.main_panel(self,main,
        prop_str = "push_main",
        icon = "CON_LOCLIKE",
        name = translate("Offset"),
        )
    if is_open:
            draw_particle_push(self, main)
            templates.main_spacing(main)
            
    is_open = templates.main_panel(self,main,
        prop_str = "wind_main",
        icon = "FORCE_WIND",
        name = translate("Wind"),
        )
    if is_open:
            draw_wind(self,main)
            templates.main_spacing(main)

    is_open = templates.main_panel(self,main,
        prop_str = "visibility_main",
        icon = "HIDE_OFF",
        name = translate("Visibility"),
        )
    if is_open:
            draw_visibility(self,main)
            templates.main_spacing(main)

    is_open = templates.main_panel(self,main,
        prop_str = "instances_main",
        icon = "W_INSTANCE",
        name = translate("Instancing"),
        )
    if is_open:
            draw_instances(self,main)
            templates.main_spacing(main)

    is_open = templates.main_panel(self,main,
        prop_str = "display_main",
        icon = "CAMERA_STEREO",
        name = translate("Display"),
        )
    if is_open:
            draw_display(self,main)
            #draw_batch_set_display(self,main)
            templates.main_spacing(main)

    #Needed? i mean c'mon they won't purchase addons if they can't paint a vgroup right? 

    #if (scat_scene.sec_emit_verts_max_allow or scat_scene.sec_emit_verts_min_allow):
    #    verts=len(emitter.data.vertices)
    #    if (scat_scene.sec_emit_verts_min_allow and (verts<scat_scene.sec_emit_verts_min)):
    #        main.separator()
    #        word_wrap(layout=main.box(), string=translate("This emitter mesh is too low poly!\nVertex-groups masks need some Vertices!"), max_char=60,)

    layout.separator(factor=0.5)
    return 


#  .oooooo..o           oooo                          .    o8o                                   .o.
# d8P'    `Y8           `888                        .o8    `"'                                  .888.
# Y88bo.       .ooooo.   888   .ooooo.   .ooooo.  .o888oo oooo   .ooooo.  ooo. .oo.            .8"888.     oooo d8b  .ooooo.   .oooo.
#  `"Y8888o.  d88' `88b  888  d88' `88b d88' `"Y8   888   `888  d88' `88b `888P"Y88b          .8' `888.    `888""8P d88' `88b `P  )88b
#      `"Y88b 888ooo888  888  888ooo888 888         888    888  888   888  888   888         .88ooo8888.    888     888ooo888  .oP"888
# oo     .d8P 888    .o  888  888    .o 888   .o8   888 .  888  888   888  888   888        .8'     `888.   888     888    .o d8(  888
# 8""88888P'  `Y8bod8P' o888o `Y8bod8P' `Y8bod8P'   "888" o888o `Y8bod8P' o888o o888o      o88o     o8888o d888b    `Y8bod8P' `Y888""8o


def draw_particle_selection(self,layout):

    addon_prefs, scat_scene, scat_ui, scat_win, emitter = get_props()

    box, is_open = templates.sub_panel(self, layout, 
        prop_str   = "selection_sub1", 
        icon       = "PARTICLES", 
        name       = "         " + translate("Systems List"),
        description= "",
        doc        = translate("Select or set active your particle-system here.\nYou can select multiple system(s) at the same time to batch change properties by pressing 'ALT'\nNote that there's an Alternative system list view in Scatter manager interface, I'd advise to use this view when working with a lot of particles.")+"\n\n"+translate("Learn more in the Docs") +"_#LINK#_"+"https://sites.google.com/view/scatter5docs/manual/scattering#h.llfxvv18875z",
        )
    if is_open:

        psy_active = emitter.scatter5.get_psy_active()

        row = box.row()

        #left spacers
        row.separator(factor=0.5)

        #list template
        
        template = row.column()

        ui_list = template.column()
        ui_list.scale_y = addon_prefs.ui_selection_y
        ui_list.template_list("SCATTER5_UL_list_particles", "", emitter.scatter5, "particle_systems", emitter.scatter5, "particle_systems_idx", type="DEFAULT", rows=10,)

        #retrocompatibility warnings 

        if (psy_active is not None): 
            
            if (psy_active.scatter_obj is None):
                
                warning = template.column()
                warning.alert = True
                warning.label(text=translate("Missing Data"), icon="ERROR")

            elif (psy_active.scatter_obj.modifiers.get("Scatter5 Geonode Engine MKI") is None):

                template.separator(factor=0.5)
                warning = template.column().box()
                warning.alert = True
                word_wrap( string=translate("Warning, Particle-Systems created during the OpenBeta are not stable & not supported."), active=True,  layout=warning, alignment="CENTER", max_char=30,)

        #Operators side menu
        
        ope = row.column(align=True)

        #add
        
        add = ope.column(align=True)
        op = add.operator("scatter5.add_psy_simple",text="",icon="ADD",)
        op.emitter_name = emitter.name
        op.instance_names = "_!#!_".join( [o.name for o in bpy.context.selected_objects] )
        op.psy_color_random = True 

        #remove
        
        rem = ope.column(align=True)
        rem.enabled = psy_active is not None
        op = rem.operator("scatter5.remove_system",text="",icon="REMOVE",)
        op.undo_push=True
        op.emitter_name = emitter.name
        op.method = "name"
        if psy_active:
            op.name = psy_active.name

        ope.separator()
        
        #selection menu

        ope.menu("SCATTER5_MT_selection_menu", icon='DOWNARROW_HLT', text="",)

        ope.separator()        

        #move up & down

        updo = ope.column(align=True)
        updo.enabled = len(emitter.scatter5.particle_systems)!=0
        op = updo.operator("scatter5.list_move",text="",icon="TRIA_UP")
        op.target_idx = emitter.scatter5.particle_systems_idx       
        op.direction = "UP"    
        op.api_propgroup = "emitter.scatter5.particle_systems"
        op.api_propgroup_idx = "emitter.scatter5.particle_systems_idx"
        op = updo.operator("scatter5.list_move",text="",icon="TRIA_DOWN")
        op.target_idx = emitter.scatter5.particle_systems_idx       
        op.direction = "DOWN"   
        op.api_propgroup = "emitter.scatter5.particle_systems"
        op.api_propgroup_idx = "emitter.scatter5.particle_systems_idx"

        #right spacers
        row.separator(factor=0.1)

        templates.sub_spacing(box)

    return None 



class SCATTER5_MT_selection_menu(bpy.types.Menu):

    bl_idname      = "SCATTER5_MT_selection_menu"
    bl_label       = ""
    bl_description = ""

    def draw(self, context):
        
        emitter  = bpy.context.scene.scatter5.emitter
        psys     = emitter.scatter5.particle_systems
        psys_sel = emitter.scatter5.get_psys_selected()
        lenselecstr = f" ({len(psys_sel)})"

        layout=self.layout

        #Select All 

        psys_sel = [p.sel for p in emitter.scatter5.particle_systems]
        is_some_sel = (True in psys_sel)
        count = " " if not is_some_sel else f"{sum(psys_sel)}"
        is_full = (False not in psys_sel)
        text = translate("De-Select")+lenselecstr if (is_some_sel) else translate("Select All")+f" ({len(psys)})"
        args = {"text":text, "icon_value":cust_icon("W_SELECT_FULL")}  if is_full else {"text":text, "icon":"RESTRICT_SELECT_OFF" if is_some_sel else "RESTRICT_SELECT_ON"}
        sel = layout.row()
        sel.enabled = bool(len(psys))
        sel.operator("scatter5.toggle_selection",**args )

        #show color 

        sub = layout.row(align=True)
        sub.enabled = bool(len(psys))
        condition = (bpy.context.space_data.shading.type == 'SOLID') and (bpy.context.space_data.shading.color_type == 'OBJECT')
        op = sub.operator("scatter5.set_solid_and_object_color",text=translate("Show Systems Colors"), icon="COLOR",)
        op.mode = "restore" if condition else "set"

        layout.separator()

        #apply preset to selection

        row=layout.row()
        row.enabled = is_some_sel
        icon_gallery = row.enum_item_icon(bpy.context.window_manager,"scatter5_preset_gallery", bpy.context.window_manager.scatter5_preset_gallery)
        op = row.operator("scatter5.apply_preset_dialog",text=translate("Paste Preset to Selected")+lenselecstr,icon_value=icon_gallery)
        op.single_category = "all"
        op.method = "selection"

        layout.separator()
 
        #Copy 

        row=layout.row()
        row.enabled = is_some_sel
        op = row.operator("scatter5.copy_paste_systems",text=translate("Copy Selected Systems")+lenselecstr,icon="DUPLICATE")
        op.copy = True
        op.method = "selection"

        #Paste 

        from .. scattering.copy_paste import is_bufferpsy_filled

        row=layout.row() 
        row.enabled = is_bufferpsy_filled()
        op = row.operator("scatter5.copy_paste_systems",text=translate("Paste"),icon="DUPLICATE")
        op.paste = True
        op.synchronize = False

        row=layout.row()
        row.enabled = is_bufferpsy_filled()
        op = row.operator("scatter5.copy_paste_systems",text=translate("Paste & Synchronize Settings"),icon="DUPLICATE")
        op.paste = True
        op.synchronize = True

        layout.separator()

        #Save

        #col=layout.column()
        #col.enabled = is_some_sel
        #col.operator("scatter5.save_preset_to_disk_dialog", text=translate("Selected to Preset(s)")+lenselecstr, icon="FILE_NEW")
        #col.operator("scatter5.save_biome_to_disk_dialog", text=translate("Selected to Biome")+lenselecstr, icon="FILE_NEW")

        #layout.separator()
        
        #Remove System 

        sub = layout.row(align=True)
        sub.enabled = is_some_sel
        op = sub.operator("scatter5.remove_system",text=translate("Remove Selected")+lenselecstr, icon="TRASH")
        op.undo_push = True
        op.emitter_name = emitter.name
        op.method  = "selection"

        return None




class SCATTER5_UL_list_particles(bpy.types.UIList):
    """selection area"""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        
        if not item:
            return 
        row  = layout.row(align=True)
        row.scale_y = bpy.context.preferences.addons["Scatter5"].preferences.ui_selection_y
        
        #Selection 

        sub = row.row(align=True)
        sub.scale_x = 0.95
        sub.active = item.active
        sub.prop(item,"sel", text="", icon="RESTRICT_SELECT_OFF"if item.sel else "RESTRICT_SELECT_ON", emboss=False,)
        
        #Color 

        color = row.row()
        color.scale_x = 0.29
        color.prop(item,"s_color",text="")

        #Name 

        name = row.row(align=True)
        name.prop(item,"name", text="", emboss=False, )

        #Render Status
    
        sub = row.row(align=True)
        sub.active = item.active
        sub.scale_x = 0.95
        sub.prop(item, "hide_viewport", text="", icon="RESTRICT_VIEW_ON" if item.hide_viewport else "RESTRICT_VIEW_OFF", invert_checkbox=True, emboss=False,)
        sub.prop(item, "hide_render", text="", icon="RESTRICT_RENDER_ON" if item.hide_render else "RESTRICT_RENDER_OFF", invert_checkbox=True, emboss=False,)

        # loc = sub.row(align=True)
        # loc.scale_x = 0.9 #need narrow ui because of icon unusual size
        # loc.prop(item,"lock",
        #     text="",
        #     icon="LOCKED" if item.is_all_locked() else "UNLOCKED",
        #     invert_checkbox= item.is_all_locked(),
        #     emboss=False,
        #     )

        return


##############################################################################################################################################
#
#  .oooooo..o               .       .    o8o
# d8P'    `Y8             .o8     .o8    `"'
# Y88bo.       .ooooo.  .o888oo .o888oo oooo  ooo. .oo.    .oooooooo  .oooo.o
#  `"Y8888o.  d88' `88b   888     888   `888  `888P"Y88b  888' `88b  d88(  "8
#      `"Y88b 888ooo888   888     888    888   888   888  888   888  `"Y88b.
# oo     .d8P 888    .o   888 .   888 .  888   888   888  `88bod8P'  o.  )88b
# 8""88888P'  `Y8bod8P'   "888"   "888" o888o o888o o888o `8oooooo.  8""888P'
#                                                         d"     YD
#                                                         "Y88888P'
##############################################################################################################################################


# oooooooooo.    o8o               .             o8o   .o8                       .    o8o
# `888'   `Y8b   `"'             .o8             `"'  "888                     .o8    `"'
#  888      888 oooo   .oooo.o .o888oo oooo d8b oooo   888oooo.  oooo  oooo  .o888oo oooo   .ooooo.  ooo. .oo.
#  888      888 `888  d88(  "8   888   `888""8P `888   d88' `88b `888  `888    888   `888  d88' `88b `888P"Y88b
#  888      888  888  `"Y88b.    888    888      888   888   888  888   888    888    888  888   888  888   888
#  888     d88'  888  o.  )88b   888 .  888      888   888   888  888   888    888 .  888  888   888  888   888
# o888bood8P'   o888o 8""888P'   "888" d888b    o888o  `Y8bod8P'  `V88V"V8P'   "888" o888o `Y8bod8P' o888o o888o


def draw_particle_distribution(self,layout):

    addon_prefs, scat_scene, scat_ui, scat_win, emitter = get_props()

    box, is_open = templates.sub_panel(self, layout, 
        prop_str   = "distribution_sub1", 
        icon       = "STICKY_UVS_DISABLE", 
        name       = "         " + translate("Distribution"),
description= "",
doc        = translate("Select your particle-system here.\nYou can select multiple system(s) at the same time to batch change properties by pressing 'ALT'\nNote that there's an Alternative system list view in Scatter manager interface, I'd advise to use this view when working with a lot of particles.")+"\n\n"+translate("Learn more in the Docs") +"_#LINK#_"+"https://sites.google.com/view/scatter5docs/manual/scattering#h.llfxvv18875z",
        panel      = "SCATTER5_PT_settings",
        context_pointer_set = [["ctxt",scat_ui.type_s_distribution]],
        )
    if is_open:
            if warnings(box): return 

            psy_active = emitter.scatter5.get_psy_active()

            if lock_check(box, psy_active, "s_distribution"): return 
            sync_info(box, psy_active, s_category="s_distribution")
            
            mainr = box.row()
            mainr1 = mainr.row()
            mainr2 = mainr.row()

            col = mainr2.column(align=True)
            
            #Particle Count Info 
        
            # stats = col.row()
            # info_lbl = stats.row()
            # info_lbl.scale_x = 0.60
            # info_lbl.label(text=translate("Stats")+":")
            # info_col = stats.column(align=True)
            # #m²
            # info_box = info_col.box().row()
            # info_box.scale_y = 0.53
            # info_box.label(text="520.23 m²", icon="SURFACE_NSURFACE")
            # info_box_refr = info_box.row() ; info_box_refr.active = False ; info_box_refr.operator("scatter5.dummy",text="",icon="FILE_REFRESH", emboss=False,) #TODO
            # #view count
            # info_box = info_col.box().row()
            # info_box.scale_y = 0.53
            # info_box.label(text="30.000 p", icon="RESTRICT_VIEW_OFF")
            # info_box_refr = info_box.row() ; info_box_refr.active = False ; info_box_refr.operator("scatter5.dummy",text="",icon="FILE_REFRESH", emboss=False,) #TODO
            # #render count
            # info_box = info_col.box().row()
            # info_box.scale_y = 0.53
            # info_box.label(text="78.000 p", icon="RESTRICT_RENDER_OFF")
            # info_box_refr = info_box.row() ; info_box_refr.active = False ; info_box_refr.operator("scatter5.dummy",text="",icon="FILE_REFRESH", emboss=False,) #TODO

            # col.separator(factor=2.0)

            #Distribution Method 

            method = col.row()
            info_lbl = method.row()
            info_lbl.scale_x = 0.55
            info_lbl.label(text=translate("Method")+":")
            info_col = method.column(align=True)
            info_col.prop( psy_active, "s_distribution_method", text="",)
    
            #Distribution Space, manual is special case unfortunately
            
            if (psy_active.s_distribution_method!="manual_all"):
                
                col.separator()

                space = col.row()
                info_lbl = space.row()
                info_lbl.scale_x = 0.55
                info_lbl.label(text=translate("Space")+":") #TODO logically, distribution space only apply for /m² density, aka clump & random??
                info_col = space.column(align=True)
                info_col.prop( psy_active, "s_distribution_space", text="",)

            col.separator(factor=1.5)

            #Manual

            if (psy_active.s_distribution_method=="manual_all"):

                buttons = col.column(align=True)
                buttons.scale_y = 1.15
                
                draw_manual_brush_buttons(layout=buttons, cls=brushes.SCATTER5_OT_manual_dot_brush,)
                draw_manual_brush_buttons(layout=buttons, cls=brushes.SCATTER5_OT_manual_pose_brush,)   
                draw_manual_brush_buttons(layout=buttons, cls=brushes.SCATTER5_OT_manual_path_brush,)
                draw_manual_brush_buttons(layout=buttons, cls=brushes.SCATTER5_OT_manual_spatter_brush,)
                draw_manual_brush_buttons(layout=buttons, cls=brushes.SCATTER5_OT_manual_spray_brush,)
                
                buttons.separator()

                draw_manual_brush_buttons(layout=buttons, cls=brushes.SCATTER5_OT_manual_move_brush,)
                
                buttons.separator()
                
                draw_manual_brush_buttons(layout=buttons, cls=brushes.SCATTER5_OT_manual_eraser_brush,)
                draw_manual_brush_buttons(layout=buttons, cls=brushes.SCATTER5_OT_manual_dilute_brush,)                
                                                
                buttons.separator()
                
                op = buttons.column(align=True)
                edit = op.row(align=True)
                op.operator("scatter5.manual_drop", icon="NLA_PUSHDOWN",)
                edit.enabled = len(psy_active.scatter_obj.data.vertices)!=0
                edit = edit.operator("scatter5.exec_line", text=translate("Edit Points"), icon="EDITMODE_HLT",)
                edit.api = "bpy.ops.object.select_all(action='DESELECT') ; psy_active = bpy.context.scene.scatter5.emitter.scatter5.get_psy_active() ; bpy.context.view_layer.objects.active = psy_active.scatter_obj ; bpy.ops.object.editmode_toggle() ; bpy.ops.view3d.toggle_xray()"
                op.operator("scatter5.manual_clear", icon="TRASH",).confirmed = False 

                buttons.separator()

                word_wrap( string=translate("Be aware that procedural settings can override your points rotation / scale / density."), layout=buttons, alignment="CENTER", max_char=50,)

            #Random

            elif (psy_active.s_distribution_method=="random"):
                
                col.prop( psy_active, "s_distribution_density")

                sed = col.row(align=True)
                sed.prop( psy_active, "s_distribution_seed")
                sedbutton = sed.row(align=True)
                sedbutton.scale_x = 1.2
                sedbutton.prop( psy_active,"s_distribution_is_random_seed", icon_value=cust_icon("W_DICE"),text="")

                col.separator()

                coef = col.column(align=True)
                coef_prop = coef.row(align=True)
                coef_prop.prop( psy_active, "s_distribution_coef")
                coef_op = coef.row(align=True)
                coef_op.operator("scatter5.density_coef_calculation", text="*").operation="*"
                coef_op.operator("scatter5.density_coef_calculation", text="/").operation="/"
                coef_op.operator("scatter5.density_coef_calculation", text="+").operation="+"
                coef_op.operator("scatter5.density_coef_calculation", text="-").operation="-"

                col.separator()

                tocol, is_toggled = templates.bool_toggle(col, 
                    prop_api=psy_active,
                    prop_str="s_distribution_limit_distance_allow", 
                    label=translate("Limit Collision"), 
                    icon="AUTOMERGE_ON" if psy_active.s_distribution_limit_distance_allow else "AUTOMERGE_OFF", 
                    left_space=False,
                    panel_close=False,
                    )
                if is_toggled:

                    tocol.prop( psy_active, "s_distribution_limit_distance")

            #Clumping 

            elif (psy_active.s_distribution_method=="clumping"):

                #Clump Settings 
                #col.label(text=translate("Clumps")+":",)

                col.prop( psy_active, "s_distribution_clump_density")

                row = col.row(align=True)
                row.prop( psy_active, "s_distribution_clump_seed")
                button = row.row(align=True)
                button.scale_x = 1.2
                button.prop( psy_active, "s_distribution_clump_is_random_seed", icon_value=cust_icon("W_DICE"),text="")

                col.separator()
                
                col.prop( psy_active, "s_distribution_clump_max_distance")
                col.prop( psy_active, "s_distribution_clump_falloff")
                col.prop( psy_active, "s_distribution_clump_random_factor")

                col.separator()

                tocol, is_toggled = templates.bool_toggle(col, 
                    prop_api=psy_active,
                    prop_str="s_distribution_clump_limit_distance_allow", 
                    label=translate("Limit Collision"), 
                    icon="AUTOMERGE_ON" if psy_active.s_distribution_clump_limit_distance_allow else "AUTOMERGE_OFF", 
                    left_space=False,
                    panel_close=False,
                    )
                if is_toggled:

                    tocol.prop( psy_active, "s_distribution_clump_limit_distance")

                #Children Settings 

                col.separator(factor=2.0)

                #col.label(text=translate("Children")+":",)
                
                col.prop( psy_active,"s_distribution_clump_children_density")

                row = col.row(align=True)
                row.prop( psy_active, "s_distribution_clump_children_seed")
                button = row.row(align=True)
                button.scale_x = 1.2
                button.prop( psy_active, "s_distribution_clump_children_is_random_seed", icon_value=cust_icon("W_DICE"),text="")

                col.separator()

                tocol, is_toggled = templates.bool_toggle(col, 
                    prop_api=psy_active,
                    prop_str="s_distribution_clump_children_limit_distance_allow", 
                    label=translate("Limit Collision"), 
                    icon="AUTOMERGE_ON" if psy_active.s_distribution_clump_children_limit_distance_allow else "AUTOMERGE_OFF", 
                    left_space=False,
                    panel_close=False,
                    )
                if is_toggled:

                    tocol.prop( psy_active, "s_distribution_clump_children_limit_distance")

            #Pixel Based Distribution 

            elif (psy_active.s_distribution_method=="pixel"):

                box.label(text="Work in Progress")

            #Pixel Based Distribution 

            elif (psy_active.s_distribution_method=="curve"):

                box.label(text="Work in Progress")

            templates.sub_spacing(box)
    return 


# ooo        ooooo                    oooo
# `88.       .888'                    `888
#  888b     d'888   .oooo.    .oooo.o  888  oooo   .oooo.o
#  8 Y88. .P  888  `P  )88b  d88(  "8  888 .8P'   d88(  "8
#  8  `888'   888   .oP"888  `"Y88b.   888888.    `"Y88b.
#  8    Y     888  d8(  888  o.  )88b  888 `88b.  o.  )88b
# o8o        o888o `Y888""8o 8""888P' o888o o888o 8""888P'


def draw_particle_masks(self,layout):

    addon_prefs, scat_scene, scat_ui, scat_win, emitter = get_props()

    box, is_open = templates.sub_panel(self, layout, 
        prop_str   = "densmask_sub1", 
        icon       = "MOD_MASK", 
        name       =  translate("Remove Density"),
        description= "",
        doc        = translate("Mask your particles with the following masks features.")+"\n\n"+translate("Learn more in the Docs") +"_#LINK#_"+"https://sites.google.com/view/scatter5docs/manual/masks",
        #panel      = "SCATTER5_PT_maskdist",       
        )
    if is_open:
            if warnings(box): return 

            psy_active = emitter.scatter5.get_psy_active()

            ########## ########## Vgroup

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_mask_vg_allow", 
                label=translate("Vertex-Group"), 
                icon="WPAINT_HLT", 
                )
            if is_toggled:

                mask_col = tocol.column(align=True)
                mask_col.separator(factor=0.35)

                exists = (psy_active.s_mask_vg_ptr!="")

                mask = mask_col.row(align=True)
                mask.prop_search( psy_active, f"s_mask_vg_ptr", emitter, "vertex_groups",text="")
                
                if exists:
                    mask.prop( psy_active, f"s_mask_vg_revert",text="",icon="ARROW_LEFTRIGHT")

                op = mask.operator("scatter5.vg_quick_paint",text="",icon="BRUSH_DATA" if exists else "ADD", depress=is_vg_active(emitter,psy_active.s_mask_vg_ptr))
                op.group_name = psy_active.s_mask_vg_ptr
                op.mode       = "vg" 
                op.api        = f"emitter.scatter5.particle_systems['{psy_active.name}'].s_mask_vg_ptr"

                tocol.separator(factor=0.5)

            ########## ########## Vcolor

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_mask_vcol_allow", 
                label=translate("Vertex-Color"), 
                icon="VPAINT_HLT", 
                )
            if is_toggled:

                mask_col = tocol.column(align=True)

                exists = (psy_active.s_mask_vcol_ptr!="")
                set_color = (0,0,0)

                if exists:

                    #pick method 

                    meth = mask_col.row(align=True)

                    #custom color 

                    if (psy_active.s_mask_vcol_color_sample_method=="id_picker"):
                        color = meth.row(align=True)
                        color.scale_x = 0.35
                        color.prop(psy_active, "s_mask_vcol_id_color_ptr",text="")

                        set_color = psy_active.s_mask_vcol_id_color_ptr
                    else: 
                        equivalence = {"id_greyscale":(1,1,1),"id_red":(1,0,0),"id_green":(0,1,0),"id_blue":(0,0,1),"id_black":(0,0,0),"id_white":(1,1,1),"id_saturation":(1,1,1),"id_value":(1,1,1)}
                        set_color = equivalence[psy_active.s_mask_vcol_color_sample_method]

                    #sample method
                    
                    meth.prop( psy_active, "s_mask_vcol_color_sample_method", text="")

                mask = mask_col.row(align=True)
                mask.prop_search( psy_active, "s_mask_vcol_ptr", emitter.data, "vertex_colors",text="")

                if exists:
                    mask.prop( psy_active, "s_mask_vcol_revert",text="",icon="ARROW_LEFTRIGHT")

                op = mask.operator("scatter5.vg_quick_paint",text="",icon="BRUSH_DATA" if exists else "ADD", depress=is_vg_active(emitter, psy_active.s_mask_vcol_ptr))
                op.group_name = psy_active.s_mask_vcol_ptr
                op.set_color = set_color
                op.mode = "vcol" 
                op.api = f"emitter.scatter5.particle_systems['{psy_active.name}'].s_mask_vcol_ptr"

                tocol.separator(factor=0.2)

            ########## ########## Bitmap

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_mask_bitmap_allow", 
                label=translate("Image"), 
                icon="TPAINT_HLT", 
                )
            if is_toggled:

                mask_col = tocol.column(align=True)

                exists = (psy_active.s_mask_bitmap_ptr!="")
                set_color = (0,0,0)

                if exists:

                    #pick method 

                    meth = mask_col.row(align=True)

                    #custom color 

                    if (psy_active.s_mask_bitmap_color_sample_method=="id_picker"):
                        color = meth.row(align=True)
                        color.scale_x = 0.35
                        color.prop(psy_active, "s_mask_bitmap_id_color_ptr",text="")

                        set_color = psy_active.s_mask_bitmap_id_color_ptr
                    else: 
                        equivalence = {"id_greyscale":(1,1,1),"id_red":(1,0,0),"id_green":(0,1,0),"id_blue":(0,0,1),"id_black":(0,0,0),"id_white":(1,1,1),"id_saturation":(1,1,1),"id_value":(1,1,1)}
                        set_color = equivalence[psy_active.s_mask_bitmap_color_sample_method]

                    #sample method
                    
                    meth.prop( psy_active, "s_mask_bitmap_color_sample_method", text="")

                mask = mask_col.row(align=True)
                mask.prop_search( psy_active, "s_mask_bitmap_ptr", bpy.data, "images",text="")

                if not exists:

                    op = mask.operator("scatter5.image_utils",text="", icon="ADD",)
                    op.option = "new"
                    op.img_name = psy_active.s_mask_bitmap_ptr
                    op.api = f"emitter.scatter5.particle_systems['{psy_active.name}'].s_mask_bitmap_ptr"

                else:
                    mask.prop( psy_active, "s_mask_bitmap_revert",text="",icon="ARROW_LEFTRIGHT")
                    op = mask.operator("scatter5.image_utils",text="", icon="BRUSH_DATA", depress=(bpy.context.mode=="PAINT_TEXTURE") and (bpy.context.scene.tool_settings.image_paint.mode=='IMAGE') and (bpy.context.scene.tool_settings.image_paint.canvas==bpy.data.images.get(psy_active.s_mask_bitmap_ptr)))
                    op.option = "paint"
                    op.paint_color = set_color
                    op.uv_ptr = psy_active.s_mask_bitmap_uv_ptr
                    op.img_name= psy_active.s_mask_bitmap_ptr
                    op.api = f"emitter.scatter5.particle_systems['{psy_active.name}'].s_mask_bitmap_ptr"

                    mask_col.separator(factor=0.5)
                    mask_col.label(text=translate("UvMap")+":",)
                    mask_col.prop_search( psy_active, "s_mask_bitmap_uv_ptr", emitter.data, "uv_layers",text="")

                tocol.separator(factor=0.2)
                        
            ########## ########## Curve 

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_mask_curve_allow", 
                label=translate("Bezier-Area"), 
                icon="CURVE_BEZCIRCLE", 
                )
            if is_toggled:

                mask = tocol.row(align=True)
                mask.prop( psy_active, "s_mask_curve_ptr", text="", icon="CURVE_BEZCIRCLE")
                mask.prop( psy_active, "s_mask_curve_revert", text="",icon="ARROW_LEFTRIGHT")

                tocol.separator(factor=0.2)

            ########## ########## Upward Obstruction

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_mask_upward_allow", 
                label=translate("Upward-Obstruction"), 
                icon="GIZMO", 
                )
            if is_toggled:

                mask = tocol.row(align=True)
                mask.prop( psy_active, "s_mask_upward_coll_ptr", text="")
                mask.prop( psy_active, "s_mask_upward_revert", text="",icon="ARROW_LEFTRIGHT")

                tocol.separator(factor=0.2)

            ########## ########## Material

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_mask_material_allow", 
                label=translate("Material Slot"), 
                icon="MATERIAL", 
                )
            if is_toggled:

                mask = tocol.row(align=True)
                mask.prop_search( psy_active, "s_mask_material_ptr", emitter.data, "materials", text="")
                mask.prop( psy_active, "s_mask_material_revert", text="",icon="ARROW_LEFTRIGHT")

            templates.sub_spacing(box)
    return 


# ooooooooo.                 .                 .    o8o
# `888   `Y88.             .o8               .o8    `"'
#  888   .d88'  .ooooo.  .o888oo  .oooo.   .o888oo oooo   .ooooo.  ooo. .oo.
#  888ooo88P'  d88' `88b   888   `P  )88b    888   `888  d88' `88b `888P"Y88b
#  888`88b.    888   888   888    .oP"888    888    888  888   888  888   888
#  888  `88b.  888   888   888 . d8(  888    888 .  888  888   888  888   888
# o888o  o888o `Y8bod8P'   "888" `Y888""8o   "888" o888o `Y8bod8P' o888o o888o



def draw_particle_rot(self,layout):

    addon_prefs, scat_scene, scat_ui, scat_win, emitter = get_props()

    box, is_open = templates.sub_panel(self, layout, 
        prop_str   = "rotation_sub1", 
        icon       = "CON_ROTLIKE", 
        name       = "         " + translate("Rotation"),
        description= "",
        doc        = translate("Have complete control over your particles rotation settings and alignment.")+"\n\n"+translate("Learn more in the Docs") +"_#LINK#_"+"https://sites.google.com/view/scatter5docs/manual/rotation",
        panel      = "SCATTER5_PT_settings",       
        context_pointer_set = [["ctxt",scat_ui.type_s_rot]],
        )
    if is_open:
            if warnings(box): return 

            psy_active = emitter.scatter5.get_psy_active()

            if lock_check(box, psy_active, "s_rot"): return 
            sync_info(box, psy_active, s_category="s_rot")

            ########## ########## Manual Workflow

            if ((psy_active.s_distribution_method=="manual_all")):

                mainr = box.row()
                mainr1 = mainr.row()
                mainr2 = mainr.row()

                col = mainr2.column(align=True)
                col.scale_y = 1.15

                draw_manual_brush_buttons(layout=col, cls=brushes.SCATTER5_OT_manual_comb_brush, )
                draw_manual_brush_buttons(layout=col, cls=brushes.SCATTER5_OT_manual_z_align_brush, )

                col.separator()

                draw_manual_brush_buttons(layout=col, cls=brushes.SCATTER5_OT_manual_rotation_brush, )
                draw_manual_brush_buttons(layout=col, cls=brushes.SCATTER5_OT_manual_random_rotation_brush, )

                # lab = col.row()
                # lab.enabled = False
                # lab.label(text=translate("Settings below will influence manual attributes."))

            ########## ########## Align Z
            
            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_rot_align_z_allow", 
                label=translate("Align Normal"), 
                icon="W_ARROW_NORMAL", 
                )
            if is_toggled:

                #Normal Alignment 

                met = tocol.column(align=True)
                met.label(text=translate("Default Axis")+":")

                enum_row = met.row(align=True)
                enum_row.prop( psy_active,"s_rot_align_z_method", text="")
                enum_row.prop( psy_active,"s_rot_align_z_revert", text="", icon="ARROW_LEFTRIGHT")

                if psy_active.s_rot_align_z_method in ("meth_align_z_object","meth_align_z_origin","meth_align_z_normal","meth_align_z_random"):

                    # if (psy_active.s_rot_align_z_method=="meth_align_z_random"):
                        
                    #     met.separator()
                    #     seed = met.row(align=True)
                    #     seed.prop( psy_active, "s_rot_align_z_random_seed")
                    #     button = seed.row(align=True)
                    #     button.scale_x = 1.2
                    #     button.prop( psy_active, "s_rot_align_z_is_random_seed", icon_value=cust_icon("W_DICE"),text="")

                    if (psy_active.s_rot_align_z_method=="meth_align_z_object"):

                        met.separator()
                        met.prop( psy_active, "s_rot_align_z_object",text="")

                    met.separator()

                    tocol2, is_toggled2 = templates.bool_toggle(met, 
                        prop_api=psy_active,
                        prop_str="s_rot_align_z_influence_allow", 
                        label=translate("Vertical Influence"), 
                        icon="EMPTY_SINGLE_ARROW", 
                        left_space=False,
                        panel_close=False,
                        )
                    if is_toggled2:

                        tocol2.prop( psy_active, "s_rot_align_z_influence_value")

                if (psy_active.s_distribution_method=="clumping"):

                    met.separator()

                    tocol2, is_toggled = templates.bool_toggle(met, 
                        prop_api=psy_active,
                        prop_str="s_rot_align_z_clump_allow", 
                        label=translate("Clump Normal Influence"), 
                        icon="W_CLUMP", 
                        left_space=False,
                        panel_close=False,
                        )
                    if is_toggled:

                        tocol2.prop(psy_active, "s_rot_align_z_clump_value", expand=True)

                met.separator(factor=1.1)

            ########## ########## Align Y
            
            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_rot_align_y_allow", 
                label=translate("Align Tangent"), 
                icon="W_ARROW_TANGENT", 
                )
            if is_toggled:
                    
                #Tangent Alignment 

                met = tocol.column(align=True)
                met.label(text=translate("Default Axis")+":")

                enum_row = met.row(align=True)
                enum_row.prop( psy_active,"s_rot_align_y_method", text="")
                enum_row.prop( psy_active,"s_rot_align_y_revert", text="", icon="ARROW_LEFTRIGHT")

                if (psy_active.s_rot_align_y_method=="meth_align_y_object"):

                    met.separator()

                    met.prop( psy_active, "s_rot_align_y_object",text="")

                elif (psy_active.s_rot_align_y_method=="meth_align_y_random"):

                    met.separator()

                    seed = met.row(align=True)
                    seed.prop( psy_active, "s_rot_align_y_random_seed")
                    button = seed.row(align=True)
                    button.scale_x = 1.2
                    button.prop( psy_active, "s_rot_align_y_is_random_seed", icon_value=cust_icon("W_DICE"),text="")

                elif (psy_active.s_rot_align_y_method=="meth_align_y_flow"):

                    met.separator()

                    met.prop( psy_active, "s_rot_align_y_flow_method", text="")

                    if (psy_active.s_rot_align_y_flow_method=="flow_vcol"):

                        met.separator()

                        mask = met.row(align=True)
                        mask.prop_search( psy_active, "s_rot_align_y_vcol_ptr", emitter.data, "vertex_colors",text="")

                        ixon = "VPAINT_HLT" if psy_active.s_rot_align_y_vcol_ptr!="" else "ADD"
                        op = mask.operator("scatter5.vg_quick_paint",text="",icon=ixon, depress=is_vg_active(emitter, psy_active.s_rot_align_y_vcol_ptr))
                        op.group_name = psy_active.s_rot_align_y_vcol_ptr
                        op.mode       = "vcol" 
                        op.api        = f"emitter.scatter5.particle_systems['{psy_active.name}'].s_rot_align_y_vcol_ptr"

                        getflow = mask.row()
                        getflow.active = False
                        op = getflow.operator( "scatter5.popup_dialog", text="", icon="QUESTION",emboss=False)
                        op.no_confirm = True
                        op.msg = translate("Flowmaps cannot be created natively in blender. \n You'll need to download the Flowmap-painter addon by Clemens Beute on Gumroad.\n Then use his addon in Vertex-Paint while using the UV Space color theme option.")

                    elif (psy_active.s_rot_align_y_flow_method=="flow_text"):

                        met.separator()

                        #Draw Texture Data Block

                        block = met.column()
                        node = psy_active.scatter_obj.modifiers["Scatter5 Geonode Engine MKI"].node_group.nodes[f"TEXTURE_NODE s_rot_align_y"]
                        draw_texture_datablock(block, psy=psy_active, ptr_name=f"s_rot_align_y_texture_ptr", texture_node=node, new_name=f"Align")

                    met.separator()
                    met.prop( psy_active, "s_rot_align_y_flow_direction",)

                met.separator(factor=1.1)

            ########## ########## Rotate

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_rot_add_allow", 
                label=translate("Rotate"), 
                icon="CON_ROTLIKE",
                )
            if is_toggled:

                vec = tocol.column()
                vec.scale_y = 0.9
                vec.prop( psy_active, "s_rot_add_default")

                vec = tocol.column()
                vec.scale_y = 0.9
                vec.prop( psy_active, "s_rot_add_random")

                tocol.separator()
                col = tocol.column(align=True)

                seed = col.row(align=True)
                seed.prop( psy_active, "s_rot_add_seed")
                button = seed.row(align=True)
                button.scale_x = 1.2
                button.prop( psy_active, "s_rot_add_is_random_seed", icon_value=cust_icon("W_DICE"),text="")
                
                col.prop( psy_active, "s_rot_add_snap")

                #Universal Masking System

                draw_universal_masks(layout=tocol, mask_api="s_rot_add", psy_api=psy_active, emitter=emitter)

                tocol.separator()

            #Random

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_rot_random_allow", 
                label=translate("Random Rotation"), 
                icon="ORIENTATION_GIMBAL", 
                )
            if is_toggled:

                col = tocol.column(align=True)
                col.label(text=translate("Random Values")+":")
                col.prop( psy_active, "s_rot_random_tilt_value")
                col.prop( psy_active, "s_rot_random_yaw_value")

                seed = col.row(align=True)
                seed.prop( psy_active, "s_rot_random_seed")
                button = seed.row(align=True)
                button.scale_x = 1.2
                button.prop( psy_active, "s_rot_random_is_random_seed", icon_value=cust_icon("W_DICE"),text="")

                #Universal Masking System

                draw_universal_masks(layout=tocol, mask_api="s_rot_random", psy_api=psy_active, emitter=emitter)

                tocol.separator()

            ########## ########## Tilting

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_rot_tilt_allow", 
                label=translate("Flowmap Tilting"), 
                icon="W_ARROW_SWINGY", 
                )
            if is_toggled:

                met = tocol.column()
                met.label(text=translate("Flowmap-Data")+":")
                met.prop( psy_active, "s_rot_tilt_method", text="",)

                met.separator(factor=0.5)

                if (psy_active.s_rot_tilt_method=="tilt_vcol"):

                    #Draw Vcol Data Block 

                    mask = met.row(align=True)
                    mask.prop_search( psy_active, "s_rot_tilt_vcol_ptr", emitter.data, "vertex_colors",text="",)

                    ixon = "VPAINT_HLT" if psy_active.s_rot_tilt_vcol_ptr!="" else "ADD"
                    op = mask.operator("scatter5.vg_quick_paint",text="",icon=ixon, depress=is_vg_active(emitter, psy_active.s_rot_tilt_vcol_ptr))
                    op.group_name = psy_active.s_rot_tilt_vcol_ptr
                    op.mode = "vcol" 
                    op.api = f"emitter.scatter5.particle_systems['{psy_active.name}'].s_rot_tilt_vcol_ptr"

                    getflow = mask.row()
                    getflow.active = False
                    op = getflow.operator( "scatter5.popup_dialog", text="", icon="QUESTION",emboss=False)
                    op.no_confirm = True
                    op.msg = translate("Flowmaps cannot be created natively in blender. \n You'll need to download the Flowmap-painter addon by Clemens Beute on Gumroad.\n Then use his addon in Vertex-Paint while using the UV Space color theme option.")
            
                elif (psy_active.s_rot_tilt_method=="tilt_text"):
                    
                    #Draw Texture Data Block

                    block = met.column()
                    node = psy_active.scatter_obj.modifiers["Scatter5 Geonode Engine MKI"].node_group.nodes[f"TEXTURE_NODE s_rot_tilt"]
                    draw_texture_datablock(block, psy=psy_active, ptr_name=f"s_rot_tilt_texture_ptr", texture_node=node, new_name=f"Tilt")

                #strength

                tocol.separator(factor=0.5)

                props = tocol.column(align=True)
                props.label(text=translate("Tilting Value")+":")
                props.prop(psy_active,"s_rot_tilt_force")
                props.prop(psy_active,"s_rot_tilt_direction") #TODO 3.0 attribute rotate 

                #Blue channel strength

                tocol.separator(factor=0.5)
                templates.bool_toggle(tocol, 
                    prop_api=psy_active,
                    prop_str="s_rot_tilt_blue_is_strength", 
                    label=translate("Blue Channel Strength"), 
                    icon="COLOR_BLUE", 
                    left_space=False,
                    panel_close=False,
                    )

                #Universal Masking System

                draw_universal_masks(layout=tocol, mask_api="s_rot_tilt", psy_api=psy_active, emitter=emitter)

            templates.sub_spacing(box)
    return 


#  .oooooo..o                     oooo
# d8P'    `Y8                     `888
# Y88bo.       .ooooo.   .oooo.    888   .ooooo.
#  `"Y8888o.  d88' `"Y8 `P  )88b   888  d88' `88b
#      `"Y88b 888        .oP"888   888  888ooo888
# oo     .d8P 888   .o8 d8(  888   888  888    .o
# 8""88888P'  `Y8bod8P' `Y888""8o o888o `Y8bod8P'


def draw_particle_scale(self,layout):

    addon_prefs, scat_scene, scat_ui, scat_win, emitter = get_props()

    box, is_open = templates.sub_panel(self, layout, 
        prop_str   = "scale_sub1", 
        icon       = "OBJECT_ORIGIN", 
        name       = "         " + translate("Scale"),
        description= "",
        doc        = translate("Have control over the scale of your particles invarious ways.")+"\n\n"+translate("Learn more in the Docs") +"_#LINK#_"+"https://sites.google.com/view/scatter5docs/manual/scale",
        panel      = "SCATTER5_PT_settings",       
        context_pointer_set = [["ctxt",scat_ui.type_s_scale]],
        )
    if is_open:
            if warnings(box): return 

            psy_active = emitter.scatter5.get_psy_active()

            if lock_check(box, psy_active, "s_scale"): return 
            sync_info(box, psy_active, s_category="s_scale")

            ########## ########## Manual Workflow

            if (psy_active.s_distribution_method=="manual_all"):

                mainr = box.row()
                mainr1 = mainr.row()
                mainr2 = mainr.row()

                col = mainr2.column(align=True)
                col.scale_y = 1.15
                
                draw_manual_brush_buttons(layout=col, cls=brushes.SCATTER5_OT_manual_scale_brush, )
                draw_manual_brush_buttons(layout=col, cls=brushes.SCATTER5_OT_manual_scale_grow_shrink_brush, )
            
                # lab = col.row()
                # lab.enabled = False
                # lab.label(text=translate("Settings below will influence manual attributes."))

            ########## ########## Default 

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_scale_default_allow", 
                label=translate("Default Scale"), 
                icon="OBJECT_ORIGIN", 
                )
            if is_toggled:

                spaces = tocol.column(align=True)
                spaces.label(text=translate("Space")+":")
                spaces.prop( psy_active, "s_scale_default_space",text="")

                tocol.separator(factor=0.5)

                vec = tocol.column()
                vec.scale_y = 0.9
                vec.prop( psy_active, "s_scale_default_value",)

                tocol.separator(factor=0.1)

            ########## ########## Random

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_scale_random_allow", 
                label=translate("Random Scale"), 
                icon="W_DICE", 
                )
            if is_toggled:

                tocol.separator(factor=0.3)

                vec = tocol.column()
                vec.scale_y = 0.9
                vec.prop( psy_active, "s_scale_random_factor",)

                tocol.separator(factor=0.3)

                ccol = tocol.column(align=True)

                ccol.label(text=translate("Randomization Method")+":")
                lbl = ccol.column()
                lbl.scale_y = 0.9
                row = ccol.row(align=True)
                row.prop( psy_active, "s_scale_random_method", icon="BLANK1", expand=True)
                if (psy_active.s_scale_random_method=="random_uniform"):
                    row = ccol.row(align=True)
                    row.prop( psy_active, "s_scale_random_probability",)
                rrow = ccol.row(align=True)
                prop = rrow.row(align=True)
                prop.prop( psy_active, "s_scale_random_seed")
                button = rrow.row(align=True)
                button.scale_x = 1.2
                button.prop( psy_active, "s_scale_random_is_random_seed", icon_value=cust_icon("W_DICE"),text="")
                    
                tocol.separator(factor=0.1)

                #Universal Masking System

                draw_universal_masks(layout=tocol, mask_api="s_scale_random", psy_api=psy_active, emitter=emitter)

                tocol.separator()

            ########## ########## Shrink Mask

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_scale_shrink_allow", 
                label=translate("Shrink"), 
                icon="W_SCALE_SHRINK", 
                )
            if is_toggled:
                
                    vec = tocol.column()
                    vec.scale_y = 0.9
                    vec.prop( psy_active,"s_scale_shrink_factor")

                    #Universal Masking System

                    draw_universal_masks(layout=tocol, mask_api="s_scale_shrink", psy_api=psy_active, emitter=emitter)

                    tocol.separator()
                        
            ########## ########## Grow Mask

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_scale_grow_allow", 
                label=translate("Grow"), 
                icon="W_SCALE_GROW", 
                )
            if is_toggled:

                    vec = tocol.column()
                    vec.scale_y = 0.9
                    vec.prop( psy_active,"s_scale_grow_factor")

                    #Universal Masking System

                    draw_universal_masks(layout=tocol, mask_api="s_scale_grow", psy_api=psy_active, emitter=emitter)

                    #Error ?
                    
                    if psy_active.s_scale_grow_mask_ptr != "" and psy_active.s_scale_grow_mask_ptr==psy_active.s_scale_shrink_mask_ptr:

                        tocol.separator()

                        lbl = tocol.column()
                        lbl.scale_y = 0.8
                        lbl.active = False
                        lbl.label(text=translate("You are Shrinking/Growing at the same time"))
                        lbl.label(text=translate("This do not make a lot of sense!"))

                    tocol.separator()

            ########## ########## Mirror

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_scale_mirror_allow", 
                label=translate("Random Mirror"), 
                icon="MOD_MIRROR", 
                )
            if is_toggled:

                subcol = tocol.column(align=True)
                subcol.label(text=translate("Mirror Axis")+":")
                enum = subcol.row(align=True) 
                enum.prop(psy_active, "s_scale_mirror_is_x",text="X",icon="BLANK1")
                enum.prop(psy_active, "s_scale_mirror_is_y",text="Y",icon="BLANK1")
                enum.prop(psy_active, "s_scale_mirror_is_z",text="Z",icon="BLANK1")

                rrow = subcol.row(align=True)
                prop = rrow.row(align=True)
                prop.prop( psy_active, "s_scale_mirror_seed")
                button = rrow.row(align=True)
                button.scale_x = 1.2
                button.prop( psy_active, "s_scale_mirror_is_random_seed", icon_value=cust_icon("W_DICE"),text="")

                #Universal Masking System

                draw_universal_masks(layout=tocol, mask_api="s_scale_mirror", psy_api=psy_active, emitter=emitter)

                tocol.separator()

            ########## ########## Clump Distribution Special
            
            if (psy_active.s_distribution_method=="clumping"):

                tocol, is_toggled = templates.bool_toggle(box, 
                    prop_api=psy_active,
                    prop_str="s_scale_clump_allow", 
                    label=translate("Clump Scale"), 
                    icon="W_CLUMP_STRAIGHT", 
                    )
                if is_toggled:

                    tocol.prop(psy_active, "s_scale_clump_value")

                    tocol.separator()

            ########## ########## Minimal Scale

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_scale_min_allow", 
                label=translate("Minimal Scale"), 
                icon="CON_SAMEVOL", 
                )
            if is_toggled:

                subcol = tocol.column(align=True)
                subcol.label(text=translate("Treshold")+":")
                enum = subcol.row(align=True) 
                enum.prop(psy_active, "s_scale_min_method", expand=True)
                subcol.prop( psy_active, "s_scale_min_value")

            templates.sub_spacing(box)
    return 


# ooooooooo.                 .       .
# `888   `Y88.             .o8     .o8
#  888   .d88'  .oooo.   .o888oo .o888oo  .ooooo.  oooo d8b ooo. .oo.
#  888ooo88P'  `P  )88b    888     888   d88' `88b `888""8P `888P"Y88b
#  888          .oP"888    888     888   888ooo888  888      888   888
#  888         d8(  888    888 .   888 . 888    .o  888      888   888
# o888o        `Y888""8o   "888"   "888" `Y8bod8P' d888b    o888o o888o


def draw_pattern(self,layout):

    addon_prefs, scat_scene, scat_ui, scat_win, emitter = get_props()

    big_col = layout.column(align=True)
    box, is_open = templates.sub_panel(self, big_col, 
        prop_str    = f"pattern_sub1", 
        icon        = f"TEXTURE", 
        name        = "         " + translate("Pattern"),
        description = "",
        doc         = translate("Add some pattern influencing your particles density/scale with the help of blender texture-data.")+"\n\n"+translate("Learn more in the Docs") +"_#LINK#_"+"https://sites.google.com/view/scatter5docs/manual/pattern",
        panel       = "SCATTER5_PT_settings",       
        context_pointer_set = [["ctxt",scat_ui.type_s_pattern]],
        )

    if is_open:
        if warnings(box): return 

        psy_active = emitter.scatter5.get_psy_active()

        if lock_check(box, psy_active, f"s_pattern"): return
        sync_info(box, psy_active, s_category=f"s_pattern")

        for i in (1,2):

            ########## ########## Pattern 1&2

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str=f"s_pattern{i}_allow",
                label=translate("Pattern")+str(i),
                icon=f"W_PATTERN{i}", 
                )
            if is_toggled:


                #Draw Texture Data Block

                block = tocol.column()
                block.label(text=translate("Texture-Data")+":")
                node = psy_active.scatter_obj.modifiers["Scatter5 Geonode Engine MKI"].node_group.nodes[f"TEXTURE_NODE s_pattern{i}"]
                draw_texture_datablock(block, psy=psy_active, ptr_name=f"s_pattern{i}_texture_ptr", texture_node=node, new_name=f"Pattern{i}")

                #Draw Particle ID specific
                    
                tocol.separator(factor=0.5)

                met=tocol.column(align=True)
                met.prop( psy_active, f"s_pattern{i}_color_sample_method", text="")
                color_sample_method = eval(f"psy_active.s_pattern{i}_color_sample_method")
                if (color_sample_method == "id_picker"):

                    pick = met.row(align=True)
                    ptrc = pick.row(align=True)
                    ptrc.scale_x = 0.4
                    ptrc.prop( psy_active, f"s_pattern{i}_id_color_ptr", text="")
                    pick.prop( psy_active, f"s_pattern{i}_id_color_tolerence")

                # Remap
                #
                # tocol.separator(factor=2)
                # tocol.operator("scatter5.dummy",text=translate("Remap Values"), icon="FCURVE") #TODO FOR LATER ?

                #Particle Influence

                col=tocol.column(align=True)
                col.separator()
                lbl=col.row()
                lbl.scale_y = 0.9
                lbl.label(text=translate("Influence")+":")

                row=col.row(align=True)
                row.prop( psy_active, f"s_pattern{i}_dist_influence")
                row.prop( psy_active, f"s_pattern{i}_dist_revert", text="", icon="ARROW_LEFTRIGHT")
                row=col.row(align=True)
                row.prop( psy_active, f"s_pattern{i}_scale_influence")
                row.prop( psy_active, f"s_pattern{i}_scale_revert", text="", icon="ARROW_LEFTRIGHT")

                tocol.separator(factor=0.44)

                #Universal Masking System

                draw_universal_masks(layout=tocol, mask_api=f"s_pattern{i}", psy_api=psy_active, emitter=emitter)

        templates.sub_spacing(box)
    return 


#       .o.        .o8        o8o                .    o8o
#      .888.      "888        `"'              .o8    `"'
#     .8"888.      888oooo.  oooo   .ooooo.  .o888oo oooo   .ooooo.
#    .8' `888.     d88' `88b `888  d88' `88b   888   `888  d88' `"Y8
#   .88ooo8888.    888   888  888  888   888   888    888  888
#  .8'     `888.   888   888  888  888   888   888 .  888  888   .o8
# o88o     o8888o  `Y8bod8P' o888o `Y8bod8P'   "888" o888o `Y8bod8P'


def draw_geo_filter(self,layout):

    addon_prefs, scat_scene, scat_ui, scat_win, emitter = get_props()

    box, is_open = templates.sub_panel(self, layout, 
        prop_str   = "geo_filter_sub1", 
        icon       = "W_TERRAIN", 
        name       = "         "+ translate("Abiotic"),
        description= "",
        doc        = translate("The terrain abiotic factors are all factors related to your terrain surface that can influence your particles density/scale, such as slope or altitude for example.")+"\n\n"+translate("Learn more in the Docs") +"_#LINK#_"+"https://sites.google.com/view/scatter5docs/manual/abiotic",
        panel      = "SCATTER5_PT_settings",       
        context_pointer_set = [["ctxt",scat_ui.type_s_abiotic]],
        )
    if is_open:
            if warnings(box): return 

            psy_active = emitter.scatter5.get_psy_active()

            if lock_check(box, psy_active, "s_abiotic"): return 
            sync_info(box, psy_active, s_category="s_abiotic")

            ########## ########## Elevation 

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_abiotic_elev_allow", 
                label=translate("Elevation"), 
                icon="W_ALTITUDE", 
                )
            if is_toggled:

                spaces = tocol.column(align=True)
                spaces.label(text=translate("Space")+":")
                spaces.prop( psy_active, "s_abiotic_elev_space",text="")

                tocol.separator(factor=0.5)

                #Min/Max & Falloff 

                elevprp = tocol.column(align=True)
                elevprp.label(text=translate("Treshold")+":",)
                elevprp.scale_y = 0.9
                elevprp.prop(psy_active, f"s_abiotic_elev_min_value_{psy_active.s_abiotic_elev_space}")  
                elevprp.prop(psy_active, f"s_abiotic_elev_min_falloff_{psy_active.s_abiotic_elev_space}")  

                tocol.separator(factor=0.5)

                elevprp = tocol.column(align=True)
                elevprp.scale_y = 0.9
                elevprp.prop(psy_active, f"s_abiotic_elev_max_value_{psy_active.s_abiotic_elev_space}")  
                elevprp.prop(psy_active, f"s_abiotic_elev_max_falloff_{psy_active.s_abiotic_elev_space}")  

                #Particle Influence

                col=tocol.column(align=True)
                lbl=col.row()
                lbl.scale_y = 0.9
                lbl.label(text=translate("Influence")+":")

                row=col.row(align=True)
                row.prop( psy_active, f"s_abiotic_elev_dist_influence")
                row.prop( psy_active, f"s_abiotic_elev_dist_revert", text="", icon="ARROW_LEFTRIGHT")
                row=col.row(align=True)
                row.prop( psy_active, f"s_abiotic_elev_scale_influence")
                row.prop( psy_active, f"s_abiotic_elev_scale_revert", text="", icon="ARROW_LEFTRIGHT")

                #Universal Masking System

                draw_universal_masks(layout=tocol, mask_api=f"s_abiotic_elev", psy_api=psy_active, emitter=emitter)

                tocol.separator()

            ########## ########## Slope 

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_abiotic_slope_allow", 
                label=translate("Slope"), 
                icon="W_SLOPE", 
                )
            if is_toggled:

                spaces = tocol.column(align=True)
                spaces.label(text=translate("Space")+":")
                spaces.prop( psy_active, "s_abiotic_slope_space",text="")

                tocol.separator(factor=0.5)

                templates.bool_toggle(tocol, 
                    prop_api=psy_active,
                    prop_str="s_abiotic_slope_absolute", 
                    label=translate("Absolute Slope"), 
                    icon="CON_TRANSLIKE", 
                    left_space=False,
                    panel_close=False,
                    )

                tocol.separator(factor=0.5)

                #Min/Max & Falloff 

                slpprp = tocol.column(align=True)
                slpprp.label(text=translate("Treshold")+":",)
                slpprp.scale_y = 0.9
                slpprp.prop(psy_active, "s_abiotic_slope_min_value")     
                slpprp.prop(psy_active, "s_abiotic_slope_min_falloff")     

                tocol.separator(factor=0.5)

                slpprp = tocol.column(align=True)
                slpprp.scale_y = 0.9
                slpprp.prop(psy_active, "s_abiotic_slope_max_value")     
                slpprp.prop(psy_active, "s_abiotic_slope_max_falloff")   

                #Particle Influence

                col=tocol.column(align=True)
                lbl=col.row()
                lbl.scale_y = 0.9
                lbl.label(text=translate("Influence")+":")

                row=col.row(align=True)
                row.prop( psy_active, f"s_abiotic_slope_dist_influence")
                row.prop( psy_active, f"s_abiotic_slope_dist_revert", text="", icon="ARROW_LEFTRIGHT")
                row=col.row(align=True)
                row.prop( psy_active, f"s_abiotic_slope_scale_influence")
                row.prop( psy_active, f"s_abiotic_slope_scale_revert", text="", icon="ARROW_LEFTRIGHT")

                #Universal Masking System

                draw_universal_masks(layout=tocol, mask_api=f"s_abiotic_slope", psy_api=psy_active, emitter=emitter)

                tocol.separator()

            ########## ########## Normal 

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_abiotic_dir_allow", 
                label=translate("Orientation"), 
                icon="NORMALS_FACE", 
                )
            if is_toggled:

                spaces = tocol.column(align=True)
                spaces.label(text=translate("Space")+":")
                spaces.prop( psy_active, "s_abiotic_dir_space",text="")

                tocol.separator(factor=0.5)

                #Direction & Treshold

                dirprp = tocol.column()
                lbl=dirprp.row()
                lbl.scale_y = 0.9
                lbl.label(text=translate("Treshold")+":")
                rwoo = dirprp.row()
                rwoo.prop( psy_active, "s_abiotic_dir_direction", text="")
                rowc = rwoo.column()
                rowc.scale_x = 0.55
                rowc.prop( psy_active, "s_abiotic_dir_direction_euler", text="", expand=True) #alias of direction

                tocol.separator(factor=0.7)

                dirprp = tocol.column(align=True,)
                dirprp.prop(psy_active, "s_abiotic_dir_max")
                dirprp.prop(psy_active, "s_abiotic_dir_treshold")

                #Particle Influence

                col=tocol.column(align=True)
                lbl=col.row()
                lbl.scale_y = 0.9
                lbl.label(text=translate("Influence")+":")

                row=col.row(align=True)
                row.prop( psy_active, f"s_abiotic_dir_dist_influence")
                row.prop( psy_active, f"s_abiotic_dir_dist_revert", text="", icon="ARROW_LEFTRIGHT")
                row=col.row(align=True)
                row.prop( psy_active, f"s_abiotic_dir_scale_influence")
                row.prop( psy_active, f"s_abiotic_dir_scale_revert", text="", icon="ARROW_LEFTRIGHT")

                #Universal Masking System

                draw_universal_masks(layout=tocol, mask_api=f"s_abiotic_dir", psy_api=psy_active, emitter=emitter)

                tocol.separator()

            ########## ########## Curvature 

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_abiotic_cur_allow", 
                label=translate("Curvature"), 
                icon="W_CURVATURE", 
                )
            if is_toggled:

                spaces = tocol.column(align=True)
                spaces.label(text=translate("Treshold")+":")
                spaces.prop( psy_active, "s_abiotic_cur_type",text="")

                tocol.separator(factor=0.5)
                
                #Treshold

                curprp = tocol.column(align=True,)
                curprp.prop(psy_active, "s_abiotic_cur_max")
                curprp.prop(psy_active, "s_abiotic_cur_treshold")

                #Particle Influence

                col=tocol.column(align=True)
                lbl=col.row()
                lbl.scale_y = 0.9
                lbl.label(text=translate("Influence")+":")

                row=col.row(align=True)
                row.prop( psy_active, f"s_abiotic_cur_dist_influence")
                row.prop( psy_active, f"s_abiotic_cur_dist_revert", text="", icon="ARROW_LEFTRIGHT")
                row=col.row(align=True)
                row.prop( psy_active, f"s_abiotic_cur_scale_influence")
                row.prop( psy_active, f"s_abiotic_cur_scale_revert", text="", icon="ARROW_LEFTRIGHT")

                #Universal Masking System

                draw_universal_masks(layout=tocol, mask_api=f"s_abiotic_cur", psy_api=psy_active, emitter=emitter)

                tocol.separator()

            ########## ########## Border 

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_abiotic_border_allow", 
                label=translate("Border"), 
                icon="W_BORDER", 
                )
            if is_toggled:

                #Treshold

                curprp = tocol.column(align=True)
                curprp.label(text=translate("Treshold")+":")                
                curprp.prop(psy_active, "s_abiotic_border_max")
                curprp.prop(psy_active, "s_abiotic_border_treshold")

                #Particle Influence

                col=tocol.column(align=True)
                lbl=col.row()
                lbl.scale_y = 0.9
                lbl.label(text=translate("Influence")+":")

                row=col.row(align=True)
                row.prop( psy_active, f"s_abiotic_border_dist_influence")
                row.prop( psy_active, f"s_abiotic_border_dist_revert", text="", icon="ARROW_LEFTRIGHT")
                row=col.row(align=True)
                row.prop( psy_active, f"s_abiotic_border_scale_influence")
                row.prop( psy_active, f"s_abiotic_border_scale_revert", text="", icon="ARROW_LEFTRIGHT")

                #Universal Masking System

                draw_universal_masks(layout=tocol, mask_api=f"s_abiotic_border", psy_api=psy_active, emitter=emitter)

            templates.sub_spacing(box)
    return 


# ooooooooo.                                   o8o                     o8o      .
# `888   `Y88.                                 `"'                     `"'    .o8
#  888   .d88' oooo d8b  .ooooo.  oooo    ooo oooo  ooo. .oo.  .oo.   oooo  .o888oo oooo    ooo
#  888ooo88P'  `888""8P d88' `88b  `88b..8P'  `888  `888P"Y88bP"Y88b  `888    888    `88.  .8'
#  888          888     888   888    Y888'     888   888   888   888   888    888     `88..8'
#  888          888     888   888  .o8"'88b    888   888   888   888   888    888 .    `888'
# o888o        d888b    `Y8bod8P' o88'   888o o888o o888o o888o o888o o888o   "888"     .8'
#                                                                                   .o..P'
#                                                                                   `Y8P'


def draw_proximity(self,layout):

    addon_prefs, scat_scene, scat_ui, scat_win, emitter = get_props()

    box, is_open = templates.sub_panel(self, layout, 
        prop_str   = "proxi_filter_sub1", 
        icon       = "W_SNAP", 
        name       = "         "+ translate("Proximity"),
        description= "",
        doc        = translate("Influence your particles density/rotation/scale with the proximity of other elements in your scene.")+"\n\n"+translate("Learn more in the Docs") +"_#LINK#_"+"https://sites.google.com/view/scatter5docs/manual/proximity",
        panel      = "SCATTER5_PT_settings",       
        context_pointer_set = [["ctxt",scat_ui.type_s_proximity]],
        )
    if is_open:
            if warnings(box): return 

            psy_active = emitter.scatter5.get_psy_active()
            
            if lock_check(box, psy_active, "s_proximity"): return 
            sync_info(box, psy_active, s_category="s_proximity")

            ########## ########## Remove Near

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_proximity_removenear_allow",
                label=translate("Remove Near Object"), 
                icon="SELECT_SUBTRACT", 
                )
            if is_toggled:

                #Target
                proxprp = tocol.column(align=True)
                proxprp.label(text=translate("Collection")+":")
                ptr_row = proxprp.row(align=True)
                ptr_row.prop(psy_active, "s_proximity_removenear_coll_ptr", text="")
                ptr_row_enum = ptr_row.row(align=True)
                ptr_row_enum.scale_x = 0.9
                ptr_row_enum.prop(psy_active, "s_proximity_removenear_type", text="", icon_only=True)

                if psy_active.s_proximity_removenear_coll_ptr!=None:

                    tocol.separator(factor=0.5)

                    #Treshold

                    proxprp = tocol.column(align=True)
                    proxprp.prop(psy_active, "s_proximity_removenear_max")
                    proxprp.prop(psy_active, "s_proximity_removenear_treshold")

                    #Particle Influence

                    col=tocol.column(align=True)
                    lbl=col.row()
                    lbl.scale_y = 0.9
                    lbl.label(text=translate("Influence")+":")

                    row=col.row(align=True)
                    row.prop( psy_active, f"s_proximity_removenear_dist_influence")
                    row.prop( psy_active, f"s_proximity_removenear_dist_revert", text="", icon="ARROW_LEFTRIGHT")
                    row=col.row(align=True)
                    row.prop( psy_active, f"s_proximity_removenear_scale_influence")
                    row.prop( psy_active, f"s_proximity_removenear_scale_revert", text="", icon="ARROW_LEFTRIGHT")

                    #Universal Masking System

                    draw_universal_masks(layout=tocol, mask_api=f"s_proximity_removenear", psy_api=psy_active, emitter=emitter)

                tocol.separator()

            ########## ########## Tilt Near

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_proximity_leanover_allow",
                label=translate("Lean Near Object"),
                icon="GP_MULTIFRAME_EDITING", 
                )
            if is_toggled:

                #Target
                proxprp = tocol.column(align=True)
                proxprp.label(text=translate("Collection")+":")
                ptr_row = proxprp.row(align=True)
                ptr_row.prop(psy_active, "s_proximity_leanover_coll_ptr", text="")
                ptr_row_enum = ptr_row.row(align=True)
                ptr_row_enum.scale_x = 0.9
                ptr_row_enum.prop(psy_active, "s_proximity_leanover_type", text="", icon_only=True)

                if psy_active.s_proximity_leanover_coll_ptr!=None:

                    tocol.separator(factor=0.5)

                    #Treshold

                    proxprp = tocol.column(align=True)
                    proxprp.prop(psy_active, "s_proximity_leanover_max")
                    proxprp.prop(psy_active, "s_proximity_leanover_treshold")

                    #Turbulence #5.1 Helicopter Hover example

                    # tocol.separator(factor=0.5)

                    # tocol2, is_toggled2 = templates.bool_toggle(tocol, 
                    #     prop_api=psy_active,
                    #     prop_str="s_proximity_leanover_turbulence_allow", 
                    #     label=translate("Turbulence"), 
                    #     icon="HAIR_DATA", 
                    #     left_space=False,
                    #     panel_close=False,
                    #     )
                    # if is_toggled2:

                    #     proxprp = tocol2.column(align=True)
                    #     proxprp.prop( psy_active, f"s_proximity_leanover_turbulence_scale")
                    #     proxprp.prop( psy_active, f"s_proximity_leanover_turbulence_detail")
                    #     proxprp.prop( psy_active, f"s_proximity_leanover_turbulence_speed")

                    #     tocol2.separator()

                    #Particle Influence

                    col=tocol.column(align=True)
                    lbl=col.row()
                    lbl.scale_y = 0.9
                    lbl.label(text=translate("Influence")+":")

                    proxprp=col.column(align=True)
                    proxprp.prop( psy_active, f"s_proximity_leanover_scale_influence")
                    proxprp.prop( psy_active, f"s_proximity_leanover_tilt_influence")

                    #Universal Masking System

                    draw_universal_masks(layout=tocol, mask_api=f"s_proximity_leanover", psy_api=psy_active, emitter=emitter)

                tocol.separator()

            ########## ########## Outskirt 

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_proximity_outskirt_allow",
                label=translate("Outskirt (Experimental)"), 
                icon="W_PROXBOU", 
                )
            if is_toggled:

                #Treshold

                curprp = tocol.column(align=True)
                curprp.label(text=translate("Treshold")+":")                
                curprp.prop(psy_active, "s_proximity_outskirt_treshold")
                curprp.prop(psy_active, "s_proximity_outskirt_limit")

                #Particle Influence

                col=tocol.column(align=True)
                lbl=col.row()
                lbl.scale_y = 0.9
                lbl.label(text=translate("Influence")+":")

                proxprp=col.column(align=True)
                proxprp.prop( psy_active, f"s_proximity_outskirt_scale_influence")
                proxprp.prop( psy_active, f"s_proximity_outskirt_tilt_influence")

                #Universal Masking System

                draw_universal_masks(layout=tocol, mask_api=f"s_proximity_outskirt", psy_api=psy_active, emitter=emitter)

            #Near Pathway 

            # tocol, is_toggled = templates.bool_toggle(box, 
            #     prop_api=psy_active,
            #     prop_str="s_proximity_curve_allow",
            #     label=translate("Proximity by Bezier-Curve"), 
            #     icon="CURVE_DATA", 
            #     )
            # if is_toggled:
            #     tocol.label(text="Work in Progress")

            templates.sub_spacing(box)
    return 


# oooooooooooo                                                       .
# `888'     `8                                                     .o8
#  888          .ooooo.   .ooooo.   .oooo.o oooo    ooo  .oooo.o .o888oo  .ooooo.  ooo. .oo.  .oo.
#  888oooo8    d88' `"Y8 d88' `88b d88(  "8  `88.  .8'  d88(  "8   888   d88' `88b `888P"Y88bP"Y88b
#  888    "    888       888   888 `"Y88b.    `88..8'   `"Y88b.    888   888ooo888  888   888   888
#  888       o 888   .o8 888   888 o.  )88b    `888'    o.  )88b   888 . 888    .o  888   888   888
# o888ooooood8 `Y8bod8P' `Y8bod8P' 8""888P'     .8'     8""888P'   "888" `Y8bod8P' o888o o888o o888o
#                                           .o..P'
#                                           `Y8P'

def draw_ecosystem(self,layout):

    addon_prefs, scat_scene, scat_ui, scat_win, emitter = get_props()

    box, is_open = templates.sub_panel(self, layout, 
        prop_str   = "ecosystem_sub1", 
        icon       = "W_ECOSYSTEM", 
        name       = "         "+ translate("Ecosystem"),
        description= "",
        doc        = translate("Influence your particles density/rotation/scale with the proximity of other elements in your scene.")+"\n\n"+translate("Learn more in the Docs") +"_#LINK#_"+"https://sites.google.com/view/scatter5docs/manual/proximity",
        panel      = "SCATTER5_PT_settings",       
        context_pointer_set = [["ctxt",scat_ui.type_s_ecosystem]],
        )
    if is_open:
            if warnings(box): return 

            psy_active = emitter.scatter5.get_psy_active()
            
            if lock_check(box, psy_active, "s_ecosystem"): return 
            sync_info(box, psy_active, s_category="s_ecosystem")

            ########## ########## Affinity

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str=f"s_ecosystem_affinity_allow",
                label=translate("Affinity"),
                icon="W_AFFINITY",
                )
            if is_toggled:
                
                for i in (1,2,3):

                    #do not display slots unecessarily
                    target_name_1 = getattr(psy_active, f"s_ecosystem_affinity_01_ptr")
                    target_name_2 = getattr(psy_active, f"s_ecosystem_affinity_02_ptr")
                    target_name_3 = getattr(psy_active, f"s_ecosystem_affinity_03_ptr")
                    if (i==2 and (target_name_1=="" and target_name_2=="" and target_name_3=="")):
                        continue
                    elif (i==3 and (target_name_2=="" and target_name_3=="")):
                        continue

                    api_str = f"s_ecosystem_affinity_{i:02}"
                    target_name = eval(f"target_name_{i}")
                    target_null = (target_name == "")
                    target_loop = (target_name == psy_active.name)
                    target_exists = (target_name in emitter.scatter5.particle_systems)

                    if i!=1:
                        tocol.separator(factor=0.85)
                    part_col = tocol.column(align=True)
                    part_lbl = part_col.column(align=True)
                    part_lbl.label(text=translate("Affinity")+f" {i}:")
                    ptr_row = part_col.row(align=True)

                    if (not target_null and target_exists):

                        psy_col = ptr_row.row(align=True)
                        psy_col.scale_x = 0.3
                        psy_col.prop(emitter.scatter5.particle_systems[target_name], "s_color", text="")

                    ptr_row.prop_search(psy_active, f"{api_str}_ptr", emitter.scatter5, "particle_systems", text="", icon="PARTICLES")
                    ptr_row_enum = ptr_row.row(align=True)
                    ptr_row_enum.scale_x = 0.9
                    ptr_row_enum.prop(psy_active, f"{api_str}_type", text="", icon_only=True)

                    if target_null:
                        tocol.separator(factor=0.5)
                        continue

                    if target_loop:
                        lbl=part_col.column()
                        lbl.alert=True
                        lbl.label(text=translate("Feedback Loop Detected"),icon="ERROR")
                        if (i==1 and (target_name_2=="" and target_name_3=="")) or (i==2 and (target_name_3=="")):
                            break
                        continue

                    if not target_exists:
                        lbl=part_col.column()
                        lbl.alert=True
                        lbl.label(text=translate("System does not exist"),icon="ERROR")
                        if (i==1 and (target_name_2=="" and target_name_3=="")) or (i==2 and (target_name_3=="")):
                            break
                        continue    

                    part_props = part_col.column(align=True)
                    part_props.separator(factor=0.5)
                    part_props.prop(psy_active, f"{api_str}_max_value",)
                    part_props.prop(psy_active, f"{api_str}_max_falloff",)
                    part_props.prop(psy_active, f"{api_str}_limit_distance",)

                    if (i==getattr(psy_active,f"s_ecosystem_affinity_ui_max_slot") and i!=3):
                        if (i==1 and (target_name_2=="" and target_name_3=="")) or (i==2 and (target_name_3=="")):

                            part_col.separator(factor=0.5)
                            addslot = part_col.row()
                            addslot.scale_y = 0.9
                            addslot.operator("scatter5.exec_line", text=translate("Add Affinity"), icon="ADD").api = f"bpy.data.objects['{emitter.name}'].scatter5.particle_systems['{psy_active.name}'].s_ecosystem_affinity_ui_max_slot +=1"
                            
                            tocol.separator(factor=0.75)
                            
                            break

                    continue

                tocol.separator(factor=0.25)

                #Particle Influence

                col=tocol.column(align=True)
                lbl=col.row()
                lbl.scale_y = 0.9
                lbl.label(text=translate("Influence")+":")
                col.prop( psy_active, f"s_ecosystem_affinity_dist_influence")
                col.prop( psy_active, f"s_ecosystem_affinity_scale_influence")

                #Universal Masking System

                draw_universal_masks(layout=tocol, mask_api="s_ecosystem_affinity", psy_api=psy_active, emitter=emitter)

                tocol.separator()

            ########## ########## Repulsion

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str=f"s_ecosystem_repulsion_allow",
                label=translate("Repulsion"),
                icon="W_REPULSION",
                )
            if is_toggled:
                
                for i in (1,2,3):

                    #do not display slots unecessarily
                    target_name_1 = getattr(psy_active, f"s_ecosystem_repulsion_01_ptr")
                    target_name_2 = getattr(psy_active, f"s_ecosystem_repulsion_02_ptr")
                    target_name_3 = getattr(psy_active, f"s_ecosystem_repulsion_03_ptr")
                    if (i==2 and (target_name_1=="" and target_name_2=="" and target_name_3=="")):
                        continue
                    elif (i==3 and (target_name_2=="" and target_name_3=="")):
                        continue

                    api_str = f"s_ecosystem_repulsion_{i:02}"
                    target_name = eval(f"target_name_{i}")
                    target_null = (target_name == "")
                    target_loop = (target_name == psy_active.name)
                    target_exists = (target_name in emitter.scatter5.particle_systems)

                    if i!=1:
                        tocol.separator(factor=0.85)
                    part_col = tocol.column(align=True)
                    part_lbl = part_col.column(align=True)
                    part_lbl.label(text=translate("Repulsion")+f" {i}:")
                    ptr_row = part_col.row(align=True)

                    if (not target_null and target_exists):

                        psy_col = ptr_row.row(align=True)
                        psy_col.scale_x = 0.3
                        psy_col.prop(emitter.scatter5.particle_systems[target_name], "s_color", text="")

                    ptr_row.prop_search(psy_active, f"{api_str}_ptr", emitter.scatter5, "particle_systems", text="", icon="PARTICLES")
                    ptr_row_enum = ptr_row.row(align=True)
                    ptr_row_enum.scale_x = 0.9
                    ptr_row_enum.prop(psy_active, f"{api_str}_type", text="", icon_only=True)

                    if target_null:
                        tocol.separator(factor=0.5)
                        continue

                    if target_loop:
                        lbl=part_col.column()
                        lbl.alert=True
                        lbl.label(text=translate("Feedback Loop Detected"),icon="ERROR")
                        if (i==1 and (target_name_2=="" and target_name_3=="")) or (i==2 and (target_name_3=="")):
                            break
                        continue

                    if not target_exists:
                        lbl=part_col.column()
                        lbl.alert=True
                        lbl.label(text=translate("System does not exist"),icon="ERROR")
                        if (i==1 and (target_name_2=="" and target_name_3=="")) or (i==2 and (target_name_3=="")):
                            break
                        continue    

                    part_props = part_col.column(align=True)
                    part_props.separator(factor=0.5)
                    part_props.prop(psy_active, f"{api_str}_max_value",)
                    part_props.prop(psy_active, f"{api_str}_max_falloff",)

                    if (i==getattr(psy_active,f"s_ecosystem_repulsion_ui_max_slot") and i!=3):
                        if (i==1 and (target_name_2=="" and target_name_3=="")) or (i==2 and (target_name_3=="")):

                            part_col.separator(factor=0.5)
                            addslot = part_col.row()
                            addslot.scale_y = 0.9
                            addslot.operator("scatter5.exec_line", text=translate("Add Repulsion"), icon="ADD").api = f"bpy.data.objects['{emitter.name}'].scatter5.particle_systems['{psy_active.name}'].s_ecosystem_repulsion_ui_max_slot +=1"
                            
                            tocol.separator(factor=0.75)
                            
                            break

                    continue

                tocol.separator(factor=0.25)

                #Particle Influence

                col=tocol.column(align=True)
                lbl=col.row()
                lbl.scale_y = 0.9
                lbl.label(text=translate("Influence")+":")
                col.prop( psy_active, f"s_ecosystem_repulsion_dist_influence")
                col.prop( psy_active, f"s_ecosystem_repulsion_scale_influence")

                #Universal Masking System

                draw_universal_masks(layout=tocol, mask_api="s_ecosystem_repulsion", psy_api=psy_active, emitter=emitter)

                tocol.separator()

            templates.sub_spacing(box)
    return 


#   .oooooo.    .o88o.  .o88o.                        .
#  d8P'  `Y8b   888 `"  888 `"                      .o8
# 888      888 o888oo  o888oo   .oooo.o  .ooooo.  .o888oo
# 888      888  888     888    d88(  "8 d88' `88b   888
# 888      888  888     888    `"Y88b.  888ooo888   888
# `88b    d88'  888     888    o.  )88b 888    .o   888 .
#  `Y8bood8P'  o888o   o888o   8""888P' `Y8bod8P'   "888"


def draw_particle_push(self,layout):

    addon_prefs, scat_scene, scat_ui, scat_win, emitter = get_props()

    box, is_open = templates.sub_panel(self, layout, 
        prop_str   = "push_sub1", 
        icon       = "CON_LOCLIKE", 
        name       = "         " + translate("Offset"),
        description= "",
        doc        = translate("Offset your particles, push them around, or add falling effects.")+"\n\n"+translate("Learn more in the Docs") +"_#LINK#_"+"https://sites.google.com/view/scatter5docs/manual/offset",
        panel      = "SCATTER5_PT_settings",       
        context_pointer_set = [["ctxt",scat_ui.type_s_push]],
        )
    if is_open:
            if warnings(box): return 

            psy_active = emitter.scatter5.get_psy_active()

            if lock_check(box, psy_active, "s_push"): return 
            sync_info(box, psy_active, s_category="s_push")

            ########## ########## Push Offset 

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_push_offset_allow", 
                label=translate("Location Offset/Scale"), 
                icon="CON_LOCLIKE", 
                )
            if is_toggled:

                vec = tocol.column()
                vec.label(text=translate("Offset Value/Random")+":")
                vecr = vec.row(align=True)
                veccol = vecr.column(align=True)
                veccol.scale_y = 0.9
                veccol.prop(psy_active,"s_push_offset_add_value",text="")
                veccol = vecr.column(align=True)
                veccol.scale_y = 0.9
                veccol.prop(psy_active,"s_push_offset_add_random",text="")

                tocol.separator(factor=0.5)

                vec = tocol.column()
                vec.label(text=translate("Scale Value/Random")+":")
                vecr = vec.row(align=True)
                veccol = vecr.column(align=True)
                veccol.scale_y = 0.9
                veccol.prop(psy_active,"s_push_offset_scale_value",text="")
                veccol = vecr.column(align=True)
                veccol.scale_y = 0.9
                veccol.prop(psy_active,"s_push_offset_scale_random",text="")

                tocol.separator(factor=0.3)

                #Universal Masking System
                draw_universal_masks(layout=tocol, mask_api=f"s_push_offset", psy_api=psy_active, emitter=emitter)

                tocol.separator()

            ########## ########## Push Direction

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_push_dir_allow", 
                label=translate("Push Along"), 
                icon="SORT_DESC", 
                )
            if is_toggled:

                met = tocol.column(align=True)
                met.prop( psy_active, "s_push_dir_method", text="")
                met.separator()

                vec = tocol.column()
                vec.label(text=translate("Offset")+":")
                veccol = vec.column(align=True)
                veccol.scale_y = 0.9
                veccol.prop(psy_active,"s_push_dir_add_value",)
                veccol.prop(psy_active,"s_push_dir_add_random",)

                tocol.separator(factor=0.3)

                #Universal Masking System
                draw_universal_masks(layout=tocol, mask_api=f"s_push_dir", psy_api=psy_active, emitter=emitter)

                tocol.separator()

            ########## ########## Push Noise

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_push_noise_allow", 
                label=translate("Noise Animation"), 
                icon="BOIDS", 
                )
            if is_toggled:

                col = tocol.column()
                col.scale_y = 0.85
                col.prop( psy_active, "s_push_noise_vector")

                tocol.separator(factor=0.5)
                tocol.prop( psy_active, "s_push_noise_speed")

                #Universal Masking System
                draw_universal_masks(layout=tocol, mask_api=f"s_push_noise", psy_api=psy_active, emitter=emitter)

                tocol.separator()

            ########## ########## Push Fall

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_push_fall_allow", 
                label=translate("Falling Animation"), 
                icon="FORCE_FORCE", 
                )
            if is_toggled:

                props =tocol.column(align=True)
                props.scale_y = 0.9
                props.label(text=translate("Start/End")+":")
                props_pos = props.row(align=True)
                props_pos.prop(psy_active, "s_push_fall_key1_pos")
                props_pos.prop(psy_active, "s_push_fall_key2_pos", text="")
                props_hei = props.row(align=True)
                props_hei.prop(psy_active, "s_push_fall_key1_height")
                props_hei.prop(psy_active, "s_push_fall_key2_height", text="")

                tocol.separator(factor=0.5)
                tocol.prop(psy_active, "s_push_fall_height")
                
                tocol.separator()
                templates.bool_toggle(tocol, 
                    prop_api=psy_active,
                    prop_str="s_push_fall_stop_when_initial_z", 
                    label=translate("Fall at Initial Position"), 
                    icon="ANCHOR_BOTTOM", 
                    left_space=False,
                    panel_close=False,
                    )

                tocol.separator(factor=0.5)

                tocol2, is_toggled2 = templates.bool_toggle(tocol, 
                    prop_api=psy_active,
                    prop_str="s_push_fall_turbulence_allow", 
                    label=translate("Fall Turbulence"), 
                    icon="FORCE_MAGNETIC", 
                    left_space=False,
                    panel_close=False,
                    )
                if is_toggled2:
                        
                    vec = tocol2.column(align=True)
                    vec.scale_y = 0.85
                    vec.prop( psy_active, "s_push_fall_turbulence_spread")

                    tocol2.separator(factor=0.5)
                    tocol2.prop( psy_active, "s_push_fall_turbulence_speed")
                    
                    vec = tocol2.column(align=True)
                    vec.scale_y = 0.85
                    vec.prop( psy_active, "s_push_fall_turbulence_rot_vector")

                    tocol2.separator(factor=0.5)
                    tocol2.prop( psy_active, "s_push_fall_turbulence_rot_factor", expand=False)

                #Universal Masking System
                draw_universal_masks(layout=tocol, mask_api=f"s_push_fall", psy_api=psy_active, emitter=emitter)

                tocol.separator()

            templates.sub_spacing(box)
    return 


# oooooo   oooooo     oooo  o8o                    .o8
#  `888.    `888.     .8'   `"'                   "888
#   `888.   .8888.   .8'   oooo  ooo. .oo.    .oooo888
#    `888  .8'`888. .8'    `888  `888P"Y88b  d88' `888
#     `888.8'  `888.8'      888   888   888  888   888
#      `888'    `888'       888   888   888  888   888
#       `8'      `8'       o888o o888o o888o `Y8bod88P"


def draw_wind(self,layout):

    addon_prefs, scat_scene, scat_ui, scat_win, emitter = get_props()

    box, is_open = templates.sub_panel(self, layout, 
        prop_str   = "wind_sub1", 
        icon       = "FORCE_WIND", 
        name       = "         "+ translate("Wind"),
        description= "",
        doc        = translate("Add wind effects on your scattering by tilting your particles.")+"\n\n"+translate("Learn more in the Docs") +"_#LINK#_"+"https://sites.google.com/view/scatter5docs/manual/wind",
        panel      = "SCATTER5_PT_settings",       
        context_pointer_set = [["ctxt",scat_ui.type_s_wind]],
        )
    if is_open:
            if warnings(box): return 

            psy_active = emitter.scatter5.get_psy_active()

            if lock_check(box, psy_active, "s_wind"): return
            sync_info(box, psy_active, s_category="s_wind")


            ########## ########## Wind Wave

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_wind_wave_allow", 
                label=translate("Wind Waves"), 
                icon="FORCE_WIND", 
                )
            if is_toggled:

                col = tocol.column(align=True)
                col.scale_y = 0.9
                col.label(text=translate("Wind Settings")+":")
                col.prop(psy_active, "s_wind_wave_speed")
                col.prop(psy_active, "s_wind_wave_force")
                
                tocol.separator(factor=0.5)

                templates.bool_toggle(tocol, 
                    prop_api=psy_active,
                    prop_str="s_wind_wave_swinging", 
                    label=translate("Bilateral Swing"), 
                    icon="W_ARROW_SWINGY",
                    left_space=False,
                    panel_close=False,
                    )
                
                tocol.separator(factor=0.5)

                templates.bool_toggle(tocol, 
                    prop_api=psy_active,
                    prop_str="s_wind_wave_scale_influence", 
                    label=translate("Scale Influence"), 
                    icon="CON_SAMEVOL",
                    left_space=False,
                    panel_close=False,
                    )

                tocol.separator(factor=0.5)

                col = tocol.column(align=True)
                col.label(text=translate("Wind Direction")+":")
                col.prop( psy_active,"s_wind_wave_dir_method", text="")

                tocol.separator(factor=0.5)

                if (psy_active.s_wind_wave_dir_method=="vcol"):

                    tocol.prop(psy_active, "s_wind_wave_direction")

                    tocol.separator(factor=0.5)

                    mask = tocol.row(align=True)
                    mask.prop_search( psy_active, "s_wind_wave_flowmap_ptr", emitter.data, "vertex_colors",text="",)

                    ixon = "VPAINT_HLT" if psy_active.s_wind_wave_flowmap_ptr!="" else "ADD"
                    op = mask.operator("scatter5.vg_quick_paint",text="",icon=ixon, depress=is_vg_active(emitter, psy_active.s_wind_wave_flowmap_ptr))
                    op.group_name = psy_active.s_wind_wave_flowmap_ptr
                    op.mode = "vcol" 
                    op.api = f"emitter.scatter5.particle_systems['{psy_active.name}'].s_wind_wave_flowmap_ptr"

                    getflow = mask.row()
                    getflow.active = False
                    op = getflow.operator( "scatter5.popup_dialog", text="", icon="QUESTION",emboss=False)
                    op.no_confirm = True
                    op.msg = translate("Flowmaps cannot be created natively in blender. \n You'll need to download the Flowmap-painter addon by Clemens Beute on Gumroad.\n Then use his addon in Vertex-Paint while using the UV Space color theme option.")

                elif (psy_active.s_wind_wave_dir_method=="fixed"):

                    tocol.prop(psy_active, "s_wind_wave_direction")

                tocol.separator(factor=0.7)

                col = tocol.column(align=True)
                col.scale_y = 0.9
                col.label(text=translate("Waves Pattern")+":")
                col.prop(psy_active, "s_wind_wave_texture_scale")
                col.prop(psy_active, "s_wind_wave_texture_turbulence")
                col.prop(psy_active, "s_wind_wave_texture_brightness")
                col.prop(psy_active, "s_wind_wave_texture_contrast")

                #Universal Masking System
                draw_universal_masks(layout=tocol, mask_api=f"s_wind_wave", psy_api=psy_active, emitter=emitter)

                tocol.separator(factor=0.5)

            ########## ########## Wind noise 

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_wind_noise_allow", 
                label=translate("Wind Turbulence"), 
                icon="FORCE_TURBULENCE", 
                )
            if is_toggled:

                col = tocol.column(align=True)
                col.scale_y = 0.9
                col.label(text=translate("Wind Settings")+":")
                col.prop(psy_active, "s_wind_noise_force")
                col.prop(psy_active, "s_wind_noise_speed")

                #Universal Masking System
                draw_universal_masks(layout=tocol, mask_api=f"s_wind_noise", psy_api=psy_active, emitter=emitter)

            templates.sub_spacing(box)

    return 


# oooooo     oooo  o8o            o8o   .o8        o8o  oooo   o8o      .
#  `888.     .8'   `"'            `"'  "888        `"'  `888   `"'    .o8
#   `888.   .8'   oooo   .oooo.o oooo   888oooo.  oooo   888  oooo  .o888oo oooo    ooo
#    `888. .8'    `888  d88(  "8 `888   d88' `88b `888   888  `888    888    `88.  .8'
#     `888.8'      888  `"Y88b.   888   888   888  888   888   888    888     `88..8'
#      `888'       888  o.  )88b  888   888   888  888   888   888    888 .    `888'
#       `8'       o888o 8""888P' o888o  `Y8bod8P' o888o o888o o888o   "888"     .8'
#                                                                           .o..P'
#                                                                           `Y8P'

def draw_visibility(self,layout):
    
    addon_prefs, scat_scene, scat_ui, scat_win, emitter = get_props()

    box, is_open = templates.sub_panel(self, layout, 
        prop_str   = "visibility_sub1", 
        icon       = "HIDE_OFF", 
        name       = "         " + translate("Visibility"),
        description= "",
        doc        = translate("Control your particles visibility to optimize your viewport performance.\nNote that these settings are not saved per scattering presets/biomes.")+"\n\n"+translate("Learn more in the Docs") +"_#LINK#_"+"https://sites.google.com/view/scatter5docs/manual/visibility",
        panel      = "SCATTER5_PT_settings",       
        context_pointer_set = [["ctxt",scat_ui.type_s_visibility]],
        )
    if is_open:
            if warnings(box): return 

            psy_active = emitter.scatter5.get_psy_active()

            if lock_check(box, psy_active, "s_visibility"): return 
            sync_info(box, psy_active, s_category="s_visibility")

            # row = box.row()
            # row_1 = row.row() ; row_1.scale_x = 0.01
            # row_2 = row.row() ; row_2.scale_x = 1.0
            # row_3 = row.row() ; row_3.scale_x = 1.0
            # row_2.prop(psy_active, "hide_viewport", text="", icon="RESTRICT_VIEW_ON" if psy_active.hide_viewport else "RESTRICT_VIEW_OFF", invert_checkbox=True)
            # row_3.label(text =translate("This particle-system is Hidden") if psy_active.hide_viewport else translate("This particle-system is Visible"))
            
            ########## ########## Percentage

            if psy_active.s_distribution_method in ["clumping","random"]:


                tocol, is_toggled = templates.bool_toggle(box, 
                    prop_api=psy_active,
                    prop_str="s_visibility_view_allow", 
                    label=translate("Density Reduction"), 
                    icon="W_PERCENTAGE", 
                    )
                if is_toggled:

                    tocol.prop(psy_active,"s_visibility_view_percentage",)
                        
                    #Viewport Method 

                    tocol.separator(factor=0.5)

                    prop = tocol.column(align=True)
                    prop.label(text=translate("Feature Visibility")+":",)
                    prop.prop(psy_active,"s_visibility_view_viewport_method",text="")

                    tocol.separator(factor=0.2)

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_visibility_cam_allow", 
                label=translate("Camera Optimization"), 
                icon="OUTLINER_OB_CAMERA", 
                enabled=bpy.context.scene.camera is not None,
                )
            if is_toggled:

                #Camera Frustrum 

                tocol2, is_toggled2 = templates.bool_toggle(tocol, 
                    prop_api=psy_active,
                    prop_str="s_visibility_camclip_allow", 
                    label=translate("Frustrum Culling"), 
                    icon="CAMERA_DATA", 
                    enabled=bpy.context.scene.camera is not None,
                    left_space=False,
                    panel_close=False,
                    )
                if is_toggled2:

                    prop = tocol2.column(align=True)
                    prop.scale_y = 0.9
                    prop.prop(psy_active, "s_visibility_camclip_dir_crop_x")
                    prop.prop(psy_active, "s_visibility_camclip_dir_crop_y")

                    tocol2.separator(factor=0.35)

                    prop = tocol2.column(align=True)
                    prop.scale_y = 0.9
                    prop.prop(psy_active, "s_visibility_camclip_dir_shift_x")
                    prop.prop(psy_active, "s_visibility_camclip_dir_shift_y")

                    tocol2.separator(factor=0.35)

                    prop = tocol2.column(align=True)
                    prop.prop(psy_active, "s_visibility_camclip_proximity")

                    tocol2.separator(factor=0.2)

                #Camera Distance Culling 

                tocol.separator(factor=0.2)
                tocol2, is_toggled2 = templates.bool_toggle(tocol, 
                    prop_api=psy_active,
                    prop_str="s_visibility_camdist_allow", 
                    label=translate("Distance Culling"), 
                    icon="DRIVER_DISTANCE", 
                    enabled=bpy.context.scene.camera is not None,
                    left_space=False,
                    panel_close=False,
                    )
                if is_toggled2:

                    prop = tocol2.column(align=True)
                    prop.scale_y = 0.9
                    prop.prop(psy_active, "s_visibility_camdist_min")
                    prop.prop(psy_active, "s_visibility_camdist_max")

                    tocol2.separator(factor=0.2)

                #Viewport Method 

                tocol.separator(factor=0.5)

                prop = tocol.column(align=True)
                prop.label(text=translate("Feature Visibility")+":",)
                prop.prop(psy_active,"s_visibility_cam_viewport_method",text="")


            templates.sub_spacing(box)
    return 


# ooooo                          .
# `888'                        .o8
#  888  ooo. .oo.    .oooo.o .o888oo  .oooo.   ooo. .oo.    .ooooo.   .ooooo.   .oooo.o
#  888  `888P"Y88b  d88(  "8   888   `P  )88b  `888P"Y88b  d88' `"Y8 d88' `88b d88(  "8
#  888   888   888  `"Y88b.    888    .oP"888   888   888  888       888ooo888 `"Y88b.
#  888   888   888  o.  )88b   888 . d8(  888   888   888  888   .o8 888    .o o.  )88b
# o888o o888o o888o 8""888P'   "888" `Y888""8o o888o o888o `Y8bod8P' `Y8bod8P' 8""888P'


class SCATTER5_UL_list_instances(bpy.types.UIList):
    """instance area"""

    def __init__(self,):
       self.use_filter_sort_alpha = True
       self.use_filter_show = False

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        
        if not item:
            return 

        addon_prefs, scat_scene, scat_ui, scat_win, emitter = get_props()
        psy_active = emitter.scatter5.get_psy_active()
        coll = psy_active.s_instances_coll_ptr

        #find index 

        i = None
        for i,o in enumerate(sorted(coll.objects, key= lambda o:o.name)):
            i+=1
            if o==item:
                break

        row = layout.row(align=True)
        row.scale_y = 0.7

        #select operator 

        selct = row.row()

        if (bpy.context.mode=="OBJECT"):

            selct.active = (item==bpy.context.object)
            op = selct.operator("scatter5.instance_selection",emboss=False,text="",icon="RESTRICT_SELECT_OFF" if item in bpy.context.selected_objects else "RESTRICT_SELECT_ON")
            op.obj_name = item.name
            op.coll_name = coll.name
        
        else:
            selct.separator(factor=1.2)

        #name 

        name = row.row()
        name.prop(item,"name", text="", emboss=False, )

        #pick method chosen? 

        if (psy_active.s_instances_pick_method != "pick_random"):

            #pick rate slider 

            if (psy_active.s_instances_pick_method == "pick_rate"):

                slider = row.row()

                if i<=20:
                    slider.prop( psy_active, f"s_instances_id_{i:02}_rate", text="",)
                else:
                    slider.alignment = "RIGHT"
                    slider.label(text=translate("Not Supported"),)

            #pick index 

            elif (psy_active.s_instances_pick_method == "pick_idx"):

                slider = row.row()
                slider.alignment= "RIGHT"
                slider.label(text=f"{i-1:02} ")

            #pick scale 

            elif (psy_active.s_instances_pick_method == "pick_scale"):

                slider = row.row(align=True)

                if i<=20:
                    slider.scale_x = 0.71
                    slider.prop( psy_active, f"s_instances_id_{i:02}_scale_min", text="",)
                    slider.prop( psy_active, f"s_instances_id_{i:02}_scale_max", text="",)
                else:
                    slider.operator("scatter5.dummy",text=translate("Not Supported"),)

            #pick color 

            elif (psy_active.s_instances_pick_method == "pick_color"):

                clr = row.row(align=True)
                clr.alignment = "RIGHT"

                if i<=20:
                      clr.prop( psy_active, f"s_instances_id_{i:02}_color", text="",)
                else: clr.label(text=translate("Not Supported"),)

        #remove operator 

        ope = row.row(align=False)
        ope.scale_x = 0.9
        ope.operator("scatter5.remove_instances",emboss=False,text="",icon="TRASH").ins_idx = i-1

        return


def draw_instances(self,layout):

    addon_prefs, scat_scene, scat_ui, scat_win, emitter = get_props()

    box, is_open = templates.sub_panel(self, layout, 
        prop_str   = "instances_sub1", 
        icon       = "W_INSTANCE", 
        name       = "         " + translate("Instancing"),
        description= "",
        doc        = translate("Have control over how your particles are assigned to your chosen instances.")+"\n\n"+translate("Learn more in the Docs") +"_#LINK#_"+"https://sites.google.com/view/scatter5docs/manual/instancing",
        panel      = "SCATTER5_PT_settings",       
        context_pointer_set = [["ctxt",scat_ui.type_s_instances]],
        )
    if is_open:
            if warnings(box): return 

            psy_active = emitter.scatter5.get_psy_active()

            if lock_check(box, psy_active, "s_instances"): return 
            sync_info(box, psy_active, s_category="s_instances")

            mainr = box.row()
            mainr1 = mainr.row()
            mainr1.separator(factor=0.8) 
            mainr2 = mainr.row()

            col = mainr2.column(align=True)
                
            #agencing two labels spaces correctly with c1 & c2 

            twor = col.row()
            c1 = twor.column()
            c1.scale_x = 0.55
            c2 = twor.column()

            #instancing method? 

            #c1.label(text=translate("Method")+":",)
            #c2.prop( psy_active, "s_instances_method", text="",)

            #collection method?

            if (psy_active.s_instances_method == "ins_collection"): 
                                
                #spawning method 

                c1.label(text=translate("Spawn")+":",)
                c2.prop( psy_active, "s_instances_pick_method", text="",)

                if (psy_active.s_instances_pick_method=="pick_idx") and (psy_active.s_distribution_method!="manual_all"):
                    
                    col.separator(factor=1.0)
                    word_wrap(string=translate("This method is designed for manual distribution mode only."), layout=col, alignment="CENTER", max_char=45,)
                    col.separator()

                    return None 

                #collection list 
                
                col.separator(factor=1.5)

                col.prop( psy_active, "s_instances_coll_ptr", text="",)

                col.separator(factor=0.75)

                coll = psy_active.s_instances_coll_ptr
                if (coll is None):
                    
                    col.separator()

                    return None

                #list template

                ui_list = col.column(align=True)
                ui_list.template_list("SCATTER5_UL_list_instances", "", coll, "objects", psy_active, "s_instances_list_idx", rows=5, sort_lock=True,)

                #add operator

                add = ui_list.column(align=True)
                add.active = (bpy.context.mode=="OBJECT")
                add.operator_menu_enum("scatter5.add_instances", "method", text=translate("Add Objects"), icon="ADD")

                #seed 

                if psy_active.s_instances_pick_method in ("pick_random","pick_rate",):

                    col.separator(factor=2)
                    
                    rrow = col.row(align=True)
                    prop = rrow.row(align=True)
                    prop.prop( psy_active, "s_instances_seed",)
                    button = rrow.row(align=True)
                    button.scale_x = 1.2
                    button.prop( psy_active, "s_instances_is_random_seed", icon_value=cust_icon("W_DICE"),text="",)

                #index

                elif (psy_active.s_instances_pick_method=="pick_idx"):

                    col.separator(factor=2)

                    button = col.row(align=True)
                    button.scale_y = 1.15
                    draw_manual_brush_buttons(layout=button, cls=brushes.SCATTER5_OT_manual_object_brush, )

                #scale

                elif (psy_active.s_instances_pick_method=="pick_scale"):

                    col.separator(factor=2)

                    col.prop( psy_active, "s_instances_id_scale_method", text="",)

                #color 

                elif (psy_active.s_instances_pick_method=="pick_color"):

                    col.separator(factor=2)

                    col.prop( psy_active, "s_instances_id_color_sample_method", text="",)

                    col.separator(factor=1)

                    if (psy_active.s_instances_id_color_sample_method=="vcol"):

                        mask = col.row(align=True)
                        mask.prop_search( psy_active, "s_instances_vcol_ptr", emitter.data, "vertex_colors",text="")

                        ixon = "VPAINT_HLT" if psy_active.s_instances_vcol_ptr!="" else "ADD"
                        op = mask.operator("scatter5.vg_quick_paint",text="",icon=ixon, depress=is_vg_active(emitter, psy_active.s_instances_vcol_ptr),)
                        op.group_name = psy_active.s_instances_vcol_ptr
                        op.mode       = "vcol" 
                        op.api        = f"emitter.scatter5.particle_systems['{psy_active.name}'].s_instances_vcol_ptr"

                    elif (psy_active.s_instances_id_color_sample_method=="text"):

                        #Draw Texture Data Block

                        block = col.column()
                        node = psy_active.scatter_obj.modifiers["Scatter5 Geonode Engine MKI"].node_group.nodes[f"TEXTURE_NODE s_instances"]
                        draw_texture_datablock(block, psy=psy_active, ptr_name=f"s_instances_texture_ptr", texture_node=node, new_name=f"ColorCluster")

                    col.separator(factor=1)

                    col.prop( psy_active, "s_instances_id_color_tolerence",)

                #cluster

                elif (psy_active.s_instances_pick_method=="pick_cluster"):
                        
                    col.separator(factor=2)

                    if (psy_active.s_distribution_method=="clumping"):

                        templates.bool_toggle(col, 
                            prop_api=psy_active,
                            prop_str="s_instances_pick_clump", 
                            label=translate("Use Clumps as Clusters"), 
                            icon="STICKY_UVS_LOC", 
                            left_space=False,
                            panel_close=False,
                            )

                        if psy_active.s_instances_pick_clump:

                            col = col.column(align=True)
                            col.active = False

                        col.separator(factor=1)

                    twor = col.row()
                    c1 = twor.column()
                    c1.scale_x = 0.55
                    c2 = twor.column()

                    c1.label(text=translate("Space")+":")
                    c2.prop( psy_active, "s_instances_pick_cluster_projection_method", text="",)

                    col.separator()
                    col.prop( psy_active, "s_instances_pick_cluster_scale",)
                    col.prop( psy_active, "s_instances_pick_cluster_blur",)
                
                    rrow = col.row(align=True)
                    prop = rrow.row(align=True)
                    prop.prop( psy_active, "s_instances_seed")
                    button = rrow.row(align=True)
                    button.scale_x = 1.2
                    button.prop( psy_active, "s_instances_is_random_seed", icon_value=cust_icon("W_DICE"),text="")

            #volume method? 

            elif (psy_active.s_instances_method == "ins_volume"): #TODO WILL NEED TO CHANGE FOR COLLECTION -> SEARCH ME 

                col.separator()

                coll = col.column(align=True)
                coll.scale_y = 0.95
                coll.prop(psy_active,"s_instances_volume_density")
                coll.prop(psy_active,"s_instances_volume_voxel_ammount")

            templates.sub_spacing(box)
    return 


# oooooooooo.    o8o                      oooo
# `888'   `Y8b   `"'                      `888
#  888      888 oooo   .oooo.o oo.ooooo.   888   .oooo.   oooo    ooo
#  888      888 `888  d88(  "8  888' `88b  888  `P  )88b   `88.  .8'
#  888      888  888  `"Y88b.   888   888  888   .oP"888    `88..8'
#  888     d88'  888  o.  )88b  888   888  888  d8(  888     `888'
# o888bood8P'   o888o 8""888P'  888bod8P' o888o `Y888""8o     .8'
#                               888                       .o..P'
#                              o888o                      `Y8P'


def draw_display(self,layout):
    
    addon_prefs, scat_scene, scat_ui, scat_win, emitter = get_props()

    box, is_open = templates.sub_panel(self, layout, 
        prop_str   = "display_sub1", 
        icon       = "CAMERA_STEREO", 
        name       = "         " + translate("Display As"),
        description= "",
        doc        = translate("Change how your particles are visualized in the viewport.")+"\n\n"+translate("Learn more in the Docs") +"_#LINK#_"+"https://sites.google.com/view/scatter5docs/manual/display",
        panel      = "SCATTER5_PT_settings",       
        context_pointer_set = [["ctxt",scat_ui.type_s_display]],
        )
    if is_open:
            if warnings(box): return 

            psy_active = emitter.scatter5.get_psy_active()

            if lock_check(box, psy_active, "s_display"): return 
            sync_info(box, psy_active, s_category="s_display")

            ########## ########## Display Method 

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=psy_active,
                prop_str="s_display_allow", 
                label=translate("Display As"), 
                icon="CAMERA_STEREO", 
                )
            if is_toggled:

                tocol.prop( psy_active, "s_display_method", text="")

                if (psy_active.s_display_method.startswith("placeholder")):

                    tocol.separator(factor=0.5)

                    if (psy_active.s_display_method=="placeholder"):

                        col = tocol.column()
                        col.separator(factor=0.1)
                        col.prop( psy_active, "s_display_placeholder_type", text="")

                    else:

                        col = tocol.column()
                        col.separator(factor=0.1)
                        col.prop( psy_active, "s_display_custom_placeholder_ptr",text="")

                    col.separator(factor=0.1)
                    
                    vec = col.column()
                    vec.scale_y = 0.9
                    vec.prop( psy_active, "s_display_placeholder_scale")

                elif (psy_active.s_display_method=="point"):

                    tocol.separator(factor=0.7)

                    col = tocol.column()
                    col.prop( psy_active, "s_display_point_radius")

                #Show Instances Close to Camera

                tocol.separator(factor=0.5)

                tocol2, is_toggled2 = templates.bool_toggle(tocol, 
                    prop_api=psy_active,
                    prop_str="s_display_camdist_allow", 
                    label=translate("Reveal Near Camera"), 
                    icon="DRIVER_DISTANCE", 
                    enabled=bpy.context.scene.camera is not None,
                    left_space=False,
                    panel_close=False,
                    )
                if is_toggled2:

                    tocol2.prop(psy_active, "s_display_camdist_distance")

                #Viewport Method 
                
                tocol.separator(factor=0.8)

                prop = tocol.column(align=True)
                prop.label(text=translate("Feature Visibility")+":",)
                prop.prop(psy_active,"s_display_viewport_method",text="")

            templates.sub_spacing(box)
    return 


# def draw_batch_set_display(self,layout):
    
#     addon_prefs, scat_scene, scat_ui, scat_win, emitter = get_props()

#     box, is_open = templates.sub_panel(self, layout, 
#         prop_str   = "display_sub2", 
#         icon       = "CONSOLE", 
#         name       = translate("Display Operation"),
#         description= "",
#         doc        = translate("Change how your objects are visualized in the viewport. Objects display are only visible when there is no particle-display methods active. You can also choose ")+"\n\n"+translate("Learn more in the Docs") +"_#LINK#_"+"https://sites.google.com/view/scatter5docs/manual/display#h.ry0930wrbuxd",
#         )
#     if is_open:
#             if warnings(box): return 

#             psy_active = emitter.scatter5.get_psy_active()
#             psys = emitter.scatter5.particle_systems

#             row  = box.row()
#             row1 = row.row() ; row1.scale_x = 0.17
#             row2 = row.row()
#             row3 = row.row() ; row3.scale_x = 0.17
#             col = row2.column()

#             txt = col.row()
#             txt.label(text=translate("Viewport Shading")+":")
#             sub = col.row(align=True)
#             sub.enabled = bool(len(psys))
#             condition = (bpy.context.space_data.shading.type == 'SOLID') and (bpy.context.space_data.shading.color_type == 'OBJECT')
#             op = sub.operator("scatter5.set_solid_and_object_color",text=translate("Show Systems Colors"), icon="COLOR",)
#             op.mode = "restore" if condition else "set"
            
#             col.separator()

#             txt = col.row()
#             txt.label(text=translate("Instance Display")+":")
#             op = col.column(align=True)
#             op.operator("scatter5.instances_batch_set_display",icon="CUBE", text=translate("Bounds Display")).display_type = "BOUNDS"
#             op.operator("scatter5.instances_batch_set_display",icon="SHADING_SOLID", text=translate("Solid Display")).display_type = "SOLID"

#             # if is_addon_enabled("Lodify"):

#             #     col.separator()

#             #     txt = col.row()
#             #     txt.label(text=translate("Enable/Disable Lodify")+":")
#             #     op = col.column(align=True)
#             #     op.operator("scatter5.instances_batch_set_display",icon="MESH_ICOSPHERE", text=translate("Enable Lodify")).display_type = "LODIFY_ENABLE"
#             #     op.operator("scatter5.instances_batch_set_display",icon="PANEL_CLOSE", text=translate("Disable Lodify")).display_type = "LODIFY_DISABLE"
            
#             templates.sub_spacing(box)
#     return 


#    .oooooo.   oooo
#   d8P'  `Y8b  `888
#  888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
#  888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
#  888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
#  `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#   `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


class SCATTER5_PT_tweaking_object(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_tweaking_object"
    bl_label       = translate("Tweaking")
    bl_category    = "Scatter5"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_context     = "objectmode"
    bl_order       = 1

    @classmethod
    def poll(cls, context, ):
        return context.scene.scatter5.emitter is not None
        
    def draw_header_preset(self, _context):
        templates.main_panel_header(self)

    def draw(self, context):
        layout = self.layout
        draw_tweaking_panel(self,layout)

class SCATTER5_PT_tweaking_weight(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_tweaking_weight"
    bl_label       = translate("Tweaking")
    bl_category    = "Scatter5"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_context     = "weightpaint"
    bl_order       = 1

    @classmethod
    def poll(cls, context, ):
        return context.scene.scatter5.emitter is not None

    def draw_header_preset(self, _context):
        templates.main_panel_header(self)

    def draw(self, context):
        layout = self.layout
        draw_tweaking_panel(self,layout)

class SCATTER5_PT_tweaking_vcolor(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_tweaking_vcolor"
    bl_label       = translate("Tweaking")
    bl_category    = "Scatter5"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_context     = "vertexpaint"
    bl_order       = 1

    @classmethod
    def poll(cls, context, ):
        return context.scene.scatter5.emitter is not None

    def draw_header_preset(self, _context):
        templates.main_panel_header(self)

    def draw(self, context):
        layout = self.layout
        draw_tweaking_panel(self,layout)

class SCATTER5_PT_tweaking_imgpaint(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_tweaking_imgpaint"
    bl_label       = translate("Tweaking")
    bl_category    = "Scatter5"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_context     = "imagepaint"
    bl_order       = 1

    @classmethod
    def poll(cls, context, ):
        return context.scene.scatter5.emitter is not None

    def draw_header_preset(self, _context):
        templates.main_panel_header(self)

    def draw(self, context):
        layout = self.layout
        draw_tweaking_panel(self,layout)



classes = [
    
    SCATTER5_MT_selection_menu, #Particle Action Menu
    
    SCATTER5_UL_list_particles, #Particle List GUI
    SCATTER5_UL_list_instances,

    SCATTER5_PT_tweaking_object,
    SCATTER5_PT_tweaking_weight,
    SCATTER5_PT_tweaking_vcolor,
    SCATTER5_PT_tweaking_imgpaint,

    ]



#if __name__ == "__main__":
#    register()