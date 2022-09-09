
#####################################################################################################
#
# ooooo     ooo ooooo      ooo        ooooo
# `888'     `8' `888'      `88.       .888'
#  888       8   888        888b     d'888   .ooooo.  ooo. .oo.   oooo  oooo   .oooo.o
#  888       8   888        8 Y88. .P  888  d88' `88b `888P"Y88b  `888  `888  d88(  "8
#  888       8   888        8  `888'   888  888ooo888  888   888   888   888  `"Y88b.
#  `88.    .8'   888        8    Y     888  888    .o  888   888   888   888  o.  )88b
#    `YbodP'    o888o      o8o        o888o `Y8bod8P' o888o o888o  `V88V"V8P' 8""888P'
#
#####################################################################################################

#Note that i'm not consistent, and some menus are not here 


import bpy, os, json

from .. resources.icons import cust_icon
from .. resources.translate import translate
from .. resources import directories

from .. utils.extra_utils import is_rendered_view

from .. scattering.copy_paste import is_buffer_filled
from .. scattering.synchronize import is_synchronized

from . import ui_creation
from . import templates




# ooooo   ooooo                           .o8                          ooo        ooooo
# `888'   `888'                          "888                          `88.       .888'
#  888     888   .ooooo.   .oooo.    .oooo888   .ooooo.  oooo d8b       888b     d'888   .ooooo.  ooo. .oo.   oooo  oooo   .oooo.o
#  888ooooo888  d88' `88b `P  )88b  d88' `888  d88' `88b `888""8P       8 Y88. .P  888  d88' `88b `888P"Y88b  `888  `888  d88(  "8
#  888     888  888ooo888  .oP"888  888   888  888ooo888  888           8  `888'   888  888ooo888  888   888   888   888  `"Y88b.
#  888     888  888    .o d8(  888  888   888  888    .o  888           8    Y     888  888    .o  888   888   888   888  o.  )88b
# o888o   o888o `Y8bod8P' `Y888""8o `Y8bod88P" `Y8bod8P' d888b         o8o        o888o `Y8bod8P' o888o o888o  `V88V"V8P' 8""888P'



class SCATTER5_PT_scatter_selected(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_scatter_selected"
    bl_label       = ""
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}

    @classmethod
    def poll(cls, context):
        return (bpy.context.scene.scatter5.emitter!=None)

    def draw(self, context):

        addon_prefs = bpy.context.preferences.addons["Scatter5"].preferences
        scat_scene = bpy.context.scene.scatter5
        preset_exists = os.path.exists(scat_scene.preset_path)
        layout = self.layout

        #Preset Name

        #layout.label(text=translate("Not Preset Chosen Yet") if not preset_exists else os.path.basename(scat_scene.preset_path),)

        #Emitter

        # layout.separator(factor=0.33)

        # col = layout.column(align=True)
        # txt = col.row()
        # txt.label(text=translate("Emitter")+" :")

        # op = col.operator("scatter5.exec_line",text=translate("Refresh m² Estimation"),icon="SURFACE_NSURFACE",)
        # op.api = "bpy.context.scene.scatter5.emitter.scatter5.get_estimated_square_area()"
        # op.description = translate("Recalculate Emitter Surface m² Estimation")
        
        #Preset Path 

        layout.separator(factor=0.15)

        col = layout.column(align=True)
        txt = col.row()
        txt.label(text=translate("Preset")+" :")
        
        path = col.row(align=True)
        path.alert = not preset_exists
        path.prop(scat_scene,"preset_path",text="")
        path.operator("scatter5.open_directory",text="",icon="FILE_TEXT").folder = os.path.join(directories.lib_presets, bpy.context.window_manager.scatter5_preset_gallery +".preset")
        col.separator()
        col.operator("scatter5.save_preset_to_disk_dialog", text=translate("Selection to Preset(s)"),icon="FILE_NEW")

        #Create New 

        col = layout.column(align=True)
        txt = col.row()
        txt.label(text=translate("Thumbnail")+" :")

        op = col.operator("scatter5.generate_thumbnail",text=translate("ReGenerate Thumbnail"),icon="RESTRICT_RENDER_OFF")
        op.json_path = os.path.join(directories.lib_presets, bpy.context.window_manager.scatter5_preset_gallery +".preset")
        op.render_output = os.path.join(directories.lib_presets, bpy.context.window_manager.scatter5_preset_gallery +".jpg")

        #Library 

        col = layout.column(align=True)
        txt = col.row()
        txt.label(text=translate("Gallery")+" :")

        col.operator("scatter5.reload_preset_gallery",text=translate("Reload Preset Gallery"), icon="FILE_REFRESH")
        col.separator()
        col.operator("scatter5.open_directory",text=translate("Open Preset Library"), icon="FOLDER_REDIRECT").folder = directories.lib_presets

        #Options 

        col.separator(factor=0.25)

        col = layout.column(align=True)
        col.label(text=translate("Automatic Name")+" :",)
        templates.bool_toggle(col, 
              prop_api=scat_scene,
              prop_str="preset_find_color", 
              label=translate("Use Material Color"), 
              icon="MATERIAL", 
              left_space=False,
              panel_close=False,
              )
        
        col.separator()

        templates.bool_toggle(col, 
              prop_api=scat_scene,
              prop_str="preset_find_name", 
              label=translate("Use Instance Name"), 
              icon="SMALL_CAPS", 
              left_space=False,
              panel_close=False,
              )

        return None


