import bpy
from bpy.types import Panel, Operator
from . import ke_copyplus, ke_itemize, ke_mouse_mirror_flip, ke_lineararray, ke_radialarray
from ._prefs import pcoll


#
# MODULE UI
#
class UIDupeModule(Panel):
    bl_idname = "UI_PT_M_DUPE"
    bl_label = "Duplication"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    # bl_category = __package__
    bl_parent_id = "UI_PT_kekit"
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        k = context.scene.kekit
        u = pcoll['kekit']['ke_uncheck'].icon_id
        layout = self.layout
        layout = layout.column(align=True)
        row = layout.row(align=True)
        row.operator('view3d.ke_copyplus', text="Cut+").mode = "CUT"
        row.operator('view3d.ke_copyplus', text="Copy+").mode = "COPY"
        row.operator('view3d.ke_copyplus', text="Paste+").mode = "PASTE"
        # row.separator()
        if k.paste_merge:
            row.prop(k, "paste_merge", text="", toggle=True, icon="CHECKMARK")
        else:
            row.prop(k, "paste_merge", text="", toggle=True, icon_value=u)

        row = layout.row(align=True)
        row.operator('mesh.ke_extract_and_edit', text="Extract&Edit").copy = False
        row.operator('mesh.ke_extract_and_edit', text="E&E Copy").copy = True
        row = layout.row(align=True)
        row.operator('mesh.ke_itemize', text="Itemize").mode = "DEFAULT"
        row.operator('mesh.ke_itemize', text="DupeItemize").mode = "DUPE"

        row = layout.row(align=True)
        row.operator('view3d.ke_mouse_mirror_flip', icon="MOUSE_MOVE", text="MouseMirror").mode = "MIRROR"
        row.operator('view3d.ke_mouse_mirror_flip', icon="MOUSE_MOVE", text="MouseFlip").mode = "FLIP"

        row = layout.row(align=True)
        row.operator("view3d.ke_lineararray")
        row.operator("view3d.ke_radialarray")
        row2 = row.row(align=True)
        row2.alignment = "RIGHT"
        if k.ra_autoarrange:
            row2.prop(context.scene.kekit, "ra_autoarrange", text="", toggle=True, icon="CHECKMARK")
        else:
            row2.prop(context.scene.kekit, "ra_autoarrange", text="", toggle=True, icon_value=u)


#
# MODULE OPERATORS (MISC)
#
class KeExtractAndEdit(Operator):
    bl_idname = "mesh.ke_extract_and_edit"
    bl_label = "Extract & Edit"
    bl_description = "Separate element selection into a New Object & set as Active Object in Edit Mode"
    bl_options = {'REGISTER', 'UNDO'}

    copy: bpy.props.BoolProperty(default=False, options={"HIDDEN"})

    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.object.type == 'MESH' and
                context.object.data.is_editmode)

    def execute(self, context):
        sel_obj = [o for o in context.selected_objects if o.type == "MESH"]

        if not len(sel_obj):
            self.report({'INFO'}, "Selection Error: No valid/active object(s) selected?")
            return {"CANCELLED"}

        if self.copy:
            bpy.ops.mesh.duplicate(mode=1)

        bpy.ops.mesh.separate(type="SELECTED")
        new_obj = [o for o in context.selected_objects if o.type == 'MESH'][-1]

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action="DESELECT")
        new_obj.select_set(True)

        view_layer = bpy.context.view_layer
        view_layer.objects.active = new_obj

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action="SELECT")
        return {'FINISHED'}


#
# MODULE REGISTRATION
#
classes = (
    UIDupeModule,
    KeExtractAndEdit,
)

modules = (
    ke_copyplus,
    ke_itemize,
    ke_mouse_mirror_flip,
    ke_lineararray,
    ke_radialarray
)


def register():
    if bpy.context.preferences.addons[__package__].preferences.m_dupe:
        for c in classes:
            bpy.utils.register_class(c)

        for m in modules:
            m.register()


def unregister():
    if "bl_rna" in UIDupeModule.__dict__:
        for c in reversed(classes):
            bpy.utils.unregister_class(c)

        for m in modules:
            m.unregister()


if __name__ == "__main__":
    register()
