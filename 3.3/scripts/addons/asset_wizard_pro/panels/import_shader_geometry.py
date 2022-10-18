# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy

from bpy.types import Panel

from ..constants import panel_name
from ..registries.resource_lists_registry import ResourceListsRegistry
from ..utils.blender import is_valid_node_space
from ..operators.import_assets import ASSET_OT_import


class NODE_PT_awp_import_shader_geometry_panel(Panel):
    """
    Shown in both Shader and Geometry side panel, imports 
    and drops nodes from assets.
    """
    bl_label = 'Import'
    bl_idname = 'NODE_PT_awp_import_shader_geometry_panel'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = panel_name


    @classmethod
    def poll(cls, context):
        return is_valid_node_space(context, ['GeometryNodeTree', 'ShaderNodeTree'])


    def draw(self, context: bpy.context):
        is_shader = context.space_data.tree_type == 'ShaderNodeTree'
        c = self.layout.column(align=True)

        shaders = ResourceListsRegistry.get().shader_nodes() if is_shader else ResourceListsRegistry.get().geometry_nodes() 
        for k in sorted(shaders.keys()):
            c.label(text=f'{k}:')
            for file, name, short_name, desc in sorted(shaders[k], key=lambda x: x[2]):
                ASSET_OT_import.create_ui(
                    c, 
                    'SHADER' if is_shader else 'GEOMETRY', 
                    file, 
                    name, 
                    short_name,
                    desc
                )
                