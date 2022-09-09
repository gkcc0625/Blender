import bpy, bmesh

from bpy.types import Operator
from .functions import (add_material,
                        set_active_collection_to_master_coll,
                        set_active_object,
                        deselect_all_objects,
                        select_object,
                        remove_special_chars_in_name,
                        remove_obj_by_name
                        )


def cell_fracture(obj, collection_name):
    deselect_all_objects()
    select_object(obj)
    set_active_object(obj)
    if 'PARTICLE_OWN' in bpy.context.scene.rbdlab_props.rbdlab_cf_source and len(obj.particle_systems) == 0:
        bpy.ops.add.scatter()
    # Cell Fracture Options:
    # source = {'PARTICLE_OWN'},
    # source_limit = 100,
    # source_noise = 0,
    # cell_scale = (1, 1, 1),
    # recursion = 0,
    # recursion_source_limit = 8,
    # recursion_clamp = 250,
    # recursion_chance = 0.25,
    # recursion_chance_select = 'SIZE_MIN',
    # use_smooth_faces = False,
    # use_sharp_edges = True,
    # use_sharp_edges_apply = True,
    # use_data_match = True,
    # use_island_split = True,
    # margin = 0.001,
    # material_index = 0,
    # use_interior_vgroup = False,
    # mass_mode = 'VOLUME',
    # mass = 1,
    # use_recenter = True,
    # use_remove_original = True,
    # collection_name = "",
    # use_debug_points = False,
    # use_debug_redraw = True,
    # use_debug_bool = False
    source = bpy.context.scene.rbdlab_props.rbdlab_cf_source
    source_limit = bpy.context.scene.rbdlab_props.rbdlab_cf_source_limit
    noise = bpy.context.scene.rbdlab_props.rbdlab_cf_noise
    scale = bpy.context.scene.rbdlab_props.rbdlab_cf_cell_scale
    recursion = bpy.context.scene.rbdlab_props.rbdlab_cf_recursion
    recursion_source_limit = bpy.context.scene.rbdlab_props.rbdlab_cf_recursion_source_limit
    recursion_clamp = bpy.context.scene.rbdlab_props.rbdlab_cf_recursion_clamp
    recursion_chance = bpy.context.scene.rbdlab_props.rbdlab_cf_recursion_chance
    recursion_chance_select = bpy.context.scene.rbdlab_props.rbdlab_cf_recursion_chance_select
    use_sharp_edges_apply = bpy.context.scene.rbdlab_props.rbdlab_cf_use_sharp_edges_apply
    # use_sharp_edges_apply = True  # parece que con objetos con shade smooth queda mejor asi que lo activo por defecto
    margin = bpy.context.scene.rbdlab_props.rbdlab_cf_margin

    if collection_name:
        set_active_collection_to_master_coll()
        bpy.ops.object.add_fracture_cell_objects(
            source=source,
            source_limit=source_limit,
            source_noise=noise,
            cell_scale=scale,
            recursion=recursion,
            recursion_source_limit=recursion_source_limit,
            recursion_clamp = recursion_clamp,
            recursion_chance=recursion_chance,
            recursion_chance_select=recursion_chance_select,
            use_sharp_edges_apply=use_sharp_edges_apply,
            margin=margin,
            material_index=1,
            use_interior_vgroup=1,
            collection_name=collection_name
        )

    # guardo su nombre de objeto original para poder hacer el per island
    for ob in bpy.context.selected_objects:
        ob['rbdlab_island'] = obj.name

    if bpy.context.scene.rbdlab_props.post_original == 'HIDE':
        obj.hide_set(True)
        obj.hide_render = True
    else:
        remove_obj_by_name(obj.name)
        bpy.context.scene.rbdlab_props.post_original = 'HIDE'
        
    deselect_all_objects()


class CELL_FRACTURE_OT_custom(Operator):
    bl_idname = "rbdlab.cellfracture"
    bl_label = "RBDLab Cell Fracture GUI"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if len(bpy.context.selected_objects) > 0:
            for obj in bpy.context.selected_objects:

                obj.name = remove_special_chars_in_name(obj.name)

                obj.hide_set(False)
                obj.hide_render = False

                white = [0.8, 0.8, 0.8, 1.0]
                darkgrey = [0.03, 0.03, 0.03, 1.0]

                if len(obj.data.materials) == 0:
                    add_material(obj.name, 'Outer_mat', white)
                    add_material(obj.name, 'Inner_mat', darkgrey)
                if len(obj.data.materials) == 1:
                    add_material(obj.name, 'Inner_mat', darkgrey)

                if bpy.context.scene.rbdlab_props.optinoal_auto_name:
                    collection_name = obj.name
                else:
                    collection_name = bpy.context.scene.rbdlab_props.rbdlab_cf_collection_name
                    if not collection_name:
                        self.report({'WARNING'}, 'Output Collection Name is mandatory!')
                        return {'CANCELLED'}

                cell_fracture(obj, collection_name)

                if not bpy.context.scene.rbdlab_props.target_collection:
                    bpy.context.scene.rbdlab_props.target_collection = collection_name

            bpy.context.scene.rbdlab_props.rbdlab_cf_collection_name = ''
            deselect_all_objects()
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, 'No Selected objects!')
            return {'CANCELLED'}
