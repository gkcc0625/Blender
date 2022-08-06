
#####################################################################################################
#
# ooooooooooooo                                        o8o
# 8'   888   `8                                        `"'
#      888       .ooooo.  oooo d8b oooo d8b  .oooo.   oooo  ooo. .oo.
#      888      d88' `88b `888""8P `888""8P `P  )88b  `888  `888P"Y88b
#      888      888ooo888  888      888      .oP"888   888   888   888
#      888      888    .o  888      888     d8(  888   888   888   888
#     o888o     `Y8bod8P' d888b    d888b    `Y888""8o o888o o888o o888o
#
#####################################################################################################


import bpy
import bmesh
from mathutils import Matrix, Vector

from .. resources.icons import cust_icon
from .. resources.translate import translate

from .. import utils



# oooooooooo.    o8o                      oooo                                                                            .
# `888'   `Y8b   `"'                      `888                                                                          .o8
#  888      888 oooo   .oooo.o oo.ooooo.   888   .oooo.    .ooooo.   .ooooo.  ooo. .oo.  .oo.    .ooooo.  ooo. .oo.   .o888oo
#  888      888 `888  d88(  "8  888' `88b  888  `P  )88b  d88' `"Y8 d88' `88b `888P"Y88bP"Y88b  d88' `88b `888P"Y88b    888
#  888      888  888  `"Y88b.   888   888  888   .oP"888  888       888ooo888  888   888   888  888ooo888  888   888    888
#  888     d88'  888  o.  )88b  888   888  888  d8(  888  888   .o8 888    .o  888   888   888  888    .o  888   888    888 .
# o888bood8P'   o888o 8""888P'  888bod8P' o888o `Y888""8o `Y8bod8P' `Y8bod8P' o888o o888o o888o `Y8bod8P' o888o o888o   "888"
#                               888
#                              o888o
 


def add_displace_modifier(o, name="", texture_data=None):
    """create a new displace modifier"""
    
    m = o.modifiers.get(name)
    if m is None:
        m = o.modifiers.new(name=name,type="DISPLACE")

    if texture_data:
        m.texture = texture_data

    return m  


order = ["Scatter5 Displace img-uv","Scatter5 Displace noise 01","Scatter5 Displace noise 02"]



class SCATTER5_OP_create_displace_dialog(bpy.types.Operator):

    bl_idname  = "scatter5.create_displace_dialog"
    bl_label   = translate("Please choose a Heightmap from Image-Data.")
    bl_options = {'REGISTER', 'INTERNAL','UNDO'}

    create : bpy.props.BoolProperty()

    def execute(self, context):

        rm, ro, rs = utils.override_utils.set_mode(mode="OBJECT")

        img = bpy.context.scene.scatter5.displace_img
        if not img:
            return {'FINISHED'}

        if self.create:
            #find plane size ration from image
            if img.size[1] == 0:
                  ratio = 1
            else: ratio = img.size[0]/img.size[1]
            o = utils.create_utils.subdivided_plane(subdiv=7,ratio=ratio)
        else: 
            o = bpy.context.scene.scatter5.emitter

        name = "Scatter5 Displace img-uv"
        t = utils.create_utils.texture_data(name=name,image_data=img)
        m = add_displace_modifier(o, name, texture_data=t)
        m.texture_coords = "UV"
        m.show_expanded = False

        utils.mod_utils.order_by_names(o,names=order)
        utils.override_utils.set_mode(mode=rm, active=ro, selection=rs)

        #UNDO_PUSH 
        bpy.ops.ed.undo_push(message=translate("Image displacement"))

        return {'FINISHED'}

    def invoke(self, context, event):
        return bpy.context.window_manager.invoke_props_dialog(self)

    def draw(self, context):

        layout = self.layout
        layout.prop(bpy.context.scene.scatter5,"displace_img",text='')

        return None



class SCATTER5_OT_add_displace(bpy.types.Operator):

    bl_idname = "scatter5.add_displace"
    bl_label = translate("Add procedural displacement")
    bl_description = translate("add a procedural displacement to the emitter object.")

    name : bpy.props.StringProperty()

    def execute(self, context):

        emitter = bpy.context.scene.scatter5.emitter

        if emitter:

            rm, ro, rs = utils.override_utils.set_mode(mode="OBJECT")

            t = utils.create_utils.texture_data(name=self.name,type="CLOUDS")
            m = add_displace_modifier(emitter, self.name, texture_data=t)
            m.show_expanded = False

            if self.name.endswith("01"):
                m.strength    = 5
                t.noise_scale = 10
                t.noise_depth = 2

            elif self.name.endswith("02"):
                m.strength    = 0.3
                t.noise_scale = 0.5
                t.noise_depth = 4

            utils.mod_utils.order_by_names(emitter,names=order)

            utils.override_utils.set_mode(mode=rm, active=ro, selection=rs)

        #UNDO_PUSH 
        bpy.ops.ed.undo_push(message=translate("Add Displacement"))

        return {'FINISHED'}



