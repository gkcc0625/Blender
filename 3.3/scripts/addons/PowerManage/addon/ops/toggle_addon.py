import bpy
from .. import utils


class ToggleAddon(bpy.types.Operator):
    bl_idname = 'powermanage.toggle_addon'
    bl_label = 'Toggle Addon'
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def description(cls, context, properties) -> str:
        prefs = utils.meta.prefs()
        addon = prefs.addon_items[properties['addon']]
        return addon.description()

    addon: bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context: bpy.types.Context) -> set:
        prefs = utils.meta.prefs()

        addon = prefs.addon_items[self.addon]
        utils.addon.toggle_addon(self, addon)

        utils.meta.update_simple_tabs()

        utils.meta.save_userpref()
        return {'FINISHED'}
