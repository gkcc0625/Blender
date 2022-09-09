import bpy
import pathlib
from .. import utils


class Addon(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name='Module',
        description='The name of the module for this addon',
    )

    label: bpy.props.StringProperty(
        name='Label',
        description='The label for this addon',
    )

    category: bpy.props.StringProperty(
        name='Category',
        description='The category for this addon',
    )

    visible: bpy.props.BoolProperty(
        name='Visible',
        description='Whether this addon is shown in the manage panel, and affected by presets',
    )

    def full_label(self) -> str:
        return f'{self.category}: {self.label}'

    def description(self) -> str:
        if self.enabled():
            return f'Backup prefs for "{self.full_label()}" and disable it'
        else:
            return f'Enable "{self.full_label()}" and restore its prefs'

    def installed(self) -> bool:
        return self.name in utils.meta.other_modules()

    def enabled(self) -> bool:
        return self.name in bpy.context.preferences.addons

    def icon(self) -> str:
        return 'CHECKBOX_HLT' if self.enabled() else 'CHECKBOX_DEHLT'

    def prefs(self) -> bpy.types.AddonPreferences:
        return bpy.context.preferences.addons[self.name].preferences

    def path(self) -> pathlib.Path:
        return utils.meta.folder() / f'{self.name}.json'
