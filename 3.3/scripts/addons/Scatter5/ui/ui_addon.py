

#####################################################################################################
#
# ooooo     ooo ooooo            .o.             .o8        .o8
# `888'     `8' `888'           .888.           "888       "888
#  888       8   888           .8"888.      .oooo888   .oooo888   .ooooo.  ooo. .oo.
#  888       8   888          .8' `888.    d88' `888  d88' `888  d88' `88b `888P"Y88b
#  888       8   888         .88ooo8888.   888   888  888   888  888   888  888   888
#  `88.    .8'   888        .8'     `888.  888   888  888   888  888   888  888   888
#    `YbodP'    o888o      o88o     o8888o `Y8bod88P" `Y8bod88P" `Y8bod8P' o888o o888o
#
#####################################################################################################


import bpy, os, platform 

from .. resources.icons import cust_icon
from .. resources.translate import translate
from .. resources import directories

from .. utils.str_utils import word_wrap

from . import templates


# ooo        ooooo            o8o                         .o.             .o8        .o8
# `88.       .888'            `"'                        .888.           "888       "888
#  888b     d'888   .oooo.   oooo  ooo. .oo.            .8"888.      .oooo888   .oooo888   .ooooo.  ooo. .oo.
#  8 Y88. .P  888  `P  )88b  `888  `888P"Y88b          .8' `888.    d88' `888  d88' `888  d88' `88b `888P"Y88b
#  8  `888'   888   .oP"888   888   888   888         .88ooo8888.   888   888  888   888  888   888  888   888
#  8    Y     888  d8(  888   888   888   888        .8'     `888.  888   888  888   888  888   888  888   888
# o8o        o888o `Y888""8o o888o o888o o888o      o88o     o8888o `Y8bod88P" `Y8bod88P" `Y8bod8P' o888o o888o


#addon class stored in properties...

def draw_addon(self,layout):

    addon_prefs = bpy.context.preferences.addons["Scatter5"].preferences

    row = layout.row()
    r1 = row.separator()
    r2 = row.column()
    r3 = row.separator()
    
    #r2.label(text="Thanks for Supporting our work !")

    #agree= r2.row().box()
    #agree.operator("scatter5.dummy_op",text='I agreed to Scatter licence agreement',icon='CHECKBOX_HLT',emboss=False)
    #agree.scale_y = 1.4

    #r2.separator()
    
    r2.label(text="Enter Scatter5 Biome & Preferences Manager.")

    enter = r2.row()
    enter.alert=True
    enter.scale_y = 1.4
    enter.operator("scatter5.impost_addonprefs",text=translate("Enter Manager"),icon_value=cust_icon('W_SCATTER')).state = True

    r2.separator()

    # r2.label(text="Install Lodify, the free standalone LOD/Proxy addon.")

    # from .. external import is_addon_enabled, is_addon_installed
    # if is_addon_installed("Lodify"):
    #     if is_addon_enabled("Lodify"):

    #         ltext="Lodify is enabled"
    #         licon='CHECKBOX_HLT'
    #         api ="print('')" #"bpy.ops.preferences.addon_disable(module='Lodify')"
    #         emboss=False
    #     else: 
    #         ltext="Lodify is not enabled yet"
    #         licon='CHECKBOX_DEHLT'
    #         api ="bpy.ops.preferences.addon_refresh() ; bpy.ops.preferences.addon_enable(module='Lodify')"
    #         emboss=False
    # else:
    #     ltext="Lodify is not installed yet"
    #     licon='URL'
    #     api ="bpy.ops.wm.url_open(url='https://github.com/DB3D/Lodify')"
    #     emboss=False 

    # lodif = r2.box().row()
    # lodif.operator("scatter5.exec_line",text=ltext,icon=licon,emboss=emboss).api = api
    # lodif.scale_y = 1.25

    r2.separator(factor=2)

    return



# ooooo   ooooo  o8o   o8o                     oooo         o8o
# `888'   `888'  `"'   `"'                     `888         `"'
#  888     888  oooo  oooo  .oooo.    .ooooo.   888  oooo  oooo  ooo. .oo.    .oooooooo
#  888ooooo888  `888  `888 `P  )88b  d88' `"Y8  888 .8P'   `888  `888P"Y88b  888' `88b
#  888     888   888   888  .oP"888  888        888888.     888   888   888  888   888
#  888     888   888   888 d8(  888  888   .o8  888 `88b.   888   888   888  `88bod8P'
# o888o   o888o o888o  888 `Y888""8o `Y8bod8P' o888o o888o o888o o888o o888o `8oooooo.
#                      888                                                   d"     YD
#                  .o. 88P                                                   "Y88888P'
#                  `Y888P


Status = False
AddonPanel_OriginalDraw = None
AddonNavBar_OriginalDraw = None
AddonHeader_OriginalDraw = None


