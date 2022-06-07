import bpy
from mathutils import Vector, Matrix


class VIEW3D_OT_KE_TT(bpy.types.Operator):
    bl_idname = "view3d.ke_tt"
    bl_label = "Transform Tool Toggle"
    bl_options = {'REGISTER'}

    mode: bpy.props.EnumProperty(
        items=[("TOGGLE_MOVE", "TT Move Mode", "", "TOGGLE_MOVE", 1),
               ("TOGGLE_ROTATE", "TT Rotate Mode", "", "TOGGLE_ROTATE", 2),
               ("TOGGLE_SCALE", "TT Scale Mode", "", "TOGGLE_SCALE", 3),
               ("TOGGLE_CYCLE", "TT Cycle Modes", "", "TOGGLE_CYCLE", 4),
               ("MOVE", "TT Move", "", "MOVE", 5),
               ("ROTATE", "TT Rotate", "", "ROTATE", 6),
               ("SCALE", "TT Scale", "", "SCALE", 7),
               ("DUPE", "TT Dupe", "", "DUPE", 8),
               ("TOGGLE_DUPE", "TT Dupe Mode", "", "TOGGLE_DUPE", 9),
               ("F_DUPE", "TT Dupe Forced", "", "F_DUPE", 10),
               ("F_LINKDUPE", "TT LinkDupe Forced", "", "F_LINKDUPE", 11)
               ],
        name="Level Mode",
        options={'HIDDEN'},
        default="TOGGLE_MOVE")

    @classmethod
    def description(cls, context, properties):
        if properties.mode == "MOVE":
            return "TT Move - can be toggled between using Default Transform Tools / MouseAxis / Viewplane\n" \
                   "Can also be used in 2D editors (UV, Nodes)"
        elif properties.mode == "ROTATE":
            return "TT Rotate - can be toggled between using Default Transform Tools / MouseAxis / Viewplane\n" \
                   "Can also be used in 2D editors (UV, Nodes)"
        elif properties.mode == "ROTATE":
            return "TT Scale - can be toggled between using Default Transform Tools / MouseAxis / Viewplane\n" \
                   "Can also be used in 2D editors (UV, Nodes)"
        elif properties.mode == "TOGGLE_DUPE":
            return "TT Linked Dupe Toggle - Duplicate Linked or not using TT Dupe\n" \
                   "Also used by MouseAxis Dupe & VPtransform Dupe"
        elif properties.mode == "F_DUPE":
            return "TT Dupe Forced - Overrides Toggle value -> Unlinked duplication"
        elif properties.mode == "F_LINKDUPE":
            return "TT Linked Dupe Forced - Overrides Toggle value -> Linked duplication"
        else:
            return "Toggles TT Move/Rotate/Scale between using Default Transform / MouseAxis / Viewplane\n" \
                   "Note: Preferred default state can be set by saving kit settings\n" \
                   "Icons visibility: keKit/Context Tools/TT Toggle/Hide Icons"

    def execute(self, context):
        tt_handles = bpy.context.scene.kekit.tt_handles
        tt_mode = bpy.context.scene.kekit.tt_mode
        tt_linkdupe = bpy.context.scene.kekit.tt_linkdupe

        # Forcing modes overrides
        if self.mode == "F_DUPE":
            self.mode = "DUPE"
            tt_linkdupe = False
            bpy.context.scene.kekit.tt_linkdupe = False
        elif self.mode == "F_LINKDUPE":
            self.mode = "DUPE"
            tt_linkdupe = True
            bpy.context.scene.kekit.tt_linkdupe = True

        if context.space_data.type in {"IMAGE_EDITOR", "NODE_EDITOR"}:
            if tt_mode[2]:
                tt_mode = (False, True, False)

        if self.mode == "MOVE":
            if tt_mode[0]:
                if tt_handles:
                    bpy.ops.wm.tool_set_by_id(name="builtin.move")
                else:
                    bpy.ops.transform.translate('INVOKE_DEFAULT')
            elif tt_mode[1]:
                bpy.ops.view3d.ke_mouse_axis_move('INVOKE_DEFAULT', mode='MOVE')
            elif tt_mode[2]:
                bpy.ops.view3d.ke_vptransform('INVOKE_DEFAULT', transform='TRANSLATE')

        elif self.mode == "ROTATE":
            if tt_mode[0]:
                if tt_handles:
                    bpy.ops.wm.tool_set_by_id(name="builtin.rotate")
                else:
                    bpy.ops.transform.rotate('INVOKE_DEFAULT')
            elif tt_mode[1]:
                bpy.ops.view3d.ke_mouse_axis_move('INVOKE_DEFAULT', mode='ROT')
            elif tt_mode[2]:
                bpy.ops.view3d.ke_vptransform('INVOKE_DEFAULT', transform='ROTATE')

        elif self.mode == "SCALE":

            if tt_mode[0]:
                if tt_handles:
                    bpy.ops.wm.tool_set_by_id(name="builtin.scale")
                else:
                    bpy.ops.transform.resize('INVOKE_DEFAULT')

            elif tt_mode[1]:
                if not context.scene.kekit.mam_scl:
                    bpy.ops.transform.resize('INVOKE_DEFAULT')
                else:
                    bpy.ops.view3d.ke_mouse_axis_move('INVOKE_DEFAULT', mode='SCL')

            elif tt_mode[2]:
                bpy.ops.view3d.ke_vptransform('INVOKE_DEFAULT', transform='RESIZE')

        elif self.mode == "DUPE":
            if tt_mode[0]:
                if context.mode == 'EDIT_MESH' and context.object.type == 'MESH':
                    bpy.ops.mesh.duplicate_move('INVOKE_DEFAULT')
                elif context.mode != "OBJECT" and context.object:
                    if context.object.type == "CURVE":
                        bpy.ops.curve.duplicate('INVOKE_DEFAULT')
                else:
                    if tt_linkdupe:
                        bpy.ops.object.duplicate_move_linked('INVOKE_DEFAULT', OBJECT_OT_duplicate={"linked":True, "mode":'TRANSLATION'})
                    else:
                        bpy.ops.object.duplicate_move('INVOKE_DEFAULT', OBJECT_OT_duplicate={"linked": False, "mode": 'TRANSLATION'})
            elif tt_mode[1]:
                bpy.ops.view3d.ke_mouse_axis_move('INVOKE_DEFAULT', mode='DUPE')
            elif tt_mode[2]:
                bpy.ops.view3d.ke_vptransform('INVOKE_DEFAULT', transform='COPYGRAB')

        elif self.mode == "TOGGLE_DUPE":
            bpy.context.scene.kekit.tt_linkdupe = not tt_linkdupe
            context.area.tag_redraw()
            return {"FINISHED"}

        elif self.mode == "TOGGLE_CYCLE":
            if tt_mode[0]:
                tt_mode[0], tt_mode[1], tt_mode[2] = False, True, False
            elif tt_mode[1]:
                tt_mode[0], tt_mode[1], tt_mode[2] = False, False, True
            else:
                tt_mode[0], tt_mode[1], tt_mode[2] = True, False, False

        # Note: These actually set the TT mode : not type...naming sux
        elif self.mode == "TOGGLE_MOVE":
            # tt_mode[0] = not tt_mode[0]
            tt_mode[0] = True
            if tt_mode[0]:
                tt_mode[1], tt_mode[2] = False, False

        elif self.mode == "TOGGLE_ROTATE":
            # tt_mode[1] = not tt_mode[1]
            tt_mode[1] = True
            if tt_mode[1]:
                tt_mode[0], tt_mode[2] = False, False

        elif self.mode == "TOGGLE_SCALE":
            # tt_mode[2] = not tt_mode[2]
            tt_mode[2] = True
            if tt_mode[2]:
                tt_mode[0], tt_mode[1] = False, False

        if not any(tt_mode):
            tt_mode[0], tt_mode[1], tt_mode[1] = True, False, False

        context.area.tag_redraw()

        if context.scene.kekit.tt_select:
            active = context.workspace.tools.from_space_view3d_mode(context.mode, create=False).idname
            builtins = ["builtin.move", "builtin.rotate", "builtin.scale"]
            if active in builtins and not tt_mode[0] or not tt_handles:
                bpy.ops.wm.tool_set_by_id(name="builtin.select")

        return {"FINISHED"}


