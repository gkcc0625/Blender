import bpy
from .. import utils


class RemovePreset(bpy.types.Operator):
    bl_idname = 'powermanage.remove_preset'
    bl_label = 'Remove Preset'
    bl_description = 'Remove the selected preset'
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        prefs = utils.meta.prefs()
        return prefs.selected_preset()

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set:
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context: bpy.types.Context) -> set:
        prefs = utils.meta.prefs()

        index = prefs.preset_index()
        utils.preset.remove_preset(self, index)

        utils.meta.save_userpref()
        return {'FINISHED'}
