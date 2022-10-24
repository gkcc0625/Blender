from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .. import props

import bpy
import re
from .. import utils


def uniquify_name(preset: props.preset.Preset, name: str):
    prefs = utils.meta.prefs()
    others = [p.name for p in prefs.preset_items if p != preset]

    while name in others:
        numbers = re.findall(r'\d+', name)

        if numbers:
            old = numbers[-1]
            new = str(int(old) + 1)

            zeroes = 3 - len(new)
            new = zeroes * '0' + new

            parts = name.rsplit(old, 1)
            name = new.join(parts)

        else:
            name += '.001'

    preset['name'] = name


def add_preset(self: bpy.types.Operator):
    prefs = utils.meta.prefs()

    preset = prefs.preset_items.add()
    preset.name = 'Preset'

    for addon in prefs.addon_items:
        if addon.visible and addon.enabled():
            preset_addon = preset.addon_items.add()
            preset_addon.name = addon.name

    index = len(prefs.preset_items) - 1
    prefs['preset_enum'] = index

    self.report({'INFO'}, f'Added preset "{preset.name}"')


def remove_preset(self: bpy.types.Operator, index: int):
    prefs = utils.meta.prefs()
    prefs['preset_enum'] = -1

    name = prefs.preset_items[index].name
    prefs.preset_items.remove(index)

    self.report({'INFO'}, f'Removed preset "{name}"')


def save_preset(self: bpy.types.Operator, preset: props.preset.Preset):
    prefs = utils.meta.prefs()
    preset.addon_items.clear()

    for addon in prefs.addon_items:
        if addon.visible and addon.enabled():
            preset_addon = preset.addon_items.add()
            preset_addon.name = addon.name

    self.report({'INFO'}, f'Saved preset "{preset.name}"')


def load_preset(self: bpy.types.Operator, preset: props.preset.Preset):
    prefs = utils.meta.prefs()

    for addon in prefs.addon_items:
        addon: props.addon.Addon

        if not addon.visible:
            continue

        if preset.additive:
            if addon.enabled() or not preset.stored(addon):
                continue

        else:
            if addon.enabled() == preset.stored(addon):
                continue

        utils.addon.toggle_addon(self, addon)

    self.report({'INFO'}, f'Loaded preset "{preset.name}"')
