import bpy
import re
import os
import bmesh

###########################################################################
# BASIC FUNCTIONS
###########################################################################


def enter_object_mode():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def enter_edit_mode():
    if bpy.context.mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')


def select_object(ob):
    obj = None
    if isinstance(ob, str):
        if ob in bpy.context.view_layer.objects:
            obj = bpy.context.view_layer.objects[ob]
    elif isinstance(ob, bpy.types.Object):
        if ob.name in bpy.context.view_layer.objects:
            obj = ob
    if obj:
        obj.select_set(True)


def deselect_object(ob):
    ob.select_set(False)


def deselect_all_objects_no_meshes():
    for obj in bpy.context.selected_objects:
        if obj.type != 'MESH':
            deselect_object(obj)


def set_active_object(obj):
    if not isinstance(obj, bpy.types.Object):
        if isinstance(obj, str):
            if obj in bpy.context.scene.objects:
                obj = bpy.context.scene.objects.get(obj)
            else:
                obj = False
                print(obj, 'not avalidable in bpy.context.scene.objects!')
    if obj:
        bpy.context.view_layer.objects.active = obj


def deselect_all_objects():
    bpy.ops.object.select_all(action='DESELECT')


def encode_string(text):
    return text.replace(' ', '#').upper()


def decode_string(text):
    return text.replace('#', ' ').title()


def hide_collection_in_viewport(coll_name):
    if coll_name in bpy.data.collections:
        layer_collection = bpy.context.view_layer.layer_collection.children[coll_name]
        bpy.context.view_layer.active_layer_collection = layer_collection
        bpy.context.view_layer.active_layer_collection.hide_viewport = True


def unhide_collection_in_viewport(coll_name):
    if coll_name in bpy.data.collections:
        layer_collection = bpy.context.view_layer.layer_collection.children[coll_name]
        bpy.context.view_layer.active_layer_collection = layer_collection
        bpy.context.view_layer.active_layer_collection.hide_viewport = False


def hide_collection_in_render(coll_name):
    if coll_name in bpy.data.collections:
        if coll_name in bpy.data.collections:
            bpy.data.collections[coll_name].hide_render = True


def unhide_collection_in_render(coll_name):
    if coll_name in bpy.data.collections:
        bpy.data.collections[coll_name].hide_render = False


def remove_obj_by_name(target_name):
    bpy.ops.object.select_all(action='DESELECT')
    if target_name in bpy.context.view_layer.objects:
        obj = bpy.context.view_layer.objects[target_name]
        select_object(obj)
        set_active_object(obj)
        bpy.ops.object.delete(use_global=False)


def remove_collection_by_name(coll_name, and_objects):
    coll = bpy.data.collections.get(coll_name)
    if coll:
        if and_objects:
            obs = [o for o in coll.objects if o.users == 1]
            while obs:
                bpy.data.objects.remove(obs.pop())

        bpy.data.collections.remove(coll)


def get_constraints_from_obj(obj):
    key_constraints = 'rbdlab_constraints'
    if key_constraints in obj:
        const_a = obj[key_constraints].split()
        return const_a
    else:
        return False


def get_array_data_from_obj(key, obj):
    if not isinstance(obj, bpy.types.Object):
        if isinstance(obj, str):
            if obj in bpy.context.scene.objects:
                obj = bpy.context.scene.objects.get(obj)
        else:
            return False

    if key in obj:
        data = obj[key].split()
        return data


def append_constraints_to_obj(obj, item):
    key_constraints = 'rbdlab_constraints'
    if key_constraints in obj:
        obj[key_constraints] += ' ' + item


def clear_constraints_to_obj(obj):
    key_constraints = 'rbdlab_constraints'
    if key_constraints in obj:
        del obj[key_constraints]


def select_pieces_mass_less_than(delimiter):
    masas = []
    bpy.ops.object.select_all(action='DESELECT')

    if bpy.context.scene.rbdlab_props.target_collection:
        deselect_all_objects()

        for obj in bpy.data.collections[bpy.context.scene.rbdlab_props.target_collection].objects:
            if obj.rigid_body and obj.visible_get():
                    if hasattr(obj.rigid_body, 'mass'):
                        m = obj.rigid_body.mass
                        masas.append(m)
                        if m <= delimiter:
                            select_object(obj)
                            bpy.context.view_layer.objects.active = obj

    bpy.context.scene.rbdlab_props.chunks_selected = len(bpy.context.selected_objects)


def select_pieces_dimensions_less_than(delimiter):
    d = []
    delimiter = delimiter/10
    bpy.ops.object.select_all(action='DESELECT')

    if bpy.context.scene.rbdlab_props.target_collection:
        deselect_all_objects()

        for obj in bpy.data.collections[bpy.context.scene.rbdlab_props.target_collection].objects:
            if obj.type == 'MESH' and obj.visible_get():
                s = obj.dimensions.x + obj.dimensions.y + obj.dimensions.z
                d.append(s)
                if s <= delimiter:
                    obj.select_set(True)
                    bpy.context.view_layer.objects.active = obj

    bpy.context.scene.rbdlab_props.chunks_selected = len(bpy.context.selected_objects)


