import bpy
from .. import utils


class OpenPreferences(bpy.types.Operator):
    bl_idname = 'powermanage.open_preferences'
    bl_label = 'Open Preferences'
    bl_description = 'Open the PowerManage preferences'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context: bpy.types.Context) -> set:
        bpy.ops.preferences.addon_show(module=utils.meta.module())

        addons, categories, presets = utils.refresh.refresh_all()
        self.report({'INFO'}, f'Refreshed {presets} presets')
        self.report({'INFO'}, f'Found {addons} addons in {categories} categories')

        utils.meta.save_userpref()
        return {'FINISHED'}
