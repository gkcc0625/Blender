import bpy
from bpy.props import IntProperty, BoolProperty, FloatProperty, EnumProperty
import bmesh
from .. utils.selection import get_selected_vert_sequences
from .. utils.math import create_circle_coords
from .. utils.draw import draw_line
from .. utils.property import rotate_list
from .. utils.tool import create_pipe_coords, create_pipe_ring_coords
from .. items import boolean_solver_items













class OffsetCut(bpy.types.Operator):
    bl_idname = "machin3.offset_cut"
    bl_label = "MACHIN3: Offset Cut"
    bl_description = "description"
    bl_options = {'REGISTER', 'UNDO'}

    width: FloatProperty(name="Width", default=0.1, min=0.001, step=0.1)

    resample: BoolProperty(name="Resample", default=True)
    factor: FloatProperty(name="Factor", default=1, min=0.5)

    smooth: BoolProperty(name="Smooth", default=False)
    iterations: IntProperty(name="Iterations", default=1, min=1)

    optimize: BoolProperty(name="Optimize", default=True)
    angle: FloatProperty(name="Angle", default=180, min=0, max=180)

    extend: FloatProperty(name="Extend", default=0.2, min=0)
    override: BoolProperty(name="Spread", default=False)

    rails: IntProperty(name="Precision", default=18, min=7)
    tilt: FloatProperty(name="Wiggle", default=1)
    shift: BoolProperty(name="Shift", default=True)

    solver: EnumProperty(name="Solver", items=boolean_solver_items, default='FAST')


    shade_smooth: BoolProperty(default=False)
    mark_sharp: BoolProperty(default=False)
    all_cyclic: BoolProperty(default=False)


    def draw(self, context):
        layout = self.layout

        column = layout.column(align=True)

        column.prop(self, "width")

        if not self.all_cyclic:
            split = column.split(factor=0.7, align=True)
            split.prop(self, "extend")
            split.prop(self, "override", toggle=True)

        column.separator()

        row = column.row(align=True)


        row.prop(self, "resample", toggle=True)
        r = row.split(align=True)
        r.active = self.resample
        r.prop(self, "factor")

        row = column.row(align=True)
        row.prop(self, "smooth", toggle=True)
        r = row.split(align=True)
        r.active = self.smooth
        r.prop(self, "iterations")

        row = column.row(align=True)
        row.prop(self, "optimize", toggle=True)
        r = row.split(align=True)
        r.active = self.optimize
        r.prop(self, "angle")

        row = column.row(align=True)
        row.prop(self, "solver", expand=True)

        column.separator()

        row = column.row(align=True)
        row.prop(self, "rails")
        row.prop(self, "tilt")
        row.prop(self, "shift", toggle=True)

    def execute(self, context):
        active = context.active_object
        mxw = active.matrix_world

        bm = bmesh.from_edit_mesh(active.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()

        s = bm.edges.layers.string.verify()
        fm = bm.faces.layers.face_map.verify()

        fmap_count = len(active.face_maps)

        verts = [v for v in bm.verts if v.select]

        sequences = get_selected_vert_sequences(verts, debug=False)

        edge = bm.edges.get((sequences[0][0][0], sequences[0][0][1]))
        face = edge.link_faces[0]
        self.mark_sharp = not edge.smooth
        self.shade_smooth = face.smooth
        self.all_cyclic = all(cyclic for _, cyclic in sequences)

        circle_coords, circle_normals = create_circle_coords(self.width, self.rails, self.tilt, calc_normals=True, debug=False)

        pipes = []
        all_pipe_faces = []
        face_maps = []

        for idx, (seq, cyclic) in enumerate(sequences):
            coords = create_pipe_coords(seq, cyclic, self.resample, self.factor, self.smooth, self.iterations, self.optimize, self.angle, mxw, debug=False)

            ext_coords = self.extend_coords(coords, cyclic, self.extend)

            ring_coords = create_pipe_ring_coords(ext_coords, cyclic, circle_coords, circle_normals, mx=mxw, debug=False)

            vert_rings = self.create_pipe_verts(bm, ring_coords, cyclic, mx=mxw, debug=False)

            pipe_faces = self.create_pipe_faces(bm, vert_rings, cyclic, s, idx, self.shift, self.shade_smooth)
            all_pipe_faces.extend(pipe_faces)

            fmap = self.create_pipe_face_map(active, pipe_faces, fmap_count, fm, idx)
            face_maps.append(fmap)

            pipes.append((coords, cyclic))


        bmesh.ops.recalc_face_normals(bm, faces=all_pipe_faces)
        bmesh.update_edit_mesh(active.data)

        for idx, _ in enumerate(pipes):
            self.boolean_pipe(active, fmap_count, idx)

        bpy.ops.mesh.select_all(action='DESELECT')


        bm = bmesh.from_edit_mesh(active.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()

        s = bm.edges.layers.string.verify()
        fm = bm.faces.layers.face_map.verify()

        merge_verts = []
        junk_edges = []

        for pipe_idx, (coords, cyclic) in enumerate(pipes):
            faces = [f for f in bm.faces if f[fm] == fmap_count + pipe_idx]
            edges = {e for f in faces for e in f.edges}
            verts = {v for f in faces for v in f.verts}

            geom = bmesh.ops.region_extend(bm, geom=faces, use_faces=True)
            border_faces = geom['geom']
            border_edges = {e for f in border_faces for e in f.edges}
            border_verts = {v for f in border_faces for v in f.verts}

            sweeps, non_sweep_edges, has_caps = self.get_sorted_sweep_edges(len(coords), edges, s, pipe_idx)

            end_rail_edges = self.set_end_sweeps(sweeps, border_verts, border_edges) if not cyclic and len(sweeps) > 2 else set()

            junk = self.collect_junk_edges(non_sweep_edges, border_edges, border_verts, end_rail_edges)
            junk_edges.extend(junk)

            merge = self.recreate_hard_edges(sweeps, cyclic, coords, border_verts, self.override)
            merge_verts.extend(merge)

            self.mark_end_sweep_edges_sharp(self.mark_sharp, cyclic, has_caps, border_edges, merge_verts)


        bmesh.ops.dissolve_edges(bm, edges=junk_edges, use_verts=True)
        bmesh.ops.remove_doubles(bm, verts=[v for v in merge_verts if v.is_valid], dist=0.00001)

        bm.select_flush(True)

        self.mark_selected_sharp(bm, self.mark_sharp)

        self.cleanup(active, bm, face_maps, s)

        bmesh.update_edit_mesh(active.data)
        return {'FINISHED'}



    def cleanup(self, active, bm, face_maps, s):
        for fmap in face_maps:
            active.face_maps.remove(fmap)

        bm.edges.layers.string.remove(s)

    def mark_selected_sharp(self, bm, mark_sharp):
        if mark_sharp:
            for e in bm.edges:
                if e.select:
                    e.smooth = False

    def mark_end_sweep_edges_sharp(self, mark_sharp, cyclic, has_caps, border_edges, merge_verts):
        if cyclic or has_caps or not mark_sharp:
            return

        else:
            for e in [e for e in border_edges if any([v in merge_verts for v in e.verts])]:
                e.smooth = False

    def collect_junk_edges(self, non_sweep_edges, border_edges, border_verts, end_rail_edges):
        junk = set()

        for e in non_sweep_edges - border_edges - end_rail_edges:
            if any(v in border_verts for v in e.verts):
                junk.add(e)

        return list(junk)

    def recreate_hard_edges(self, sweeps, cyclic, coords, border_verts, override):
        merge = set()

        for idx, (sweep, co) in enumerate(zip(sweeps, coords)):
            if sweep:
                sweep_verts = {v for e in sweep for v in e.verts}

                if cyclic or 0 < idx < len(sweeps) - 1 or override:
                    sweep_verts -= border_verts

                for v in sweep_verts:
                    v.co = co

                    merge.add(v)

                    v.select_set(True)

        return merge

    def set_end_sweeps(self, sweeps, border_verts, border_edges):
        end_rails = set()


        if sweeps[1]:
            for e in sweeps[1]:
                if not any([v in border_verts for v in e.verts]):
                    sweep = []

                    for loop in e.link_loops:
                        start_loop = loop

                        while True:
                            loop = loop.link_loop_next

                            if loop.edge in border_edges:
                                sweep.append(loop.edge)

                            else:
                                end_rails.add(loop.edge)

                            if loop == start_loop:
                                break

                    if sweeps[0] is None:
                        sweeps[0] = sweep

                    else:
                        sweeps[0].extend(sweep)

        if sweeps[-2]:
            for e in sweeps[-2]:
                if not any([v in border_verts for v in e.verts]):
                    sweep = []

                    for loop in e.link_loops:
                        start_loop = loop

                        while True:
                            loop = loop.link_loop_next

                            if loop.edge in border_edges:
                                sweep.append(loop.edge)

                            else:
                                end_rails.add(loop.edge)

                            if loop == start_loop:
                                break

                            if sweeps[-1] is None:
                                sweeps[-1] = sweep

                            else:
                                sweeps[-1].extend(sweep)

        return end_rails

    def get_sorted_sweep_edges(self, sweep_count, edges, layer, pipe_idx):
        sweeps = [None] * sweep_count
        non_sweep_edges = set()

        for e in edges:
            edge_string = e[layer].decode()

            if edge_string:
                edge_dict = eval(edge_string)

                sweep_idx = edge_dict.get(pipe_idx)

                sweep = sweeps[sweep_idx]

                if sweep:
                    sweeps[sweep_idx].append(e)

                else:
                    sweeps[sweep_idx] = [e]

            else:
                non_sweep_edges.add(e)

        return sweeps, non_sweep_edges, True if sweeps[0] and sweeps[-1] else False

    def boolean_pipe(self, active, fmap_count, pipe_idx):
        bpy.ops.mesh.select_all(action='DESELECT')

        fmap_idx = fmap_count + pipe_idx
        active.face_maps.active_index = fmap_idx
        bpy.ops.object.face_map_select()

        bpy.ops.mesh.intersect_boolean(operation='DIFFERENCE', solver=self.solver)

    def create_pipe_face_map(self, active, faces, offset, layer, pipe_idx):
        fmap = active.face_maps.new(name="pipe%d" % (pipe_idx + 1))

        for f in faces:
            f[layer] = offset + pipe_idx

        return fmap

    def create_pipe_faces(self, bm, vert_rings, cyclic, layer, pipe_idx, shift, smooth):
        pipe_faces = []

        for ridx, ring in enumerate(vert_rings):
            if cyclic:
                if ridx == len(vert_rings) - 1:
                    next_verts = vert_rings[0][0]

                else:
                    next_verts = vert_rings[ridx + 1][0]

            else:
                if ridx in [0, len(vert_rings) - 1]:
                    f = bm.faces.new(ring[0])

                    pipe_faces.append(f)

                    for e in f.edges:
                        d = {pipe_idx: ridx}
                        e[layer] = str(d).encode()

                    if ridx == len(vert_rings) - 1:
                        continue

                next_verts = vert_rings[ridx + 1][0]

            verts, shift_amount = ring

            if shift and shift_amount:
                next_verts = next_verts.copy()
                rotate_list(next_verts, shift_amount)

            for vidx, (v, vn) in enumerate(zip(verts, next_verts)):

                if vidx < self.rails - 1:
                    f = bm.faces.new([v, verts[vidx + 1], next_verts[vidx + 1], vn])

                else:
                    f = bm.faces.new([v, verts[0], next_verts[0], vn])

                f.smooth = smooth

                if cyclic or ridx > 0:
                    e = f.edges[0]

                    d = {pipe_idx: ridx}
                    e[layer] = str(d).encode()

                pipe_faces.append(f)

        return pipe_faces

    def create_pipe_verts(self, bm, ring_coords, cyclic, mx=None, debug=False):

        vert_rings = []

        for ridx, ring in enumerate(ring_coords):
            if ridx == len(ring_coords) - 1:
                if cyclic:
                    next_ring = ring_coords[0]
                else:
                    verts = []
                    for co, _ in ring:
                        v = bm.verts.new(co)
                        verts.append(v)

                    vert_rings.append((verts, 0))
                    continue
            else:
                next_ring = ring_coords[ridx + 1]

            first_co, first_nrm = ring[0]

            dots = [(idx, co, first_nrm.dot(nrm)) for idx, (co, nrm) in enumerate(next_ring)]
            maxdot = max(dots, key=lambda x: x[2])

            shift_amount = maxdot[0]

            if debug and mx:
                draw_line([first_co, maxdot[1]], mx=mx, color=(1, 1, 0), alpha=0.5, modal=False)

            verts = []
            for co, _ in ring:
                v = bm.verts.new(co)
                verts.append(v)

            vert_rings.append((verts, shift_amount))

        return vert_rings

    def create_pipe_ring_coords(self, coords, cyclic, circle_coords, circle_normals=None, mx=None, debug=False):

        ring_coords = []

        for idx, co in enumerate(coords):
            ring = []

            prevco = coords[-1] if idx == 0 else coords[idx -1]
            nextco = coords[0] if idx == len(coords) - 1 else coords[idx + 1]

            if cyclic or idx not in [0, len(coords) - 1]:
                vec_next = (nextco - co).normalized()
                vec_prev = (co - prevco).normalized()

                direction = vec_prev + vec_next

            else:
                if idx == 0:
                    direction = (nextco - co).normalized()

                elif idx == len(coords) - 1:
                    direction = (co - prevco).normalized()

            if debug and mx:
                draw_vector(direction * 0.05, origin=co, mx=mx, color=(1, 1, 1), modal=False)

            rotmx = create_rotation_matrix_from_vector(direction)

            locmx = get_loc_matrix(co)

            for cidx, cco in enumerate(circle_coords):
                if circle_normals:
                    normal = circle_normals[cidx]
                    ring.append((locmx @ rotmx @ cco, rotmx @ normal))

                else:
                    ring.append(locmx @ rotmx @ cco)

            if debug and mx:
                if circle_normals:
                    dcoords = [co for co, _ in ring]
                    draw_points(dcoords[1:], mx=mx, color=(1, 1, 1), size=4, alpha=0.5, modal=False)
                    draw_point(dcoords[0], mx=mx, color=(1, 0, 0), size=4, alpha=1, modal=False)

                    normals = [nrm for _, nrm in ring]
                    draw_vectors(normals, dcoords, mx=mx, color=(1, 0, 0), alpha=0.5, modal=False)

                else:
                    draw_points(ring[1:], mx=mx, color=(1, 1, 1), size=4, alpha=0.5, modal=False)
                    draw_point(ring[0], mx=mx, color=(1, 0, 0), size=4, alpha=1, modal=False)

            ring_coords.append(ring)

        return ring_coords

    def extend_coords(self, coords, cyclic, extend):
        if not cyclic and extend:
            ext_coords = coords.copy()

            start_dir = (coords[0] - coords[1]).normalized()
            ext_coords[0] = coords[0] + start_dir * extend

            end_dir = (coords[-1] - coords[-2]).normalized()
            ext_coords[-1] = coords[-1] + end_dir * extend

        else:
            ext_coords = coords

        return ext_coords

    def get_pipe_coords(self, seq, cyclic, resample, factor, smooth, iterations, optimize, angle, mx, debug=False):
        def smooth_coords(coords, cyclic, iterations, mx, debug=False):
            while iterations:
                iterations -= 1

                smoothed = []

                for idx, co in enumerate(coords):
                    if idx in [0, len(coords) - 1]:
                        if cyclic:
                            if idx == 0:
                                smoothed.append(average_locations([coords[-1], coords[1]]))

                            elif idx == len(coords) - 1:
                                smoothed.append(average_locations([coords[-2], coords[0]]))
                        else:
                            smoothed.append(co)
                    else:
                        co_prev = coords[idx - 1]
                        co_next = coords[idx + 1]

                        smoothed.append(average_locations([co_prev, co_next]))


                coords = smoothed

            if debug:
                draw_points(coords, mx=mx, color=red, xray=True, modal=False)

            return coords

        def optimize_straights(coords, cyclic, angle, mx, debug=False):
            optimized = []
            removed = []

            for idx, co in enumerate(coords):
                if idx in [0, len(coords) - 1]:
                    if cyclic:
                        if idx == 0:
                            co_prev = coords[-1]
                            co_next = coords[1]

                        elif idx == len(coords) - 1:
                            co_prev = coords[-2]
                            co_next = coords[0]
                    else:
                        optimized.append(co)
                        continue
                else:
                    co_prev = coords[idx - 1]
                    co_next = coords[idx + 1]

                vec1 = co_prev - co
                vec2 = co_next - co
                a = round(degrees(vec1.angle(vec2)), 3)

                if a >= angle:
                    removed.append(co)

                else:
                    optimized.append(co)

            if debug:
                draw_points(removed, mx=mx, color=black, modal=False)

            return optimized

        coords = [v.co.copy() for v in seq]

        if resample:
            coords = resample_coords(coords, cyclic, segments=int(len(coords) * factor), mx=mx, debug=False)

        if smooth:
            coords = smooth_coords(coords, cyclic, iterations, mx, debug=False)

        if optimize:
            coords = optimize_straights(coords, cyclic, angle, mx, debug=False)

        if debug:
            draw_points(coords, mx=mx, color=white, xray=True, modal=False)

        return coords
