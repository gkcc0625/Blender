
#####################################################################################################
#
# ooooo     ooo ooooo      oooooooooooo                 .
# `888'     `8' `888'      `888'     `8               .o8
#  888       8   888        888         oooo    ooo .o888oo oooo d8b  .oooo.
#  888       8   888        888oooo8     `88b..8P'    888   `888""8P `P  )88b
#  888       8   888        888    "       Y888'      888    888      .oP"888
#  `88.    .8'   888        888       o  .o8"'88b     888 .  888     d8(  888
#    `YbodP'    o888o      o888ooooood8 o88'   888o   "888" d888b    `Y888""8o
#
#####################################################################################################



import bpy

from .. resources.icons import cust_icon
from .. resources.translate import translate

from . import templates

from .. utils.str_utils import word_wrap
from .. utils.vg_utils import is_vg_active

from .. utils.extra_utils import is_rendered_view


# oooooooooo.
# `888'   `Y8b
#  888      888 oooo d8b  .oooo.   oooo oooo    ooo
#  888      888 `888""8P `P  )88b   `88. `88.  .8'
#  888      888  888      .oP"888    `88..]88..8'
#  888     d88'  888     d8(  888     `888'`888'
# o888bood8P'   d888b    `Y888""8o     `8'  `8'


def draw_extra_panel(self,layout):

    scat_scene = bpy.context.scene.scatter5
        
    main = layout.column()
    main.enabled = scat_scene.ui_enabled

    #Synchronization 

    is_open = templates.main_panel(self,main,
        prop_str = "sync_main",
        icon = "W_ARROW_SYNC",
        name = translate("Synchronize Scattering"),
        )
    if is_open:
            draw_sync(self,main)
            templates.main_spacing(main)

    #Procedural Vertex Group Workflow

    is_open = templates.main_panel(self,main,
        prop_str = "masks_main",
        icon = "GROUP_VERTEX",
        name = translate("Procedural Vertex-Data"),
        )
    if is_open:
            draw_parametric_masks(self,main)
            templates.main_spacing(main)
    
    #Update Behavior

    is_open = templates.main_panel(self,main,
        prop_str = "upd_main",
        icon = "FILE_REFRESH",
        name = translate("Update Behavior"),
        )
    if is_open:
            draw_update(self,main)
            templates.main_spacing(main)

    #Security

    is_open = templates.main_panel(self,main,
        prop_str = "security_main",
        icon = "FAKE_USER_ON",
        name = translate("Security"),
        )
    if is_open:
            draw_security(self,main)
            templates.main_spacing(main)

    #main panel terrain

    is_open = templates.main_panel(self,main,
        prop_str = "terrain_main",
        icon = "MOD_DISPLACE",
        name = translate("Quick Displace"),
        )
    if is_open:
            draw_terrain_displace(self,main)
            templates.main_spacing(main)

    #Export 

    is_open = templates.main_panel(self,main,
        prop_str = "export_main",
        icon = "W_EXPORT_FILE",
        name = translate("Export"),
        )
    if is_open:
            draw_export(self,main)
            templates.main_spacing(main)

    #main panel manual 

    is_open = templates.main_panel(self,main,
        prop_str = "manual_main",
        icon = "HELP",
        name = translate("Help and Links"),
        )
    if is_open:
            draw_social(self,main)
            templates.main_spacing(main)
            
    layout.separator(factor=50)
    
    return None 


#   .oooooo.                   o8o            oooo             oooooooooo.    o8o                      oooo
#  d8P'  `Y8b                  `"'            `888             `888'   `Y8b   `"'                      `888
# 888      888    oooo  oooo  oooo   .ooooo.   888  oooo        888      888 oooo   .oooo.o oo.ooooo.   888   .oooo.    .ooooo.   .ooooo.
# 888      888    `888  `888  `888  d88' `"Y8  888 .8P'         888      888 `888  d88(  "8  888' `88b  888  `P  )88b  d88' `"Y8 d88' `88b
# 888      888     888   888   888  888        888888.          888      888  888  `"Y88b.   888   888  888   .oP"888  888       888ooo888
# `88b    d88b     888   888   888  888   .o8  888 `88b.        888     d88'  888  o.  )88b  888   888  888  d8(  888  888   .o8 888    .o
#  `Y8bood8P'Ybd'  `V88V"V8P' o888o `Y8bod8P' o888o o888o      o888bood8P'   o888o 8""888P'  888bod8P' o888o `Y888""8o `Y8bod8P' `Y8bod8P'
#                                                                                            888
#                                                                                           o888o


