import bpy
from bpy.types import Panel
from ...core.functions import have_particle_sytem_smoke, get_first_mesh_visible, get_constraints_from_obj


class PARTICLES_PT_smoke(Panel):
    bl_label = "Smoke"
    bl_idname = "PARTICLES_PT_smoke"
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

        if not have_particle_sytem_smoke():
            obj = get_first_mesh_visible()
            if obj:
                const = get_constraints_from_obj(obj)
                if const:
                    col.prop(context.scene.rbdlab_props, 'ps_smoke_from')
            col.operator("smoke.add", text="Emit From Current Frame")
        else:
            ps_name = bpy.context.scene.rbdlab_props.target_collection + "_Smoke"
            col.prop(bpy.data.particles[ps_name], 'count')
            col.prop(bpy.data.particles[ps_name], 'frame_start')
            col.prop(bpy.data.particles[ps_name], 'frame_end')
            col.prop(bpy.data.particles[ps_name], 'lifetime')
            col.prop(bpy.data.particles[ps_name], 'emit_from')
            col.prop(bpy.data.particles[ps_name], 'normal_factor')
            col.prop(bpy.data.particles[ps_name], 'object_align_factor')
            col.prop(bpy.data.particles[ps_name], 'factor_random', text='Randomize')
            col.prop(bpy.data.particles[ps_name], 'render_type', text='Render As')
            col.prop(bpy.context.scene.rbdlab_props, "smoke_density", text="Smoke Density")
            col.operator("smoke.rm", text="Remove Smoke")