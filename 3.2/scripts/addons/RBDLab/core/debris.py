import os
import bpy

from bpy.types import Operator
from .functions import (
    deselect_all_objects,
    get_first_mesh_visible,
    select_object,
    set_active_object,
    create_particle_system,
    next_seed,
    particle_system_remove,
    append_collection,
    select_chunks_with_break_constraints,
    particle_system_remove,
    copy_particle_system_to_selected_objects,
    get_constraints_from_obj,
)


class DEBRIS_OT_add(Operator):
    bl_idname = "debris.add"
    bl_label = "Add Debris"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        coll_name = bpy.context.scene.rbdlab_props.target_collection
        if coll_name:
            deselect_all_objects()
            ps_name = coll_name + '_Debris'
            obj = get_first_mesh_visible()

            if obj:
                set_active_object(obj)
                if ps_name not in obj.particle_systems:
                    ps_type = bpy.context.scene.rbdlab_props.ps_debris_type_combobox
                    dps_size_detail = 0.025
                    lifetime = bpy.context.scene.frame_end
                    count = bpy.context.scene.rbdlab_props.debris_count
                    v_group = 'Interior'
                    normal = 1
                    randomize = 2
                    rotation = True
                    random_phase = 2
                    dynamic = True
                    render_type = 'COLLECTION'
                    particle_scale = 0.4
                    p_random = 1
                    instance_collection = 'Debris_Basics'

                    if ps_name not in obj.particle_systems:
                        append_collection(instance_collection)
                        instance_collection = bpy.data.collections[instance_collection]

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
                            render_type,
                            particle_scale,
                            p_random,
                            instance_collection,
                        )

                        # PROPAGATE PARTICLES:
                        if bpy.context.scene.rbdlab_props.ps_debris_from == 'BROKEN':
                            select_chunks_with_break_constraints(coll_name)
                        else:
                            # SIN ESTIMAR LOS QUE ROMPEN:
                            for obj in bpy.data.collections[coll_name].objects:
                                if obj.type == 'MESH' and obj.visible_get():
                                    select_object(obj)

                        if len(bpy.context.selected_objects) > 1:
                            # esto copia todos los systemas de particulas! cuidado
                            # bpy.ops.particle.copy_particle_systems(remove_target_particles=True, use_active=False)
                            copy_particle_system_to_selected_objects(ps_name)
                            next_seed()
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


class DEBRIS_OT_rm(Operator):
    bl_idname = "debris.rm"
    bl_label = "Remove Debris"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        collection_name = bpy.context.scene.rbdlab_props.target_collection

        if collection_name:
            deselect_all_objects()
            ps_name = collection_name + '_Debris'
            particle_system_remove(ps_name)
        else:
            self.report({'WARNING'}, 'Target Collection is Empty!')
            return {'CANCELLED'}

        return {'FINISHED'}
