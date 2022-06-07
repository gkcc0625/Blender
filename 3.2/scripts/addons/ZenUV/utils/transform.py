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

"""Zen UV Transform utils """
import bmesh
import random
from math import sin, cos, pi
from mathutils import Vector
from mathutils.geometry import convex_hull_2d, box_fit_2d
from ZenUV.utils.generic import (
    resort_objects,
    loops_by_sel_mode
)
from ZenUV.utils import get_uv_islands as island_util

UV_AREA_BBOX = {
    'bl': Vector((0.0, 0.0)),
    'tl': Vector((0.0, 1.0)),
    'tr': Vector((1.0, 1.0)),
    'br': Vector((1.0, 0.0)),
    'cen': Vector((0.5, 0.5)),
    'tc': Vector((0.5, 1.0)),
    'rc': Vector((1.0, 0.5)),
    'bc': Vector((0.5, 0.0)),
    'lc': Vector((0.0, 0.5)),
    'len_x': 1.0,
    'len_y': 1.0
    }


def align_vertical(points, increment_angle=0, base_direction="tl"):
    angle = box_fit_2d(points)
    r_points = []
    rotated = make_rotation_transformation(angle, (0, 0))
    for i in range(len(points)):
        r_points.append(rotated(points[i]))
    bbox = bound_box(points=r_points)
    if bbox["len_x"] > bbox["len_y"]:
        angle += pi / 2
    return angle


def align_auto(points, increment_angle=0, base_direction="tl"):
    angle = align_vertical(points)
    if (0.785 < abs(angle) < 2.356) or (3.927 < abs(angle) < 5.498):
        return angle + pi / 2
    return angle


def align_horizontal(points, increment_angle=0, base_direction="tl"):
    return align_vertical(points) + pi / 2


def calc_length_of_loops(uv_layer, loop_stripe):
    """
    Input: List. Loop Stripe defined by loops
    Output: List. Length of each loop
    """
    loop_stripe_length = []
    for idx in range(len(loop_stripe) - 1):
        start_loop = loop_stripe[idx][0][uv_layer].uv
        next_loop = loop_stripe[idx + 1][0][uv_layer].uv
        loop_stripe_length.append((start_loop - next_loop).length)
    return loop_stripe_length


def calculate_fit_scale(pp_pos, padding, bbox, keep_proportion=True, bounds=Vector((0.0, 0.0))):
    factor_u = (bounds.x - padding * 2) / bbox['len_x']
    factor_v = (bounds.y - padding * 2) / bbox['len_y']

    # Check fit proportions
    if keep_proportion:
        # Scale to fit bounds
        min_factor = min(factor_u, factor_v)
        scale = (min_factor, min_factor)

        # Scale to fit one side
        if pp_pos in ("lc", "rc"):
            scale = (factor_v, factor_v)
        elif pp_pos in ("tc", "bc"):
            scale = (factor_u, factor_u)
    else:
        scale = (factor_u, factor_v)
    return scale


def get_bbox(context):
    objs = resort_objects(context, context.objects_in_mode)
    bb = []
    for obj in objs:
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()
        islands = island_util.get_island(context, bm, uv_layer)
        if islands:
            cbbox = bound_box(islands=islands, uv_layer=uv_layer)
            bb.extend((cbbox["bl"], cbbox["tr"]))
    gbb = bound_box(points=bb)
    if gbb["len_x"] + gbb["len_y"] == 0:
        gbb = UV_AREA_BBOX
    return gbb


def get_bbox_loops(context):
    objs = resort_objects(context, context.objects_in_mode)
    bb = []
    for obj in objs:
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()
        loops = loops_by_sel_mode(context, bm)
        points = [loop[uv_layer].uv for loop in loops]
        # islands = island_util.get_island(context, bm, uv_layer)
        if loops:
            cbbox = bound_box(points=points, uv_layer=uv_layer)
            bb.extend((cbbox["bl"], cbbox["tr"]))
    gbb = bound_box(points=bb)
    res = Vector((0.0, 0.0))
    for value in gbb.values():
        if isinstance(value, Vector):
            res += value
    if res == Vector((0.0, 0.0)):
        gbb = UV_AREA_BBOX
    return gbb


