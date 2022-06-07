import bpy
from bpy.types import Panel


class EXPLODE_PT_ui(Panel):
    bl_idname = "EXPLODE_PT_ui"
    bl_label = "Explode Visualization"
    bl_category = "RBDLab"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False
        flow = layout.grid_flow(align=True)
        col = flow.column()

        col = col.column()
        big_col = col.column()
        big_col.scale_y = 1.5

        if not bpy.context.scene.rbdlab_props.exploding:
            big_col.operator("explode.start", text="Start Explode")
        else:
            col.prop(bpy.context.scene.rbdlab_props, "colorize", text='Colorize')
            col.prop(bpy.context.scene.rbdlab_props, "explode_slider", text='Amount')
            col.operator("explode.restart", text="Well, let's start again")
            big_col.operator("explode.end", text="End Explode")