import bpy
from bpy.props import StringProperty
from bpy.types import Operator

class PHOTOGRAPHER_OT_ButtonStringClear(Operator):
    bl_idname = "photographer.button_string_clear"
    bl_label = "Clear string name search"

    prop : StringProperty()

    def execute(self, context):
        settings = context.scene.photographer
        if settings.get(self.prop,False):
            settings[self.prop] = ""
            return{'FINISHED'}