# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy

from bpy.types import Operator

from ..menus.nodes_pie import NODE_MT_awp_nodes_pie_menu
from ..utils.blender import material_wizard_enabled, shader_node_wizard_enabled
from ..preferences import PreferencesPanel


class ASSET_OT_invoke_pie(Operator):
    """
    Opens the Pie Menu
    """
    bl_idname = 'awp.invoke_pie'
    bl_label = ''
    bl_description = 'Open the Pie Menu'
    bl_options = {'REGISTER'}


    def execute(self, context: bpy.context):
        # If SNW if preferred in prefs, open this instead.
        if PreferencesPanel.get().prefer_snw:
            if context.space_data.tree_type == 'ShaderNodeTree':
                if shader_node_wizard_enabled():
                    bpy.ops.wm.call_menu_pie(name='NODE_MT_snw_main_pie_menu')
                    return {'FINISHED'}

        # Check if we are in MW tree space ..
        if material_wizard_enabled() and context.space_data.tree_type == 'MaterialWizardTree':
            bpy.ops.wm.call_menu_pie(name='MATERIAL_MT_mw_nodes_pie_menu')
            return {'FINISHED'}

        # Finally call ours (obvisouly Geometry .. or Shader).    
        bpy.ops.wm.call_menu_pie(name=NODE_MT_awp_nodes_pie_menu.bl_idname)
        return {'FINISHED'}
