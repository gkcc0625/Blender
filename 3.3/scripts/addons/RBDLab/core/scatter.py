import bpy
from bpy.types import Operator
from .functions import enter_object_mode, enter_edit_mode, set_active_object
import bmesh


def create_particle_system(slot, obj, ps_name, ps_type, dps_size, ps_count):
    obj.modifiers.new(ps_name, type='PARTICLE_SYSTEM')
    part = obj.particle_systems[slot]
    part.settings.name = ps_name
    settings = part.settings
    settings.emit_from = ps_type
    settings.physics_type = 'NO'
    settings.particle_size = 0.1
    settings.show_unborn = True
    settings.use_dead = True
    settings.frame_end = 1
    settings.count = ps_count
    settings.display_size = dps_size
    # settings.userjit = 1
    # settings.jitter_factor = 1.5
    settings.distribution = 'RAND'
    # random seed
    part.seed = list(bpy.context.scene.objects).index(obj)


class SCATTER_OT_object(Operator):
    bl_idname = "add.scatter"
    bl_label = "add scatter"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        enter_object_mode()
        ps_name = "Detail_Scatter"
        ps_secondary_name = "Secondary_Scatter"
        ps_detail_count = bpy.context.scene.rbdlab_props.particle_count
        ps_secondary_count = bpy.context.scene.rbdlab_props.particle_secondary_count
        vg_name = "paint"
        ps_type = "VOLUME"
        dps_size_detail = 0.025
        dps_size_secondary = 0.018

        # multi scatter para los objetos seleccionados:
        for obj in bpy.context.selected_objects:
            if obj:
                set_active_object(obj)
                if obj.type == 'MESH' and obj.visible_get():
                    if vg_name in obj.vertex_groups:
                        # determino si pintaron:
                        enter_edit_mode()
                        obj.vertex_groups.active_index = obj.vertex_groups.find('paint')
                        bpy.ops.mesh.select_all(action='DESELECT')
                        bpy.ops.object.vertex_group_select()

                        bm = bmesh.from_edit_mesh(obj.data)
                        selected_vertex = []
                        for v in bm.verts:
                            if v.select:
                                selected_vertex.append(v.co)

                        enter_object_mode()

                        if ps_name not in obj.particle_systems:
                            if len(selected_vertex):
                                create_particle_system(len(obj.particle_systems), obj, ps_name, ps_type, dps_size_detail, ps_detail_count)
                                obj.particle_systems[ps_name].vertex_group_density = vg_name
                            else:
                                bpy.context.active_object.particle_systems.active_index = bpy.context.active_object.particle_systems.find(ps_name)
                                bpy.ops.object.particle_system_remove()
                        else:
                            if len(selected_vertex) < 1:
                                bpy.context.active_object.particle_systems.active_index = bpy.context.active_object.particle_systems.find(ps_name)
                                bpy.ops.object.particle_system_remove()

                    if ps_secondary_name not in obj.particle_systems:
                        create_particle_system(len(obj.particle_systems), obj, ps_secondary_name, ps_type, dps_size_secondary, ps_secondary_count)

                    obj.display_type = 'WIRE'

                else:
                    self.report({'WARNING'}, 'Is necesary select one object!')

        return {'FINISHED'}


class ACCEPT_OT_scatter(Operator):
    bl_idname = "accept.scatter"
    bl_label = "Accept Scatter"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ps_name = "Detail_Scatter"
        obj = context.selected_objects
        if obj:
            obj = context.object
        obj.display_type = 'TEXTURED'
        bpy.data.particles[ps_name].display_size = 0

        return {'FINISHED'}