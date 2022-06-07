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

"""
Zen UV Quadrify operator based on native Blender Follow Active Quad operator.
"""
from math import atan2, pi
import bpy
import bmesh
from bpy.props import EnumProperty
from mathutils import Vector
from ZenUV.utils.transform import rotate_island, centroid
from ZenUV.utils import get_uv_islands as island_util
from ZenUV.utils.generic import check_selection, fit_uv_view, pin_island, resort_objects, select_all
from ZenUV.ui.labels import ZuvLabels
from ZenUV.ops.mark import assign_seam_to_edges
from ZenUV.utils.hops_integration import show_uv_in_3dview
from ZenUV.stacks.utils import Cluster

STATUS_OK = (1 << 0)


def get_opposite_edge(edge, face):
    # for loop in edge.link_loops:
    #     if loop in face.loops:
    #         return loop.link_loop_next.link_loop_next.edge
    return [loop.link_loop_next.link_loop_next.edge for loop in edge.link_loops if loop in face.loops][0]


def get_adjective_edge(edge, face):
    # for loop in edge.link_loops:
    #     if loop in face.loops:
    #         return loop.link_loop_next.edge
    return [loop.link_loop_next.edge for loop in edge.link_loops if loop in face.loops][0]


def get_ering_for_edge(init_edge, island):
    visited_faces = set()
    edges_ring = [init_edge]
    collector = [init_edge]

    while collector:
        edge = collector.pop()
        for face in edge.link_faces:
            if face in island and face not in visited_faces:
                next_edge = get_opposite_edge(edge, face)
                collector.append(next_edge)
                visited_faces.add(face)
                edges_ring.append(next_edge)
    return edges_ring


def get_edges_for_edge(init_edge, island):
    visited_faces = set()
    edges_ring = [init_edge]
    collector = [init_edge]

    while collector:
        edge = collector.pop()
        for face in edge.link_faces:
            if face in island and face not in visited_faces:
                next_edge = get_opposite_edge(edge, face)
                collector.append(next_edge)
                visited_faces.add(face)
                edges_ring.append(next_edge)
                edges_ring.append(get_adjective_edge(edge, face))
    return edges_ring





def find_squared_face(faces):
    init_face = faces[0]
    min_aspect_face = faces[0]
    min_aspect = 100
    avg_aspect = 0
    for f in faces:
        sides = [f.loops[0].edge.calc_length(), f.loops[1].edge.calc_length()]
        calc_aspect = (max(sides) / min(sides))
        avg_aspect += calc_aspect
        if calc_aspect < min_aspect:
            min_aspect = calc_aspect
            min_aspect_face = f

    edge_01 = init_face.loops[0].edge
    edge_02 = init_face.loops[0].link_loop_next.edge

    face_edges = {edge_01: edge_01.calc_length(), edge_02: edge_02.calc_length()}
    max_key = max(face_edges.keys(), key=(lambda k: face_edges[k]))
    face_edges[max_key] = face_edges[max_key] / min_aspect

    # print("Calculated face: ", min_aspect_face, calc_aspect)
    # print("Averaged Aspect for all Faces: ", avg_aspect / len(faces))
    # print("Sides: ", face_edges)
    return min_aspect_face


def get_rectangle_sides(init_face, faces, uv_layer):
    sum_aspect = 0
    for f in faces:
        sides = [f.loops[0].edge.calc_length(), f.loops[1].edge.calc_length()]
        sum_aspect += max(sides) / min(sides)
    avg_aspect = sum_aspect / len(faces)
    edge_01 = init_face.loops[0].edge
    edge_02 = init_face.loops[0].link_loop_next.edge

    face_edges = {edge_01: edge_01.calc_length(), edge_02: edge_02.calc_length()}
    max_key = max(face_edges.keys(), key=(lambda k: face_edges[k]))
    face_edges[max_key] = face_edges[max_key] / avg_aspect

    edge_01_uv_length = (edge_01.link_loops[0].link_loop_next[uv_layer].uv - edge_01.link_loops[0][uv_layer].uv).length

    if edge_01_uv_length < 0.001:
        edge_01_uv_length = 0.08

    edge_02_length = face_edges[edge_02]

    aspect = face_edges[edge_01] / edge_01_uv_length

    edge_02_uv_length = edge_02_length / aspect

    return edge_01_uv_length, edge_02_uv_length


def get_avg_length(_edges):
    """Calculate averaged edges length for loop[0].edge ring"""
    # sum_edges_length = 0
    # for edge in _edges:
    #     sum_edges_length += edge.calc_length()
    # return sum_edges_length / len(_edges)
    return sum([edge.calc_length() for edge in _edges]) / len(_edges)


