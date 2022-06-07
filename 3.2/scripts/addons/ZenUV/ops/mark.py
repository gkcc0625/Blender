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

""" # Zen UV Mark System """
from math import radians
import bpy
import bmesh
from ZenUV.utils.generic import (
    get_mesh_data,
    select_all,
    collect_selected_objects_data,
    enshure_facemap
)
from ZenUV.utils.get_uv_islands import uv_bound_edges_indexes
from ZenUV.utils.finishing_util import FINISHED_FACEMAP_NAME


from ZenUV.ui.labels import ZuvLabels


def call_from_zen_check():
    return ZUV_OT_Mark_Seams.call_from_zen


def restore_selected_faces(selfaces):
    for face in selfaces:
        face.select = True


def assign_seam_to_edges(edges, assign=True):
    for edge in edges:
        edge.seam = assign


def assign_sharp_to_edges(edges, assign=True):
    for edge in edges:
        edge.smooth = not assign


def assign_seam_to_selected_edges(bm):
    for edge in bm.edges:
        if edge.select:
            edge.seam = True


def get_bound_edges(edges_from_polygons):
    boundary_edges = []
    for edge in edges_from_polygons:
        if False in [f.select for f in edge.link_faces] or edge.is_boundary:
            boundary_edges.append(edge)
    return boundary_edges


def zuv_mark_seams(context, bm, silent_mode=False, assign=True, switch=False):
    addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
    selfaces = []
    seledges = []
    # Check if face selection mode
    # Check if have currently selected faces
    # Check Mark Seams is True
    if bm.select_mode == {'FACE'} and True in [f.select for f in bm.faces]:
        fin_fmap = enshure_facemap(bm, FINISHED_FACEMAP_NAME)
        selfaces = [f for f in bm.faces if f.select]
        region_loop_edges = get_bound_edges([e for e in bm.edges if e.select])
        # Emulate Live Unwrap as Blender's native
        if switch and False not in [edge.seam for edge in region_loop_edges]:
            assign = not assign

        # Clear FINISHED for selected faces
        for face in selfaces:
            face[fin_fmap] = 0

        # Test if selected edges exist - seams to borders
        if region_loop_edges:
            # Clear sharp and seams for selected faces
            edges_from_faces = [e for f in selfaces for e in f.edges]
            if addon_prefs.markSeamEdges:
                for edge in edges_from_faces:
                    edge.seam = False
                assign_seam_to_edges(region_loop_edges, assign=assign)
            if addon_prefs.markSharpEdges:
                for edge in edges_from_faces:
                    edge.smooth = True
                assign_sharp_to_edges(region_loop_edges, assign=assign)
        else:
            if not silent_mode:
                bpy.ops.wm.call_menu(name="ZUV_MT_ZenMark_Popup")
            # zen_message(message="Nothing is produced. Selected polygons do not have a borders.")

    # Check if Edge selection mode
    if bm.select_mode == {'EDGE'} and True in [x.select for x in bm.edges]:
        seledges = [e for e in bm.edges if e.select]
        # Emulate Live Unwrap as Blender's native
        if switch and False not in [edge.seam for edge in seledges]:
            assign = not assign
        if addon_prefs.markSeamEdges:
            # print("Seam is true")
            assign_seam_to_edges(seledges, assign=assign)
        if addon_prefs.markSharpEdges:
            # print("Sharp is true")
            assign_sharp_to_edges(seledges, assign=assign)


class ZUV_OT_Mark_Seams(bpy.types.Operator):
    """Mark selected edges or face borders as Seams and/or Sharp edges"""
    bl_idname = "uv.zenuv_mark_seams"
    bl_label = ZuvLabels.OT_MARK_LABEL
    bl_description = ZuvLabels.OT_MARK_DESC
    bl_options = {'REGISTER', 'UNDO'}

    call_from_zen = False

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        scene = context.scene
        for obj in context.objects_in_mode:
            bm = bmesh.from_edit_mesh(obj.data)
            zuv_mark_seams(context, bm, assign=True, switch=False)
            bmesh.update_edit_mesh(obj.data, loop_triangles=False)

        if scene.tool_settings.use_edge_path_live_unwrap:
            bpy.ops.uv.zenuv_unwrap("INVOKE_DEFAULT", mark_switch=False, mark_selected=False)
        return {'FINISHED'}


