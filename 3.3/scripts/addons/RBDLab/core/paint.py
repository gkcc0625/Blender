import bpy
from bpy.types import Operator


class GOTO_OT_weight_paint(Operator):
    bl_idname = "goto.weightpaint"
    bl_label = "Go to weight paint"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'SOLID'

        bpy.ops.paint.weight_paint_toggle()
        obj = bpy.context.object

        obj.display_type = 'SOLID'

        if 'paint' not in obj.vertex_groups:
            bpy.ops.object.vertex_group_add()
            if obj.vertex_groups.find('paint') == -1:
                obj.vertex_groups[-1].name = 'paint'

        return {'FINISHED'}


class CLEAR_weight_paint(Operator):
    bl_idname = "clear.weightpaint"
    bl_label = "Clear wight paint"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = bpy.context.object
        obj.display_type = 'SOLID'

        if 'paint' in obj.vertex_groups:
            obj.vertex_groups.active_index = obj.vertex_groups.find('paint')
            bpy.ops.object.vertex_group_remove()

            bpy.ops.object.vertex_group_add()
            if obj.vertex_groups.find('paint') == -1:
                obj.vertex_groups[-1].name = 'paint'

        return {'FINISHED'}


class GOTO_OT_anotation_paint(Operator):
    bl_idname = "goto.annotation"
    bl_label = "Go to Anotation Paint"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        if not bpy.context.scene.rbdlab_props.in_annotation_mode:
            bpy.context.scene.rbdlab_props.in_annotation_mode = True
            las_active_tool = bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode, create=False).idname
            if las_active_tool:
                bpy.context.scene.rbdlab_props.las_active_tool = las_active_tool

            # sobreescribir el contexto:
            for window in bpy.context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if area.type == 'VIEW_3D':
                        override = {'window': window, 'screen': screen, 'area': area}
                        bpy.ops.wm.tool_set_by_id(override, name="builtin.annotate")
                        break

            context.scene.tool_settings.annotation_stroke_placement_view3d = 'SURFACE'

            # pongo todos los objetos seleccionados en solid mode
            for obj in bpy.context.selected_objects:
                obj.display_type = 'TEXTURED'

        else:
            bpy.context.scene.rbdlab_props.in_annotation_mode = False
            # sobreescribir el contexto:
            for window in bpy.context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if area.type == 'VIEW_3D':
                        override = {'window': window, 'screen': screen, 'area': area}
                        bpy.ops.wm.tool_set_by_id(override, name=bpy.context.scene.rbdlab_props.las_active_tool)
                        break

            if 'Annotations' in bpy.data.grease_pencils:
                if len(bpy.data.grease_pencils['Annotations'].layers) > 0:
                    items = list(bpy.context.scene.rbdlab_props.rbdlab_cf_source)
                    if 'PENCIL' not in items:
                        items.append('PENCIL')
                    bpy.context.scene.rbdlab_props.rbdlab_cf_source = set(items)
                else:
                    items = list(bpy.context.scene.rbdlab_props.rbdlab_cf_source)
                    if 'PENCIL' in items:
                        items.remove('PENCIL')
                    bpy.context.scene.rbdlab_props.rbdlab_cf_source = set(items)

        return {'FINISHED'}
