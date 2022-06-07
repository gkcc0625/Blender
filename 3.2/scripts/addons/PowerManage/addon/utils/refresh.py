from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Tuple

if TYPE_CHECKING:
    from .. import props

import bpy
from .. import utils


def refresh_all() -> Tuple[int, int, int]:
    prefs = utils.meta.prefs()
    modules = utils.meta.other_modules()

    addons = refresh_addons(prefs, modules)
    categories = refresh_categories(prefs)
    presets = refresh_presets(prefs)

    return addons, categories, presets


def refresh_addons(prefs: props.prefs.Prefs, modules: Dict[str, dict]) -> int:
    visible_dict = prefs.visible_dict()
    prefs.addon_items.clear()

    for name, bl_info in modules.items():
        addon: props.addon.Addon = prefs.addon_items.add()

        addon.name = name
        addon.label = bl_info.get('name', name)
        addon.category = bl_info.get('category', 'Unknown')
        addon.visible = visible_dict.get(name, False)

    return len(prefs.addon_items)


def refresh_categories(prefs: props.prefs.Prefs) -> int:
    category_dict = prefs.category_dict()
    prefs.category_items.clear()

    for addon in prefs.addon_items:
        addon: props.addon.Addon

        if addon.category not in prefs.category_items:
            category: props.category.Category = prefs.category_items.add()
            category.name = addon.category
            category.expand = category_dict.get(category.name, True)

    return len(prefs.category_items)


def refresh_presets(prefs: props.prefs.Prefs) -> int:
    for preset in prefs.preset_items:
        preset: props.preset.Preset

        addon_names = preset.addon_names()
        preset.addon_items.clear()

        for name in addon_names:
            if name in prefs.addon_items:
                preset_addon: bpy.types.PropertyGroup = preset.addon_items.add()
                preset_addon.name = name

    return len(prefs.preset_items)
