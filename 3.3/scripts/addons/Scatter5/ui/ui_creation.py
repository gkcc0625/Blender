
#####################################################################################################
#
# ooooo     ooo ooooo        .oooooo.                                    .    o8o
# `888'     `8' `888'       d8P'  `Y8b                                 .o8    `"'
#  888       8   888       888          oooo d8b  .ooooo.   .oooo.   .o888oo oooo   .ooooo.  ooo. .oo.
#  888       8   888       888          `888""8P d88' `88b `P  )88b    888   `888  d88' `88b `888P"Y88b
#  888       8   888       888           888     888ooo888  .oP"888    888    888  888   888  888   888
#  `88.    .8'   888       `88b    ooo   888     888    .o d8(  888    888 .  888  888   888  888   888
#    `YbodP'    o888o       `Y8bood8P'  d888b    `Y8bod8P' `Y888""8o   "888" o888o `Y8bod8P' o888o o888o
#
#####################################################################################################


import bpy, os

#from .. external import is_addon_enabled

from .. resources.icons import cust_icon
from .. resources.translate import translate
from .. resources import directories

from .. scattering.instances import find_compatible_instances
from .. scattering.emitter import is_ready_for_scattering

from .. utils.str_utils import word_wrap
from .. utils.vg_utils import is_vg_active

from . import templates


def get_props():
    """get useful props used in interface"""

    addon_prefs = bpy.context.preferences.addons["Scatter5"].preferences
    scat_scene  = bpy.context.scene.scatter5
    scat_ui     = bpy.context.scene.scatter5.ui
    scat_win    = bpy.context.window_manager.scatter5
    emitter     = scat_scene.emitter

    return (addon_prefs, scat_scene, scat_ui, scat_win, emitter)



# ooo        ooooo            o8o                   ooooooooo.                                   oooo
# `88.       .888'            `"'                   `888   `Y88.                                 `888
#  888b     d'888   .oooo.   oooo  ooo. .oo.         888   .d88'  .oooo.   ooo. .oo.    .ooooo.   888
#  8 Y88. .P  888  `P  )88b  `888  `888P"Y88b        888ooo88P'  `P  )88b  `888P"Y88b  d88' `88b  888
#  8  `888'   888   .oP"888   888   888   888        888          .oP"888   888   888  888ooo888  888
#  8    Y     888  d8(  888   888   888   888        888         d8(  888   888   888  888    .o  888
# o8o        o888o `Y888""8o o888o o888o o888o      o888o        `Y888""8o o888o o888o `Y8bod8P' o888o



def draw_creation_panel(self,layout):
    """draw main creation panel"""

    addon_prefs, scat_scene, scat_ui, scat_win, emitter = get_props()

    main = layout.column()
    main.enabled = scat_scene.ui_enabled

    #main scattering 

    is_open = templates.main_panel(self,main,
        prop_str = "scattering_main",
        icon = "W_SCATTER",
        name = translate("Scatter Preset"),
        )
    if is_open:
            draw_scattering(self,main)
            templates.main_spacing(main)

    #biomes

    is_open = templates.main_panel(self,main,
        prop_str = "biomes_main",
        icon = "ASSET_MANAGER",
        name = translate("Scatter Biome"),
        )
    if is_open:
            draw_biomes(self,main)
            templates.main_spacing(main)

    #options 

    is_open = templates.main_panel(self,main,
        prop_str = "options_main",
        icon = "SETTINGS",
        name = translate("Creation Settings"),
        )
    if is_open:
            draw_visibility(self,main)
            draw_display(self,main)
            draw_creation_actions(self,main)
            #draw_link_options(self,main)
            templates.main_spacing(main)
        
    layout.separator(factor=0.5)
    return


#  .oooooo..o                         .       .                       o8o
# d8P'    `Y8                       .o8     .o8                       `"'
# Y88bo.       .ooooo.   .oooo.   .o888oo .o888oo  .ooooo.  oooo d8b oooo  ooo. .oo.    .oooooooo
#  `"Y8888o.  d88' `"Y8 `P  )88b    888     888   d88' `88b `888""8P `888  `888P"Y88b  888' `88b
#      `"Y88b 888        .oP"888    888     888   888ooo888  888      888   888   888  888   888
# oo     .d8P 888   .o8 d8(  888    888 .   888 . 888    .o  888      888   888   888  `88bod8P'
# 8""88888P'  `Y8bod8P' `Y888""8o   "888"   "888" `Y8bod8P' d888b    o888o o888o o888o `8oooooo.
#                                                                                      d"     YD
#                                                                                      "Y88888P'


