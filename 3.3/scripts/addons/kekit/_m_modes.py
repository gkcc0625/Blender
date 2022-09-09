import bpy
from bpy.types import Panel, Operator
from mathutils import Vector
from ._utils import mouse_raycast


#
# MODULE UI
#
class UIModesModule(Panel):
    bl_idname = "UI_PT_M_MODES"
    bl_label = "Modes"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    # bl_category = __package__
    bl_parent_id = "UI_PT_kekit"
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=False)
        row.alignment = "CENTER"
        row.operator('view3d.ke_selmode', text="", icon="VERTEXSEL").edit_mode = "VERT"
        row.operator('view3d.ke_selmode', text="", icon="EDGESEL").edit_mode = "EDGE"
        row.operator('view3d.ke_selmode', text="", icon="FACESEL").edit_mode = "FACE"
        row.operator('view3d.ke_selmode', text="", icon="OBJECT_DATAMODE").edit_mode = "OBJECT"
        row.operator('view3d.object_mode_pie_or_toggle', text="", icon="THREE_DOTS")
        row.prop(context.scene.kekit, "selmode_mouse", text="")
        row.operator('view3d.ke_spacetoggle', text="", icon="MOUSE_MOVE")


#
# MODULE OPERATORS (MISC)
#
class KeSelectionMode(Operator):
    bl_idname = "view3d.ke_selmode"
    bl_label = "Direct Element <-> Object Mode Switch"
    bl_description = "Sets Element Mode - Direct to selection mode, also from Object Mode'\n" \
                     "Legacy Feature - Needed for 'Mouse Over Element Select Mode"

    edit_mode: bpy.props.EnumProperty(
        items=[("VERT", "Vertex Edit Mode", "", 1),
               ("EDGE", "Edge Edit Mode", "", 2),
               ("FACE", "Face Edit Mode", "", 3),
               ("OBJECT", "Object Mode", "", 4)],
        name="Edit Mode",
        default="OBJECT")

    mouse_pos = [0, 0]

    @classmethod
    def description(cls, context, properties):
        if properties.edit_mode == "VERT":
            return "Direct to Vertex Element Mode in Edit Mode'\n" \
                   "Legacy Feature - Needed for 'Mouse Over Element Select Mode"
        elif properties.edit_mode == "EDGE":
            return "Direct to Edge Element Mode in Edit Mode'\n" \
                   "Legacy Feature - Needed for 'Mouse Over Element Select Mode"
        elif properties.edit_mode == "FACE":
            return "Direct to Face Element Mode in Edit Mode'\n" \
                   "Legacy Feature - Needed for 'Mouse Over Element Select Mode"
        elif properties.edit_mode == "OBJECT":
            return "Direct to Object Mode'\n" \
                   "Legacy Feature - Needed for 'Mouse Over Element Select Mode"
        else:
            return "Set Element Mode - Direct to selection mode from Object Mode'\n" \
                   "Legacy Feature - Needed for 'Mouse Over Element Select Mode"

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def invoke(self, context, event):
        self.mouse_pos[0] = event.mouse_region_x
        self.mouse_pos[1] = event.mouse_region_y
        return self.execute(context)

    def execute(self, context):
        mode = str(context.mode)
        has_componentmodes = {"MESH", "ARMATURE", "GPENCIL"}
        has_editmode_only = {"CURVE", "SURFACE", "LATTICE", "META", "HAIR", "FONT"}

        # Mouse Over select option
        if context.scene.kekit.selmode_mouse and context.space_data.type == "VIEW_3D":
            og_obj = context.object

            if mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")

            bpy.ops.view3d.select(extend=False, deselect=False, toggle=False, deselect_all=False, center=False,
                                  enumerate=False, object=False, location=self.mouse_pos)

            sel_obj = context.object

            if og_obj == sel_obj:
                if mode == "OBJECT" and sel_obj.type in (has_componentmodes | has_editmode_only):
                    bpy.ops.object.editmode_toggle()
                return {"FINISHED"}

            if mode != "OBJECT" and sel_obj.type in (has_componentmodes | has_editmode_only):
                bpy.ops.object.editmode_toggle()
            else:
                mode = "OBJECT"

        # Set selection mode
        if context.active_object is not None:
            obj = context.active_object
        else:
            obj = context.object

        if obj.type in has_componentmodes:

            if self.edit_mode != "OBJECT":

                if obj.type == "ARMATURE":
                    bpy.ops.object.posemode_toggle()

                elif obj.type == "GPENCIL":
                    if mode == "OBJECT":
                        bpy.ops.gpencil.editmode_toggle()
                    if self.edit_mode == "VERT":
                        context.scene.tool_settings.gpencil_selectmode_edit = 'POINT'
                    elif self.edit_mode == "EDGE":
                        context.scene.tool_settings.gpencil_selectmode_edit = 'STROKE'
                    elif self.edit_mode == "FACE":
                        obj.data.use_curve_edit = not obj.data.use_curve_edit
                else:
                    if mode == "OBJECT" or mode == "SCULPT":
                        bpy.ops.object.editmode_toggle()
                    bpy.ops.mesh.select_mode(type=self.edit_mode)
            else:
                if obj.type == "GPENCIL":
                    bpy.ops.gpencil.editmode_toggle()
                else:
                    bpy.ops.object.editmode_toggle()

        elif obj.type in has_editmode_only:
            bpy.ops.object.editmode_toggle()

        else:
            # print("Object does not have an Edit Mode")
            return {"CANCELLED"}

        return {"FINISHED"}


class KeSpaceToggle(Operator):
    bl_idname = "view3d.ke_spacetoggle"
    bl_label = "Space Toggle"
    bl_description = "Space Toggle: Toggle between Edit and Object modes on selected object\n" \
                     "when mouse pointer is over -nothing-"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'REGISTER'}

    mouse_pos = Vector((0, 0))

    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.object.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'HAIR', 'GPENCIL'})

    def invoke(self, context, event):
        self.mouse_pos[0] = event.mouse_region_x
        self.mouse_pos[1] = event.mouse_region_y
        return self.execute(context)

    def execute(self, context):
        sel_mode = str(bpy.context.mode)
        bpy.ops.object.mode_set(mode='OBJECT')
        obj, hit_wloc, hit_normal, face_index = mouse_raycast(context, self.mouse_pos)

        if not face_index:
            if sel_mode == "OBJECT":
                bpy.ops.object.mode_set(mode="EDIT")
            elif sel_mode == "EDIT_MESH":
                bpy.ops.object.mode_set(mode="OBJECT")

        return {'FINISHED'}


#
# MODULE REGISTRATION
#
classes = (
    UIModesModule,
    KeSpaceToggle,
    KeSelectionMode,
)

modules = ()


def register():
    if bpy.context.preferences.addons[__package__].preferences.m_modes:
        for c in classes:
            bpy.utils.register_class(c)


def unregister():
    if "bl_rna" in UIModesModule.__dict__:
        for c in reversed(classes):
            bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()
