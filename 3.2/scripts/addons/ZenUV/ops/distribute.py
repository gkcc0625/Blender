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


import bpy
import bmesh
from bpy.props import (
    EnumProperty,
    BoolProperty,
    FloatVectorProperty,
    FloatProperty
)
from mathutils import Vector
from ZenUV.utils.generic import (
    resort_objects,
    get_mesh_data,
    loops_by_sel_mode,
    edge_loops_from_uvs
)
from ZenUV.utils.transform import calc_length_of_loops
from ZenUV.utils import get_uv_islands as island_util
from ZenUV.stacks.utils import Cluster
from ZenUV.ui.labels import ZuvLabels


class ZUV_OT_Distribute(bpy.types.Operator):
    bl_idname = "uv.zenuv_distribute"
    bl_label = ZuvLabels.PROP_STRAIGHTEN_LABEL
    bl_description = ZuvLabels.PROP_DISTRIBUTE_DESC
    bl_options = {'REGISTER', 'UNDO'}

    start: EnumProperty(
        name=ZuvLabels.PROP_REV_START_LABEL,
        description=ZuvLabels.PROP_REV_START_DESC,
        items=[
            ("TOP_LEFT", "Top - Left", ""),
            ("BOTTOM_RIGHT", "Bottom - Right", "")
        ],
        default="TOP_LEFT"
    )
    align_to: EnumProperty(
        name=ZuvLabels.PROP_ALIGN_TO_LABEL,
        description=ZuvLabels.PROP_ALIGN_TO_DESC,
        items=[
            ("NONE", "None", ""),
            ("U", "U Axis", ""),
            ("V", "V Axis", ""),
            ("AUTO", "Auto", "")
        ],
        default="AUTO"
    )
    reverse_start: BoolProperty(
        name=ZuvLabels.PROP_REV_START_LABEL,
        description=ZuvLabels.PROP_REV_START_DESC,
        default=False
    )
    reverse_dir: BoolProperty(
        name=ZuvLabels.PROP_REV_DIR_LABEL,
        description=ZuvLabels.PROP_REV_DIR_DESC,
        default=False
    )
    relax_linked: BoolProperty(
        name=ZuvLabels.PROP_REL_LINK_LABEL,
        description=ZuvLabels.PROP_REL_LINK_DESC,
        default=False,
    )
    relax_mode: EnumProperty(
        name=ZuvLabels.PROP_REL_MODE_LABEL,
        description=ZuvLabels.PROP_REL_MODE_DESC,
        items=[
            ("ANGLE_BASED", "Angle Based", ""),
            ("CONFORMAL", "Conformal", ""),
        ]
    )
    desc: bpy.props.StringProperty(name="Description", default=ZuvLabels.PROP_STRAIGHTEN_DESC, options={'HIDDEN'})

    @classmethod
    def description(cls, context, properties):
        return properties.desc

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "start")
        layout.separator_spacer()
        row = layout.row(align=True)
        row.prop(self, "align_to")
        row.prop(self, "reverse_dir", icon_only=True, icon="ARROW_LEFTRIGHT")
        layout.separator_spacer()
        if context.space_data.type == 'IMAGE_EDITOR':
            row = layout.row(align=True)
            if self.desc == ZuvLabels.PROP_STRAIGHTEN_DESC:
                # row.prop(self, "relax_linked")
                pass
            else:
                self.relax_linked = False
            if self.relax_linked:
                row.prop(self, "relax_mode")

    def execute(self, context):

        objs = resort_objects(context, context.objects_in_mode)
        if not objs:
            return {"CANCELLED"}
        for obj in objs:
            me, bm = get_mesh_data(obj)
            uv_layer = bm.loops.layers.uv.verify()

            def align_auto():
                if abs(base_vec.dot(axis_u)) < abs(base_vec.dot(axis_v)):
                    return axis_v * base_vec
                else:
                    return axis_u * base_vec

            def align_inplace():
                return last_loop_co - first_loop_co

            def align_u():
                return Vector((1.0, 0.0)) * base_vec

            def align_v():
                return Vector((0.0, 1.0)) * base_vec

            loops = loops_by_sel_mode(context, bm)
            sorted_loops = edge_loops_from_uvs(list(loops), uv_layer)

            direction = Vector((0.0, 0.0))
            axis_u = Vector((1.0, 0.0))
            axis_v = Vector((0.0, 1.0))

            # Bring all stripes to Order
            r_sorted_loops = []
            for stripe in sorted_loops:
                first_loop_co = stripe[0][0][uv_layer].uv
                last_loop_co = stripe[-1][0][uv_layer].uv
                if last_loop_co.y > first_loop_co.y:
                    r_sorted_loops.append(self.reverse_stripe(stripe))
                else:
                    r_sorted_loops.append(stripe)
            sorted_loops = r_sorted_loops

            if self.start == "BOTTOM_RIGHT":
                r_sorted_loops = []
                for stripe in sorted_loops:
                    r_sorted_loops.append(self.reverse_stripe(stripe))
                sorted_loops = r_sorted_loops

            align_solver = {"NONE": align_inplace, "U": align_u, "V": align_v, "AUTO": align_auto}

            for stripe in sorted_loops:
                loop_stripe_length = calc_length_of_loops(uv_layer, stripe)
                first_loop_co = stripe.pop(0)[0][uv_layer].uv
                last_loop_co = stripe[-1][0][uv_layer].uv
                base_vec = (last_loop_co - first_loop_co).normalized()
                base_position = first_loop_co

                direction = align_solver[self.align_to]()
                if self.reverse_dir:
                    direction = direction * -1
                for loops, length in zip(stripe, loop_stripe_length):
                    co = base_position + direction.normalized() * length
                    for loop in loops:
                        loop[uv_layer].uv = co
                    base_position = co

            bmesh.update_edit_mesh(me, loop_triangles=False)

        if self.relax_linked:
            self._relax_linked(context)

        return {'FINISHED'}

    def reverse_stripe(self, stripe):
        # r_sorted_loops = []
        stripe = [loop for loop in reversed(stripe)]
        # r_sorted_loops.append(stripe)
        return stripe

    def _relax_linked(self, context):
        init_select_mode = context.tool_settings.mesh_select_mode[:]
        objs = list(context.objects_in_mode_unique_data)
        view_layer = context.view_layer
        active_obj = view_layer.objects.active

        bpy.ops.object.mode_set(mode='OBJECT')
        for obj in objs:
            obj.select_set(state=False)

        for obj in objs:
            view_layer.objects.active = obj
            obj.select_set(state=True)
            bpy.ops.object.mode_set(mode='EDIT')

            me = obj.data
            bm = bmesh.from_edit_mesh(me)
            uv_layer = bm.loops.layers.uv.verify()
            sync_uv = context.scene.tool_settings.use_uv_select_sync

            init_pins = []
            init_selection = set()

            sync_mode = context.space_data.type == 'IMAGE_EDITOR' and sync_uv
            loops = [loop for face in bm.faces for loop in face.loops]

            for face in bm.faces:
                for loop in face.loops:
                    if loop[uv_layer].pin_uv:
                        init_pins.append(loop[uv_layer])
                        loop[uv_layer].pin_uv = False
                    if not sync_mode and loop[uv_layer].select:
                        init_selection.add(loop)
                    if sync_mode and loop.vert.select:
                        init_selection.add(loop.vert)
                    loop[uv_layer].pin_uv = True
            bm.faces.ensure_lookup_table()

            islands = island_util.get_island(context, bm, uv_layer)
            if not sync_mode:
                for island in islands:
                    for face in island:
                        for loop in face.loops:
                            loop[uv_layer].pin_uv = loop[uv_layer].select
            else:
                for island in islands:
                    for face in island:
                        for loop in face.loops:
                            loop[uv_layer].pin_uv = loop.vert.select

            if not sync_mode:
                for island in islands:
                    for face in island:
                        for loop in face.loops:
                            loop[uv_layer].select = True
            else:
                for island in islands:
                    for face in island:
                        face.select = True

            bpy.ops.uv.unwrap(
                method=self.relax_mode,
                # fill_holes=self.fill_holes,
                # correct_aspect=self.correct_aspect,
                # ue_subsurf_data=self.use_subsurf_data,
                margin=0
            )

            for loop in loops:
                loop[uv_layer].pin_uv = False

            for loop in init_pins:
                loop.pin_uv = True

            # Restore Init Selection
            if not sync_mode:
                for loop in loops:
                    if loop not in init_selection:
                        loop[uv_layer].select = False
            else:
                context.tool_settings.mesh_select_mode = [True, False, False]
                bmesh.select_mode = {'VERT'}
                for v in bm.verts:
                    v.select = v in init_selection
                bm.select_flush_mode()

            bpy.ops.object.mode_set(mode='OBJECT')
            obj.select_set(state=False)

        for obj in objs:
            obj.select_set(state=True)
        view_layer.objects.active = active_obj
        bpy.ops.object.mode_set(mode='EDIT')
        context.tool_settings.mesh_select_mode = init_select_mode


