import bpy
from typing import List
from .. import props
from .. import utils


class Prefs(bpy.types.AddonPreferences):
    bl_idname = utils.meta.module()

    addon_sorting: bpy.props.EnumProperty(
        name='Addon Sorting',
        description='How to show addons in the panel',
        items=[
            ('NAME', 'By Name', 'Sort addons by name alone'),
            ('ENABLED', 'By Enabled', 'Sort addons by enabled state'),
            ('CATEGORY', 'By Category', 'Sort addons by category'),
            ('LIST', 'As List', 'Display addons in a list'),
        ],
        default='CATEGORY',
    )

    expand_addons: bpy.props.BoolProperty(name='Addons', default=True)
    expand_enabled: bpy.props.BoolProperty(name='Enabled', default=True)
    expand_disabled: bpy.props.BoolProperty(name='Disabled', default=True)
    category_items: bpy.props.CollectionProperty(type=props.category.Category)

    addon_items: bpy.props.CollectionProperty(type=props.addon.Addon)
    addon_index: bpy.props.IntProperty(default=-1, min=-1, max=-1)

    preset_items: bpy.props.CollectionProperty(type=props.preset.Preset)
    preset_enum: bpy.props.EnumProperty(
        name='Preset',
        items=props.preset.enum_items,
        get=props.preset.get_enum,
        set=props.preset.set_enum,
    )

    panel_category: bpy.props.StringProperty(
        name='Panel Category',
        description='Sidebar category to show the panel in, empty to hide it',
        default='PowerSave',
        update=utils.meta.update_panel_category,
    )

    simple_tabs: bpy.props.BoolProperty(
        name='SIMPLE TABS Integration',
        description='Loading a preset or enabling an addon will update SIMPLE TABS',
        default=True,
    )

    def category_dict(self) -> dict:
        return {category.name: category.expand for category in self.category_items}

    def visible_dict(self) -> dict:
        return {addon.name: addon.visible for addon in self.addon_items}

    def sorted_addons(self) -> List[props.addon.Addon]:
        all_addons: List[props.addon.Addon] = self.addon_items
        visible_addons = [addon for addon in all_addons if addon.visible]
        return sorted(visible_addons, key=lambda addon: addon.label)

    def preset_index(self) -> int:
        return self.get('preset_enum', -1)

    def selected_preset(self) -> props.preset.Preset:
        index = self.preset_index()

        if index in range(len(self.preset_items)):
            return self.preset_items[index]

    def draw(self, context: bpy.types.Context):
        layout: bpy.types.UILayout = self.layout

        col = layout.column()
        utils.ui.draw_prefs(col)
