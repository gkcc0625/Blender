import bpy
from bpy.types import Header, Panel, Operator
from bpy.props import EnumProperty
from mathutils import Vector, Matrix
from math import radians
from ._utils import rotation_from_vector
from ._prefs import pcoll


class VIEW3D_HT_KCM(Header):
    bl_region_type = 'HEADER'
    bl_space_type = 'VIEW_3D'
    bl_label = "keKit Cursor Menu"

    def draw(self, context):
        layout = self.layout
        layout.popover(panel="VIEW3D_PT_KCM", icon="CURSOR", text="")


class VIEW3D_PT_KCM(Panel):
    bl_region_type = 'HEADER'
    bl_space_type = 'VIEW_3D'
    bl_label = "KCM"

    def draw(self, context):
        bookmarks = bool(bpy.context.preferences.addons[__package__].preferences.m_bookmarks)
        k = context.scene.kekit_temp
        layout = self.layout
        c = layout.column()

        c.operator("view3d.ke_cursor_rotation", text="Align Cursor To View").mode = "VIEW"

        c.label(text="Step Rotate")
        col = c.column(align=True)
        row = col.row(align=True)
        row.prop(k, "kcm_axis", expand=True)

        row = col.row(align=True)
        row.prop(k, "kcm_rot_preset", expand=True)
        row = col.row(align=True)
        row.prop(k, "kcm_custom_rot")
        row = col.row(align=True)
        row.operator("view3d.ke_cursor_rotation", text="Step Rotate").mode = "STEP"

        c.label(text="Target Object")
        c.prop_search(context.scene, "kekit_cursor_obj", bpy.data, "objects", text="")
        row = c.row(align=True)
        row.operator("view3d.ke_cursor_rotation", text="Point To Obj").mode = "OBJECT"
        row.operator("view3d.ke_cursor_rotation", text="Copy Obj Rot").mode = "MATCH"

        c.label(text="Snap Cursor To")
        col = c.column(align=True)
        row = col.row(align=True)
        row.operator("view3d.snap_cursor_to_selected", text="Selected")
        row.operator("view3d.snap_cursor_to_active", text="Active")
        row.operator("view3d.snap_cursor_to_grid", text="Grid")

        if bookmarks:
            c.label(text="Cursor Bookmarks")
            row = c.grid_flow(row_major=True, columns=6, align=True)
            row.operator('view3d.ke_cursor_bookmark', text="", icon="IMPORT").mode = "SET1"
            row.operator('view3d.ke_cursor_bookmark', text="", icon="IMPORT").mode = "SET2"
            row.operator('view3d.ke_cursor_bookmark', text="", icon="IMPORT").mode = "SET3"
            row.operator('view3d.ke_cursor_bookmark', text="", icon="IMPORT").mode = "SET4"
            row.operator('view3d.ke_cursor_bookmark', text="", icon="IMPORT").mode = "SET5"
            row.operator('view3d.ke_cursor_bookmark', text="", icon="IMPORT").mode = "SET6"

            if sum(k.cursorslot1) == 0:
                row.operator('view3d.ke_cursor_bookmark', text="1", depress=False).mode = "USE1"
            else:
                row.operator('view3d.ke_cursor_bookmark', text="1", depress=True).mode = "USE1"
            if sum(k.cursorslot2) == 0:
                row.operator('view3d.ke_cursor_bookmark', text="2", depress=False).mode = "USE2"
            else:
                row.operator('view3d.ke_cursor_bookmark', text="2", depress=True).mode = "USE2"
            if sum(k.cursorslot3) == 0:
                row.operator('view3d.ke_cursor_bookmark', text="3", depress=False).mode = "USE3"
            else:
                row.operator('view3d.ke_cursor_bookmark', text="3", depress=True).mode = "USE3"
            if sum(k.cursorslot4) == 0:
                row.operator('view3d.ke_cursor_bookmark', text="4", depress=False).mode = "USE4"
            else:
                row.operator('view3d.ke_cursor_bookmark', text="4", depress=True).mode = "USE4"
            if sum(k.cursorslot5) == 0:
                row.operator('view3d.ke_cursor_bookmark', text="5", depress=False).mode = "USE5"
            else:
                row.operator('view3d.ke_cursor_bookmark', text="5", depress=True).mode = "USE5"
            if sum(k.cursorslot6) == 0:
                row.operator('view3d.ke_cursor_bookmark', text="6", depress=False).mode = "USE6"
            else:
                row.operator('view3d.ke_cursor_bookmark', text="6", depress=True).mode = "USE6"

        cf = c.column_flow(columns=2, align=True)
        cf.prop(context.scene.cursor, "location", text="Cursor Location", expand=True)
        cf.operator("view3d.snap_cursor_to_center", text="Clear Loc")
        cf.prop(context.scene.cursor, "rotation_euler", text="Cursor Rotation", expand=True)
        cf.operator("view3d.ke_cursor_clear_rot", text="Clear Rot")
        c.operator("view3d.snap_cursor_to_center", text="Reset Cursor (Loc & Rot)")


