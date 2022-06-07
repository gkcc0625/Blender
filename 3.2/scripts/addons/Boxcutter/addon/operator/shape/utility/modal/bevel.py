import bpy

from math import radians
from mathutils import Vector

from .. import mesh
from ...... utility import addon, screen, modifier

rounded = lambda n: round(n, 8)

# XXX: bevel before array
def shape(op, context, event):
    preference = addon.preference()
    bc = context.scene.bc

    # TODO: lasso bevel support
    if (op.shape_type == 'NGON' or op.ngon_fit) and preference.shape.lasso:
        return

    snap = preference.snap.enable and preference.snap.incremental

    straight_edge = preference.shape.straight_edges or bc.q_back_only

    max_dimension = max(bc.bound_object.dimensions[:-1])
    clamped = False

    clamp_offset = clamp(op)

    width_input = ((op.mouse['location'].x - op.last['mouse'].x) / screen.dpi_factor(ui_scale=False, integer=True)) * max_dimension
    factor = 0.0001 if event and event.shift and op.prior_to_shift == 'NONE' else 0.001

    if op.shape_type == 'CIRCLE' and preference.shape.circle_type == 'POLYGON' and preference.shape.circle_vertices > 12:
        bc['q_bevel'] = bc.shape.data.bc.q_beveled = True
        bc.q_back_only = False
        op.geo['indices']['mid_edge'] = []

    if preference.shape.quad_bevel:
        if not straight_edge or op.shape_type == 'CIRCLE' or bc.q_back_only:
            mesh.bevel_weight(op, context, event)

        else:
            mesh.vertex_group(op, context, event)
    else:
        mesh.bevel_weight(op, context, event)

    m = None
    for mod in bc.shape.modifiers:
        if mod.type == 'BEVEL':
            m = mod
            break

    if not m:
        for mod in modifier.collect(bc.shape, type='WELD'):
            bc.shape.modifiers.remove(mod)

        vertex_only = (op.shape_type == 'NGON' or op.ngon_fit) and not op.extruded
        quad_bevel = not preference.shape.quad_bevel or (preference.shape.quad_bevel and not straight_edge)

        if vertex_only:
            mod = bc.shape.modifiers.new(name='Bevel', type='BEVEL')
            mod.show_render = False
            mod.show_expanded = False

            if bpy.app.version[:2] < (2, 90):
                mod.use_only_vertices = True

            else:
                mod.affect = 'VERTICES'

            mod.width = op.last['modifier']['bevel_width'] if op.shape_type != 'NGON' and not op.ngon_fit else clamp_offset
            mod.segments = preference.shape.bevel_segments
            mod.limit_method = 'WEIGHT'
            mod.offset_type = 'OFFSET'

            bc.shape.data.use_customdata_vertex_bevel = True

            for v in bc.shape.data.vertices:
                v.bevel_weight = v.bevel_weight if op.ngon_point_bevel else 1

            mod = bc.shape.modifiers.new(name='Bevel Weld', type='WELD')
            mod.show_render = False
            mod.show_expanded = False

            modifier.sort(bc.shape, sort_types=['LATTICE', 'BEVEL'], first=True, ignore_hidden=False, use_index_operator=False)

        elif quad_bevel or (op.shape_type == 'CIRCLE' and preference.shape.circle_type == 'MODIFIER'):
            mod = bc.shape.modifiers.new(name='Bevel', type='BEVEL')

            mod.show_render = False
            mod.show_expanded = False

            mod.width = op.last['modifier']['bevel_width'] if op.shape_type != 'NGON' and not op.ngon_fit else clamp_offset

            mod.segments = preference.shape.bevel_segments
            mod.limit_method = 'WEIGHT'
            mod.offset_type = 'OFFSET'

            # if op.mode in {'JOIN', 'MAKE'} and (op.shape_type == 'BOX' and not op.ngon_fit):
            #     mesh.mesh.recalc_normals(bc.shape, face=True, index=4, inside=True)

            mod = bc.shape.modifiers.new(name='Bevel Weld', type='WELD')
            mod.show_render = False
            mod.show_expanded = False

            if (op.shape_type == 'NGON' or op.ngon_fit) and not preference.shape.cyclic:
                modifier.sort(bc.shape, sort_types=['LATTICE', 'BEVEL'], first=True, ignore_hidden=False, use_index_operator=False)

        vertex_groups = bc.shape.vertex_groups if not straight_edge else reversed(bc.shape.vertex_groups)
        front_bevel = bc.bevel_front_face and (bc.q_bevel and not bc.q_back_only and op.geo['indices']['top_face']) and vertex_groups

        if not front_bevel or preference.shape.bevel_both:
            for group in vertex_groups:
                mod = bc.shape.modifiers.new(name=group.name, type='VERTEX_WEIGHT_EDIT')
                mod.vertex_group = group.name
                mod.use_remove = True
                mod.remove_threshold = 0.99

                mod = bc.shape.modifiers.new(name='Quad Bevel', type='BEVEL')
                mod.show_viewport = op.extruded
                mod.show_expanded = False

                mod.width = op.last['modifier']['quad_bevel_width']
                mod.segments = preference.shape.quad_bevel_segments
                mod.limit_method = 'VGROUP'
                mod.vertex_group = group.name
                mod.offset_type = 'OFFSET'
                mod.use_clamp_overlap = op.shape_type == 'NGON' or op.ngon_fit

                if mod.vertex_group == 'bottom' and not straight_edge:
                    mod.offset_type = 'WIDTH'

                if width_input > clamp(op):
                    mod.width = clamp_offset

                mod = bc.shape.modifiers.new(name='Quad Bevel Weld', type='WELD')
                mod.show_render = False
                mod.show_expanded = False

        if front_bevel:
            mesh.mesh.recalc_normals(bc.shape, face_indices=op.geo['indices']['top_face'], inside=not op.inverted_extrude)

            mod = bc.shape.modifiers.new(name='Vgroup', type='VERTEX_WEIGHT_MIX')
            mod.vertex_group_a = 'bottom'
            mod.vertex_group_b = 'bottom'
            mod.mix_mode = 'ADD'

            mod = bc.shape.modifiers.new(name='Front Bevel', type='BEVEL')
            mod.show_viewport = op.extruded
            mod.show_expanded = False

            mod.width = op.last['modifier']['front_bevel_width']
            mod.segments = preference.shape.front_bevel_segments
            mod.limit_method = 'VGROUP'
            mod.vertex_group = 'bottom'
            mod.invert_vertex_group = True
            mod.offset_type = 'WIDTH'
            mod.angle_limit = radians(50)

            if width_input > clamp(op):
                mod.width = clamp_offset

            mod = bc.shape.modifiers.new(name='Front Bevel Weld', type='WELD')
            mod.show_render = False
            mod.show_expanded = False

        elif not bc.q_bevel:
            mesh.mesh.recalc_normals(bc.shape, inside=op.inverted_extrude)

        return

    if op.shape_type == 'NGON' or op.ngon_fit:
        # if op.ngon_point_bevel_reset:
        #     clamp_and_visual_weight(op, bc, preference, clamp_offset, set=False)
        #     op.ngon_point_bevel_reset = False

        delta = ((op.mouse['location'].x - op.last['mouse'].x) / screen.dpi_factor(ui_scale=False, integer=True)) * (0.001 if op.ngon_point_index == -1 else 0.003)

        for index, vindex in enumerate(op.geo['indices']['offset'] if not op.inverted_extrude else op.geo['indices']['extrusion']):
            vert = bc.shape.data.vertices[vindex]

            if op.ngon_point_index == -1:
                if vert.bevel_weight and op.last['vert_weight'][index] + delta <= 0:
                    for mod in bc.shape.modifiers:
                        if mod.type == 'BEVEL':
                            if mod.segments == 1 and op.segment_state:
                                mod.segments = preference.shape.bevel_segments if preference.shape.bevel_segments != 1 else preference.shape.bevel_segments_default

                            else:
                                op.segment_state = True
                                mod.segments = 1

                            break

            if vert.index == op.ngon_point_index or op.ngon_point_index == -1:
                vert.bevel_weight = op.last['vert_weight'][index] + delta

                update = True
                for eindex in op.geo['indices']['top_edge']:
                    edge = bc.shape.data.edges[eindex]

                    if vert.index not in edge.vertices:
                        continue

                    vert1 = bc.shape.data.vertices[edge.vertices[0]]
                    vert2 = bc.shape.data.vertices[edge.vertices[1]]

                    weight = 0
                    if vert.index != vert1.index:
                        weight = bc.shape.data.vertices[vert1.index].bevel_weight

                    if vert.index != vert2.index:
                        weight = bc.shape.data.vertices[vert2.index].bevel_weight

                    length = (vert1.co - vert2.co).length

                    if op.ngon_point_index != -1:
                        length = length - (length * weight)

                    if clamp_offset * vert.bevel_weight > length:
                        update = False
                        continue

                        # if op.ngon_point_index == -1:
                        #     vert.bevel_weight = length * vert.bevel_weight
                        # update = False

                    elif op.ngon_point_index == -1 and not vert.bevel_weight:
                        op.last['vert_weight'][index] = preference.shape.bevel_width - (clamp_offset * vert.bevel_weight)

                if update:
                    vert.bevel_weight = op.last['vert_weight'][index] + delta

                for eindex in op.geo['indices']['mid_edge']:
                    edge = bc.shape.data.edges[eindex]

                    if vert.index not in edge.vertices:
                        continue

                    edge.bevel_weight = vert.bevel_weight

        if not preference.shape.quad_bevel and op.extruded and op.ngon_point_index == -1 and bc.q_bevel:
            if not op.last['edge_weight']:
                op.last['edge_weight'] = [edge.bevel_weight for edge in bc.shape.data.edges]

            eindices = op.geo['indices']['bot_edge']

            for index in eindices:
                edge = bc.shape.data.edges[index]
                edge.bevel_weight = op.last['edge_weight'][index] + delta

        return

    segment_state = False
    update = True
    for mod in bc.shape.modifiers:
        if mod.type == 'BEVEL':
            width_type = 'bevel_width' if mod.name.startswith('Bevel') else F'{mod.name.split(" ")[0].lower()}_bevel_width'

            width = rounded(op.last['modifier'][width_type] + width_input * factor) if op.last['modifier'][width_type] + width_input * factor > 0.0004 else 0.0004

            if width >= clamp_offset:
                clamped = True
                width = clamp_offset
                update = False

            if snap and event and event.ctrl:
                width = round(width, 2 if event and event.shift and op.prior_to_shift == 'NONE' else 1)

            if not clamped:
                if width < 0.001 and not op.width_state or segment_state:
                    segment_state = True
                    op.width_state = True

                    if mod.segments == 1 and op.segment_state:
                        mod.segments = preference.shape.bevel_segments if preference.shape.bevel_segments != 1 else preference.shape.bevel_segments_default

                    else:
                        op.segment_state = True
                        mod.segments = 1

                elif width > 0.0011 and op.width_state:
                    op.width_state = False

            if update:
                op.last['modifier'][width_type] = width
                preference.shape[width_type] = width

            mod.width = width

    op.last['mouse'] = op.mouse['location']