class ZUV_OT_Unmark_Seams(bpy.types.Operator):
    bl_idname = "uv.zenuv_unmark_seams"
    bl_label = ZuvLabels.OT_UNMARK_LABEL
    bl_description = ZuvLabels.OT_UNMARK_DESC
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        scene = context.scene
        for obj in context.objects_in_mode:
            bm = bmesh.from_edit_mesh(obj.data)
            zuv_mark_seams(context, bm, assign=False, switch=False)
            bmesh.update_edit_mesh(obj.data, loop_triangles=False)

        if scene.tool_settings.use_edge_path_live_unwrap:
            bpy.ops.uv.zenuv_unwrap("INVOKE_DEFAULT", action='NONE', mark_switch=False, mark_selected=False)
        return {'FINISHED'}


class ZUV_OT_Unmark_All(bpy.types.Operator):
    bl_idname = "uv.zenuv_unmark_all"
    bl_label = ZuvLabels.UNMARK_ALL_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.UNMARK_ALL_DESC

    def execute(self, context):
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        for obj in context.objects_in_mode:
            me, bm = get_mesh_data(obj)

            """ Clear Pinned Data """
            uv_layer = bm.loops.layers.uv.verify()

            loops = [loop for face in bm.faces for loop in face.loops]
            edges = [edge for edge in bm.edges if not edge.hide]
            for loop in loops:
                loop[uv_layer].pin_uv = False

            if addon_prefs.markSeamEdges:
                for edge in edges:
                    edge.seam = False

            if addon_prefs.markSharpEdges:
                for edge in edges:
                    edge.smooth = True

            select_all(bm, action=False)
            bmesh.update_edit_mesh(me, loop_triangles=False)

        return {'FINISHED'}


def seams_by_uv_border(bms):
    for obj in bms:
        bm = bms[obj]['data']
        uv_layer = bm.loops.layers.uv.verify()
        faces = [f for f in bm.faces if not f.hide]
        for i in uv_bound_edges_indexes(faces, uv_layer):
            bm.edges[i].seam = True
        bmesh.update_edit_mesh(obj.data, loop_triangles=False)


def seams_by_open_edges(bms):
    for obj in bms:
        bm = bms[obj]['data']
        sources = [e.index for e in bm.edges if True in [f.hide for f in e.link_faces] and not e.hide]
        bound = [e.index for e in bm.edges if e.is_boundary and not e.link_faces[0].hide]
        sources.extend(bound)
        for i in sources:
            bm.edges[i].seam = True
        bmesh.update_edit_mesh(obj.data, loop_triangles=False)


def seams_by_sharp(context):
    for obj in context.objects_in_mode:
        me, bm = get_mesh_data(obj)
        for edge in bm.edges:
            edge.seam = not edge.smooth
        bmesh.update_edit_mesh(me, loop_triangles=False)


def sharp_by_seam(context):
    for obj in context.objects_in_mode:
        me, bm = get_mesh_data(obj)
        for edge in bm.edges:
            edge.smooth = not edge.seam
        bmesh.update_edit_mesh(me, loop_triangles=False)


class ZUV_OT_UnifiedMark(bpy.types.Operator):
    bl_idname = "uv.zenuv_unified_mark"
    bl_label = ZuvLabels.UNIFIED_MARK_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.UNIFIED_MARK_DESC

    convert: bpy.props.EnumProperty(
        items=[
            ("SEAM_BY_UV_BORDER", ZuvLabels.MARK_BY_BORDER_LABEL, ZuvLabels.MARK_BY_BORDER_DESC),
            ("SEAM_BY_SHARP", ZuvLabels.SEAM_BY_SHARP_LABEL, ZuvLabels.SEAM_BY_SHARP_DESC),
            ("SHARP_BY_SEAM", ZuvLabels.SHARP_BY_SEAM_LABEL, ZuvLabels.SHARP_BY_SEAM_DESC),
            ("SEAM_BY_OPEN_EDGES", ZuvLabels.SEAM_BY_OPEN_EDGES_LABEL, ZuvLabels.SEAM_BY_OPEN_EDGES_DESC),
        ],
        default="SEAM_BY_OPEN_EDGES",
        options={'HIDDEN'}
    )

    def invoke(self, context, event):
        self.convert = context.scene.zen_uv.sl_convert
        return self.execute(context)

    def execute(self, context):
        bms = collect_selected_objects_data(context)
        if self.convert == "SEAM_BY_UV_BORDER":
            seams_by_uv_border(bms)
        elif self.convert == "SEAM_BY_SHARP":
            seams_by_sharp(context)
        elif self.convert == "SHARP_BY_SEAM":
            sharp_by_seam(context)
        elif self.convert == "SEAM_BY_OPEN_EDGES":
            seams_by_open_edges(bms)
        return {'FINISHED'}