def find_preset_name(compatible_instances):
    """find particle system name depending on instances and options"""

    scat_scene = bpy.context.scene.scatter5

    #auto color? 
    if (not scat_scene.preset_find_name):
        return scat_scene.preset_name

    for o in compatible_instances:
        return o.name

    return translate("No Object Found")


def find_preset_color(compatible_instances):
    """find particle system color depending on instances and options"""

    scat_scene = bpy.context.scene.scatter5

    #auto color? 
    if (not scat_scene.preset_find_color):
        return  list(scat_scene.preset_color)[:3], None

    for o in compatible_instances:
        if len(o.material_slots):
            for slot in o.material_slots:
                if (slot.material is not None):
                    return list(slot.material.diffuse_color)[:3], slot.material
    return list(scat_scene.preset_color)[:3], None


def draw_scattering(self,layout):

    addon_prefs, scat_scene, scat_ui, scat_win, emitter = get_props()

    box, is_open = templates.sub_panel(self, layout, 
        prop_str   = "scattering_sub1", 
        panel      = "SCATTER5_PT_scatter_selected",
        icon       = "W_SCATTER", 
        name       = "        "+ translate("Scatter Preset"),
        description= "",
        doc        = translate("Here you will be able to change your distribution method and settings.\nNote that some methods, such as clump distribution will add new scale/rotation settings.\nNote that there's an operator to bring the procedurally generated points to manual distribution mode in the header")+"\n\n"+translate("Learn more in the Docs")+"_#LINK#_"+"https://sites.google.com/view/scatter5docs/manual/distribution?authuser=0",
        )

    if is_open:
            
            # layout spacing 

            def layout_spacing(layout):
                row = layout.row(align=True)

                left = row.column(align=True)
                left.scale_x = 0.8
                left.operator("scatter5.dummy",text="",icon="BLANK1", emboss=False,)
                center = row.column()
                right = row.column(align=True)
                right.scale_x = 0.8
                right.operator("scatter5.dummy",text="",icon="BLANK1", emboss=False,)

                return left, center, right

            left, area, right = layout_spacing(box)

            #instances found ? 

            if (scat_scene.add_psy_selection_method=="viewport"):
                  compatible_instances = list(find_compatible_instances(bpy.context.selected_objects))
            else: compatible_instances = []

            area.separator(factor=0.1)

            # preset thumbnail 
            
            left.scale_y = 2
            right.scale_y = 2
            
            left.operator("scatter5.preset_enum_skip",text="",icon="TRIA_LEFT", emboss=False).direction = "LEFT"
            area.template_icon_view(bpy.context.window_manager, "scatter5_preset_gallery", show_labels=False, scale=6.0, scale_popup=6.0)
            right.operator("scatter5.preset_enum_skip",text="",icon="TRIA_RIGHT", emboss=False).direction = "RIGHT"

            # preset color and name 

            area.separator(factor=0.7)

            under_area = area.column()
            #under_area.scale_y = 0.95

            under_props = under_area.row(align=True)
            
            # preset color

            if not (scat_scene.preset_find_color):
                clr = under_props.row(align=True) 
                clr.scale_x = 0.4
                clr.prop(scat_scene,"preset_color",text="")
            else: 
                clr = under_props.box()
                clr.label(text="",icon="MATERIAL")
                clr.scale_y = 0.5
                clr.scale_x = 1.1
                        
            # preset name 

            if (scat_scene.preset_find_name):

                found_name = "*AUTO*"                    
                txt_name = translate("*Asset Name*") if (scat_scene.add_psy_selection_method=="browser") else translate("*Object Name*")

                nambox = under_props.box()
                nambox.scale_y = 0.5
                nambox.label(text=txt_name)
            else:       
                found_name = scat_scene.preset_name         
                under_props.prop(scat_scene,"preset_name",text="")

            under_area.separator(factor=0.5)

            # Estimation, also see etimation function in add_psy

            estim = under_area.column()
            estim.active = False
            estim.scale_y = 0.75

            if (emitter.scatter5.estimated_square_area==-1):

                op = estim.operator("scatter5.exec_line",text=translate("Refresh Estimation"), icon="FILE_REFRESH", emboss=False,)
                op.api = "bpy.context.scene.scatter5.emitter.scatter5.get_estimated_square_area()"
                op.description = translate("Recalculate Emitter Surface m² Estimation")

            elif (scat_scene.estimated_preset_density_method==""):

                #ParticleNot Available
                estim.label(text=translate("Estimation Not Available"))
                
            elif ("random" in scat_scene.estimated_preset_density_method) or ("clumping" in scat_scene.estimated_preset_density_method):
                    
                is_random = ("random" in scat_scene.estimated_preset_density_method)

                #Method
                nfo = estim.row(); left = nfo.row() ; left.scale_x=1.0 ; left.alignment="LEFT" ; right = nfo.row() ; right.alignment="RIGHT" 
                left.label(text=translate("Distribution")+":")
                right.label(text=translate("Random") if is_random else translate("Clumping"),)

                #Surface
                estimated_square_area = emitter.scatter5.estimated_square_area
                if ("global" in scat_scene.estimated_preset_density_method):
                    estimated_square_area *= sum(emitter.scale)/len(emitter.scale)
                if estimated_square_area<1_000:
                      estimated_square_area = round(estimated_square_area,2)
                else: estimated_square_area = int(estimated_square_area)
                nfo = estim.row(); left = nfo.row() ; left.scale_x=1.0 ; left.alignment="LEFT" ; right = nfo.row() ; right.alignment="RIGHT" 
                left.label(text=translate("Emitter Surface")+":")
                right.label(text=f" {estimated_square_area:,} m²")

                #Density
                estimated_preset_density =round(scat_scene.estimated_preset_density,2)
                nfo = estim.row(); left = nfo.row() ; left.scale_x=1.0 ; left.alignment="LEFT" ; right = nfo.row() ; right.alignment="RIGHT" 
                left.label(text=translate("Preset Density")+":")
                right.label(text=f" {estimated_preset_density:,} P/m²")
            
                #Particle-Count
                estimated_preset_particle_count = int(estimated_square_area*estimated_preset_density)
                nfo = estim.row(); left = nfo.row() ; left.scale_x=1.0 ; left.alignment="LEFT" ; right = nfo.row() ; right.alignment="RIGHT" 
                right.alert = estimated_preset_particle_count>scat_scene.sec_emit_count
                left.label(text=translate("Estimated Count")+":")

                if (scat_scene.add_psy_allocation_method == "individual") and len(compatible_instances)!=0: 
                    estimated_preset_particle_count *= len(compatible_instances)
                right.label(text=f"{estimated_preset_particle_count:,} P")

            elif ("verts" in scat_scene.estimated_preset_density_method) or ("faces" in scat_scene.estimated_preset_density_method):

                is_perface = ("faces" in scat_scene.estimated_preset_density_method)
                poly_count = len(emitter.data.polygons) if is_perface else len(emitter.data.vertices)

                #Method
                nfo = estim.row(); left = nfo.row() ; left.scale_x=1.0 ; left.alignment="LEFT" ; right = nfo.row() ; right.alignment="RIGHT" 
                left.label(text=translate("Method")+":")
                right.label(text=translate("Per Face") if is_perface else translate("Per Vert"))

                #PolyCount 
                nfo = estim.row(); left = nfo.row() ; left.scale_x=1.0 ; left.alignment="LEFT" ; right = nfo.row() ; right.alignment="RIGHT" 
                left.label(text=translate("Polycount")+":")
                right.label(text=f"{poly_count:,} F" if is_perface else f"{poly_count:,} V")

                #Particle-Count
                nfo = estim.row(); left = nfo.row() ; left.scale_x=1.0 ; left.alignment="LEFT" ; right = nfo.row() ; right.alignment="RIGHT" 
                left.label(text=translate("Estimated Count")+":")

                if (scat_scene.add_psy_allocation_method == "individual") and len(compatible_instances)!=0: 
                    poly_count *= len(compatible_instances)
                right.label(text=f"{poly_count:,} P")

            elif ("manual_all" in scat_scene.estimated_preset_density_method):

                #Method
                nfo = estim.row(); left = nfo.row() ; left.scale_x=1.0 ; left.alignment="LEFT" ; right = nfo.row() ; right.alignment="RIGHT" 
                left.label(text=translate("Method")+":")
                right.label(text=translate("Manual"))

                #Particle-Count
                nfo = estim.row(); left = nfo.row() ; left.scale_x=1.0 ; left.alignment="LEFT" ; right = nfo.row() ; right.alignment="RIGHT" 
                left.label(text=translate("Estimated Count")+":")
                right.label(text=f"0 P")


            under_area.separator(factor=0.5)

            # Main Scattering Button 

            # scattering method

            area.prop(scat_scene, "add_psy_selection_method", text="",)
            area.separator(factor=0.6)
            #area.prop(scat_scene, "add_psy_allocation_method", text="",)

            operator_text = translate("Scatter Object(s)") if (scat_scene.add_psy_selection_method == "viewport") else translate("Scatter Asset(s)")

            if (scat_scene.add_psy_allocation_method == "group"):

                button= area.row(align=True)
                button.scale_y=1.25
                button.enabled = is_ready_for_scattering()

                op = button.operator("scatter5.add_psy_preset", text=operator_text,)
                op.psy_name = found_name
                op.emitter_name = emitter.name
                op.instance_names = "_!#!_".join( [o.name for o in bpy.context.selected_objects] )
                op.use_asset_browser = (scat_scene.add_psy_selection_method=="browser")
                op.json_path = scat_scene.preset_path
                op.psy_color = find_preset_color(compatible_instances)[0]
                op.from_biome = False
                op.pop_msg = True

            elif (scat_scene.add_psy_allocation_method == "individual"):

                button= area.row(align=True)
                button.scale_y=1.25
                button.enabled = is_ready_for_scattering()

                if (scat_scene.progress_context=="individual"):
                
                    button.prop(scat_scene,"progress_bar",text=scat_scene.progress_label,)

                else:
                    op = button.operator("scatter5.add_psy_individual", text=operator_text,)
                    op.emitter_name = emitter.name
                    op.instance_names = "_!#!_".join( [o.name for o in bpy.context.selected_objects] )
                    op.use_asset_browser = (scat_scene.add_psy_selection_method=="browser")
                    op.json_path = scat_scene.preset_path

            templates.sub_spacing(box)
    return 



