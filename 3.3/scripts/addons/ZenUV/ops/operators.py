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

# Zen UV Generic Opertators

import bpy
import bmesh
from bpy.props import EnumProperty, BoolProperty
from ZenUV.utils import get_uv_islands as island_util
from ZenUV.utils.generic import (
    get_mesh_data,
    select_all,
    check_selection,
    check_selection_mode,
    switch_mesh_to_smooth_mode,
    collect_selected_objects_data,
    restore_selection,
    fit_uv_view,
    select_edges,
    is_island_flipped,
    select_elements,
    resort_objects,
    select_faces,
    select_loops,
    select_islands
)

from ZenUV.utils.messages import zen_message

from ZenUV.ui.labels import ZuvLabels
from ZenUV.utils.hops_integration import show_uv_in_3dview
from ZenUV.prop.zuv_preferences import get_prefs

class ZUV_OT_Select_UV_Overlap(bpy.types.Operator):
    bl_idname = "uv.zenuv_select_uv_overlap"
    bl_label = ZuvLabels.SELECT_OVERLAP_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.SELECT_OVERLAP_DESC

    @classmethod
    def poll(cls, context):
        return (2, 81, 0) < bpy.app.version

    def execute(self, context):
        for obj in context.objects_in_mode:
            me, bm = get_mesh_data(obj)
            uv_layer = bm.loops.layers.uv.verify()
            select_all(bm, action=False)
            context.scene.tool_settings.use_uv_select_sync = True
            bpy.ops.uv.select_overlap()
            overlapped_islands = island_util.get_island(context, bm, uv_layer)
            for island in overlapped_islands:
                for face in island:
                    face.select = True

            if not check_selection(context):
                zen_message(context, message="Overlappings are not found.",)

        return {'FINISHED'}


class ZUV_OT_SmoothBySharp(bpy.types.Operator):
    bl_idname = "view3d.zenuv_set_smooth_by_sharp"
    bl_label = ZuvLabels.AUTOSMOOTH_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.AUTOSMOOTH_DESC

    def execute(self, context):
        for obj in context.objects_in_mode:
            data = obj.data

            switch_mesh_to_smooth_mode(context)

            if data.auto_smooth_angle != 3.141590118408203:
                data.auto_smooth_angle = 3.141590118408203
                data.use_auto_smooth = True
            else:
                data.use_auto_smooth = not data.use_auto_smooth

        return {'FINISHED'}


class ZUV_OT_Isolate_Island(bpy.types.Operator):
    bl_idname = "uv.zenuv_isolate_island"
    bl_label = ZuvLabels.ISOLATE_ISLAND_LABEL
    bl_description = ZuvLabels.ISOLATE_ISLAND_DESC
    bl_options = {'REGISTER', 'UNDO'}

    isolate_mode = False
    bms = {}
    work_mode = None
    obj_in_isolation_mode = False
    selection_mode = False
    blender_sync_mode = None

    def invoke(self, context, event):
        self.bms = collect_selected_objects_data(context)
        self.work_mode = check_selection_mode(context)
        return self.execute(context)

    def execute(self, context):
        self.blender_sync_mode = context.scene.tool_settings.use_uv_select_sync
        for obj in self.bms:
            if not self.obj_in_isolation_mode and True in [f.hide for f in self.bms[obj]['data'].faces] or self.check_isolation(context, obj):
                self.obj_in_isolation_mode = True
            if not self.selection_mode and self.bms[obj]['pre_selected_faces'] or self.bms[obj]['pre_selected_edges'] or True in [v.select for v in self.bms[obj]['data'].verts]:
                self.selection_mode = True

        # Return From Isolation
        if self.obj_in_isolation_mode:
            if context.area.type == 'VIEW_3D':
                bpy.ops.mesh.reveal(select=False)
            elif context.area.type == 'IMAGE_EDITOR':
                if self.blender_sync_mode:
                    bpy.ops.mesh.reveal(select=False)
                else:
                    for obj in self.bms:
                        bm = self.bms[obj]['data']
                        for face in bm.faces:
                            face.select = True
                        bmesh.update_edit_mesh(obj.data, loop_triangles=False)

        elif not self.obj_in_isolation_mode and self.selection_mode:
            for obj in self.bms:
                bm = self.bms[obj]['data']
                uv_layer = bm.loops.layers.uv.verify()
                islands_for_isolate = island_util.get_island(context, bm, uv_layer)
                bmesh.update_edit_mesh(obj.data, loop_triangles=False)
                faces_for_isolate = []
                for island in islands_for_isolate:
                    faces_for_isolate.extend(island)

                if context.area.type == 'VIEW_3D':
                    self.go_to_isolate_mode([f for f in bm.faces if f not in faces_for_isolate])
                elif context.area.type == 'IMAGE_EDITOR':
                    if self.blender_sync_mode:
                        self.go_to_isolate_mode([f for f in bm.faces if f not in faces_for_isolate])
                    else:
                        self.go_to_isolate_mode_in_sync([f for f in bm.faces if f not in faces_for_isolate])

                bmesh.update_edit_mesh(obj.data, loop_triangles=False)

        return {'FINISHED'}

    def go_to_isolate_mode(self, faces_to_hide):
        for face in faces_to_hide:
            face.hide_set(True)

    def go_to_isolate_mode_in_sync(self, faces_to_hide):
        for face in faces_to_hide:
            face.select = False

    def check_isolation(self, context, obj):
        if context.area.type == 'IMAGE_EDITOR' and not self.blender_sync_mode and False in [f.select for f in self.bms[obj]['data'].faces]:
            return True
        else:
            return False


