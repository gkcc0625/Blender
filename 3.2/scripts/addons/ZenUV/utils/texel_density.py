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

""" Zen UV Texel Density utilities"""

import math
import bmesh
from mathutils import Vector, Matrix, Color
import numpy as np
from ZenUV.ui.labels import ZuvLabels
from ZenUV.utils.transform import centroid, scale2d
from ZenUV.utils import get_uv_islands as island_util
from ZenUV.utils import vc_processor as vc
from ZenUV.utils.generic import select_all, get_mesh_data, face_indexes_by_sel_mode, resort_by_type_mesh
from ZenUV.prop.zuv_preferences import get_prefs
import colorsys
from ZenUV.utils.generic import Timer

UNITS_CONV = {
        'km': 100000,
        'm': 100,
        'cm': 1,
        'mm': 0.1,
        'um': 0.0001,
        'mil': 160934,
        'ft': 30.48,
        'in': 2.54,
        'th': 0.00254
    }


def gathering_input_data():
    addon_prefs = get_prefs()
    if addon_prefs.td_im_size_presets == 'Custom':
        image_size = [addon_prefs.TD_TextureSizeX, addon_prefs.TD_TextureSizeY]
    else:
        image_size = [addon_prefs.TD_TextureSizeX, addon_prefs.TD_TextureSizeX]
    return {
        "td": addon_prefs.TexelDensity,
        "im_size": image_size,
        "units": UNITS_CONV[addon_prefs.td_unit],
        "set_mode": addon_prefs.td_set_mode,
        "obj_mode": False
        }


def get_td_color_map_from(_obj, map_name=vc.Z_TD_BALANCED_V_MAP_NAME):
    """ Return Texel Density VC Layer or None """
    return _obj.data.vertex_colors.get(map_name) or None


def is_td_display_activated(context):
    objs = resort_by_type_mesh(context)
    for obj in objs:
        if obj.data.vertex_colors.get(vc.Z_TD_BALANCED_V_MAP_NAME):
            return True
    return False


def Saturate(val):
    return max(min(val, 1), 0)


def Value_To_Color(value, range_min, range_max):
    remaped_value = (value - range_min) / (range_max - range_min)
    remaped_value = Saturate(remaped_value)
    hue = (1 - remaped_value) * 0.67
    color = colorsys.hsv_to_rgb(hue, 1, 1)
    color4 = (color[0], color[1], color[2], 1)
    return color4


def get_td_data(context, objs, td_inputs, per_face=False):
    generic_color = Color((0.0, 0.0, 0.0))
    td_dict = dict()
    for obj in objs:
        if obj.mode == "EDIT":
            bm = bmesh.from_edit_mesh(obj.data)
            obj_td_data = collect_td_data(context, td_inputs, per_face, generic_color, obj, bm)
            for value, data in obj_td_data.items():
                if value not in td_dict:
                    td_dict[value] = data
                else:
                    td_dict[value]["objs"].update(data["objs"])
            # print("Time in get td: ", t.delta())
        else:
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            obj_td_data = collect_td_data(context, td_inputs, per_face, generic_color, obj, bm)
            for value, data in obj_td_data.items():
                if value not in td_dict:
                    td_dict[value] = data
                else:
                    td_dict[value]["objs"].update(data["objs"])
            bm.free()
    return td_dict


def collect_td_data(context, td_inputs, per_face, generic_color, obj, bm):
    td_set = dict()
    if per_face:
        islands = [[f, ] for f in bm.faces]
    else:
        islands = island_util.get_islands(bm)

    for island in islands:
        idxs_island = [f.index for f in island]
        current_td = get_texel_density_from_faces(context, obj, island, td_inputs)
        if round(current_td[0], 2) not in td_set.keys():
            td_set[current_td[0]] = {"objs": {obj.name: [idxs_island]}, "color": generic_color}
        else:
            if obj.name not in td_set[current_td[0]]["objs"].keys():
                td_set[current_td[0]]["objs"].update({obj.name: [idxs_island]})
            else:
                td_set[current_td[0]]["objs"][obj.name].append(idxs_island)
    return td_set


def polygon_area(p):
    return 0.5 * abs(sum(x0*y1 - x1*y0 for ((x0, y0), (x1, y1)) in segments(p)))


def segments(p):
    return zip(p, p[1:] + [p[0]])


def UV_faces_area(_faces, uv_layer):
    return sum([polygon_area([loop[uv_layer].uv for loop in face.loops]) for face in _faces])


