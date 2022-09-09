
#####################################################################################################
#
# oooooooooo.                           .o8
# `888'   `Y8b                         "888
#  888     888  .ooooo.  oooo d8b  .oooo888   .ooooo.  oooo d8b
#  888oooo888' d88' `88b `888""8P d88' `888  d88' `88b `888""8P
#  888    `88b 888   888  888     888   888  888ooo888  888
#  888    .88P 888   888  888     888   888  888    .o  888
# o888bood8P'  `Y8bod8P' d888b    `Y8bod88P" `Y8bod8P' d888b
#
#####################################################################################################


import bpy, bmesh
import numpy as np

from ... import utils
from ... utils.str_utils import no_names_in_double

from ... resources.icons import cust_icon
from ... resources.translate import translate


url = "https://www.scatterforblender.com/" #just link to website?



# oooooooooo.
# `888'   `Y8b
#  888      888 oooo d8b  .oooo.   oooo oooo    ooo
#  888      888 `888""8P `P  )88b   `88. `88.  .8'
#  888      888  888      .oP"888    `88..]88..8'
#  888     d88'  888     d8(  888     `888'`888'
# o888bood8P'   d888b    `Y888""8o     `8'  `8'



def draw_settings(layout,i):

    scat_scene = bpy.context.scene.scatter5
    emitter    = scat_scene.emitter
    masks      = emitter.scatter5.mask_systems
    m          = masks[i]

    layout.separator(factor=0.5)

    #layout setup 

    row = layout.row()
    row.row()
    row.scale_y = 0.9

    row1 = row.row()
    row1.scale_x = 1.201
    lbl = row1.column()
    lbl.alignment="RIGHT"

    row2 = row.row()
    prp = row2.column()

    #settings

    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    lbl.label(text="")
    prp.prop(m,"mesh_data_prox_distance",text=translate("Distance"))  

    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    lbl.label(text="")
    prp.prop(m,"mesh_data_prox_offset",text=translate("Offset"))   

    if m.mesh_data_prox_offset>m.mesh_data_prox_distance:
        lbl.label(text="")
        warn = prp.row()
        warn.active = False
        warn.label(text=translate("Offset need to be smaller than distance"))
    
    lbl.separator(factor=3.7)
    prp.separator(factor=3.7)

    lbl.label(text=translate("Data"))
    refresh = prp.row(align=True)
    re = refresh.operator("scatter5.refresh_mask",text=translate("Recalculate"),icon="FILE_REFRESH")
    re.mask_type = m.type
    re.mask_idx = i

    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    lbl.label(text=translate("Remap"))
    mod_name   = f"Scatter5 Remapping {m.name}"
    if (mod_name in emitter.modifiers) and (emitter.modifiers[mod_name].falloff_type=="CURVE"):
        mod = emitter.modifiers[mod_name]
        remap = prp.row(align=True)
        o = remap.operator("scatter5.graph_dialog",text=translate("Remap Values"),icon="FCURVE")
        o.source_api= f"bpy.data.objects['{emitter.name}'].modifiers['{mod.name}']"
        o.mapping_api= f"bpy.data.objects['{emitter.name}'].modifiers['{mod.name}'].map_curve"
        o.mask_name = m.name
        
        butt = remap.row(align=True)
        butt.operator("scatter5.property_toggle",
               text="",
               icon="RESTRICT_VIEW_OFF" if mod.show_viewport else"RESTRICT_VIEW_ON",
               depress=mod.show_viewport,
               ).api = f"bpy.context.scene.scatter5.emitter.modifiers['{mod_name}'].show_viewport"
    else:
        o = prp.operator("scatter5.add_vg_edit",text=translate("Add Remap"),icon="FCURVE")
        o.mask_name = m.name
        

    layout.separator()

    return 



#       .o.             .o8        .o8
#      .888.           "888       "888
#     .8"888.      .oooo888   .oooo888
#    .8' `888.    d88' `888  d88' `888
#   .88ooo8888.   888   888  888   888
#  .8'     `888.  888   888  888   888
# o88o     o8888o `Y8bod88P" `Y8bod88P"


#Support Vcol 
def get_border_data(o, ray_distance=2.5,ray_offset=0.1,):

    ob = o.data

    bm = bmesh.new()
    bm.from_mesh(ob)
    bm.verts.ensure_lookup_table()

    r = []
    for v in bm.verts:
        if v.is_boundary:
            r.append(v.index)

    bm.free()

    return utils.vg_utils.kd_trees_rays(ob, verts_idx=r, distance=ray_distance, offset=ray_offset,)



def add():

    scat_scene = bpy.context.scene.scatter5
    emitter    = scat_scene.emitter
    masks      = emitter.scatter5.mask_systems

    #add mask to list 
    m = masks.add()
    m.type      = "border"
    m.icon      = "W_BORDER"                             
    m.name = m.user_name = no_names_in_double("Border", [vg.name for vg  in emitter.vertex_groups], startswith00=True)
    m.mesh_data_prox_distance  = 1.0
    m.mesh_data_prox_offset = 0.1

    #create the vertex group
    vg = utils.vg_utils.create_vg(emitter, m.name, fill=get_border_data(emitter, ray_distance=m.mesh_data_prox_distance, ray_offset=m.mesh_data_prox_offset),)
    vg.lock_weight = True

    return 



# ooooooooo.              .o88o.                             oooo
# `888   `Y88.            888 `"                             `888
#  888   .d88'  .ooooo.  o888oo  oooo d8b  .ooooo.   .oooo.o  888 .oo.
#  888ooo88P'  d88' `88b  888    `888""8P d88' `88b d88(  "8  888P"Y88b
#  888`88b.    888ooo888  888     888     888ooo888 `"Y88b.   888   888
#  888  `88b.  888    .o  888     888     888    .o o.  )88b  888   888
# o888o  o888o `Y8bod8P' o888o   d888b    `Y8bod8P' 8""888P' o888o o888o



def refresh(i,obj=None):

    scat_scene = bpy.context.scene.scatter5

    if obj: 
          emitter = obj
    else: emitter = scat_scene.emitter

    masks    = emitter.scatter5.mask_systems
    m        = masks[i]

    #create the vertex group
    vg = utils.vg_utils.create_vg(emitter, m.name, set_active=False, 
        fill=get_border_data(emitter, ray_distance=m.mesh_data_prox_distance, ray_offset=m.mesh_data_prox_offset,)
        )
    vg.lock_weight = True

    return 



# ooooooooo.
# `888   `Y88.
#  888   .d88'  .ooooo.  ooo. .oo.  .oo.    .ooooo.  oooo    ooo  .ooooo.
#  888ooo88P'  d88' `88b `888P"Y88bP"Y88b  d88' `88b  `88.  .8'  d88' `88b
#  888`88b.    888ooo888  888   888   888  888   888   `88..8'   888ooo888
#  888  `88b.  888    .o  888   888   888  888   888    `888'    888    .o
# o888o  o888o `Y8bod8P' o888o o888o o888o `Y8bod8P'     `8'     `Y8bod8P'



def remove(i):
    from ..remove import general_mask_remove
    general_mask_remove(obj_name=bpy.context.scene.scatter5.emitter.name,mask_idx=i) #remove vg, vgedit, mask from list, refresh viewport
    return 


