import bpy
from bpy.types import Panel


class FRACTURE_PT_ui(Panel):
    bl_label = "Cell Fracture"
    bl_idname = "FRACTURE_PT_ui"
    bl_category = "RBDLab"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False
        flow = layout.grid_flow(align=True)

        obj = bpy.context.active_object
        objects = len(bpy.context.selected_objects)

        box = flow.box()
        col = box.column()
        col.label(text="Point Source")

        col.prop(bpy.context.scene.rbdlab_props, "rbdlab_cf_source", text="Source")

        col.prop(bpy.context.scene.rbdlab_props, "rbdlab_cf_source_limit", text="Max Chunks")
        col.prop(bpy.context.scene.rbdlab_props, "rbdlab_cf_noise", text="Noise")
        rowsub = col.row()
        rowsub.prop(bpy.context.scene.rbdlab_props, "rbdlab_cf_cell_scale", text="Scale")
        if obj and objects:
            if obj.type == 'MESH':
                col.enabled = True
            else:
                col.enabled = False

        flow = layout.grid_flow(align=True)
        box = flow.box()
        col = box.column()
        col.label(text="Recursive Shatter")

        col.prop(bpy.context.scene.rbdlab_props, "rbdlab_cf_recursion", text="Recursion")
        col.prop(bpy.context.scene.rbdlab_props, "rbdlab_cf_recursion_source_limit", text="Recursion Source Limit")
        col.prop(bpy.context.scene.rbdlab_props, "rbdlab_cf_recursion_clamp", text="Recursion Clamp")

        rowsub = col.row()
        rowsub.prop(bpy.context.scene.rbdlab_props, "rbdlab_cf_recursion_chance")
        rowsub = col.row()
        rowsub.prop(bpy.context.scene.rbdlab_props, "rbdlab_cf_recursion_chance_select", expand=True)
        if obj and objects:
            if obj.type == 'MESH':
                col.enabled = True
            else:
                col.enabled = False

        flow = layout.grid_flow(align=True)
        box = flow.box()
        col = box.column()
        col.label(text="Mesh Data")

        col.prop(bpy.context.scene.rbdlab_props, "rbdlab_cf_use_sharp_edges_apply")
        col.prop(bpy.context.scene.rbdlab_props, "rbdlab_cf_margin")
        if obj and objects:
            if obj.type == 'MESH':
                col.enabled = True
            else:
                col.enabled = False

        flow = layout.grid_flow(align=True)
        box = flow.box()
        col = box.column()
        col.label(text="Output Collection")
        if obj and objects:
            if obj.type == 'MESH':
                col.enabled = True
            else:
                col.enabled = False

        col = box.column(align=False, heading="Auto Name")
        col.use_property_decorate = False
        row = col.row(align=True)
        sub = row.row(align=True)
        sub.prop(bpy.context.scene.rbdlab_props, "optinoal_auto_name", text='')
        sub = sub.row(align=True)
        sub.prop(bpy.context.scene.rbdlab_props, "rbdlab_cf_collection_name", text='')
        sub.enabled = not bpy.context.scene.rbdlab_props.optinoal_auto_name

        col.prop(bpy.context.scene.rbdlab_props, "post_original", text="Original")
        big_col = layout.column()
        big_col.scale_y = 1.5
        big_col.operator("rbdlab.cellfracture", text="Fracture")
        if obj and objects:
            if obj.type == 'MESH':
                col.enabled = True
                big_col.enabled = True
            else:
                col.enabled = False
                big_col.enabled = False

        if 'Annotations' in bpy.data.grease_pencils and not bpy.context.scene.rbdlab_props.in_annotation_mode:
            if len(bpy.data.grease_pencils['Annotations'].layers) > 0:
                big_col.operator('gpencil.layer_annotation_remove', text='Clear Annotations')