def calculate_texel_density(context, uv_layer, faces, td_inputs):
    # addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
    # if addon_prefs.td_im_size_presets == 'Custom':
    #     image_size = [addon_prefs.TD_TextureSizeX, addon_prefs.TD_TextureSizeY]
    # else:
    #     image_size = [addon_prefs.TD_TextureSizeX, addon_prefs.TD_TextureSizeX]
    image_size = td_inputs['im_size']
    max_side = max(image_size)
    image_aspect = max(image_size) / min(image_size)
    # Calculating GEOMETRY AREA
    geometry_area = sum(f.calc_area() for f in faces)
    # Calculating UV AREA
    uv_area = UV_faces_area(faces, uv_layer)

    if geometry_area > 0 and uv_area > 0:
        texel_density = ((max_side / math.sqrt(image_aspect)) * math.sqrt(uv_area)) / (math.sqrt(geometry_area) * 100) / context.scene.unit_settings.scale_length
    else:
        texel_density = 0.0001
    # texel_density = texel_density * float(addon_prefs.td_unit)
    texel_density = texel_density * float(td_inputs["units"])
    return [round(texel_density, 2), round(uv_area * 100, 2)]


def calculate_uv_coverage(context, uv_layer, faces):
    uv_area = UV_faces_area(faces, uv_layer)
    return uv_area * 100


def calc_averaged_td(context, uv_layer, islands_for_td, td_inputs):
    """ Calculate averaged texel desity """
    td_sum = 0
    uv_coverage = 0
    for island in islands_for_td:
        td = calculate_texel_density(context, uv_layer, island, td_inputs)
        td_sum += td[0]
        uv_coverage += td[1]
    return [td_sum / len(islands_for_td), uv_coverage]


def get_texel_density_from_faces(context, obj, faces, td_inputs):
    """ Return list [texel density, uv coverage] """
    # Get Selection info from object
    # bmo = bmesh.from_edit_mesh(obj.data)
    overall_td = []
    faces_indexes = [f.index for f in faces]
    # bmesh.update_edit_mesh(obj.data, loop_triangles=False)
    obj.update_from_editmode()

    dg = context.evaluated_depsgraph_get()
    bm = bmesh.new()

    bm.from_object(obj, dg)
    bm.transform(obj.matrix_world)
    # loc, rot, sca = obj.matrix_world.decompose()
    # bmesh.ops.scale(bm, vec=sca, space=obj.matrix_world, verts=bm.verts)
    uv_layer = bm.loops.layers.uv.verify()
    bm.faces.ensure_lookup_table()

    select_all(bm, False)

    # Collect faces in bm
    faces_for_td = []
    for index in faces_indexes:
        faces_for_td.append(bm.faces[index])

    overall_td.append(calc_averaged_td(context, uv_layer, [faces_for_td], td_inputs))
    bm.free()
    td_sum = 0
    uv_coverage = 0
    for td_data in overall_td:
        td_sum += td_data[0]
        uv_coverage += td_data[1]

    return [td_sum / len(overall_td), uv_coverage]


def get_texel_density_in_obj_mode(context, objs, td_inputs):
    if objs:
        overall_td = []
        for obj in objs:
            obj.update_from_editmode()

            dg = context.evaluated_depsgraph_get()
            bm = bmesh.new()

            bm.from_object(obj, dg)
            bm.transform(obj.matrix_world)
            uv_layer = bm.loops.layers.uv.verify()
            bm.faces.ensure_lookup_table()
            overall_td.append(calc_averaged_td(context, uv_layer, [bm.faces], td_inputs))
            bm.free()
        td_sum = 0
        uv_coverage = 0
        for td_data in overall_td:
            td_sum += td_data[0]
            uv_coverage += td_data[1]
        return [td_sum / len(overall_td), uv_coverage]

    return [0.0001, 0.0001]


def get_texel_density(context, objs, td_inputs):
    if objs:
        overall_td = []
        for obj in objs:
            # Get Selection info from object
            bmo = bmesh.from_edit_mesh(obj.data)
            faces_indexes = face_indexes_by_sel_mode(context, bmo)
            # selected_edges_indexes = [e.index for e in bmo.edges if e.select]
            # selected_verts_indexes = [v.index for v in bmo.verts if v.select]
            # bmesh.update_edit_mesh(obj.data, loop_triangles=False)
            obj.update_from_editmode()

            dg = context.evaluated_depsgraph_get()
            bm = bmesh.new()

            bm.from_object(obj, dg)
            bm.transform(obj.matrix_world)
            uv_layer = bm.loops.layers.uv.verify()
            # bm.faces.ensure_lookup_table()
            # bm.edges.ensure_lookup_table()
            bm.faces.ensure_lookup_table()

            # select_all(bm, False)

            # Select faces in bm
            # for index in selected_faces_indexes:
            #     bm.faces[index].select = True
            # for index in selected_edges_indexes:
            #     bm.edges[index].select = True
            # for index in selected_verts_indexes:
            #     bm.verts[index].select = True
            # islands_for_td = island_util.get_islands_by_vert_list_indexes(context, bm, selected_verts_indexes, uv_layer)
            islands_for_td = island_util.get_islands_by_face_list_indexes(bm, faces_indexes)
            # islands_for_td = island_util.get_island(context, bm, uv_layer)
            overall_td.append(calc_averaged_td(context, uv_layer, islands_for_td, td_inputs))
            bm.free()
        td_sum = 0
        uv_coverage = 0
        for td_data in overall_td:
            td_sum += td_data[0]
            uv_coverage += td_data[1]

        return [td_sum / len(overall_td), uv_coverage]
    return [0.0001, 0.0001]


