import bpy
from .. import utils


class MainPanel(bpy.types.Panel):
    bl_idname = 'POWERMANAGE_PT_main_panel'
    bl_label = 'PowerManage'
    bl_category = 'PowerSave'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        col = layout.column()
        utils.ui.draw_panel(col)
