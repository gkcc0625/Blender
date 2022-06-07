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

""" Zen UV Finishing System """
import bpy
import bmesh
# import mathutils

# from ZenUV.utils.transform import move_island_sort, centroid
from ZenUV.utils import get_uv_islands as island_util
from ZenUV.utils.generic import (
    enshure_facemap,
    collect_selected_objects_data,
    fit_uv_view,
    check_selection,
    get_mesh_data,
    switch_shading_style,
    enshure_facemap
)
from ZenUV.ui.labels import ZuvLabels
from ZenUV.utils import vc_processor as vc
from ZenUV.utils.finishing_util import (
    FINISHED_FACEMAP_NAME,
    sort_islands,
    tag_finished,
    get_finished_map_from,
    is_finished_activated,
    show_in_view_finished,
    select_finished,
    finished_enshure_consistency
)
from ZenUV.zen_checker.checker import get_materials_with_overrider, get_materials_from_objects


class ZUV_OT_Sorting_Islands(bpy.types.Operator):
    bl_idname = "uv.zenuv_islands_sorting"
    bl_label = ZuvLabels.SORTING_LABEL
    bl_description = ZuvLabels.SORTING_DESC
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        # print("Zen UV: Islands Sorting Starting")
        selection_mode = False

        bms = collect_selected_objects_data(context)
        # work_mode = check_selection_mode()

        for obj in bms:
            # Detect if exist previously selectet elements at least in one object
            if not selection_mode and \
                    bms[obj]['pre_selected_faces'] or \
                    bms[obj]['pre_selected_edges']:
                selection_mode = True

        for obj in bms:
            # print("\nStart sorting", obj.name)
            bm = bms[obj]['data']
            bm.faces.ensure_lookup_table()
            bm.verts.ensure_lookup_table()
            me = obj.data
            # finished_enshure_consistency(context, bm)
            islands_for_process = island_util.get_islands(bm)
            sort_islands(me, bm, islands_for_process)
            bmesh.update_edit_mesh(me, loop_triangles=False)
        fit_uv_view(context, mode="checker")
        return {'FINISHED'}


class ZUV_OT_Tag_Finished(bpy.types.Operator):
    """
    Operator to Tag Finished Islands
    """
    bl_idname = "uv.zenuv_tag_finished"
    bl_label = ZuvLabels.OT_TAG_FINISHED_LABEL
    bl_description = ZuvLabels.OT_TAG_FINISHED_DESC
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        tag_finished(context, action="TAG")
        fit_uv_view(context, mode="checker")
        return {'FINISHED'}


class ZUV_OT_UnTag_Finished(bpy.types.Operator):
    """
    Operator to Untag Finished Islands
    """
    bl_idname = "uv.zenuv_untag_finished"
    bl_label = ZuvLabels.OT_UNTAG_FINISHED_LABEL
    bl_description = ZuvLabels.OT_UNTAG_FINISHED_DESC
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        tag_finished(context, action="UNTAG")
        fit_uv_view(context, mode="checker")
        return {'FINISHED'}


class ZUV_OT_Display_Finished(bpy.types.Operator):
    bl_idname = "uv.zenuv_display_finished"
    bl_label = ZuvLabels.OT_FINISHED_DISPLAY_LABEL
    bl_description = ZuvLabels.OT_FINISHED_DISPLAY_DESC
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.zen_display.finished = not context.scene.zen_display.finished
        """
        bpy.ops.mesh.select_all(action='DESELECT')

        for obj in context.objects_in_mode:
            vc.disable_zen_vc_map(obj, vc.Z_TD_BALANCED_V_MAP_NAME)

        #  Try to detect finished color map in selected objects
        finished_vc_map = is_finished_activated(context)
        if finished_vc_map:  # If finished vc map exist - delete it
            for obj in context.objects_in_mode:
                finished_vc_map.active = False
                finished_vc_map = get_finished_map_from(obj)
                if finished_vc_map:
                    obj.data.vertex_colors.remove(finished_vc_map)
            switch_shading_style(context, "TEXTURE", switch=False)
        else:  # If finished vc map not exist - create it
            for obj in context.objects_in_mode:
                me, bm = get_mesh_data(obj)
                finished_facemap = enshure_facemap(bm, FINISHED_FACEMAP_NAME)
                show_in_view_finished(context, bm, finished_facemap)
                finished_vc_map = get_finished_map_from(obj)
                if finished_vc_map:
                    finished_vc_map.active = True

            # Update VC on objects
            bpy.ops.object.mode_set(mode='VERTEX_PAINT')
            bpy.ops.object.mode_set(mode="EDIT")
            switch_shading_style(context, "VERTEX", switch=False)
        """
        return {"FINISHED"}


class ZUV_OT_Select_Finished(bpy.types.Operator):
    bl_idname = "uv.zenuv_select_finished"
    bl_label = ZuvLabels.OT_FINISHED_SELECT_LABEL
    bl_description = ZuvLabels.OT_FINISHED_SELECT_DESC
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in context.objects_in_mode:
            me, bm = get_mesh_data(obj)
            bm.faces.ensure_lookup_table()
            finished_facemap = enshure_facemap(bm, FINISHED_FACEMAP_NAME)
            select_finished(bm, finished_facemap)
            bmesh.update_edit_mesh(me, loop_triangles=False)

        return {"FINISHED"}



if __name__ == '__main__':
    pass