# oooooooooo.   o8o
# `888'   `Y8b  `"'
#  888     888 oooo   .ooooo.  ooo. .oo.  .oo.    .ooooo.   .oooo.o
#  888oooo888' `888  d88' `88b `888P"Y88bP"Y88b  d88' `88b d88(  "8
#  888    `88b  888  888   888  888   888   888  888ooo888 `"Y88b.
#  888    .88P  888  888   888  888   888   888  888    .o o.  )88b
# o888bood8P'  o888o `Y8bod8P' o888o o888o o888o `Y8bod8P' 8""888P'



def draw_biomes(self,layout):
    
    addon_prefs, scat_scene, scat_ui, scat_win, emitter = get_props()

    box, is_open = templates.sub_panel(self, layout, 
        prop_str   = "biomes_sub1", 
        icon       = "ASSET_MANAGER", 
        name       = "        "+ translate("Scatter Biome"),
        description= "",
        doc        = translate("Here you will be able to open your biome library, click on an item from your library and Scatter will load the assets and scatter the encoded layers one by one.\nNote that you can directly display the biomes particles placeholder in the creation settings menu.\nNote that security features and creation settings can have an impact on creation.\nIf you don't see anything, make sure the show viewport icon is active.")+"\n\n"+translate("Learn more in the Docs") +"_#LINK#_"+"https://sites.google.com/view/scatter5docs/manual/scattering#h.uixz6f3f1k1u",
        )
    if is_open:

            row  = box.row()
            row1 = row.row() ; row1.scale_x = 0.17
            row2 = row.column()
            row3 = row.row() ; row3.scale_x = 0.17

            #biome manager
            button= row2.column(align=False)
            button.scale_y=1.2
            button.operator("scatter5.open_manager", text=translate("Open Library"),).manager_category = "library"

            #row2.separator()

            #marketplace
            #button= row2.column(align=False)
            #button.scale_y=1.2
            #button.operator("scatter5.open_manager", text=translate("Biome Available Online"),).manager_category = "market"

            templates.sub_spacing(box)

    return 