class SCATTER5_OT_remove_displace(bpy.types.Operator):

    bl_idname = "scatter5.remove_displace"
    bl_label = translate("Remove displacement")
    bl_description = translate("Remove displacement")

    name : bpy.props.StringProperty()

    def execute(self, context):

        emitter = bpy.context.scene.scatter5.emitter

        if emitter:
            m = emitter.modifiers.get(self.name)

            if m:
                emitter.modifiers.remove(m)

        #UNDO_PUSH 
        bpy.ops.ed.undo_push(message=translate("Remove Displacement"))

        return {'FINISHED'}




#    ooooooooo.                                                  oooo
#    `888   `Y88.                                                `888
#     888   .d88'  .ooooo.  ooo. .oo.  .oo.    .ooooo.   .oooo.o  888 .oo.
#     888ooo88P'  d88' `88b `888P"Y88bP"Y88b  d88' `88b d88(  "8  888P"Y88b
#     888`88b.    888ooo888  888   888   888  888ooo888 `"Y88b.   888   888
#     888  `88b.  888    .o  888   888   888  888    .o o.  )88b  888   888
#    o888o  o888o `Y8bod8P' o888o o888o o888o `Y8bod8P' 8""888P' o888o o888o


#New algo


def grid_bisect(o, subdiv_x=7, subdiv_y=7, subdiv_z=0,):
    """automatic bpy.ops.mesh.bisect(), done on global space, function for edit mode"""

    #get global bounding box coords and 

    bbs = [o.matrix_world @ Vector((bb)) for bb in bpy.context.object.bound_box]

    #fint the 2d bounding box coord we need 

    x = [b[0] for b in bbs]
    y = [b[1] for b in bbs]
    z = [b[2] for b in bbs]

    #find the plane tris

    def generate_planes(axis_min, axis_max, axis=0, subdiv=10, ):
        dist = (axis_max-axis_min)/subdiv
        for i in range(1,subdiv):
            yield (axis_min+(dist*i),axis_min,0) if (axis==0) else (axis_min,axis_min+(dist*i),0) if (axis==1) else (axis_min,0,axis_min+(dist*i))
    
    #proceed to bissections

    if subdiv_x!=0:                
        for plane in generate_planes(min(x), max(x), axis=0, subdiv=subdiv_x, ):
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.bisect(plane_co=plane, plane_no=(1,0,0),)
    
    if subdiv_y!=0:    
        for plane in generate_planes(min(y), max(y), axis=1, subdiv=subdiv_y, ):
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.bisect(plane_co=plane, plane_no=(0,1,0),)

    if subdiv_z!=0:    
        for plane in generate_planes(min(z), max(z), axis=2, subdiv=subdiv_z, ):
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.bisect(plane_co=plane, plane_no=(0,0,1),)

    return None 


class SCATTER5_OT_grid_bisect(bpy.types.Operator):

    bl_idname = "scatter5.grid_bisect"
    bl_label = translate("Grid Bisect")
    bl_description = translate("This operator will bissect your active object in a grid pattern. It will create a grid topology on your mesh, and this is handy for adding deformation easily or painting weight anywhere.")
    bl_options =  {'REGISTER', 'UNDO'} #Active Operator

    subdiv_x : bpy.props.IntProperty( name="Division X", default=10, soft_min=3, soft_max=20, )
    subdiv_y : bpy.props.IntProperty( name="Division Y", default=10, soft_min=3, soft_max=20, )
    subdiv_z : bpy.props.IntProperty( name="Division Z", default=0, soft_min=3, soft_max=20, )

    def execute(self, context):
        
        rm, ro, rs = utils.override_utils.set_mode(mode="EDIT_MESH")

        grid_bisect(o=context.object, subdiv_x=self.subdiv_x, subdiv_y=self.subdiv_y, subdiv_z=self.subdiv_z,)
        bpy.context.space_data.overlay.show_overlays = True
        bpy.context.space_data.overlay.show_wireframes = True
        
        utils.override_utils.set_mode(mode=rm, active=ro, selection=rs, )
        
        return {'FINISHED'}



#    .oooooo.   oooo
#   d8P'  `Y8b  `888
#  888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
#  888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
#  888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
#  `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#   `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'



classes = [
        
        SCATTER5_OP_create_displace_dialog,
        SCATTER5_OT_add_displace,
        SCATTER5_OT_remove_displace,

        SCATTER5_OT_grid_bisect,

    ]


def register():

    for cls in reversed(classes):
        bpy.utils.register_class(cls)

    return None


def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    return None



#if __name__ == "__main__":
#    register()