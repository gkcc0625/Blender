
#####################################################################################################
#
# ooooo                          .
# `888'                        .o8
#  888  ooo. .oo.    .oooo.o .o888oo  .oooo.   ooo. .oo.    .ooooo.   .ooooo.   .oooo.o
#  888  `888P"Y88b  d88(  "8   888   `P  )88b  `888P"Y88b  d88' `"Y8 d88' `88b d88(  "8
#  888   888   888  `"Y88b.    888    .oP"888   888   888  888       888ooo888 `"Y88b.
#  888   888   888  o.  )88b   888 . d8(  888   888   888  888   .o8 888    .o o.  )88b
# o888o o888o o888o 8""888P'   "888" `Y888""8o o888o o888o `Y8bod8P' `Y8bod8P' 8""888P'
#
#####################################################################################################


import bpy

from .. utils.event_utils import get_event
from .. resources.translate import translate
from .. utils.import_utils import import_selected_assets


# oooooooooooo                                       .    o8o
# `888'     `8                                     .o8    `"'
#  888         oooo  oooo  ooo. .oo.    .ooooo.  .o888oo oooo   .ooooo.  ooo. .oo.
#  888oooo8    `888  `888  `888P"Y88b  d88' `"Y8   888   `888  d88' `88b `888P"Y88b
#  888    "     888   888   888   888  888         888    888  888   888  888   888
#  888          888   888   888   888  888   .o8   888 .  888  888   888  888   888
# o888o         `V88V"V8P' o888o o888o `Y8bod8P'   "888" o888o `Y8bod8P' o888o o888o


def collection_users(collection):
    """return all scatter5 psy that use this collection as s_instances_coll_ptr"""

    users = []
    for o in bpy.data.objects:
        if len(o.scatter5.particle_systems):
            for p in o.scatter5.particle_systems:
                if p.s_instances_coll_ptr == collection:
                    users.append(p)
    return users

def is_compatible_instance(o, emitter=None,):
    """check if object compatible to be scattered"""

    #get emitter 
    if emitter is None:
        emitter = bpy.context.scene.scatter5.emitter

    #emitter need to exists!
    if emitter is None:
        return False
    #cannot be active emitter
    elif o==emitter:
        return False
    #cannot be an emitter
    elif len(o.scatter5.particle_systems)!=0:
        return False
    #scatter object not supported 
    elif o.name.startswith("scatter_obj : "):
        return False
    #supported meshes
    elif o.type not in ["MESH","CURVE","LIGHT","LIGHT_PROBE","VOLUME","EMPTY","FONT","META","SURFACE"]:  
        return False

    return True 

def find_compatible_instances(obj_list, emitter=None,):
    """return a generator of compatible object"""

    for o in obj_list:
        if is_compatible_instance(o, emitter=emitter):
            yield o


#   .oooooo.                                               .
#  d8P'  `Y8b                                            .o8
# 888      888 oo.ooooo.   .ooooo.  oooo d8b  .oooo.   .o888oo  .ooooo.  oooo d8b
# 888      888  888' `88b d88' `88b `888""8P `P  )88b    888   d88' `88b `888""8P
# 888      888  888   888 888ooo888  888      .oP"888    888   888   888  888
# `88b    d88'  888   888 888    .o  888     d8(  888    888 . 888   888  888
#  `Y8bood8P'   888bod8P' `Y8bod8P' d888b    `Y888""8o   "888" `Y8bod8P' d888b
#               888
#              o888o


