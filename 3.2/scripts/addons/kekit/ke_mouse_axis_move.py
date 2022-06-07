import bpy
from mathutils import Vector, Matrix
from bpy_extras.view3d_utils import region_2d_to_location_3d
from .ke_utils import getset_transform, restore_transform, average_vector


class VIEW3D_OT_ke_mouse_axis_move(bpy.types.Operator):
    bl_idname = "view3d.ke_mouse_axis_move"
    bl_label = "Mouse Axis Move"
    bl_description = "Runs Grab with Axis auto-locked based on your mouse movement (or viewport when rot) using recalculated orientation " \
                     "based on the selected Orientation type."
    bl_options = {'REGISTER', 'UNDO'}

    mode: bpy.props.EnumProperty(
        items=[("MOVE", "Move", "", 1),
               ("DUPE", "Duplicate", "", 2),
               ("ROT", "Rotate", "", 3),
               ("SCL", "Resize", "", 4),
               ("CURSOR", "Cursor", "", 5)
               ],
        name="Mode",
        default="MOVE")

    mouse_pos = Vector((0, 0))
    startpos = Vector((0, 0, 0))
    tm = Matrix().to_3x3()
    rv = None
    ot = "GLOBAL"
    obj = None
    obj_loc = None
    em_types = {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'HAIR', 'GPENCIL'}
    em_normal_mode = False
    pe_use = False
    pe_proj = False
    pe_connected = False
    pe_falloff = "SMOOTH"
    is_editor2d = False

    @classmethod
    def description(cls, context, properties):
        if properties.mode == "DUPE":
            return "Duplicates mesh/object before running Mouse Axis Move"
        elif properties.mode == "CURSOR":
            return "Mouse Axis Move for the Cursor. Global orientation or Cursor orientation (used in all modes except Global)"
        else:
            return "Runs Grab, Rotate or Resize with Axis auto-locked based on your mouse movement (or viewport when Rot) " \
                   "using recalculated orientation based on the selected Orientation type.\n" \
                   "Can also be used in 2D editors (UV, Nodes)"

    @classmethod
    def get_mpos(cls, context, coord, pos):
        region = context.region
        rv3d = context.region_data
        return region_2d_to_location_3d(region, rv3d, coord, pos)

    def invoke(self, context, event):
        # mouse track start
        self.mouse_pos[0] = int(event.mouse_region_x)
        self.mouse_pos[1] = int(event.mouse_region_y)

        # Proportional Edit Support
        self.pe_use = context.scene.tool_settings.use_proportional_edit
        self.pe_connected = context.scene.tool_settings.use_proportional_connected
        self.pe_proj = context.scene.tool_settings.use_proportional_projected
        self.pe_falloff = context.scene.tool_settings.proportional_edit_falloff

        if context.space_data.type in {"IMAGE_EDITOR", "NODE_EDITOR"}:
            self.is_editor2d = True
            if self.mode == "ROT":
                self.ot = "VIEW"
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}

        sel_obj = [o for o in context.selected_objects]

        if not sel_obj and context.object:
            sel_obj = [context.object]

        if sel_obj:
            self.obj = sel_obj[0]

            if len(sel_obj) > 1:
                self.obj_loc = average_vector([o.location for o in sel_obj])
            else:
                self.obj_loc = sel_obj[0].location

        if not self.obj:
            self.report({"INFO"}, " No valid objects selected ")
            return {'CANCELLED'}


        context.view_layer.objects.active = self.obj

        # Mouse vec start ( lazy edit mode overwrite later)
        if self.mode != "ROT":
            self.startpos = self.get_mpos(context, self.mouse_pos, self.obj_loc)

        # get rotation vectors
        og = getset_transform(setglobal=False)
        self.ot = og[0]

        if self.mode == "CURSOR":
            if og[0] == "GLOBAL":
                pass
            else:
                og[0] = "CURSOR"
                self.tm = context.scene.cursor.matrix.to_3x3()

        else:
            is_em = False
            if self.obj.type == "GPENCIL":
                is_em = bool(self.obj.data.use_stroke_edit_mode)
            else:
                if self.obj.type in self.em_types:
                    is_em = bool(self.obj.data.is_editmode)

            # check type
            if is_em:
                em = True
            else:
                em = "OBJECT"

            if og[0] == "GLOBAL":
                pass

            elif og[0] == "CURSOR":
                self.tm = context.scene.cursor.matrix.to_3x3()

            elif og[0] == "LOCAL" or og[0] == "NORMAL" and not em:
                self.tm = self.obj.matrix_world.to_3x3()

            elif og[0] == "VIEW":
                self.tm = context.space_data.region_3d.view_matrix.inverted().to_3x3()

            elif og[0] == "GIMBAL":
                self.report({"INFO"}, "Gimbal Orientation not supported")
                return {'CANCELLED'}

            # NORMAL / SELECTION
            elif em != "OBJECT":
                self.obj.update_from_editmode()
                sel = [v for v in self.obj.data.vertices if v.select]
                sel_co = average_vector([self.obj.matrix_world @ v.co for v in sel])
                # Use selection for mouse start 2d pos instead of obj loc
                self.startpos = self.get_mpos(context, self.mouse_pos, sel_co)

                if sel:
                    try:
                        bpy.ops.transform.create_orientation(name='keTF', use_view=False, use=True, overwrite=True)
                        self.tm = context.scene.transform_orientation_slots[0].custom_orientation.matrix.copy()
                        bpy.ops.transform.delete_orientation()
                        restore_transform(og)
                        # if og[1] == "ACTIVE_ELEMENT":
                        self.em_normal_mode = True

                    except RuntimeError:
                        print("Fallback: Invalid selection for Orientation - Using Local")
                        # Normal O. with a entire cube selected will fail create_o.
                        bpy.ops.transform.select_orientation(orientation='LOCAL')
                        self.tm = self.obj.matrix_world.to_3x3()
                else:
                    self.report({"INFO"}, " No elements selected ")
                    return {'CANCELLED'}
            else:
                self.report({"INFO"}, "Unsupported Orientation Mode")
                return {'CANCELLED'}


            if self.mode == "DUPE":
                if context.mode != "OBJECT" and self.obj.type == "CURVE":
                    bpy.ops.curve.duplicate('INVOKE_DEFAULT')
                elif em != "OBJECT":
                    bpy.ops.mesh.duplicate('INVOKE_DEFAULT')
                else:
                    if bpy.context.scene.kekit.tt_linkdupe:
                        bpy.ops.object.duplicate('INVOKE_DEFAULT', linked=True)
                    else:
                        bpy.ops.object.duplicate('INVOKE_DEFAULT', linked=False)

        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):

        if event.type == 'MOUSEMOVE':
            # mouse track end candidate
            new_mouse_pos = Vector((int(event.mouse_region_x), int(event.mouse_region_y)))
            t1 = abs(new_mouse_pos[0] - self.mouse_pos[0])
            t2 = abs(new_mouse_pos[1] - self.mouse_pos[1])

            if t1 > 10 or t2 > 10 or self.mode == "ROT":

                if self.is_editor2d:
                    if t1 > 10:
                        axis = True, False, False
                        oa = "Z"
                    else:
                        axis = False, True, False
                        oa = "Z"
                    if self.mode == "ROT":
                        axis = False, False, False
                else:
                    if self.mode == "ROT":
                        # no need to track mouse vec
                        rm = context.space_data.region_3d.view_matrix
                        v = self.tm.inverted() @ Vector(rm[2]).to_3d()
                        x, y, z = abs(v[0]), abs(v[1]), abs(v[2])

                    else:
                        # mouse vec end
                        newpos = self.get_mpos(context, new_mouse_pos, self.obj_loc)
                        v = self.tm.inverted() @ Vector(self.startpos - newpos).normalized()
                        x, y, z = abs(v[0]), abs(v[1]), abs(v[2])

                    if x > y and x > z:
                        axis = True, False, False
                        oa = "X"
                    elif y > x and y > z:
                        axis = False, True, False
                        oa = "Y"
                    else:
                        axis = False, False, True
                        oa = "Z"

                if self.mode == "ROT":
                    bpy.ops.transform.rotate('INVOKE_DEFAULT', orient_axis=oa, orient_type=self.ot,
                                             orient_matrix=self.tm, orient_matrix_type=self.ot,
                                             constraint_axis=axis, mirror=True,
                                             use_proportional_edit=self.pe_use,
                                             proportional_edit_falloff=self.pe_falloff,
                                             use_proportional_connected=self.pe_connected,
                                             use_proportional_projected=self.pe_proj)
                elif self.mode == "SCL":
                    bpy.ops.transform.resize('INVOKE_DEFAULT', orient_type=self.ot,
                                             orient_matrix=self.tm, orient_matrix_type=self.ot,
                                             constraint_axis=axis, mirror=True,
                                             use_proportional_edit=self.pe_use,
                                             proportional_edit_falloff=self.pe_falloff,
                                             use_proportional_connected=self.pe_connected,
                                             use_proportional_projected=self.pe_proj)

                elif self.mode == "CURSOR":
                    bpy.ops.transform.translate('INVOKE_DEFAULT', orient_type=self.ot, orient_matrix_type=self.ot,
                                                constraint_axis=axis, mirror=True,
                                                use_proportional_edit=self.pe_use,
                                                proportional_edit_falloff=self.pe_falloff,
                                                use_proportional_connected=self.pe_connected,
                                                use_proportional_projected=self.pe_proj)
                else:
                    if self.em_normal_mode:
                        axis = False, False, True
                    bpy.ops.transform.translate('INVOKE_DEFAULT', orient_type=self.ot, orient_matrix_type=self.ot,
                                                constraint_axis=axis, mirror=True,
                                                use_proportional_edit=self.pe_use,
                                                proportional_edit_falloff=self.pe_falloff,
                                                use_proportional_connected=self.pe_connected,
                                                use_proportional_projected=self.pe_proj)

                return {'FINISHED'}

        elif event.type == 'ESC':
            # Justincase
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}


# -------------------------------------------------------------------------------------------------
# Class Registration & Unregistration
# -------------------------------------------------------------------------------------------------
def register():
    bpy.utils.register_class(VIEW3D_OT_ke_mouse_axis_move)


def unregister():
    bpy.utils.unregister_class(VIEW3D_OT_ke_mouse_axis_move)


if __name__ == "__main__":
    register()
