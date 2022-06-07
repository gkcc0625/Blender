import bpy
from bpy.types import Panel
from ...core.functions import have_particle_sytem_debris, have_particle_sytem_dust, have_particle_sytem_smoke


class PARTICLES_PT_ui(Panel):
    bl_label = "Particles"
    bl_idname = "PARTICLES_PT_ui"
    bl_category = "RBDLab"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout

        col = layout.column()
        layout.use_property_split = True
        layout.use_property_decorate = False

        if any([have_particle_sytem_debris(), have_particle_sytem_dust(), have_particle_sytem_smoke()]):
            col.label(text='Visualization')
            col.prop(bpy.context.scene.rbdlab_props, "show_emitter_viewport", text="Show Emitter Viewport")
            col.prop(bpy.context.scene.rbdlab_props, "show_emitter_render", text="Show Emitter Render")


