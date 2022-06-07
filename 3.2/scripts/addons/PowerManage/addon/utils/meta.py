from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .. import props

import bpy
import addon_utils
import pathlib
from .. import ui


def module() -> str:
    return __name__.partition('.')[0]


def prefs() -> props.prefs.Prefs:
    return bpy.context.preferences.addons[module()].preferences


def folder() -> pathlib.Path:
    path = pathlib.Path(__file__)
    path = path.parents[__name__.count('.') + 1]
    return path.resolve() / 'powermanage'


def update_panel_category(self=None, context=None):
    category = prefs().panel_category

    for cls in ui.classes:
        if issubclass(cls, bpy.types.Panel):
            cls.bl_category = category
            cls.bl_region_type = 'UI' if category else 'HEADER'

            bpy.utils.unregister_class(cls)
            bpy.utils.register_class(cls)


def save_userpref():
    preferences = bpy.context.preferences

    if preferences.use_preferences_save:
        bpy.ops.wm.save_userpref()


def other_modules() -> dict:
    addon_utils.modules_refresh()
    modules, own_name = addon_utils.modules(), module()
    return {m.__name__: m.bl_info for m in modules if m.__name__ != own_name}