def draw_terrain_displace(self,layout):

    box, is_open = templates.sub_panel(self, layout, 
        prop_str   = "terrain_sub2", 
        icon       = "MOD_DISPLACE", 
        name       = translate("Quick Displace"),
        description= "",
        doc        = translate("Change how your properties update your scene.")+"\n\n"+translate("Learn more in the Docs") +"_#LINK#_"+"https://sites.google.com/view/scatter5docs/manual/extra?authuser=0#h.1co5rd7tchu7",
        )
    if is_open:

            emitter = bpy.context.scene.scatter5.emitter

            row  = box.row()
            row1 = row.row() ; row1.scale_x = 0.17
            row2 = row.row()
            row3 = row.row() ; row3.scale_x = 0.17
            col = row2.column()

            mods    = emitter.modifiers

            #box.label(text=translate("Add Uv-Image Displacement"))

            name = "Scatter5 Displace img-uv"
            if name not in mods:
                op = col.row()
                op.scale_y = 1.2
                op.operator("scatter5.create_displace_dialog",text=translate("UV Displace")).create=False
            else:
                m = emitter.modifiers[name]
                col = col.column(align=True)
                row = col.row(align=True) 
                row.scale_y = 1.1
                row.operator("scatter5.dummy",text="UV Displace")
                row.prop(m,"show_viewport",text="")
                row.operator("scatter5.remove_displace",text="",icon="TRASH").name=name
                col.prop(m,"strength")
                col.prop(m,"mid_level")
                
                #t = m.texture
                #if t is not None:
                #    col.template_ID(t, "image", open="image.open", unlink="object.unlink_data")


            col.separator()
            #col.label(text=translate("Add Procedural Displacement"))

            name = "Scatter5 Displace noise 01"
            if name not in mods:
                op = col.row()
                op.scale_y = 1.2
                op.operator("scatter5.add_displace",text=translate("Noise Displace 01")).name=name
            else:
                m = emitter.modifiers[name]
                col = col.column(align=True)
                row = col.row(align=True) 
                row.scale_y = 1.1
                row.operator("scatter5.dummy",text="Noise Displace 01")
                row.prop(m,"show_viewport",text="")
                row.operator("scatter5.remove_displace",text="",icon="TRASH").name=name
                col.prop(m,"strength")
                col.prop(m,"mid_level")
                
                t = m.texture
                if t is not None:
                    col.prop(t,"noise_scale")
                    col.prop(t,"noise_depth")


            col.separator()
            #col.label(text=translate("Add Procedural Displacement"))

            name = "Scatter5 Displace noise 02"
            if name not in mods:
                op = col.row()
                op.scale_y = 1.2
                op.operator("scatter5.add_displace",text=translate("Noise Displace 02")).name=name
            else:
                m = emitter.modifiers[name]
                col = col.column(align=True)
                row = col.row(align=True) 
                row.scale_y = 1.1
                row.operator("scatter5.dummy",text="Noise Displace 02")
                row.prop(m,"show_viewport",text="")
                row.operator("scatter5.remove_displace",text="",icon="TRASH").name=name
                col.prop(m,"strength")
                col.prop(m,"mid_level")

                t = m.texture
                if t is not None:
                    col.prop(t,"noise_scale")
                    col.prop(t,"noise_depth")                    

            templates.sub_spacing(box)
    return



