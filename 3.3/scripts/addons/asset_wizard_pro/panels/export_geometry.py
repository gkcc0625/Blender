# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy

from bpy.types import Panel

from ..utils.blender import is_valid_node_space
from ..constants import panel_name
from ..properties import Properties
from ..awp.ui import export_panel


class NODE_PT_awp_export_geometry_panel(Panel):
    """
    Shown in Shader Editor, side panel.
    """
    bl_label = 'Export'
    bl_idname = 'NODE_PT_awp_export_geometry_panel'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = panel_name


    @classmethod
    def poll(cls, context):
        return is_valid_node_space(context, ['GeometryNodeTree'])


    def draw(self, context: bpy.context):
        props = Properties.get()
        
        res = []
        n = context.active_node

        res.append((
            'NODE_GROUP',
            'NODE_SEL',
            'whole Tree',
            context.space_data.node_tree.name,
            props.geometry_tag_select
        ))
        if n and n.bl_idname == 'GeometryNodeGroup':
            res.append((
                'NODE_GROUP', 
                'NODE', 
                'Node Group', 
                n.node_tree.name,
                props.geometry_tag_select
            ))

        if res:
            c = export_panel(self.layout, res, props.geometry_node_section, 'G')

            if n and n.bl_idname == 'GeometryNodeGroup':
                if props.geometry_tag_select:
                    c.prop(props, 'geometry_tag_select', text='')