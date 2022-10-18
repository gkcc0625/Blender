# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy, os

from bpy.types import UILayout

from typing import List, Tuple, Union


from ..properties import PropertySection, Properties
from ..utils.blender import all_spaces, is_file_saved
from ..registries.resource_lists_registry import ResourceListsRegistry
from ..registries.config_registry import ConfigRegistry

from ..operators.multi_purpose import ASSET_OT_multi_purpose
from ..operators.tag_manager import ASSET_OT_tag_manager
from ..operators.export_assets import ASSET_OT_export
from ..operators.update_local import ASSET_OT_update_local
from ..operators.create_new_blend import ASSET_OT_create_new_blend
from ..operators.create_catalog import ASSET_OT_create_catalog


def initial_info(l: UILayout):
    c = l.column(align=True)
    c.label(text='! NOTICE !', icon='ERROR')
    c.separator()
    for t in [
            'Despite Asset Wizard Pro has been',
            'tested, exporting Assets into', 
            'existing .blend Files was not', 
            'straightforward, as it is not',
            'directly possible with Blender\'s API.',
            'So please make a Backup of Library', 
            'Files, to which you like to add Assets.',
            '',
            'I\'m not responsible for data', 
            'losses when ignoring this Advice.',
            'Backups are recommended in any way.'
        ]:
        c.label(text=t)

    c.separator()
    ASSET_OT_multi_purpose.create_ui_agree(c)



def export_panel(
    l: UILayout, 
    res: List[Tuple[str, str, str, str]], 
    section: PropertySection, 
    section_name: str
    ) -> Union[UILayout, None]:
    """
    Common UI for export used in Shader and Geometry Node space, as well as in 3D view.
    Returns column layout if export is possible, otherwise None
    """
    if ConfigRegistry.get().show_initial_info():
        return initial_info(l)

    c = l.column(align=True)
    c.use_property_decorate = False
    c.use_property_split = True
    if bpy.context.preferences.filepaths.asset_libraries:
        # Asset output file.
        r = c.row(align=True)
        ASSET_OT_create_new_blend.create_ui(r, section.export_library, section_name)
        if ResourceListsRegistry.get().library_files(section.export_library):
            r.prop(section, 'show_stats', text='', icon='QUESTION', toggle=True)
            ASSET_OT_multi_purpose.create_ui_open_asset(r, os.path.join(section.export_library, section.export_file))
        ASSET_OT_multi_purpose.create_ui_img_update_res_lists(r)
        if all_spaces('FILE_BROWSER'):
            ASSET_OT_multi_purpose.create_ui_refresh_lib(r)
        c.prop(section, 'export_library', text='')
        
        # Is there any file in this repo?
        if ResourceListsRegistry.get().library_files(section.export_library):
            c.prop(section, 'export_file', text='')

            # File statistics.
            if section.show_stats:
                b = c.box().column()
                for e, t in ResourceListsRegistry.get().stats(os.path.join(section.export_library, section.export_file)):
                    b.label(text=f'{e}: {t}')

            c.separator()

            c.prop(section, 'use_render_as_preview', toggle=True, text='Render Result', icon='RENDER_STILL')

            # Catalog, tags, description author.
            s = c.row(align=True)# c.split(factor=0.9, align=True)
            if ResourceListsRegistry.get().catalogs(section.export_library):
                s.prop(section, 'catalog', text='Catalog')
            else:
                s.box().label(text='Repository has no Catalog yet')
            ASSET_OT_create_catalog.create_ui(s, section_name)

            c.prop(section, 'description', text='Description')

            c.prop(Properties.get(), 'author', text='Author')

            #c.separator()

            if ConfigRegistry.get().tags():
                s = c.row(align=True) #c.split(factor=0.9, align=True)
                s.prop(section, 'tag_select', text='Tag')
                ASSET_OT_tag_manager.create_ui(s, 'ADD', True, 'ADD', section_name, section.tag_select)

            s = c.row(align=True) #c.split(factor=0.9, align=True)
            s.prop(section, 'new_tag', text='New Tag')
            ASSET_OT_tag_manager.create_ui(
                s, 
                'ADD', 
                len(section.new_tag) > 0,
                'ADD_NEW',
                section_name,
                section.new_tag
            )

            if section.tags:
                c.separator()
                b = c.box().column(align=True)
                for t in section.tags:
                    s = b.split(factor=0.9, align=True)
                    s.label(text=t.title)
                    ASSET_OT_tag_manager.create_ui(s, 'REMOVE', True, 'REMOVE', section_name, t.title)

            c.separator()
            for mitn in res:
                ASSET_OT_export.create_ui(c, mitn, section)

            return c
        else:
            c.box().label(text='No File in Library, create one', icon='ERROR')
    else:
        b = c.box()
        b.label(text='No Asset Libraries configured,')
        b.label(text='check Preferences')


def asset_browser_header(self, context: bpy.context):
    """
    Add buttons to asset browser header to recreate local asset prview images.
    """
    from bpy_extras.asset_utils import SpaceAssetInfo

    space_data = context.space_data
    if SpaceAssetInfo.is_asset_browser(space_data):
        layout = self.layout # type: bpy.types.UILayout

        props = Properties.get()

        layout.separator()
        r = layout.row(align=True)
        r2 = r.row(align=True)
        r2.enabled = is_file_saved()
        ASSET_OT_update_local.create_ui(r2)
        ASSET_OT_multi_purpose.create_ui_auto_place(r, props.auto_place_padding)
        r.prop(props, 'auto_place_padding')
