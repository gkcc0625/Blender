import bpy
from .functions import enter_object_mode, deselect_all_objects, select_object, set_active_object, decode_string, \
    select_pieces_mass_less_than, select_pieces_dimensions_less_than, get_first_mesh_visible
from .constraints import update_values
from mathutils import Vector


###########################################################################
# UPDATES
###########################################################################


def riggidbodies_update(self, context):
    bpy.ops.rbd.add()


def update_constraints(self, context):
    if bpy.context.scene.rbdlab_props.target_collection:
        constraints_collection_name = bpy.context.scene.rbdlab_props.target_collection + '_GlueConstraints'
        if constraints_collection_name in bpy.data.collections:
            update_values(constraints_collection_name)


def part_count(self, context):
    for obj in bpy.context.selected_objects:
        if 'Detail_Scatter' in obj.modifiers:
            obj.particle_systems['Detail_Scatter'].settings.count = bpy.context.scene.rbdlab_props.particle_count


def part_second_count(self, context):
    for obj in bpy.context.selected_objects:
        if 'Secondary_Scatter' in obj.modifiers:
            obj.particle_systems['Secondary_Scatter'].settings.count = bpy.context.scene.rbdlab_props.particle_secondary_count


def show_emitter_viewport_update(self, context):
    if bpy.context.scene.rbdlab_props.target_collection:
        for obj in bpy.data.collections[bpy.context.scene.rbdlab_props.target_collection].objects:
            if obj.type == 'MESH' and obj.visible_get():
                obj.show_instancer_for_viewport = bpy.context.scene.rbdlab_props.show_emitter_viewport


def show_emitter_render_update(self, context):
    if bpy.context.scene.rbdlab_props.target_collection:
        for obj in bpy.data.collections[bpy.context.scene.rbdlab_props.target_collection].objects:
            if obj.type == 'MESH' and obj.visible_get():
                obj.show_instancer_for_render = bpy.context.scene.rbdlab_props.show_emitter_render


def mass_delimiter_by_mass_update(self, context):
    select_pieces_mass_less_than(bpy.context.scene.rbdlab_props.mass_delimiter)


def size_delimiter_update(self, context):
    select_pieces_dimensions_less_than(bpy.context.scene.rbdlab_props.size_delimiter)


def subdiv_update(self, context):
    objects = bpy.context.selected_objects
    if objects:
        deselect_all_objects()
        for obj in objects:
            select_object(obj)
            set_active_object(obj)
            if obj.type == 'MESH':
                obj.display_type = 'SOLID'
                enter_object_mode()
                if bpy.context.scene.rbdlab_props.subdivision_level > 0:
                    for obj in bpy.context.selected_objects:
                        set_active_object(obj)
                        obj.show_wire = True
                        bpy.ops.object.subdivision_set(level=bpy.context.scene.rbdlab_props.subdivision_level, relative=False)
                        for mod in obj.modifiers:
                            if mod.type == 'SUBSURF':
                                mod.show_only_control_edges = False
                                if bpy.context.scene.rbdlab_props.subdivision_simple:
                                    mod.subdivision_type = "CATMULL_CLARK"
                                else:
                                    mod.subdivision_type = "SIMPLE"
                else:
                    for obj in bpy.context.selected_objects:
                        obj.show_wire = False
                        set_active_object(obj)
                        bpy.ops.object.modifier_remove(modifier="Subdivision")


def scatter_type_update(self, context):
    obj = bpy.context.object
    if obj:
        enter_object_mode()
        if len(obj.particle_systems) > 0:
            bpy.data.particles["Detail_Scatter"].emit_from = bpy.context.scene.rbdlab_props.scatter_types_combobox


def target_collection_update(self, context):
    obj = get_first_mesh_visible()
    props = bpy.data.scenes[bpy.context.scene.name].rbdlab_props

    if obj:
        if obj.display_type == 'BOUNDS':
            bpy.context.scene.rbdlab_props.show_boundingbox = True
        else:
            bpy.context.scene.rbdlab_props.show_boundingbox = False

        if obj.rigid_body:

            if 'rbdlab_current_mass' in obj:
                props.avalidable_mass = obj['rbdlab_current_mass']
            else:
                props.avalidable_mass = props.get_default_properties('avalidable_mass')

            props.use_collision_margin = obj.rigid_body.use_margin
            props.collision_margin = obj.rigid_body.collision_margin
            props.rb_friction = obj.rigid_body.friction
            props.deactivation = obj.rigid_body.use_deactivation
            props.d_translation = obj.rigid_body.linear_damping
            props.d_rotation = obj.rigid_body.angular_damping

            key_constraints = 'rbdlab_constraints'
            if key_constraints in obj:
                const_a = obj[key_constraints].split()
                empty = const_a[0]
                props.breakable = bpy.data.objects[empty].rigid_body_constraint.use_breaking
                props.glue_strength = bpy.data.objects[empty].rigid_body_constraint.breaking_threshold
                props.override_iterations = bpy.data.objects[empty].rigid_body_constraint.use_override_solver_iterations
                props.iterations = bpy.data.objects[empty].rigid_body_constraint.solver_iterations
            else:
                props.breakable = props.get_default_properties('breakable')
                props.glue_strength = props.get_default_properties('glue_strength')
                props.override_iterations = props.get_default_properties('override_iterations')
                props.iterations = props.get_default_properties('iterations')
    else:
        # Defaults:
        # rbd
        props.avalidable_mass = props.get_default_properties('avalidable_mass')
        props.use_collision_margin = props.get_default_properties('use_collision_margin')
        props.collision_margin = props.get_default_properties('Collision Margin')  # Cuando la prop tiene name hay que suar su name
        props.rb_friction = props.get_default_properties('rb_friction')
        props.deactivation = props.get_default_properties('deactivation')
        props.d_translation = props.get_default_properties('d_translation')
        props.d_rotation = props.get_default_properties('d_rotation')
        # const
        props.breakable = props.get_default_properties('breakable')
        props.glue_strength = props.get_default_properties('glue_strength')
        props.override_iterations = props.get_default_properties('override_iterations')
        props.iterations = props.get_default_properties('iterations')





