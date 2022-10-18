# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy

from bpy.types import Panel

from ..constants import panel_name
from ..properties import Properties
from ..awp.ui import export_panel
from ..utils.blender import is_valid_node_space


class NODE_PT_awp_export_material_panel(Panel):
    """
    Shown in Shader Editor, side panel.
    """
    bl_label = 'Export'
    bl_idname = 'NODE_PT_awp_export_material_panel'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = panel_name


    @classmethod
    def poll(cls, context):
        return is_valid_node_space(context, ['ShaderNodeTree'])


    def draw(self, context: bpy.context):
        props = Properties.get()
        
        res = []
        m = context.material
        if m:
            res.append(('MATERIAL', 'MATERIAL', 'Material', m.name))
        n = context.active_node
        if n and n.bl_idname == 'ShaderNodeGroup':
            res.append((
                'NODE_GROUP', 
                'NODE', 
                'Node Group', 
                n.node_tree.name, 
                props.shader_tag_select
            ))
        if res:
            c = export_panel(self.layout, res, props.material_node_section, 'MN')

            if n and n.bl_idname == 'ShaderNodeGroup':
                if props.shader_tag_select:
                    c.prop(props, 'shader_tag_select', text='')

                    