def get_initial_face_edges_lengths(face, faces, uv_layer):
    """
    Return averaged UV edge length
    """

    edge_01 = face.loops[0].edge
    edge_02 = face.loops[0].link_loop_next.edge

    edge_01_ering = get_ering_for_edge(edge_01, faces)
    edge_02_ering = get_ering_for_edge(edge_02, faces)

    edge_01_length = get_avg_length(edge_01_ering)
    edge_02_length = get_avg_length(edge_02_ering)

    sum_edges_uv = 0
    col = 0
    for edge in edge_01_ering:
        edge_uv_length = (edge.link_loops[0].link_loop_next[uv_layer].uv - edge.link_loops[0][uv_layer].uv).length
        if edge_uv_length > 0:
            col += 1
            sum_edges_uv += edge_uv_length
    if col > 0:
        edge_01_uv_length = sum_edges_uv / col
    else:
        edge_01_uv_length = (edge_01.link_loops[0].link_loop_next[uv_layer].uv - edge_01.link_loops[0][uv_layer].uv).length

    if edge_01_uv_length < 0.0001:
        edge_01_uv_length = 0.08

    aspect = edge_01_length / edge_01_uv_length

    edge_02_uv_length = edge_02_length / aspect

    return edge_01_uv_length, edge_02_uv_length


def clear_blender_tag(bm):
    for f in bm.faces:
        f.tag = False


def align_init_face(uv_layer, face, edge1_length, edge2_length, orient_to_world):
    rotate_to_nearest = True
    move_to_base = True
    quadrify = True
    orient_to_world = False

    point1 = face.loops[0][uv_layer]
    point2 = face.loops[0].link_loop_next[uv_layer]
    loop_0_init_vec = point2.uv - point1.uv
    if loop_0_init_vec.length == 0.0:
        loop_0_init_vec = Vector((0, edge1_length))
        point1.uv = loop_0_init_vec

    # Rotate initial face to nearest basis by loop[0]
    if rotate_to_nearest and not orient_to_world:
        current_angle = atan2(loop_0_init_vec.y, loop_0_init_vec.x)
        increment_angle = round(current_angle / (pi / 2)) * (pi / 2) - current_angle
        anchor = Vector(centroid([loop[uv_layer].uv for loop in face.loops]))
        rotate_island([face], uv_layer, increment_angle, anchor)
        loop_0_init_vec = point2.uv - point1.uv

    if orient_to_world:
        loop_0_init_vec = Vector((0, edge1_length))

    fp = dict(
        start_point=Vector(centroid([loop[uv_layer].uv for loop in face.loops])),
        loop_0_vec=loop_0_init_vec * (edge1_length / loop_0_init_vec.length),
        loop_1_vec=loop_0_init_vec.orthogonal() * (edge2_length / loop_0_init_vec.orthogonal().length),
        loop_0=face.loops[0][uv_layer],
        loop_1=face.loops[0].link_loop_next[uv_layer],
        loop_2=face.loops[0].link_loop_next.link_loop_next[uv_layer],
        loop_3=face.loops[0].link_loop_prev[uv_layer])

    if quadrify:
        fp["loop_0"].uv = (0, 0)
        fp["loop_1"].uv = fp["loop_0_vec"]
        fp["loop_2"].uv = fp["loop_0_vec"] + fp["loop_1_vec"]
        fp["loop_3"].uv = fp["loop_1_vec"]

    # Translate face to initial coordinates
    if move_to_base:
        current_pos = Vector(centroid([loop[uv_layer].uv for loop in face.loops]))
        desired_pos = fp["start_point"] - current_pos
        for loop in face.loops:
            loop[uv_layer].uv += desired_pos


