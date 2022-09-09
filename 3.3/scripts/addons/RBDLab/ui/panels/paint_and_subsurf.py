import bpy
from bpy.types import Panel


class PAINT_AND_SUBSURF_PT_ui(Panel):
    bl_label = "Paint Tools"
    bl_idname = "PAINT_AND_SUBSURF_PT_ui"
    bl_category = "RBDLab"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        flow = layout.grid_flow(align=True)

        # subivision
        flow = layout.grid_flow(align=True)
        box = flow.box()
        col1 = box.column()

        col1.prop(bpy.context.scene.rbdlab_props, "subdivision_level", text="Subdivision")
        if bpy.context.scene.rbdlab_props.subdivision_level > 0:
            col1.prop(bpy.context.scene.rbdlab_props, "subdivision_simple", text="Catmull Clark")

        if bpy.context.scene.rbdlab_props.subdivision_level > 0:
            col1.operator('apply.subdivision', text='Apply')

        if len(bpy.context.selected_objects) == 1:
            obj = bpy.context.selected_objects[0]
            if obj.type == 'MESH':
                if bpy.context.mode == 'OBJECT':
                    col1.enabled=True
                else:
                    col1.enabled = False
            else:
                col1.enabled = False
        elif len(bpy.context.selected_objects) == 0:
            col1.enabled = False

        # paint
        flow = layout.grid_flow(align=True)
        box = flow.box()
        col2 = box.column()
        big_col2 = col2.column()
        big_col2.scale_y = 1.5

        if len(bpy.context.selected_objects) == 1:
            obj = bpy.context.selected_objects[0]
            if obj.type == 'MESH':
                if bpy.context.mode == 'PAINT_WEIGHT':
                    big_col2.operator('goto.weightpaint', text='End Paint')
                    col2.operator('clear.weightpaint', text='Clear')
                    big_col2.enabled = True
                    col2.enabled = True
                else:
                    big_col2.operator('goto.weightpaint', text='Start to Paint')
                if bpy.context.scene.rbdlab_props.subdivision_level > 0:
                    big_col2.enabled = False
                    col2.enabled = False
                else:
                    big_col2.enabled = True
                    col2.enabled = True
            else:
                big_col2.operator('goto.weightpaint', text='Start to Paint')
                big_col2.enabled = False
        else:
            big_col2.operator('goto.weightpaint', text='Start to Paint')
            big_col2.enabled = False

        # annotate
        flow = layout.grid_flow(align=True)
        box = flow.box()
        col3 = box.column()
        big_col3 = col3.column()
        big_col3.scale_y = 1.5

        if not bpy.context.scene.rbdlab_props.in_annotation_mode:
            text_annotation = 'Start to Annotation'
        else:
            text_annotation = 'End Annotation'

        big_col3.operator('goto.annotation', text=text_annotation)

        if bpy.context.scene.rbdlab_props.in_annotation_mode:
            col3.operator('gpencil.layer_annotation_remove', text='Clear')


        if len(bpy.context.selected_objects) > 0:
            if any([obj for obj in bpy.context.selected_objects if obj.type != 'MESH']):
                big_col3.enabled = False
                col3.enabled = False
            else:
                big_col3.enabled = True
                col3.enabled = True