class ZUV_OT_Select_UV_Island(bpy.types.Operator):
    bl_idname = "uv.zenuv_select_island"
    bl_label = ZuvLabels.SELECT_ISLAND_LABEL
    bl_description = ZuvLabels.SELECT_ISLAND_DESC
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        objs = resort_objects(context, context.objects_in_mode)
        if not objs:
            return {'CANCELLED'}
        select_islands(context, objs)
        context.tool_settings.mesh_select_mode = [False, False, True]

        return {'FINISHED'}


class ZUV_OT_Select_Loop(bpy.types.Operator):
    bl_idname = "uv.zenuv_select_loop"
    bl_label = ZuvLabels.SELECT_EDGE_LOOP_LABEL
    bl_description = ZuvLabels.SELECT_EDGE_LOOP_DESC
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    # @classmethod
    # def poll(cls, context):
    #     for obj in context.objects_in_mode:
    #         me, bm = get_mesh_data(obj)
    #         if context.active_object.mode == 'EDIT' and True in [x.select for x in bm.edges]:
    #             return True

    def execute(self, context):
        for obj in context.objects_in_mode:
            me, bm = get_mesh_data(obj)
            bm.edges.ensure_lookup_table()
            # Start to work if some edge selectet
            if True in [edge.select for edge in bm.edges]:
                selected_edges = [edge for edge in bm.edges if edge.select]
                for selected_edge in selected_edges:
                    start_loop = selected_edge.link_loops[0]
                    if selected_edge:
                        # CW direction
                        for i in range(len(bm.edges)):
                            next_edge_in_loop = start_loop.link_loop_next.link_loop_radial_next.edge
                            next_loop = start_loop.link_loop_next.link_loop_radial_next.link_loop_next

                            if next_edge_in_loop.seam is True \
                                or next_edge_in_loop == selected_edge \
                                    or next_loop.edge == start_loop.link_loop_next.link_loop_next.edge \
                                    or next_loop.edge == start_loop.link_loop_radial_next.link_loop_prev.edge \
                                    or len(start_loop.link_loop_next.vert.link_edges) > 4:
                                break
                            else:

                                next_loop.edge.select = True
                                start_loop = next_loop

                        # CCW direction
                        for i in range(len(bm.edges)):
                            next_edge_in_loop = start_loop.link_loop_prev.link_loop_radial_next.edge
                            next_loop = start_loop.link_loop_prev.link_loop_radial_next.link_loop_prev

                            if next_edge_in_loop.seam is True \
                                or next_edge_in_loop == selected_edge \
                                    or next_loop.edge == start_loop.link_loop_next.link_loop_next.edge \
                                    or next_loop.edge == start_loop.link_loop_radial_next.link_loop_next.edge \
                                    or len(start_loop.vert.link_edges) > 4:
                                break
                            else:
                                next_loop.edge.select = True
                                start_loop = next_loop
            bmesh.update_edit_mesh(me, loop_triangles=False)

        return {'FINISHED'}


