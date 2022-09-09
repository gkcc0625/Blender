# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy

from bpy.utils import register_class, unregister_class
from bpy.props import IntProperty

from ZenUV.ops.operators import (
    ZUV_OT_SmoothBySharp,
    ZUV_OT_SelectSharp,
    ZUV_OT_SelectSeams,
    ZUV_OT_SelectFlipped,
    ZUV_OT_Select_UV_Overlap,
    ZUV_OT_Select_UV_Island,
    ZUV_OT_Select_Loop,
    ZUV_OT_Pack,
    ZUV_OT_Isolate_Island,
    ZUV_OT_MirrorSeams,
    ZUV_OT_SyncZenUvToUVP
)

from ZenUV.ops.finishing import (
    ZUV_OT_UnTag_Finished,
    ZUV_OT_Tag_Finished,
    ZUV_OT_Sorting_Islands,
    ZUV_OT_Select_Finished,
    ZUV_OT_Display_Finished
)

from ZenUV.ops.mark import (
    ZUV_OT_Unmark_Seams,
    ZUV_OT_Unmark_All,
    ZUV_OT_Sharp_By_Seam,
    ZUV_OT_Seams_By_UV_Borders,
    ZUV_OT_Seam_By_Sharp,
    ZUV_OT_Mark_Seams,
    ZUV_OT_Auto_Mark,
    ZUV_OT_Seams_By_Open_Edges,
    ZUV_OT_UnifiedMark
)

from ZenUV.ops.texel import td_classes

from ZenUV.ops.zen_unwrap import ZUV_OT_ZenUnwrap
from ZenUV.ops.quadrify import ZUV_OT_Quadrify
from ZenUV.ops.transformations import uv_transform_classes
from ZenUV.ops.distribute import uv_distribute_classes
from ZenUV.ops.pt_uv_texture_advanced import (
    AddUVMaps,
    RemoveUVMaps,
    AutoSyncUVMapsIDs,
    RemoveInactiveUVMaps,
    RenameUVMaps,
    SyncUVMapsIDs,
    ShowUVMap
)

from ZenUV.ops.seam_groups import (
    ZSG_UL_List,
    ZSGListGroup,
    ZSG_OT_NewItem,
    ZSG_OT_DeleteItem,
    ZSG_OT_MoveItem,
    ZSG_OT_AssignToGroup,
    ZSG_OT_ActivateGroup,

)

from ZenUV.ops.texel_presets import TDPR_classes, TDPRListGroup

ZSG_classes = (
    ZSG_UL_List,
    ZSGListGroup,
    ZSG_OT_NewItem,
    ZSG_OT_DeleteItem,
    ZSG_OT_MoveItem,
    ZSG_OT_AssignToGroup,
    ZSG_OT_ActivateGroup

)

CLASSES = (
    ZUV_OT_Auto_Mark,
    ZUV_OT_SmoothBySharp,
    ZUV_OT_Unmark_All,
    ZUV_OT_Isolate_Island,
    ZUV_OT_Mark_Seams,
    ZUV_OT_Seams_By_UV_Borders,
    ZUV_OT_Seams_By_Open_Edges,
    ZUV_OT_Seam_By_Sharp,
    ZUV_OT_Sharp_By_Seam,
    ZUV_OT_Select_UV_Overlap,
    ZUV_OT_Select_UV_Island,
    ZUV_OT_Unmark_Seams,
    ZUV_OT_ZenUnwrap,
    ZUV_OT_Quadrify,
    ZUV_OT_Select_Loop,
    ZUV_OT_Pack,
    ZUV_OT_Tag_Finished,
    ZUV_OT_UnTag_Finished,
    ZUV_OT_Sorting_Islands,
    ZUV_OT_Display_Finished,
    ZUV_OT_Select_Finished,
    ZUV_OT_SelectSharp,
    ZUV_OT_SelectSeams,
    ZUV_OT_SelectFlipped,
    ZUV_OT_MirrorSeams,
    ZUV_OT_SyncZenUvToUVP,
    ZUV_OT_UnifiedMark
)

adv_uv_texture_classes = (
    AddUVMaps,
    RemoveUVMaps,
    AutoSyncUVMapsIDs,
    RemoveInactiveUVMaps,
    RenameUVMaps,
    SyncUVMapsIDs,
    ShowUVMap
)


def register():
    """Registering Operators"""
    for cl in CLASSES:
        register_class(cl)

    # Zen Transform Registration
    for cl in uv_transform_classes:
        register_class(cl)

    # Zen Distribute Registration
    for cl in uv_distribute_classes:
        register_class(cl)

    # Advanced UV Texture Registration
    for cl in adv_uv_texture_classes:
        register_class(cl)

    # Zen Seam Groups Registration
    for cl in ZSG_classes:
        register_class(cl)

    # Texel Density Registration
    for cl in td_classes:
        register_class(cl)

    # Texel Density Presets Registration
    for cl in TDPR_classes:
        register_class(cl)
    register_class(TDPRListGroup)

    # Smooth Groups
    bpy.types.Object.zen_sg_list = bpy.props.CollectionProperty(type=ZSGListGroup)
    bpy.types.Object.zsg_list_index = IntProperty(name="Index for zen_sg_list", default=0)

    # Texel Density Presets
    bpy.types.Scene.zen_tdpr_list = bpy.props.CollectionProperty(type=TDPRListGroup)
    bpy.types.Scene.zen_tdpr_list_index = IntProperty(name="Index for zen_tdpr_list", default=0)


def unregister():
    """Unegistering Operators"""
    for cl in CLASSES:
        unregister_class(cl)

    # Zen Transform
    for cl in uv_transform_classes:
        unregister_class(cl)

    # Zen Distribute
    for cl in uv_distribute_classes:
        unregister_class(cl)

    # Advanced UV Texture
    for cl in adv_uv_texture_classes:
        unregister_class(cl)

    # Zen Seam Groups
    for cl in ZSG_classes:
        unregister_class(cl)

    # Texel Density
    for cl in td_classes:
        unregister_class(cl)

    # Texel Density Presets
    for cl in TDPR_classes:
        unregister_class(cl)
    unregister_class(TDPRListGroup)


if __name__ == "__main__":
    pass
