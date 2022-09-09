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

""" Zen UV Transformation module """

import random
from mathutils import Vector
from math import radians
import bpy
import bmesh
from ZenUV.stacks.utils import Cluster
from bpy.props import (
    FloatVectorProperty,
    StringProperty,
    BoolProperty,
    FloatProperty,
    IntProperty
)
from ZenUV.ui.labels import ZuvLabels
from ZenUV.utils import get_uv_islands as island_util
from ZenUV.utils.generic import (
    resort_objects,
    get_mesh_data,
    get_padding_in_pct,
    loops_by_sel_mode,
)

from ZenUV.utils.transform import (
    centroid,
    rotate_island,
    move_island,
    zen_convex_hull_2d,
    get_bbox,
    scale_island,
    bound_box,
    calculate_fit_scale,
    # make_rotation_transformation,
    move_points,
    scale_points,
    rotate_points,
    get_bbox_loops,
    UV_AREA_BBOX,
    align_auto,
    align_horizontal,
    align_vertical

)
from ZenUV.utils.texel_density import calculate_overall_centroid
from ZenUV.utils.hops_integration import show_uv_in_3dview


def pp_cursor(context):
    cursor = (0.0, 0.0)
    for area in context.screen.areas:
        if area.type == 'IMAGE_EDITOR':
            cursor = area.spaces.active.cursor_location
    return cursor


def pp_median(context):
    objs = resort_objects(context, context.objects_in_mode)
    per_object_centroid = []
    for obj in objs:
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()
        islands = island_util.get_island(context, bm, uv_layer)
        per_object_centroid.append(calculate_overall_centroid(uv_layer, islands))
    return Vector(centroid(per_object_centroid))


def pp_center(context):
    return get_bbox(context)["cen"]


def pp_individual_origins(context):
    return (0, 0)


ANCHORS = {
    "CENTER": pp_center,
    "CURSOR": pp_cursor,
    "MEDIAN": pp_median,
    "INDIVIDUAL_ORIGINS": pp_individual_origins,
    "BOUNDING_BOX_CENTER": pp_center,
    "ACTIVE_ELEMENT": pp_individual_origins,
    "MEDIAN_POINT": pp_median
}


def system_pivot_point(context):
    """
    Return Pivot Point Type
    case VIEW_3D:
        'BOUNDING_BOX_CENTER'
        'CURSOR'
        'INDIVIDUAL_ORIGINS'
        'MEDIAN_POINT'
        'ACTIVE_ELEMENT'

    case IMAGE_EDITOR:
        "CENTER"
        "CURSOR"
        "MEDIAN"
        "INDIVIDUAL_ORIGINS"
    """
    scene = context.scene
    sima = context.space_data
    pivot_point = None
    if context.space_data.type == 'VIEW_3D':
        pivot_point = scene.tool_settings.transform_pivot_point
    elif context.space_data.type == 'IMAGE_EDITOR':
        pivot_point = sima.pivot_point
    return pivot_point


def get_position(context, pivot_point_type, bbox_pivot, cursor_location=Vector((0.0, 0.0)), increment=0, direction=Vector((0.0, 0.0))):
    """
        return position in 2D coord (Vector).
        pivot_point_type (string) - from UV types.
            "CENTER"
            "CURSOR"
            "MEDIAN"
            "INDIVIDUAL_ORIGINS"

        bbox_pivot (Vector) - pivot point of island.
        cursor_location (Vector) - Location of 2D Cursor.
        increment (Float) - Island shift increment.
        direction (Vector) - Island shift direction.
    """
    prop = context.scene.zen_uv
    incr = Vector((increment, increment))
    new_position = Vector(
        (
            direction.x * incr.x,
            direction.y * incr.y
        )
    )
    if pivot_point_type == "CURSOR":
        new_position = Vector(
            (
                cursor_location.x - bbox_pivot.x,
                cursor_location.y - bbox_pivot.y
            )
        )
    if prop.tr_space_mode == "TEXTURE" and context.space_data.type == 'VIEW_3D':
        new_position = Vector((new_position[0] * -1, new_position[1] * -1))
    return new_position


def rotate_in_direction(points, increment_angle=0, base_direction="tl"):
    rot_dir = {
        "tl": 1,
        "tr": -1,
        "bl": 1,
        "br": -1,
    }
    return increment_angle * rot_dir[base_direction]


def r_direction(context, points, base_direction):
    prop = context.scene.zen_uv
    increment_angle = radians(prop.tr_rot_inc)
    rotation_direction = {
        "tl": rotate_in_direction,
        "tc": align_vertical,
        "tr": rotate_in_direction,
        "lc": align_horizontal,
        "cen": align_auto,
        "rc": align_horizontal,
        "bl": rotate_in_direction,
        "bc": align_vertical,
        "br": rotate_in_direction,
    }
    factor = 1
    if prop.tr_space_mode == "TEXTURE" and context.space_data.type == 'VIEW_3D' and base_direction in ("tl", "tr", "bl", "br"):
        factor = -1
    angle = rotation_direction[base_direction](points, increment_angle, base_direction) * factor
    return angle


