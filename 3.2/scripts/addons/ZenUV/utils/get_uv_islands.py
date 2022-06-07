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

""" Zen UV Islands Processor """

# from ZenUV.utils.generic import Timer
from ZenUV.utils.generic import face_indexes_by_sel_mode


def get_islands_by_face_list(context, bm, faces, uv_layer):
    ''' Return islands by indexes '''
    # faces = [bm.faces[index] for index in indexes]
    selection = [f for f in faces if not f.hide]

    return zen_get_islands(bm, selection, has_selected_faces=True)


def get_islands_by_vert_list_indexes(context, bm, verts, uv_layer):
    ''' Return islands by indexes '''
    # faces = [bm.faces[index] for index in indexes]
    selection = [face for vert in [bm.verts[index] for index in verts] for face in vert.link_faces if not face.hide]
    # print("SELECTION inside islands by vert_indexes: ", selection)
    return zen_get_islands(bm, selection, has_selected_faces=True)


def get_islands_by_face_list_indexes(bm, face_list):
    ''' Return islands by indexes '''
    # faces = [bm.faces[index] for index in indexes]
    selection = [bm.faces[index] for index in face_list if not bm.faces[index].hide]
    # print("SELECTION inside islands by vert_indexes: ", selection)
    return zen_get_islands(bm, selection, has_selected_faces=True)


def get_island(context, bm, uv_layer):
    ''' Return island (s) by selected faces, edges or vertices '''
    bm.faces.ensure_lookup_table()
    selection = [bm.faces[index] for index in face_indexes_by_sel_mode(context, bm)]
    return zen_get_islands(bm, selection, has_selected_faces=True)


def get_selected_faces(context, bm):
    selection = [bm.faces[index] for index in face_indexes_by_sel_mode(context, bm)]
    if selection:
        return [selection, ]
    return []


def get_islands(bm):
    ''' Return all islands from mesh '''
    return zen_get_islands(bm, None, has_selected_faces=False)


def get_islands_in_indices(bm):
    ''' Return all islands as indices from mesh '''
    islands_ind = []
    islands = zen_get_islands(bm, None, has_selected_faces=False)
    for island in islands:
        islands_ind.append([f.index for f in island])
    return islands_ind


def uv_bound_edges_indexes(faces, uv_layer):
    """ Return indexes of border edges of given island (faces) from current UV Layer """
    if faces:
        edges = {edge for face in faces for edge in face.edges if edge.link_loops}
        return [edge.index for edge in edges
                if edge.link_loops[0][uv_layer].uv
                != edge.link_loops[0].link_loop_radial_next.link_loop_next[uv_layer].uv
                or edge.link_loops[len(edge.link_loops)-1][uv_layer].uv
                != edge.link_loops[len(edge.link_loops)-1].link_loop_radial_next.link_loop_next[uv_layer].uv]
    return None


def zen_get_islands(bm, _selection, has_selected_faces=False):
    # print("SELECTION: ", _selection)
    uv_layer = bm.loops.layers.uv.verify()
    _uv_borders = uv_bound_edges_indexes(bm.faces, uv_layer)
    bm.edges.ensure_lookup_table()
    for edge in bm.edges:
        edge.tag = False
    # Tag all edges in uv borders
    for index in _uv_borders:
        bm.edges[index].tag = True
        # print(bm.edges[index], bm.edges[index].tag)

    _islands = []
    if has_selected_faces:
        faces = set(_selection)
    # if has_selected_faces:
    #     faces = {f for f in bm.faces if f.select}
        # faces = {f for f in bm.faces for l in f.loops if l[uv_layer].select}
    else:
        faces = set(bm.faces)
    while len(faces) != 0:
        init_face = faces.pop()
        island = {init_face}
        stack = [init_face]
        while len(stack) != 0:
            face = stack.pop()
            for e in face.edges:
                if not e.tag:
                    for f in e.link_faces:
                        if f not in island:
                            stack.append(f)
                            island.add(f)
        for f in island:
            faces.discard(f)
        if True in [f.hide for f in island]:
            continue
        _islands.append(island)
    for index in _uv_borders:
        bm.edges[index].tag = False

    return _islands


if __name__ == "__main__":
    pass