# ooooooooo.                                                .o8                                 oooo       oooooo     oooo
# `888   `Y88.                                             "888                                 `888        `888.     .8'
#  888   .d88' oooo d8b  .ooooo.   .ooooo.   .ooooo.   .oooo888  oooo  oooo  oooo d8b  .oooo.    888         `888.   .8'    .oooooooo
#  888ooo88P'  `888""8P d88' `88b d88' `"Y8 d88' `88b d88' `888  `888  `888  `888""8P `P  )88b   888          `888. .8'    888' `88b
#  888          888     888   888 888       888ooo888 888   888   888   888   888      .oP"888   888           `888.8'     888   888
#  888          888     888   888 888   .o8 888    .o 888   888   888   888   888     d8(  888   888            `888'      `88bod8P'
# o888o        d888b    `Y8bod8P' `Y8bod8P' `Y8bod8P' `Y8bod88P"  `V88V"V8P' d888b    `Y888""8o o888o            `8'       `8oooooo.
#                                                                                                                          d"     YD
#                                                                                                                          "Y88888P'

from .. procedural_vg import mask_type 


def draw_parametric_masks(self,layout):

    MainCol = layout.column(align=True)
    box, is_open = templates.sub_panel(self, MainCol.column(align=True), 
        prop_str   = "masks_sub1", 
        icon       = "GROUP_VERTEX", 
        name       = "    "+ translate("Vertex-Data"),
        description= "",
        doc        = translate("Generate extremely useful vertex-data to influence your scatter or perhaps your shaders.")+"\n\n"+translate("Learn more in the Docs") +"_#LINK#_"+"https://sites.google.com/view/scatter5docs/manual/procedural-vertex-data",
        panel      = "SCATTER5_PT_mask_header",
        )
    if is_open:

            scat_scene = bpy.context.scene.scatter5
            emitter = scat_scene.emitter
            masks       = emitter.scatter5.mask_systems
            active_mask = None 
            mask_idx    = emitter.scatter5.mask_systems_idx
            if (len(masks)!=0):
                active_mask = masks[mask_idx]

            #Warnings to user 

            if (scat_scene.sec_emit_verts_max_allow or scat_scene.sec_emit_verts_min_allow):

                verts=len(emitter.data.vertices)

                if (scat_scene.sec_emit_verts_max_allow and (verts>scat_scene.sec_emit_verts_max)):
                    word_wrap(layout=box, string=translate("This emitter mesh is too high poly!\nYou may experience slowdowns"), max_char=50,)
                    box.separator(factor=0.1)

                if (scat_scene.sec_emit_verts_min_allow and (verts<scat_scene.sec_emit_verts_min)):
                    word_wrap(layout=box, string=translate("This emitter mesh is too low poly!\nVertex-groups masks need some Vertices!"), max_char=60,)
                    box.separator(factor=0.1)

            row = box.row()

            #Left Spacers
            row.separator(factor=0.5)

            #List Template
            
            template = row.column()
            template.template_list("SCATTER5_UL_tweaking_masks", "", emitter.scatter5, "mask_systems", emitter.scatter5, "mask_systems_idx", rows=10,)
                
            #Operators side menu

            ope = row.column(align=True)

            #Add New mask 

            op = ope.operator("scatter5.add_mask", text="", icon="ADD")
            op.draw = True

            #remove mask 

            op = ope.operator("scatter5.remove_mask",text="",icon="REMOVE")
            op.mask_type = active_mask.type if (active_mask is not None) else ""
            op.mask_idx = mask_idx

            #move up down

            ope.separator()
            updo = ope.column(align=True)
            updo.enabled = len(masks)!=0
            op = updo.operator("scatter5.list_move",text="",icon="TRIA_UP")
            op.target_idx = mask_idx       
            op.direction = "UP"    
            op.api_propgroup = "emitter.scatter5.mask_systems"
            op.api_propgroup_idx = "emitter.scatter5.mask_systems_idx"
            op = updo.operator("scatter5.list_move",text="",icon="TRIA_DOWN")
            op.target_idx = mask_idx       
            op.direction = "DOWN"   
            op.api_propgroup = "emitter.scatter5.mask_systems"
            op.api_propgroup_idx = "emitter.scatter5.mask_systems_idx"

            #assign mask

            ope.separator()
            op = ope.operator("scatter5.assign_mask",text="",icon="FILE_PARENT")
            op.mask_idx = mask_idx

            #Right Spacer
            row.separator(factor=0.1)

            #Stop drawing if no active mask
            if active_mask==None:
            
                templates.sub_spacing(box)
                return                 

            #box.separator(factor=0.3)

            #Draw settings under tittle info
            
            undertittle = box.column(align=True)

            subrow = undertittle.row()
            subrow.active = False

            #vg pointer
            ptr = None 

            #Draw Vg Pointer, note that some masks don't respect the classic vg per mask format, such as modifier based masks 

            if active_mask.type in ["vcol_to_vgroup","vgroup_split","vgroup_merge"]:

                modname = f"Scatter5 {active_mask.name}"

                ptr = subrow.column(align=True)
                ptr.scale_y = 0.85
                ptr.enabled = False
                ptr.alert = (modname not in emitter.modifiers)
                ptr.prop(active_mask,"name",icon="MODIFIER_OFF",text="modifier")

                #Stop drawing if no mod

                if (modname not in emitter.modifiers):

                    box = MainCol.box().column(align=True)   

                    warn = box.row(align=True)
                    warn.alignment = "CENTER"
                    warn.active = False
                    warn.scale_y = 0.9
                    warn.label(text=translate("Modifier Missing, Please Refresh"),icon="ERROR")
                    box.separator()

                    return 

            else:

                ptr = subrow.column(align=True)
                ptr.scale_y = 0.85
                ptr.enabled = False
                ptr.prop_search(active_mask, "name", emitter, "vertex_groups", text=f"vgroup")

                #Stop drawing if no vg pointers

                if (active_mask.name not in emitter.vertex_groups):

                    box = MainCol.box().column(align=True)   

                    warn = box.row(align=True)
                    warn.alignment = "CENTER"
                    warn.active = False
                    warn.scale_y = 0.9
                    warn.label(text=translate("Vertex Group Missing, Please Refresh"),icon="ERROR")
                    box.separator()

                    return 

            box = MainCol.box().column(align=True)            

            #drawing code of each masks stored within it's own type module. 
            exec(f"mask_type.{active_mask.type}.draw_settings( box, mask_idx,)")

            box.separator(factor=1.2)
            return 

    return 



