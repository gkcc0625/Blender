import bpy
from .. import utils


class UpdatePreset(bpy.types.Operator):
    bl_idname = 'powermanage.update_preset'
    bl_label = 'Update Preset'
    bl_description = 'Update the selected preset'
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        prefs = utils.meta.prefs()
        return prefs.selected_preset()

    def execute(self, context: bpy.types.Context) -> set:
        prefs = utils.meta.prefs()

        preset = prefs.selected_preset()
        utils.preset.save_preset(self, preset)

        utils.meta.save_userpref()
        return {'FINISHED'}
