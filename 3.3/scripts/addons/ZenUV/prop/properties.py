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
from bpy.props import FloatProperty, BoolProperty, EnumProperty, FloatVectorProperty, IntProperty
from ZenUV.ui.labels import ZuvLabels
from ZenUV.zen_checker.zen_checker_labels import ZCheckerLabels as ch_labels
from ZenUV.ico import icon_get
from ZenUV.zen_checker.checker import ZEN_GLOBAL_OVERRIDER_NAME, ZEN_IMAGE_NODE_NAME

class ZUV_Properties(bpy.types.PropertyGroup):

    def update_tr_fit_bounds_single(self, context):
        self.tr_fit_bound[0] = self.tr_fit_bound[1] = self.tr_fit_bounds_single

    def tr_pivot_mode_items(self, context):
        if 'IMAGE_EDITOR' in [area.type for area in context.screen.areas]:
            return [
                ('CENTER', 'Bounding Box Points', '', 'PIVOT_BOUNDBOX', 0),
                ('MEDIAN', 'Median Point', '', 'PIVOT_MEDIAN', 1),
                ('CURSOR', '2D Cursor', '', 'PIVOT_CURSOR', 2),
                ('INDIVIDUAL_ORIGINS', 'Individual Origins', '', 'PIVOT_INDIVIDUAL', 3)
            ]
        else:
            return [
                ('CENTER', 'Bounding Box Points', '', 'PIVOT_BOUNDBOX', 0),
                ('MEDIAN', 'Median Point', '', 'PIVOT_MEDIAN', 1),
                # ('CURSOR', '2D Cursor', '', 'PIVOT_CURSOR', 2),
                ('INDIVIDUAL_ORIGINS', 'Individual Origins', '', 'PIVOT_INDIVIDUAL', 3)
            ]

    def tr_mode_items(self, context):
        return [
            ('MOVE', 'Move', 'MOVE', icon_get("transform-move"), 0),
            ('SCALE', 'Scale', 'SCALE', icon_get("transform-scale"), 1),
            ('ROTATE', 'Rotate', 'ROTATE', icon_get("transform-rotate"), 2),
            ('FLIP', 'Flip', 'FLIP', icon_get("transform-flip"), 3),
            ('FIT', 'Fit', 'FIT', icon_get("transform-fit"), 4),
            ('ALIGN', 'Align', 'ALIGN', icon_get("transform-orient"), 5),
            ('DISTRIBUTE', 'Distribute', 'DISTRIBUTE', icon_get("transform-distribute"), 6),
            ('2DCURSOR', '2D Cursor', 'CURSOR', icon_get("transform-cursor"), 7)
        ]

    def update_interpolation(self, context):
        interpolation = {True: 'Linear', False: 'Closest'}
        _overrider = None
        if bpy.data.node_groups.items():
            _overrider = bpy.data.node_groups.get(ZEN_GLOBAL_OVERRIDER_NAME, None)
        if _overrider:
            if hasattr(_overrider, "nodes"):
                image_node = _overrider.nodes.get(ZEN_IMAGE_NODE_NAME)
                if image_node:
                    # image_node.image = _image
                    image_node.interpolation = interpolation[context.scene.zen_uv.tex_checker_interpolation]

    tr_scale: FloatVectorProperty(
        name="Scale",
        size=2,
        default=(2.0, 2.0),
        subtype='XYZ'
    )

    tr_move_inc: FloatProperty(
        name=ZuvLabels.PROP_MOVE_INCREMENT_LABEL,
        default=1.0,
        min=0,
        step=0.1,
    )

    tr_fit_keep_proportion: BoolProperty(
        name="Keep Proportion",
        default=True
    )
    tr_fit_padding: FloatProperty(
        name="Padding",
        default=0.0
    )
    tr_fit_bound: FloatVectorProperty(
        name="Bounds",
        size=2,
        default=(1.0, 1.0),
        subtype='XYZ'
    )
    tr_fit_bounds_single: FloatProperty(
        name="Bounds",
        min=0.01,
        default=1.0,
        precision=2,
        update=update_tr_fit_bounds_single
    )

    tr_rot_inc: IntProperty(
        name=ZuvLabels.PROP_ROTATE_INCREMENT_LABEL,
        description=ZuvLabels.PROP_ROTATE_INCREMENT_DESC,
        min=1,
        max=360,
        default=90
    )

    tr_rot_orient: BoolProperty(
        name="Orient to selection",
        default=False
    )

    tr_align_center: BoolProperty(
        name="Always center",
        default=False
    )

    tr_mode: EnumProperty(
        name=ZuvLabels.PANEL_TRANSFORM_LABEL,
        description=ZuvLabels.PROP_ENUM_TRANSFORM_DESC,
        items=tr_mode_items
    )

    tr_pivot_mode: EnumProperty(
        name="Pivot",
        description="Transform Pivot",
        items=tr_pivot_mode_items
    )

    tr_space_mode: EnumProperty(
        name=ZuvLabels.PROP_TRANSFORM_SPACE_LABEL,
        description=ZuvLabels.PROP_TRANSFORM_SPACE_DESC,
        items=[
            ("ISLAND", "Island", ""),
            ("TEXTURE", "Texture", "")
        ],
        default="ISLAND"
    )

    tr_type: EnumProperty(
        name=ZuvLabels.PROP_TRANSFORM_TYPE_LABEL,
        description=ZuvLabels.PROP_TRANSFORM_TYPE_DESC,
        items=[
            ("ISLAND", "Islands", ""),
            ("SELECTION", "Elements", "")
        ],
        default="ISLAND"
    )
    tr_uv_area_bounds: BoolProperty(
        name="To UV Area Bounds",
        default=False,
        description="Align to UV Area Bounds"
    )
    sl_convert: EnumProperty(
        items=[
            ("SEAM_BY_UV_BORDER", ZuvLabels.MARK_BY_BORDER_LABEL, ZuvLabels.MARK_BY_BORDER_DESC),
            ("SEAM_BY_SHARP", ZuvLabels.SEAM_BY_SHARP_LABEL, ZuvLabels.SEAM_BY_SHARP_DESC),
            ("SHARP_BY_SEAM", ZuvLabels.SHARP_BY_SEAM_LABEL, ZuvLabels.SHARP_BY_SEAM_DESC),
            ("SEAM_BY_OPEN_EDGES", ZuvLabels.SEAM_BY_OPEN_EDGES_LABEL, ZuvLabels.SEAM_BY_OPEN_EDGES_DESC),
        ],
        default="SEAM_BY_OPEN_EDGES",
    )
    pack_uv_packer_margin: FloatProperty(
        name="Padding",
        description="Margin in conventional units. Not percentages or pixels.",
        default=2.0
    )
    tex_checker_interpolation: BoolProperty(
        name=ch_labels.PROP_INTERPOLATION_LABEL,
        default=True,
        description=ch_labels.PROP_INTERPOLATION_DESC,
        update=update_interpolation
    )
    td_select_type: EnumProperty(
        name="Select",
        description=ZuvLabels.PROP_TRANSFORM_TYPE_DESC,
        items=[
            ("UNDERRATED", ZuvLabels.PROP_TD_SELECT_TYPE_UNDER_LABEL, ""),
            ("OVERRATED", ZuvLabels.PROP_TD_SELECT_TYPE_OVER_LABEL, ""),
            ("VALUE", ZuvLabels.PROP_TD_SELECT_TYPE_VALUE_LABEL, "")
        ],
        default="VALUE"
    )
