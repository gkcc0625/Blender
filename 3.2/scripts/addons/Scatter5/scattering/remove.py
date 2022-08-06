
#####################################################################################################
#
# ooooooooo.
# `888   `Y88.
#  888   .d88'  .ooooo.  ooo. .oo.  .oo.    .ooooo.  oooo    ooo  .ooooo.
#  888ooo88P'  d88' `88b `888P"Y88bP"Y88b  d88' `88b  `88.  .8'  d88' `88b
#  888`88b.    888ooo888  888   888   888  888   888   `88..8'   888ooo888
#  888  `88b.  888    .o  888   888   888  888   888    `888'    888    .o
# o888o  o888o `Y8bod8P' o888o o888o o888o `Y8bod8P'     `8'     `Y8bod8P'
#
#####################################################################################################



import bpy 

from .. resources.icons import cust_icon
from .. resources.translate import translate


#####################################################################################################



class SCATTER5_OT_remove_system(bpy.types.Operator):
    """Remove the selected particle system(s)"""
    bl_idname      = "scatter5.remove_system" #this operator is stupid, prefer to use `p.remove_psy()`
    bl_label       = ""
    bl_description = translate("Remove Particle-System(s) ?")

    undo_push     : bpy.props.BoolProperty(default=True) 
    emitter_name  : bpy.props.StringProperty(default="")  
    method        : bpy.props.StringProperty(default="selection")  #"selection" or "name"
    name          : bpy.props.StringProperty(default="")

    def execute(self, context):

        if (self.emitter_name=="") or (self.emitter_name not in bpy.context.scene.objects):
            return {'FINISHED'}
        
        #find emitter object 
        emitter  = bpy.data.objects[self.emitter_name]
        psys     = emitter.scatter5.particle_systems

        #defind what to del, need to be as memory adress will keep changing
        to_del = []
        if self.method == "selection":
            to_del = [p.name for p in psys if p.sel]
        elif self.method == "active":
            to_del = [p.name for p in psys if p.active]
        elif self.method == "name":
            to_del = [p.name for p in psys if p.name == self.name]

        for x in to_del:
            p = emitter.scatter5.particle_systems[x]
            p.remove_psy()

        #UNDO_PUSH 
        if self.undo_push:
            bpy.ops.ed.undo_push(message=translate("Remove Particle-System(s)"))
        self.undo_push = True 
        return {'FINISHED'}



#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'



classes = [

    SCATTER5_OT_remove_system,
    
    ]



#if __name__ == "__main__":
#    register()