class SCATTER5_PT_settings(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_settings"
    bl_label       = ""
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}

    @classmethod
    def poll(cls, context):
        return (bpy.context.scene.scatter5.emitter!=None)

    def draw(self, context):

        layout     = self.layout
        scat_scene = bpy.context.scene.scatter5
        emitter    = scat_scene.emitter
        psys       = emitter.scatter5.particle_systems
        psy_active = emitter.scatter5.get_psy_active()

        #Msg if no system 
        if (len(psys)==0):
            layout.active = False
            layout.label(text=translate("No System(s) Created"))
            return 

        #Get arg from 'context_pointer_set' method -> transfering whole API created for the occation, as we can't transfer simple string arg.. see gui_props.py
        s_category = context.ctxt.value
        title      = context.ctxt.label

        supported = ["s_distribution","s_rot","s_scale","s_pattern","s_abiotic","s_proximity","s_ecosystem","s_push","s_wind","s_visibility","s_instances","s_display",]
        if s_category in supported:

            #Category Copy/Paste

            col = layout.column(align=True)
            txt = col.row()
            txt.label(text=translate("Settings Copy/Paste")+" :")
            row = col.row(align=True)
            #
            cc = row.row(align=True)
            op = cc.operator("scatter5.copy_paste",text=translate("Copy"),icon="COPYDOWN")
            op.copy = True
            op.s_category = s_category
            #
            cc = row.row(align=True)
            cc.enabled = is_buffer_filled(s_category)
            op = cc.operator("scatter5.copy_paste",text=translate("Paste"),icon="PASTEDOWN")
            op.paste = True
            op.s_category = s_category

            #Category Reset/Preset 

            col = layout.column(align=True)
            txt = col.row()
            txt.label(text=translate("Settings Reset/ Use Preset ")+" :")
            row = col.row(align=True)
            #
            op = row.operator("scatter5.reset_settings_to_default",text=translate("Reset"), icon="LOOP_BACK")
            op.s_category = s_category
            op.method = "active"
            #
            pre = row.column(align=True)
            icon_gallery = row.enum_item_icon(bpy.context.window_manager,"scatter5_preset_gallery", bpy.context.window_manager.scatter5_preset_gallery)
            ope = pre.row(align=True)
            if s_category not in ["s_visibility","s_display"]: #Presets do not supports visibility/display settings 
                ope.operator_context = "EXEC_DEFAULT"
                op = ope.operator("scatter5.apply_preset_dialog",text=translate("Preset"),icon_value=icon_gallery,)
                op.method = "active"
                op.single_category = s_category
            else: 
                ope.enabled = False
                op = ope.operator("scatter5.dummy",text=translate("No Support"),icon_value=icon_gallery,)
                op.description = translate("Paste the Active Preset Settings to the Selected-System(s)")

            #Category Lock/Unlock

            col = layout.column(align=True)
            txt = col.row()
            txt.label(text=translate("Settings Lock/Unlock")+" :")
            row = col.row(align=True)
            row.prop(psy_active, f"{s_category}_locked", text=translate("Unlock"), icon="UNLOCKED", invert_checkbox=True)
            row.prop(psy_active, f"{s_category}_locked", text=translate("Lock"), icon="LOCKED")

            #Category Synchronization

            if is_synchronized(psy_active,s_category):
                
                col = layout.column(align=True)
                txt = col.row()
                txt.label(text=translate("Settings are in Synch")+" :")

                sync_channels = scat_scene.sync_channels
                lbl = layout.row()
                lbl.alert = True
                ch = [ch for ch in sync_channels if ch.psy_settings_in_channel(emitter, psy_active.name, s_category,)][0]
                lbl.prop(ch,s_category,text=translate("Remove Synchronization"),icon_value=cust_icon("W_ARROW_SYNC"))

            #Special, Some categories got some extra items 

            if (s_category=="s_distribution") and (psy_active.s_distribution_method!="manual_all"):

                #Export to manual 

                col = layout.column(align=True)
                txt = col.row()
                txt.label(text=translate("Manual Edition")+" :")

                ope = col.row()
                ope.operator_context = "INVOKE_DEFAULT"
                ope.operator("scatter5.manual_convert_dialog",text=translate("Convert to Manual Distribution"), icon="BRUSHES_ALL")

            elif (s_category=="s_visibility"):

                #Camera Update Method

                col = layout.column(align=True)
                txt = col.row()
                txt.label(text=translate("Camera Clip update")+" :")

                row = col.row(align=True)
                row.prop(scat_scene,"factory_cam_update_method", text="")
                if (scat_scene.factory_cam_update_method=="toggle"):
                    row.operator("scatter5.exec_line", text="", icon="FILE_REFRESH").api = f"psy = bpy.data.objects['{emitter.name}'].scatter5.particle_systems['{psy_active.name}'] ; psy.s_visibility_camdist_allow = not psy.s_visibility_camdist_allow ; psy.s_visibility_camdist_allow = not psy.s_visibility_camdist_allow"

            elif (s_category=="s_display"):

                #Visualize

                col = layout.column(align=True)
                txt = col.row()
                txt.label(text=translate("Display Color")+" :")

                ope = col.row()
                condition = (bpy.context.space_data.shading.type == 'SOLID') and (bpy.context.space_data.shading.color_type == 'OBJECT')
                op = ope.operator("scatter5.set_solid_and_object_color",text=translate("Show Systems Colors"), icon="COLOR", depress=condition)
                op.mode = "restore" if condition else "set"

        layout.separator(factor=0.3)

        return None