def panel_hijack():
    """register impostors"""

    global Status
    if Status==True:
        return None

    #show header just in case user hided it (show/hide header on 'PREFERENCE' areas)

    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if(area.type == 'PREFERENCES'):
                for space in area.spaces:
                    if(space.type == 'PREFERENCES'):
                        space.show_region_header = True
                        #space.show_region_footer = boolean #Meh seem that there's no way to show navigation bar or footer automatically.. i hope user won't be dummy

    #Save Original Class Drawing Function in global , and replace their function with one of my own 

    global AddonPanel_OriginalDraw
    AddonPanel_OriginalDraw = bpy.types.USERPREF_PT_addons.draw
    bpy.types.USERPREF_PT_addons.draw = addonpanel_overridedraw
        
    global AddonNavBar_OriginalDraw
    AddonNavBar_OriginalDraw = bpy.types.USERPREF_PT_navigation_bar.draw
    bpy.types.USERPREF_PT_navigation_bar.draw = addonnavbar_overridedraw
    
    global AddonHeader_OriginalDraw
    AddonHeader_OriginalDraw = bpy.types.USERPREF_HT_header.draw
    bpy.types.USERPREF_HT_header.draw = addonheader_overridedraw
    
    Status=True
    return None

def panel_restore():
    """restore and find original drawing classes"""

    global Status
    if Status==False:
        return None

    #restore original drawing code 
    
    global AddonPanel_OriginalDraw
    bpy.types.USERPREF_PT_addons.draw = AddonPanel_OriginalDraw
    AddonPanel_OriginalDraw = None 

    global AddonNavBar_OriginalDraw
    bpy.types.USERPREF_PT_navigation_bar.draw = AddonNavBar_OriginalDraw
    AddonNavBar_OriginalDraw = None 

    global AddonHeader_OriginalDraw
    bpy.types.USERPREF_HT_header.draw = AddonHeader_OriginalDraw
    AddonHeader_OriginalDraw = None 

    #Trigger Redraw, otherwise some area will be stuck until user put cursor 

    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if(area.type == 'PREFERENCES'):
                area.tag_redraw()
                
    Status=False
    return None



#Register Impostor/Original Operator
class SCATTER5_OT_impost_addonprefs(bpy.types.Operator):
    bl_idname      = "scatter5.impost_addonprefs"
    bl_label       = ""
    bl_description = translate("replace/restore native blender preference ui by custom scatter manager ui")

    state : bpy.props.BoolProperty()

    def execute(self, context):

        if self.state == True:
               panel_hijack()
        else:  panel_restore()

        return{'FINISHED'}


# ooooo                                                     .                           ooooooooo.                                   oooo
# `888'                                                   .o8                           `888   `Y88.                                 `888
#  888  ooo. .oo.  .oo.   oo.ooooo.   .ooooo.   .oooo.o .o888oo  .ooooo.  oooo d8b       888   .d88'  .oooo.   ooo. .oo.    .ooooo.   888   .oooo.o
#  888  `888P"Y88bP"Y88b   888' `88b d88' `88b d88(  "8   888   d88' `88b `888""8P       888ooo88P'  `P  )88b  `888P"Y88b  d88' `88b  888  d88(  "8
#  888   888   888   888   888   888 888   888 `"Y88b.    888   888   888  888           888          .oP"888   888   888  888ooo888  888  `"Y88b.
#  888   888   888   888   888   888 888   888 o.  )88b   888 . 888   888  888           888         d8(  888   888   888  888    .o  888  o.  )88b
# o888o o888o o888o o888o  888bod8P' `Y8bod8P' 8""888P'   "888" `Y8bod8P' d888b         o888o        `Y888""8o o888o o888o `Y8bod8P' o888o 8""888P'
#                          888
#                         o888o


#Impostor Main 

def addonpanel_overridedraw(self,context):

    layout = self.layout
    addon_prefs = bpy.context.preferences.addons["Scatter5"].preferences

    #Prefs
    if (addon_prefs.manager_category == "prefs"):
        draw_add_prefs(self, layout)

    elif (addon_prefs.manager_category == "library"):
        from . biome_library import draw_library_grid
        draw_library_grid(self, layout)

    elif (addon_prefs.manager_category == "market"):
        from . biome_library import draw_online_grid
        draw_online_grid(self, layout)

    elif (addon_prefs.manager_category == "stats"):
        draw_stats(self, layout)

    return 

    
#Impostor Header

# @staticmethod #override save preference double drawing
# def draw_buttons(layout, context):
#     pass
            