class SCATTER5_UL_tweaking_masks(bpy.types.UIList):
    """mask lists to set active"""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if not item:
            return 

        emitter = bpy.context.scene.scatter5.emitter
        
        #user_name
        if item.icon.startswith("W_"):
              layout.prop(item,"user_name", text="", emboss=False, icon_value=cust_icon(item.icon) )
        else: layout.prop(item,"user_name", text="", emboss=False, icon=item.icon )

        #mask refresh operation
        ope = layout.row()
        op = ope.operator("scatter5.refresh_mask",text="",icon="FILE_REFRESH",emboss=False,)
        op.mask_type = item.type
        op.mask_idx = [i for i,m in enumerate(emitter.scatter5.mask_systems) if m==item][0]

        #direct paint operator
        w = layout.row()
        
        if item.type in ["vcol_to_vgroup","vgroup_split","vgroup_merge"]:

            #these masks do not work like all other masks
            mod = emitter.modifiers.get(f"Scatter5 {item.name}")
            if (item.type=="vgroup_merge") and (mod is not None) and (mod["Output_5_attribute_name"]!=""):
                vg_name = mod["Output_5_attribute_name"]
                vg_active = is_vg_active(emitter, vg_name)
                w.active = (vg_active) and (bpy.context.mode == "PAINT_WEIGHT")
                op = w.operator("scatter5.vg_quick_paint",text="",icon="BRUSH_DATA", emboss=vg_active, depress=vg_active,) ; op.mode = "vg" ; op.group_name = vg_name
            else:
                w.operator("scatter5.dummy",text="",icon="BLANK1",emboss=False, depress=False,)

        else:

            #set mask active 
            vg_active = is_vg_active(emitter, item.name)
            w.active = (vg_active) and (bpy.context.mode == "PAINT_WEIGHT")
            op = w.operator("scatter5.vg_quick_paint",text="",icon="BRUSH_DATA", emboss=vg_active, depress=vg_active,) ; op.mode = "vg" ; op.group_name = item.name

        return