class ZUV_OT_Distribute_Islands(bpy.types.Operator):
    bl_idname = "uv.zenuv_distribute_islands"
    bl_label = "Distribute"
    bl_description = "Distributes and sorts the selected islands."
    bl_options = {'REGISTER', 'UNDO'}

    from_where: FloatVectorProperty(
        name=ZuvLabels.PROP_FROM_WHERE_LABEL,
        description=ZuvLabels.PROP_FROM_WHERE_DESC,
        size=2,
        default=(0.0, 0.0),
        subtype='XYZ'
    )
    sort_to: EnumProperty(
        name=ZuvLabels.PROP_SORT_TO_LABEL,
        description=ZuvLabels.PROP_SORT_TO_DESC,
        items=[
            ("NONE", "None", ""),
            ("UVAREA", "UV Area", ""),
            ("MESHAREA", "Mesh Area", ""),
            ("TD", "Texel Density", ""),
            ("UVCOVERAGE", "UV Coverage", "")
        ],
        default="NONE"
    )
    reverse: BoolProperty(
        name=ZuvLabels.PROP_REV_SORT_LABEL,
        description=ZuvLabels.PROP_REV_SORT_DESC,
        default=False
    )
    margin: FloatProperty(
        name=ZuvLabels.PROP_SORT_MARGIN_LABEL,
        description=ZuvLabels.PROP_SORT_MARGIN_LABEL,
        min=0.0,
        default=0.005,
        precision=3
    )
    align_to: EnumProperty(
        name=ZuvLabels.PROP_SORT_ALIGN_TO_LABEL,
        description=ZuvLabels.PROP_SORT_ALIGN_TO_DESC,
        items=[
            ("INPLACE", "In Place", ""),
            ("BOTTOM", "Bottom", ""),
            ("CENTER", "Center", ""),
            ("TOP", "Top", "")
        ],
        default="BOTTOM"
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "from_where")
        layout.prop(self, "sort_to")
        row = layout.row()
        row.enabled = not self.sort_to == "NONE"
        row.prop(self, "reverse")
        layout.prop(self, "margin")
        layout.prop(self, "align_to")

    def execute(self, context):
        objs = resort_objects(context, context.objects_in_mode)
        if not objs:
            return {"CANCELLED"}
        area_data = dict()
        counter = 0
        for obj in objs:
            me, bm = get_mesh_data(obj)
            uv_layer = bm.loops.layers.uv.verify()
            bm.faces.ensure_lookup_table()
            islands = island_util.get_island(context, bm, uv_layer)
            for island in islands:
                cluster = Cluster(context, obj, island)
                if self.sort_to == "MESHAREA":
                    cluster_area = cluster.area
                elif self.sort_to == "UVAREA":
                    cluster_area = cluster.get_uv_area()
                elif self.sort_to == "NONE":
                    cluster_area = 1
                elif self.sort_to == "TD":
                    cluster_area = cluster.get_td()[0]
                elif self.sort_to == "UVCOVERAGE":
                    cluster_area = cluster.get_td()[1]

                if cluster_area not in area_data.keys():
                    area_data.update({cluster_area: {}})
                area_data[cluster_area].update(
                    {
                        counter:
                            {
                                "cluster": cluster.geometry["faces_ids"],
                                "bbox": cluster.bbox,
                                "area": cluster_area,
                                "object": obj.name
                            }
                    }
                )
                counter += 1

        # Abstract Sorting
        if self.sort_to == "MESHAREA":
            pass
        elif self.sort_to == "UVAREA":
            pass
        elif self.sort_to == "NONE":
            pass
        elif self.sort_to == "TD":
            pass
        position = self.from_where
        if self.align_to == "TOP":
            # position = Vector((0.0, 0.0))
            divider = - 2
            mult = 1
            mutator = 0
        elif self.align_to == "BOTTOM":
            # position = Vector((0.0, 0.0))
            divider = 2
            mult = 1
            mutator = 0
        elif self.align_to == "CENTER":
            # position = Vector((0.0, 0.0))
            divider = 1
            mult = 0
            mutator = 0
        elif self.align_to == "INPLACE":
            # position = Vector((0.0, 0.0))
            divider = 1
            mult = 0
            mutator = 1

        area_chart = sorted(area_data.keys(), reverse=not self.reverse)
        for area in area_chart:
            for counter in area_data[area].keys():
                cluster = area_data[area][counter]
                cl_position = position + Vector((cluster["bbox"]["len_x"]/2, mult * cluster["bbox"]["len_y"] / divider + (cluster["bbox"]["cen"][1] * mutator)))
                area_data[area][counter].update({"position": cl_position})
                position = position + Vector((cluster["bbox"]["len_x"], 0.0)) + Vector((self.margin, 0.0))

        # Set Cluster to position
        for area, data in area_data.items():
            for cluster in data.values():
                cl = Cluster(context, cluster['object'], cluster["cluster"])
                cl.move_to(cluster["position"])
                cl.update_mesh()

        return {'FINISHED'}


uv_distribute_classes = (
    ZUV_OT_Distribute,
    ZUV_OT_Distribute_Islands
)

if __name__ == '__main__':
    pass