def zen_follow_quad(bm, island, uv_act, EXTEND_MODE="LENGTH_AVERAGE", orient_to_world=False):
    """
    Valeriy Remark
    Blender Native Follow active quad operator.
    Changes only in initial data. Original operator works only with selection.
    Original operator possibly based on UV Squares Master addon created by
    reslav.hollos@gmail.com
    https://github.com/Radivarig/UvSquares
    My changes: def walk_edgeloop (l) function changed. Now it walks only in specified faces instead of
    all edges in the face loop. The averaging is now calculated correctly. And don't include edges of unselected faces.
    In my case, do not include off-island edges.
    """
    clear_blender_tag(bm)
    faces = [f for f in island if len(f.verts) == 4]

    if not faces:
        return False

    f_act = faces[0]

    inf_edge_1_uv_length, inf_edge_2_uv_length = get_initial_face_edges_lengths(f_act, faces, uv_act)

    align_init_face(uv_act, f_act, inf_edge_1_uv_length, inf_edge_2_uv_length, orient_to_world)

    # our own local walker
    def walk_face_init(faces, f_act):
        # first tag all faces True (so we don't uvmap them)
        for f in bm.faces:
            f.tag = True
        # then tag faces arg False
        for f in faces:
            f.tag = False
        # tag the active face True since we begin there
        f_act.tag = True

    def walk_face(f):
        # all faces in this list must be tagged
        f.tag = True
        faces_a = [f]
        faces_b = []

        while faces_a:
            for f in faces_a:
                for l in f.loops:
                    l_edge = l.edge
                    if (l_edge.is_manifold is True) and (l_edge.seam is False):
                        l_other = l.link_loop_radial_next
                        f_other = l_other.face
                        if not f_other.tag:
                            yield (f, l, f_other)
                            f_other.tag = True
                            faces_b.append(f_other)
            # swap
            faces_a, faces_b = faces_b, faces_a
            faces_b.clear()

    def walk_edgeloop(l):

        # Could make this a generic function

        # Valeriy changes: if len(l.face.verts) == 4:
        # changed to if l.face.tag and len(l.face.verts) == 4:
        # it give skipping faces not included in given face set.
        e_first = l.edge
        e = None
        while True:
            e = l.edge
            yield e
            # don't step past non-manifold edges
            if e.is_manifold:
                # walk around the quad and then onto the next face
                l = l.link_loop_radial_next
                if l.face.tag: # and len(l.face.verts) == 4:
                    l = l.link_loop_next.link_loop_next
                    if l.edge is e_first:
                        break
                else:
                    break
            else:
                break

    def extrapolate_uv(fac, l_a_outer, l_a_inner, l_b_outer, l_b_inner):
        l_b_inner[:] = l_a_inner
        l_b_outer[:] = l_a_inner + ((l_a_inner - l_a_outer) * fac)

    def apply_uv(_f_prev, l_prev, _f_next):
        l_a = [None, None, None, None]
        l_b = [None, None, None, None]

        l_a[0] = l_prev
        l_a[1] = l_a[0].link_loop_next
        l_a[2] = l_a[1].link_loop_next
        l_a[3] = l_a[2].link_loop_next

        #  l_b
        #  +-----------+
        #  |(3)        |(2)
        #  |           |
        #  |l_next(0)  |(1)
        #  +-----------+
        #        ^
        #  l_a   |
        #  +-----------+
        #  |l_prev(0)  |(1)
        #  |    (f)    |
        #  |(3)        |(2)
        #  +-----------+
        #  copy from this face to the one above.

        # get the other loops
        l_next = l_prev.link_loop_radial_next
        if l_next.vert != l_prev.vert:
            l_b[1] = l_next
            l_b[0] = l_b[1].link_loop_next
            l_b[3] = l_b[0].link_loop_next
            l_b[2] = l_b[3].link_loop_next
        else:
            l_b[0] = l_next
            l_b[1] = l_b[0].link_loop_next
            l_b[2] = l_b[1].link_loop_next
            l_b[3] = l_b[2].link_loop_next

        l_a_uv = [l[uv_act].uv for l in l_a]
        l_b_uv = [l[uv_act].uv for l in l_b]

        if EXTEND_MODE == 'LENGTH_AVERAGE':
            d1 = edge_lengths[l_a[1].edge.index][0]
            d2 = edge_lengths[l_b[2].edge.index][0]
            try:
                fac = d2 / d1
            except ZeroDivisionError:
                fac = 1.0
        elif EXTEND_MODE == 'LENGTH':
            a0, b0, c0 = l_a[3].vert.co, l_a[0].vert.co, l_b[3].vert.co
            a1, b1, c1 = l_a[2].vert.co, l_a[1].vert.co, l_b[2].vert.co

            d1 = (a0 - b0).length + (a1 - b1).length
            d2 = (b0 - c0).length + (b1 - c1).length
            try:
                fac = d2 / d1
            except ZeroDivisionError:
                fac = 1.0
        else:
            fac = 1.0

        extrapolate_uv(fac,
                       l_a_uv[3], l_a_uv[0],
                       l_b_uv[3], l_b_uv[0])

        extrapolate_uv(fac,
                       l_a_uv[2], l_a_uv[1],
                       l_b_uv[2], l_b_uv[1])

    # -------------------------------------------
    # Calculate average length per loop if needed
    if EXTEND_MODE == 'LENGTH_AVERAGE':
        bm.edges.index_update()
        edge_lengths = [None] * len(bm.edges)
        for f in faces:
            f.tag = True
        for f in faces:
            # we know its a quad
            l_quad = f.loops[:]
            l_pair_a = (l_quad[0], l_quad[2])
            l_pair_b = (l_quad[1], l_quad[3])

            for l_pair in (l_pair_a, l_pair_b):
                if edge_lengths[l_pair[0].edge.index] is None:

                    edge_length_store = [-1.0]
                    edge_length_accum = 0.0
                    edge_length_total = 0

                    for l in l_pair:
                        if edge_lengths[l.edge.index] is None:
                            for e in walk_edgeloop(l):
                                if edge_lengths[e.index] is None:
                                    edge_lengths[e.index] = edge_length_store
                                    edge_length_accum += e.calc_length()
                                    edge_length_total += 1

                    edge_length_store[0] = edge_length_accum / edge_length_total
        for f in faces:
            f.tag = False
    # done with average length
    # ------------------------
    walk_face_init(faces, f_act)
    for f_triple in walk_face(f_act):
        apply_uv(*f_triple)

    # Clean Tag
    clear_blender_tag(bm)

    # bmesh.update_edit_mesh(me, loop_triangles=False)

    return STATUS_OK


