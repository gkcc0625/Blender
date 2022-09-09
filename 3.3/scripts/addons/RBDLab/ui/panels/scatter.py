import bpy
from bpy.types import Panel


class SCATTER_PT_ui(Panel):
    bl_label = "Scatter"
    bl_idname = "SCATTER_PT_ui"
    bl_category = "RBDLab"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False
        flow = layout.grid_flow(align=True)
        col = flow.column()

        valid_meshes = False
        good_objects = not [obj for obj in bpy.context.selected_objects if obj.type != 'MESH']
        particle_systems = [obj.particle_systems for obj in bpy.context.selected_objects if obj.particle_systems]

        if len(bpy.context.selected_objects) > 0 and good_objects:
            for obj in bpy.context.selected_objects:
                if obj.type == 'MESH' and obj.visible_get():
                    valid_meshes = True
        else:
            valid_meshes = False

        if valid_meshes:
            if particle_systems:
                if any([obj.particle_systems for obj in bpy.context.selected_objects if "Detail_Scatter" in obj.particle_systems]):
                    col.prop(bpy.context.scene.rbdlab_props, "particle_count", text="Detail")
                    col.prop(bpy.context.scene.rbdlab_props, "scatter_types_combobox", text="Detail Type")
                if any([obj.particle_systems for obj in bpy.context.selected_objects if "Secondary_Scatter" in obj.particle_systems]):
                    col.prop(bpy.context.scene.rbdlab_props, "particle_secondary_count", text="Secondary")

            col.operator('add.scatter', text='Scatter')
            col.enabled = True
        else:
            col.operator('add.scatter', text='Scatter')
            col.enabled = False