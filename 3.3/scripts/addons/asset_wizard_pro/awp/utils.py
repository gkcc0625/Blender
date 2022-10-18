# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy

from ..utils.blender import all_spaces
from ..properties import Properties, PropertySection


def update_asset_browser(context: bpy.context):
    """
    Update libraries in asset browser.
    """
    if (3, 2, 0) > bpy.app.version:
        override = bpy.context.copy()
        override['area'] = all_spaces('FILE_BROWSER')[0]
        bpy.ops.asset.library_refresh(override)
    else:
        with bpy.context.temp_override(area=all_spaces('FILE_BROWSER')[0]):
            bpy.ops.asset.library_refresh()


def section_by_name(name: str) -> PropertySection:
    """
    Used to pass section to OP via StringProperty.
    """
    props = Properties.get()
    return {
        'MN': props.material_node_section,
        'G': props.geometry_node_section,
        'OC': props.object_collection_section,
    }[name]
    