class ZUV_OT_Quadrify(bpy.types.Operator):
    bl_idname = "uv.zenuv_quadrify"
    bl_label = ZuvLabels.QUADRIFY_LABEL
    bl_description = ZuvLabels.QUADRIFY_DESC
    bl_options = {'REGISTER', 'UNDO'}

    orient: EnumProperty(
        name="Orient to:",
        description="Orient Quadrified Islands",
        items=[
            ("VERTICAL", "Vertical", ""),
            ("HORIZONTAL", "Horizontal", "")
        ],
        default="HORIZONTAL"
    )

    @classmethod
    def poll(cls, context):
        # return check_selection(context)
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        objects = resort_objects(context, context.objects_in_mode)
        if objects:
            for obj in objects:
                bm = bmesh.from_edit_mesh(obj.data)
                uv_layer = bm.loops.layers.uv.verify()
                bm.edges.index_update()
                init_selection = {"verts": [v for v in bm.verts if v.select], "edges": [e for e in bm.edges if e.select], "faces": [f for f in bm.faces if f.select]}
                # Create seam by selected edge
                if addon_prefs.QuadrifyBySelected \
                    and context.tool_settings.mesh_select_mode[1] \
                        and bpy.ops.uv.zenuv_select_loop.poll():
                    bpy.ops.uv.zenuv_select_loop()
                    to_seams = [e for e in bm.edges if e.select]
                    assign_seam_to_edges(to_seams)
                islands_for_process = island_util.get_island(context, bm, uv_layer)
                for island in islands_for_process:
                    quads = [f for f in island if len(f.verts) == 4]
                    if not quads:
                        continue
                    # non quads detection
                    # print(f"Island: {island}")
                    non_quads = [f for f in island if len(f.verts) != 4]

                    zen_follow_quad(bm, island, uv_layer, orient_to_world=addon_prefs.quadrifyOrientToWorld)
                    # Pin Island
                    if addon_prefs.autoPinQuadrified:
                        pin_island(island, uv_layer, True)
                        # bpy.ops.uv.zenuv_pin_island()

                    master = Cluster(context, obj, quads)
                    master.orient(self.orient)

                    # Unwrap Non Quads
                    select_all(bm, action=False)
                    for f in non_quads:
                        f.select = True
                    bpy.ops.uv.unwrap(
                        method=addon_prefs.UnwrapMethod,
                        # fill_holes=self.fill_holes,
                        # correct_aspect=self.correct_aspect,
                        # ue_subsurf_data=self.use_subsurf_data,
                        margin=0
                    )
                    # bmesh.select_mode = {'FACE'}
                    non_quads_islands = island_util.get_island(context, bm, uv_layer)
                    for n_island in non_quads_islands:
                        cluster = Cluster(context, obj, n_island)
                        cluster.match_td(master)
                        cluster.move_to(master.bbox["cen"])

                # Zen Pack if needed
                if addon_prefs.packAfQuadrify:
                    bpy.ops.uv.zenuv_pack(display_uv=False)

                # Update seams
                if addon_prefs.quadrifyUpdateSeamsFromUV:
                    bpy.ops.uv.zenuv_unified_mark(convert="SEAM_BY_UV_BORDER")

                # If Count of objects more than 1 - Fit UV view in mode checker
                if addon_prefs.autoFitUV and addon_prefs.packAfQuadrify:
                    fit_uv_view(context, mode="all")

                # Restore selection
                select_all(bm, action=False)
                mode = context.tool_settings.mesh_select_mode
                if mode[0]:
                    elements = "verts"
                elif mode[1]:
                    elements = "edges"
                elif mode[2]:
                    elements = "faces"
                for i in init_selection[elements]:
                    i.select = True

        # Display UV Widget from HOPS addon
        show_uv_in_3dview(context, use_selected_meshes=True, use_selected_faces=False, use_tagged_faces=True)

        return {'FINISHED'}