#  .oooooo..o                                   oooo                                        o8o
# d8P'    `Y8                                   `888                                        `"'
# Y88bo.      oooo    ooo ooo. .oo.    .ooooo.   888 .oo.   oooo d8b  .ooooo.  ooo. .oo.   oooo    oooooooo  .ooooo.
#  `"Y8888o.   `88.  .8'  `888P"Y88b  d88' `"Y8  888P"Y88b  `888""8P d88' `88b `888P"Y88b  `888   d'""7d8P  d88' `88b
#      `"Y88b   `88..8'    888   888  888        888   888   888     888   888  888   888   888     .d8P'   888ooo888
# oo     .d8P    `888'     888   888  888   .o8  888   888   888     888   888  888   888   888   .d8P'  .P 888    .o
# 8""88888P'      .8'     o888o o888o `Y8bod8P' o888o o888o d888b    `Y8bod8P' o888o o888o o888o d8888888P  `Y8bod8P'
#             .o..P'
#             `Y8P'


def draw_sync(self,layout):

    box, is_open = templates.sub_panel(self, layout, 
        prop_str   = "sync_sub1", 
        icon       = "W_ARROW_SYNC", 
        name       = translate("Synchronize Scattering"), 
        description= "",
        doc        = translate("Synchronize Scattering Settings Together.")+"\n\n"+translate("Learn more in the Docs") +"_#LINK#_"+"https://sites.google.com/view/scatter5docs/manual/extra#h.rmdc9wrrzah6",
        )
    if is_open:

        scat_scene = bpy.context.scene.scatter5

        row = box.row()

        row.separator(factor=0.5)

        row.template_list("SCATTER5_UL_sync_channels", "", scat_scene, "sync_channels", scat_scene, "sync_channels_idx", rows=3)

        col = row.column(align=True)

        add = col.row(align=True)
        add.operator("scatter5.add_sync_channel", icon="ADD", text="").add = True

        rem = col.row(align=True)
        rem.enabled = bool(len(scat_scene.sync_channels)) and scat_scene.sync_channels_idx<len(scat_scene.sync_channels)
        rem.operator("scatter5.add_sync_channel", icon="REMOVE", text="").remove = True

        #Right Spacer
        row.separator(factor=0.1)

        templates.sub_spacing(box)
        
    return 


# ooooo     ooo                  .o8                .
# `888'     `8'                 "888              .o8
#  888       8  oo.ooooo.   .oooo888   .oooo.   .o888oo  .ooooo.
#  888       8   888' `88b d88' `888  `P  )88b    888   d88' `88b
#  888       8   888   888 888   888   .oP"888    888   888ooo888
#  `88.    .8'   888   888 888   888  d8(  888    888 . 888    .o
#    `YbodP'     888bod8P' `Y8bod88P" `Y888""8o   "888" `Y8bod8P'
#                888
#               o888o


