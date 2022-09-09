import bpy
from .. import utils


class NewPreset(bpy.types.Operator):
    bl_idname = 'powermanage.new_preset'
    bl_label = 'New Preset'
    bl_description = 'Save setup to a new preset'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context: bpy.types.Context) -> set:
        utils.preset.add_preset(self)

        utils.meta.save_userpref()
        return {'FINISHED'}