def clamp(op):
    preference = addon.preference()
    bc = bpy.context.scene.bc

    offset = 0.0025 if bpy.app.version[:2] < (2, 82) else 0

    taper = preference.shape.taper

    if (op.shape_type == 'NGON' or op.ngon_fit) and not preference.shape.lasso:
        dist = 0
        for index in op.geo['indices']['top_edge']:
            edge = bc.shape.data.edges[index]

            vert1 = bc.shape.data.vertices[edge.vertices[0]]
            vert2 = bc.shape.data.vertices[edge.vertices[1]]

            length = (vert1.co - vert2.co).length

            if length > dist:
                dist = length

        return dist * taper - offset

    vector1 = Vector(bc.shape.bound_box[0][:])
    vector2 = Vector(bc.shape.bound_box[1][:])
    vector3 = Vector(bc.shape.bound_box[5][:])
    vector4 = Vector(bc.shape.bound_box[6][:])

    distances = [vector4 - vector3, vector3 - vector2]

    if bc.shape.data.bc.q_beveled and op.extruded:
        distances.append((vector2 - vector1) * 2)

    return max(min(distances)) * 0.5 * taper - offset


def clamp_and_visual_weight(op, bc, pref, clamp, set=True):
    prev = op.last['modifier']['bevel_width']

    vindices = op.geo['indices']['offset'] if not op.inverted_extrude else op.geo['indices']['extrusion']
    eindices = op.geo['indices']['mid_edge']

    for index, vindex in enumerate(vindices):
        vert = bc.shape.data.vertices[vindex]

        if op.last['modifier']['bevel_width'] > clamp:
            op.last['modifier']['bevel_width'] = clamp

        if vert.bevel_weight == 1.0:
            vert.bevel_weight = clamp * (prev / 100) * 100

        elif set:
            vert.bevel_weight = pref.shape.bevel_width * (clamp / 100) * 100

        # if vert.index == op.ngon_point_index:
        op.last['vert_weight'][index] = vert.bevel_weight

        for eindex in eindices:
            edge = bc.shape.data.edges[eindex]

            if vert.index not in edge.vertices:
                continue

            edge.bevel_weight = vert.bevel_weight
