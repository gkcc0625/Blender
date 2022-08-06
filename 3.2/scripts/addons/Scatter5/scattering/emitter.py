
##################################################################################################
#
# oooooooooooo                    o8o      .       .
# `888'     `8                    `"'    .o8     .o8
#  888         ooo. .oo.  .oo.   oooo  .o888oo .o888oo  .ooooo.  oooo d8b
#  888oooo8    `888P"Y88bP"Y88b  `888    888     888   d88' `88b `888""8P
#  888    "     888   888   888   888    888     888   888ooo888  888
#  888       o  888   888   888   888    888 .   888 . 888    .o  888
# o888ooooood8 o888o o888o o888o o888o   "888"   "888" `Y8bod8P' d888b
#
#####################################################################################################


import bpy

from .. utils.extra_utils import dprint
from .. resources.translate import translate


def is_correct_emitter(object):
    """check if emitter emitter type is mesh"""
    return  ( 
               (object)  
               and (object.type == "MESH") 
               and (object.name in bpy.context.scene.objects) 
            )

def poll_emitter(self, object):
    """poll fct  for bpy.context.scene.scatter5.emitter prop"""

    dprint("PROP_FCT: poll 'scat_scene.emitter'")

    #don't poll if context object is not compatible
    return is_correct_emitter(object) 

def handler_emitter_check():
    """depsgraph: check emitter prop workflow"""

    emitter = bpy.context.scene.scatter5.emitter

    #remove emitter if somehow user deleted it, or (somehow) set it to wrong object type
    if emitter:
        if not is_correct_emitter(emitter):
            dprint("HANDLER: 'scatter5_depsgraph' -> 'handler_emitter_check'")
            bpy.context.scene.scatter5.emitter = None 

    return None

def handler_emitter_if_pinned_mode():
    """depsgraph: automatically update emitter pointer to context.object if in pineed mode"""

    #don't update if the options is not enabled
    if (bpy.context.preferences.addons["Scatter5"].preferences.emitter_method!="pin"):
        return None 

    #don't update if no context object  
    a = bpy.context.object 
    if not a:
        return None 

    #don't update if context object is not compatible
    if not is_correct_emitter(a):
        return None  

    scat_scene = bpy.context.scene.scatter5
    if (not scat_scene.emitter_pinned):
        if (scat_scene.emitter != bpy.context.object):
            dprint("HANDLER: 'scatter5_depsgraph' -> 'handler_emitter_if_pinned_mode'")
            scat_scene.emitter = bpy.context.object

    return None

def handler_scene_emitter_cleanup():
    """depsgraph: clean up emitter objects that have been dupplicated (not instanced)"""


    emitters = [o for o in bpy.data.objects if len(o.scatter5.particle_systems)]
    for emitter in emitters:
        
        #if emitter no longer exists in any scene, then remove it!
        if not bool(emitter.users_scene):
            for p in emitter.scatter5.particle_systems:
                p.remove_psy()
            continue 

        #Dupplicate Emitter == Clean Particle System That do not belongs to correct emitter
        if (emitter.scatter5.particle_systems[0].scatter_obj.scatter5.original_emitter is not emitter) :
            dprint("HANDLER: 'handler_scene_emitter_cleanup'",depsgraph=True)
            emitter.scatter5.particle_systems.clear()
            break

    return None

def is_ready_for_scattering():
    """check if emitter is ok for scattering preset or biome"""
    
    scat_scene  = bpy.context.scene.scatter5
    emitter     = bpy.context.scene.scatter5.emitter

    if (emitter is None):
        return False
    if (emitter.name not in bpy.context.scene.objects):
        return False
    if (bpy.context.mode!="OBJECT"):
        return False

    return True


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


class SCATTER5_OT_active_as_emitter(bpy.types.Operator):

    bl_idname      = "scatter5.active_as_emitter"
    bl_label       = translate("Set Active Object as Scatter-Emitter Target")
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO'}

    def execute(self, context):

        if bpy.context.object is None: 
            return {'FINISHED'}

        scat_scene = bpy.context.scene.scatter5
        scat_scene.emitter = bpy.context.object

        return {'FINISHED'}
        

# class SCATTER5_OT_estimate(bpy.types.Operator):

#     bl_idname      = "scatter5.estimate"
#     bl_label       = translate("Estimate Particle Count/ Surface Area")
#     bl_description = ""
#     bl_options     = {'INTERNAL','UNDO'}

#     mode : bpy.props.StringProperty()

#     def execute(self, context):

#         scat_scene = bpy.context.scene.scatter5
#         emitter = scat_scene.emitter
#         emitters = [o for o in bpy.context.scene.objects if len(o.scatter5.particle_systems)]

#         if (self.mode=="surface"):
#             for e in emitters:
#                 e.scatter5.get_estimated_square_area()

#         elif (self.mode=="viewcount"):

#             #i'm not using get_estimated_particle_count() in this case, we have multiple psy to analyse and it's faster to do one loop in depsgraph
            
#             psydict = { f"scatter_obj : {p.name}":0 for e in emitters for p in e.scatter5.particle_systems}

#             for o in bpy.context.evaluated_depsgraph_get().object_instances:
#                 if (o.is_instance and o.parent.original.name in psydict ):
#                     psydict[o.parent.original.name]+=1

#             for e in emitters:
#                 for p in e.scatter5.particle_systems:
#                     p.estimated_particlecount = psydict[f"scatter_obj : {p.name}"]
            

#         elif (self.mode=="rendercount"):
#             for e in emitters:
#                 for p in e.scatter5.particle_systems:
#                     p.get_estimated_particle_count(state="RENDER",)

#         return {'FINISHED'}


classes = [

    SCATTER5_OT_active_as_emitter,
    #SCATTER5_OT_estimate, 
    
    ]