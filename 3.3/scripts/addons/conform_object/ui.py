import bpy
from bpy.types import Panel, UIList
from bpy.utils import register_class, unregister_class

class CONFORMOBJECT_PT_GeneralPanel(bpy.types.Panel):
    """Conform Object Panel"""
    bl_idname = "CONFORMOBJECT_PT_GeneralPanel"
    bl_label = "Conform"
    bl_category = "Conform"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    # bl_parent_id = 'MESHMATERIALIZER_PT_Panel'

    def draw(self, context):
        layout = self.layout
        layout.label(text="Conform, dammit")
        col = layout.column()
        # col.operator("conform_object.conform").redo_conform = False
        col.operator("conform_object.conform")
        col.operator("conform_object.conform_undo")



classes = [
    #CONFORMOBJECT_PT_GeneralPanel
    ]


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in classes:
        unregister_class(cls)