def auto_smooth_update(self, context):
    if bpy.context.scene.rbdlab_props.target_collection:
        props = bpy.data.scenes[bpy.context.scene.name].rbdlab_props
        deselect_all_objects()
        if props.use_auto_smooth:
            for obj in bpy.data.collections[bpy.context.scene.rbdlab_props.target_collection].objects:
                if obj.type == 'MESH' and obj.visible_get():
                    obj.data.auto_smooth_angle = props.auto_smooth
                    if props.auto_smooth != 0.000000:
                        obj.data.use_auto_smooth = True
                    else:
                        obj.data.use_auto_smooth = False
        else:
            for obj in bpy.data.collections[bpy.context.scene.rbdlab_props.target_collection].objects:
                if obj.type == 'MESH' and obj.visible_get():
                    obj.data.use_auto_smooth = False


#######################################################################################################################
# Explode casero
#######################################################################################################################


def get_objects_centroids():
    # hallar el centroid de la seleccion:
    objx = []  # <- aqui iremos guardando las coordenadas x de todos los objetos
    objy = []  # <- aqui iremos guardando las coordenadas y de todos los objetos
    objz = []  # <- aqui iremos guardando las coordenadas z de todos los objetos

    # el total de objetos:
    valid_objects = 0
    for obj in bpy.data.collections[bpy.context.scene.rbdlab_props.target_collection].objects:
        if obj.type == 'MESH' and obj.visible_get():
            objx.append(obj.location.x)
            objy.append(obj.location.y)
            objz.append(obj.location.z)
            valid_objects += 1

    total_objects = valid_objects

    # obtenemos el centroid:
    centroid = Vector((sum(objx) / total_objects, sum(objy) / total_objects, sum(objz) / total_objects))
    return [centroid, total_objects]


def explode_slider_update(self, context):
    if bpy.context.scene.rbdlab_props.exploding:
        deselect_all_objects()

        centroid, total_objects = get_objects_centroids()
        speed_decrementor = 20
        current_active = bpy.context.active_object

        for obj in bpy.data.collections[bpy.context.scene.rbdlab_props.target_collection].objects:
            if obj.type == 'MESH' and obj.visible_get():
                select_object(obj)
                set_active_object(obj)

                if 'exploded' not in obj:
                    obj['exploded'] = obj.location

                fuerza = bpy.context.scene.rbdlab_props.explode_slider
                initial_location = Vector((obj["exploded"]))
                direccion = obj.location - centroid
                # direccion.normalize() 
                obj.delta_location = initial_location + (direccion * (fuerza/speed_decrementor)) - obj.location

        set_active_object(current_active)
        deselect_all_objects()


def colorize_update(self, context):
    if context.scene.rbdlab_props.colorize:
        if bpy.context.space_data.shading.type != 'SOLID':
            bpy.context.space_data.shading.type = 'SOLID'
        bpy.context.space_data.shading.color_type = 'RANDOM'
    else:
        if bpy.context.space_data.shading.type == 'SOLID':
            if bpy.context.space_data.shading.color_type != 'MATERIAL':
                bpy.context.space_data.shading.color_type = 'MATERIAL'
        elif bpy.context.space_data.shading.type == 'WIREFRAME':
            if bpy.context.space_data.shading.color_type != 'OBJECT':
                bpy.context.space_data.shading.color_type = 'OBJECT'


def show_boundingbox_update(self, context):
    if bpy.context.scene.rbdlab_props.target_collection:
        enter_object_mode()
        for obj in bpy.data.collections[bpy.context.scene.rbdlab_props.target_collection].objects:
            if obj.type == 'MESH' and obj.visible_get():
                if bpy.data.scenes[bpy.context.scene.name].rbdlab_props.show_boundingbox:
                    obj.display_type = 'BOUNDS'
                else:
                    obj.display_type = 'TEXTURED'

