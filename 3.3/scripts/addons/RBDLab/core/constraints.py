import bpy
from bpy.types import Operator
import collections


from .functions import select_object, deselect_all_objects, hide_collection_in_viewport, append_constraints_to_obj, \
    remove_obj_by_name, set_active_object, unhide_collection_in_viewport, \
    clear_constraints_to_obj, set_active_collection_to_master_coll, get_first_mesh_visible, get_pack_islands


def update_values(constraints_collection_name):
    
    for obj in bpy.data.collections[constraints_collection_name].objects:
        # override_iterations
        obj.rigid_body_constraint.use_override_solver_iterations = bpy.context.scene.rbdlab_props.override_iterations
        obj.rigid_body_constraint.solver_iterations = bpy.context.scene.rbdlab_props.iterations
        # breakeable
        obj.rigid_body_constraint.use_breaking = bpy.context.scene.rbdlab_props.breakable
        obj.rigid_body_constraint.breaking_threshold = bpy.context.scene.rbdlab_props.glue_strength

        if bpy.context.scene.rbdlab_props.breakable:
            obj.rigid_body_constraint.disable_collisions = False


def add_constraint(object1, object2, constraints_coll):
    if object1 != object2:
        con_obj = bpy.data.objects.new(bpy.context.scene.rbdlab_props.target_collection + "_GlueConstraint", None)
        con_obj.location = (object1.location + object2.location) / 2.0
        bpy.context.scene.collection.objects.link(con_obj)
        bpy.context.view_layer.objects.active = con_obj
        # con_obj.select_set(True)
        bpy.ops.rigidbody.constraint_add()
        con_obj.empty_display_type = 'ARROWS'
        con = con_obj.rigid_body_constraint
        con.type = 'FIXED'

        con.object1 = object1
        con.object2 = object2

        key_constraints = 'rbdlab_constraints'

        # IMPLEMENTACION DE QUE SOLO EMITA DESDE LOS CHUNKS QUE ESTIMO QUE SE ROMPIERON
        distance = (object1.matrix_world.translation - object2.matrix_world.translation).length
        con_obj['rbdlab_const_dist'] = object1.name + ' ' + str(distance) + ' ' + object2.name

        if key_constraints not in object1:
            object1[key_constraints] = con_obj.name
        else:
            append_constraints_to_obj(object1, con_obj.name)

        if key_constraints not in object2:
            object2[key_constraints] = con_obj.name
        else:
            append_constraints_to_obj(object2, con_obj.name)


        if con_obj.name in bpy.context.collection.objects:
            bpy.context.collection.objects.unlink(con_obj)

        bpy.data.collections[constraints_coll.name].objects.link(con_obj)


def create_constraints(self, constraints_collection_name):
    # prepare collection
    if constraints_collection_name not in bpy.data.collections:
        constraints_coll = bpy.data.collections.new(constraints_collection_name)
        bpy.context.scene.collection.children.link(constraints_coll)
    else:
        constraints_coll = bpy.data.collections[constraints_collection_name]

    # create constraints
    obj_act = bpy.context.active_object

    if obj_act:
        objs_sorted = [obj_act]
        objects_tmp = bpy.context.selected_objects

        last_obj = obj_act

        while objects_tmp:
            objects_tmp.sort(key=lambda o: (last_obj.location - o.location).length)
            last_obj = objects_tmp.pop(0)
            objs_sorted.append(last_obj)
        
        set_active_collection_to_master_coll()

        for i in range(1, len(objs_sorted)):
            add_constraint(objs_sorted[i - 1], objs_sorted[i], constraints_coll)

    update_values(constraints_collection_name)
    deselect_all_objects()
    hide_collection_in_viewport(constraints_collection_name)


class CONST_OT_update(Operator):
    bl_idname = "const.update"
    bl_label = "Constraints Update"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if bpy.context.scene.rbdlab_props.target_collection:
            target_coll_name = bpy.context.scene.rbdlab_props.target_collection
            constraints_collection_name = target_coll_name + '_GlueConstraints'
            if constraints_collection_name in bpy.data.collections:
                update_values(constraints_collection_name)
        else:
            self.report({'WARNING'}, 'Target Collection is Empty!')
            return {'CANCELLED'}

        bpy.context.scene.frame_current = bpy.context.scene.frame_start
        deselect_all_objects()
        return {'FINISHED'}


class CONST_OT_add(Operator):
    bl_idname = "const.add"
    bl_label = "Add Constraints"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if bpy.context.scene.rbdlab_props.target_collection:
            target_coll_name = bpy.context.scene.rbdlab_props.target_collection
            constraints_collection_name = target_coll_name + '_GlueConstraints'

            if constraints_collection_name in bpy.data.collections:
                update_values(constraints_collection_name)
            else:
                minimun = 0
                deselect_all_objects()
                ######################################################################################################
                # si voy por islas para crear los constraints
                ######################################################################################################
                if bpy.context.scene.rbdlab_props.glue_island_or_default:

                    pack_islands = get_pack_islands(target_coll_name)

                    deselect_all_objects()
                    for k, v in pack_islands.items():
                        for chunk in v:
                            obj = bpy.data.objects[chunk]
                            if hasattr(obj.rigid_body, 'type'):
                                select_object(obj)
                                set_active_object(obj)
                                minimun += 1

                        create_constraints(self, constraints_collection_name)
                else:
                    ######################################################################################################
                    # si van todos con constraints
                    ######################################################################################################
                    for obj in bpy.data.collections[bpy.context.scene.rbdlab_props.target_collection].objects:
                        if obj.type == 'MESH' and obj.visible_get():
                            if hasattr(obj.rigid_body, 'type'):
                                select_object(obj)
                                set_active_object(obj)
                                minimun += 1
                            else:
                                self.report({'WARNING'}, 'Is necessary that the objects in the collection, first have Rigid Bodies on them!')
                                return {'CANCELLED'}

                    if minimun < 2:
                        self.report({'WARNING'}, 'Is necessary minimun tow Rigid Bodies objects!')
                        return {'CANCELLED'}

                    create_constraints(self, constraints_collection_name)
        else:
            self.report({'WARNING'}, 'Target Collection is Empty!')
            return {'CANCELLED'}


        bpy.context.scene.frame_current = bpy.context.scene.frame_start

        return {'FINISHED'}


class CONST_OT_rm(Operator):
    bl_idname = "const.rm"
    bl_label = "Remove Constraints"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if bpy.context.scene.rbdlab_props.target_collection:
            constraints_collection_name = bpy.context.scene.rbdlab_props.target_collection + '_GlueConstraints'
            deselect_all_objects()

            if constraints_collection_name in bpy.data.collections:
                unhide_collection_in_viewport(constraints_collection_name)

                for obj in bpy.data.collections[constraints_collection_name].objects:
                    select_object(obj)
                    clear_constraints_to_obj(obj.rigid_body_constraint.object1)
                    clear_constraints_to_obj(obj.rigid_body_constraint.object2)

                set_active_object(bpy.data.collections[constraints_collection_name].objects[0])
                bpy.ops.object.delete(use_global=False)

                if len(bpy.data.collections[constraints_collection_name].objects) == 0:
                    bpy.data.collections.remove(bpy.data.collections[constraints_collection_name])

        else:
            self.report({'WARNING'}, 'Target Collection is Empty!')
            return {'CANCELLED'}

        bpy.context.scene.frame_current = bpy.context.scene.frame_start
        return {'FINISHED'}
