import bpy
from bpy.types import Operator
from .functions import set_active_object, select_object, deselect_all_objects


class SUBDIVISION_OT_surface(Operator):
    bl_idname = "apply.subdivision"
    bl_label = "Apply Subdivision modifier"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        objects = bpy.context.selected_objects
        if objects:
            deselect_all_objects()
            for obj in objects:
                select_object(obj)
                set_active_object(obj)
                bpy.ops.object.modifier_apply(modifier="Subdivision")
                obj.show_wire = False
                bpy.context.scene.rbdlab_props.subdivision_level = 0

        return {'FINISHED'}