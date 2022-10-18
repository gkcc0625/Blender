# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy, addon_utils

from bpy.types import Panel

from ..operators.import_cleaner import ASSET_OT_import_cleaner
from ..operators.object_placer import ASSET_OT_object_placer
from ..operators.multi_purpose import ASSET_OT_multi_purpose
from ..operators.blend_importer import ASSET_OT_blend_importer

from ..constants import panel_name
from ..properties import Properties


class VIEW3D_PT_awp_tools_panel(Panel):
    """
    Various tools in 3D View
    """
    bl_label = 'Tools'
    bl_idname = 'VIEW3D_PT_awp_tools_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = panel_name


    def draw(self, context: bpy.types.Context):
        props = Properties.get()

        c = self.layout.column(align=True)
        c.label(text='Import', icon='IMPORT')
        ASSET_OT_blend_importer.create_ui(c, 'FILE_BLEND', 'Batch Import Blend')
        for addon_name, icon, operator in [
            ( 'io_scene_fbx', 'EVENT_F', 'import_scene.fbx' ),
            ( 'io_scene_gltf2', 'EVENT_G', 'import_scene.gltf'),
            ( 'io_scene_obj', 'EVENT_O', 'import_scene.obj'),
            ]:
            if addon_utils.check(addon_name)[1]:
                c.operator(operator, icon=icon)

        c.separator()
        c.label(text='Cleanup Tools', icon='MENU_PANEL')
        ASSET_OT_multi_purpose.create_ui_img_cleanup(c)
        if context.selected_objects:
            c.prop(props, 'show_object_cleaners', toggle=True, icon='OBJECT_DATAMODE')
            if props.show_object_cleaners:
                sp = c.split(factor=0.05, align=True)
                sp.label(text='')
                sc = sp.column(align=True)
                r = sc.row(align=True)
                r.prop(props, 'oc_remove_animation_data', toggle=True, text='', icon='CHECKBOX_HLT' if props.oc_remove_animation_data else 'CHECKBOX_DEHLT')
                ASSET_OT_import_cleaner.create_ui_objects(r, 'Remove Animation Data', 'ANIM_DATA', remove_animation_data=True)
                r = sc.row(align=True)
                r.prop(props, 'oc_unparent', toggle=True, text='', icon='CHECKBOX_HLT' if props.oc_unparent else 'CHECKBOX_DEHLT')
                ASSET_OT_import_cleaner.create_ui_objects(r, 'Remove parent Empties', 'OUTLINER_OB_EMPTY', unparent=True)
                r = sc.row(align=True)
                r.prop(props, 'oc_merge_objects', toggle=True, text='', icon='CHECKBOX_HLT' if props.oc_merge_objects else 'CHECKBOX_DEHLT')
                ASSET_OT_import_cleaner.create_ui_objects(r, 'Merge Objects', 'MOD_BOOLEAN', merge_objects=True)
                if props.oc_remove_animation_data or props.oc_unparent or props.oc_merge_objects:
                    ASSET_OT_import_cleaner.create_ui_objects(
                        sc, 
                        'Run selected Tasks', 
                        'PLAY', 
                        remove_animation_data=props.oc_remove_animation_data,
                        unparent=props.oc_unparent,
                        merge_objects=props.oc_merge_objects
                    )

            c.prop(props, 'show_mesh_cleaners', toggle=True, icon='OUTLINER_DATA_MESH')
            if props.show_mesh_cleaners:
                sp = c.split(factor=0.05, align=True)
                sp.label(text='')
                sc = sp.column(align=True)
                r = sc.row(align=True)
                r.prop(props, 'mc_clear_custom_split_normals', toggle=True, text='', icon='CHECKBOX_HLT' if props.mc_clear_custom_split_normals else 'CHECKBOX_DEHLT')
                ASSET_OT_import_cleaner.create_ui_meshes(r, 'Clear custom split Normals', 'NORMALS_VERTEX_FACE', clear_custom_split_normals=True)
                r = sc.row(align=True)
                r.prop(props, 'mc_set_auto_smooth', toggle=True, text='', icon='CHECKBOX_HLT' if props.mc_set_auto_smooth else 'CHECKBOX_DEHLT')
                ASSET_OT_import_cleaner.create_ui_meshes(r, 'Auto Smooth', 'NODE_MATERIAL', set_auto_smooth=True, auto_smooth_angle=props.mc_auto_smooth_angle)
                r = sc.split(factor=0.1, align=True)
                r.label(text='')
                r.prop(props, 'mc_auto_smooth_angle')
                r = sc.row(align=True)
                r.prop(props, 'mc_recalculate_normals_outside', toggle=True, text='', icon='CHECKBOX_HLT' if props.mc_recalculate_normals_outside else 'CHECKBOX_DEHLT')
                ASSET_OT_import_cleaner.create_ui_meshes(r, 'Recalculate Normals', 'NORMALS_VERTEX', recalculate_normals_outside=True)
                r = sc.row(align=True)
                r.prop(props, 'mc_join_vertices', toggle=True, text='', icon='CHECKBOX_HLT' if props.mc_join_vertices else 'CHECKBOX_DEHLT')
                ASSET_OT_import_cleaner.create_ui_meshes(r, 'Join Vertices', icon='AUTOMERGE_ON', join_vertices=True, join_vertices_distance=props.mc_join_vertices_distance)
                r = sc.split(factor=0.1, align=True)
                r.label(text='')
                r.prop(props, 'mc_join_vertices_distance')
                r = sc.row(align=True)
                r.prop(props, 'mc_limited_dissolve', toggle=True, text='', icon='CHECKBOX_HLT' if props.mc_limited_dissolve else 'CHECKBOX_DEHLT')
                ASSET_OT_import_cleaner.create_ui_meshes(r, 'Limited Dissolve', icon='UV_EDGESEL', limited_dissolve=True)
                if props.mc_clear_custom_split_normals or props.mc_set_auto_smooth or props.mc_recalculate_normals_outside or props.mc_join_vertices or props.mc_limited_dissolve:
                    ASSET_OT_import_cleaner.create_ui_meshes(
                        sc, 
                        'Run selected Tasks', 
                        'PLAY', 
                        clear_custom_split_normals=props.mc_clear_custom_split_normals,
                        set_auto_smooth=props.mc_set_auto_smooth,
                        recalculate_normals_outside=props.mc_recalculate_normals_outside,
                        limited_dissolve=props.mc_limited_dissolve,
                        join_vertices=props.mc_join_vertices,
                        auto_smooth_angle=props.mc_auto_smooth_angle,
                        join_vertices_distance=props.mc_join_vertices_distance
                    )                    


            c.separator()

            c.label(text='Batch Rotate:', icon='DRIVER_ROTATIONAL_DIFFERENCE')
            r = c.row(align=True)
            for i, t in enumerate(['-X', '-Y', '-Z', '+X', '+Y', '+Z' ]):
                #if i == 3: r.label(text='')
                ASSET_OT_multi_purpose.create_ui_rotate_90(r, t, t, 'ERROR')
            ASSET_OT_multi_purpose.create_ui_apply(c, 'ROTATION', 'Apply Rotation', 'ORIENTATION_GIMBAL')
            c.separator()

            c.label(text='Batch Set Origin:', icon='TRANSFORM_ORIGINS')
            r = c.row(align=True)
            for i, t in enumerate(['-X', '-Y', '-Z', 'C', '+X', '+Y', '+Z' ]):
                if i == 3 or i == 4: r.label(text='')
                ASSET_OT_multi_purpose.create_ui_update_origin(r, t, t, 'ERROR')

            if [ o for o in context.selected_objects if o.library ]:
                c.separator()
                ASSET_OT_multi_purpose.create_ui_library_override_selected(c)

        if context.active_object:
            c.separator()
            c.label(text='Viewport Tools', icon='VIEW3D')
            if context.active_object.library:
                ASSET_OT_multi_purpose.create_ui_library_override(c)
            else:
                ASSET_OT_object_placer.create_ui(c, props.replace_mode, props.place_quick, props.place_create_copy, props.place_linked_copy, props.place_auto_parent)
                r = c.row(align=True)
                r.prop(props, 'replace_mode', toggle=True, icon='PIVOT_ACTIVE', text='')
                r.prop(props, 'place_quick', toggle=True, icon='TIME', text='')
                r.prop(props, 'place_create_copy', toggle=True, icon='DUPLICATE', text='')
                if props.place_create_copy:
                    r.prop(props, 'place_linked_copy', toggle=True, icon='LIBRARY_DATA_DIRECT', text='')
                r.prop(props, 'place_auto_parent', toggle=True, icon='CONSTRAINT', text='')
