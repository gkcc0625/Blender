# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy

from bpy.types import Operator, UILayout
from bpy.props import StringProperty

from ..awp.utils import section_by_name
from ..registries.config_registry import ConfigRegistry

class ASSET_OT_tag_manager(Operator):
    """
    Handle operation related to tags.
    """
    bl_idname = 'awp.tag_manager'
    bl_label = ''
    bl_description = ''
    bl_options = {'REGISTER'}   


    mode: StringProperty()
    section: StringProperty()
    tag: StringProperty()


    @classmethod
    def description(cls, context, properties):
        if properties.tag:
            m = {
                'ADD': 'Add Tag',
                'ADD_NEW': 'Create and add new Tag',
                'REMOVE': 'Remove Tag'
            }.get(properties.mode, '??')
            return f'{m} "{properties.tag}"'
        else:
            return 'Please enter new Tag Name'


    def execute(self, context: bpy.context):
        if self.tag:
            if self.mode in [ 'ADD', 'REMOVE', 'ADD_NEW' ]:
                # Side panel.
                section = section_by_name(self.section)
                if self.mode == 'ADD' or self.mode == 'ADD_NEW':
                    if self.tag not in [ t.title for t in section.tags ]:
                        t = section.tags.add()
                        t.title = self.tag
                elif self.mode == 'REMOVE':
                    for i, t in enumerate(section.tags):
                        if t.title == self.tag:
                            section.tags.remove(i)
                            break
                if self.mode == 'ADD_NEW':
                    ConfigRegistry.get().add_tag(self.tag)
                    section.new_tag = ''
            else:
                # Preferences panel.
                if self.mode == 'ADD_TAG': ConfigRegistry.get().add_tag(self.tag)
                if self.mode == 'ADD_SHADER_TAG': ConfigRegistry.get().add_shader_tag(self.tag)
                if self.mode == 'ADD_GEOMETRY_TAG': ConfigRegistry.get().add_geometry_tag(self.tag)
                if self.mode == 'REMOVE_TAG': ConfigRegistry.get().remove_tag(self.tag)
                if self.mode == 'REMOVE_SHADER_TAG': ConfigRegistry.get().remove_shader_tag(self.tag)
                if self.mode == 'REMOVE_GEOMETRY_TAG': ConfigRegistry.get().remove_geometry_tag(self.tag)

        return {'FINISHED'}
        

    @staticmethod
    def create_ui(l: UILayout, icon: str, emboss: bool, mode: str, section: str, tag: str):
        op = l.operator(ASSET_OT_tag_manager.bl_idname, icon=icon, text='', emboss=emboss) # type: ASSET_OT_tag_manager
        op.mode = mode
        op.section = section
        op.tag = tag