def calculate_overall_centroid(uv_layer, islands):
    points = []
    for island in islands:
        points.extend([loop[uv_layer].uv for face in island for loop in face.loops])
    return Vector(centroid(points))


def set_texel_density_to_faces(context, obj, island, td_inputs):

    def bm_from_edit(context, obj):
        return bmesh.from_edit_mesh(obj.data)

    def set_to_edit(obj, bm):
        bmesh.update_edit_mesh(obj.data, loop_triangles=False)

    def data_per_island(context, td_inputs, uv_layer, island):
        anchor = Vector(centroid(([loop[uv_layer].uv for face in island for loop in face.loops])))
        current_td = get_texel_density_from_faces(context, obj, island, td_inputs)[0]
        return anchor, current_td

    bm = bm_from_edit(context, obj)
    uv_layer = bm.loops.layers.uv.verify()

    anchor, current_td = data_per_island(context, td_inputs, uv_layer, island)
    scale = td_inputs["td"] / current_td
    if scale != 1:
        loops = [loop for face in island for loop in face.loops]
        for loop in loops:
            loop[uv_layer].uv = scale2d(loop[uv_layer].uv, [scale, scale], anchor)

    set_to_edit(obj, bm)


def set_texel_density(context, objs, td_inputs):

    def bm_from_object(context, obj):
        dg = context.evaluated_depsgraph_get()
        bm = bmesh.new()
        bm.from_object(obj, dg)
        return bm

    def bm_from_edit(context, obj):
        return bmesh.from_edit_mesh(obj.data)

    def data_per_island(context, td_inputs, uv_layer, island, overall_td, overall_centroid):
        anchor = Vector(centroid(([loop[uv_layer].uv for face in island for loop in face.loops])))
        current_td = calculate_texel_density(context, uv_layer, island, td_inputs)[0]
        return anchor, current_td

    def data_overall(context, td_inputs, uv_layer, island, overall_td, overall_centroid):
        anchor = overall_centroid
        current_td = overall_td
        return anchor, current_td

    def get_islands_obj(context, bm, uv_layer):
        # bm.faces.ensure_lookup_table()
        return island_util.get_islands(bm)

    def get_islands_event(context, bm, uv_layer):
        # bm.faces.ensure_lookup_table()
        return island_util.get_island(context, bm, uv_layer)

    def set_to_obj(obj, bm):
        bm.to_mesh(obj.data)
        bm.free()

    def set_to_edit(obj, bm):
        bmesh.update_edit_mesh(obj.data, loop_triangles=False)

    def finish_bm(obj, bm):
        bm.free()

    td_set_mesh_data = {'island': data_per_island, 'overall': data_overall}
    td_get_islands = {True: get_islands_obj, False: get_islands_event}
    td_set_changes = {True: set_to_obj, False: set_to_edit}
    get_bm_from = {True: bm_from_object, False: bm_from_edit}
    td_finish_bm = {True: finish_bm, False: set_to_edit}

    def to_rev_scale_matrix(sca):
        matrix = Matrix()
        matrix[0][0] = 1 / sca[0]
        matrix[1][1] = 1 / sca[1]
        matrix[2][2] = 1 / sca[2]
        return matrix

    def to_scale_matrix(sca):
        matrix = Matrix()
        matrix[0][0] = sca[0]
        matrix[1][1] = sca[1]
        matrix[2][2] = sca[2]
        return matrix

    if objs:
        per_object_centroid = []
        per_object_td = 0
        overall_islands_count = 0
        # Calculate anchor and scale for Overall mode
        for obj in objs:
            # bm = bm_from_object(context, obj)
            bm = get_bm_from[td_inputs["obj_mode"]](context, obj)

            loc, rot, init_scale = obj.matrix_world.decompose()
            rev_scale_matrix = to_rev_scale_matrix(init_scale)
            scale_matrix = to_scale_matrix(init_scale)
            bm.transform(scale_matrix)

            uv_layer = bm.loops.layers.uv.verify()
            islands_for_td = td_get_islands[td_inputs["obj_mode"]](context, bm, uv_layer)
            # # EDIT Mode
            # islands_for_td = island_util.get_island(context, bm, uv_layer)
            # # OBJ Mode
            # islands_for_td = island_util.get_islands(bm)
            per_object_td += calc_averaged_td(context, uv_layer, islands_for_td, td_inputs)[0]
            per_object_centroid.append(calculate_overall_centroid(uv_layer, islands_for_td))
            overall_islands_count += 1
            bm.transform(rev_scale_matrix)
            td_finish_bm[td_inputs["obj_mode"]](obj, bm)
            # bm.free()

        overall_td = per_object_td / overall_islands_count
        overall_centroid = Vector(centroid(per_object_centroid))

        for obj in objs:
            # bm = bm_from_object(context, obj)
            bm = get_bm_from[td_inputs["obj_mode"]](context, obj)
            loc, rot, init_scale = obj.matrix_world.decompose()
            rev_scale_matrix = to_rev_scale_matrix(init_scale)
            scale_matrix = to_scale_matrix(init_scale)
            bm.transform(scale_matrix)

            uv_layer = bm.loops.layers.uv.verify()

            islands_for_td = td_get_islands[td_inputs["obj_mode"]](context, bm, uv_layer)
            # islands_for_td = island_util.get_islands(bm)
            for island in islands_for_td:
                anchor, current_td = td_set_mesh_data[td_inputs["set_mode"]](context, td_inputs, uv_layer, island, overall_td, overall_centroid)
                scale = td_inputs["td"] / current_td
                if scale != 1:
                    loops = [loop for face in island for loop in face.loops]
                    for loop in loops:
                        loop[uv_layer].uv = scale2d(loop[uv_layer].uv, [scale, scale], anchor)

            bm.transform(rev_scale_matrix)
            td_set_changes[td_inputs["obj_mode"]](obj, bm)
            # bm.to_mesh(obj.data)
            # bm.free()


