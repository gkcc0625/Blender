from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .. import props

import bpy


class AddonList(bpy.types.UIList):
    bl_idname = 'POWERMANAGE_UL_addon_list'

    def draw_item(
        self,
        context: bpy.types.Context,
        layout: bpy.types.UILayout,
        data,
        item: props.addon.Addon,
        icon,
        active_data,
        active_propname,
    ):
        row = layout.row(align=True)
        row.alignment = 'LEFT'

        row.prop(
            item,
            'visible',
            text='',
            icon='HIDE_OFF' if item.visible else 'HIDE_ON',
            emboss=False,
        )

        row.operator(
            'powermanage.toggle_addon',
            text=item.full_label() if context.area.type == 'PREFERENCES' else item.label,
            icon=item.icon(),
            emboss=False,
        ).addon = item.name