def draw_update(self,layout):

    box, is_open = templates.sub_panel(self, layout, 
        prop_str   = "upd_sub1", 
        icon       = "FILE_REFRESH", 
        name       = translate("Update Behavior"),
        description= "",
        doc        = translate("Change how your properties update your scene.")+"\n\n"+translate("Learn more in the Docs") +"_#LINK#_"+"https://sites.google.com/view/scatter5docs/manual/extra#h.2doyr3ks9f0f",
        )
    if is_open:

            scat_scene = bpy.context.scene.scatter5

            #Alt batch Update 

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=scat_scene,
                prop_str="factory_alt_allow", 
                label=translate("Alt Batch Selection"), 
                icon="EVENT_ALT", 
                )
            if is_toggled:

                tocol.prop( scat_scene, "factory_alt_selection_method",text="")

            #Property Update Method 

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=scat_scene,
                prop_str="factory_delay_allow", 
                label=translate("Settings Update"), 
                icon="FILE_REFRESH", 
                )
            if is_toggled:

                tocol.prop( scat_scene, "factory_update_method",text="")
                
                if (scat_scene.factory_update_method=="update_delayed"):
                    tocol.separator(factor=0.5)
                    tocol.prop( scat_scene, "factory_update_delay")

            #Set Active ScatterObj

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=scat_scene,
                prop_str="update_auto_set_scatter_obj_active", 
                label=translate("Draw System Outline"), 
                icon="SEQ_STRIP_META", 
                )

            #Renndered View Overlay 

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=scat_scene,
                prop_str="update_auto_overlay_rendered", 
                label=translate("Disable Overlay on Render-View"), 
                icon="OVERLAY", 
                enabled= not is_rendered_view(),
                )

            templates.sub_spacing(box)
    return 


#  .oooooo..o                                           o8o      .
# d8P'    `Y8                                           `"'    .o8
# Y88bo.       .ooooo.   .ooooo.  oooo  oooo  oooo d8b oooo  .o888oo oooo    ooo
#  `"Y8888o.  d88' `88b d88' `"Y8 `888  `888  `888""8P `888    888    `88.  .8'
#      `"Y88b 888ooo888 888        888   888   888      888    888     `88..8'
# oo     .d8P 888    .o 888   .o8  888   888   888      888    888 .    `888'
# 8""88888P'  `Y8bod8P' `Y8bod8P'  `V88V"V8P' d888b    o888o   "888"     .8'
#                                                                    .o..P'
#                                                                    `Y8P'


def draw_security(self,layout):
    """draw security sub panel"""

    box, is_open = templates.sub_panel(self, layout, 
        prop_str   = "security_sub1", 
        icon       = "FAKE_USER_ON", 
        name       = translate("Security"), 
        description= "",
        doc        = translate("Change security behavior when scattering with presets or using biomes.")+"\n\n"+translate("Learn more in the Docs") +"_#LINK#_"+"https://sites.google.com/view/scatter5docs/manual/scattering#h.6j6ktj4599c3",
        )
    if is_open:

            scat_scene = bpy.context.scene.scatter5
            
            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=scat_scene,
                prop_str="sec_emit_count_allow", 
                label=translate("Max Particle-Count"), 
                icon="W_SECURITY_PARTICLE", 
                )
            if is_toggled:
                tocol.prop(scat_scene,"sec_emit_count")

            tocol, is_toggled = templates.bool_toggle(box, 
                prop_api=scat_scene,
                prop_str="sec_inst_verts_allow", 
                label=translate("Instances Max Poly-Count"), 
                icon="W_SECURITY_MESH", 
                )
            if is_toggled:
                tocol.prop(scat_scene,"sec_inst_verts")

            # tocol, is_toggled = templates.bool_toggle(box, 
            #     prop_api=scat_scene,
            #     prop_str="sec_emit_verts_min_allow", 
            #     label=translate("Emitter Minimal Poly-Count"), 
            #     icon="FAKE_USER_ON", 
            #     )
            # if is_toggled:
            #     tocol.prop(scat_scene,"sec_emit_verts_min")

            # tocol, is_toggled = templates.bool_toggle(box, 
            #     prop_api=scat_scene,
            #     prop_str="sec_emit_verts_max_allow", 
            #     label=translate("Emitter Maximal Poly-Count"), 
            #     icon="FAKE_USER_ON", 
            #     )
            # if is_toggled:
            #     tocol.prop(scat_scene,"sec_emit_verts_max")


            templates.sub_spacing(box)

    return