def get_first_mesh_visible():
    if bpy.context.scene.rbdlab_props.target_collection in bpy.data.collections:
        # si es una coleccion de emptys va a hacer un stop iteration
        try:
            obj = next(obj for obj in bpy.data.collections[bpy.context.scene.rbdlab_props.target_collection].objects if obj.type == 'MESH' and obj.visible_get())
            if obj:
                return obj
        except StopIteration:
            pass


def have_rigidbodies_in_target_collection():
    obj = get_first_mesh_visible()
    if obj:
        if obj.rigid_body:
            return True
        else:
            return False


def get_fist_constraint():
    obj = get_first_mesh_visible()
    if obj:
        const = get_array_data_from_obj('rbdlab_constraints', obj)
        if const:
            return const


def have_constraint_in_target_collection():
    const = get_fist_constraint()
    if const:
        return True
    else:
        return False


def set_active_collection_to_master_coll():
    bpy.data.scenes[bpy.context.scene.name].view_layers[bpy.context.view_layer.name].active_layer_collection = bpy.context.scene.view_layers[bpy.context.view_layer.name].layer_collection


def get_first_and_last_keyframe_frame(obj):
    all_keyframes = []
    if obj.animation_data:
        for fc in obj.animation_data.action.fcurves:
            for key in fc.keyframe_points:
                all_keyframes.append(key.co.x)

    return [min(all_keyframes), max(all_keyframes)]


def inner_parts_to_facemap(facemap_name):
    
    obj = bpy.context.edit_object
    me = obj.data

    bm = bmesh.from_edit_mesh(me)
    for e in bm.edges:
        if not e.smooth:
            e.select = True

    bmesh.update_edit_mesh(me, False)
    bpy.ops.mesh.loop_multi_select(ring=False)
    
    if facemap_name not in bpy.context.object.face_maps:
        bpy.ops.object.face_map_add()
        bpy.context.object.face_maps[list(bpy.context.object.face_maps)[-1].name].name = facemap_name
        
    bpy.context.object.face_maps.active_index = bpy.context.object.face_maps.find(facemap_name)
    bpy.ops.object.face_map_assign()


def add_material(obj_name, mat_name, color4):
    activeObject = bpy.data.objects[obj_name]
    if mat_name not in bpy.data.materials:
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
    else:
        mat = bpy.data.materials[mat_name]
    if mat_name not in activeObject.data.materials:
        activeObject.data.materials.append(mat)
        activeObject.active_material_index = activeObject.data.materials.find(mat.name)
        activeObject.active_material.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = color4
        activeObject.active_material.diffuse_color = color4


def get_pack_islands(target_collection):
    pack_islands = {}
    for obj in bpy.data.collections[bpy.context.scene.rbdlab_props.target_collection].objects:
        if obj.type == 'MESH' and obj.visible_get():

            key_island = obj['rbdlab_island']
            chunk_name = obj.name

            if key_island in pack_islands:
                pack_islands[key_island].append(chunk_name)
            else:
                pack_islands[key_island] = [chunk_name]

    return pack_islands


def remove_special_chars_in_name(input_name):
    # input_name = ''.join(e for e in input_name if e.isalnum())
    input_name = re.sub('[^A-Za-z0-9]+', '_', input_name)
    return input_name



############################################################################################################################
# Particulas
############################################################################################################################


def have_particle_sytem_debris():
    obj = get_first_mesh_visible()
    if obj:
        ps_name = bpy.context.scene.rbdlab_props.target_collection + '_Debris'
        if ps_name in obj.particle_systems:
            return True
        else:
            return False


def have_particle_sytem_dust():
    obj = get_first_mesh_visible()
    if obj:
        ps_name = bpy.context.scene.rbdlab_props.target_collection + '_Dust'
        if ps_name in obj.particle_systems:
            return True
        else:
            return False


def have_particle_sytem_smoke():
    obj = get_first_mesh_visible()
    if obj:
        ps_name = bpy.context.scene.rbdlab_props.target_collection + '_Smoke'
        if ps_name in obj.particle_systems:
            return True
        else:
            return False


def next_seed():
    # rand seed
    bpy.context.scene.rbdlab_props.iter_seed = 0
    for obj in bpy.data.collections[bpy.context.scene.rbdlab_props.target_collection].objects:
        if obj.type == 'MESH' and obj.visible_get():
            for ps in obj.particle_systems:
                ps.seed = bpy.context.scene.rbdlab_props.iter_seed
                bpy.context.scene.rbdlab_props.iter_seed += 1


