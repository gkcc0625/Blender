import bpy
import pathlib
from .. import props
from .. import utils


class Meta(bpy.types.PropertyGroup):

    def module(self) -> str:
        return utils.meta.module()

    def prefs(self) -> props.prefs.Prefs:
        return utils.meta.prefs()

    def folder(self) -> pathlib.Path:
        return utils.meta.folder()

    def draw_prefs(self, layout: bpy.types.UILayout):
        utils.ui.draw_prefs(layout)

    def draw_panel(self, layout: bpy.types.UILayout):
        utils.ui.draw_panel(layout)
