import bpy
from bpy.types import Panel


class EXTRAS_PT_ui(Panel):
    bl_label = "Extras"
    bl_idname = "EXTRAS_PT_ui"
    bl_category = "RBDLab"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False
        flow = layout.grid_flow(align=True)
        col = flow.column()

        col = layout.column(align=False, heading="Use Auto Smooth")
        col.use_property_decorate = False
        row = col.row(align=True)
        sub = row.row(align=True)
        sub.prop(bpy.context.scene.rbdlab_props, "use_auto_smooth", text='')
        sub = sub.row(align=True)
        sub.active = bpy.context.scene.rbdlab_props.use_auto_smooth
        sub.prop(bpy.context.scene.rbdlab_props, 'auto_smooth', text='')

        # gravity
        col.prop(context.scene, "use_gravity", text="Gravity")