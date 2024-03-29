import bpy
import bmesh
from ._utils import vertloops, correct_normal, average_vector, tri_points_order
from mathutils import Vector, Matrix


class KeItemize(bpy.types.Operator):
    bl_idname = "mesh.ke_itemize"
    bl_label = "Itemize"
    bl_description = "Creates new mesh from selection in face or edge mode. Active face/edge(w.connected loop) " \
                     "will be used for rotation/position (the bottom). Edge mode auto-connects linked elements."
    bl_options = {'REGISTER', 'UNDO'}

    mode: bpy.props.EnumProperty(items=[("DEFAULT", "Default", "", 1), ("DUPE", "Duplicate", "", 2)],
                                 name="Mode", default="DEFAULT")

    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.object.type == 'MESH' and
                context.object.data.is_editmode)

    def execute(self, context):
        obj = bpy.context.active_object

        ouc = obj.users_collection
        if len(ouc) > 0:
            coll = ouc[0]
        else:
            coll = context.scene.collection

        bm = bmesh.from_edit_mesh(obj.data)
        obj_mtx = obj.matrix_world.copy()
        sel_mode = bpy.context.tool_settings.mesh_select_mode[:]

        sel_poly = [p for p in bm.faces if p.select]
        active_face = bm.faces.active
        n_v, pos, vec_poslist = [], [], []

        #
        # Initial selection
        #
        if sel_mode[1]:
            # EDGE MODE
            bm.edges.ensure_lookup_table()

            sel_edges = [e for e in bm.edges if e.select]
            active_edge = bm.select_history.active

            if len(sel_edges) >= 2 and active_edge:
                # Expand Linked
                bpy.ops.mesh.select_linked()
                # linked_verts = [v for v in bm.verts if v.select]
                # Find the active edges loop selection
                vert_pairs = []
                for e in sel_edges:
                    vp = [v for v in e.verts]
                    vert_pairs.append(vp)

                active_loop_verts = 0
                loops = vertloops(vert_pairs)

                if loops:
                    # print("loop found")
                    sel_verts = []
                    for loop in loops:
                        if active_edge.verts[0] in loop and active_edge.verts[1] in loop:
                            sel_verts.extend(loop)
                            active_loop_verts = len(loop)
                            break
                    sel_verts = list(set(sel_verts))

                    if active_loop_verts >= 3:
                        # Trimming selection
                        if len(sel_verts) > 4:
                            vec_poslist.append(obj_mtx @ sel_verts[0].co)
                            vec_poslist.append(obj_mtx @ sel_verts[int(len(sel_verts) * 0.33)].co)
                            vec_poslist.append(obj_mtx @ sel_verts[int(len(sel_verts) * 0.66)].co)
                        else:
                            vec_poslist = obj_mtx @ sel_verts[0].co,\
                                          obj_mtx @ sel_verts[1].co,\
                                          obj_mtx @ sel_verts[2].co

                    if active_loop_verts > 2:
                        sel_pos_co = [obj_mtx @ v.co for v in sel_verts]
                        pos = Vector(average_vector(sel_pos_co))

        elif sel_mode[2] and sel_poly and active_face:
            # FACE mode
            n_v = correct_normal(obj_mtx, active_face.normal * -1)
            vec_poslist = [obj_mtx @ v.co for v in active_face.verts]
            pos = obj_mtx @ active_face.calc_center_median()

        else:
            self.report({"INFO"}, "Selection Error / Active Element not found?")

        #
        # Get settings & Make new item
        #
        if pos and vec_poslist:

            h = tri_points_order(vec_poslist)
            vec_poslist = vec_poslist[h[0]], vec_poslist[h[1]], vec_poslist[h[2]]

            p1, p2, p3 = vec_poslist[0], vec_poslist[1], vec_poslist[2]
            v_1 = p2 - p1
            v_2 = p3 - p1
            if not n_v:
                n_v = v_1.cross(v_2).normalized()
                n_v *= -1
            # find the better rot
            c1 = n_v.cross(v_1).normalized()
            c2 = n_v.cross(v_2).normalized()
            if c1.dot(n_v) < c2.dot(n_v):
                u_v = c2
            else:
                u_v = c1
            t_v = u_v.cross(n_v).normalized()

            nrot = Matrix((t_v, u_v, n_v)).to_4x4().inverted()
            loc = pos
            rot = nrot.to_euler()
            rot.x = round(rot.x, 4)
            rot.y = round(rot.y, 4)
            rot.z = round(rot.z, 4)

            # Create new mesh and apply settings
            new_mesh = bpy.data.meshes.new(obj.name + '_itemized_mesh')
            new_obj = bpy.data.objects.new(obj.name + '_itemized', new_mesh)
            coll.objects.link(new_obj)

            new_obj.location = loc
            new_obj.rotation_euler = rot
            new_obj.data.use_auto_smooth = True

            if self.mode == "DUPE":
                bpy.ops.mesh.duplicate()

            bpy.ops.mesh.separate(type='SELECTED')
            temp_dupe = bpy.context.selected_objects[-1]

            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action="DESELECT")

            temp_dupe.select_set(True)
            new_obj.select_set(True)

            bpy.context.view_layer.objects.active = temp_dupe
            bpy.context.view_layer.objects.active = new_obj
            bpy.ops.object.join('INVOKE_DEFAULT')

            bpy.ops.transform.select_orientation(orientation='LOCAL')
            bpy.context.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'

        else:
            self.report({"INFO"}, "Selection Error / Active Element not found?")

        return {"FINISHED"}


#
# CLASS REGISTRATION
#
classes = (KeItemize,)

modules = ()


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
