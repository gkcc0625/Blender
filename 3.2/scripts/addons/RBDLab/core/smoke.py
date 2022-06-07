import bpy

from bpy.types import Operator
from .functions import (
    deselect_all_objects,
    get_first_mesh_visible,
    select_object,
    set_active_object,
    create_particle_system,
    particle_system_remove,
    add_driver,
    select_chunks_with_break_constraints,
    copy_particle_system_to_selected_objects,
    get_constraints_from_obj,
)


class SMOKE_OT_add(Operator):
    bl_idname = "smoke.add"
    bl_label = "Add Smoke"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        coll_name = bpy.context.scene.rbdlab_props.target_collection
        if coll_name:
            deselect_all_objects()
            ps_name = coll_name + '_Smoke'
            modifier_name = 'Fluid'
            obj = get_first_mesh_visible()
            if obj:
                set_active_object(obj)

                if bpy.context.scene.rbdlab_props.ps_smoke_from == 'BROKEN':
                    select_chunks_with_break_constraints(coll_name)
                else:
                    for ob in bpy.data.collections[coll_name].objects:
                        if ob.type == 'MESH' and ob.visible_get():
                            select_object(ob)

                if ps_name not in obj.particle_systems:
                    ps_type = bpy.context.scene.rbdlab_props.ps_smoke_type_combobox
                    dps_size_detail = 0.025
                    v_group = 'Interior'
                    normal = 1
                    randomize = 2
                    rotation = True
                    random_phase = 2
                    dynamic = True
                    particle_scale = 0.1
                    p_random = 1
                    # lifetime = bpy.context.scene.frame_end
                    lifetime = 8
                    count = bpy.context.scene.rbdlab_props.smoke_count

                # PROPAGATE PARTICLES:

                create_particle_system(
                    obj.particle_systems.find(ps_name),
                    obj,
                    ps_name,
                    ps_type,
                    dps_size_detail,
                    lifetime,
                    count,
                    v_group,
                    normal,
                    randomize,
                    rotation,
                    random_phase,
                    dynamic,
                    None,
                    particle_scale,
                    p_random,
                    None
                )

                if modifier_name not in obj.modifiers:
                    bpy.ops.object.modifier_add(type='FLUID')
                    obj.modifiers[modifier_name].name = modifier_name
                    obj.modifiers[modifier_name].fluid_type = 'FLOW'
                    obj.modifiers[modifier_name].flow_settings.flow_type = 'SMOKE'
                    obj.modifiers[modifier_name].flow_settings.flow_behavior = 'INFLOW'
                    obj.modifiers[modifier_name].flow_settings.flow_source = 'PARTICLES'
                    obj.modifiers[modifier_name].flow_settings.use_initial_velocity = True
                    obj.modifiers[modifier_name].flow_settings.particle_system = obj.particle_systems[ps_name]

                if len(bpy.context.selected_objects) > 1:
                    bpy.ops.object.modifier_copy_to_selected(modifier=modifier_name)
                    # copy_particle_system_to_selected_objects(ps_name)
                    add_driver(modifier_name)
                else:
                    const = get_constraints_from_obj(obj)
                    if const:
                        particle_system_remove(ps_name)
                        self.report({'WARNING'}, 'No constraint breaking was detected, therefore no particles will be emitted!')

            deselect_all_objects()
        else:
            self.report({'WARNING'}, 'Target Collection is Empty!')
            return {'CANCELLED'}

        return {'FINISHED'}


class SMOKE_OT_rm(Operator):
    bl_idname = "smoke.rm"
    bl_label = "Remove Smoke"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        collection_name = bpy.context.scene.rbdlab_props.target_collection

        if collection_name:
            deselect_all_objects()
            ps_name = collection_name + '_Smoke'
            particle_system_remove(ps_name)

            for obj in bpy.data.collections[collection_name].objects:
                if obj.type == 'MESH' and obj.visible_get():
                    for mod in obj.modifiers:
                        if mod.type == 'FLUID':
                            obj.modifiers.remove(mod)
        else:
            self.report({'WARNING'}, 'Target Collection is Empty!')
            return {'CANCELLED'}

        return {'FINISHED'}
