import bpy
from typing import List
from .. import props
from .. import utils


def draw_prefs(layout: bpy.types.UILayout):
    prefs = utils.meta.prefs()

    split = layout.split(factor=0.7)
    split.label(text='Choose addons to show in the manage panel')
    split.operator(
        'powermanage.refresh_list',
        text='Refresh List',
        icon='FILE_REFRESH',
    )

    layout.separator(factor=0.5)

    layout.template_list(
        'POWERMANAGE_UL_addon_list',
        '',
        prefs,
        'addon_items',
        prefs,
        'addon_index',
        rows=8,
    )

    layout.separator(factor=0.5)

    split = layout.split(factor=0.5)
    split.label(text='Addon Sorting')
    split.prop(prefs, 'addon_sorting', text='')

    layout.separator(factor=0.5)

    split = layout.split(factor=0.5)
    split.label(text='Additive Presets')
    row = split.row()
    row.alignment = 'RIGHT'
    row.prop(prefs, 'additive_presets', text='')

    layout.separator(factor=0.5)

    split = layout.split(factor=0.5)
    split.label(text='Panel Category')
    split.prop(prefs, 'panel_category', text='')

    layout.separator(factor=0.5)

    row = layout.row()
    row.operator('powermanage.backup_preferences')
    row.operator('powermanage.restore_preferences')


def draw_panel(layout: bpy.types.UILayout):
    prefs = utils.meta.prefs()
    addons = prefs.sorted_addons()

    if addons or prefs.addon_sorting == 'LIST':
        col = layout.column(align=True)

        row = col.row(align=True)
        row.prop(prefs, 'preset_enum', text='', icon='PRESET', icon_only=True)
        preset = prefs.selected_preset()

        if preset:
            row.prop(preset, 'name', text='')
            menu = 'POWERMANAGE_MT_preset_menu'
            row.menu(menu, text='', icon='DOWNARROW_HLT')
        else:
            row.operator('powermanage.new_preset', icon='ADD')

        box = col.box()
        box.prop(prefs, 'additive_presets')

        if prefs.addon_sorting == 'NAME':
            draw_by_name(layout, prefs, addons)
        elif prefs.addon_sorting == 'ENABLED':
            draw_by_enabled(layout, prefs, addons)
        elif prefs.addon_sorting == 'CATEGORY':
            draw_by_category(layout, prefs, addons)
        elif prefs.addon_sorting == 'LIST':
            draw_as_list(layout, prefs)

    else:
        layout.operator(
            'powermanage.open_preferences',
            text='Setup Visible Addons',
            icon='PREFERENCES',
        )


def draw_by_name(layout: bpy.types.UILayout, prefs: props.prefs.Prefs, addons: List[props.addon.Addon]):
    layout.separator()

    col = layout.box().column()
    row = col.row()
    row.alignment = 'LEFT'

    row.prop(
        prefs,
        'expand_addons',
        icon='DISCLOSURE_TRI_DOWN' if prefs.expand_addons else 'DISCLOSURE_TRI_RIGHT',
        emboss=False,
    )

    if not prefs.expand_addons:
        return

    col.separator(factor=0.5)

    for addon in addons:
        draw_addon(col, addon)


def draw_by_enabled(layout: bpy.types.UILayout, prefs: props.prefs.Prefs, addons: List[props.addon.Addon]):
    enabled_addons = []
    disabled_addons = []

    for addon in addons:
        if addon.enabled():
            enabled_addons.append(addon)
        else:
            disabled_addons.append(addon)

    for state in ('enabled', 'disabled'):
        state_addons = enabled_addons if state == 'enabled' else disabled_addons
        if not state_addons:
            continue

        layout.separator()

        col = layout.box().column()
        row = col.row()
        row.alignment = 'LEFT'

        row.prop(
            prefs,
            f'expand_{state}',
            icon='DISCLOSURE_TRI_DOWN' if prefs.get(f'expand_{state}') else 'DISCLOSURE_TRI_RIGHT',
            emboss=False,
        )

        if not prefs.get(f'expand_{state}'):
            continue

        col.separator(factor=0.5)

        for addon in state_addons:
            draw_addon(col, addon)


def draw_by_category(layout: bpy.types.UILayout, prefs: props.prefs.Prefs, addons: List[props.addon.Addon]):
    if not prefs.category_items:
        utils.refresh.refresh_categories(prefs)

    for category in prefs.category_items:
        category: props.category.Category

        category_addons = [addon for addon in addons if addon.category == category.name]
        if not category_addons:
            continue

        layout.separator()

        col = layout.box().column()
        row = col.row()
        row.alignment = 'LEFT'

        row.prop(
            category,
            'expand',
            text=category.name,
            icon=category.icon(),
            emboss=False,
        )

        if not category.expand:
            continue

        col.separator(factor=0.5)

        for addon in category_addons:
            draw_addon(col, addon)


def draw_as_list(layout: bpy.types.UILayout, prefs: props.prefs.Prefs):
    layout.separator()

    layout.template_list(
        'POWERMANAGE_UL_addon_list',
        '',
        prefs,
        'addon_items',
        prefs,
        'addon_index',
        rows=8,
    )


def draw_addon(layout: bpy.types.UILayout, addon: props.addon.Addon):
    row = layout.row()
    row.alignment = 'LEFT'

    row.operator(
        'powermanage.toggle_addon',
        text=addon.label,
        icon=addon.icon(),
        emboss=False,
    ).addon = addon.name