def addonheader_overridedraw(self, context):

    layout = self.layout
    addon_prefs = bpy.context.preferences.addons["Scatter5"].preferences

    row = layout.row()
    row.template_header()
    row.menu("SCATTER5_MT_manager_header_menu_scatter", text="Scatter5",icon_value=cust_icon('W_SCATTER'))

    if addon_prefs.manager_category == "library":
        row.menu("SCATTER5_MT_manager_header_menu_open", text=translate("File"),)
        row.menu("SCATTER5_MT_manager_header_menu_biome_option", text=translate("Options"),)
        row.menu("SCATTER5_MT_manager_header_menu_biome_interface", text=translate("Interface"),)

    elif addon_prefs.manager_category == "market":
        row.menu("SCATTER5_MT_manager_header_menu_open", text=translate("File"),)
        row.menu("SCATTER5_MT_manager_header_menu_biome_interface", text=translate("Interface"),)

    elif addon_prefs.manager_category == "prefs":
        row.menu("USERPREF_MT_save_load", text=translate("Preferences"),)

    layout.separator_spacer()
    
    exit = layout.column()
    exit.alert = True
    exit.operator("scatter5.impost_addonprefs",text=translate("Exit"),icon='PANEL_CLOSE').state = False

    return 

#Impostor T Panel

def addonnavbar_overridedraw(self, context):

    layout      = self.layout
    addon_prefs = bpy.context.preferences.addons["Scatter5"].preferences
    scat_scene  = bpy.context.scene.scatter5
    scat_win    = bpy.context.window_manager.scatter5

    #Close if user is dummy 

    if not context.space_data.show_region_header:
        exit = layout.column()
        exit.alert = True
        exit.operator("scatter5.impost_addonprefs",text=translate("Exit"),icon='PANEL_CLOSE').state = False
        exit.scale_y = 1.8
        return 

    #Draw main categories 

    enum = layout.column()
    enum.scale_y = 1.3
    enum.prop(addon_prefs,"manager_category",expand=True)

    layout.separator(factor=5)

    #Per category draw

    if (addon_prefs.manager_category == "prefs"):
        pass

    elif (addon_prefs.manager_category == "library"):

        #layout.label(text=translate("Search")+" :")

        row = layout.row(align=True)
        row.scale_y = 1.2
        row.prop(scat_scene,"library_search",icon="VIEWZOOM",text="") 

        layout.separator(factor=0.33)

        #layout.label(text=translate("Navigate")+" :")

        wm = bpy.context.window_manager
        navigate = layout.column()
        navigate.scale_y = 1
        navigate.template_list("SCATTER5_UL_folder_navigation", "", wm.scatter5, "folder_navigation", wm.scatter5, "folder_navigation_idx",rows=20,)

        lbl = navigate.column()
        lbl.scale_y = 0.8
        lbl.active = False
        lbl.separator()
        elements_count = 0 
        if len(scat_win.folder_navigation): elements_count = scat_win.folder_navigation[scat_win.folder_navigation_idx].elements_count
        lbl.label(text=f'{elements_count} {translate("Elements in Folder")}')
        
        #lbl.separator(factor=2)
        #lbl.label(text=translate("Need more?"))
        #lbl.operator("scatter5.exec_line",text=translate("Check out what's available"),emboss=False).api = 'bpy.context.preferences.addons["Scatter5"].preferences.manager_category = "market" ; bpy.context.area.tag_redraw()'

    elif (addon_prefs.manager_category == "stats"):

        #lbl = layout.row()
        #lbl.active = False
        #lbl.label(text=translate("Estimate:"))

        #ope = layout.column()
        #ope.scale_y = 1
        #ope.operator("scatter5.estimate",text=translate("View Particle-Count"), emboss=True, icon="RESTRICT_VIEW_OFF").mode ="viewcount"
        #ope.operator("scatter5.estimate",text=translate("Render Particle-Count"), emboss=True, icon="RESTRICT_RENDER_OFF").mode ="rendercount"
        #ope.operator("scatter5.estimate",text=translate("Surface Area"), emboss=True, icon="SURFACE_NSURFACE").mode ="surface"
            
        layout.separator()

        lbl = layout.row()
        lbl.active = False
        lbl.label(text=translate("Operations:"))

        ope = layout.column()
        ope.scale_y = 1
        ope.operator("scatter5.exec_line",text=translate("Hide All"),icon="RESTRICT_VIEW_ON",).api= f"one_liner = [exec('p.hide_viewport=True') for o in bpy.context.scene.objects if len(o.scatter5.particle_systems) for p in o.scatter5.particle_systems ]"
        ope.operator("scatter5.exec_line",text=translate("Remove Selected"),icon="TRASH",).api= f"bpy.ops.ed.undo_push(message='Remove Selected', ) ;one_liner = [ bpy.ops.scatter5.remove_system(undo_push=False, emitter_name=o.name, method='selection') for o in bpy.context.scene.objects if len(o.scatter5.particle_systems)]"
        #layout.operator("scatter5.exec_line",text=translate("Select All"),).api= f"one_liner = [exec('p.sel=True') for o in bpy.context.scene.objects if len(o.scatter5.particle_systems) for p in o.scatter5.particle_systems ]"
        #layout.operator("scatter5.exec_line",text=translate("Hide All Selected"),).api= f"one_liner = [exec('p.hide_viewport=True') for o in bpy.context.scene.objects if len(o.scatter5.particle_systems) for p in o.scatter5.particle_systems if p.sel]"


    return 