class SCATTER5_PT_mask_header(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_mask_header"
    bl_label       = ""
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}


    @classmethod
    def poll(cls, context):
        return (bpy.context.scene.scatter5.emitter!=None)

    def draw(self, context):
        layout = self.layout

        scat_scene = bpy.context.scene.scatter5
        emitter    = scat_scene.emitter

        col = layout.column()
        txt = col.row()
        txt.label(text=translate("Recalculate Mask-Data :"))
        prp = col.row()
        prp.operator("scatter5.refresh_every_masks",text=translate("Recalculate All Masks"),icon="FILE_REFRESH")
        
        # col = layout.column()
        # txt = col.row()
        # txt.label(text=translate("Export masks :"))
        # prp = col.row()
        # prp.operator("scatter5.bake_vertex_groups",text=translate("Bake Mask(s)"))
        
        return None


class SCATTER5_PT_graph_subpanel(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_graph_subpanel"
    bl_label       = ""
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}


    @classmethod
    def poll(cls, context):
        return (bpy.context.scene.scatter5.emitter!=None)

    def draw(self, context):
        layout = self.layout
    
        dialog = context.dialog

        from .. graph_remap import preset_buffer

        layout.label(text=translate("Move Widget Value")+" :")
        layout.prop(dialog,"op_move",text=translate("step"))

        layout.label(text=translate("Resize Widget Value")+" :")
        layout.prop(dialog,"op_size",text=translate("factor"))

        layout.label(text=translate("Graph Buffer")+" :")

        #Copy

        col = layout.column(align=True)
        op = col.operator("scatter5.graph_copy_preset", text=translate("Copy"),icon="COPYDOWN")
        op.source_api=dialog.source_api
        op.mapping_api=dialog.mapping_api
        op.copy= True
        op.paste= False
        
        #Paste 

        ope = col.row(align=True)
        ope.enabled = preset_buffer is not None
        op = ope.operator("scatter5.graph_copy_preset", text=translate("Paste"),icon="PASTEDOWN")
        op.source_api=dialog.source_api
        op.mapping_api=dialog.mapping_api
        op.copy= False
        op.paste= True

        return None


# ooo        ooooo
# `88.       .888'
#  888b     d'888   .ooooo.  ooo. .oo.   oooo  oooo
#  8 Y88. .P  888  d88' `88b `888P"Y88b  `888  `888
#  8  `888'   888  888ooo888  888   888   888   888
#  8    Y     888  888    .o  888   888   888   888
# o8o        o888o `Y8bod8P' o888o o888o  `V88V"V8P'