class VIEW3D_HT_KE_TT(bpy.types.Header):
    bl_label = "Transform Toggle Menu"
    bl_region_type = 'HEADER'
    bl_space_type = 'VIEW_3D'

    def draw(self, context):
        layout = self.layout
        if not bpy.context.scene.kekit.tt_hide:
            tt_mode = bpy.context.scene.kekit.tt_mode
            tt_link = bpy.context.scene.kekit.tt_linkdupe

            row = layout.row(align=True)
            row.operator("view3d.ke_tt", text="", icon='OBJECT_ORIGIN', depress=tt_mode[0]).mode = "TOGGLE_MOVE"
            row.operator("view3d.ke_tt", text="", icon='EMPTY_AXIS', depress=tt_mode[1]).mode = "TOGGLE_ROTATE"
            row.operator("view3d.ke_tt", text="", icon='AXIS_SIDE', depress=tt_mode[2]).mode = "TOGGLE_SCALE"
            row.separator(factor=0.5)
            row.operator("view3d.ke_tt", text="", icon='LINKED', depress=tt_link).mode = "TOGGLE_DUPE"


class VIEW3D_OT_ke_vptransform(bpy.types.Operator):
    bl_idname = "view3d.ke_vptransform"
    bl_label = "VP-Transform"
    bl_description = "Runs Grab,Rotate or Scale with View Planes auto-locked based on your viewport rotation."
    bl_options = {'REGISTER'}

    transform: bpy.props.EnumProperty(
        items=[("TRANSLATE", "Translate", "", 1),
               ("ROTATE", "Rotate", "", 2),
               ("RESIZE", "Resize", "", 3),
               ("COPYGRAB", "Duplicate & Move", "", 4),
               ],
        name="Transform",
        default="ROTATE")

    world_only: bpy.props.BoolProperty(default=True)
    rot_got: bpy.props.BoolProperty(default=True)
    loc_got: bpy.props.BoolProperty(default=False)
    scl_got: bpy.props.BoolProperty(default=False)

    tm = None
    obj = None

    @classmethod
    def poll(cls, context):
        return context.selected_objects is not None

    def execute(self, context):

        sel_obj = [o for o in context.selected_objects]
        if not sel_obj:
            self.report({"INFO"}, " No objects selected ")
            return {'CANCELLED'}

        if sel_obj and context.object is None:
            self.obj = sel_obj[0]

        elif context.object is not None:
            self.obj = context.object
        else:
            self.report({"INFO"}, " No valid objects selected ")
            return {'CANCELLED'}

        context.view_layer.objects.active = self.obj

        self.world_only = bpy.context.scene.kekit.vptransform
        self.rot_got = bpy.context.scene.kekit.rot_got
        self.loc_got = bpy.context.scene.kekit.loc_got
        self.scl_got = bpy.context.scene.kekit.scl_got

        pe_use = context.scene.tool_settings.use_proportional_edit
        pe_connected = context.scene.tool_settings.use_proportional_connected
        pe_proj = context.scene.tool_settings.use_proportional_projected
        pe_falloff = context.scene.tool_settings.proportional_edit_falloff

        if self.world_only:
            # set Global
            bpy.ops.transform.select_orientation(orientation='GLOBAL')
            og_transform = "GLOBAL"
        else:
            # check current transform
            og_transform = str(context.scene.transform_orientation_slots[0].type)

        # Transform
        if og_transform == "GLOBAL":
            self.tm = Matrix.Identity(3)
        if og_transform == "CURSOR":
            self.tm = context.scene.cursor.matrix.to_3x3()

        elif og_transform == "LOCAL" or og_transform == "NORMAL":
            self.tm = self.obj.matrix_world.to_3x3()

        elif og_transform == "VIEW":
            self.tm = context.space_data.region_3d.view_matrix.inverted().to_3x3()

        elif og_transform == "GIMBAL":
            self.report({"INFO"}, "Gimbal Orientation not supported")
            return {'CANCELLED'}

        # Get Viewplane
        rm = context.space_data.region_3d.view_matrix
        if og_transform == "GLOBAL":
            v = Vector(rm[2])
        else:
            v = self.tm.inverted() @ Vector(rm[2]).to_3d()

        xz, xy, yz = Vector((0, 1, 0)), Vector((0, 0, 1)), Vector((1, 0, 0))
        dic = {(True, False, True): abs(xz.dot(v)), (True, True, False): abs(xy.dot(v)),
               (False, True, True): abs(yz.dot(v))}
        vplane = sorted(dic, key=dic.get)[-1]

        # Set Transforms
        if self.transform == 'TRANSLATE':
            if self.loc_got:
                if og_transform == "GLOBAL":
                    bpy.ops.transform.translate('INVOKE_DEFAULT', constraint_axis=vplane,
                                                use_proportional_edit=pe_use,
                                                proportional_edit_falloff=pe_falloff,
                                                use_proportional_connected=pe_connected,
                                                use_proportional_projected=pe_proj
                                                )
                else:
                    bpy.ops.wm.tool_set_by_id(name="builtin.move")
            else:
                bpy.ops.transform.translate('INVOKE_DEFAULT', constraint_axis=vplane,
                                            orient_matrix_type=og_transform, orient_type=og_transform,
                                            use_proportional_edit=pe_use,
                                            proportional_edit_falloff=pe_falloff,
                                            use_proportional_connected=pe_connected,
                                            use_proportional_projected=pe_proj
                                            )

        elif self.transform == 'ROTATE':
            if self.rot_got:
                if og_transform == "GLOBAL":
                    bpy.ops.transform.rotate('INVOKE_DEFAULT', constraint_axis=vplane,
                                             use_proportional_edit=pe_use,
                                             proportional_edit_falloff=pe_falloff,
                                             use_proportional_connected=pe_connected,
                                             use_proportional_projected=pe_proj
                                             )
                else:
                    bpy.ops.wm.tool_set_by_id(name="builtin.rotate")
            else:
                bpy.ops.transform.rotate('INVOKE_DEFAULT', constraint_axis=vplane,
                                         orient_matrix_type=og_transform, orient_type=og_transform,
                                         use_proportional_edit=pe_use,
                                         proportional_edit_falloff=pe_falloff,
                                         use_proportional_connected=pe_connected,
                                         use_proportional_projected=pe_proj
                                         )

        elif self.transform == 'RESIZE':
            if self.scl_got:
                if og_transform == "GLOBAL":
                    bpy.ops.transform.resize('INVOKE_DEFAULT', constraint_axis=vplane,
                                             use_proportional_edit=pe_use,
                                             proportional_edit_falloff=pe_falloff,
                                             use_proportional_connected=pe_connected,
                                             use_proportional_projected=pe_proj
                                             )
                else:
                    bpy.ops.wm.tool_set_by_id(name="builtin.scale")
            else:
                bpy.ops.transform.resize('INVOKE_DEFAULT', constraint_axis=vplane,
                                         orient_matrix_type=og_transform, orient_type=og_transform,
                                         use_proportional_edit=pe_use,
                                         proportional_edit_falloff=pe_falloff,
                                         use_proportional_connected=pe_connected,
                                         use_proportional_projected=pe_proj
                                         )

        # Copygrab
        elif self.transform == 'COPYGRAB':

            if context.mode == 'EDIT_MESH' and context.object.type == 'MESH':
                bpy.ops.mesh.duplicate('INVOKE_DEFAULT')
            elif context.mode != 'OBJECT' and self.obj.type == "CURVE":
                bpy.ops.curve.duplicate('INVOKE_DEFAULT')
            elif context.mode == 'OBJECT':
                if bpy.context.scene.kekit.tt_linkdupe:
                    bpy.ops.object.duplicate('INVOKE_DEFAULT', linked=True)
                else:
                    bpy.ops.object.duplicate('INVOKE_DEFAULT', linked=False)
            else:
                return {'CANCELLED'}
            bpy.ops.transform.translate('INVOKE_DEFAULT', constraint_axis=vplane,
                                        orient_matrix_type=og_transform, orient_type=og_transform)

        return {'FINISHED'}


classes = (VIEW3D_OT_KE_TT, VIEW3D_OT_ke_vptransform)


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.VIEW3D_HT_header.prepend(VIEW3D_HT_KE_TT.draw)


def unregister():
    bpy.types.VIEW3D_HT_header.remove(VIEW3D_HT_KE_TT.draw)
    for c in reversed(classes):
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()
