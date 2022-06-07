import bpy
from .. import props
from .. import utils


class Preset(bpy.types.PropertyGroup):

    def _get_name(self) -> str:
        return self.get('name', '')

    def _set_name(self, value: str):
        name = value.strip()

        if name:
            utils.preset.uniquify_name(self, name)

    name: bpy.props.StringProperty(
        name='Name',
        description='Name this preset has in the list',
        get=_get_name,
        set=_set_name,
    )

    addon_items: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)

    def addon_names(self) -> list:
        return [addon.name for addon in self.addon_items]

    def stored(self, addon: props.addon.Addon):
        return addon.name in self.addon_items


# It's important to keep a global reference for enum items.
_enum_items = []


def enum_items(
    self: bpy.types.PropertyGroup,
    context: bpy.types.Context,
) -> list:
    global _enum_items

    _enum_items = [(p.name, p.name, '') for p in self.preset_items]
    return _enum_items


def get_enum(self: bpy.types.PropertyGroup) -> int:
    return self.get('preset_enum', 0)


def set_enum(self: bpy.types.PropertyGroup, value: int):
    self['preset_enum'] = value
    bpy.ops.powermanage.reload_preset()