class SCATTER5_MT_manager_header_menu_scatter(bpy.types.Menu):

    bl_idname = "SCATTER5_MT_manager_header_menu_scatter"
    bl_label  = ""

    def draw(self, context):

        layout=self.layout
        layout.enabled = False
        layout.operator("wm.url_open",text=translate("Documentation"),icon="URL").url = "https://www.scatterforblender.com/"
        layout.operator("wm.url_open",text=translate("Need help?"),icon="URL").url = "https://www.blendermarket.com/creators/bd3d-store"
        layout.operator("wm.url_open",text=translate("Blender Artist Forum"),icon="URL").url = "https://blenderartists.org/t/scatter4/1177672"
        layout.operator("wm.url_open",text=translate("Leave a nice review :) ?"),icon="SOLO_ON").url = "https://www.blendermarket.com/products/scatter/ratings"

        return None


class SCATTER5_MT_manager_header_menu_biome_interface(bpy.types.Menu):

    bl_idname = "SCATTER5_MT_manager_header_menu_biome_interface"
    bl_label  = ""

    def draw(self, context):

        layout=self.layout
        addon_prefs = bpy.context.preferences.addons["Scatter5"].preferences
        scat_scene = bpy.context.scene.scatter5

        layout.prop(scat_scene,"library_adaptive_columns") 
        layout.prop(scat_scene,"library_item_size",icon="ARROW_LEFTRIGHT") 
        #layout.prop(scat_scene,"library_typo_limit",icon="OUTLINER_DATA_FONT")  #seem that this is no longer required
        if not scat_scene.library_adaptive_columns:
            layout.prop(scat_scene,"library_columns") 

        return None 


class SCATTER5_MT_manager_header_menu_open(bpy.types.Menu):

    bl_idname = "SCATTER5_MT_manager_header_menu_open"
    bl_label  = ""

    def draw(self, context):

        layout=self.layout
        addon_prefs = bpy.context.preferences.addons["Scatter5"].preferences


        if addon_prefs.manager_category == "library":

            row = layout.row()
            row.operator_context = "INVOKE_DEFAULT"
            row.operator("scatter5.save_biome_to_disk_dialog", text=translate("Create New Biome"),icon="FILE_NEW")

            layout.separator()

            layout.operator("scatter5.reload_biome_library", text=translate("Reload Biomes"), icon="FILE_REFRESH")
            layout.operator("scatter5.open_directory", text=translate("Open Library"), icon="FOLDER_REDIRECT").folder = directories.lib_library
            layout.operator("scatter5.install_package", text=translate("Install a .Scatpack"), icon="NEWFOLDER")
                        
        elif addon_prefs.manager_category == "market":

            layout.operator("wm.url_open",text=translate("Add your Packs here? Contact me"),icon="URL").url="https://www.blendermarket.com/creators/bd3d-store"

            layout.separator()

            layout.operator("scatter5.manual_fetch_from_git",text=translate("Refresh Online Previews"), icon="FILE_REFRESH")
            layout.operator("scatter5.open_directory",text=translate("Open Library"), icon="FOLDER_REDIRECT").folder = directories.lib_library
            layout.operator("scatter5.install_package", text=translate("Install a .Scatpack"), icon="NEWFOLDER")

        return None 


class SCATTER5_MT_manager_header_menu_biome_option(bpy.types.Menu):

    bl_idname = "SCATTER5_MT_manager_header_menu_biome_option"
    bl_label  = ""

    def draw(self, context):

        layout=self.layout
        scat_scene = bpy.context.scene.scatter5

        layout.prop(scat_scene,"s_visibility_hide_viewport",text=translate("Hide Particle-System on Creation"),)
        layout.prop(scat_scene,"s_display_biome_placeholder",text=translate("Use Biome Placeholder on Creation"),)
        layout.prop(scat_scene,"s_display_bounding_box",text=translate("Display as Bounding-box on Creation"),)
        layout.prop(scat_scene,"opt_import_method",text="",)

        layout.separator()
        
        txt=layout.row()
        txt.active =False
        txt.label(text=translate("More options available in the creation panel."),icon="INFO",)
    
        return None 


