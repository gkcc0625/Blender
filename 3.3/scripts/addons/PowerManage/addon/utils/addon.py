from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .. import props

import bpy
import json
from .. import utils


def backup(self: bpy.types.Operator, addon: props.addon.Addon):
    prefs = addon.prefs()
    path = addon.path()

    if prefs is not None:
        data = utils.backup.save_recursive_group(prefs)
        datastr = json.dumps(data, indent=1, sort_keys=False)

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(datastr)

        self.report({'INFO'}, f'Saved file "{path.name}"')

    else:
        self.report({'INFO'}, f'Addon "{addon.name}" has no preferences')


def restore(self: bpy.types.Operator, addon: props.addon.Addon):
    prefs = addon.prefs()
    path = addon.path()

    if prefs is None:
        self.report({'INFO'}, f'Addon "{addon.name}" has no preferences')

    elif not path.is_file():
        self.report({'INFO'}, f'File "{path}" does not exist')

    else:
        datastr = path.read_text()
        data = json.loads(datastr)

        utils.backup.load_recursive_group(prefs, data)
        self.report({'INFO'}, f'Loaded file "{path.name}"')


def toggle_addon(self: bpy.types.Operator, addon: props.addon.Addon):
    if not addon.installed():
        self.report({'WARNING'}, f'Addon "{addon.label}" is not installed')

    elif addon.enabled():
        backup(self, addon)
        bpy.ops.preferences.addon_disable(module=addon.name)

    else:
        bpy.ops.preferences.addon_enable(module=addon.name)
        restore(self, addon)