class ZUV_OT_Pack(bpy.types.Operator):
    bl_idname = "uv.zenuv_pack"
    bl_label = ZuvLabels.PACK_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.PACK_DESC

    display_uv: BoolProperty(
        name="Display UV",
        default=False,
        options={'HIDDEN'}
    )

    def execute(self, context):
        selection_mode = False
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        bms = collect_selected_objects_data(context)
        work_mode = check_selection_mode(context)
        scene = context.scene
        prop = context.scene.zen_uv

        for obj in bms:
            # Detect if exist previously selectet elements at least in one object
            if not selection_mode and bms[obj]['pre_selected_faces'] or bms[obj]['pre_selected_edges']:
                selection_mode = True

        blender_sync_mode = context.scene.tool_settings.use_uv_select_sync

        context.scene.tool_settings.use_uv_select_sync = True

        bpy.ops.mesh.select_all(action='SELECT')

        # UVPackmaster 2
        if addon_prefs.packEngine == "UVP":
            # if addon_prefs.averageBeforePack:
            #     bpy.ops.uv.average_islands_scale()
            if hasattr(bpy.types, bpy.ops.uvpackmaster2.uv_pack.idname()):
                print(ZuvLabels.PACK_CONSOLE_OUTPUT_UVP)
                if hasattr(context.scene, "uvp2_props") and hasattr(context.scene.uvp2_props, "margin"):
                    uvp2_props = context.scene.uvp2_props
                    try:
                        member = [
                            uvp2_props.margin,
                            uvp2_props.rot_enable,
                            uvp2_props.lock_overlapping_mode,
                            uvp2_props.fixed_scale,
                            uvp2_props.lock_overlapping_mode,
                            uvp2_props.heuristic_enable,
                            uvp2_props.normalize_islands,
                            uvp2_props.pack_to_others,
                            uvp2_props.use_blender_tile_grid,
                            # uvp2_props.tile_count,
                            # uvp2_props.tiles_in_row
                        ]
                    except Exception:
                        _message = ("Zen UV: Some features of UV Packmaster cannot be performed. Update UV Packmaster to the latest version.")
                        print(_message)
                        self.report({'WARNING'}, _message)
                        zen_message(context, message=_message,)
                        return {'CANCELLED'}

                    # print("UVP Margin before:", context.scene.uvp2_props.margin)
                    uvp2_props.margin = addon_prefs.margin
                    uvp2_props.rot_enable = addon_prefs.rotateOnPack
                    uvp2_props.use_blender_tile_grid = False
                    uvp2_props.pack_to_others = False
                    # if addon_prefs.keepStacked:
                    uvp2_props.normalize_islands = addon_prefs.averageBeforePack
                    uvp2_props.lock_overlapping_mode = addon_prefs.lock_overlapping_mode
                    uvp2_props.fixed_scale = addon_prefs.packFixedScale
                    if bpy.ops.uvpackmaster2.uv_pack.poll():
                        bpy.ops.uvpackmaster2.uv_pack("INVOKE_DEFAULT")
                    else:
                        self.report({'WARNING'}, "For some reason, UVPackmaster 2 cannot be launched. Check out its performance separately from Zen UV.")
                    fit_uv_view(context, mode="all")
                    self.restore_uvp2_settings(uvp2_props, member)
            else:
                # zen_message(message="Nothing is produced. Seems like Pack Master 2 is not installed on your system.")
                bpy.ops.wm.call_menu(name="ZUV_MT_ZenPack_Uvp_Popup")

        # Blender Pack Engine
        elif addon_prefs.packEngine == "BLDR":
            if addon_prefs.averageBeforePack:
                bpy.ops.uv.average_islands_scale()
            try:
                bpy.ops.uv.pack_islands(rotate=addon_prefs.rotateOnPack, margin=addon_prefs.margin)
            except Exception:
                _message = "Zen UV: Potential Crash in Blender Pack process. \
                    Try to clean up geometry."
                print(_message)
                self.report({'WARNING'}, _message)
            fit_uv_view(context, mode="all")

        # UV-Packer
        elif addon_prefs.packEngine == "UVPACKER":
            if hasattr(bpy.types, bpy.ops.uvpackeroperator.packbtn.idname()):
                print(ZuvLabels.PACK_CONSOLE_OUTPUT_UVPACKER)

                if hasattr(context.scene, "UVPackerProps") and hasattr(context.scene.UVPackerProps, "uvp_padding"):
                    uvPackerProps = scene.UVPackerProps
                    member = [
                        # uvPackerProps.uvp_padding,
                        uvPackerProps.uvp_width,
                        uvPackerProps.uvp_height,
                        uvPackerProps.uvp_rescale,
                        uvPackerProps.uvp_rotate,
                        uvPackerProps.uvp_padding,
                    ]
                    # A margin in the UV-Packer uses an abstract value, so it is excluded from the settings.
                    uvPackerProps.uvp_width = addon_prefs.TD_TextureSizeX
                    uvPackerProps.uvp_height = addon_prefs.TD_TextureSizeY
                    uvPackerProps.uvp_rescale = addon_prefs.averageBeforePack
                    uvPackerProps.uvp_padding = prop.pack_uv_packer_margin
                    if not addon_prefs.rotateOnPack:
                        uvPackerProps.uvp_rotate = "0"
                if bpy.ops.uvpackeroperator.packbtn.poll():
                    bpy.ops.uvpackeroperator.packbtn()
                else:
                    self.report({'WARNING'}, "For some reason, UV-Packer cannot be launched. Check out its performance separately from Zen UV.")
                fit_uv_view(context, mode="all")
                uvPackerProps.uvp_width = member[0]
                uvPackerProps.uvp_height = member[1]
                uvPackerProps.uvp_rescale = member[2]
                uvPackerProps.uvp_rotate = member[3]
                uvPackerProps.uvp_padding = member[4]
            else:
                bpy.ops.wm.call_menu(name="ZUV_MT_ZenPack_Uvpacker_Popup")

        # elif addon_prefs.packEngine == "CUSTOM":
        #     print(f"Custom command executed: {addon_prefs.customEngine}")
        #     if hasattr(bpy.types, bpy.ops.uvpackeroperator.packbtn.idname()):
        #         print(ZuvLabels.PACK_CONSOLE_OUTPUT_CUSTOM)
        #         if bpy.ops.uvpackeroperator.packbtn.poll():
        #             bpy.ops.uvpackeroperator.packbtn()
        #         else:
        #             self.report({'WARNING'}, "For some reason, Custom Command cannot be launched. Check out its performance separately from Zen UV.")
        #         fit_uv_view(context, mode="all")

        bpy.ops.mesh.select_all(action='DESELECT')

        context.scene.tool_settings.use_uv_select_sync = blender_sync_mode

        if selection_mode:
            for obj in bms:
                restore_selection(
                    work_mode,
                    bms[obj]['pre_selected_faces'],
                    bms[obj]['pre_selected_edges']
                )
        fit_uv_view(context, mode="all")
        if self.display_uv:
            # Display UV Widget from HOPS addon
            show_uv_in_3dview(context, use_selected_meshes=True, use_selected_faces=False, use_tagged_faces=False)

        return {'FINISHED'}

    def restore_uvp2_settings(self, uvp2_props, member):
        uvp2_props.margin = member[0]
        uvp2_props.rot_enable = member[1]
        uvp2_props.lock_overlapping_mode = member[2]
        uvp2_props.fixed_scale = member[3]
        uvp2_props.lock_overlapping_mode = member[4]
        uvp2_props.heuristic_enable = member[5]
        uvp2_props.normalize_islands = member[6]
        uvp2_props.pack_to_others = member[7]
        uvp2_props.use_blender_tile_grid = member[8]
        # uvp2_props.tile_count = member[8]
        # uvp2_props.tiles_in_row = member[9]