#   .oooooo.                  .    o8o
#  d8P'  `Y8b               .o8    `"'
# 888      888 oo.ooooo.  .o888oo oooo   .ooooo.  ooo. .oo.    .oooo.o
# 888      888  888' `88b   888   `888  d88' `88b `888P"Y88b  d88(  "8
# 888      888  888   888   888    888  888   888  888   888  `"Y88b.
# `88b    d88'  888   888   888 .  888  888   888  888   888  o.  )88b
#  `Y8bood8P'   888bod8P'   "888" o888o `Y8bod8P' o888o o888o 8""888P'
#               888
#              o888o


on_creation_link = "\n\n"+translate("Learn more in the Docs") +"_#LINK#_"+"https://sites.google.com/view/scatter5docs/manual/scattering#h.o3pfl8c6mklq"


def draw_creation_actions(self,layout):

    addon_prefs, scat_scene, scat_ui, scat_win, emitter = get_props()

    box, is_open = templates.sub_panel(self, layout,         
        prop_str   = "options_sub3", 
        icon       = "SHADERFX", 
        name       = translate("On Creation"), 
        description= "",
        doc        = translate("Below you are able to choose special actions taken upon creation, for example, directly prepare the Scattering/Biome to be used in manual mode, or directly start painting density in weight painting") + on_creation_link,          
        )
    if is_open:

            row = box.row()
            row_1 = row.row() ; row_1.scale_x = 0.01
            row_2 = row.column() 

            row_2.prop( scat_scene, "opt_import_method",text="",)
            row_2.separator()

            row_2.prop( scat_scene, "opt_mask_assign_method",text="",)
            row_2.separator(factor=0.2)

            if scat_scene.opt_mask_assign_method == "curve":

                row_2.prop( scat_scene, "opt_mask_curve_area_ptr", text="",)

            elif scat_scene.opt_mask_assign_method == "vg":

                slotcol = row_2.column(align=True)
                slotcol.prop_search(scat_scene, "opt_vg_assign_slot", emitter, "vertex_groups", text="")

            templates.sub_spacing(box)
    return 


