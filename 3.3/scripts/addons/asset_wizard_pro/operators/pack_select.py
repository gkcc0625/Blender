# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy

from bpy.types import Operator, UILayout
from bpy.props import StringProperty

from ..registries.image_packer_registry import ImagePackerRegistry


class ASSET_OT_pack_select(Operator):
    """
    Used to toggle selection of packed images.
    """
    bl_idname = 'awp.pack_select'
    bl_label = ''
    bl_description = ''
    bl_options = {'REGISTER'}


    mode: StringProperty()
    image: StringProperty()


    @classmethod
    def description(cls, context, properties):
        return {
            'ALL': 'Pack all Images',
            'NONE': 'Pack no Images',
            'TOGGLE': 'Toggle pack Option',
            'INFO': 'Toggle Info Display',
        }.get(properties.mode, '??')


    def execute(self, context: bpy.context):
        if self.mode == 'ALL': ImagePackerRegistry.get().set_all(True)
        elif self.mode == 'NONE': ImagePackerRegistry.get().set_all(False)
        elif self.mode == 'TOGGLE': ImagePackerRegistry.get().toggle(self.image)
        elif self.mode == 'INFO': ImagePackerRegistry.get().toggle_info(self.image)
        
        return {'FINISHED'}


    @staticmethod
    def create_ui(l: UILayout, icon: str, text: str, depress: bool, mode: str, image: str):
        op = l.operator(ASSET_OT_pack_select.bl_idname, icon=icon, text=text, depress=depress) # type: ASSET_OT_pack_select
        op.mode = mode
        op.image = image
        