def centroid(vertexes):
    """ Calculate Centroid of the given vertices set """
    # vertexes = zen_convex_hull_2d(vertexes)
    x_list = [vertex[0] for vertex in vertexes]
    y_list = [vertex[1] for vertex in vertexes]
    length = len(vertexes)
    if length == 0:
        length = 1
    x = sum(x_list) / length
    y = sum(y_list) / length
    return Vector((x, y))


def centroid_3d(vertexes):
    """ Calculate Centroid of the given vertices set """
    # vertexes = zen_convex_hull_2d(vertexes)
    x_list = [vertex[0] for vertex in vertexes]
    y_list = [vertex[1] for vertex in vertexes]
    z_list = [vertex[2] for vertex in vertexes]
    length = len(vertexes)
    if length == 0:
        length = 1
    x = sum(x_list) / length
    y = sum(y_list) / length
    z = sum(z_list) / length
    return Vector((x, y, z))


def bound_box(islands=None, points=None, uv_layer=None):
    """ Return Dict with bbox parameters as Vectors
    bl: bottom left
    tl: top left
    tr: top right
    br: bottom right
    cen: center
    len_x: length by X
    len_y: length by Y
"""
    minX = +1000
    minY = +1000
    maxX = -1000
    maxY = -1000
    if islands and uv_layer:
        points = []
        for island in islands:
            points.extend([loop[uv_layer].uv for face in island for loop in face.loops])
    if points:
        points = zen_convex_hull_2d(points)
        for point in points:
            u, v = point
            minX = min(u, minX)
            minY = min(v, minY)
            maxX = max(u, maxX)
            maxY = max(v, maxY)
    if minX == +1000 and minY == +1000 and maxX == -1000 and maxY == -1000:
        minX = minY = maxX = maxY = 0
    bbox = {
        "bl": Vector((minX, minY)),
        "tl": Vector((minX, maxY)),
        "tr": Vector((maxX, maxY)),
        "br": Vector((maxX, minY)),
        "cen": (Vector((minX, minY)) + Vector((maxX, maxY))) / 2,
        "tc": (Vector((minX, maxY)) + Vector((maxX, maxY))) / 2,
        "rc": (Vector((maxX, maxY)) + Vector((maxX, minY))) / 2,
        "bc": (Vector((maxX, minY)) + Vector((minX, minY))) / 2,
        "lc": (Vector((minX, minY)) + Vector((minX, maxY))) / 2,
        "len_x": (Vector((maxX, maxY)) - Vector((minX, maxY))).length,
        "len_y": (Vector((minX, minY)) - Vector((minX, maxY))).length
    }
    return bbox


def scale2d(v, s, p):
    """ v - coordinates; s - scale by axis [x,y]; p - anchor point """
    return (p[0] + s[0] * (v[0] - p[0]), p[1] + s[1] * (v[1] - p[1]))


def make_rotation_transformation(angle, origin=(0, 0)):
    """ Calculate rotation transformation by the angle and origin """
    cos_theta, sin_theta = cos(angle), sin(angle)
    x0, y0 = origin

    def xform(point):
        x, y = point[0] - x0, point[1] - y0
        return (x * cos_theta - y * sin_theta + x0,
                x * sin_theta + y * cos_theta + y0)
    return xform


def rotate_island(island, uv_layer, angle, anchor):
    """ Perform rotation of the given island """
    # print("Island turned to :", angle)
    rotated = make_rotation_transformation(angle, anchor)
    for face in island:
        for loop in face.loops:
            loop[uv_layer].uv = rotated(loop[uv_layer].uv)