class ZUV_OT_SyncZenUvToUVP(bpy.types.Operator):
    bl_idname = "uv.zenuv_sync_to_uvp"
    bl_label = ZuvLabels.OT_SYNC_TO_UVP_LABEL
    bl_description = ZuvLabels.OT_SYNC_TO_UVP_DESC
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if hasattr(bpy.types, bpy.ops.uvpackmaster2.uv_pack.idname()):
            print(ZuvLabels.PACK_CONSOLE_OUTPUT_UVP)
            if hasattr(context.scene, "uvp2_props") and hasattr(context.scene.uvp2_props, "margin"):
                addon_prefs = get_prefs()
                context.scene.uvp2_props.margin = addon_prefs.margin
                context.scene.uvp2_props.rot_enable = addon_prefs.rotateOnPack
                context.scene.uvp2_props.lock_overlapping_mode = addon_prefs.lock_overlapping_mode
                context.scene.uvp2_props.fixed_scale = addon_prefs.packFixedScale
                context.scene.uvp2_props.normalize_islands = addon_prefs.averageBeforePack
        else:
            bpy.ops.wm.call_menu(name="ZUV_MT_ZenPack_Uvp_Popup")
        return {'FINISHED'}


class ZUV_OT_SelectSharp(bpy.types.Operator):
    bl_idname = "mesh.zenuv_select_sharp"
    bl_label = ZuvLabels.OT_SELECT_EDGES_SHARP_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.OT_SELECT_EDGES_SHARP_DESC

    @classmethod
    def poll(cls, context):
        if context.objects_in_mode:
            return True
        else:
            return False

    def execute(self, context):
        for obj in context.objects_in_mode:
            me, bm = get_mesh_data(obj)
            # data = obj.data
            select_edges([e for e in bm.edges if not e.smooth])
            bmesh.update_edit_mesh(obj.data, loop_triangles=False)
        return {'FINISHED'}


