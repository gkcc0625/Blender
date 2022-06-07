import bpy
from bpy.types import Panel
from ...core.functions import have_rigidbodies_in_target_collection


class CHIPPING_PT_ui(Panel):
    bl_idname = "CHIPPING_PT_ui"
    bl_label = "Chipping"
    bl_category = "RBDLab"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False
        flow = layout.grid_flow(align=True)
        col = flow.column()

        col.prop(bpy.context.scene.rbdlab_props, "size_delimiter", text="Select Small Chunks")

        display = flow.column()
        display.prop(bpy.context.scene.rbdlab_props, "chunks_selected", text="Selected")
        display.active = False

        col = flow.column()
        col.operator("chipping.coll", text='Convert to Chipping')
        if bpy.context.scene.rbdlab_props.chunks_selected > 0:
            col.active = True
        else:
            col.active = False