class KeCursorRotation(Operator):
    bl_idname = "view3d.ke_cursor_rotation"
    bl_label = "Cursor Rotation"
    bl_options = {'REGISTER'}

    mode: EnumProperty(items=[
        ("STEP", "Step Rotate", "", 1),
        ("VIEW", "Align To View", "", 2),
        ("OBJECT", "Point To Object", "", 3),
        ("MATCH", "Match Object Rot", "", 4)],
        name="Mode", default="STEP", options={"HIDDEN"})

    @classmethod
    def poll(cls, context):
        return context.space_data.type == "VIEW_3D"

    @classmethod
    def description(cls, context, properties):
        if properties.mode == "STEP":
            return "Rotate the cursor along chosen AXIS with either PRESET -or- CUSTOM degrees"
        elif properties.mode == "VIEW":
            return "Aligns the cursor Z axis to the view camera"
        elif properties.mode == "OBJECT":
            return "Rotate the cursor Z towards chosen object"
        else:
            return "Cursor uses chosen object's rotation"

    def execute(self, context):
        obj = bpy.data.objects.get(context.scene.kekit_cursor_obj)
        cursor = context.scene.cursor
        qc = context.scene.cursor.matrix

        if self.mode == "VIEW":
            rv3d = context.space_data.region_3d
            cursor.rotation_euler = rv3d.view_rotation.to_euler()

        elif self.mode == "OBJECT":
            if obj:
                v = Vector(obj.location - cursor.location).normalized()
                if round(abs(v.dot(Vector((1, 0, 0)))), 3) == 1:
                    u = Vector((0, 0, 1))
                else:
                    u = Vector((-1, 0, 0))
                t = v.cross(u).normalized()
                rot_mtx = rotation_from_vector(v, t, rw=False)
                cursor.rotation_euler = rot_mtx.to_euler()

        elif self.mode == "MATCH":
            if obj:
                cursor.rotation_euler = obj.rotation_euler

        elif self.mode == "STEP":
            axis = context.scene.kekit_temp.kcm_axis
            custom_rot = context.scene.kekit_temp.kcm_custom_rot
            preset_rot = context.scene.kekit_temp.kcm_rot_preset
            if custom_rot != 0:
                rval = custom_rot
            else:
                rval = radians(int(preset_rot))
            rot_mtx = qc @ Matrix.Rotation(rval, 4, axis)
            cursor.rotation_euler = rot_mtx.to_euler()

        return {"FINISHED"}


classes = (
    VIEW3D_HT_KCM,
    VIEW3D_PT_KCM,
    KeCursorRotation,
)


def register():
    k = bpy.context.preferences.addons[__package__].preferences
    if k.m_selection:
        for c in classes:
            bpy.utils.register_class(c)

        if k.kcm:
            bpy.types.VIEW3D_MT_editor_menus.append(VIEW3D_HT_KCM.draw)


def unregister():
    if "bl_rna" in VIEW3D_HT_KCM.__dict__:
        bpy.types.VIEW3D_MT_editor_menus.remove(VIEW3D_HT_KCM.draw)

        for c in reversed(classes):
            bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()
