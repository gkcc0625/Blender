import bpy
from bpy.types import Panel


class ACETONE_PT_ui(Panel):
    bl_label = "Acetone"
    bl_idname = "ACETONE_PT_ui"
    bl_parent_id = "CONSTRAINTS_PT_ui"
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


        col.operator("acetone.addhelper", text='Add Helper')
        col.operator("acetone.record", text='Recording')
        col.operator("acetone.clean", text='Clear')
