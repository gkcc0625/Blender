import bpy

from bpy.types import Operator
from .functions import deselect_all_objects, select_object, set_active_object, remove_collection_by_name, get_pack_islands
from .update_functions import colorize_update


class EXPLODE_OT_start(Operator):
    bl_idname = "explode.start"
    bl_label = "Start Explode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if bpy.context.scene.rbdlab_props.target_collection and len(bpy.data.collections[bpy.context.scene.rbdlab_props.target_collection].objects) > 0:
            colorize_update(self, context)

            bpy.context.scene.frame_current = bpy.context.scene.frame_start
            bpy.context.scene.rbdlab_props.show_boundingbox = False

            # isolate
            deselect_all_objects()
            for obj in bpy.data.collections[bpy.context.scene.rbdlab_props.target_collection].objects:
                select_object(obj)

            bpy.ops.view3d.localview(frame_selected=False)
            deselect_all_objects()
            # end isolate

            bpy.context.scene.rbdlab_props.exploding = True
        else:
            self.report({'WARNING'}, 'No valid objects in this collection!')
            return {'CANCELLED'}
        return {'FINISHED'}


class EXPLODE_OT_end(Operator):
    bl_idname = "explode.end"
    bl_label = "End Explode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.context.scene.rbdlab_props.explode_slider = 0

        if bpy.context.space_data.shading.type == 'SOLID':
            if bpy.context.space_data.shading.color_type != 'MATERIAL':
                bpy.context.space_data.shading.color_type = 'MATERIAL'
        elif bpy.context.space_data.shading.type == 'WIREFRAME':
            if bpy.context.space_data.shading.color_type != 'OBJECT':
                bpy.context.space_data.shading.color_type = 'OBJECT'

        if bpy.context.scene.rbdlab_props.target_collection:
            for obj in bpy.data.collections[bpy.context.scene.rbdlab_props.target_collection].objects:
                if obj.type == 'MESH' and obj.visible_get():
                    if 'exploded' in obj:
                        del obj['exploded']

            # isolate
            deselect_all_objects()
            for obj in bpy.data.collections[bpy.context.scene.rbdlab_props.target_collection].objects:
                select_object(obj)

            bpy.ops.view3d.localview(frame_selected=False)
            deselect_all_objects()
            # end isolate

            bpy.context.scene.rbdlab_props.exploding = False
        return {'FINISHED'}


class EXPLODE_OT_restart(Operator):
    bl_idname = "explode.restart"
    bl_label = "Restart Process"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        target_coll = bpy.context.scene.rbdlab_props.target_collection
        if target_coll:

            pack_islands = get_pack_islands(target_coll)

            deselect_all_objects()
            bpy.ops.explode.end()
            for k, v in pack_islands.items():
                obj = bpy.data.objects.get(k)
                if obj:
                    remove_collection_by_name(target_coll, True)
                    bpy.context.scene.rbdlab_props.target_collection = ""
                    obj.hide_set(False)
                    obj.hide_render = False
                    select_object(obj)
                    set_active_object(obj)
                    # si tiene particulas se las quito:
                    if len(obj.particle_systems) > 0:
                        for ps in obj.particle_systems:
                            obj.particle_systems.active_index = obj.particle_systems.find(ps.name)
                            bpy.ops.object.particle_system_remove()
                    obj.display_type = 'TEXTURED'
                else:
                    self.report({'WARNING'}, 'The original object: ' + k + ' not are avalidable!')
                    #return {'CANCELLED'}
        else:
            self.report({'WARNING'}, 'Not target colection!')
            return {'CANCELLED'}
        return {'FINISHED'}
