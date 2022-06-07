import bpy

from bpy.types import Operator
from .functions import deselect_all_objects, set_active_collection_to_master_coll


class GROUND_OT_add(Operator):
    bl_idname = "rbdlab.aground"
    bl_label = "Add ground"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if 'Ground' not in bpy.data.objects:
            set_active_collection_to_master_coll()
            bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD', location=(0, 0, -0.05), scale=(30, 30, 0.05))
            bpy.context.object.name = 'Ground'
            bpy.ops.rigidbody.object_add()
            bpy.context.object.rigid_body.type = 'PASSIVE'
            bpy.ops.object.modifier_add(type='COLLISION')
            bpy.context.object.collision.damping_factor = 0.7
            bpy.context.object.collision.friction_factor = 0.5
            bpy.context.object.collision.damping_random = 0.1
        deselect_all_objects()
        return {'FINISHED'}
