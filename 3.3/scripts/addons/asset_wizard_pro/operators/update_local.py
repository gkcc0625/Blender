# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy, os

from bpy.types import Operator, UILayout

from typing import Union

from ..utils.io import os_path, TempFile
from ..utils.blender import is_file_saved
from ..awp.invoke_external import render_preview


class ASSET_OT_update_local(Operator):
    """
    Update previews of local asset collection, objects and materials.
    Controls are placed in Asset Browser header.
    """
    bl_idname = 'awp.update_local'
    bl_label = 'Update all selected Previews (may take some time)?'
    bl_description = 'Update the Preview Images of all selected Assets'
    bl_options = {'REGISTER'}


    def __render_and_assign_preview(
            self,
            mode: str,
            image_file: str,
            o: Union[bpy.types.Material, bpy.types.Object, bpy.types.Collection],
            name: str
        ):
        render_preview(os_path(bpy.data.filepath), image_file, mode, name)
        if os.path.exists(image_file):
            if (3, 2, 0) > bpy.app.version:
                override = bpy.context.copy()
                override['id'] = o
                bpy.ops.ed.lib_id_load_custom_preview(override, filepath=image_file)
            else:
                with bpy.context.temp_override(id=o):
                    bpy.ops.ed.lib_id_load_custom_preview(filepath=image_file)
        else:
            self.report({'ERROR'}, 'Preview rendering failed (see Console)')


    @classmethod
    def poll(cls, context):
        return hasattr(context.space_data, 'params') and \
            context.space_data.params.asset_library_ref == 'LOCAL' and \
            context.selected_asset_files


    @classmethod
    def description(cls, context, properties):
        if is_file_saved():
            return 'Render Preview Image for all selected Assets in Asset Browser'
        else:
            return 'File must be saved to update Previews'


    def execute(self, context: bpy.context):
        if is_file_saved():
            with TempFile('png') as image_file:
                for a in context.selected_asset_files:
                    if a.id_type == 'MATERIAL':
                        m = bpy.data.materials[a.name]
                        self.__render_and_assign_preview('MATERIAL', image_file, m, m.name)
                    elif a.id_type == 'OBJECT':
                        o = bpy.data.objects[a.name]
                        self.__render_and_assign_preview('OBJECT', image_file, o, o.name)
                    elif a.id_type == 'COLLECTION':
                        c = bpy.data.collections[a.name]
                        self.__render_and_assign_preview('COLLECTION', image_file, c, c.name)

        return {'FINISHED'}


    def invoke(self, context, event):
        if is_file_saved():
            return context.window_manager.invoke_confirm(self, event)        
        else:
            return {'FINISHED'}
            

    @staticmethod
    def create_ui(l: UILayout):
        l.operator(ASSET_OT_update_local.bl_idname, icon='SEQ_PREVIEW', text='Update Previews') # type: ASSET_OT_update_local
