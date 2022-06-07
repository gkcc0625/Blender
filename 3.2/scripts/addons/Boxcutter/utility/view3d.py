import bpy
import math
import bl_ui


from mathutils import Matrix, Vector
from mathutils.geometry import intersect_line_plane

from bpy_extras.view3d_utils import region_2d_to_origin_3d, region_2d_to_vector_3d, location_3d_to_region_2d, region_2d_to_location_3d

from . import addon, tool, method_handler


def location2d_to_origin3d(x, y):
    return region_2d_to_origin_3d(bpy.context.region, bpy.context.region_data, (x, y))


def location2d_to_vector3d(x, y):
    return region_2d_to_vector_3d(bpy.context.region, bpy.context.region_data, (x, y))


def location2d_to_intersect3d(x, y, location, normal, origin=None):
    if not origin:
        origin = location2d_to_origin3d(x, y)
    return intersect_line_plane(origin, origin + location2d_to_vector3d(x, y), location, normal)


def location3d_to_location2d(location, region_3d=None, persp_matrix_invert=False):
    if region_3d or persp_matrix_invert:
        region_3d = region_3d or bpy.context.space_data.region_3d

        if not region_3d.is_perspective:
            location = region_3d.view_matrix.inverted() @ Vector(location)

    return location_3d_to_region_2d(bpy.context.region, bpy.context.region_data, location)


def location2d_to_location3d(x, y, location, region_3d=None, persp_matrix_invert=False):
    if region_3d or persp_matrix_invert:
        region_3d = region_3d or bpy.context.space_data.region_3d

        if not region_3d.is_perspective:
            location = region_3d.view_matrix.inverted() @ Vector(location)

    return region_2d_to_location_3d(bpy.context.region, bpy.context.region_data, (x, y), location)


def track_matrix(normal=Vector(), location=Vector(), matrix=Matrix(), up='Z', align='Y'):
    track_mat = (matrix.copy().to_3x3().inverted() @ normal).to_track_quat(up, align).to_matrix().to_4x4()
    track_mat.translation = location if location != Vector() else matrix.translation

    return track_mat


def intersect_plane(x, y, location, matrix=Matrix()):
    matrix = matrix.copy().to_3x3()
    inverse = matrix.inverted()

    props = (x, y, location, matrix @ Vector((0, 0, 1)))
    intersect = location2d_to_intersect3d(*props)

    if intersect:
        return inverse @ intersect

    return None


def orientation_get():
    if not hasattr(bpy.context, 'region_data'):
        return 'UNDEFINED'

    _round = lambda x: round(x, 4)
    orientation = {
        (0.0, 0.0, 0.0): 'TOP',
        (_round(math.pi), 0.0, 0.0): 'BOTTOM',
        (_round(math.pi * 0.5), 0.0, 0.0): 'FRONT',
        (_round(math.pi * 0.5), 0.0, _round(math.pi)): 'BACK',
        (_round(math.pi * 0.5), 0.0, _round(-math.pi * 0.5)): 'LEFT',
        (_round(math.pi * 0.5), 0.0, _round(math.pi * 0.5)): 'RIGHT'}

    view_rotation = bpy.context.region_data.view_rotation.to_euler()
    return orientation.get(tuple(map(_round, view_rotation)), 'UNDEFINED')


orientation = method_handler(orientation_get)