def set_texel_density_legacy(context, objs, td_inputs):

    def to_rev_scale_matrix(sca):
        matrix = Matrix()
        matrix[0][0] = 1 / sca[0]
        matrix[1][1] = 1 / sca[1]
        matrix[2][2] = 1 / sca[2]
        return matrix

    def to_scale_matrix(sca):
        matrix = Matrix()
        matrix[0][0] = sca[0]
        matrix[1][1] = sca[1]
        matrix[2][2] = sca[2]
        return matrix

    if objs:
        # addon_prefs = get_prefs()
        per_object_centroid = []
        per_object_td = 0
        overall_islands_count = 0
        # Calculate anchor and scale for Overall mode
        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)

            loc, rot, init_scale = obj.matrix_world.decompose()
            rev_scale_matrix = to_rev_scale_matrix(init_scale)
            scale_matrix = to_scale_matrix(init_scale)
            bm.transform(scale_matrix)

            uv_layer = bm.loops.layers.uv.verify()
            islands_for_td = island_util.get_island(context, bm, uv_layer)
            per_object_td += calc_averaged_td(context, uv_layer, islands_for_td, td_inputs)[0]
            per_object_centroid.append(calculate_overall_centroid(uv_layer, islands_for_td))
            overall_islands_count += 1
            bm.transform(rev_scale_matrix)
            bmesh.update_edit_mesh(obj.data, loop_triangles=False)

        overall_td = per_object_td / overall_islands_count
        overall_centroid = Vector(centroid(per_object_centroid))

        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)

            loc, rot, init_scale = obj.matrix_world.decompose()
            rev_scale_matrix = to_rev_scale_matrix(init_scale)
            scale_matrix = to_scale_matrix(init_scale)
            bm.transform(scale_matrix)

            uv_layer = bm.loops.layers.uv.verify()

            islands_for_td = island_util.get_island(context, bm, uv_layer)
            calculate_overall_centroid(uv_layer, islands_for_td)

            for island in islands_for_td:
                if td_inputs["set_mode"] == 1:
                    anchor = Vector(centroid(([loop[uv_layer].uv for face in island for loop in face.loops])))
                    current_td = calculate_texel_density(context, uv_layer, island, td_inputs)[0]
                else:
                    anchor = overall_centroid
                    current_td = overall_td

                # scale = addon_prefs.TexelDensity / current_td
                scale = td_inputs["td"] / current_td
                if scale != 1:
                    loops = [loop for face in island for loop in face.loops]
                    for loop in loops:
                        loop[uv_layer].uv = scale2d(loop[uv_layer].uv, [scale, scale], anchor)

            bm.transform(rev_scale_matrix)
            bmesh.update_edit_mesh(obj.data, loop_triangles=False)
