import bpy
from bpy.types import Panel
from ...core.functions import have_particle_sytem_debris, get_first_mesh_visible, get_constraints_from_obj


class PARTICLES_PT_debris(Panel):
    bl_label = "Debris"
    bl_idname = "PARTICLES_PT_debris"
    bl_parent_id = "PARTICLES_PT_ui"
    bl_category = "RBDLab"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        flow = layout.grid_flow(align=True)
        col = flow.column()

        if not have_particle_sytem_debris():
            obj = get_first_mesh_visible()
            if obj:
                const = get_constraints_from_obj(obj)
                if const:
                    col.prop(context.scene.rbdlab_props, 'ps_debris_from')
            col.operator("debris.add", text="Emit From Current Frame")
        else:
            ps_name = bpy.context.scene.rbdlab_props.target_collection + "_Debris"
            col.prop(bpy.data.particles[ps_name], 'count')
            col.prop(bpy.data.particles[ps_name], 'frame_start')
            col.prop(bpy.data.particles[ps_name], 'frame_end')
            col.prop(bpy.data.particles[ps_name], 'lifetime')
            col.prop(bpy.data.particles[ps_name], 'emit_from')
            col.prop(bpy.data.particles[ps_name], 'normal_factor')
            col.prop(bpy.data.particles[ps_name], 'object_align_factor')
            col.prop(bpy.data.particles[ps_name], 'factor_random', text='Randomize')
            col.prop(bpy.data.particles[ps_name], 'use_rotations')
            col.prop(bpy.data.particles[ps_name], 'phase_factor_random', text='Randomize Phase')
            col.prop(bpy.data.particles[ps_name], 'use_dynamic_rotation')
            col.prop(bpy.data.particles[ps_name], 'render_type', text='Render As')
            col.prop(bpy.data.particles[ps_name], 'particle_size')
            col.prop(bpy.data.particles[ps_name], 'size_random')
            col.prop(bpy.data.particles[ps_name], 'instance_collection')
            col.operator("debris.rm", text="Remove Debris")