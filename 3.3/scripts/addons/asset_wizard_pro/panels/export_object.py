# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy

from bpy.types import Panel

from ..constants import panel_name
from ..properties import Properties
from ..awp.ui import export_panel


class VIEW3D_PT_awp_export_object_panel(Panel):
    """
    Export objects + materials, shown in 3DView side panel.
    """
    bl_label = 'Export'
    bl_idname = 'VIEW3D_PT_awp_export_object_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = panel_name


    def draw(self, context: bpy.context):
        props = Properties.get()
        res = []
        o = context.active_object
        if o:
            res.append(('OBJECT', 'OBJECT_DATA', 'Object', o.name))
        if context.selected_objects:
            res.append(('SELECTED_OBJECTS', 'RESTRICT_SELECT_OFF', 'Selected Objects', ''))
        if bpy.data.collections:
            res.append(( 'COLLECTION', 'OUTLINER_COLLECTION', 'Collection', props.collection))

        if res:
            c = export_panel(self.layout, res, props.object_collection_section, 'OC')

            if c and bpy.data.collections:
                c.prop(props, 'collection', text='')
        else:
            self.layout.box().label(text='Nothing to export', icon='ERROR')
                