# oooooooooooo                                               .
# `888'     `8                                             .o8
#  888         oooo    ooo oo.ooooo.   .ooooo.  oooo d8b .o888oo
#  888oooo8     `88b..8P'   888' `88b d88' `88b `888""8P   888
#  888    "       Y888'     888   888 888   888  888       888
#  888       o  .o8"'88b    888   888 888   888  888       888 .
# o888ooooood8 o88'   888o  888bod8P' `Y8bod8P' d888b      "888"
#                           888
#                          o888o


def draw_export(self,layout):

    box, is_open = templates.sub_panel(self, layout, 
        prop_str   = "export_sub1", 
        icon       = "W_EXPORT_FILE", 
        name       = translate("Export"),
        description= "",
        doc        = translate("Export your particles.")+"\n\n"+translate("Learn more in the Docs") +"_#LINK#_"+"https://sites.google.com/view/scatter5docs/manual/export",
        )
    if is_open:

            emitter = bpy.context.scene.scatter5.emitter
            psys_sel = emitter.scatter5.get_psys_selected()

            if not len(psys_sel):
                
                txt = box.row()
                txt.active = False
                txt.alignment = "CENTER"
                txt.label(text=translate("No Particles Selected"),icon="RESTRICT_SELECT_ON")

                templates.sub_spacing(box)
                return 

            row  = box.row()
            row1 = row.row() ; row1.scale_x = 0.17
            row2 = row.row()
            row3 = row.row() ; row3.scale_x = 0.17
            col = row2.column()

            exp = col.row()
            exp.scale_y = 1.2
            exp.operator("scatter5.export_to_instance", text=translate("Selection to Instances"), )

            # Bad Idea, having a mesh that fat is not good for blender, user could Merge instance afterwards from option below
            # exp = col.row()
            # exp.enabled = False
            # exp.active = len(psys_sel)>0
            # exp.scale_y = 1.2
            # exp.operator("scatter5.dummy", text=translate("Merge Selected as Blender Mesh"), )

            col.separator()
            
            exp = col.row()
            exp.scale_y = 1.2 
            exp.operator("scatter5.export_to_json", text=translate("Selection to Json"), )

            col.separator()
                        
            exp = col.row()
            exp.scale_y = 1.2 
            exp.operator("scatter5.save_preset_to_disk_dialog", text=translate("Selection to Preset(s)"), )

            col.separator()
            
            exp = col.row()
            exp.scale_y = 1.2 
            exp.operator("scatter5.save_biome_to_disk_dialog", text=translate("Selection to Biome"), )

            # enable this for 5.1, way too much stuff in 5.0 already.
            # exp = col.row()
            # exp.enabled = False
            # exp.scale_y = 1.2
            # exp.operator("scatter5.bake_vertex_groups", text=translate("Bake VertexGroup(s)"), )

            col.separator()

            templates.sub_spacing(col)
    return




#  .oooooo..o                      o8o            oooo
# d8P'    `Y8                      `"'            `888
# Y88bo.       .ooooo.   .ooooo.  oooo   .oooo.    888
#  `"Y8888o.  d88' `88b d88' `"Y8 `888  `P  )88b   888
#      `"Y88b 888   888 888        888   .oP"888   888
# oo     .d8P 888   888 888   .o8  888  d8(  888   888
# 8""88888P'  `Y8bod8P' `Y8bod8P' o888o `Y888""8o o888o