# oooooooooo.                                        ooooo     ooo                              ooooooooo.                       .o88o.
# `888'   `Y8b                                       `888'     `8'                              `888   `Y88.                     888 `"
#  888      888 oooo d8b  .oooo.   oooo oooo    ooo   888       8   .oooo.o  .ooooo.  oooo d8b   888   .d88' oooo d8b  .ooooo.  o888oo   .oooo.o
#  888      888 `888""8P `P  )88b   `88. `88.  .8'    888       8  d88(  "8 d88' `88b `888""8P   888ooo88P'  `888""8P d88' `88b  888    d88(  "8
#  888      888  888      .oP"888    `88..]88..8'     888       8  `"Y88b.  888ooo888  888       888          888     888ooo888  888    `"Y88b.
#  888     d88'  888     d8(  888     `888'`888'      `88.    .8'  o.  )88b 888    .o  888       888          888     888    .o  888    o.  )88b
# o888bood8P'   d888b    `Y888""8o     `8'  `8'         `YbodP'    8""888P' `Y8bod8P' d888b     o888o        d888b    `Y8bod8P' o888o   8""888P'



def draw_add_prefs(self, layout):

    addon_prefs = bpy.context.preferences.addons["Scatter5"].preferences

    #some users have this way too big...
    rrr = layout.row()
    rrr.alignment="LEFT"
    flow = rrr.column()
    flow.alignment = "LEFT"

    box, is_open = templates.sub_panel(self, flow, 
        prop_str   = "add_pack", 
        icon       = "NEWFOLDER", 
        name       = translate("Install a ScatPack"),
        description= translate("Install External '.scatpack' File from here"),
        )
    if is_open:

            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)

            rwoo = col.row()
            rwoo.operator("scatter5.install_package", text=translate("Install a Scatter Package"), icon="NEWFOLDER")
            scatpack = rwoo.row()
            scatpack.active = False
            scatpack.operator("wm.url_open", text=translate("Find ScatPack Online"),icon_value=cust_icon("W_SUPERMARKET")).url = ""

            col.separator()

            txt = col.column(align=True)
            word_wrap(layout=txt, max_char=75, string=translate("ScatPacks are premade libraries of biomes, presets & assets ready to be used. You can make your own '.scatpack' by renaming a compressed .zip extension. The content of the zip should respect the '_presets_'/'_biomes_' folder hierarchy. Be careful to only zip what is yours when creating your zip file!"),)

            templates.sub_spacing(box)

    box, is_open = templates.sub_panel(self, flow, 
        prop_str   = "add_fetch", 
        icon       = "URL", 
        name       = translate("Marketplace Online Fetch"),
        description= translate("Change values here if you don't want scatter to fetch from the net"),
        )
    if is_open:

            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)

            templates.bool_toggle(col, 
                prop_api=addon_prefs,
                prop_str="fetch_automatic_allow", 
                label=translate("Automatically Fetch Biome Previews from Web."), 
                icon="FILE_REFRESH", 
                left_space=False,
                panel_close=False,
                )
            
            col.separator()
            row = col.row()
            #
            subr = row.row()
            subr.active = addon_prefs.fetch_automatic_allow
            subr.prop(addon_prefs, "fetch_automatic_daycount", text=translate("Fetch every n Day"),)
            #
            subr = row.row()
            subr.operator("scatter5.manual_fetch_from_git", text=translate("Fetch Now"), icon="FILE_REFRESH")

            templates.sub_spacing(box)
            
    # box, is_open = templates.sub_panel(self, flow, 
    #     prop_str   = "add_lang", 
    #     icon       = "WORLD_DATA", 
    #     name       = translate("Languages"),
    #     description= translate("Choose your Language"),
    #     doc        = "I still need to write the docs, this plugin is currently in WIP and you are not using the final version ",
    #     )
    # if is_open: 

    #         box.label(text="TODO create .excel sheet, separate it per column into single column file, create enum from single column, make enum then made translate() fct work on restart")

    #         txt = box.column()
    #         txt.scale_y = 0.8
    #         txt.label(text="Supported Languages:")
    #         txt.label(text="        -English")
    #         txt.label(text="        -Spanish")
    #         txt.label(text="        -French")
    #         txt.label(text="        -Japanese")
    #         txt.label(text="        -Chinese (Simplified)")

    #         templates.sub_spacing(box)

    box, is_open = templates.sub_panel(self, flow, 
        prop_str   = "add_path", 
        icon       = "FILEBROWSER", 
        name       = translate("Library Path"),
        description= translate("Choose your Scatter library path, where you library and preset are contained"),
        )
    if is_open:

            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)
                
            is_library = os.path.exists(addon_prefs.library_path)
            is_biomes  = os.path.exists(os.path.join(addon_prefs.library_path,"_biomes_"))
            is_presets = os.path.exists(os.path.join(addon_prefs.library_path,"_presets_"))
            is_bitmaps = os.path.exists(os.path.join(addon_prefs.library_path,"_bitmaps_"))

            colc = col.column(align=True)
            colc.label(text=translate("Library Location")+" :")
            pa = colc.row(align=True)
            pa.alert = not is_library
            pa.prop(addon_prefs,"library_path",text="")

            if False in [is_library, is_biomes, is_presets,]:
                colc.separator(factor=0.7)

                warn = colc.column(align=True)
                warn.scale_y = 0.9
                warn.alert = True
                warn.label(text=translate("There's problem(s) with the location you have chosen"),icon="ERROR")
                
                if not is_library:
                    warn.label(text=" "*10 + translate("-The chosen path does not exists"))
                if not is_biomes:
                    warn.label(text=" "*10 + translate("-'_biomes_' Directory not Found"))
                if not is_presets:
                    warn.label(text=" "*10 + translate("-'_presets_' Directory not Found"))
                if not is_bitmaps:
                    warn.label(text=" "*10 + translate("-'_bitmaps_' Directory not Found"))
                warn.label(text=translate("Scatter will use the default library location instead"),icon="BLANK1")

            if all([ is_library, is_biomes, is_presets, is_bitmaps]) and (directories.lib_library!=addon_prefs.library_path):
                colc.separator(factor=0.7)

                warn = colc.column(align=True)
                warn.scale_y = 0.85
                warn.label(text=translate("Chosen Library is Valid, Please save your addonprefs and restart blender."),icon="CHECKMARK")

            col.separator()

            row = col.row()
            col1 = row.column()
            col1.operator("scatter5.reload_biome_library", text=translate("Reload Biomes"), icon="FILE_REFRESH")
            col1.operator("scatter5.reload_preset_gallery", text=translate("Reload Presets"), icon="FILE_REFRESH")
            col1.operator("scatter5.dummy", text=translate("Reload Images"), icon="FILE_REFRESH")

            col2 = row.column()
            col2.operator("scatter5.open_directory", text=translate("Open Library"),icon="FOLDER_REDIRECT").folder = directories.lib_library
            col2.operator("scatter5.open_directory", text=translate("Open Default Library"),icon="FOLDER_REDIRECT").folder = directories.lib_default
            col2.operator("scatter5.open_directory", text=translate("Open Blender Addons"),icon="FOLDER_REDIRECT").folder = directories.blender_addons                    
            
            templates.sub_spacing(box)

    box, is_open = templates.sub_panel(self, flow, 
        prop_str   = "add_work", 
        icon       = "W_SCATTER", 
        name       = translate("Workflow"),
        description= translate("Tweak your workflow settings here"),
        )
    if is_open:

            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)

            emitmethod = col.column(align=True)
            emitmethod.label(text=translate("Emitter Switch Method:"))
            emit_prop = emitmethod.column() 
            emit_prop.scale_y = 1.0
            emit_prop.prop(addon_prefs,"emitter_method",expand=True,)

            templates.sub_spacing(box)

    box, is_open = templates.sub_panel(self, flow, 
        prop_str   = "add_shortcut", 
        icon       = "EVENT_TAB", 
        name       = translate("Shortcuts"),
        description= translate("Tweak your shortcuts settings here"),
        )
    if is_open:

            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)

            col.label(text=translate("Manual Mode Shortcuts:"),)
            
            # ---------------------------------------------------------
            
            '''
            def preferences():
                return bpy.context.preferences.addons["Scatter5"].preferences.manual_key_config
            
            def prop_name(cls, prop, colon=False, ):
                for p in cls.bl_rna.properties:
                    if(p.identifier == prop):
                        if(colon):
                            return "{}:".format(p.name)
                        return p.name
                return ''
            
            def dupli(cfg, ):
                ls = []
                vs = []
                for i, n in enumerate(cfg.__annotations__):
                    if(n in ('skip', 'gesture_key_alt', 'gesture_key_alt_oskey', 'gesture_key_alt_shift', )):
                        continue
                    ls.append(n)
                    vs.append(getattr(cfg, n))
                ds = []
                for i, n in enumerate(ls):
                    v = vs[i]
                    if(vs.count(v) > 1):
                        ds.append(n)
                ds = set(ds)
                return ds
            
            l = col
            cfg = preferences()
            c = l.column()
            c.scale_y = 0.8
            c.use_property_split = True
            
            ds = dupli(cfg, )
            
            def label(e, t, ):
                r = e.row()
                r.label(text=t, )
                r.enabled = False
            
            def line(e, n, ):
                r = e.row()
                # s = r.split(factor=0.666, )
                # s.label(text=prop_name(cfg, n, True, ))
                # s = s.split()
                if(getattr(cfg, n) == ''):
                    # s.alert = True
                    r.alert = True
                if(n in ds):
                    # s.alert = True
                    r.alert = True
                # s.prop(cfg, n, text='', )
                r.prop(cfg, n)
            
            label(c, "Brushes:", )
            
            for i, p in enumerate(cfg.__annotations__):
                if(p.startswith('gesture_')):
                    continue
                if(p == 'skip'):
                    continue
                line(c, p, )
            
            c.separator()
            
            label(c, "Brush Gestures:", )
            line(c, 'gesture_key', )

            c.separator()
            label(c, "Gesture Invoke Alternate Modifiers")
            
            line(c, 'gesture_key_alt_oskey', )
            line(c, 'gesture_key_alt_shift', )
            '''
            
            def preferences():
                return bpy.context.preferences.addons["Scatter5"].preferences.manual_key_config
            
            def dupli():
                cfg = preferences()
                ls = cfg.items
                ds = []
                ns = []
                for i, l in enumerate(ls):
                    d = {}
                    for a in l.__annotations__:
                        if(a in {'name', 'label', 'utility', 'ascii', 'unicode', }):
                            continue
                        d[a] = getattr(l, a)
                    ds.append(d)
                    ns.append(getattr(l, 'name'))
                r = []
                
                # for i in ds:
                #     print(i)
                # print()
                
                for i, d in enumerate(ds):
                    if(ds.count(d) > 1):
                        r.append(ns[i])
                return r
            
            ds = dupli()
            cfg = preferences()
            ls = cfg.items
            
            l = col.column()
            l.scale_y = 0.8
            #r = l.row()
            #r.label(text="Tools:")
            #r.enabled = False
            for i, o in enumerate(ls):
                if(o.name.startswith('_gesture')):
                    continue
                c = l.column()
                r = c.row()
                s = r.split(factor=0.5, )
                s.alignment = 'RIGHT'
                s.label(text='{}:'.format(o.label))
                s = s.split()
                if(o.name in ds):
                    s.alert = True
                if(o.type == ''):
                    s.alert = True
                if(o.flag):
                    sr = s.row()
                    sr.operator('scatter5.manual_key_config_set_key', text='Press a key', depress=True, ).name = o.name
                    sr.operator('scatter5.manual_key_config_reset_key', text='', icon='X', emboss=False).name = o.name
                else:
                    sr = s.row()
                    sr.operator('scatter5.manual_key_config_set_key', text=o.char, ).name = o.name
                    sr.operator('scatter5.manual_key_config_reset_key', text='', icon='X', emboss=False).name = o.name
                
            col.separator(factor=1)

            l = col.column()
            l.scale_y = 0.8
            #r = l.row()
            #r.label(text="Tool Gestures:")
            #r.enabled = False
            for i, o in enumerate(ls):
                if(not o.name.startswith('_gesture')):
                    continue
                alt = False
                if('alternate' in o.name):
                    alt = True
                
                c = l.column()
                r = c.row()
                s = r.split(factor=0.5, )
                s.alignment = 'RIGHT'
                s.label(text='{}:'.format(o.label))
                s = s.split()
                if(o.name in ds):
                    s.alert = True
                if(o.type == ''):
                    s.alert = True
                if(o.flag):
                    sr = s.row()
                    sr.operator('scatter5.manual_key_config_set_key', text='Press a key', depress=True, ).name = o.name
                    sr.operator('scatter5.manual_key_config_reset_key', text='', icon='X', emboss=False).name = o.name
                else:
                    sr = s.row()
                    sr.operator('scatter5.manual_key_config_set_key', text=o.char, ).name = o.name
                    sr.operator('scatter5.manual_key_config_reset_key', text='', icon='X', emboss=False).name = o.name
                
                if(alt):
                    r = c.row()
                    s = r.split(factor=0.5, )
                    s.label(text="")
                    s = s.split()
                    rr = s.row()
                    rr.prop(o, 'oskey', text='Ctrl/Cmd', )
                    rr.prop(o, 'shift', text='Shift', )
            
            # ---------------------------------------------------------
            
            templates.sub_spacing(box)

    box, is_open = templates.sub_panel(self, flow, 
        prop_str   = "add_gui", 
        icon       = "COLOR", 
        name       = translate("Interface"),
        description= translate("Change Your interface Settings Here"),
        )
    if is_open:

            row = box.row()
            row.separator(factor=0.3)
            row.prop(addon_prefs,"ui_selection_y", text=translate("Selection Area: Items Height"))
            row.separator(factor=0.3)

            templates.bool_toggle(box, 
                prop_api=addon_prefs,
                prop_str="ui_use_dark_box", 
                label=translate("Sub-Panel: Use Dark Box Header"), 
                icon="ALIGN_MIDDLE", 
                left_space=True,
                panel_close=False,
                )

            templates.bool_toggle(box, 
                prop_api=addon_prefs,
                prop_str="ui_use_arrow", 
                label=translate("Main-Panel: Use Arrows Instead of Icons"), 
                icon="DOWNARROW_HLT", 
                left_space=True,
                panel_close=False,
                )

            templates.bool_toggle(box, 
                prop_api=addon_prefs,
                prop_str="ui_use_active", 
                label=translate("Main-Panel: Highlight When Open"), 
                icon="CLIPUV_HLT", 
                left_space=True,
                panel_close=False,
                )

            row = box.row()
            row.separator(factor=0.3)
            row.prop(addon_prefs,"ui_scale_y", text=translate("Main-Panel: Spacing Between Panels"))
            row.separator(factor=0.3)

            row = box.row()
            row.separator(factor=0.3)
            row.prop(addon_prefs,"ui_main_when_open", text=translate("Main-Panel: Spacing When Open"))
            row.separator(factor=0.3)

            templates.bool_toggle(box, 
                prop_api=addon_prefs,
                prop_str="ui_bool_use_standard", 
                label=translate("Toggles: Use Native Toggles"), 
                icon="CHECKBOX_HLT", 
                left_space=True,
                panel_close=False,
                )

            templates.bool_toggle(box, 
                prop_api=addon_prefs,
                prop_str="ui_bool_use_panelclose", 
                label=translate("Toggles: Use Cross When Toggle turned Off"), 
                icon="CANCEL", 
                left_space=True,
                panel_close=False,
                enabled=not addon_prefs.ui_bool_use_standard
                )

            row = box.row()
            row.separator(factor=0.3)
            row.prop(addon_prefs,"ui_word_wrap_max_char_factor", text=translate("Word Wrap: Max Character per Lines Factor"))
            row.separator(factor=0.3)

            row = box.row()
            row.separator(factor=0.3)
            row.prop(addon_prefs,"ui_word_wrap_y", text=translate("Word Wrap: Text Y Scale"))
            row.separator(factor=0.3)

            templates.sub_spacing(box)

    if platform.system() == 'Windows':

        box, is_open = templates.sub_panel(self, flow, 
            prop_str   = "add_win", 
            icon       = "WINDOW", 
            name       = translate("Manager Window Size"),
            description= translate("Change the size of the window when calling the manager from the Biome subpanel"),
            )
        if is_open:

                row = box.row()
                row1 = row.separator()
                row2 = row.column()

                proprow = row2.column()
                proprow.prop(addon_prefs,"win_pop_size",)
                
                row2.separator(factor=0.3)
                
                proprow = row2.column()
                proprow.prop(addon_prefs,"win_pop_location", )

                templates.sub_spacing(box)

    box, is_open = templates.sub_panel(self, flow, 
        prop_str   = "add_dev", 
        icon       = "CONSOLE", 
        name       = translate("Debugging"),
        description= translate("Settings for developpers"),
        )
    if is_open:

            templates.bool_toggle(box, 
                prop_api=addon_prefs,
                prop_str="debug", 
                label=translate("Console prints."), 
                icon="CONSOLE", 
                left_space=True,
                panel_close=False,
                )

            d = box.row()
            d.active = addon_prefs.debug
            templates.bool_toggle(d, 
                prop_api=addon_prefs,
                prop_str="debug_depsgraph", 
                label=translate("Depsgraph console prints."), 
                icon="CONSOLE", 
                left_space=True,
                panel_close=False,
                )

            templates.sub_spacing(box)
    
    for i in range(10):
        layout.separator_spacer()
    return


