# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy, traceback

from bpy.types import Operator, UILayout
from bpy.props import StringProperty

from ..utils.blender import DropNodeOperator


class ASSET_OT_import(Operator, DropNodeOperator):
    """
    Import node.
    """
    bl_idname = 'awp.import'
    bl_label = ''
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}


    mode: StringProperty()
    filename: StringProperty()
    node: StringProperty()
    desc: StringProperty()


    @classmethod
    def description(cls, context, properties):
        return properties.desc if properties.desc else properties.node


    def execute(self, context: bpy.context):
        try:
            with bpy.data.libraries.load(self.filename, link=False) as (_, data_to):
                data_to.node_groups = [self.node]
                nodes = data_to.node_groups

            if self.mode == 'GEOMETRY':
                bpy.ops.node.add_node(
                    type='GeometryNodeGroup', 
                    use_transform=True, 
                    settings=[{
                        'name': 'node_tree', 
                        'value': "bpy.data.node_groups['%s']" % nodes[0].name
                    }]
                )
            else:
                bpy.ops.node.add_node(
                    type='ShaderNodeGroup', 
                    use_transform=True, 
                    settings=[{
                        'name': 'node_tree', 
                        'value': "bpy.data.node_groups['%s']" % nodes[0].name
                    }]
                )

            return bpy.ops.node.translate_attach_remove_on_cancel('INVOKE_DEFAULT')
        except Exception as ex:
            print(traceback.format_exc())
            self.report({'ERROR'}, f'Asset loading failed, see Console ({ex})')
            return {'FINISHED'}


    @staticmethod
    def create_ui(l: UILayout, mode: str, filename: str, node: str, short_name: str, desc: str):
        op = l.operator(ASSET_OT_import.bl_idname, text=short_name, icon='NODE') # type: ASSET_OT_import
        op.mode = mode
        op.filename = filename
        op.node = node
        op.desc = desc
        