# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy

from bpy.types import Operator, UILayout
from bpy.props import StringProperty

from ..utils.blender import DropNodeOperator


class ASSET_OT_std_node_drop(Operator, DropNodeOperator):
    """
    Import node.
    """
    bl_idname = 'awp.std_node_drop'
    bl_label = ''
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}


    system: StringProperty()
    type: StringProperty()
    op: StringProperty()
    bt: StringProperty()
    tooltip: StringProperty()


    @classmethod
    def description(cls, context, properties):
        return properties.tooltip


    def execute(self, context: bpy.context):
        settings = []
        if self.op: 
            settings.append({ 
                'name': 'operation',
                'value': self.op
            })
        if self.bt:
            settings.append({ 
                'name': 'blend_type',
                'value': self.bt
            })

        if settings:
            bpy.ops.node.add_node(
                type=f"{self.system}Node{self.type}", 
                use_transform=True,
                settings=settings
            )
        else:
            bpy.ops.node.add_node(
                type=f"{self.system}Node{self.type}", 
                use_transform=True,
            )

        return bpy.ops.node.translate_attach_remove_on_cancel('INVOKE_DEFAULT')


    @staticmethod
    def create_ui(l: UILayout, system: str, type: str, ope: str, bt: str, text: str, icon: str, tooptip: str):
        op = l.operator(ASSET_OT_std_node_drop.bl_idname, text=text, icon=icon if icon else 'NONE') # type: ASSET_OT_std_node_drop
        op.system = system
        op.type = type
        op.op = ope
        op.bt = bt
        op.tooltip = tooptip