class ZUV_OT_UnifiedTransform(bpy.types.Operator):
    bl_idname = "uv.zenuv_unified_transform"
    bl_label = "Zen Transform"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.OT_MOVE_DESC

    # Variable for disabling the operator from the interface
    # works via .poll ()
    transform_mode: StringProperty(
        name="Transform Mode",
        description="Sets transform mode",
        default="",
        options={'HIDDEN'}
    )
    active: BoolProperty(
        name="Enable operator",
        default=True,
        options={'HIDDEN'}
    )
    direction: FloatVectorProperty(
        name="Transformation direction",
        size=2,
        default=(0.0, 0.0),
        subtype='DIRECTION',
        options={'HIDDEN'}
    )
    orient_by_selected: BoolProperty(
        name="Orient to Selection",
        description="",
        default=False,
        options={'HIDDEN'}
    )
    pp_pos: StringProperty(
        name="Anchor Position",
        default="cen",
        options={'HIDDEN'}
    )
    fit_keep_proportion: BoolProperty(
        name="Fit keep proportion",
        description="",
        default=True,
        options={'HIDDEN'}
    )
    dir_vector = {
        "tl": Vector((-1, 1)),
        "tc": Vector((0, 1)),
        "tr": Vector((1, 1)),
        "lc": Vector((-1, 0)),
        "cen": Vector((0, 0)),
        "rc": Vector((1, 0)),
        "bl": Vector((-1, -1)),
        "bc": Vector((0, -1)),
        "br": Vector((1, -1))
    }
    flip_vector = {
        "tl": Vector((-1, -1)),
        "tc": Vector((1, -1)),
        "tr": Vector((-1, -1)),
        "lc": Vector((-1, 1)),
        "cen": Vector((1, 1)),
        "rc": Vector((-1, 1)),
        "bl": Vector((-1, -1)),
        "bc": Vector((1, -1)),
        "br": Vector((-1, -1))
    }
    fit_position = {
        "tl": Vector((0, 1)),
        "tc": Vector((0.5, 1)),
        "tr": Vector((1, 1)),
        "lc": Vector((0, 0.5)),
        "cen": Vector((0.5, 0.5)),
        "rc": Vector((1, 0.5)),
        "bl": Vector((0, 0)),
        "bc": Vector((0.5, 0)),
        "br": Vector((1, 0))
    }
    desc: bpy.props.StringProperty(name="Description", default="Transform", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'  # and properties.active

    @classmethod
    def description(cls, context, properties):
        return properties.desc

    def execute(self, context):

        transform_modes = (
            "MOVE",
            "SCALE",
            "ROTATE",
            "FLIP",
            "FIT",
            "ALIGN",
            "2DCURSOR"
        )
        scene = context.scene

        # Type of transformation Islands or Selection
        transform_islands = scene.zen_uv.tr_type == 'ISLAND'

        if self.transform_mode == "" or self.transform_mode not in transform_modes:
            transform_mode = scene.zen_uv.tr_mode
        else:
            transform_mode = self.transform_mode

        # Any transforms blocked (operator CANCELLED) if no selection.
        # Except case 2D Cursor operation.
        # It allows positioning 2D Cursor over UV Area withot Selection.
        objs = resort_objects(context, context.objects_in_mode)
        if not objs:
            if not transform_mode == "2DCURSOR":
                return {"CANCELLED"}

        pivot_point = scene.zen_uv.tr_pivot_mode
        if pivot_point == '':
            pivot_point = 'CENTER'
        # print("Pivot MODE", pivot_point)
        uv_cursor_location = Vector((0.0, 0.0))
        for area in context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                uv_cursor_location = area.spaces.active.cursor_location

        # 2D Cursor Mode
        if transform_mode == "2DCURSOR":
            for area in context.screen.areas:
                if area.type == 'IMAGE_EDITOR':
                    if transform_islands:
                        area.spaces.active.cursor_location = get_bbox(context)[self.pp_pos]
                    else:
                        area.spaces.active.cursor_location = get_bbox_loops(context)[self.pp_pos]

        # Move Mode
        if transform_mode == "MOVE":
            bbox = get_bbox(context)
            prop_move_incr = scene.zen_uv.tr_move_inc
            direction = self.dir_vector[self.pp_pos]
            position = get_position(context, pivot_point, bbox[self.pp_pos], uv_cursor_location, prop_move_incr, direction)

            for obj in objs:
                me, bm = get_mesh_data(obj)
                uv_layer = bm.loops.layers.uv.verify()
                # print(f"Transform Islands: {transform_islands}")
                if transform_islands:
                    islands_for_process = island_util.get_island(context, bm, uv_layer)
                    for island in islands_for_process:
                        move_island(island, uv_layer, position)
                else:
                    loops = loops_by_sel_mode(context, bm)
                    move_points(loops, uv_layer, position)
                bmesh.update_edit_mesh(me, loop_triangles=False)

        # Flip/Scale Mode
        if transform_mode in ("FLIP", "SCALE"):
            anchor = ANCHORS[pivot_point](context)
            if pivot_point in ("CENTER", "BOUNDING_BOX_CENTER"):
                anchor = get_bbox(context)[self.pp_pos]
            for obj in objs:
                me, bm = get_mesh_data(obj)
                uv_layer = bm.loops.layers.uv.verify()

                if transform_mode == "SCALE":
                    # scale = [addon_prefs.tr_scale_x, addon_prefs.tr_scale_y]
                    scale = scene.zen_uv.tr_scale

                elif transform_mode == "FLIP":
                    scale = self.flip_vector[self.pp_pos]

                if transform_islands:
                    islands_for_process = island_util.get_island(context, bm, uv_layer)
                    for island in islands_for_process:
                        if pivot_point in ("INDIVIDUAL_ORIGINS", "ACTIVE_ELEMENT"):
                            points = [loop[uv_layer].uv for face in island for loop in face.loops]
                            anchor = bound_box(points=zen_convex_hull_2d(points), uv_layer=uv_layer)["cen"]

                        scale_island(island, uv_layer, scale, anchor)
                else:
                    loops = loops_by_sel_mode(context, bm)
                    points = [loop[uv_layer].uv for loop in loops]
                    if pivot_point == 'CURSOR':
                        for area in context.screen.areas:
                            if area.type == 'IMAGE_EDITOR':
                                anchor = area.spaces.active.cursor_location
                    else:
                        # anchor = bound_box(points=zen_convex_hull_2d(points), uv_layer=uv_layer)[self.pp_pos]
                        anchor = get_bbox_loops(context)[self.pp_pos]
                    if pivot_point in ("INDIVIDUAL_ORIGINS", "ACTIVE_ELEMENT"):
                        anchor = bound_box(points=zen_convex_hull_2d(points), uv_layer=uv_layer)["cen"]
                    if pivot_point in ("MEDIAN"):
                        anchor = get_bbox_loops(context)["cen"]
                    scale_points(loops, uv_layer, scale, anchor)

                bmesh.update_edit_mesh(me, loop_triangles=False)

        # Fit Mode
        if transform_mode == "FIT":
            anchor = ANCHORS[pivot_point](context)
            if pivot_point in ("CENTER", "BOUNDING_BOX_CENTER"):
                anchor = get_bbox(context)[self.pp_pos]
            bbox = get_bbox(context)
            # print(f"Fit Mode: BBOX {bbox}")
            padding = get_padding_in_pct(context, scene.zen_uv.tr_fit_padding)
            fit_bounds = scene.zen_uv.tr_fit_bound

            bb_padding = {
                "tl": Vector((padding, -padding)),
                "tc": Vector((0, -padding)),
                "tr": Vector((-padding, -padding)),
                "lc": Vector((padding, 0)),
                "cen": Vector((0, 0)),
                "rc": Vector((-padding, 0)),
                "bl": Vector((padding, padding)),
                "bc": Vector((0, padding)),
                "br": Vector((-padding, padding))
            }

            scale = calculate_fit_scale(
                self.pp_pos,
                padding,
                bbox,
                self.fit_keep_proportion,
                fit_bounds
            )

            for obj in objs:
                me, bm = get_mesh_data(obj)
                uv_layer = bm.loops.layers.uv.verify()

                if transform_islands:
                    islands_for_process = island_util.get_island(context, bm, uv_layer)

                    for island in islands_for_process:
                        if pivot_point in ("INDIVIDUAL_ORIGINS", "ACTIVE_ELEMENT"):
                            bbox = bound_box(islands=[island, ], uv_layer=uv_layer)
                            anchor = bbox[self.pp_pos]
                            scale = calculate_fit_scale(
                                self.pp_pos,
                                padding,
                                bbox,
                                self.fit_keep_proportion,
                                fit_bounds
                            )

                        scale_island(island, uv_layer, scale, bbox[self.pp_pos])

                        if pivot_point == "CURSOR":
                            position = Vector(
                                (
                                    uv_cursor_location.x - bbox[self.pp_pos].x,
                                    uv_cursor_location.y - bbox[self.pp_pos].y
                                )
                            )
                        else:
                            position = Vector(
                                (
                                    (self.fit_position[self.pp_pos].x - bbox[self.pp_pos].x) + bb_padding[self.pp_pos].x,
                                    (self.fit_position[self.pp_pos].y - bbox[self.pp_pos].y) + bb_padding[self.pp_pos].y
                                )
                            )

                        move_island(island, uv_layer, position)

                else:
                    loops = loops_by_sel_mode(context, bm)
                    points = [loop[uv_layer].uv for loop in loops]
                    bbox = get_bbox_loops(context)
                    scale = calculate_fit_scale(
                            self.pp_pos,
                            padding,
                            bbox,
                            self.fit_keep_proportion,
                            fit_bounds
                        )

                    scale_points(loops, uv_layer, scale, bbox[self.pp_pos])

                    if pivot_point == "CURSOR":
                        position = Vector(
                            (
                                uv_cursor_location.x - bbox[self.pp_pos].x,
                                uv_cursor_location.y - bbox[self.pp_pos].y
                            )
                        )
                    else:
                        position = Vector(
                            (
                                (self.fit_position[self.pp_pos].x - bbox[self.pp_pos].x) + bb_padding[self.pp_pos].x,
                                (self.fit_position[self.pp_pos].y - bbox[self.pp_pos].y) + bb_padding[self.pp_pos].y
                            )
                        )

                    move_points(loops, uv_layer, position)

                bmesh.update_edit_mesh(me, loop_triangles=False)

        # Rotate Mode
        if transform_mode == "ROTATE":

            def get_all_loops(context):
                objs = resort_objects(context, context.objects_in_mode)
                g_points = set()
                for obj in objs:
                    bm = bmesh.from_edit_mesh(obj.data)
                    uv_layer = bm.loops.layers.uv.verify()
                    loops = loops_by_sel_mode(context, bm)
                    g_points.update({loop[uv_layer].uv.copy().freeze() for loop in loops})
                return list(g_points)

            def get_points(self, bm, uv_layer, orient_sel_mode, island=None, individual=True):
                sync_uv = context.scene.tool_settings.use_uv_select_sync
                if orient_sel_mode and self.pp_pos not in ("tl", "tr", "bl", "br"):
                    # print(f"Orient Selection Mode: {orient_sel_mode}")
                    if individual and island:
                        # For each island with orientation to the selection
                        if sync_uv:
                            pts = [(loop[uv_layer].uv).copy().freeze() for face in island for v in face.verts for loop in v.link_loops if v.select and loop in face.loops]
                        else:
                            pts = [(loop[uv_layer].uv).copy().freeze() for face in island for loop in face.loops if loop[uv_layer].select]
                    else:
                        # For all islands with orientation to the selection
                        if sync_uv:
                            islands_for_process = island_util.get_island(context, bm, uv_layer)
                            pts = [(loop[uv_layer].uv).copy().freeze() for island in islands_for_process for face in island for v in face.verts for loop in v.link_loops if v.select and loop in face.loops]
                        else:
                            pts = [(loop[uv_layer].uv).copy().freeze() for v in bm.verts for loop in v.link_loops if loop[uv_layer].select]
                else:  # With no orient to selection
                    if individual and island:
                        # For each island with no orientation to the selection
                        pts = [(loop[uv_layer].uv).copy().freeze() for face in island for loop in face.loops]
                    else:
                        # For all islands with no orientation to the selection
                        islands_for_process = island_util.get_island(context, bm, uv_layer)
                        pts = [(loop[uv_layer].uv).copy().freeze() for island in islands_for_process for face in island for loop in face.loops]
                return pts

            anchor = ANCHORS[pivot_point](context)
            global_center_anchor = get_bbox_loops(context)["cen"]
            global_angle = r_direction(context, zen_convex_hull_2d(get_all_loops(context)), self.pp_pos)

            if pivot_point not in ("INDIVIDUAL_ORIGINS", "ACTIVE_ELEMENT"):
                points = set()
                for obj in objs:
                    me, bm = get_mesh_data(obj)
                    uv_layer = bm.loops.layers.uv.verify()
                    points.update(get_points(self, bm, uv_layer, self.orient_by_selected))

                if self.orient_by_selected or self.pp_pos not in ("tl", "tr", "bl", "br"):
                    anchor = bound_box(points=zen_convex_hull_2d(list(points)), uv_layer=uv_layer)["cen"]

                angle = r_direction(context, zen_convex_hull_2d(list(points)), self.pp_pos)

            for obj in objs:
                me, bm = get_mesh_data(obj)
                uv_layer = bm.loops.layers.uv.verify()
                if transform_islands:
                    islands_for_process = island_util.get_island(context, bm, uv_layer)

                    for island in islands_for_process:
                        if pivot_point in ("INDIVIDUAL_ORIGINS", "ACTIVE_ELEMENT"):
                            points = set()
                            points.update(get_points(self, bm, uv_layer, self.orient_by_selected, island, individual=True))
                            anchor = bound_box(points=zen_convex_hull_2d(list(points)), uv_layer=uv_layer)["cen"]
                            angle = r_direction(context, zen_convex_hull_2d(list(points)), self.pp_pos)

                        rotate_island(island, uv_layer, angle, anchor)
                else:
                    loops = loops_by_sel_mode(context, bm)
                    points = [loop[uv_layer].uv for loop in loops]

                    # move_2d_cursor(context, global_center_anchor)

                    rotate_points(loops, uv_layer, global_angle, global_center_anchor)

                bmesh.update_edit_mesh(me, loop_triangles=False)

        # Align Mode
        if transform_mode == "ALIGN":

            def increment(pp_cen, b_pos, pos):
                if pp_cen in ("tl", "tr", "cen", "bl", "br"):
                    return Vector((b_pos[0] - pos[0], b_pos[1] - pos[1]))
                elif pp_cen in ("tc", "bc"):
                    return Vector((0, b_pos[1] - pos[1]))
                elif pp_cen in ("lc", "rc"):
                    return Vector((b_pos[0] - pos[0], 0))
                else:
                    return None

            def loop_position(pp_cen, b_pos, pos):
                if pp_cen in ("tl", "tr", "cen", "bl", "br"):
                    return Vector((pos[0], pos[1]))
                elif pp_cen in ("tc", "bc"):
                    return Vector((b_pos[0], pos[1]))
                elif pp_cen in ("lc", "rc"):
                    return Vector((pos[0], b_pos[1]))
                else:
                    return None

            prop_move_incr = scene.zen_uv.tr_move_inc
            base_position = None
            for obj in objs:
                me, bm = get_mesh_data(obj)
                uv_layer = bm.loops.layers.uv.verify()
                if transform_islands:
                    islands_for_process = island_util.get_island(context, bm, uv_layer)
                    for island in islands_for_process:
                        if not base_position:
                            if scene.zen_uv.tr_uv_area_bounds:
                                bbox = UV_AREA_BBOX
                            else:
                                bbox = get_bbox(context)
                            if pivot_point in ("MEDIAN", "INDIVIDUAL_ORIGINS", "MEDIAN_POINT", "ACTIVE_ELEMENT"):
                                base_position = bbox["cen"]

                            elif pivot_point == "CURSOR":
                                base_position = ANCHORS[pivot_point](context)
                            else:
                                if scene.zen_uv.tr_align_center:
                                    base_position = bbox["cen"]
                                else:
                                    base_position = bbox[self.pp_pos]

                        bbox = bound_box(islands=[island, ], uv_layer=uv_layer)
                        if scene.zen_uv.tr_align_center or pivot_point in ("MEDIAN", "INDIVIDUAL_ORIGINS", "MEDIAN_POINT", "ACTIVE_ELEMENT"):
                            position = bbox["cen"]
                        else:
                            position = bbox[self.pp_pos]

                        inc = increment(self.pp_pos, base_position, position)
                        move_island(island, uv_layer, inc)
                else:
                    loops = loops_by_sel_mode(context, bm)
                    if pivot_point in ("MEDIAN", "INDIVIDUAL_ORIGINS", "MEDIAN_POINT", "ACTIVE_ELEMENT"):
                        position = get_bbox_loops(context)["cen"]
                    elif pivot_point == "CURSOR":
                        position = ANCHORS[pivot_point](context)
                    else:
                        position = get_bbox_loops(context)[self.pp_pos]
                    if scene.zen_uv.tr_uv_area_bounds:
                        position = UV_AREA_BBOX[self.pp_pos]

                    for loop in loops:
                        loop[uv_layer].uv = loop_position(self.pp_pos, loop[uv_layer].uv, position)

                bmesh.update_edit_mesh(me, loop_triangles=False)

        # Display UV Widget from HOPS addon
        show_uv_in_3dview(context, use_selected_meshes=True, use_selected_faces=False, use_tagged_faces=True)

        return {'FINISHED'}


class ZUV_OT_RandomizeTransform(bpy.types.Operator):
    bl_idname = "uv.zenuv_randomize_transform"
    bl_label = ZuvLabels.OT_RANDOMIZE_TRANSFORM_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.OT_RANDOMIZE_TRANSFORM_DESC

    def update_scale(self, context):
        if self.uniform_scale:
            self.scale_v = self.scale_u

    def update_move(self, context):
        if self.uniform_move:
            self.move_v = self.move_u

    transform_islands: bpy.props.EnumProperty(
        name=ZuvLabels.PROP_TRANSFORM_TYPE_LABEL,
        description=ZuvLabels.PROP_TRANSFORM_TYPE_DESC,
        items=[
            ("ISLAND", "Island", ""),
            ("SELECTION", "Selection", "")
        ],
        default="ISLAND"
    )
    move_u: FloatProperty(
        name="U",
        description=ZuvLabels.PROP_RAND_POS_DESC,
        default=0.0,
        update=update_move
    )
    move_v: FloatProperty(
        name="V",
        description=ZuvLabels.PROP_RAND_POS_DESC,
        default=0.0,
    )
    uniform_move: BoolProperty(
        name=ZuvLabels.PROP_RAND_LOCK_LABEL,
        description=ZuvLabels.PROP_RAND_LOCK_DESC,
        default=True
    )
    scale_u: FloatProperty(
        name="U",
        description=ZuvLabels.PROP_RAND_SCALE_DESC,
        default=0.0,
        update=update_scale
    )
    scale_v: FloatProperty(
        name="V",
        description=ZuvLabels.PROP_RAND_SCALE_DESC,
        default=0.0,
    )
    uniform_scale: BoolProperty(
        name=ZuvLabels.PROP_RAND_LOCK_LABEL,
        description=ZuvLabels.PROP_RAND_LOCK_DESC,
        default=True
    )
    rotate: FloatProperty(
        name=ZuvLabels.PROP_RAND_ROT_LABEL,
        description=ZuvLabels.PROP_RAND_ROT_DESC,
        default=0.0,
    )
    shaker: IntProperty(
        name=ZuvLabels.PROP_RAND_SHAKE_LABEL,
        description=ZuvLabels.PROP_RAND_SHAKE_DESC,
        default=132,
    )

    def draw_move(self, context):
        col = self.layout.column(align=True)
        col.label(text="Position:")
        row = col.row(align=True)
        row.prop(self, "move_u")
        if self.uniform_move:
            lock_icon = "LOCKED"
            enb = False
        else:
            lock_icon = "UNLOCKED"
            enb = True
        row.prop(self, "uniform_move", icon=lock_icon, icon_only=True)
        col = row.column(align=True)
        col.enabled = enb
        col.prop(self, "move_v", text="")

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "transform_islands")
        if self.transform_islands == 'ISLAND':
            # Move
            self.draw_move(context)
            # Rotate
            layout.separator_spacer()
            layout.label(text="Rotation:")
            row = layout.row(align=True)
            row.prop(self, "rotate", text="")
            # Scale
            layout.separator_spacer()
            col = layout.column(align=True)
            col.label(text="Scale:")
            row = col.row(align=True)
            row.prop(self, "scale_u")
            if self.uniform_scale:
                lock_icon = "LOCKED"
                enb = False
            else:
                lock_icon = "UNLOCKED"
                enb = True
            row.prop(self, "uniform_scale", icon=lock_icon, icon_only=True)
            col = row.column(align=True)
            col.enabled = enb
            col.prop(self, "scale_v", text="")
        else:
            self.draw_move(context)
        layout.separator_spacer()
        layout.prop(self, "shaker")

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'  # and properties.active

    # def invoke(self, context, event):
    #     self.transform_mode = context.scene.zen_uv.tr_type == 'ISLAND'
    #     return self.execute(context)

    def execute(self, context):
        scene = context.scene

        # Type of transformation Islands or Selection
        # self.transform_islands = scene.zen_uv.tr_type == 'ISLAND'

        objs = resort_objects(context, context.objects_in_mode)
        if not objs:
            return {"CANCELLED"}

        pivot_point = scene.zen_uv.tr_pivot_mode
        if pivot_point == '':
            pivot_point = 'CENTER'

        for obj in objs:
            me, bm = get_mesh_data(obj)
            uv_layer = bm.loops.layers.uv.verify()
            if self.transform_islands == 'ISLAND':
                bm.faces.ensure_lookup_table()
                islands_for_process = island_util.get_island(context, bm, uv_layer)
                for island in islands_for_process:
                    # Move
                    position = Vector((random.uniform(-self.move_u, self.move_u), random.uniform(-self.move_v, self.move_v)))
                    move_island(island, uv_layer, position)
                    # Rotate
                    points = [loop[uv_layer].uv for face in island for loop in face.loops]
                    bbox = bound_box(points=zen_convex_hull_2d(points), uv_layer=uv_layer)
                    anchor = bbox["cen"]
                    angle = random.uniform(self.rotate * -1, self.rotate)
                    rotate_island(island, uv_layer, -radians(angle), anchor)
                    # Scale
                    points = [loop[uv_layer].uv for face in island for loop in face.loops]
                    bbox = bound_box(points=zen_convex_hull_2d(points), uv_layer=uv_layer)
                    anchor = bbox["cen"]
                    scale_factor_u = 1 + random.uniform(self.scale_u * -1, self.scale_u)
                    scale_factor_v = 1 + random.uniform(self.scale_v * -1, self.scale_v)
                    if self.uniform_scale:
                        scale = Vector((scale_factor_u, scale_factor_u))
                    else:
                        scale = Vector((scale_factor_u, scale_factor_v))
                    scale_island(island, uv_layer, scale, anchor)

            else:
                loops = loops_by_sel_mode(context, bm)
                f_loops = {loop[uv_layer].uv.copy().freeze(): [lp for lp in loop.vert.link_loops if lp[uv_layer].uv == loop[uv_layer].uv] for loop in loops}
                for loops in f_loops.values():
                    direction = Vector((random.uniform(0, self.move_u), random.uniform(0, self.move_v)))
                    for loop in loops:
                        loop[uv_layer].uv += direction

            bmesh.update_edit_mesh(me, loop_triangles=False)

        return {'FINISHED'}