class ZUV_OT_SelectSeams(bpy.types.Operator):
    bl_idname = "mesh.zenuv_select_seams"
    bl_label = ZuvLabels.OT_SELECT_EDGES_SEAM_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.OT_SELECT_EDGES_SEAM_DESC

    @classmethod
    def poll(cls, context):
        if context.objects_in_mode:
            return True
        else:
            return False

    def execute(self, context):
        for obj in context.objects_in_mode:
            me, bm = get_mesh_data(obj)
            # data = obj.data
            select_edges([e for e in bm.edges if e.seam])
            bmesh.update_edit_mesh(obj.data, loop_triangles=False)
        return {'FINISHED'}


class ZUV_OT_SelectFlipped(bpy.types.Operator):
    bl_idname = "uv.zenuv_select_flipped"
    bl_label = ZuvLabels.OT_SELECT_FLIPPED_ISLANDS_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.OT_SELECT_FLIPPED_ISLANDS_DESC

    @classmethod
    def poll(cls, context):
        if context.objects_in_mode:
            return True
        else:
            return False

    def execute(self, context):
        sync_uv = context.scene.tool_settings.use_uv_select_sync
        for obj in context.objects_in_mode:
            me, bm = get_mesh_data(obj)
            islands_for_process = island_util.get_islands(bm)
            uv_layer = bm.loops.layers.uv.verify()

            self.clear_selection(context, bm, uv_layer)

            for island in islands_for_process:
                if is_island_flipped(island, uv_layer):
                    if context.area.type == 'VIEW_3D':
                        select_all(bm, action=False)
                        select_elements(island)
                    elif context.area.type == 'IMAGE_EDITOR':
                        if sync_uv:
                            select_all(bm, action=False)
                            select_elements(island)
                        else:
                            select_elements([loop[uv_layer] for face in island for loop in face.loops])

            bmesh.update_edit_mesh(obj.data, loop_triangles=False)
        return {'FINISHED'}

    def clear_selection(self, context, bm, uv_layer):
        if context.area.type == 'VIEW_3D':
            select_all(bm, action=False)
        elif context.area.type == 'IMAGE_EDITOR':
            for loop in [loop[uv_layer] for face in bm.faces for loop in face.loops]:
                loop.select = False


class ZUV_OT_MirrorSeams(bpy.types.Operator):
    bl_idname = "mesh.zenuv_mirror_seams"
    bl_label = ZuvLabels.OT_MIRROR_SEAMS_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.OT_MIRROR_SEAMS_DESC

    use_mirror_x: BoolProperty(
        name="X",
        default=True,
        options={'HIDDEN'}
    )
    use_mirror_y: BoolProperty(
        name="Y",
        default=False,
        options={'HIDDEN'}
    )
    use_mirror_z: BoolProperty(
        name="Z",
        default=False,
        options={'HIDDEN'}
    )

    @classmethod
    def poll(cls, context):
        if context.objects_in_mode:
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        layout.label(text="Axis:")
        row = layout.row(align=True)
        row.prop(self, "use_mirror_x", text="X", toggle=True)
        row.prop(self, "use_mirror_y", text="Y", toggle=True)
        row.prop(self, "use_mirror_z", text="Z", toggle=True)

    def execute(self, context):
        context.tool_settings.mesh_select_mode = [False, True, False]
        axis = set("X")
        if self.use_mirror_x:
            axis.update("X")
        else:
            axis.discard("X")
        if self.use_mirror_y:
            axis.update("Y")
        else:
            axis.discard("Y")
        if self.use_mirror_z:
            axis.update("Z")
        else:
            axis.discard("Z")

        for obj in context.objects_in_mode:
            me, bm = get_mesh_data(obj)
            bm.edges.ensure_lookup_table()
            seams = [e for e in bm.edges if e.seam]
            select_all(bm, action=False)
            for e in seams:
                e.select = True
            bpy.ops.mesh.select_mirror(axis=axis, extend=True)
            new_edges = [e for e in bm.edges if e.select]
            for e in new_edges:
                e.seam = True
            bmesh.update_edit_mesh(me, loop_triangles=False)

        return {'FINISHED'}


if __name__ == '__main__':
    pass