class SCATTER5_OT_add_instances(bpy.types.Operator):

    bl_idname = "scatter5.add_instances"
    bl_label       = translate("Add Selected")
    bl_description = translate("Add selected objects in Scatter instance collection, If multiple systems are selected press [ALT] to add to all selected system collections at the same time")
    bl_options     = {'INTERNAL','UNDO'}

    method : bpy.props.EnumProperty(
        name=translate("Add from"),
        default= "viewport", 
        items= [ ("viewport", translate("Selected Object(s)"), translate("Add the selected compatible objects found in the viewport"), "VIEW3D",1 ),
                 ("browser", translate("Selected Asset(s)"), translate("Add the selected object found in the asset browser"), "ASSET_MANAGER",2 ),
               ],
        )

    def execute(self, context):

        event = get_event()

        scat_scene = bpy.context.scene.scatter5
        emitter    = scat_scene.emitter
        psys       = emitter.scatter5.particle_systems
        psy_active = emitter.scatter5.get_psy_active()
        psys_sel   = emitter.scatter5.get_psys_selected()

        if (self.method=="browser"):
              obj_list = import_selected_assets(link=(scat_scene.opt_import_method=="LINK"),)
        else: obj_list = bpy.context.selected_objects 
        instances = list(find_compatible_instances(obj_list, emitter=emitter,))
             
        if (len(instances)==0):
            msg = translate("No valid Object(s) found in Selection.") if (not self.method=="browser") else translate("No Asset(s) found in Asset-Browser.")
            bpy.ops.scatter5.popup_menu(msgs=msg, title=translate("Warning"),icon="ERROR",)
            return {'FINISHED'}

        if (event.alt):  
              colls = [ p.s_instances_coll_ptr for p in psys_sel]
        else: colls = [ psy_active.s_instances_coll_ptr ]


        o = None 
        for coll in colls:

            for o in instances:
                
                if coll is not None:
                    if o.name not in coll.objects:
                        coll.objects.link(o)
                continue

            #refresh signal needed for collection
            display = o.display_type
            o.display_type = "BOUNDS"
            o.display_type = display

            continue

        return {'FINISHED'}

class SCATTER5_OT_remove_instances(bpy.types.Operator):

    bl_idname = "scatter5.remove_instances"
    bl_label       = translate("Remove this instance")
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO'}

    ins_idx : bpy.props.IntProperty()

    def execute(self, context):

        event = get_event()

        scat_scene = bpy.context.scene.scatter5
        emitter    = scat_scene.emitter
        psys       = emitter.scatter5.particle_systems
        psy_active = emitter.scatter5.get_psy_active()
        psys_sel   = emitter.scatter5.get_psys_selected()

        if (event.alt):  
              colls = [ p.s_instances_coll_ptr for p in psys_sel]
        else: colls = [ psy_active.s_instances_coll_ptr ]

        for coll in colls:
            for i,o in enumerate(coll.objects):
                if (i==self.ins_idx):
                    coll.objects.unlink(o)
                continue
            continue
            
        #refresh signal needed for collection

        if len(coll.objects)!=0:
            o = coll.objects[0]
            display = o.display_type
            o.display_type = "BOUNDS"
            o.display_type = display

        return {'FINISHED'}

# class SCATTER5_OT_instances_batch_set_display(bpy.types.Operator):

#     bl_idname = "scatter5.instances_batch_set_display"
#     bl_label       = translate("Change the real-objects display with this operator")
#     bl_description = translate("Batche set instances display option, for every instances of the active or selecte particle-systems if the hotkey ALT is hold on click")
#     bl_options     = {'INTERNAL','UNDO'}

#     display_type : bpy.props.StringProperty() #BOUNDS/SOLID/LODIFY_ENABLE/LODIFY_DISABLE
#     instances_list : bpy.props.StringProperty() # name of assets separated by "_#_" #-> unused in Scatter

#     def execute(self, context):

#         instances = [] 

#         if self.instances_list=="": #then we need to find them 

#             emitter = bpy.context.scene.scatter5.emitter
#             psys    = emitter.scatter5.particle_systems

#             event = get_event()
            
#             if (event.alt): 
#                   psys = [p for p in psys if p.sel]
#             else: psys = [p for p in psys if p.active]

#             #get instances
#             for p in psys:
#                 for o in p.get_instances_obj():
#                     instances.append(o)
#         else:
#             #gather objects
#             for n in self.instances_list.split("_#_"):
#                 o = bpy.data.objects.get(n)  
#                 if o is not None: 
#                     instances.append(o)

#         #Now change the instance type

#         if self.display_type in ["BOUNDS","SOLID"]:
#             for o in instances:        
#                 o.display_type = self.display_type

#         elif self.display_type in ["LODIFY_ENABLE","LODIFY_DISABLE"]:
#             from..external import enable_lodify
#             enable_lodify(instances, status= self.display_type=="LODIFY_ENABLE")

#         return {'FINISHED'}


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = [

    SCATTER5_OT_add_instances,
    SCATTER5_OT_remove_instances,

    ]