def add_driver(modifier_name):
    if len(bpy.context.selected_objects) > 0:
        for obj in bpy.context.selected_objects:
            if modifier_name in obj.modifiers:
                my_driver = obj.modifiers[modifier_name].flow_settings.driver_add("density")
                var = my_driver.driver.variables.new()
                var.name = 'smoke_density'
                var.type = 'SINGLE_PROP'
                my_driver.driver.expression = var.name
                var.targets[0].id_type = 'SCENE'
                var.targets[0].id = bpy.data.scenes[bpy.context.scene.name]
                var.targets[0].data_path = 'rbdlab_props.smoke_density'


def create_particle_system(
        slot,
        obj,
        ps_name,
        ps_type,
        dps_size,
        lifetime,
        count,
        v_group=None,
        normal=None,
        randomize=None,
        rotation=None,
        random_phase=None,
        dynamic=None,
        render_type=None,
        particle_scale=None,
        p_random=None,
        instance_collection=None
    ):
    if ps_name not in obj.particle_systems:
        set_active_object(obj)
        obj.modifiers.new(ps_name, type='PARTICLE_SYSTEM')
        part = obj.particle_systems[slot]
        part.settings.name = ps_name
        settings = part.settings
        settings.count = count
        settings.frame_start = bpy.context.scene.frame_current+0.0002
        settings.frame_end = bpy.context.scene.frame_current+5
        settings.lifetime = lifetime
        settings.emit_from = ps_type
        settings.display_size = dps_size
        settings.distribution = 'RAND'
        if normal:
            settings.normal_factor = normal
        if randomize:
            settings.factor_random = randomize
        if rotation:
            settings.use_rotations = rotation
        if random_phase:
            settings.phase_factor_random = random_phase
        if particle_scale:
            settings.particle_size = particle_scale
        if p_random:
            settings.size_random = p_random
        if dynamic:
            if hasattr(settings, 'use_dynamic_rotation'):
                settings.use_dynamic_rotation = dynamic
        if render_type:
            settings.render_type = render_type
        if v_group:
            part.vertex_group_density = v_group
        if instance_collection:
            settings.instance_collection = instance_collection


def particle_system_remove(ps_name):
    if len(bpy.data.collections[bpy.context.scene.rbdlab_props.target_collection].objects):
        for obj in bpy.data.collections[bpy.context.scene.rbdlab_props.target_collection].objects:
            if obj.type == 'MESH' and obj.visible_get():
                select_object(obj)
                set_active_object(obj)
                if ps_name in obj.particle_systems:
                    obj.particle_systems.active_index = bpy.context.active_object.particle_systems.find(ps_name)
                    bpy.ops.object.particle_system_remove()
    deselect_all_objects()


def copy_particle_system_to_selected_objects(ps_name):
    if ps_name in bpy.data.particles:
        obj_from = bpy.context.active_object
        for obj in bpy.context.selected_objects:
            if obj.name != obj_from.name:
                set_active_object(obj)
                bpy.ops.object.particle_system_add()
                obj.particle_systems[-1].name = ps_name
                ps = obj_from.particle_systems.get(ps_name)
                obj.particle_systems[-1].settings = ps.settings


def copy_modifier_to_selected_objects(mod_name):
    obj_from = bpy.context.active_object
    for obj in bpy.context.selected_objects:
        if obj.name != obj_from.name:
            set_active_object(obj)
            bpy.ops.object.modifier_add(type='FLUID')


def select_chunks_with_break_constraints(coll_name):
    threshold = 0.200000
    last_current_frame = bpy.context.scene.frame_current
    deselect_all_objects()
    for obj in bpy.data.collections[coll_name].objects:
        if obj.type == 'MESH' and obj.visible_get():
            constrainsts = get_array_data_from_obj('rbdlab_constraints', obj)
            if constrainsts:
                for const in constrainsts:
                    data = bpy.context.scene.objects[const]['rbdlab_const_dist'].split()
                    obj1 = data[0]
                    dist = float(data[1])
                    obj2 = data[2]
                    bpy.context.scene.frame_set(bpy.context.scene.frame_end)
                    current_dist = (bpy.context.scene.objects[obj1].matrix_world.translation - bpy.context.scene.objects[obj2].matrix_world.translation).length

                    if float("{:.6f}".format(current_dist)) - float("{:.6f}".format(dist)) > threshold:
                        select_object(obj1)
                        select_object(obj2)
            else:
                select_object(obj)

    bpy.context.scene.frame_current = last_current_frame


def append_collection(coll_name):
    # importo la coleccion de debris basicos:
    script_file = os.path.realpath(__file__)
    directory = os.path.dirname(script_file)
    fpath = directory.replace('core', 'libs')
    fname = os.path.join('debris_basics.blend', 'Collection')
    a_coll = coll_name
    if a_coll not in bpy.data.collections:
        bpy.ops.wm.append(filename=a_coll, directory=os.path.join(fpath, fname))
        hide_collection_in_viewport(coll_name)