class SCATTER5_MT_biome_ctrl_click(bpy.types.Menu):

    bl_idname = "SCATTER5_MT_biome_ctrl_click"
    bl_label  = ""

    def __init__(self):

        #get context element 
        self.path_arg = bpy.context.lib_element.name

        return None 

    def draw(self, context):

        layout = self.layout

        layout.menu("SCATTER5_MT_sub_biome_ctrl_click_single_layer",text=translate("Scatter Single Layer"),icon="DOCUMENTS")

        ope = layout.column()
        ope.operator_context = "INVOKE_DEFAULT"
        op = ope.operator("scatter5.rename_biome", text=translate("Rename this .biome"), icon="FONT_DATA")
        op.path = self.path_arg
        op.old_name = bpy.context.window_manager.scatter5.library[self.path_arg].user_name

        ope = layout.row()
        ope.operator_context = "INVOKE_DEFAULT"
        op = ope.operator("scatter5.generate_thumbnail",text=translate("Thumbnail Generator"),icon="RESTRICT_RENDER_OFF")
        op.json_path = self.path_arg
        op.render_output = self.path_arg.replace(".biome",".jpg")

        layout.menu("SCATTER5_MT_sub_biome_ctrl_click_open",text=translate("Open Files"),icon="FILE_FOLDER")  
        
        # layout.separator()
        
        # txt = layout.row()
        # txt.active = False
        # txt.label(text=translate("Hover to see description"),icon="QUESTION")
        
        return None 


class SCATTER5_MT_sub_biome_ctrl_click_single_layer(bpy.types.Menu):

    bl_idname = "SCATTER5_MT_sub_biome_ctrl_click_single_layer"
    bl_label  = ""

    def __init__(self):

        #get context element 
        self.path_arg = bpy.context.lib_element.name

        #get layer 
        with open(self.path_arg) as f:
            d = json.load(f)
        self.layers = []
        for k,v in d.items():
            if k.isdigit():
                self.layers.append(v["name"])

        return None 

    def draw(self, context):

        layout = self.layout

        for i,l in enumerate(self.layers):
            op = layout.operator("scatter5.load_biome", text=l, icon="FILE_BLANK" )
            op.emitter_name = "" #Auto
            op.json_path = self.path_arg
            op.single_layer = i+1

        return None 

class SCATTER5_MT_sub_biome_ctrl_click_open(bpy.types.Menu):

    bl_idname = "SCATTER5_MT_sub_biome_ctrl_click_open"
    bl_label  = ""

    def __init__(self):

        #get context element 
        self.path_arg = bpy.context.lib_element.name

        #get layer 
        with open(self.path_arg) as f:
            d = json.load(f)
        self.layers = []
        i=0
        for k,v in d.items():
            if k.isdigit():
                self.layers.append( (v["name"],self.path_arg.replace(".biome",f".layer{i:02}.preset")) )
                i+=1

        return None 

    def draw(self, context):

        layout = self.layout

        op = layout.operator("scatter5.open_directory", text=translate("Open Parent Directory"), icon="FOLDER_REDIRECT")
        op.folder = os.path.dirname(self.path_arg)

        op = layout.operator("scatter5.open_directory", text=f'{translate("Open")} "{os.path.basename(self.path_arg)}"', icon="FILE_TEXT")
        op.folder = self.path_arg

        layout.separator()

        for n,p in self.layers:
            op = layout.operator("scatter5.open_directory", text=f'{translate("Open")} "{n}" .preset', icon="FILE_TEXT" )
            op.folder = p

        return None 


#   ooooooooo.
#   `888   `Y88.
#    888   .d88'  .ooooo.   .oooooooo
#    888ooo88P'  d88' `88b 888' `88b
#    888`88b.    888ooo888 888   888
#    888  `88b.  888    .o `88bod8P'
#   o888o  o888o `Y8bod8P' `8oooooo.
#                          d"     YD
#                          "Y88888P'


classes = [

    SCATTER5_PT_scatter_selected,
    SCATTER5_PT_settings, #copy_paste
    
    SCATTER5_PT_mask_header,
    SCATTER5_PT_graph_subpanel,

    SCATTER5_MT_manager_header_menu_scatter,
    SCATTER5_MT_manager_header_menu_biome_interface,
    SCATTER5_MT_manager_header_menu_open,
    SCATTER5_MT_manager_header_menu_biome_option,

    SCATTER5_MT_biome_ctrl_click,
    SCATTER5_MT_sub_biome_ctrl_click_single_layer,
    SCATTER5_MT_sub_biome_ctrl_click_open,

    ]



#if __name__ == "__main__":
#    register()