class ZUV_OT_Seams_By_UV_Borders(bpy.types.Operator):
    bl_idname = "uv.zenuv_seams_by_uv_islands"
    bl_label = ZuvLabels.MARK_BY_BORDER_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.MARK_BY_BORDER_DESC

    def execute(self, context):
        bms = collect_selected_objects_data(context)

        seams_by_uv_border(bms)
        return {'FINISHED'}


class ZUV_OT_Seams_By_Open_Edges(bpy.types.Operator):
    bl_idname = "uv.zenuv_seams_by_open_edges"
    bl_label = ZuvLabels.SEAM_BY_OPEN_EDGES_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.SEAM_BY_OPEN_EDGES_DESC

    def execute(self, context):
        bms = collect_selected_objects_data(context)

        seams_by_open_edges(bms)
        return {'FINISHED'}


class ZUV_OT_Seam_By_Sharp(bpy.types.Operator):
    bl_idname = "uv.zenuv_seams_by_sharp"
    bl_label = ZuvLabels.SEAM_BY_SHARP_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.SEAM_BY_SHARP_DESC

    def execute(self, context):
        seams_by_sharp(context)
        return {'FINISHED'}


class ZUV_OT_Sharp_By_Seam(bpy.types.Operator):
    bl_idname = "uv.zenuv_sharp_by_seams"
    bl_label = ZuvLabels.SHARP_BY_SEAM_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.SHARP_BY_SEAM_DESC

    def execute(self, context):
        sharp_by_seam(context)
        return {'FINISHED'}


class ZUV_OT_Auto_Mark(bpy.types.Operator):
    bl_idname = "uv.zenuv_auto_mark"
    bl_label = ZuvLabels.AUTO_MARK_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.AUTO_MARK_DESC

    angle: bpy.props.FloatProperty(
        name=ZuvLabels.AUTO_MARK_ANGLE_NAME,
        description=ZuvLabels.AUTO_MARK_ANGLE_DESC,
        min=0.0,
        max=180.0,
        default=30.03
    )

    action: bpy.props.EnumProperty(
        items=[
            ("NONE", "Auto Seams", "Default Auto Seams Mode."),
            ("RESET", "Reset Auto Seams", "Perform Reset Values of Operator")],
        default="NONE"
    )

    addon_prefs = None

    def invoke(self, context, event):
        self.addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        return self.execute(context)

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        self.addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        for obj in context.objects_in_mode:
            me, bm = get_mesh_data(obj)

            sharp_edges = [edge for edge in bm.edges if not edge.hide and len(edge.link_faces) == 2 and edge.calc_face_angle() > radians(self.angle)]
            holes_edges = [edge for edge in bm.edges if not edge.hide and len(edge.link_faces) == 1]
            sharp_edges.extend(holes_edges)

            not_sharp_edges = [edge for edge in bm.edges if not edge.hide and edge not in sharp_edges]

            for edge in sharp_edges:
                if self.addon_prefs.markSeamEdges:
                    edge.seam = True
                if self.addon_prefs.markSharpEdges:
                    edge.smooth = False
            for edge in not_sharp_edges:
                if self.addon_prefs.markSeamEdges:
                    edge.seam = False
                if self.addon_prefs.markSharpEdges:
                    edge.smooth = True

            bmesh.update_edit_mesh(me, loop_triangles=False)

        return {'FINISHED'}

    def draw(self, context):
        self.addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        layout = self.layout
        layout.prop(self, "angle")
        layout.prop(self.addon_prefs, 'markSeamEdges')
        layout.prop(self.addon_prefs, 'markSharpEdges')