# oooooooooo.                                             .oooooo..o     .                 .    o8o               .    o8o
# `888'   `Y8b                                           d8P'    `Y8   .o8               .o8    `"'             .o8    `"'
#  888      888 oooo d8b  .oooo.   oooo oooo    ooo      Y88bo.      .o888oo  .oooo.   .o888oo oooo   .oooo.o .o888oo oooo   .ooooo.   .oooo.o
#  888      888 `888""8P `P  )88b   `88. `88.  .8'        `"Y8888o.    888   `P  )88b    888   `888  d88(  "8   888   `888  d88' `"Y8 d88(  "8
#  888      888  888      .oP"888    `88..]88..8'             `"Y88b   888    .oP"888    888    888  `"Y88b.    888    888  888       `"Y88b.
#  888     d88'  888     d8(  888     `888'`888'         oo     .d8P   888 . d8(  888    888 .  888  o.  )88b   888 .  888  888   .o8 o.  )88b
# o888bood8P'   d888b    `Y888""8o     `8'  `8'          8""88888P'    "888" `Y888""8o   "888" o888o 8""888P'   "888" o888o `Y8bod8P' 8""888P'



def draw_stats(self, layout):

    col = layout.column()
    col.scale_y = 0.85

    scat_scene = bpy.context.scene.scatter5
    emitters = [o for o in bpy.context.scene.objects if len(o.scatter5.particle_systems)] 
    emitter = scat_scene.emitter

    plen = 0

    #-> Need an operator that calculate all particle-count & emitter surfaces

    for e in emitters:

        erow = col.box().row()
        erow.active= e==emitter
        erow.scale_y = 0.8

        name = erow.row(align=True)
        name.alignment = "LEFT"
        op = name.operator("scatter5.exec_line",text=e.name, icon_value=cust_icon("W_EMITTER"), emboss=False, depress=False,)
        if bpy.context.mode =="OBJECT":
              op.api = f"e = bpy.data.objects['{e.name}'] ; bpy.context.scene.scatter5.emitter = e ; bpy.ops.object.select_all(action='DESELECT') ; e.select_set(True) ; bpy.context.view_layer.objects.active = e"
        else: op.api = ""

        col.separator(factor=1) 
        
        totparticle=-1
        for i,p in enumerate(e.scatter5.particle_systems):

            prow = col.row(align=True)
            
            namcol = prow.row(align=True)
            namcol.alignment = "LEFT"
            #
            color = namcol.row(align=True)
            color.scale_x = 0.3
            color.prop(p,"s_color",text="")
            #
            name = namcol.row(align=True)
            name.alignment ="LEFT"
            op = name.operator("scatter5.exec_line",
                text=p.name,
                emboss=True,
                depress=p.active,
                )
            op.description = translate("Click on this operator to set this particle system as active, you can hold SHIFT or ALT to isolate the particle system view")
            op.api = f"bpy.data.objects['{e.name}'].scatter5.particle_systems_idx = {i}"
            #
            #namcol.separator()
            
            #prow.separator_spacer()

            # if (p.estimated_particlecount!=-1):
            #     if totparticle==-1:
            #         totparticle+=1 
            #     totparticle+=p.estimated_particlecount

            #     estim = prow.row()
            #     estim.alignment="RIGHT"
            #     estim.active = p.active
            #     estim.label(text=f"{int(p.estimated_particlecount):,} P")

            sub = prow.row(align=True)

            subb = sub.row(align=True)
            #subb.active = p.active
            subb.prop(p,"sel", 
                text="", 
                emboss=True, 
                icon="RESTRICT_SELECT_OFF"if p.sel else "RESTRICT_SELECT_ON",
                )
            subb.prop(p, "hide_viewport", 
                text="", 
                icon="RESTRICT_VIEW_ON" if p.hide_viewport else "RESTRICT_VIEW_OFF", 
                invert_checkbox=True,
                emboss=True,
                )
            subb.prop(p, "hide_render", 
                text="", 
                icon="RESTRICT_RENDER_ON" if p.hide_render else "RESTRICT_RENDER_OFF", 
                invert_checkbox=True,
                emboss=True,
                ) 
            subb.prop(p,"lock",
                text="",
                icon="LOCKED" if p.is_all_locked() else "UNLOCKED",
                invert_checkbox= p.is_all_locked(),
                emboss=True,
                )

            sub.separator()

            subb = sub.row(align=True)
            #subb.active = p.active
            subb.prop(p,"s_visibility_view_allow", 
                text="", 
                emboss=True, 
                icon_value=cust_icon(f"W_PERCENTAGE_{str(p.s_visibility_view_allow).upper()}"),
                )
            subb.prop(p,"s_visibility_cam_allow", 
                text="", 
                emboss=True, 
                icon= "OUTLINER_OB_CAMERA" if p.s_visibility_cam_allow else "CAMERA_DATA",
                )
            subb.prop(p,"s_display_allow", 
                text="", 
                emboss=True, 
                icon_value=cust_icon(f"W_DISPLAY_{str(p.s_display_allow).upper()}"),
                )
            method = subb.row(align=True)
            method.active = p.s_display_allow
            method.prop(p,"s_display_method", 
                text="", 
                emboss=True,
                icon_only=True,
                )
            
            sub.separator(factor=0.1)

            op = prow.operator("scatter5.remove_system",
                text="",
                icon="TRASH",
                emboss=False,
                )
            op.undo_push=True
            op.emitter_name=e.name
            op.method="name"
            op.name=p.name

            prow.separator()

            plen +=1
            continue 


        #Emitter Information, done at the end 

        emit_text_info = ""
        
        if (e.scatter5.estimated_square_area!=-1):
            emit_text_info += f'{round(e.scatter5.estimated_square_area,2):,} m²'

        if (totparticle!=-1):
            pass
            #emit_text_info += f'  |   {int(totparticle):,} P  '
        
        if emit_text_info:
            erow.separator_spacer()

            estim = erow.row(align=True)
            estim.alignment="RIGHT"
            estim.label(text=emit_text_info)

        col.separator() 
        continue

    #not found anything? 

    if not plen:
        text = layout.column()
        text.active = False
        text.alignment="CENTER"
        text.label(text=translate("No Particle-System Added Yet?"))


    return 



#######################################################################################
#
#        .oooooo.   oooo
#       d8P'  `Y8b  `888
#      888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
#      888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
#      888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
#      `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#       `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'
#
#######################################################################################



classes = [
            SCATTER5_OT_impost_addonprefs,

          ]



#if __name__ == "__main__":
#    register()