import bpy


class PresetMenu(bpy.types.Menu):
    bl_idname = 'POWERMANAGE_MT_preset_menu'
    bl_label = 'Preset Menu'

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        layout.operator('powermanage.new_preset', icon='FILE')
        layout.operator('powermanage.update_preset', icon='FILE_TICK')
        layout.operator('powermanage.reload_preset', icon='FILE_REFRESH')
        layout.operator('powermanage.remove_preset', icon='TRASH')
