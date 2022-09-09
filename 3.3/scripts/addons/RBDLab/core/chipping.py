import bpy
from bpy.types import Operator
from .functions import set_active_object, set_active_collection_to_master_coll, deselect_all_objects


class CHIPPING_OT_to_coll(Operator):
    bl_idname = "chipping.coll"
    bl_label = "Chipping to Collection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        coll_name = bpy.context.scene.rbdlab_props.target_collection
        if coll_name:
            objects = bpy.context.selected_objects
            if objects:

                set_active_collection_to_master_coll()
                new_coll_target_name = coll_name + '_Chippings'
                if new_coll_target_name not in bpy.data.collections:
                    new_coll_target = bpy.data.collections.new(new_coll_target_name)
                    bpy.context.scene.collection.children.link(new_coll_target)

                for obj in objects:
                    set_active_object(obj)
                    if obj.name not in bpy.data.collections[new_coll_target_name].objects:
                        bpy.data.collections[new_coll_target_name].objects.link(obj)
                        if obj.name in bpy.data.collections[coll_name].objects:
                            bpy.data.collections[coll_name].objects.unlink(obj)

        deselect_all_objects()
        self.report({'INFO'}, str(bpy.context.scene.rbdlab_props.chunks_selected) + ' Chunks moved to ' + new_coll_target_name + ' Collection.')
        return {'FINISHED'}