def draw_visibility(self,layout):

    addon_prefs, scat_scene, scat_ui, scat_win, emitter = get_props()

    box, is_open = templates.sub_panel(self, layout,         
        prop_str   = "options_sub1", 
        icon       = "HIDE_OFF", 
        name       = translate("Visibility"), 
        description= "",
        doc        = translate("Options below will change your future particle-system visibility settings.") + on_creation_link,            
        )
    if is_open:

            #Hide on Creation 
            
            templates.bool_toggle(box, 
                prop_api=scat_scene,
                prop_str="s_visibility_hide_viewport", 
                label=translate("Hide Particle-System"), 
                icon="RESTRICT_VIEW_ON", 
                left_space=True,
                panel_close=False,
                )

            #Viewport % Reduction 

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=scat_scene,
                prop_str="s_visibility_view_allow", 
                label=translate("Viewport Density Reduction"), 
                icon="W_PERCENTAGE", 
                left_space=True,
                panel_close=False,
                )
            if is_toggled:
                tocol.prop(scat_scene,"s_visibility_view_percentage",)

            #Camera Optimization 

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=scat_scene,
                prop_str="s_visibility_cam_allow", 
                label=translate("Camera Optimization"), 
                icon="OUTLINER_OB_CAMERA", 
                enabled=bpy.context.scene.camera is not None,
                )
            if is_toggled:

                #Camera Frustrum 

                tocol2, is_toggled2 = templates.bool_toggle(tocol, 
                    prop_api=scat_scene,
                    prop_str="s_visibility_camclip_allow", 
                    label=translate("Frustrum Culling"), 
                    icon="CAMERA_DATA", 
                    enabled=bpy.context.scene.camera is not None,
                    left_space=False,
                    panel_close=False,
                    )
                
                #Camera Distance Culling 

                tocol.separator(factor=0.5)
                tocol2, is_toggled2 = templates.bool_toggle(tocol, 
                    prop_api=scat_scene,
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
                    prop.prop(scat_scene, "s_visibility_camdist_min")
                    prop.prop(scat_scene, "s_visibility_camdist_max")
            
            templates.sub_spacing(box)
    return 


def draw_display(self,layout):

    addon_prefs, scat_scene, scat_ui, scat_win, emitter = get_props()

    box, is_open = templates.sub_panel(self, layout,         
        prop_str   = "options_sub2", 
        icon       = "CAMERA_STEREO", 
        name       = translate("Display"), 
        description= "",
        doc        = translate("Options below will change your future particle-system display settings.\n you are also able to directly change your future object-instances display.") + on_creation_link,                      
        )
    if is_open:

            templates.bool_toggle(box, 
                prop_api=scat_scene,
                prop_str="s_display_biome_placeholder", 
                label=translate("Use Biome Placeholder"), 
                icon="MOD_CLOTH", 
                left_space=True,
                panel_close=False,
                )

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=scat_scene,
                prop_str="s_display_allow", 
                label=translate("Display As"), 
                icon="CAMERA_STEREO", 
                left_space=True,
                panel_close=False,
                )
            if is_toggled:

                tocol.prop( scat_scene, "s_display_method", text="")

                if scat_scene.s_display_method=="placeholder_custom":

                    col = tocol.column()
                    col.separator(factor=0.5)
                    col.prop( scat_scene, "s_display_custom_placeholder_ptr",text="")

                tocol.separator(factor=0.8)

                templates.bool_toggle(tocol, 
                    prop_api=scat_scene,
                    prop_str="s_display_camdist_allow", 
                    label=translate("Reveal Near Camera"), 
                    icon="DRIVER_DISTANCE", 
                    enabled=bpy.context.scene.camera is not None,
                    left_space=False,
                    panel_close=False,
                    )

            templates.bool_toggle(box, 
                prop_api=scat_scene,
                prop_str="s_display_bounding_box", 
                label=translate("Set Object Bounding-Box"), 
                icon="CUBE", 
                left_space=True,
                panel_close=False,
                )

            # if is_addon_enabled("Lodify"):
            #     templates.bool_toggle(box, 
            #         prop_api=scat_scene,
            #         prop_str="s_display_enable_lodify", 
            #         label=translate("Set Object LOD Active"), 
            #         icon="MESH_ICOSPHERE", 
            #         left_space=True,
            #         panel_close=False,
            #         )


            templates.sub_spacing(box)
    return 