def rotate_points(points, uv_layer, angle, anchor):
    """ Perform rotation of the given island """
    # print("Island turned to :", angle)
    rotated = make_rotation_transformation(angle, anchor)
    for loop in points:
        loop[uv_layer].uv = rotated(loop[uv_layer].uv)


# def rotate_points(island, uv_layer, angle, anchor):
#     """ Perform rotation of the given island """
#     # print("Island turned to :", angle)
#     rotated = make_rotation_transformation(angle * -1, anchor)
#     for face in island:
#         for loop in face.loops:
#             loop[uv_layer].uv = rotated(loop[uv_layer].uv)


def rotate_island_to_edge(island, uv_layer, angle, anchor):
    """ Perform rotation of the given island by given edge  orientation """
    # print("Island turned to :", angle)
    rotated = make_rotation_transformation(angle * -1, anchor)
    for face in island:
        for loop in face.loops:
            loop[uv_layer].uv = rotated(loop[uv_layer].uv)


def move_island(island, uv_layer, move_vector):
    """ Move the island by defined increment """
    for face in island:
        for loop in face.loops:
            loop[uv_layer].uv += move_vector


def move_points(points, uv_layer, move_vector):
    """ Move the points by defined increment """
    for loop in points:
        loop[uv_layer].uv += move_vector


def random_points_positions(points, uv_layer, limits):
    """ Move the points by defined increment """
    for loop in points:
        direction = Vector((random.uniform(0, limits[0]), random.uniform(0, limits[1])))
        loop[uv_layer].uv += direction


def move_island_to_position(island, uv_layer, position):
    """Move the island to defined position"""
    island_cen = bound_box(islands=[island], uv_layer=uv_layer)["cen"]
    move_vector = Vector(
        (
            position.x - island_cen.x,
            position.y - island_cen.y
        )
    )
    uv_island = [loop[uv_layer] for face in island for loop in face.loops]
    for loop in uv_island:
        loop.uv += move_vector


def move_points_to_position(loops, uv_layer, position):
    """Move points to defined position"""
    for loop in loops:
        move_vector = Vector(
            (
                position.x - loop[uv_layer].uv.x,
                position.y - loop[uv_layer].uv.y
            )
        )
        loop[uv_layer].uv += move_vector


def scale_island(island, uv_layer, scale, anchor):
    """ Scale island by given scale from given anchor """
    loops = [loop for face in island for loop in face.loops]
    for loop in loops:
        loop[uv_layer].uv = scale2d(loop[uv_layer].uv, scale, anchor)


def scale_points(points, uv_layer, scale, anchor):
    """ Scale island by given scale from given anchor """
    for loop in points:
        loop[uv_layer].uv = scale2d(loop[uv_layer].uv, scale, anchor)


def move_island_sort(island, uv_layer, move_vector):
    """ Move island by defined increment for Finished system"""
    # vertex_counter = 0
    for face in island:
        # if not face.select:
        for loop in face.loops:
            # vertex_counter += 1
            loop[uv_layer].uv -= move_vector


def uv_from_vert_first(uv_layer, v):
    for loop in v.link_loops:
        uv_data = loop[uv_layer]
        return uv_data.uv
    return None


def uv_from_vert_average(uv_layer, v):
    uv_average = Vector((0.0, 0.0))
    total = 0.0
    for loop in v.link_loops:
        uv_average += loop[uv_layer].uv
        total += 1.0

    if total != 0.0:
        return uv_average * (1.0 / total)
    else:
        return None


def filter_basis_selection(_b_selection):
    container = []
    for i in _b_selection:
        if i not in container:
            container.append(i)
    return container


def islands_uv(islands, uv_layer):
    points = []
    for island in islands:
        points.extend([loop[uv_layer].uv for face in island for loop in face.loops])
    return points


def zen_convex_hull_2d(points):
    ch_indices = convex_hull_2d(points)
    ch_points = []
    for i in ch_indices:
        ch_points.append(points[i])
    return ch_points
