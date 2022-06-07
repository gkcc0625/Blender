import bpy
from bpy.types import Panel
from ...core.functions import have_constraint_in_target_collection


class CONSTRAINTS_PT_ui(Panel):
    bl_label = "Constraints"
    bl_idname = "CONSTRAINTS_PT_ui"
    bl_category = "RBDLab"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False
        flow = layout.grid_flow(align=True)
        col = flow.column()

        col.prop(bpy.context.scene.rbdlab_props, "glue_island_or_default", text="Per islands")
        col.prop(bpy.context.scene.rbdlab_props, "breakable", text="Breakable")
        col.prop(bpy.context.scene.rbdlab_props, "glue_strength", text="Glue Strength")
        col.prop(bpy.context.scene.rbdlab_props, "override_iterations", text="Override Iterations")
        col.prop(bpy.context.scene.rbdlab_props, "iterations", text="Iterations")

        if not have_constraint_in_target_collection():
            col.operator("const.add", text='Add Glue Constraint')
        else:
            big_row = col.row()
            big_row.scale_y = 1.5
            big_row.operator("const.update", text='Update')
            col.operator("const.rm", text='Remove Glue Constraint')