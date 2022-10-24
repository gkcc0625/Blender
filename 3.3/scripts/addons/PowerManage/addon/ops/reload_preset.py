import bpy
from .. import utils


class ReloadPreset(bpy.types.Operator):
    bl_idname = 'powermanage.reload_preset'
    bl_label = 'Reload Preset'
    bl_description = 'Reload the selected preset'
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        prefs = utils.meta.prefs()
        return prefs.selected_preset()

    def execute(self, context: bpy.types.Context) -> set:
        prefs = utils.meta.prefs()

        preset = prefs.selected_preset()
        utils.preset.load_preset(self, preset)

        utils.meta.update_simple_tabs()

        utils.meta.save_userpref()
        return {'FINISHED'}