class ZUV_OT_TrArrange(bpy.types.Operator):
    bl_idname = "uv.zenuv_arrange_transform"
    bl_label = ZuvLabels.OT_ARRANGE_LABEL
    bl_description = ZuvLabels.OT_ARRANGE_DESC
    bl_options = {'REGISTER', 'UNDO'}

    # def update_uniform(self, context):
    #     if self.uniform_quant:
    #         self.count_v = 0
    #         self.quant_v = 0

    def upd_count_u(self, context):
        if self.count_u != 0:
            self.quant.x = 1 / self.count_u
        else:
            self.quant.x = 0

    def upd_count_v(self, context):
        if self.count_v != 0:
            self.quant.y = 1 / self.count_v
        else:
            self.quant.y = 0

    def upd_quant_u(self, context):
        self.quant.x = self.quant_u

    def upd_quant_v(self, context):
        self.quant.y = self.quant_v

    def update_input_mode(self, context):
        if self.input_mode == "SIMPLIFIED":
            if self.quant.x != 0:
                self.count_u = 1 / self.quant.x
            else:
                self.count_u = 0
            if self.quant.y != 0:
                self.count_v = 1 / self.quant.y
            else:
                self.count_v = 0

        elif self.input_mode == "ADVANCED":
            self.quant_u = self.quant.x
            self.quant_v = self.quant.y

    quant: FloatVectorProperty(
        name="",
        size=2,
        default=(0.0, 0.0),
        subtype='XYZ',
        options={"HIDDEN"}
    )
    quant_u: FloatProperty(
        name=ZuvLabels.PROP_ARRANGE_QUANT_U_LABEL,
        description=ZuvLabels.PROP_ARRANGE_QUANT_U_DESC,
        precision=3,
        default=0.0,
        step=0.01,
        min=0.0,
        update=upd_quant_u
    )
    quant_v: FloatProperty(
        name=ZuvLabels.PROP_ARRANGE_QUANT_V_LABEL,
        description=ZuvLabels.PROP_ARRANGE_QUANT_V_DESC,
        precision=3,
        default=0.0,
        step=0.01,
        min=0.0,
        update=upd_quant_v
    )
    count_u: IntProperty(
        name=ZuvLabels.PROP_ARRANGE_COUNT_U_LABEL,
        description=ZuvLabels.PROP_ARRANGE_COUNT_U_DESC,
        default=0,
        min=0,
        update=upd_count_u
    )
    count_v: IntProperty(
        name=ZuvLabels.PROP_ARRANGE_COUNT_V_LABEL,
        description=ZuvLabels.PROP_ARRANGE_COUNT_V_DESC,
        default=0,
        min=0,
        update=upd_count_v
    )
    reposition: FloatVectorProperty(
        name=ZuvLabels.PROP_ARRANGE_POSITION_LABEL,
        description=ZuvLabels.PROP_ARRANGE_POSITION_DESC,
        size=2,
        precision=4,
        step=0.01,
        default=(0.0, 0.0),
        subtype='XYZ'
    )
    limit: FloatVectorProperty(
        name=ZuvLabels.PROP_ARRANGE_LIMIT_LABEL,
        description=ZuvLabels.PROP_ARRANGE_LIMIT_DESC,
        size=2,
        precision=3,
        min=0.0,
        default=(1.0, 1.0),
        subtype='XYZ'
    )
    input_mode: bpy.props.EnumProperty(
        name=ZuvLabels.PROP_ARRANGE_INP_MODE_LABEL,
        description=ZuvLabels.PROP_ARRANGE_INP_MODE_DESC,
        items=[
            ("SIMPLIFIED", ZuvLabels.PROP_ARRANGE_INP_MODE_SIMPL_LABEL, ""),
            ("ADVANCED", ZuvLabels.PROP_ARRANGE_INP_MODE_ADV_LABEL, ""),
        ],
        default="SIMPLIFIED",
        update=update_input_mode
    )
    start_from: bpy.props.EnumProperty(
        name=ZuvLabels.PROP_ARRANGE_START_FROM_LABEL,
        description=ZuvLabels.PROP_ARRANGE_START_FROM_DESC,
        items=[
            ("INPLACE", "In Place", ""),
            ("BOTTOM", "Bottom", ""),
            ("CENTER", "Center", ""),
            ("TOP", "Top", ""),
            ("CURSOR", "Cursor", "")
        ],
        default="INPLACE"
    )
    randomize: BoolProperty(
        name=ZuvLabels.PROP_ARRANGE_RANDOMIZE_LABEL,
        description=ZuvLabels.PROP_ARRANGE_RANDOMIZE_DESC,
        default=False
    )
    seed: IntProperty(
        name=ZuvLabels.PROP_ARRANGE_SEED_LABEL,
        description=ZuvLabels.PROP_ARRANGE_SEED_DESC,
        default=132,
    )
    scale: FloatProperty(
        name=ZuvLabels.PROP_ARRANGE_SCALE_LABEL,
        description=ZuvLabels.PROP_ARRANGE_SCALE_DESC,
        precision=3,
        default=1.0,
        step=0.01,
        min=0.01
    )

    def draw_quant(self, context):
        self.layout.separator_spacer()
        col = self.layout.column(align=True)
        row = col.row(align=True)
        if self.input_mode == "SIMPLIFIED":
            mode = "count"
        elif self.input_mode == "ADVANCED":
            mode = "quant"
        row.prop(self, mode + "_u")
        col = row.column(align=True)
        col.prop(self, mode + "_v")

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "input_mode")
        row = layout.row(align=True)
        row.prop(self, "start_from")

        self.draw_quant(context)
        if not self.input_mode == "SIMPLIFIED":
            layout.prop(self, "limit")
        layout.label(text="Correction:")
        box = layout.box()
        box.prop(self, "reposition")
        row = box.row(align=True)
        row.prop(self, "randomize")
        if self.randomize:
            row.prop(self, "seed")
        box.prop(self, "scale")

    def invoke(self, context, event):
        objs = resort_objects(context, context.objects_in_mode)
        if not objs:
            return {"CANCELLED"}
        self.criterion_data = dict()
        counter = 0
        for obj in objs:
            me, bm = get_mesh_data(obj)
            uv_layer = bm.loops.layers.uv.verify()
            bm.faces.ensure_lookup_table()
            islands = island_util.get_island(context, bm, uv_layer)
            for island in islands:
                cluster = Cluster(context, obj, island)
                criterion = counter
                self.criterion_data.update(
                    {
                        counter:
                            {
                                "cluster": cluster.geometry["faces_ids"],
                                "bbox": cluster.bbox,
                                "center": cluster.bbox["cen"],
                                "criterion": criterion,
                                "object": obj.name
                            }
                    }
                )
                counter += 1
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        if self.input_mode == "SIMPLIFIED":
            self.limit = Vector((1.0, 1.0))
        reposition = self.reposition
        base_position = Vector((0.0, 0.0))
        criterion_chart = sorted(self.criterion_data.keys())
        position_chart = sorted(criterion_chart, key=lambda x: self.criterion_data[x]["center"].x, reverse=False)

        for _id in position_chart:
            if self.criterion_data[_id]["center"].x > 0:
                break

        if self.start_from == "TOP":
            base_position = Vector((0, 1 - self.criterion_data[_id]["bbox"]["len_y"]))
        elif self.start_from == "BOTTOM":
            base_position = Vector((0.0, 0.0))
        elif self.start_from == "CENTER":
            base_position = Vector((0, 0.5 - self.criterion_data[_id]["bbox"]["len_y"] / 2))
        elif self.start_from == "INPLACE":
            base_position = self.criterion_data[_id]["bbox"]["bl"]
        elif self.start_from == "CURSOR":
            base_position = pp_cursor(context)

        if self.randomize:
            random.shuffle(criterion_chart)

        real_limit = base_position + reposition + self.limit
        current = Vector((0.0, 0.0))
        for _id in criterion_chart:
            cluster = self.criterion_data[_id]
            cl_size = Vector((cluster["bbox"]["len_x"], cluster["bbox"]["len_y"])) * 0.5
            cl_position = base_position + cl_size + reposition

            if self.limit.x != 0:
                if cl_position.x + current.x > real_limit.x:
                    current.x = 0
                    current.y += self.quant.y

            if self.limit.y != 0:
                if cl_position.y + current.y > real_limit.y:
                    current.y = 0

            self.criterion_data[_id].update({"position": cl_position + current})
            current = current + Vector((self.quant.x, 0))

        # Set Cluster to position
        for cluster in self.criterion_data.values():
            cl = Cluster(context, cluster['object'], cluster["cluster"])
            cl.move_to(cluster["position"])
            cl.scale([self.scale, self.scale], cl.bbox["bl"])
            cl.update_mesh()

        return {'FINISHED'}


uv_transform_classes = (
    ZUV_OT_UnifiedTransform,
    ZUV_OT_RandomizeTransform,
    ZUV_OT_TrArrange
)

if __name__ == '__main__':
    pass
