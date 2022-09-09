import bpy
from .. import utils


class RefreshList(bpy.types.Operator):
    bl_idname = 'powermanage.refresh_list'
    bl_label = 'Refresh List'
    bl_description = 'Refresh the addon list with all installed addons'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context: bpy.types.Context) -> set:
        addons, categories, presets = utils.refresh.refresh_all()
        self.report({'INFO'}, f'Refreshed {presets} presets')
        self.report({'INFO'}, f'Found {addons} addons in {categories} categories')

        utils.meta.save_userpref()
        return {'FINISHED'}