# def draw_link_options(self,layout):

#     addon_prefs, scat_scene, scat_ui, scat_win, emitter = get_props()

#     box, is_open = templates.sub_panel(self, layout,         
#         prop_str   = "options_sub4", 
#         icon       = "IMPORT", 
#         name       = translate("Instance Import"), 
#         description= "",
#         doc        = translate("Choose if you'd like to link or append the imported objects.") + on_creation_link,                   
#         )
#     if is_open:

#             row = box.row()
#             row_1 = row.row() ; row_1.scale_x = 0.01
#             row_2 = row.column() 

#             row_2.prop( scat_scene, "opt_import_method",text="",)

#             # templates.bool_toggle(box, 
#             #     prop_api=scat_scene,
#             #     prop_str="opt_sync_settings", 
#             #     label=translate("Synchronize settings particle-name exists"), 
#             #     icon="W_ARROW_SYNC", 
#             #     left_space=True,
#             #     panel_close=False,
#             #     )

#             templates.sub_spacing(box)
#     return 


#    .oooooo.   oooo
#   d8P'  `Y8b  `888
#  888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
#  888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
#  888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
#  `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#   `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'



class SCATTER5_PT_scattering_object(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_scattering_object"
    bl_label       = translate("Creation")
    bl_category    = "Scatter5"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_context     = "objectmode"
    bl_order       = 0

    @classmethod
    def poll(cls, context, ):
        return context.scene.scatter5.emitter is not None

    def draw_header_preset(self, _context):
        templates.main_panel_header(self)

    def draw(self, context):
        layout = self.layout
        draw_creation_panel(self,layout)

class SCATTER5_PT_scattering_weight(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_scattering_weight"
    bl_label       = translate("Creation")
    bl_category    = "Scatter5"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_context     = "weightpaint"
    bl_order       = 0

    @classmethod
    def poll(cls, context, ):
        return context.scene.scatter5.emitter is not None

    def draw_header_preset(self, _context):
        templates.main_panel_header(self)

    def draw(self, context):
        layout = self.layout
        draw_creation_panel(self,layout)

class SCATTER5_PT_scattering_vcolor(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_scattering_vcolor"
    bl_label       = translate("Creation")
    bl_category    = "Scatter5"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_context     = "vertexpaint"
    bl_order       = 0

    @classmethod
    def poll(cls, context, ):
        return context.scene.scatter5.emitter is not None

    def draw_header_preset(self, _context):
        templates.main_panel_header(self)

    def draw(self, context):
        layout = self.layout
        draw_creation_panel(self,layout)

class SCATTER5_PT_scattering_imgpaint(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_scattering_imgpaint"
    bl_label       = translate("Creation")
    bl_category    = "Scatter5"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_context     = "imagepaint"
    bl_order       = 0

    @classmethod
    def poll(cls, context, ):
        return context.scene.scatter5.emitter is not None

    def draw_header_preset(self, _context):
        templates.main_panel_header(self)

    def draw(self, context):
        layout = self.layout
        draw_creation_panel(self,layout)


classes = [

    SCATTER5_PT_scattering_object,
    SCATTER5_PT_scattering_weight,
    SCATTER5_PT_scattering_vcolor,
    SCATTER5_PT_scattering_imgpaint,


    ]



#if __name__ == "__main__":
#    register()

