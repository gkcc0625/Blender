import bpy
from bpy.types import Panel


class TARGET_COLL_PT_ui(Panel):
    bl_idname = "TARGET_COLL_PT_ui"
    bl_label = "Target Collection"
    bl_category = "RBDLab"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False
        flow = layout.grid_flow(align=True)
        col = flow.column()

        col.prop_search(bpy.context.scene.rbdlab_props, "target_collection", bpy.data, "collections", text='Target')
        col.prop(bpy.context.scene.rbdlab_props, "show_boundingbox", text='Bounding Box')