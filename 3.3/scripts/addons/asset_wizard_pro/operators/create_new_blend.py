# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import traceback
import bpy, os

from bpy.types import Operator, UILayout
from bpy.props import StringProperty

from ..awp.utils import section_by_name
from ..registries.resource_lists_registry import ResourceListsRegistry

class ASSET_OT_create_new_blend(Operator):
    """
    Create an empty new blend file (if not exists).
    """
    bl_idname = 'awp.create_new_blend'
    bl_label = ''
    bl_description = ''
    bl_options = {'REGISTER'}


    path: StringProperty()
    file: StringProperty(name='File Name', description='Name of new File (without .blend)')
    section: StringProperty()


    @classmethod
    def description(cls, context, properties):
        return f'Create a new, empty Asset Library .blend File in "{properties.path}"'


    def execute(self, context: bpy.context):
        filename = os.path.join(
            self.path, 
            self.file if self.file.endswith('.blend') else f'{self.file}.blend'
        )
        if not os.path.exists(filename):
            try:
                # Create file.
                bpy.data.libraries.write(filename, set(), compress=True)

                # Update local lists.
                ResourceListsRegistry.get().update()

                # Set as default.
                fixed_name = os.path.splitext(self.file)[0]
                section = section_by_name(self.section)
                for e in ResourceListsRegistry.get().library_files(section.export_library):
                    if e[1] == fixed_name:
                        section.export_file = e[0]
                        break
            except Exception as ex:
                print(traceback.format_exc())
                self.report({'ERROR'}, f'File creation failed, see Console ({ex})')
        else:
            self.report({'ERROR'}, 'File already exists')

        return {'FINISHED'}


    def draw(self, context: bpy.context):
        l = self.layout.column(align=True)
        l.label(text=self.path)
        l.prop(self, 'file')


    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


    @staticmethod
    def create_ui(l: UILayout, path: str, section: str):
        op = l.operator(ASSET_OT_create_new_blend.bl_idname, icon='ADD', text='New File') # type: ASSET_OT_create_new_blend
        op.path = path
        op.section = section
