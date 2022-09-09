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
    Zen UV Copy / Paste uv coordinates system
"""


import bpy
from bpy.props import BoolProperty, EnumProperty
from ZenUV.utils import get_uv_islands as island_util
from ZenUV.utils.generic import (
    get_mesh_data,
    resort_objects,
    update_indexes,
    resort_by_type_mesh
    )
from ZenUV.stacks.utils import Cluster
from ZenUV.ui.labels import ZuvLabels
from ZenUV.utils.clib.lib_init import StackSolver


class ZUV_OT_UV_Copy(bpy.types.Operator):
    ''' Store selected UV island to mesh data '''
    bl_idname = "uv.zenuv_copy_uv"
    bl_label = ZuvLabels.OT_UV_COPY_LABEL
    bl_description = ZuvLabels.OT_UV_COPY_DESC
    bl_options = {'REGISTER', 'UNDO'}

    st_store_mode: EnumProperty(
        name=ZuvLabels.PREF_OT_COPY_MODE_LABEL,
        description=ZuvLabels.PREF_OT_COPY_MODE_DESC,
        items=[
            (
                "ISLAND",
                ZuvLabels.PREF_OT_COPY_MODE_ISLAND_LABEL,
                ZuvLabels.PREF_OT_COPY_MODE_ISLAND_DESC
            ),
            (
                "FACES",
                ZuvLabels.PREF_OT_COPY_MODE_FACES_LABEL,
                ZuvLabels.PREF_OT_COPY_MODE_FACES_DESC
            ),
        ],
        default="ISLAND"
    )
    uv_copy_dict = dict()
    objs = None

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def invoke(self, context, event):
        scene = context.scene
        self.objs = resort_objects(context, context.objects_in_mode)
        if not self.objs:
            self.check_copy_conditions(scene)
            return {"CANCELLED"}
        update_indexes(self.objs)
        return self.execute(context)

    def execute(self, context):
        scene = context.scene
        self.objs = resort_objects(context, context.objects_in_mode)
        for obj in self.objs:
            self.uv_copy_dict = dict()
            me, bm = get_mesh_data(obj)
            bm.faces.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.verify()
            if self.st_store_mode == "ISLAND":
                islands_for_process = island_util.get_island(context, bm, uv_layer)
            else:
                islands_for_process = island_util.get_selected_faces(context, bm)
            self.uv_copy_dict.update({obj.name: [face.index for island in islands_for_process for face in island]})
            # uv_copy_dict[obj.name] = [loop.index for island in islands_for_process for f in island for loop in f.loops]
        total = sum([len(faces) for name, faces in self.uv_copy_dict.items()])
        if total:
            # store loops in scene data
            scene["ZUV_Stored_UV"] = self.uv_copy_dict
            self.report({"INFO"}, "Island data stored")
            return {"FINISHED"}
        else:
            self.check_copy_conditions(scene)
            return {"CANCELLED"}

    def check_copy_conditions(self, scene):
        if scene.get("ZUV_Stored_UV", None):
            del scene["ZUV_Stored_UV"]
        self.report({"WARNING"}, "Select an island first")


class ZUV_OT_UV_Paste(bpy.types.Operator):
    ''' Paste selected Island to stored position '''
    bl_idname = "uv.zenuv_paste_uv"
    bl_label = ZuvLabels.OT_UV_PASTE_LABEL
    bl_description = ZuvLabels.OT_UV_PASTE_DESC
    bl_options = {'REGISTER', 'UNDO'}

    st_fit_mode: EnumProperty(
        name=ZuvLabels.PREF_OT_PASTE_MATCH_LABEL,
        description=ZuvLabels.PREF_OT_PASTE_MATCH_DESC,
        items=[
            (
                "tc",
                ZuvLabels.PREF_OT_PASTE_MATCH_HOR_LABEL,
                ZuvLabels.PREF_OT_PASTE_MATCH_HOR_DESC
            ),
            (
                "lc",
                ZuvLabels.PREF_OT_PASTE_MATCH_VERT_LABEL,
                ZuvLabels.PREF_OT_PASTE_MATCH_VERT_LABEL
            ),
        ],
        default="tc"
    )
    st_store_mode: EnumProperty(
        name=ZuvLabels.PREF_OT_PASTE_TYPE_LABEL,
        description=ZuvLabels.PREF_OT_PASTE_TYPE_DESC,
        items=[
            (
                "ISLAND",
                ZuvLabels.PREF_OT_PASTE_TYPE_ISLAND_LABEL,
                ZuvLabels.PREF_OT_PASTE_TYPE_ISLAND_DESC
            ),
            (
                "FACES",
                ZuvLabels.PREF_OT_PASTE_TYPE_FACES_LABEL,
                ZuvLabels.PREF_OT_PASTE_TYPE_FACES_DESC
            ),
        ],
        default="ISLAND"
    )
    MatchMode: EnumProperty(
        name=ZuvLabels.PREF_OT_PASTE_MATCH_LABEL,
        description=ZuvLabels.PREF_OT_PASTE_MATCH_DESC,
        items=[
            (
                "TD",
                ZuvLabels.PREF_OT_PASTE_MATCH_TD_LABEL,
                ZuvLabels.PREF_OT_PASTE_MATCH_TD_DESC
            ),
            (
                "FIT",
                ZuvLabels.PREF_OT_PASTE_MATCH_FIT_LABEL,
                ZuvLabels.PREF_OT_PASTE_MATCH_FIT_DESC
            ),
            (
                "NOTHING",
                ZuvLabels.PREF_OT_PASTE_MATCH_NOTHING_LABEL,
                ZuvLabels.PREF_OT_PASTE_MATCH_NOTHING_DESC
            ),
        ],
        default="TD"
    )
    silent: BoolProperty(
        default=False,
        description="Show stacking report",
        options={'HIDDEN'}
    )
    TransferMode: EnumProperty(
        name=ZuvLabels.PREF_OT_PASTE_TRANS_MODE_LABEL,
        description=ZuvLabels.PREF_OT_PASTE_TRANS_MODE_DESC,
        items=[
            (
                "STACK",
                ZuvLabels.PREF_OT_PASTE_TRANS_MODE_STACK_LABEL,
                ZuvLabels.PREF_OT_PASTE_TRANS_MODE_STACK_DESC
            ),
            (
                "TRANSFER",
                ZuvLabels.PREF_OT_PASTE_TRANS_MODE_TRANS_LABEL,
                ZuvLabels.PREF_OT_PASTE_TRANS_MODE_TRANS_DESC
            ),
        ],
        default="STACK"
    )
    AreaMatch: BoolProperty(
        name=ZuvLabels.PREF_OT_AREA_MATCH_LABEL,
        default=True,
        description=ZuvLabels.PREF_OT_AREA_MATCH_DESC,
        options={'HIDDEN'}
    )
    move: BoolProperty(
        name=ZuvLabels.PREF_OT_PASTE_MOVE_LABEL,
        default=False,
        description=ZuvLabels.PREF_OT_PASTE_MOVE_DESC,
        options={'HIDDEN'}
    )
    master_data = None
    master = None
    # clusters = []
    objs = None

    def invoke(self, context, event):
        self.objs = resort_by_type_mesh(context)
        if not self.objs:
            return {"CANCELLED"}
        update_indexes(self.objs)
        self.master_data = context.scene.get("ZUV_Stored_UV").to_dict()
        return self.execute(context)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "st_store_mode")
        # layout.separator_spacer()
        layout.prop(self, "TransferMode")
        if self.TransferMode == 'TRANSFER':
            self.AreaMatch = True
            # layout.separator_spacer()
            box = layout.box()
            row = box.row(align=True)
            # row.alignment = 'RIGHT'
            col = row.column(align=True)
            col.prop(self, "move")
            col.prop(self, "MatchMode", text="")
            if self.MatchMode == 'FIT':
                row = col.row(align=True)
                # row.alignment = 'RIGHT'
                row.prop(self, "st_fit_mode", expand=True)
        if self.TransferMode == 'STACK':
            box = layout.box()
            box.prop(self, "AreaMatch")

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return (active_object is not None
                and active_object.type == 'MESH'
                and context.mode == 'EDIT_MESH'
                and context.scene.get("ZUV_Stored_UV", False)
                )

    def execute(self, context):
        if not StackSolver() and self.TransferMode == 'STACK':
            self.report(
                {'WARNING'},
                "Zen UV Library is not installed! Install Library for activate Stack mode"
            )
            self.TransferMode = 'TRANSFER'
        self.objs = resort_by_type_mesh(context)
        if self.st_store_mode == 'FACES':
            faces_mode = True
        else:
            faces_mode = False
        for master_obj_name, island in self.master_data.items():
            self.master = Cluster(context, master_obj_name, island)
            if not self.AreaMatch:
                self.master.sim_index = int(self.master.sim_index)
        clusters = []
        for obj in self.objs:
            me, bm = get_mesh_data(obj)
            bm.faces.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.verify()
            if self.st_store_mode == "ISLAND":
                islands_for_process = island_util.get_island(context, bm, uv_layer)
            else:
                islands_for_process = island_util.get_selected_faces(context, bm)

            for island in islands_for_process:
                # if island:
                cluster = Cluster(context, obj, island)
                if not self.AreaMatch:
                    cluster.sim_index = int(cluster.sim_index)
                clusters.append(cluster)
        for cl in clusters:
            cl.mode = faces_mode
            cl.remap(
                self.master,
                transfer_params=self.TransferMode == "TRANSFER",
                match_position=self.move,
                match_mode=self.MatchMode,
                st_fit_mode=self.st_fit_mode
            )
            cl.update_mesh()
        context.scene["ZUV_Stored_UV"] = self.master_data
        # del self.master
        return {"FINISHED"}


if __name__ == '__main__':
    pass
