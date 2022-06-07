import bpy
from bpy.types import Operator
from .functions import enter_object_mode, deselect_all_objects, decode_string, set_active_object, select_object, get_first_mesh_visible, set_active_collection_to_master_coll


def save_type_of_mass_in_obj(obj):
    if isinstance(obj, bpy.types.Object):
        obj['rbdlab_current_mass'] = bpy.context.scene.rbdlab_props.avalidable_mass


def update_values(obj):
    obj.rigid_body.enabled = bpy.context.scene.rbdlab_props.dynamic
    obj.rigid_body.use_deactivation = bpy.context.scene.rbdlab_props.deactivation
    obj.rigid_body.use_start_deactivated = bpy.context.scene.rbdlab_props.deactivation
    obj.rigid_body.linear_damping = bpy.context.scene.rbdlab_props.d_translation
    obj.rigid_body.angular_damping = bpy.context.scene.rbdlab_props.d_rotation
    obj.rigid_body.friction = bpy.context.scene.rbdlab_props.rb_friction
    obj.rigid_body.collision_shape = bpy.context.scene.rbdlab_props.collision_shape_combobox
    obj.rigid_body.use_margin = bpy.context.scene.rbdlab_props.use_collision_margin
    obj.rigid_body.collision_margin = bpy.context.scene.rbdlab_props.collision_margin


def my_settings_copy():
    # con chuleta por si otro dia necesito mas:
    attrs = (
        "type",
        # "kinematic",
        # "mass",
        "collision_shape",
        "use_margin",
        "collision_margin",
        "friction",
        # "restitution",
        "use_deactivation",
        "use_start_deactivated",
        # "deactivate_linear_velocity",
        # "deactivate_angular_velocity",
        "linear_damping",
        "angular_damping",
        # "collision_collections",
        # "mesh_source",
        # "use_deform",
        "enabled",
    )

    objects = bpy.context.selected_objects
    if objects:
        rb_from = bpy.context.object.rigid_body
        for obj in objects:
            save_type_of_mass_in_obj(obj)
            current_active = bpy.context.object
            rb_to = obj.rigid_body
            if obj == current_active:
                continue
            if rb_to and rb_from:
                for attr in attrs:
                    setattr(rb_to, attr, getattr(rb_from, attr))


class RBD_OT_update(Operator):
    bl_idname = "rbd.update"
    bl_label = "Rigid Bodies Update"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        enter_object_mode()
        coll_name = bpy.context.scene.rbdlab_props.target_collection
        if coll_name:
            deselect_all_objects()

            for obj in bpy.data.collections[coll_name].objects:
                if obj.type == 'MESH' and obj.visible_get():
                    select_object(obj)

            obj = get_first_mesh_visible()
            if obj:
                set_active_object(obj)
                if obj.rigid_body:
                    update_values(obj)
                    my_settings_copy()
                    bpy.ops.rigidbody.mass_calculate(material=decode_string(bpy.context.scene.rbdlab_props.avalidable_mass))
            else:
                self.report({'WARNING'}, 'No valid objects in this collection!')
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, 'Target Collection is Empty!')
            return {'CANCELLED'}

        bpy.context.scene.frame_current = bpy.context.scene.frame_start
        deselect_all_objects()
        return {'FINISHED'}


class RBD_OT_add(Operator):
    bl_idname = "rbd.add"
    bl_label = "Add Rigid Bodies"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        enter_object_mode()
        coll_name = bpy.context.scene.rbdlab_props.target_collection
        if coll_name:
            deselect_all_objects()

            if hasattr(bpy.context.scene.rigidbody_world, 'enabled'):
                if not bpy.context.scene.rigidbody_world.enabled:
                    bpy.context.scene.rigidbody_world.enabled = True

            for obj in bpy.data.collections[coll_name].objects:
                if obj.type == 'MESH' and obj.visible_get():
                    select_object(obj)

            obj = get_first_mesh_visible()
            if obj:
                if not obj.rigid_body:
                    set_active_object(obj)
                    bpy.ops.rigidbody.objects_add(type='ACTIVE')

                update_values(obj)
                my_settings_copy()

                bpy.ops.rigidbody.mass_calculate(material=decode_string(bpy.context.scene.rbdlab_props.avalidable_mass))

                # auto clean de objetos con masa 0:
                deselect_all_objects()
                for obj in bpy.data.collections[bpy.context.scene.rbdlab_props.target_collection].objects:
                    if obj.rigid_body and obj.visible_get():
                        if hasattr(obj.rigid_body, 'mass'):
                            save_type_of_mass_in_obj(obj)
                            m = obj.rigid_body.mass
                            if m <= 0:
                                select_object(obj)
                                set_active_object(obj)

                bpy.ops.object.delete(use_global=False)
                deselect_all_objects()
            else:
                self.report({'WARNING'}, 'No valid objects in this collection!')
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, 'Target Collection is Empty!')
            return {'CANCELLED'}

        bpy.context.scene.frame_current = bpy.context.scene.frame_start
        return {'FINISHED'}


class RBD_OT_rm(Operator):
    bl_idname = "rbd.remove"
    bl_label = "Remove Rigid Bodies"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        enter_object_mode()
        coll_name = bpy.context.scene.rbdlab_props.target_collection
        if coll_name:
            deselect_all_objects()

            for obj in bpy.data.collections[coll_name].objects:
                if obj.type == 'MESH' and obj.visible_get():
                    if obj.rigid_body:
                        # elimino sus contraints
                        bpy.ops.const.rm()
                        select_object(obj)
                        set_active_object(obj)
                        bpy.ops.rigidbody.object_remove()
                        if 'rbdlab_current_mass' in obj:
                            del obj['rbdlab_current_mass']

            deselect_all_objects()
        else:
            self.report({'WARNING'}, 'Target Collection is Empty!')
            return {'CANCELLED'}

        bpy.context.scene.frame_current = bpy.context.scene.frame_start
        return {'FINISHED'}


class RBD_OT_passive(Operator):
    bl_idname = "rbd.passive"
    bl_label = "Rigid Bodie Passive"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        coll_name = bpy.context.scene.rbdlab_props.target_collection
        if coll_name:
            enter_object_mode()
            objects = bpy.context.selected_objects
            if objects:
                bpy.ops.rigidbody.objects_add(type='PASSIVE')

                set_active_collection_to_master_coll()
                new_coll_target_name = coll_name + '_Passive'
                if new_coll_target_name not in bpy.data.collections:
                    new_coll_target = bpy.data.collections.new(new_coll_target_name)
                    bpy.context.scene.collection.children.link(new_coll_target)

                for obj in objects:
                    set_active_object(obj)
                    if obj.name not in bpy.data.collections[new_coll_target_name].objects:
                        bpy.data.collections[new_coll_target_name].objects.link(obj)
                        if obj.name in bpy.data.collections[coll_name].objects:
                            bpy.data.collections[coll_name].objects.unlink(obj)

                self.report({'INFO'}, str(len(bpy.context.selected_objects)) + ' Chunks moved to ' + new_coll_target_name + ' Collection.')
            else:
                self.report({'WARNING'}, 'First select chunks to make passive!')
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, 'Target Collection is Empty!')
            return {'CANCELLED'}

        deselect_all_objects()
        return {'FINISHED'}