def draw_social(self,layout): #TODO update links
    """draw manual sub panel"""

    col = layout.column(align=True)
    box, is_open = templates.sub_panel(self, col, 
        prop_str   = "manual_sub1", 
        icon       = "HELP", 
        name       = translate("Help and Links"), 
        )
    if is_open:

            row  = box.row()
            row1 = row.row() ; row1.scale_x = 0.17
            row2 = row.row()
            row3 = row.row() ; row3.scale_x = 0.17
            col = row2.column(align=True)

            txt=col.row(align=True)
            txt.label(text=translate("Official Websites")+":",)
            #
            col.operator("wm.url_open", text=translate("Official Website"), icon_value=cust_icon("W_SCATTER")).url = "https://www.scatterforblender.com/"
            col.operator("wm.url_open", text=translate("Biomes Catalog"), icon_value=cust_icon("W_SUPERMARKET")).url = "https://www.scatterforblender.com/"
            col.operator("wm.url_open", text=translate("Manual"), icon="HELP").url = "https://sites.google.com/view/scatter5docs/"

            col.separator()
            
            txt=col.row(align=True)
            txt.label(text=translate("Social Media")+":",)
            #
            col.operator("wm.url_open", text=translate("Youtube"), icon_value=cust_icon("W_YOUTUBE")).url = "https://www.youtube.com/channel/UCdtlx635Lq69YvDkBsu-Kdg"
            col.operator("wm.url_open", text=translate("Twitter"), icon_value=cust_icon("W_TWITTER")).url = "https://twitter.com/_BD3D"
            col.operator("wm.url_open", text=translate("Instagram"), icon_value=cust_icon("W_INSTAGRAM")).url = "https://www.instagram.com/scatter.plugin/" #TODO will become BD3D instagram page 
            # col.operator("wm.url_open", text=translate("Facebook (News)"), icon_value=cust_icon("W_FACEBOOK")).url = "https://www.facebook.com/scatter5plugin" #TODO will become BD3D instagram page 

            col.separator()
            
            txt=col.row(align=True)
            txt.label(text=translate("Assistance")+":",)
            #
            col.operator("wm.url_open", text=translate("Contact-Us"), icon_value=cust_icon("W_MARKET")).url = "https://www.blendermarket.com/creators/bd3d-store"
            col.operator("wm.url_open", text=translate("Community"), icon_value=cust_icon("W_BA")).url = "https://blenderartists.org/t/scatter-the-scattering-tool-of-blender-2-8/1177672"


            templates.sub_spacing(box)
    return


#    .oooooo.   oooo
#   d8P'  `Y8b  `888
#  888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
#  888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
#  888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
#  `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#   `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'



class SCATTER5_PT_extra_object(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_extra_object"
    bl_label       = translate("Extras")
    bl_category    = "Scatter5"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_context     = "objectmode"
    bl_order       = 2

    @classmethod
    def poll(cls, context, ):
        return context.scene.scatter5.emitter is not None
        
    def draw_header_preset(self, _context):
        templates.main_panel_header(self)

    def draw(self, context):
        layout = self.layout
        draw_extra_panel(self,layout)

class SCATTER5_PT_extra_weight(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_extra_weight"
    bl_label       = translate("Extras")
    bl_category    = "Scatter5"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_context     = "weightpaint"
    bl_order       = 2

    @classmethod
    def poll(cls, context, ):
        return context.scene.scatter5.emitter is not None

    def draw_header_preset(self, _context):
        templates.main_panel_header(self)

    def draw(self, context):
        layout = self.layout
        draw_extra_panel(self,layout)

class SCATTER5_PT_extra_vcolor(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_extra_vcolor"
    bl_label       = translate("Extras")
    bl_category    = "Scatter5"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_context     = "vertexpaint"
    bl_order       = 2

    @classmethod
    def poll(cls, context, ):
        return context.scene.scatter5.emitter is not None

    def draw_header_preset(self, _context):
        templates.main_panel_header(self)

    def draw(self, context):
        layout = self.layout
        draw_extra_panel(self,layout)

class SCATTER5_PT_extra_imgpaint(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_extra_imgpaint"
    bl_label       = translate("Extras")
    bl_category    = "Scatter5"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_context     = "imagepaint"
    bl_order       = 2

    @classmethod
    def poll(cls, context, ):
        return context.scene.scatter5.emitter is not None

    def draw_header_preset(self, _context):
        templates.main_panel_header(self)

    def draw(self, context):
        layout = self.layout
        draw_extra_panel(self,layout)


classes = [
            
    SCATTER5_UL_tweaking_masks,

    SCATTER5_PT_extra_object,
    SCATTER5_PT_extra_weight,
    SCATTER5_PT_extra_vcolor,
    SCATTER5_PT_extra_imgpaint,

    ]


#if __name__ == "__main__":
#    register()

