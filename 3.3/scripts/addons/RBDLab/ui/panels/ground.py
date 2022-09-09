import bpy
from bpy.types import Panel


class GROUND_PT_ui(Panel):
    bl_label = "Ground"
    bl_idname = "GROUND_PT_ui"
    bl_category = "RBDLab"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False
        flow = layout.grid_flow(align=True)
        col = flow.column()

        if 'Ground' not in bpy.context.scene.objects:
            col.operator("rbdlab.aground", text='Add Ground')
        else:
            ground = bpy.context.scene.objects['Ground']
            if ground:
                col.prop(ground.collision, 'friction_factor')
                col.prop(ground.collision, 'damping_factor')
                col.prop(ground.rigid_body, 'friction')